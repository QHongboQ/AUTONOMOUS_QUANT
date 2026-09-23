"""Execute the frozen P5 H1 comparison through its upstream owners."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

CONTROL_MANIFEST_SHA256 = "7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463"
CONTROL_DATASET_IDENTITY = "P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135"
P2_REPORT_SHA256 = "eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142"
P5_PARQUET_SHA256 = "0e688195eca1d58d548666520229b701432ad9a91438558346b7897a7f9d257b"
QLIB_VERSION = "0.9.8.dev26"
QLIB_SOURCE_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"
LIGHTGBM_VERSION = "4.7.0"
SKFOlIO_VERSION = "1.0.6"
ARCH_VERSION = "8.0.0"
TRAIN = ("2015-04-01", "2019-12-31")
VALID = ("2020-01-01", "2021-12-31")
TEST = ("2022-01-03", "2024-12-31")
P5_FEATURES = (
    "Revenue", "NetIncome", "Assets", "Liabilities", "CommonEquity",
    "NetCashFromOperatingActivities", "CashAndCashEquivalents",
    "CurrentAssetsTotal", "CurrentLiabilitiesTotal", "LongTermDebt",
)
MODEL_CONFIG = {
    "loss": "mse", "colsample_bytree": 0.8879, "learning_rate": 0.2,
    "subsample": 0.8789, "lambda_l1": 205.6999, "lambda_l2": 580.9768,
    "max_depth": 8, "num_leaves": 210, "early_stopping_rounds": 50,
    "num_boost_round": 1000, "device_type": "cpu", "deterministic": True,
    "force_col_wise": True, "force_row_wise": False, "num_threads": 8,
    "seed": 20260913, "data_random_seed": 1, "feature_fraction_seed": 2,
    "bagging_seed": 3, "drop_seed": 4, "objective_seed": 5,
    "extra_seed": 6, "use_missing": True, "zero_as_missing": False,
    "bagging_freq": 0,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_crosswalk(projection: pd.DataFrame, episode_map_path: Path) -> pd.DataFrame:
    """Bind the versioned P2 instrument ranges to current P1 episode IDs."""
    episodes = projection.groupby(
        ["episode_id", "historical_ticker", "identity_excluded"], as_index=False,
    ).agg(p5_start=("session", "min"), p5_end=("session", "max"))
    p2 = pd.DataFrame(
        [json.loads(line) for line in episode_map_path.read_text(encoding="utf-8").splitlines()]
    ).rename(columns={
        "episode_id": "p2_episode_id", "instrument": "p2_instrument",
        "start": "p2_start", "end_inclusive": "p2_end",
    })
    p2["p2_start"] = pd.to_datetime(p2["p2_start"])
    p2["p2_end"] = pd.to_datetime(p2["p2_end"])
    candidates = p2.merge(episodes, on="historical_ticker", how="inner")
    crosswalk = candidates[
        (candidates["p5_end"] >= candidates["p2_start"])
        & (candidates["p5_start"] <= candidates["p2_end"])
    ].copy()
    counts = crosswalk.groupby("p2_episode_id").size()
    if len(p2) != 745 or len(crosswalk) != len(p2) or not counts.eq(1).all():
        raise RuntimeError("P2/P5 episode crosswalk is incomplete or ambiguous")
    if crosswalk.duplicated(["p2_instrument", "p2_start", "p2_end"]).any():
        raise RuntimeError("duplicate P2 range in episode crosswalk")
    return crosswalk.rename(columns={"episode_id": "p5_episode_id"})[[
        "p2_episode_id", "p2_instrument", "p2_start", "p2_end",
        "p5_episode_id", "historical_ticker", "p5_start", "p5_end",
        "identity_excluded",
    ]].sort_values(["p2_instrument", "p2_start"], ignore_index=True)


def project_index(frame: pd.DataFrame, crosswalk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Replace P2 instrument IDs with the unique date-valid P1 episode ID."""
    keys = frame.index.to_frame(index=False).rename(columns={"instrument": "p2_instrument"})
    keys["_row"] = np.arange(len(keys), dtype=np.int64)
    matched = keys.merge(crosswalk, on="p2_instrument", how="left")
    matched = matched[
        (matched["datetime"] >= matched["p2_start"])
        & (matched["datetime"] <= matched["p2_end"])
    ].sort_values("_row")
    if len(matched) != len(frame) or not np.array_equal(matched["_row"], np.arange(len(frame))):
        raise RuntimeError("Qlib row could not be projected to exactly one P1 episode")
    projected = frame.copy()
    projected.index = pd.MultiIndex.from_arrays(
        [matched["datetime"].to_numpy(), matched["p5_episode_id"].to_numpy()],
        names=["datetime", "instrument"],
    )
    if projected.index.has_duplicates:
        raise RuntimeError("projected P1 episode/session identity is not unique")
    order = np.lexsort((projected.index.get_level_values("instrument"),
                        projected.index.get_level_values("datetime")))
    projected = projected.iloc[order]
    mapped = matched.iloc[order][[
        "datetime", "p5_episode_id", "p2_instrument", "p2_start", "p2_end",
    ]].rename(columns={"p5_episode_id": "instrument"})
    return projected, mapped.reset_index(drop=True)


