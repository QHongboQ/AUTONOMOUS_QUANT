"""Evaluate frozen Protocol V1 gates from Qlib-owned daily net returns."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


DAILY_SHA256 = "7cea6cc75d473c7c3768a1bce5e45729aaf1d7d8815e6e54eb75bb27eb031d80"
PRIMARY = "LGB_30_3__BASE"
CONTROL = "LINEAR_50_5__BASE"
BASE_LGB = [
    "LGB_50_5__BASE",
    PRIMARY,
    "LGB_100_10__BASE",
    "LGB_25_3__BASE",
    "LGB_35_3__BASE",
    "LGB_30_2__BASE",
    "LGB_30_4__BASE",
]
ALL_COLUMNS = BASE_LGB + [
    CONTROL,
    "LGB_30_3__TWO_X",
    "LINEAR_50_5__TWO_X",
    "LGB_30_3__THREE_X",
    "LINEAR_50_5__THREE_X",
]
NEIGHBORS = [
    "LGB_25_3__BASE",
    "LGB_35_3__BASE",
    "LGB_30_2__BASE",
    "LGB_30_4__BASE",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def compounded(values: pd.Series | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    if not np.isfinite(array).all() or (array <= -1.0).any():
        raise RuntimeError("non-finite or invalid daily net return")
    return float(np.prod(1.0 + array) - 1.0)


def split_evidence(frame: pd.DataFrame, tests: list[np.ndarray], candidate: str, control: str) -> list[dict[str, object]]:
    result = []
    for split_id, indices in enumerate(tests):
        candidate_return = compounded(frame.iloc[indices][candidate])
        control_return = compounded(frame.iloc[indices][control])
        result.append(
            {
                "split_id": split_id,
                "start": frame.index[indices].min().strftime("%Y-%m-%d"),
                "end": frame.index[indices].max().strftime("%Y-%m-%d"),
                "session_count": len(indices),
                "candidate_net_return": candidate_return,
                "control_net_return": control_return,
                "active_return": candidate_return - control_return,
            },
        )
    return result


def reduce_splits(splits: list[dict[str, object]]) -> dict[str, object]:
    active = np.asarray([row["active_return"] for row in splits], dtype=float)
    return {
        "split_count": len(splits),
        "positive_active_return_fraction": float(np.mean(active > 0.0)),
        "median_active_return": float(np.median(active)),
        "gate": bool(np.mean(active > 0.0) >= 0.60 and np.median(active) > 0.0),
        "splits": splits,
    }


def json_value(value):
    if isinstance(value, (pd.Series, pd.DataFrame)):
        return value.to_dict()
    if isinstance(value, pd.Index):
        return value.tolist()
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=("skfolio", "arch", "validation"))
    parser.add_argument("--daily", required=True, type=Path)
    parser.add_argument("--provider-calendar", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    if (args.output / args.mode).exists():
        raise FileExistsError(f"{args.mode} rehearsal evidence already exists")
    if sha256(args.daily) != DAILY_SHA256:
        raise RuntimeError("Qlib daily-return checkpoint identity mismatch")

    raw = pd.read_csv(args.daily)
    if list(raw.columns) != ["date"] + ALL_COLUMNS:
        raise RuntimeError("unexpected Qlib daily-return columns")
    frame = raw.set_index(pd.to_datetime(raw.pop("date"))).sort_index()
    frame.index.name = "date"
    if len(frame) != 753 or frame.index.min() != pd.Timestamp("2022-01-03") or frame.index.max() != pd.Timestamp("2024-12-31"):
        raise RuntimeError("Qlib daily-return interval mismatch")
    if frame.index.duplicated().any() or not np.isfinite(frame.to_numpy(dtype=float)).all():
        raise RuntimeError("Qlib daily-return evidence is duplicate or non-finite")

    provider_sessions = pd.DatetimeIndex(
        [line for line in args.provider_calendar.read_text(encoding="utf-8").splitlines() if line],
    )
    if args.mode == "skfolio":
        import skfolio
        from skfolio.model_selection import CombinatorialPurgedCV, WalkForward

        if skfolio.__version__ != "1.0.6":
            raise RuntimeError(f"unexpected skfolio version: {skfolio.__version__}")
        wf = WalkForward(test_size=63, train_size=504, purged_size=2, expand_train=False, reduce_test=False)
        wf_pairs = list(wf.split(frame.to_numpy()))
        wf_tests = [test for _, test in wf_pairs]
        walkforward = reduce_splits(split_evidence(frame, wf_tests, PRIMARY, CONTROL))
        for train, test in wf_pairs:
            if set(train) & set(test):
                raise RuntimeError("WalkForward returned overlapping train/test indices")
        cpcv = CombinatorialPurgedCV(n_folds=10, n_test_folds=2, purged_size=2, embargo_size=2)
        cpcv_pairs = list(cpcv.split(frame.to_numpy()))
        cpcv_tests = [np.sort(np.concatenate(test_groups)) for _, test_groups in cpcv_pairs]
        cpcv_result = reduce_splits(split_evidence(frame, cpcv_tests, PRIMARY, CONTROL))
        for (train, _), test in zip(cpcv_pairs, cpcv_tests):
            if set(train) & set(test):
                raise RuntimeError("CPCV returned overlapping train/test indices")
        cost_results = {}
        for scenario, candidate, control in (
            ("BASE", PRIMARY, CONTROL),
            ("TWO_X", "LGB_30_3__TWO_X", "LINEAR_50_5__TWO_X"),
            ("THREE_X", "LGB_30_3__THREE_X", "LINEAR_50_5__THREE_X"),
        ):
            reduced = reduce_splits(split_evidence(frame, wf_tests, candidate, control))
            cost_results[scenario] = {
                "median_active_return": reduced["median_active_return"],
                "positive_active_return_fraction": reduced["positive_active_return_fraction"],
                "gate": bool(reduced["median_active_return"] > 0.0) if scenario != "THREE_X" else "EVIDENCE_ONLY",
            }
        configurations = [PRIMARY] + NEIGHBORS
        active_returns = {name: compounded(frame[name]) - compounded(frame[CONTROL]) for name in configurations}
        positive_neighbors = sum(active_returns[name] > 0.0 for name in NEIGHBORS)
        robustness_median = float(np.median(list(active_returns.values())))
        regime_results = []
        for start_year in (2015, 2017, 2019, 2021, 2023):
            expected = provider_sessions[(provider_sessions >= pd.Timestamp(f"{start_year}-01-01")) & (provider_sessions <= pd.Timestamp(f"{start_year + 1}-12-31"))]
            available = frame.index.intersection(expected)
            status = "UNAVAILABLE" if len(available) == 0 else "AVAILABLE" if len(available) == len(expected) else "PARTIAL"
            regime_results.append({
                "block": f"{start_year}-{start_year + 1}", "status": status,
                "expected_sessions": len(expected), "available_sessions": len(available),
                "active_return": None if len(available) == 0 else compounded(frame.loc[available, PRIMARY]) - compounded(frame.loc[available, CONTROL]),
            })
        report = {
            "input_sha256": sha256(args.daily), "skfolio_version": skfolio.__version__,
            "walkforward": walkforward, "cpcv": cpcv_result,
            "cost_stress_walkforward": cost_results,
            "parameter_robustness": {
                "active_returns": active_returns, "positive_neighbors": positive_neighbors,
                "median_active_return": robustness_median,
                "gate": bool(active_returns[PRIMARY] > 0.0 and positive_neighbors >= 3 and robustness_median > 0.0),
            },
            "regime_evidence": regime_results,
        }
        write_json(args.output / "skfolio" / "skfolio-report.json", report)
        print(json.dumps(report, sort_keys=True))
        return

    if args.mode == "arch":
        import arch
        from arch.bootstrap import MCS, SPA, RealityCheck, StepM

        if arch.__version__ != "8.0.0":
            raise RuntimeError(f"unexpected arch version: {arch.__version__}")
        benchmark_loss = -frame[CONTROL]
        model_losses = -frame[BASE_LGB]
        all_losses = -frame[BASE_LGB + [CONTROL]]
        spa = SPA(benchmark_loss, model_losses, block_size=10, reps=5000, bootstrap="stationary", seed=20260913)
        spa.compute()
        reality = RealityCheck(benchmark_loss, model_losses, block_size=10, reps=5000, bootstrap="stationary", seed=20260913)
        reality.compute()
        stepm = StepM(benchmark_loss, model_losses, size=0.05, block_size=10, reps=5000, bootstrap="stationary", seed=20260913)
        stepm.compute()
        mcs = MCS(all_losses, size=0.05, reps=5000, block_size=10, bootstrap="stationary", seed=20260913)
        mcs.compute()
        spa_consistent = float(spa.pvalues.loc["consistent"])
        reality_consistent = float(reality.pvalues.loc["consistent"])
        stepm_superior = list(stepm.superior_models)
        mcs_included = list(mcs.included)
        report = {
            "arch_version": arch.__version__, "input_sha256": sha256(args.daily),
            "policy": {"alpha": 0.05, "reps": 5000, "bootstrap": "stationary", "block_size": 10, "seed": 20260913},
            "spa_pvalues": json_value(spa.pvalues), "spa_consistent_pvalue": spa_consistent, "spa_gate": spa_consistent <= 0.05,
            "reality_check_pvalues": json_value(reality.pvalues), "reality_check_consistent_pvalue": reality_consistent,
            "reality_check_gate": reality_consistent <= 0.05,
            "stepm_superior_models": stepm_superior, "stepm_primary_superior": PRIMARY in stepm_superior,
            "stepm_gate": PRIMARY in stepm_superior,
            "mcs_included": mcs_included, "mcs_excluded": list(mcs.excluded),
            "mcs_primary_included": PRIMARY in mcs_included, "mcs_gate": PRIMARY in mcs_included,
        }
        write_json(args.output / "arch" / "arch-report.json", report)
        print(json.dumps(report, sort_keys=True))
        return

    import exchange_calendars
    import pandera
    import pandera.pandas as pa

    if pandera.__version__ != "0.33.1" or exchange_calendars.__version__ != "4.13.2":
        raise RuntimeError("unexpected Pandera or exchange_calendars version")
    schema = pa.DataFrameSchema(
        {
            "date": pa.Column(str, checks=pa.Check.str_matches(r"^\d{4}-\d{2}-\d{2}$"), unique=True),
            **{column: pa.Column(float, checks=pa.Check(lambda values: np.isfinite(values).all())) for column in ALL_COLUMNS},
        }, strict=True, coerce=True,
    )
    validated = schema.validate(pd.read_csv(args.daily))
    xnys = exchange_calendars.get_calendar("XNYS", start="2015-01-02", end="2024-12-31")
    expected_test = xnys.sessions_in_range("2022-01-03", "2024-12-31").tz_localize(None)
    expected_provider = xnys.sessions_in_range("2015-01-02", "2024-12-31").tz_localize(None)
    if not frame.index.equals(expected_test) or not provider_sessions.equals(expected_provider):
        raise RuntimeError("Qlib evidence/provider calendar does not exactly match XNYS")
    report = {
        "input_sha256": sha256(args.daily), "pandera_version": pandera.__version__,
        "exchange_calendars_version": exchange_calendars.__version__, "pandera_validation": "PASS",
        "xnys_validation": "PASS", "daily_rows": len(validated),
        "duplicate_dates": int(validated["date"].duplicated().sum()), "finite_required_values": True,
        "aligned_candidate_control_dates": True, "provider_calendar_rows": len(provider_sessions),
        "temporal_integrity": "PASS",
    }
    write_json(args.output / "validation" / "validation-report.json", report)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
