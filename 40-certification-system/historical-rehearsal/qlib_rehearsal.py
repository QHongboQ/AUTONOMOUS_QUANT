"""Execute the frozen Qlib-owned portion of P2 Protocol V1 exactly once."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd


QLIB_VERSION = "0.9.8.dev26"
QLIB_SOURCE_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"
PROTOCOL_SHA = "a9aed881c229f9eb7f85fa23b866168a55dc9c00be3c3b178d91a4af20451dfb"
PRIMARY_CONFIG_SHA = "c6e6c4882adeb053d58e91b27d7d796fd9886dc1946d1d0540d5d9637f42ccaf"
CONTROL_CONFIG_SHA = "b9a92537a9737ce909284e77e583ad20c0a3d2b18f795271d85db6c5ba5eafc1"
TRAIN = ("2015-04-01", "2019-12-31")
VALID = ("2020-01-01", "2021-12-31")
TEST = ("2022-01-03", "2024-12-31")
STRATEGIES = {
    "LGB_50_5": ("primary", 50, 5),
    "LGB_30_3": ("primary", 30, 3),
    "LGB_100_10": ("primary", 100, 10),
    "LGB_25_3": ("primary", 25, 3),
    "LGB_35_3": ("primary", 35, 3),
    "LGB_30_2": ("primary", 30, 2),
    "LGB_30_4": ("primary", 30, 4),
    "LINEAR_50_5": ("control", 50, 5),
}
COSTS = {
    "BASE": (0.0005, 0.0015),
    "TWO_X": (0.0010, 0.0030),
    "THREE_X": (0.0015, 0.0045),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_lf_sha256(path: Path) -> str:
    payload = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def require_hash(path: Path, expected: str, canonical: bool = False) -> None:
    actual = canonical_lf_sha256(path) if canonical else sha256(path)
    if actual != expected:
        raise RuntimeError(f"identity mismatch for {path}: {actual} != {expected}")


def create_handler(linear: bool):
    from aq_qlib_handoff.qlib_config import RaggedAlpha158, current_close_filter

    kwargs = {
        "instruments": "p2_pit",
        "start_time": "2015-01-02",
        "end_time": "2024-12-31",
        "fit_start_time": TRAIN[0],
        "fit_end_time": TRAIN[1],
        "filter_pipe": [current_close_filter()],
    }
    if linear:
        kwargs.update(
            infer_processors=[
                {
                    "class": "RobustZScoreNorm",
                    "kwargs": {"fields_group": "feature", "clip_outlier": True},
                },
                {"class": "Fillna", "kwargs": {"fields_group": "feature"}},
            ],
            learn_processors=[
                {"class": "DropnaLabel"},
                {"class": "CSRankNorm", "kwargs": {"fields_group": "label"}},
            ],
        )
    return RaggedAlpha158(**kwargs)


def create_dataset(linear: bool):
    from qlib.data.dataset import DatasetH

    return DatasetH(
        handler=create_handler(linear),
        segments={"train": TRAIN, "valid": VALID, "test": TEST},
    )


def train_and_predict(kind: str, output: Path):
    from qlib.contrib.model.gbdt import LGBModel
    from qlib.contrib.model.linear import LinearModel
    from qlib.workflow import R
    from qlib.workflow.record_temp import SigAnaRecord, SignalRecord

    linear = kind == "control"
    dataset = create_dataset(linear)
    if linear:
        model = LinearModel(estimator="ols")
        experiment = "p2_certification_historical_rehearsal_linear"
        recorder_name = "LINEAR_50_5_CONTROL"
    else:
        model = LGBModel(
            loss="mse",
            colsample_bytree=0.8879,
            learning_rate=0.2,
            subsample=0.8789,
            lambda_l1=205.6999,
            lambda_l2=580.9768,
            max_depth=8,
            num_leaves=210,
            num_threads=8,
        )
        experiment = "p2_certification_historical_rehearsal_lgb"
        recorder_name = "LGB_30_3_PRIMARY_MODEL"

    print(f"TRAIN_START {kind}", flush=True)
    with R.start(experiment_name=experiment, recorder_name=recorder_name):
        recorder = R.get_recorder()
        recorder.log_params(
            task="AUTONOMOUS_QUANT_P2_CERTIFICATION_HISTORICAL_REHEARSAL_001",
            protocol_sha256=PROTOCOL_SHA,
            model_kind=kind,
            config_sha256=CONTROL_CONFIG_SHA if linear else PRIMARY_CONFIG_SHA,
            train_interval="/".join(TRAIN),
            valid_interval="/".join(VALID),
            test_interval="/".join(TEST),
            dataset="P2_FROZEN_RAGGED_PANEL",
        )
        model.fit(dataset)
        SignalRecord(model=model, dataset=dataset, recorder=recorder).generate()
        SigAnaRecord(recorder=recorder, ana_long_short=False, ann_scaler=252).generate()
        prediction = recorder.load_object("pred.pkl")
        ic = recorder.load_object("sig_analysis/ic.pkl")
        ric = recorder.load_object("sig_analysis/ric.pkl")
        recorder_id = recorder.id

    if isinstance(prediction, pd.DataFrame):
        if prediction.shape[1] != 1:
            raise RuntimeError(f"unexpected {kind} prediction columns: {prediction.columns}")
        prediction = prediction.iloc[:, 0]
    prediction = prediction.rename("score").sort_index()
    if prediction.empty or not np.isfinite(prediction.to_numpy(dtype=float)).all():
        raise RuntimeError(f"{kind} predictions are empty or non-finite")
    prediction_path = output / f"{kind}_pred.pkl"
    prediction.to_pickle(prediction_path)
    print(f"TRAIN_FINISH {kind} rows={len(prediction)} recorder={recorder_id}", flush=True)
    del model, dataset
    gc.collect()
    signal_metrics = {
        "ic": float(ic.mean()),
        "icir": float(ic.mean() / ic.std()),
        "rank_ic": float(ric.mean()),
        "rank_icir": float(ric.mean() / ric.std()),
    }
    return prediction, recorder_id, prediction_path, signal_metrics


def run_backtest(strategy_id: str, prediction: pd.Series, topk: int, n_drop: int,
                 scenario: str, costs: tuple[float, float], output: Path) -> dict[str, object]:
    from qlib.backtest import backtest_loop, get_exchange
    from qlib.backtest.account import Account
    from qlib.backtest.executor import SimulatorExecutor
    from qlib.backtest.utils import CommonInfrastructure
    from qlib.contrib.evaluate import risk_analysis
    from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy

    run_id = f"{strategy_id}__{scenario}"
    print(f"BACKTEST_START {run_id}", flush=True)
    account = Account(
        init_cash=100_000_000,
        benchmark_config={"benchmark": None},
    )
    exchange = get_exchange(
        freq="day", start_time=TEST[0], end_time=TEST[1], codes="all",
        limit_threshold=0.095, deal_price="close",
        open_cost=costs[0], close_cost=costs[1], min_cost=5,
    )
    common = CommonInfrastructure(trade_account=account, trade_exchange=exchange)
    strategy = TopkDropoutStrategy(signal=prediction, topk=topk, n_drop=n_drop)
    strategy.reset_common_infra(common)
    executor = SimulatorExecutor(time_per_step="day", generate_portfolio_metrics=True)
    executor.reset_common_infra(common)
    portfolio_metrics, _ = backtest_loop(TEST[0], TEST[1], strategy, executor)
    report, positions = portfolio_metrics["1day"]
    required = {"return", "cost", "turnover"}
    if report.empty or not required.issubset(report.columns):
        raise RuntimeError(f"Qlib report for {run_id} lacks {sorted(required)}")
    net = (report["return"] - report["cost"]).rename(run_id)
    if not np.isfinite(net.to_numpy(dtype=float)).all():
        raise RuntimeError(f"non-finite Qlib net returns for {run_id}")
    report_path = output / "portfolio" / f"{run_id}_report_normal_1day.pkl"
    positions_path = output / "portfolio" / f"{run_id}_positions_normal_1day.pkl"
    report.to_pickle(report_path)
    pd.to_pickle(positions, positions_path)
    analysis = risk_analysis(net, freq="day")
    analysis_values = {
        str(index): float(value)
        for index, value in analysis.iloc[:, 0].items()
    }
    print(f"BACKTEST_FINISH {run_id} rows={len(report)}", flush=True)
    return {
        "run_id": run_id,
        "strategy_id": strategy_id,
        "scenario": scenario,
        "topk": topk,
        "n_drop": n_drop,
        "open_cost": costs[0],
        "close_cost": costs[1],
        "benchmark": None,
        "report_rows": len(report),
        "report_sha256": sha256(report_path),
        "positions_sha256": sha256(positions_path),
        "net": net,
        "turnover_mean": float(report["turnover"].mean()),
        "cost_sum": float(report["cost"].sum()),
        "risk_analysis": analysis_values,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--provider", required=True, type=Path)
    parser.add_argument("--provider-report", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--activation", required=True, type=Path)
    parser.add_argument("--primary-config", required=True, type=Path)
    parser.add_argument("--control-config", required=True, type=Path)
    parser.add_argument("--qlib-source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--resume-after-benchmark-wrapper-failure", action="store_true")
    args = parser.parse_args()

    if args.output.exists() and not args.resume_after_benchmark_wrapper_failure:
        raise FileExistsError(args.output)
    if args.resume_after_benchmark_wrapper_failure:
        required_resume = [
            args.output / "primary_pred.pkl",
            args.output / "control_pred.pkl",
            args.output / "mlflow" / "mlflow.db",
        ]
        if not all(path.is_file() for path in required_resume):
            raise RuntimeError("incomplete frozen model checkpoint for backtest resume")
        if list((args.output / "portfolio").glob("*.pkl")):
            raise RuntimeError("a Qlib portfolio run already exists; refusing duplicate execution")
    else:
        args.output.mkdir(parents=True)
        (args.output / "portfolio").mkdir()
        (args.output / "mlflow").mkdir()
    os.chdir(args.output)

    require_hash(args.protocol, PROTOCOL_SHA, canonical=True)
    require_hash(args.primary_config, PRIMARY_CONFIG_SHA, canonical=True)
    require_hash(args.control_config, CONTROL_CONFIG_SHA, canonical=True)
    activation = json.loads(args.activation.read_text(encoding="utf-8"))
    provider_report = json.loads(args.provider_report.read_text(encoding="utf-8"))
    if activation["protocol_sha256"] != PROTOCOL_SHA:
        raise RuntimeError("activation does not bind Protocol V1")
    expected_provider = {
        "history_start": "2015-01-02",
        "history_end": "2024-12-31",
        "unique_security_identities": 730,
        "instrument_episodes": 745,
        "total_member_session_rows": 1_267_963,
        "observed_safe_rows": 1_224_788,
        "masked_rows": 43_175,
    }
    for key, value in expected_provider.items():
        if provider_report.get(key) != value:
            raise RuntimeError(f"provider report mismatch: {key}")

    source_sha = subprocess.check_output(
        ("git", "-C", str(args.qlib_source), "rev-parse", "HEAD"), text=True,
    ).strip()
    if source_sha != QLIB_SOURCE_SHA:
        raise RuntimeError(f"unexpected Qlib source: {source_sha}")

    sys.path.insert(0, str(args.repo / "30-research-system" / "qlib" / "dataset-adapter"))
    import mlflow
    import qlib
    from qlib.data import D
    from qlib.workflow import R

    if qlib.__version__ != QLIB_VERSION:
        raise RuntimeError(f"unexpected Qlib version: {qlib.__version__}")
    qlib.init(
        provider_uri=str(args.provider),
        region="us",
        expression_cache=None,
        dataset_cache=None,
        exp_manager={
            "class": "MLflowExpManager",
            "module_path": "qlib.workflow.expm",
            "kwargs": {
                "uri": "sqlite:///" + str(args.output / "mlflow" / "mlflow.db"),
                "default_exp_name": "Experiment",
            },
        },
    )
    ranges = D.list_instruments(
        D.instruments(market="p2_pit"),
        start_time="2015-01-02",
        end_time="2024-12-31",
        freq="day",
        as_list=False,
    )
    if len(ranges) != 730 or sum(len(value) for value in ranges.values()) != 745:
        raise RuntimeError("Qlib provider instrument/range accounting mismatch")

    if args.resume_after_benchmark_wrapper_failure:
        primary_path = args.output / "primary_pred.pkl"
        control_path = args.output / "control_pred.pkl"
        primary = pd.read_pickle(primary_path)
        control = pd.read_pickle(control_path)

        def recorder_evidence(experiment_name: str):
            recorders = R.get_exp(experiment_name=experiment_name).list_recorders(rtype="list")
            if len(recorders) != 1:
                raise RuntimeError(f"unexpected recorder count for {experiment_name}: {len(recorders)}")
            recorder = recorders[0]
            ic = recorder.load_object("sig_analysis/ic.pkl")
            ric = recorder.load_object("sig_analysis/ric.pkl")
            return recorder.id, {
                "ic": float(ic.mean()), "icir": float(ic.mean() / ic.std()),
                "rank_ic": float(ric.mean()), "rank_icir": float(ric.mean() / ric.std()),
            }

        primary_recorder, primary_signal_metrics = recorder_evidence(
            "p2_certification_historical_rehearsal_lgb",
        )
        control_recorder, control_signal_metrics = recorder_evidence(
            "p2_certification_historical_rehearsal_linear",
        )
        print("RESUME_FROZEN_MODEL_PREDICTIONS", flush=True)
    else:
        primary, primary_recorder, primary_path, primary_signal_metrics = train_and_predict("primary", args.output)
        control, control_recorder, control_path, control_signal_metrics = train_and_predict("control", args.output)

    runs: list[dict[str, object]] = []
    for strategy_id, (prediction_kind, topk, n_drop) in STRATEGIES.items():
        pred = primary if prediction_kind == "primary" else control
        runs.append(run_backtest(strategy_id, pred, topk, n_drop, "BASE", COSTS["BASE"], args.output))
    for scenario in ("TWO_X", "THREE_X"):
        for strategy_id in ("LGB_30_3", "LINEAR_50_5"):
            prediction_kind, topk, n_drop = STRATEGIES[strategy_id]
            pred = primary if prediction_kind == "primary" else control
            runs.append(run_backtest(strategy_id, pred, topk, n_drop, scenario, COSTS[scenario], args.output))

    daily = pd.concat([run.pop("net") for run in runs], axis=1, join="inner").sort_index()
    if daily.index.min().strftime("%Y-%m-%d") != TEST[0] or daily.index.max().strftime("%Y-%m-%d") != TEST[1]:
        raise RuntimeError("aligned Qlib daily-return interval mismatch")
    daily.index.name = "date"
    daily_path = args.output / "daily_net_returns.csv"
    daily.to_csv(daily_path, lineterminator="\n", float_format="%.17g")

    manifest = {
        "task": "AUTONOMOUS_QUANT_P2_CERTIFICATION_HISTORICAL_REHEARSAL_001",
        "protocol_sha256": PROTOCOL_SHA,
        "activation_sha256_canonical_lf": canonical_lf_sha256(args.activation),
        "provider_report_sha256": sha256(args.provider_report),
        "primary_config_sha256_canonical_lf": PRIMARY_CONFIG_SHA,
        "control_config_sha256_canonical_lf": CONTROL_CONFIG_SHA,
        "qlib_version": qlib.__version__,
        "qlib_source_sha": source_sha,
        "mlflow_version": mlflow.__version__,
        "primary_recorder_id": primary_recorder,
        "control_recorder_id": control_recorder,
        "primary_prediction_rows": len(primary),
        "control_prediction_rows": len(control),
        "primary_prediction_sha256": sha256(primary_path),
        "control_prediction_sha256": sha256(control_path),
        "primary_signal_analysis": primary_signal_metrics,
        "control_signal_analysis": control_signal_metrics,
        "base_strategy_runs": 8,
        "cost_stress_additional_runs": 4,
        "daily_return_rows": len(daily),
        "daily_return_sha256": sha256(daily_path),
        "runs": runs,
        "benchmark": None,
        "benchmark_none_public_api_path": "ACCOUNT_BENCHMARK_CONFIG_PLUS_QLIB_BACKTEST_LOOP",
        "resolved_configuration_note": "backtest_daily wrapper converted None to an empty config whose legacy default is SH000300; Qlib Account benchmark_config with explicit benchmark=None preserves the frozen no-benchmark policy",
        "train": list(TRAIN),
        "valid": list(VALID),
        "test": list(TEST),
    }
    manifest_path = args.output / "qlib-rehearsal-report.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with R.start(
        experiment_name="p2_certification_historical_rehearsal_evidence",
        recorder_name="FROZEN_PROTOCOL_V1_EVIDENCE",
    ):
        recorder = R.get_recorder()
        recorder.log_params(
            protocol_sha256=PROTOCOL_SHA,
            activation_sha256=canonical_lf_sha256(args.activation),
            provider_report_sha256=sha256(args.provider_report),
            primary_prediction_sha256=sha256(primary_path),
            control_prediction_sha256=sha256(control_path),
            daily_return_sha256=sha256(daily_path),
            strategy_ids=";".join(STRATEGIES),
            cost_scenarios="BASE;TWO_X;THREE_X",
            benchmark="NONE",
        )
        recorder.save_objects(local_path=str(manifest_path), artifact_path="rehearsal")
        recorder.save_objects(local_path=str(daily_path), artifact_path="rehearsal")
        evidence_recorder_id = recorder.id
    manifest["evidence_recorder_id"] = evidence_recorder_id
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in manifest.items() if key != "runs"}, sort_keys=True))


if __name__ == "__main__":
    main()