def control_manifest(config_class) -> tuple[list[str], str]:
    instance = config_class.__new__(config_class)
    expressions, names = instance.get_feature_config()
    manifest = {
        "feature_family": "P2_RAGGED_ALPHA158_OHLCV_157",
        "columns": [
            {"position": index + 1, "name": name, "expression": expression}
            for index, (name, expression) in enumerate(zip(names, expressions))
        ],
    }
    return list(names), canonical_sha256(manifest)


def prepare_calendar(provider: Path, frozen_future: Path, target: Path) -> dict[str, object]:
    source = provider / "calendars" / "day.txt"
    sessions = source.read_text(encoding="utf-8").splitlines()
    future_sessions = frozen_future.read_text(encoding="utf-8").splitlines()
    if future_sessions[:-1] != sessions or len(future_sessions) != len(sessions) + 1:
        raise RuntimeError("frozen future calendar is not the exact one-session extension")
    next_session = future_sessions[-1]
    calendars = target / "calendars"
    calendars.mkdir(parents=True)
    shutil.copyfile(source, calendars / "day.txt")
    shutil.copyfile(frozen_future, calendars / "day_future.txt")
    return {"last_data_session": sessions[-1], "future_session": next_session}


def make_dataset(surface_path: Path, columns: list[str]):
    from qlib.data.dataset import DatasetH
    from qlib.data.dataset.handler import DataHandlerLP
    from qlib.data.dataset.loader import StaticDataLoader

    surface = pd.read_parquet(surface_path, columns=columns + ["__label__"])
    features = surface[columns]
    label = surface[["__label__"]].rename(columns={"__label__": "LABEL0"})
    handler = DataHandlerLP(
        instruments=None, start_time=TRAIN[0], end_time=TEST[1],
        data_loader=StaticDataLoader({"feature": features, "label": label}),
        infer_processors=[], learn_processors=[{"class": "DropnaLabel"}],
    )
    return DatasetH(handler=handler, segments={"train": TRAIN, "valid": VALID, "test": TEST})


def train_surface(surface_id: str, surface_path: Path, columns: list[str], output: Path):
    from qlib.contrib.model.gbdt import LGBModel
    from qlib.workflow import R
    from qlib.workflow.record_temp import SigAnaRecord, SignalRecord

    dataset = make_dataset(surface_path, columns)
    model = LGBModel(**MODEL_CONFIG)
    with R.start(experiment_name="p5_h1_incremental_fundamentals", recorder_name=surface_id):
        recorder = R.get_recorder()
        recorder.log_params(
            task="AUTONOMOUS_QUANT_P5_H1_INCREMENTAL_FUNDAMENTAL_EVALUATION_AND_CLOSEOUT_001",
            surface=surface_id, model_config_sha256=canonical_sha256(MODEL_CONFIG),
            column_count=len(columns), train_range="/".join(TRAIN),
            valid_range="/".join(VALID), test_range="/".join(TEST),
        )
        model.fit(dataset, verbose_eval=20)
        SignalRecord(model=model, dataset=dataset, recorder=recorder).generate()
        SigAnaRecord(recorder=recorder, ana_long_short=False, ann_scaler=252).generate()
        recorder_id = recorder.id
    recorded = R.get_recorder(recorder_id=recorder_id, experiment_name="p5_h1_incremental_fundamentals")
    prediction = recorded.load_object("pred.pkl")
    rank_ic = recorded.load_object("sig_analysis/ric.pkl")
    prediction = prediction.iloc[:, 0] if isinstance(prediction, pd.DataFrame) else prediction
    prediction = prediction.rename("score").sort_index()
    prediction_path = output / f"{surface_id.lower()}-prediction.pkl"
    rank_ic_path = output / f"{surface_id.lower()}-rank-ic.pkl"
    prediction.to_pickle(prediction_path)
    pd.to_pickle(rank_ic, rank_ic_path)
    return {
        "recorder_id": recorder_id, "prediction": prediction,
        "prediction_sha256": sha256(prediction_path), "prediction_rows": len(prediction),
        "rank_ic": float(rank_ic.mean()), "rank_ic_sha256": sha256(rank_ic_path),
        "best_iteration": int(model.model.best_iteration),
    }


