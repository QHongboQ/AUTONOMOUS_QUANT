"""One-shot execution of the frozen P7 historical static-ensemble protocol.

The ``preflight`` mode never deserializes real prediction or label values.  It
creates the immutable attempt root only after all identity and synthetic API
checks pass.  The ``execute`` mode is the single outcome-access attempt.  The
``statistics`` mode is an internal continuation invoked in the pinned
skfolio/arch runtime against the already-derived daily RankIC relation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


TASK = "AUTONOMOUS-QUANT-P7-HISTORICAL-STATIC-ENSEMBLE-RESEARCH-EXECUTION-001"
BASE_MAIN = "3cfa76f9d7541d00ce672da2cfcaf0827dfeb015"
PROTOCOL_SHA = "b60078bdba4190fbda2c6f3d3580f0e40a9801c87867095bfaa12885a0fb3ff4"
INPUT_CONTRACT_SHA = "92de81d0b8b7b7a29891bf523ae8519af44456f52fea3410ebf0ebd210d0f81f"
POPULATION_SHA = "2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e"
QLIB_SOURCE_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"
QLIB_VERSION = "0.9.8.dev26"
LABEL_SHA = "c14c7c3f1e698126663b85dfcf436cf3258dc4609e8217e95ed188d9be7db35e"
STATS_PYTHON = Path("/home/zhou/AQ_ENVS/p5-h1-statistics/bin/python")
RFC8785_PYTHON = Path("/home/zhou/AQ_ENVS/p5-fundamental-intelligence/bin/python")
PROVIDER = Path("/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data")
INPUT_ROOT = Path("/mnt/d/AQ_DATA/P7/real-data-ensemble-input-contract-and-protocol-feasibility-001")
OUTPUT_ROOT = Path("/mnt/d/AQ_DATA/P7/historical-static-ensemble-research-execution-001")
DERIVED_MANIFEST = INPUT_ROOT / "closeout-derived-view-manifest.json"
ALLOWLIST = INPUT_ROOT / "closeout-expanded-read-allowlist-frozen.json"
QUALIFICATION = INPUT_ROOT / "closeout-session-local-qualification-mask.json"
PROTOCOL = Path("30-research-system/qlib/p7-native-ensemble/historical-static-ensemble-research-protocol.json")

CANDIDATE_IDS = {
    "candidate-001": "sha256:de6ecb854a360ffe185ab055df5220d581da8a5e8c14f1a1adf24ef4cc60d577",
    "candidate-002": "sha256:5f3c9e5f6ce0a1fdf38d87ab6a4609d94f3e170e70008c4289ef3828898e9b5d",
    "candidate-003": "sha256:e36c1cd6a92ee4b078cdf3e514f839739d74a72940596c0377dcb6bbbeeb3e16",
    "candidate-004": "sha256:5e2c2e5746a020393ced636cbae76d612aaf9334cfa2ea4addd6dd6ba1960d85",
    "candidate-005": "sha256:f8409ded53d351c83de386794cf7fbf383813805cf7c60bd112dbb8fae1dc1cc",
    "candidate-006": "sha256:aad1eaafe206dfa683dfd47934b17fa0d16df65fcf7b967534f19f518ba3a81b",
    "candidate-007": "sha256:80662d497b6e0da7f60f528d56e3048f20fa3531a1f179fc36587784fbe104e7",
    "candidate-008": "sha256:7353d7a77ffb0883014e81b10457de323d4d300954be304f31c17c2b18230b15",
    "candidate-009": "sha256:61ae57c774925c90836ba69ff0fbfdbaa0ef015127f61f3a5b6e6b7f063adb4c",
    "candidate-010": "sha256:89397f82c2361985cde1e73ce740e8da808d4db005bc28885dbd1ad4271c5d5d",
    "candidate-011": "sha256:99bdafc3e9f0b1c7f895810d50f398eac92a2f8805f33b87c7fa00347f344195",
    "candidate-012": "sha256:36ef2725aea4552dcbe35791fc63b4deed4c889197d12afcc272089e19fee33b",
    "candidate-013": "sha256:c73944e9e3d16055e30d3ad5c3e1935450c32981aa3fc7408e0814662b9a88ec",
    "candidate-014": "sha256:644a49049888306381197754c95574f536fd98267766431afebd46ac0f600934",
    "candidate-015": "sha256:c21850f3f1ef47bc22ec70096622118216452ec550013f8c06874a3b6a851086",
    "candidate-016": "sha256:20f058b616bed7ce14c4c820e4742c92cafb10b12447a1706b90364137e87f0b",
    "candidate-017": "sha256:1a0e410676276ef1a7381d94d7a13feace60969b8207f195e51ea77f23450719",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value


def write_json(path: Path, value: Any, *, replace: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise FileExistsError(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(json_value(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rfc8785_sha(path: Path) -> str:
    code = (
        "import hashlib,json,rfc8785,sys;"
        "v=json.load(open(sys.argv[1],encoding='utf-8'));"
        "print(hashlib.sha256(rfc8785.dumps(v)).hexdigest())"
    )
    return subprocess.check_output([str(RFC8785_PYTHON), "-c", code, str(path)], text=True).strip()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def initialize_qlib() -> None:
    import qlib

    qlib.init(provider_uri=str(PROVIDER), region="us", expression_cache=None, dataset_cache=None)


def synthetic_qlib_preflight(repo: Path) -> dict[str, Any]:
    import qlib
    from qlib.backtest import backtest_loop, get_exchange
    from qlib.backtest.account import Account
    from qlib.backtest.executor import SimulatorExecutor
    from qlib.backtest.utils import CommonInfrastructure
    from qlib.contrib.eva.alpha import calc_ic
    from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy
    from qlib.model.ens.ensemble import AverageEnsemble

    if qlib.__version__ != QLIB_VERSION:
        raise RuntimeError(f"unexpected Qlib version: {qlib.__version__}")
    source_sha = subprocess.check_output(
        ["git", "-C", "/home/zhou/AQ_WORKSPACES/p0-poc-b-qlib-src", "rev-parse", "HEAD"], text=True
    ).strip()
    if source_sha != QLIB_SOURCE_SHA:
        raise RuntimeError(f"unexpected Qlib source SHA: {source_sha}")
    dates = pd.to_datetime(["2024-01-02", "2024-01-03"])
    index = pd.MultiIndex.from_product([dates, ["A", "B", "C"]], names=["datetime", "instrument"])
    one = pd.DataFrame({"score": [1.0, 2.0, 3.0, 3.0, 2.0, 1.0]}, index=index)
    two = pd.DataFrame({"score": [2.0, 1.0, 3.0, 1.0, 3.0, 2.0]}, index=index)
    result = AverageEnsemble()({"one": one, "two": two})
    label = pd.Series([1.0, 2.0, 3.0, 3.0, 2.0, 1.0], index=index, name="label")
    _, rank_ic = calc_ic(result, label, dropna=False)
    if len(result) != 6 or len(rank_ic) != 2 or not np.isfinite(rank_ic).all():
        raise RuntimeError("Qlib AverageEnsemble/calc_ic synthetic preflight failed")
    initialize_qlib()
    account = Account(init_cash=100_000_000, benchmark_config={"benchmark": None})
    exchange = get_exchange(
        freq="day", start_time="2024-01-02", end_time="2024-01-03", codes="all",
        limit_threshold=0.095, deal_price="close", open_cost=0.0005,
        close_cost=0.0015, min_cost=5,
    )
    common = CommonInfrastructure(trade_account=account, trade_exchange=exchange)
    strategy = TopkDropoutStrategy(signal=result, topk=30, n_drop=3)
    executor = SimulatorExecutor(time_per_step="day", generate_portfolio_metrics=True)
    strategy.reset_common_infra(common)
    executor.reset_common_infra(common)
    if not callable(backtest_loop):
        raise RuntimeError("Qlib backtest path unavailable")
    return {
        "qlib_version": qlib.__version__, "qlib_source_sha": source_sha,
        "average_ensemble": "PASS", "calc_ic": "PASS",
        "topk_dropout_strategy_backtest_path": "PASS",
    }


def stats_synthetic_preflight() -> dict[str, Any]:
    code = r'''import json,numpy as np,arch,skfolio
from arch.bootstrap import MCS,SPA
from skfolio.model_selection import WalkForward,CombinatorialPurgedCV
r=np.random.default_rng(20260913); x=r.normal(size=751)
wf=list(WalkForward(test_size=63,train_size=504,purged_size=2,expand_train=False,reduce_test=False).split(x))
cp=list(CombinatorialPurgedCV(n_folds=10,n_test_folds=2,purged_size=2,embargo_size=2).split(x))
s=SPA(-x,-x[:,None],block_size=10,reps=99,bootstrap='stationary',studentize=True,nested=False,seed=20260913);s.compute()
m=MCS(r.normal(size=(751,18)),size=.05,reps=99,block_size=10,method='R',bootstrap='stationary',seed=20260913);m.compute()
assert list(s.pvalues.index)==['lower','consistent','upper'] and len(wf)==3 and len(cp)==45
print(json.dumps({'skfolio_version':skfolio.__version__,'arch_version':arch.__version__,'walkforward_count':len(wf),'cpcv_count':len(cp),'spa_keys':list(s.pvalues.index),'mcs_columns':18}))'''
    return json.loads(subprocess.check_output([str(STATS_PYTHON), "-c", code], text=True))


def preflight(args: argparse.Namespace) -> None:
    repo = args.repo.resolve()
    os.chdir(repo)
    if args.output.exists():
        raise FileExistsError(args.output)
    local_head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    remote_main = subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip()
    if local_head != BASE_MAIN or remote_main != BASE_MAIN:
        raise RuntimeError("execution baseline differs from frozen post-PR124 main")
    protocol = read_json(repo / PROTOCOL)
    if rfc8785_sha(repo / PROTOCOL) != PROTOCOL_SHA:
        raise RuntimeError("frozen protocol RFC8785 identity mismatch")
    if protocol["input_contract"]["input_contract_sha256"] != INPUT_CONTRACT_SHA:
        raise RuntimeError("input contract identity mismatch")
    if protocol["input_contract"]["population_index_sha256"] != POPULATION_SHA:
        raise RuntimeError("population identity mismatch")
    if sorted(protocol["candidate_snapshot"]["candidate_ids"]) != sorted(CANDIDATE_IDS.values()):
        raise RuntimeError("candidate identity set mismatch")

    manifest, allowlist = read_json(DERIVED_MANIFEST), read_json(ALLOWLIST)
    if manifest["ordered_index_sha256"] != POPULATION_SHA:
        raise RuntimeError("derived population identity mismatch")
    if (manifest["row_count"], manifest["session_count"], manifest["instrument_count"]) != (374591, 751, 547):
        raise RuntimeError("derived population dimensions mismatch")
    input_hashes: dict[str, str] = {}
    for name, item in manifest["component_artifacts"].items():
        path = Path(item["path"])
        actual = sha256(path)
        if actual != item["sha256"]:
            raise RuntimeError(f"derived input hash mismatch: {name}")
        input_hashes[name] = actual
    grid = Path(manifest["grid_path"])
    if sha256(grid) != manifest["grid_sha256"]:
        raise RuntimeError("eligible-grid artifact mismatch")
    prediction_paths = [item for item in allowlist["paths"] if item["path"].endswith("pred.pkl")]
    if len(prediction_paths) != 18:
        raise RuntimeError("source prediction allowlist count mismatch")
    for item in prediction_paths:
        if sha256(Path(item["path"])) != item["sha256"]:
            raise RuntimeError(f"source prediction hash mismatch: {item['path']}")
    source_hashes = {item["sha256"] for item in prediction_paths}
    bound_source_hashes = {
        item["source_sha256"] for item in manifest["component_artifacts"].values()
    }
    if source_hashes != bound_source_hashes:
        raise RuntimeError("derived views do not bind the exact source prediction set")
    if manifest["component_artifacts"]["control"]["source_sha256"] != read_json(repo / PROTOCOL)["control"]["prediction_sha256"]:
        raise RuntimeError("OLS source prediction identity mismatch")
    label_path = Path(prediction_paths[0]["path"]).with_name("label.pkl")
    if sha256(label_path) != LABEL_SHA:
        raise RuntimeError("label artifact identity mismatch")

    qlib_report = synthetic_qlib_preflight(repo)
    stats_report = stats_synthetic_preflight()
    if stats_report != {
        "skfolio_version": "1.0.6", "arch_version": "8.0.0",
        "walkforward_count": 3, "cpcv_count": 45,
        "spa_keys": ["lower", "consistent", "upper"], "mcs_columns": 18,
    }:
        raise RuntimeError(f"statistics synthetic preflight mismatch: {stats_report}")

    args.output.mkdir(parents=True)
    (args.output / "portfolio").mkdir()
    (args.output / "mlflow").mkdir()
    attempt = {
        "task": TASK, "base_main": BASE_MAIN, "phase": "PRE_OUTCOME_PREFLIGHT", "status": "PASS",
        "created_at_utc": utc_now(), "real_outcome_access_started": False,
        "real_outcome_execution_attempt_count": 0, "protocol_sha256": PROTOCOL_SHA,
        "input_contract_sha256": INPUT_CONTRACT_SHA, "population_index_sha256": POPULATION_SHA,
        "candidate_ids": CANDIDATE_IDS, "derived_input_hashes": input_hashes,
        "source_prediction_hashes": {item["path"]: item["sha256"] for item in prediction_paths},
        "label_path": str(label_path), "label_sha256": LABEL_SHA,
        "eligible_grid_path": str(grid), "eligible_grid_sha256": manifest["grid_sha256"],
        "qlib": qlib_report, "statistics": stats_report,
        "p2_v2_sealed_oos_accessed": False,
    }
    write_json(args.output / "attempt-manifest.json", attempt)
    print(json.dumps({"preflight": "PASS", "output": str(args.output)}, sort_keys=True))


def normalize_frame(value: Any, name: str) -> pd.DataFrame:
    if isinstance(value, pd.Series):
        frame = value.rename("score").to_frame()
    elif isinstance(value, pd.DataFrame) and value.shape[1] == 1:
        frame = value.iloc[:, 0].rename("score").to_frame()
    else:
        raise TypeError(f"{name}: unsupported prediction object")
    frame.index = frame.index.set_names(["datetime", "instrument"])
    return frame.sort_index()


def normalize_grid(path: Path) -> pd.MultiIndex:
    frame = pd.read_parquet(path)
    if isinstance(frame.index, pd.MultiIndex) and frame.index.nlevels == 2:
        index = frame.index
    elif {"datetime", "instrument"}.issubset(frame.columns):
        index = frame.set_index(["datetime", "instrument"]).index
    else:
        raise RuntimeError("eligible grid has no datetime/instrument identity")
    index = index.set_names(["datetime", "instrument"])
    if len(index) != 374591 or index.has_duplicates or not index.is_monotonic_increasing:
        raise RuntimeError("eligible grid row identity invalid")
    return index


def normalize_label(value: Any, index: pd.MultiIndex) -> pd.Series:
    if isinstance(value, pd.DataFrame) and value.shape[1] == 1:
        value = value.iloc[:, 0]
    if not isinstance(value, pd.Series):
        raise TypeError("unsupported label object")
    value.index = value.index.set_names(["datetime", "instrument"])
    result = value.reindex(index).rename("label")
    if result.isna().any() or not np.isfinite(result.to_numpy(dtype=float)).all():
        raise RuntimeError("label is missing or non-finite on frozen population")
    return result


def verify_qualification(report: pd.DataFrame) -> dict[str, Any]:
    expected = read_json(QUALIFICATION)
    rows: list[dict[str, Any]] = []
    for session, row in report.iterrows():
        for name in row["inactive_components"]:
            rows.append({"candidate_id": name, "datetime": pd.Timestamp(session).strftime("%Y-%m-%d"), "inactive_exact_constant": True})
    observed_set = {(row["candidate_id"], row["datetime"]) for row in rows}
    expected_set = {(row["candidate_id"], row["datetime"]) for row in expected["qualification_rows"]}
    distribution = {str(key): int(value) for key, value in report["active_component_count"].value_counts().sort_index().items()}
    if observed_set != expected_set or distribution != expected["active_component_count_distribution"]:
        raise RuntimeError("active-component qualification differs from frozen input-contract semantics")
    return {
        "master_candidate_count": 17,
        "minimum_active_component_count": int(report["active_component_count"].min()),
        "maximum_active_component_count": int(report["active_component_count"].max()),
        "active_component_count_distribution": distribution,
        "inactive_candidate_session_count": len(rows),
        "qualification_rows": [
            {**row, "candidate_id": CANDIDATE_IDS[row["candidate_id"]]} for row in rows
        ],
    }


def rank_ic_series(prediction: pd.Series, label: pd.Series) -> pd.Series:
    from qlib.contrib.eva.alpha import calc_ic

    _, rank_ic = calc_ic(prediction, label, dropna=False)
    if len(rank_ic) != 751 or rank_ic.isna().any() or not np.isfinite(rank_ic).all():
        raise RuntimeError("Qlib RankIC result is incomplete")
    return rank_ic.rename("rank_ic")


def run_portfolio(prediction: pd.Series, output: Path) -> dict[str, Any]:
    from qlib.backtest import backtest_loop, get_exchange
    from qlib.backtest.account import Account
    from qlib.backtest.executor import SimulatorExecutor
    from qlib.backtest.utils import CommonInfrastructure
    from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy

    account = Account(init_cash=100_000_000, benchmark_config={"benchmark": None})
    exchange = get_exchange(
        freq="day", start_time="2022-01-03", end_time="2024-12-27", codes="all",
        limit_threshold=0.095, deal_price="close", open_cost=0.0005,
        close_cost=0.0015, min_cost=5,
    )
    common = CommonInfrastructure(trade_account=account, trade_exchange=exchange)
    strategy = TopkDropoutStrategy(signal=prediction, topk=30, n_drop=3)
    executor = SimulatorExecutor(time_per_step="day", generate_portfolio_metrics=True)
    strategy.reset_common_infra(common)
    executor.reset_common_infra(common)
    portfolio_metrics, _ = backtest_loop("2022-01-03", "2024-12-27", strategy, executor)
    report, positions = portfolio_metrics["1day"]
    if report.empty or not {"return", "cost", "turnover"}.issubset(report.columns):
        raise RuntimeError("Qlib portfolio report is incomplete")
    report_path = output / "portfolio" / "ensemble-report-normal-1day.pkl"
    positions_path = output / "portfolio" / "ensemble-positions-normal-1day.pkl"
    report.to_pickle(report_path)
    pd.to_pickle(positions, positions_path)
    return {
        "executed": True, "report_rows": len(report),
        "report_sha256": sha256(report_path), "positions_sha256": sha256(positions_path),
        "topk": 30, "n_drop": 3, "account": 100_000_000,
    }


def seal_failure(output: Path, exc: BaseException) -> None:
    write_json(output / "failure.json", {
        "failed_at_utc": utc_now(), "exception_type": type(exc).__name__,
        "exception": str(exc), "traceback": traceback.format_exc(),
        "real_outcome_access_started": True,
    })
    write_json(output / "final-result.json", {
        "result_classification": "STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE",
        "reason": "POST_OUTCOME_REQUIRED_METHOD_OR_INTEGRITY_FAILURE",
        "real_outcome_access_started": True, "real_outcome_execution_attempt_count": 1,
        "pristine_oos": False, "p2_certification_evidence": False,
        "p7_dynamic_roster_evidence": False, "p7_exit_condition_evidence": False,
        "production_authorization": False, "independent_alpha_family_count": 1,
        "p2_v2_sealed_oos_accessed": False,
    })
    seal_checksums(output)


def seal_checksums(output: Path) -> None:
    files = sorted(path for path in output.rglob("*") if path.is_file() and path.name != "checksums.json")
    write_json(output / "checksums.json", {
        str(path.relative_to(output)).replace("\\", "/"): sha256(path) for path in files
    }, replace=True)


def execute(args: argparse.Namespace) -> None:
    output, repo = args.output, args.repo.resolve()
    os.chdir(repo)
    manifest_path = output / "attempt-manifest.json"
    if not manifest_path.is_file() or (output / "outcome-access-started.json").exists():
        raise RuntimeError("one-shot execution is not eligible")
    manifest = read_json(manifest_path)
    if manifest["status"] != "PASS" or manifest["protocol_sha256"] != PROTOCOL_SHA:
        raise RuntimeError("pre-outcome manifest is not valid")
    write_json(output / "outcome-access-started.json", {
        "real_outcome_access_started": True, "real_outcome_execution_attempt_count": 1,
        "started_at_utc": utc_now(), "protocol_sha256": PROTOCOL_SHA,
    })
    manifest.update(phase="ONE_REAL_OUTCOME_EXECUTION", real_outcome_access_started=True,
                    real_outcome_execution_attempt_count=1, outcome_access_started_at_utc=utc_now())
    write_json(manifest_path, manifest, replace=True)

    try:
        derived = read_json(DERIVED_MANIFEST)
        index = normalize_grid(Path(derived["grid_path"]))
        predictions: dict[str, pd.DataFrame] = {}
        for name in sorted(CANDIDATE_IDS):
            frame = normalize_frame(pd.read_pickle(Path(derived["component_artifacts"][name]["path"])), name)
            if not frame.index.equals(index):
                raise RuntimeError(f"{name}: frozen population mismatch")
            predictions[name] = frame
        control = normalize_frame(pd.read_pickle(Path(derived["component_artifacts"]["control"]["path"])), "control")
        if not control.index.equals(index):
            raise RuntimeError("control: frozen population mismatch")
        label_path = Path(manifest["label_path"])
        label = normalize_label(pd.read_pickle(label_path), index)

        router = load_module(repo / "30-research-system/qlib/p7-native-ensemble/session_local_router.py", "p7_session_router_execution")
        ensemble, qualification = router.combine_session_local_nonconstant(predictions)
        qualification_evidence = verify_qualification(qualification)
        ensemble_path = output / "ensemble-prediction.pkl"
        ensemble.to_pickle(ensemble_path)
        active_path = output / "active-component-report.json"
        write_json(active_path, qualification_evidence)

        rank_columns: dict[str, pd.Series] = {
            "STATIC_17_ENSEMBLE": rank_ic_series(ensemble["score"], label),
            "OLS_ALPHA158_CONTROL": rank_ic_series(control["score"], label),
        }
        for name, frame in predictions.items():
            rank_columns[CANDIDATE_IDS[name]] = rank_ic_series(frame["score"], label)
        rank = pd.concat(rank_columns, axis=1)
        rank.index.name = "datetime"
        rank["ENSEMBLE_MINUS_OLS"] = rank["STATIC_17_ENSEMBLE"] - rank["OLS_ALPHA158_CONTROL"]
        rank_path = output / "daily-rank-ic.pkl"
        rank.to_pickle(rank_path)
        rank.to_csv(output / "daily-rank-ic.csv", lineterminator="\n", float_format="%.17g")
        component_summary = {
            column: {
                "mean_daily_rank_ic": float(rank[column].mean()),
                "median_daily_rank_ic": float(rank[column].median()),
                "positive_session_fraction": float((rank[column] > 0).mean()),
                "valid_session_count": int(rank[column].notna().sum()),
            }
            for column in CANDIDATE_IDS.values()
        }
        write_json(output / "component-summaries.json", component_summary)

        command = [str(STATS_PYTHON), str(repo / Path(__file__).relative_to(repo)), "statistics",
                   "--repo", str(repo), "--output", str(output)]
        subprocess.run(command, check=True)
        stats = read_json(output / "statistics-result.json")

        initialize_qlib()
        portfolio = run_portfolio(ensemble["score"], output)
        write_json(output / "portfolio-summary.json", portfolio)

        gates = {
            "full_period_mean_delta": float(rank["ENSEMBLE_MINUS_OLS"].mean()) > 0,
            "spa": stats["spa"]["consistent"] <= 0.05,
            "walkforward_positive_fraction": stats["walkforward"]["positive_fraction"] >= 0.6,
            "walkforward_median": stats["walkforward"]["median_mean_delta"] > 0,
            "cpcv_positive_fraction": stats["cpcv"]["positive_fraction"] >= 0.6,
            "cpcv_median": stats["cpcv"]["median_mean_delta"] > 0,
        }
        classification = (
            "STATIC_ENSEMBLE_RESEARCH_SUPPORTIVE"
            if all(gates.values()) else "STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE"
        )
        primary = {
            "ensemble_mean_rank_ic": float(rank["STATIC_17_ENSEMBLE"].mean()),
            "ols_mean_rank_ic": float(rank["OLS_ALPHA158_CONTROL"].mean()),
            "primary_mean_rank_ic_delta": float(rank["ENSEMBLE_MINUS_OLS"].mean()),
            "session_count": len(rank), "gates": gates,
        }
        write_json(output / "primary-summary.json", primary)

        import mlflow

        mlflow.set_tracking_uri("sqlite:///" + str(output / "mlflow" / "mlflow.db"))
        mlflow.set_experiment("p7_historical_static_ensemble_research_execution_001")
        with mlflow.start_run(run_name="frozen-static-17-vs-ols") as run:
            mlflow.log_params({"protocol_sha256": PROTOCOL_SHA, "candidate_count": 17, "control": "OLS_ALPHA158"})
            mlflow.log_metrics({"ensemble_mean_rank_ic": primary["ensemble_mean_rank_ic"],
                                "ols_mean_rank_ic": primary["ols_mean_rank_ic"],
                                "mean_rank_ic_delta": primary["primary_mean_rank_ic_delta"]})
            mlflow_run_id = run.info.run_id
        result = {
            "task": TASK, "result_classification": classification, "completed_at_utc": utc_now(),
            "protocol_sha256": PROTOCOL_SHA, "input_contract_sha256": INPUT_CONTRACT_SHA,
            "population_index_sha256": POPULATION_SHA, "real_outcome_access_started": True,
            "real_outcome_execution_attempt_count": 1, "ensemble_prediction_sha256": sha256(ensemble_path),
            "active_component_report_sha256": sha256(active_path), "daily_rank_ic_sha256": sha256(rank_path),
            "primary": primary, "statistics": stats, "portfolio": portfolio, "mlflow_run_id": mlflow_run_id,
            "pristine_oos": False, "p2_certification_evidence": False,
            "p7_dynamic_roster_evidence": False, "p7_exit_condition_evidence": False,
            "production_authorization": False, "independent_alpha_family_count": 1,
            "model_training_count": 0, "model_refit_count": 0, "prediction_generation_count": 0,
            "p2_v2_sealed_oos_accessed": False, "p2_v2_cohort_modified": False,
            "aq_new_generic_engine_count": 0,
        }
        write_json(output / "final-result.json", result)
        seal_checksums(output)
        print(json.dumps(result, sort_keys=True))
    except BaseException as exc:
        seal_failure(output, exc)
        raise


def statistics(args: argparse.Namespace) -> None:
    import arch
    import skfolio
    from arch.bootstrap import MCS, SPA
    from skfolio.model_selection import CombinatorialPurgedCV, WalkForward

    if arch.__version__ != "8.0.0" or skfolio.__version__ != "1.0.6":
        raise RuntimeError("statistics runtime identity mismatch")
    frame = pd.read_pickle(args.output / "daily-rank-ic.pkl")
    delta = frame["ENSEMBLE_MINUS_OLS"]
    wf_pairs = list(WalkForward(test_size=63, train_size=504, purged_size=2,
                                expand_train=False, reduce_test=False).split(frame.to_numpy()))
    cpcv_pairs = list(CombinatorialPurgedCV(n_folds=10, n_test_folds=2,
                                            purged_size=2, embargo_size=2).split(frame.to_numpy()))
    if len(wf_pairs) != 3 or len(cpcv_pairs) != 45:
        raise RuntimeError("frozen temporal split count mismatch")
    wf_values = [float(delta.iloc[test].mean()) for _, test in wf_pairs]
    cpcv_values = [float(delta.iloc[np.sort(np.concatenate(groups))].mean()) for _, groups in cpcv_pairs]
    spa = SPA(-frame["OLS_ALPHA158_CONTROL"], -frame[["STATIC_17_ENSEMBLE"]],
              block_size=10, reps=5000, bootstrap="stationary", studentize=True,
              nested=False, seed=20260913)
    spa.compute()
    component_columns = list(CANDIDATE_IDS.values())
    mcs_columns = ["STATIC_17_ENSEMBLE"] + component_columns
    mcs = MCS(-frame[mcs_columns], size=0.05, reps=5000, block_size=10,
              method="R", bootstrap="stationary", seed=20260913)
    mcs.compute()
    result = {
        "arch_version": arch.__version__, "skfolio_version": skfolio.__version__,
        "spa": {key: float(spa.pvalues.loc[key]) for key in ("lower", "consistent", "upper")},
        "walkforward": {
            "fold_count": len(wf_values), "fold_mean_deltas": wf_values,
            "positive_count": sum(value > 0 for value in wf_values),
            "positive_fraction": float(np.mean(np.asarray(wf_values) > 0)),
            "median_mean_delta": float(np.median(wf_values)),
        },
        "cpcv": {
            "split_count": len(cpcv_values), "split_mean_deltas": cpcv_values,
            "positive_count": sum(value > 0 for value in cpcv_values),
            "positive_fraction": float(np.mean(np.asarray(cpcv_values) > 0)),
            "median_mean_delta": float(np.median(cpcv_values)),
        },
        "mcs": {
            "included_models": [str(value) for value in mcs.included],
            "excluded_models": [str(value) for value in mcs.excluded],
            "pvalues": {str(key): float(value) for key, value in mcs.pvalues.items()},
            "role": "DESCRIPTIVE_ONLY_NO_PRIMARY_GATE_NO_SELECTION",
        },
    }
    write_json(args.output / "statistics-result.json", result)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("mode", choices=("preflight", "execute", "statistics"))
    result.add_argument("--repo", required=True, type=Path)
    result.add_argument("--output", type=Path, default=OUTPUT_ROOT)
    return result


def main() -> None:
    args = parser().parse_args()
    {"preflight": preflight, "execute": execute, "statistics": statistics}[args.mode](args)


if __name__ == "__main__":
    main()