def resume_finished_s0(output: Path) -> dict[str, object]:
    """Reuse the one completed S0 recorder after a pre-S1 process loss."""
    import mlflow

    tracking_uri = "sqlite:///" + str(output / "mlflow.db")
    client = mlflow.MlflowClient(tracking_uri=tracking_uri)
    experiments = client.search_experiments(filter_string="name = 'p5_h1_incremental_fundamentals'")
    if len(experiments) != 1:
        raise RuntimeError("cannot identify the completed H1 experiment for bounded resume")
    runs = client.search_runs([experiments[0].experiment_id])
    completed = [
        run for run in runs
        if run.info.status == "FINISHED" and run.data.params.get("surface") == "S0"
    ]
    interrupted_s1 = [
        run for run in runs
        if run.info.status in {"RUNNING", "FAILED"} and run.data.params.get("surface") == "S1"
    ]
    if len(completed) != 1 or len(interrupted_s1) != 1:
        raise RuntimeError("bounded resume requires exactly one finished S0 and one interrupted S1")
    expected_params = {
        "task": "AUTONOMOUS_QUANT_P5_H1_INCREMENTAL_FUNDAMENTAL_EVALUATION_AND_CLOSEOUT_001",
        "surface": "S0", "model_config_sha256": canonical_sha256(MODEL_CONFIG),
        "column_count": "157", "train_range": "/".join(TRAIN),
        "valid_range": "/".join(VALID), "test_range": "/".join(TEST),
    }
    if any(completed[0].data.params.get(key) != value for key, value in expected_params.items()):
        raise RuntimeError("completed S0 recorder identity does not match frozen authority")
    orphan = interrupted_s1[0]
    if orphan.data.metrics or client.list_artifacts(orphan.info.run_id):
        raise RuntimeError("interrupted S1 contains training evidence and cannot be retried")
    if orphan.info.status == "RUNNING":
        client.set_terminated(orphan.info.run_id, status="FAILED")

    prediction_path = output / "s0-prediction.pkl"
    rank_ic_path = output / "s0-rank-ic.pkl"
    artifact_root = Path(completed[0].info.artifact_uri.removeprefix("file://"))
    if not prediction_path.is_file() or not rank_ic_path.is_file():
        raise RuntimeError("completed S0 normalized outputs are absent")
    prediction = pd.read_pickle(prediction_path)
    recorded_prediction = pd.read_pickle(artifact_root / "pred.pkl")
    if isinstance(recorded_prediction, pd.DataFrame):
        recorded_prediction = recorded_prediction.iloc[:, 0]
    recorded_prediction = recorded_prediction.rename("score").sort_index()
    rank_ic = pd.read_pickle(rank_ic_path)
    recorded_rank_ic = pd.read_pickle(artifact_root / "sig_analysis" / "ric.pkl")
    if not prediction.equals(recorded_prediction) or not rank_ic.equals(recorded_rank_ic):
        raise RuntimeError("completed S0 output hashes do not match its finished recorder")
    history = client.get_metric_history(completed[0].info.run_id, "l2.valid")
    if not history:
        raise RuntimeError("completed S0 recorder has no validation history")
    return {
        "recorder_id": completed[0].info.run_id, "prediction": prediction,
        "prediction_sha256": sha256(prediction_path), "prediction_rows": len(prediction),
        "rank_ic": float(rank_ic.mean()), "rank_ic_sha256": sha256(rank_ic_path),
        "best_iteration": int(min(history, key=lambda item: item.value).step + 1),
        "resume_evidence": "FINISHED_S0_REUSED_AFTER_PRE_FIT_S1_PROCESS_LOSS",
    }


def p2_prediction(prediction: pd.Series, crosswalk: pd.DataFrame) -> pd.Series:
    mapping = crosswalk.set_index("p5_episode_id")["p2_instrument"]
    frame = prediction.rename("score").reset_index()
    frame["instrument"] = frame["instrument"].map(mapping)
    if frame["instrument"].isna().any() or frame.duplicated(["datetime", "instrument"]).any():
        raise RuntimeError("prediction cannot be projected uniquely to P2 execution identity")
    return frame.set_index(["instrument", "datetime"])["score"].sort_index()


def backtest(surface_id: str, prediction: pd.Series, output: Path) -> tuple[dict[str, object], pd.Series]:
    from qlib.backtest import backtest_loop, get_exchange
    from qlib.backtest.account import Account
    from qlib.backtest.executor import SimulatorExecutor
    from qlib.backtest.utils import CommonInfrastructure
    from qlib.contrib.evaluate import risk_analysis
    from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy

    account = Account(init_cash=100_000_000, benchmark_config={"benchmark": None})
    exchange = get_exchange(
        freq="day", start_time=TEST[0], end_time=TEST[1], codes="all",
        limit_threshold=0.095, deal_price="close", open_cost=0.0005,
        close_cost=0.0015, min_cost=5,
    )
    common = CommonInfrastructure(trade_account=account, trade_exchange=exchange)
    strategy = TopkDropoutStrategy(signal=prediction, topk=30, n_drop=3)
    strategy.reset_common_infra(common)
    executor = SimulatorExecutor(time_per_step="day", generate_portfolio_metrics=True)
    executor.reset_common_infra(common)
    metrics, _ = backtest_loop(TEST[0], TEST[1], strategy, executor)
    report, positions = metrics["1day"]
    if report.empty or not {"return", "cost", "turnover"}.issubset(report.columns):
        raise RuntimeError(f"incomplete Qlib portfolio evidence for {surface_id}")
    net = (report["return"] - report["cost"]).rename(surface_id)
    report_path = output / f"{surface_id.lower()}-portfolio.pkl"
    positions_path = output / f"{surface_id.lower()}-positions.pkl"
    report.to_pickle(report_path)
    pd.to_pickle(positions, positions_path)
    analysis = risk_analysis(net, freq="day").iloc[:, 0]
    return {
        "topk": 30, "n_drop": 3, "open_cost": 0.0005, "close_cost": 0.0015,
        "min_cost": 5, "benchmark": None, "report_rows": len(report),
        "report_sha256": sha256(report_path), "positions_sha256": sha256(positions_path),
        "turnover_mean": float(report["turnover"].mean()),
        "cost_sum": float(report["cost"].sum()),
        "risk_analysis": {str(key): float(value) for key, value in analysis.items()},
    }, net


def qlib_mode(args: argparse.Namespace) -> None:
    output: Path = args.output
    resume_s0 = output.exists()
    output.mkdir(parents=True, exist_ok=True)
    os.chdir(output)
    sys.path.insert(0, str(args.repo / "30-research-system" / "qlib" / "dataset-adapter"))

    import lightgbm
    import mlflow
    import qlib
    from aq_qlib_handoff.qlib_config import RaggedAlpha158, current_close_filter
    from qlib.data.dataset.handler import DataHandlerLP

    if qlib.__version__ != QLIB_VERSION or lightgbm.__version__ != LIGHTGBM_VERSION:
        raise RuntimeError("Qlib/LightGBM runtime identity mismatch")
    source_sha = subprocess.check_output(
        ("git", "-C", str(args.qlib_source), "rev-parse", "HEAD"), text=True,
    ).strip()
    if source_sha != QLIB_SOURCE_SHA:
        raise RuntimeError("Qlib source identity mismatch")
    if sha256(args.provider_report) != P2_REPORT_SHA256:
        raise RuntimeError("P2 build report identity mismatch")
    p5_manifest = json.loads(args.p5_manifest.read_text(encoding="utf-8"))
    if tuple(p5_manifest["features"]) != P5_FEATURES or p5_manifest["session_rows"] != 1_893_759:
        raise RuntimeError("P5 handoff authority mismatch")
    if p5_manifest["feature_parquet_sha256"] != P5_PARQUET_SHA256 or sha256(args.fundamentals) != P5_PARQUET_SHA256:
        raise RuntimeError("P5 feature parquet identity mismatch")

    control_columns, control_hash = control_manifest(RaggedAlpha158)
    if len(control_columns) != 157 or control_hash != CONTROL_MANIFEST_SHA256:
        raise RuntimeError("frozen CONTROL surface mismatch")
    projection = pd.read_parquet(args.projection_grid)
    if len(projection) != 1_893_759 or int(projection["identity_excluded"].sum()) != 210_966:
        raise RuntimeError("P5 projection accounting mismatch")
    crosswalk = build_crosswalk(projection, args.episode_map)
    if resume_s0:
        required = (
            "episode-crosswalk.parquet", "row-identity.parquet", "h1-surfaces.parquet",
            "s0-prediction.pkl", "s0-rank-ic.pkl", "mlflow.db",
            "calendar-runtime/calendars/day.txt", "calendar-runtime/calendars/day_future.txt",
        )
        if any(not (output / name).is_file() for name in required):
            raise RuntimeError("partial H1 output is not eligible for bounded S0 resume")
        if not pd.read_parquet(output / "episode-crosswalk.parquet").equals(crosswalk):
            raise RuntimeError("partial H1 crosswalk does not match current frozen inputs")
        calendar = {
            "last_data_session": (output / "calendar-runtime/calendars/day.txt").read_text(
                encoding="utf-8",
            ).splitlines()[-1],
            "future_session": (output / "calendar-runtime/calendars/day_future.txt").read_text(
                encoding="utf-8",
            ).splitlines()[-1],
        }
    else:
        crosswalk.to_parquet(output / "episode-crosswalk.parquet", index=False)
        calendar = prepare_calendar(args.provider, args.future_calendar, output / "calendar-runtime")
    qlib.init(
        provider_uri=str(args.provider), region="us",
        calendar_provider={
            "class": "LocalCalendarProvider", "module_path": "qlib.data.data",
            "kwargs": {"backend": {
                "class": "FileCalendarStorage", "module_path": "qlib.data.storage.file_storage",
                "kwargs": {"provider_uri": str(output / "calendar-runtime")},
            }},
        },
        expression_cache=None, dataset_cache=None,
        exp_manager={
            "class": "MLflowExpManager", "module_path": "qlib.workflow.expm",
            "kwargs": {"uri": "sqlite:///" + str(output / "mlflow.db"),
                       "default_exp_name": "Experiment"},
        },
    )
    surface_path = output / "h1-surfaces.parquet"
    if not resume_s0:
        handler = RaggedAlpha158(
            instruments="p2_pit", start_time=TRAIN[0], end_time=TEST[1],
            fit_start_time=TRAIN[0], fit_end_time=TRAIN[1],
            infer_processors=[], learn_processors=[{"class": "DropnaLabel"}],
            filter_pipe=[current_close_filter()],
        )
        raw = handler.fetch(slice(TRAIN[0], TEST[1]), col_set=["feature", "label"],
                            data_key=DataHandlerLP.DK_I)
        raw, mapped_rows = project_index(raw, crosswalk)
        features = raw["feature"]
        label = raw["label"].iloc[:, 0].rename("__label__")
        if list(features.columns) != control_columns or len(features) != 1_196_594:
            raise RuntimeError("materialized CONTROL feature/row authority mismatch")
        fundamentals = pd.read_parquet(args.fundamentals).reindex(features.index)
        if list(fundamentals.columns) != list(P5_FEATURES) or len(fundamentals) != len(features):
            raise RuntimeError("P5 fundamentals cannot be aligned to CONTROL rows")
        surface = pd.concat((features, fundamentals, label), axis=1)
        if surface.index.has_duplicates or not surface.index.is_monotonic_increasing:
            raise RuntimeError("H1 surface row identity/order mismatch")
        surface.to_parquet(surface_path, compression="zstd")
        mapped_rows.to_parquet(output / "row-identity.parquet", index=False, compression="zstd")
        del raw, features, fundamentals, surface

    s0 = resume_finished_s0(output) if resume_s0 else train_surface(
        "S0", surface_path, control_columns, output,
    )
    s1 = train_surface("S1", surface_path, control_columns + list(P5_FEATURES), output)
    s0_execution = p2_prediction(s0.pop("prediction"), crosswalk)
    s1_execution = p2_prediction(s1.pop("prediction"), crosswalk)
    s0_portfolio, s0_net = backtest("S0", s0_execution, output)
    s1_portfolio, s1_net = backtest("S1", s1_execution, output)
    daily = pd.concat((s0_net, s1_net), axis=1).sort_index()
    if daily.isna().any().any() or not np.isfinite(daily.to_numpy()).all():
        raise RuntimeError("S0/S1 daily return evidence is incomplete")
    daily.index.name = "date"
    daily_path = output / "daily-net-returns.csv"
    daily.to_csv(daily_path, lineterminator="\n")
    surface_manifest = {
        "schema": "AQ_P5_H1_SURFACES_V1", "control_dataset_identity": CONTROL_DATASET_IDENTITY,
        "control_feature_manifest_sha256": control_hash, "surface_sha256": sha256(surface_path),
        "row_identity_sha256": sha256(output / "row-identity.parquet"),
        "crosswalk_sha256": sha256(output / "episode-crosswalk.parquet"),
        "row_count": 1_196_594, "s0_column_count": 157, "s1_column_count": 167,
        "s0_columns": control_columns, "s1_increment": list(P5_FEATURES),
        "label": "Ref($close, -2)/Ref($close, -1) - 1",
        "row_order": ["datetime ASC", "episode_id ASC"],
        "fundamental_nan_preserved": True, "feature_fillna_used": False,
    }
    write_json(output / "surface-manifest.json", surface_manifest)
    report = {
        "schema": "AQ_P5_H1_QLIB_EVIDENCE_V1", "qlib_version": qlib.__version__,
        "qlib_source_sha": source_sha, "lightgbm_version": lightgbm.__version__,
        "mlflow_version": mlflow.__version__, "model": "qlib.contrib.model.gbdt.LGBModel",
        "model_config": MODEL_CONFIG, "model_config_sha256": canonical_sha256(MODEL_CONFIG),
        "train_range": TRAIN, "valid_range": VALID, "test_range": TEST,
        "calendar": calendar, "s0": s0, "s1": s1,
        "rank_ic_delta": s1["rank_ic"] - s0["rank_ic"],
        "s0_portfolio": s0_portfolio, "s1_portfolio": s1_portfolio,
        "daily_net_returns_sha256": sha256(daily_path), "daily_return_rows": len(daily),
        "p2_v2_sealed_oos_accessed": False, "sec_network_request_count": 0,
        "h2_executed": False,
    }
    write_json(output / "qlib-report.json", report)


def compounded(values: pd.Series | np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    if not np.isfinite(array).all() or (array <= -1.0).any():
        raise RuntimeError("invalid daily net return")
    return float(np.prod(1.0 + array) - 1.0)


def split_evidence(frame: pd.DataFrame, tests: list[np.ndarray]) -> dict[str, object]:
    rows = []
    for split_id, indices in enumerate(tests):
        s0 = compounded(frame.iloc[indices]["S0"])
        s1 = compounded(frame.iloc[indices]["S1"])
        rows.append({
            "split_id": split_id, "start": frame.index[indices].min().strftime("%Y-%m-%d"),
            "end": frame.index[indices].max().strftime("%Y-%m-%d"),
            "session_count": len(indices), "s0_net_return": s0,
            "s1_net_return": s1, "active_return": s1 - s0,
        })
    active = np.asarray([row["active_return"] for row in rows])
    return {
        "split_count": len(rows), "positive_active_return_fraction": float(np.mean(active > 0)),
        "median_active_return": float(np.median(active)),
        "gate": bool(np.mean(active > 0) >= 0.60 and np.median(active) > 0), "splits": rows,
    }


def skfolio_mode(args: argparse.Namespace) -> None:
    import skfolio
    from skfolio.model_selection import CombinatorialPurgedCV, WalkForward

    if skfolio.__version__ != SKFOlIO_VERSION:
        raise RuntimeError("skfolio runtime identity mismatch")
    frame = pd.read_csv(args.daily, parse_dates=["date"]).set_index("date")
    wf = WalkForward(test_size=63, train_size=504, purged_size=2,
                     expand_train=False, reduce_test=False)
    wf_pairs = list(wf.split(frame.to_numpy()))
    cpcv = CombinatorialPurgedCV(n_folds=10, n_test_folds=2, purged_size=2, embargo_size=2)
    cpcv_pairs = list(cpcv.split(frame.to_numpy()))
    wf_tests = [test for _, test in wf_pairs]
    cpcv_tests = [np.sort(np.concatenate(groups)) for _, groups in cpcv_pairs]
    for train, test in wf_pairs:
        if set(train) & set(test):
            raise RuntimeError("WalkForward overlap")
    for (train, _), test in zip(cpcv_pairs, cpcv_tests):
        if set(train) & set(test):
            raise RuntimeError("CPCV overlap")
    write_json(args.output / "skfolio-report.json", {
        "skfolio_version": skfolio.__version__, "input_sha256": sha256(args.daily),
        "walkforward": split_evidence(frame, wf_tests),
        "cpcv": split_evidence(frame, cpcv_tests),
    })


def pvalues(value) -> dict[str, float]:
    return {str(key): float(item) for key, item in value.items()}


def arch_mode(args: argparse.Namespace) -> None:
    import arch
    from arch.bootstrap import SPA, RealityCheck

    if arch.__version__ != ARCH_VERSION:
        raise RuntimeError("arch runtime identity mismatch")
    frame = pd.read_csv(args.daily, parse_dates=["date"]).set_index("date")
    results = {}
    for direction, benchmark, challenger in (("S1_MINUS_S0", "S0", "S1"),
                                               ("S0_MINUS_S1", "S1", "S0")):
        baseline_loss = -frame[benchmark]
        model_loss = -frame[[challenger]]
        spa = SPA(baseline_loss, model_loss, block_size=10, reps=5000,
                  bootstrap="stationary", seed=20260913)
        reality = RealityCheck(baseline_loss, model_loss, block_size=10, reps=5000,
                               bootstrap="stationary", seed=20260913)
        spa.compute()
        reality.compute()
        results[direction] = {
            "spa_pvalues": pvalues(spa.pvalues),
            "spa_consistent_pvalue": float(spa.pvalues.loc["consistent"]),
            "reality_check_pvalues": pvalues(reality.pvalues),
            "reality_check_consistent_pvalue": float(reality.pvalues.loc["consistent"]),
        }
    write_json(args.output / "arch-report.json", {
        "arch_version": arch.__version__, "input_sha256": sha256(args.daily),
        "policy": {"bootstrap": "stationary", "block_size": 10, "reps": 5000,
                   "seed": 20260913, "alpha": 0.05, "loss": "negative net daily return"},
        "directions": results,
    })


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("mode", choices=("qlib", "skfolio", "arch"))
    result.add_argument("--output", required=True, type=Path)
    result.add_argument("--daily", type=Path)
    result.add_argument("--repo", type=Path)
    result.add_argument("--provider", type=Path)
    result.add_argument("--provider-report", type=Path)
    result.add_argument("--future-calendar", type=Path)
    result.add_argument("--episode-map", type=Path)
    result.add_argument("--projection-grid", type=Path)
    result.add_argument("--fundamentals", type=Path)
    result.add_argument("--p5-manifest", type=Path)
    result.add_argument("--qlib-source", type=Path)
    return result


def main() -> None:
    args = parser().parse_args()
    if args.mode == "qlib":
        qlib_mode(args)
    elif args.mode == "skfolio":
        skfolio_mode(args)
    else:
        arch_mode(args)


if __name__ == "__main__":
    main()
