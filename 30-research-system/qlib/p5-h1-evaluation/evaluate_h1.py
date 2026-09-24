"""Execute the frozen P5 H1 comparison through existing upstream owners."""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import json
import os
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
SKFOLIO_VERSION = "1.0.6"
ARCH_VERSION = "8.0.0"
H2_EXECUTED = False
TRAIN = ("2015-04-01", "2019-12-31")
VALID = ("2020-01-01", "2021-12-31")
TEST = ("2022-01-03", "2024-12-31")
P5_FEATURES = (
    "Revenue", "NetIncome", "Assets", "Liabilities", "CommonEquity",
    "NetCashFromOperatingActivities", "CashAndCashEquivalents",
    "CurrentAssetsTotal", "CurrentLiabilitiesTotal", "LongTermDebt",
)
LEARN_PROCESSORS = (
    {"class": "DropnaLabel", "kwargs": {"fields_group": "label"}},
    {"class": "CSZScoreNorm", "kwargs": {"fields_group": "label"}},
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


def load_reference(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load existing repository capability: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_crosswalk(projection: pd.DataFrame, episode_map_path: Path) -> pd.DataFrame:
    """Bind versioned P2 ranges to unique date-valid P1 episode IDs."""
    episodes = projection.groupby(
        ["episode_id", "historical_ticker", "identity_excluded"], as_index=False,
    ).agg(p5_start=("session", "min"), p5_end=("session", "max"))
    p2 = pd.DataFrame(
        [json.loads(line) for line in episode_map_path.read_text(encoding="utf-8").splitlines()]
    ).rename(columns={"episode_id": "p2_episode_id", "instrument": "p2_instrument",
                      "start": "p2_start", "end_inclusive": "p2_end"})
    p2[["p2_start", "p2_end"]] = p2[["p2_start", "p2_end"]].apply(pd.to_datetime)
    candidates = p2.merge(episodes, on="historical_ticker", how="inner")
    crosswalk = candidates[(candidates["p5_end"] >= candidates["p2_start"])
                           & (candidates["p5_start"] <= candidates["p2_end"])].copy()
    counts = crosswalk.groupby("p2_episode_id").size()
    if len(p2) != 745 or len(crosswalk) != len(p2) or not counts.eq(1).all():
        raise RuntimeError("P2/P5 episode crosswalk is incomplete or ambiguous")
    if crosswalk.duplicated(["p2_instrument", "p2_start", "p2_end"]).any():
        raise RuntimeError("duplicate P2 range in episode crosswalk")
    return crosswalk.rename(columns={"episode_id": "p5_episode_id"})[[
        "p2_episode_id", "p2_instrument", "p2_start", "p2_end", "p5_episode_id",
        "historical_ticker", "p5_start", "p5_end", "identity_excluded",
    ]].sort_values(["p2_instrument", "p2_start"], ignore_index=True)


def project_index(frame: pd.DataFrame, crosswalk: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Replace P2 instrument IDs with the unique date-valid P1 episode ID."""
    keys = frame.index.to_frame(index=False).rename(columns={"instrument": "p2_instrument"})
    keys["_row"] = np.arange(len(keys), dtype=np.int64)
    matched = keys.merge(crosswalk, on="p2_instrument", how="left")
    matched = matched[(matched["datetime"] >= matched["p2_start"])
                      & (matched["datetime"] <= matched["p2_end"])].sort_values("_row")
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
    mapped = matched.iloc[order][["datetime", "p5_episode_id", "p2_instrument",
                                  "p2_start", "p2_end"]].rename(
                                      columns={"p5_episode_id": "instrument"})
    return projected, mapped.reset_index(drop=True)


def control_manifest(config_class) -> tuple[list[str], str]:
    instance = config_class.__new__(config_class)
    expressions, names = instance.get_feature_config()
    manifest = {"feature_family": "P2_RAGGED_ALPHA158_OHLCV_157", "columns": [
        {"position": index + 1, "name": name, "expression": expression}
        for index, (name, expression) in enumerate(zip(names, expressions))
    ]}
    return list(names), canonical_sha256(manifest)


def make_dataset(surface_path: Path, columns: list[str]):
    from qlib.data.dataset import DatasetH
    from qlib.data.dataset.handler import DataHandlerLP
    from qlib.data.dataset.loader import StaticDataLoader

    surface = pd.read_parquet(surface_path, columns=columns + ["__label__"])
    handler = DataHandlerLP(
        instruments=None, start_time=TRAIN[0], end_time=TEST[1],
        data_loader=StaticDataLoader({
            "feature": surface[columns],
            "label": surface[["__label__"]].rename(columns={"__label__": "LABEL0"}),
        }),
        shared_processors=[], infer_processors=[], learn_processors=list(LEARN_PROCESSORS),
        process_type=DataHandlerLP.PTYPE_A,
    )
    return DatasetH(handler=handler, segments={"train": TRAIN, "valid": VALID, "test": TEST})


def learning_surface_gate(surface_path: Path, s0_columns: list[str]) -> dict[str, object]:
    """Prove the pre-existing label-only processor authority before either fit."""
    from qlib.data.dataset.handler import DataHandlerLP

    audits = {}
    for surface_id, columns in (("S0", s0_columns), ("S1", s0_columns + list(P5_FEATURES))):
        dataset = make_dataset(surface_path, columns)
        processors = dataset.handler.learn_processors
        identity = "->".join(type(item).__name__ for item in processors)
        if identity != "DropnaLabel->CSZScoreNorm" or any(
            getattr(item, "fields_group", None) not in ("label", ["label"])
            for item in processors
        ):
            raise RuntimeError(f"{surface_id} frozen learn processor authority mismatch")
        split_stats = {}
        nan_preserved = True
        valid_zero_preserved = True
        valid_zero_count = 0
        label_hashes = []
        for segment in ("train", "valid"):
            learned = dataset.prepare(
                segment, col_set=["feature", "label"], data_key=DataHandlerLP.DK_L,
            )
            feature = learned["feature"]
            label = learned["label"].iloc[:, 0]
            expected = dataset.prepare(
                segment, col_set="feature", data_key=DataHandlerLP.DK_R,
            ).loc[feature.index]
            nan_preserved &= np.array_equal(feature.isna().to_numpy(), expected.isna().to_numpy())
            if segment == "valid":
                zero = expected.eq(0.0)
                valid_zero_count = int(zero.to_numpy().sum())
                valid_zero_preserved &= bool(feature.where(zero).stack().eq(0.0).all())
            label_hashes.append(pd.util.hash_pandas_object(label, index=True).to_numpy().tobytes())
            split_stats[segment] = {
                "non_null": int(label.notna().sum()),
                "unique": int(label.nunique(dropna=True)),
            }
        audits[surface_id] = {
            "processor_identity": identity + "(label)", "split_stats": split_stats,
            "label_sha256": hashlib.sha256(b"".join(label_hashes)).hexdigest(),
            "feature_nan_positions_preserved": bool(nan_preserved),
            "valid_feature_zero_preserved": bool(valid_zero_preserved),
            "valid_feature_zero_count": valid_zero_count,
        }
        del dataset
        gc.collect()
    if audits["S0"]["label_sha256"] != audits["S1"]["label_sha256"]:
        raise RuntimeError("S0/S1 transformed labels differ")
    if not all(audits[key]["feature_nan_positions_preserved"]
               and audits[key]["valid_feature_zero_preserved"]
               and audits[key]["valid_feature_zero_count"] > 0 for key in audits):
        raise RuntimeError("label-only processor changed a frozen feature value")
    for split in ("train", "valid"):
        stats = audits["S0"]["split_stats"][split]
        if stats["non_null"] == 0 or stats["unique"] <= 1:
            raise RuntimeError(f"{split} transformed label is degenerate")
    return {
        "schema": "AQ_P5_H1_PREFIT_PROCESSOR_GATE_V1", "surfaces": audits,
        "s0_s1_label_values_match": True, "feature_nan_positions_preserved": True,
        "valid_feature_zero_preserved": True,
    }


def train_surface(surface_id: str, surface_path: Path, columns: list[str], output: Path):
    from qlib.contrib.model.gbdt import LGBModel
    from qlib.workflow import R
    from qlib.workflow.record_temp import SigAnaRecord, SignalRecord

    dataset = make_dataset(surface_path, columns)
    model = LGBModel(**MODEL_CONFIG)
    with R.start(experiment_name="p5_h1_incremental_fundamentals_attempt_003",
                 recorder_name=surface_id):
        recorder = R.get_recorder()
        recorder.log_params(
            task="AUTONOMOUS_QUANT_P5_H1_PR82_RESOURCE_SAFE_PROCESS_ISOLATED_ATTEMPT_003_001",
            attempt="ATTEMPT_003_PROCESS_ISOLATED_AUTHORITY_CORRECTED", surface=surface_id,
            processor_chain="DropnaLabel(label)->CSZScoreNorm(label)",
            model_config_sha256=canonical_sha256(MODEL_CONFIG), column_count=len(columns),
            train_range="/".join(TRAIN), valid_range="/".join(VALID), test_range="/".join(TEST),
        )
        model.fit(dataset, verbose_eval=20)
        SignalRecord(model=model, dataset=dataset, recorder=recorder).generate()
        SigAnaRecord(recorder=recorder, ana_long_short=False, ann_scaler=252).generate()
        recorder_id = recorder.id
    recorded = R.get_recorder(recorder_id=recorder_id,
                              experiment_name="p5_h1_incremental_fundamentals_attempt_003")
    prediction = recorded.load_object("pred.pkl")
    rank_ic = recorded.load_object("sig_analysis/ric.pkl")
    prediction = prediction.iloc[:, 0] if isinstance(prediction, pd.DataFrame) else prediction
    prediction = prediction.rename("score").sort_index()
    prediction_path = output / f"{surface_id.lower()}-prediction.pkl"
    rank_ic_path = output / f"{surface_id.lower()}-rank-ic.pkl"
    prediction.to_pickle(prediction_path)
    pd.to_pickle(rank_ic, rank_ic_path)
    result = {
        "recorder_id": recorder_id, "prediction": prediction, "model_fit_count": 1,
        "prediction_sha256": sha256(prediction_path), "prediction_rows": len(prediction),
        "rank_ic": float(rank_ic.mean()), "rank_ic_sha256": sha256(rank_ic_path),
        "best_iteration": int(model.model.best_iteration),
    }
    del dataset, model
    gc.collect()
    return result


def p2_prediction(prediction: pd.Series, crosswalk: pd.DataFrame) -> pd.Series:
    mapping = crosswalk.set_index("p5_episode_id")["p2_instrument"]
    frame = prediction.rename("score").reset_index()
    frame["instrument"] = frame["instrument"].map(mapping)
    if frame["instrument"].isna().any() or frame.duplicated(["datetime", "instrument"]).any():
        raise RuntimeError("prediction cannot be projected uniquely to P2 execution identity")
    return frame.set_index(["instrument", "datetime"])["score"].sort_index()


def classify_h1(attempt: str, s0_rank_ic: float, s1_rank_ic: float,
                skfolio: dict | None = None, arch: dict | None = None) -> str:
    if attempt != "ATTEMPT_003_PROCESS_ISOLATED_AUTHORITY_CORRECTED":
        raise ValueError("attempt-001/002 is not eligible for final H1 classification")
    if not np.isfinite([s0_rank_ic, s1_rank_ic]).all():
        return "INCONCLUSIVE"
    if skfolio is None or arch is None:
        raise ValueError("finite H1 classification requires frozen temporal/statistical evidence")
    delta = s1_rank_ic - s0_rank_ic
    forward = skfolio["directions"]["S1_MINUS_S0"]
    reverse = skfolio["directions"]["S0_MINUS_S1"]
    forward_arch = arch["directions"]["S1_MINUS_S0"]
    reverse_arch = arch["directions"]["S0_MINUS_S1"]
    support = (delta > 0 and forward["walkforward"]["gate"] and forward["cpcv"]["gate"]
               and forward_arch["spa_consistent_pvalue"] <= 0.05
               and forward_arch["reality_check_consistent_pvalue"] <= 0.05)
    degraded = (delta < 0 and reverse["walkforward"]["gate"] and reverse["cpcv"]["gate"]
                and reverse_arch["spa_consistent_pvalue"] <= 0.05
                and reverse_arch["reality_check_consistent_pvalue"] <= 0.05)
    return "INCREMENTAL_VALUE_SUPPORTED" if support else "DEGRADED" if degraded \
        else "NO_MEASURABLE_INCREMENTAL_VALUE"


def init_runtime(args: argparse.Namespace, output: Path):
    sys.path.insert(0, str(args.repo / "30-research-system" / "qlib" / "dataset-adapter"))
    import lightgbm
    import qlib
    from aq_qlib_handoff.qlib_config import RaggedAlpha158, current_close_filter

    if qlib.__version__ != QLIB_VERSION or lightgbm.__version__ != LIGHTGBM_VERSION:
        raise RuntimeError("Qlib/LightGBM runtime identity mismatch")
    source_sha = subprocess.check_output(
        ("git", "-C", str(args.qlib_source), "rev-parse", "HEAD"), text=True,
    ).strip()
    if source_sha != QLIB_SOURCE_SHA or sha256(args.provider_report) != P2_REPORT_SHA256:
        raise RuntimeError("Qlib/P2 authority mismatch")
    current = (args.calendar_runtime / "calendars" / "day.txt").read_text().splitlines()
    future = (args.calendar_runtime / "calendars" / "day_future.txt").read_text().splitlines()
    if future[:-1] != current or len(future) != len(current) + 1:
        raise RuntimeError("frozen P2 calendar runtime identity mismatch")
    qlib.init(
        provider_uri=str(args.provider), region="us",
        calendar_provider={"class": "LocalCalendarProvider", "module_path": "qlib.data.data",
                           "kwargs": {"backend": {"class": "FileCalendarStorage",
                                                   "module_path": "qlib.data.storage.file_storage",
                                                   "kwargs": {"provider_uri": str(args.calendar_runtime)}}}},
        expression_cache=None, dataset_cache=None,
        exp_manager={"class": "MLflowExpManager", "module_path": "qlib.workflow.expm",
                     "kwargs": {"uri": "sqlite:///" + str(output / "mlflow.db"),
                                "default_exp_name": "Experiment"}},
    )
    return qlib, lightgbm, RaggedAlpha158, current_close_filter, source_sha, current, future


def preflight_mode(args: argparse.Namespace) -> None:
    output: Path = args.output
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    os.chdir(output)
    qlib, lightgbm, RaggedAlpha158, current_close_filter, source_sha, current, future = \
        init_runtime(args, output)
    from qlib.data.dataset.handler import DataHandlerLP

    p5_manifest = json.loads(args.p5_manifest.read_text(encoding="utf-8"))
    if (tuple(p5_manifest["features"]) != P5_FEATURES
            or p5_manifest["session_rows"] != 1_893_759
            or p5_manifest["feature_parquet_sha256"] != P5_PARQUET_SHA256
            or sha256(args.fundamentals) != P5_PARQUET_SHA256):
        raise RuntimeError("P5 handoff authority mismatch")
    control_columns, control_hash = control_manifest(RaggedAlpha158)
    if len(control_columns) != 157 or control_hash != CONTROL_MANIFEST_SHA256:
        raise RuntimeError("frozen CONTROL surface mismatch")
    projection = pd.read_parquet(args.projection_grid)
    if len(projection) != 1_893_759 or int(projection["identity_excluded"].sum()) != 210_966:
        raise RuntimeError("P5 projection accounting mismatch")
    crosswalk = build_crosswalk(projection, args.episode_map)
    crosswalk.to_parquet(output / "episode-crosswalk.parquet", index=False)
    handler = RaggedAlpha158(
        instruments="p2_pit", start_time=TRAIN[0], end_time=TEST[1],
        fit_start_time=TRAIN[0], fit_end_time=TRAIN[1], infer_processors=[],
        learn_processors=list(LEARN_PROCESSORS), filter_pipe=[current_close_filter()],
    )
    raw = handler.fetch(slice(TRAIN[0], TEST[1]), col_set=["feature", "label"],
                        data_key=DataHandlerLP.DK_I)
    raw, mapped_rows = project_index(raw, crosswalk)
    features, label = raw["feature"], raw["label"].iloc[:, 0].rename("__label__")
    if list(features.columns) != control_columns or len(features) != 1_196_594:
        raise RuntimeError("materialized CONTROL feature/row authority mismatch")
    fundamentals_source = pd.read_parquet(args.fundamentals)
    if len(features.index.intersection(fundamentals_source.index)) != len(features):
        raise RuntimeError("CONTROL/fundamental index intersection is incomplete")
    fundamentals = fundamentals_source.reindex(features.index)
    non_null_cells = int(fundamentals.notna().sum().sum())
    if list(fundamentals.columns) != list(P5_FEATURES) or non_null_cells != 10_130_596:
        raise RuntimeError("P5 fundamental content authority mismatch")
    surface = pd.concat((features, fundamentals, label), axis=1)
    if surface.index.has_duplicates or not surface.index.is_monotonic_increasing:
        raise RuntimeError("H1 surface row identity/order mismatch")
    surface_path = output / "h1-surfaces.parquet"
    surface.to_parquet(surface_path, compression="zstd")
    mapped_rows.to_parquet(output / "row-identity.parquet", index=False, compression="zstd")
    del raw, features, fundamentals, fundamentals_source, surface
    gc.collect()
    write_json(output / "prefit-processor-gate.json",
               learning_surface_gate(surface_path, control_columns))
    write_json(output / "preflight-report.json", {
        "schema": "AQ_P5_H1_PREFLIGHT_V3", "attempt": "ATTEMPT_003_PROCESS_ISOLATED",
        "qlib_version": qlib.__version__, "lightgbm_version": lightgbm.__version__,
        "qlib_source_sha": source_sha, "control_feature_manifest_sha256": control_hash,
        "surface_sha256": sha256(surface_path), "row_count": 1_196_594,
        "s0_column_count": 157, "s1_column_count": 167,
        "fundamental_non_null_cell_count": non_null_cells,
        "control_fundamental_index_intersection_fraction": 1.0,
        "calendar": {"last_data_session": current[-1], "future_session": future[-1]},
    })


def fit_mode(args: argparse.Namespace) -> None:
    output: Path = args.output
    if args.surface_id is None:
        raise RuntimeError("fit mode requires one frozen surface ID")
    if not (output / "preflight-report.json").is_file():
        raise RuntimeError("attempt-003 preflight is incomplete")
    os.chdir(output)
    _, _, RaggedAlpha158, _, _, _, _ = init_runtime(args, output)
    control_columns, control_hash = control_manifest(RaggedAlpha158)
    preflight = json.loads((output / "preflight-report.json").read_text(encoding="utf-8"))
    if control_hash != preflight["control_feature_manifest_sha256"]:
        raise RuntimeError("attempt-003 preflight identity mismatch")
    columns = control_columns if args.surface_id == "S0" else control_columns + list(P5_FEATURES)
    result = train_surface(args.surface_id, output / "h1-surfaces.parquet", columns, output)
    write_json(output / f"{args.surface_id.lower()}-fit-report.json",
               {key: value for key, value in result.items() if key != "prediction"})


def compose_mode(args: argparse.Namespace) -> None:
    import mlflow

    output: Path = args.output
    os.chdir(output)
    qlib, lightgbm, RaggedAlpha158, _, source_sha, _, _ = init_runtime(args, output)
    control_columns, control_hash = control_manifest(RaggedAlpha158)
    preflight = json.loads((output / "preflight-report.json").read_text(encoding="utf-8"))
    if control_hash != preflight["control_feature_manifest_sha256"]:
        raise RuntimeError("attempt-003 preflight identity mismatch")
    results = {surface: json.loads((output / f"{surface.lower()}-fit-report.json").read_text())
               for surface in ("S0", "S1")}
    report = {
        "schema": "AQ_P5_H1_QLIB_EVIDENCE_V3", "attempt": "ATTEMPT_003_PROCESS_ISOLATED",
        "attempt_001_classification": "INVALID_IMPLEMENTATION_DEVIATION",
        "attempt_002_classification": "AUTHORITY_CORRECTED_RESOURCE_OOM",
        "qlib_version": qlib.__version__, "qlib_source_sha": source_sha,
        "lightgbm_version": lightgbm.__version__, "mlflow_version": mlflow.__version__,
        "model": "qlib.contrib.model.gbdt.LGBModel", "model_config": MODEL_CONFIG,
        "model_config_sha256": canonical_sha256(MODEL_CONFIG), "train_range": TRAIN,
        "valid_range": VALID, "test_range": TEST, "calendar": preflight["calendar"],
        "processor_gate_sha256": sha256(output / "prefit-processor-gate.json"),
        "fundamental_non_null_cell_count": preflight["fundamental_non_null_cell_count"],
        "control_fundamental_index_intersection_fraction": 1.0,
        "s0": results["S0"], "s1": results["S1"],
        "rank_ic_delta": results["S1"]["rank_ic"] - results["S0"]["rank_ic"],
        "p2_v2_sealed_oos_accessed": False, "sec_network_request_count": 0,
        "h2_executed": H2_EXECUTED,
    }
    if not np.isfinite([results["S0"]["rank_ic"], results["S1"]["rank_ic"]]).all():
        report["status"] = "INCONCLUSIVE_UNDEFINED_PRIMARY_METRIC"
        write_json(output / "qlib-report.json", report)
        write_json(output / "classification-report.json", {
            "attempt_003": classify_h1("ATTEMPT_003_PROCESS_ISOLATED_AUTHORITY_CORRECTED",
                                       results["S0"]["rank_ic"], results["S1"]["rank_ic"]),
        })
        raise RuntimeError("attempt-003 primary QLIB_RANK_IC is undefined")
    crosswalk = pd.read_parquet(output / "episode-crosswalk.parquet")
    reference = load_reference(
        args.repo / "40-certification-system" / "historical-rehearsal" / "qlib_rehearsal.py",
        "aq_existing_qlib_rehearsal",
    )
    (output / "portfolio").mkdir()
    portfolio, returns = {}, []
    for surface_id in ("S0", "S1"):
        prediction = pd.read_pickle(output / f"{surface_id.lower()}-prediction.pkl")
        evidence = reference.run_backtest(
            surface_id, p2_prediction(prediction, crosswalk), 30, 3, "BASE",
            (0.0005, 0.0015), output,
        )
        returns.append(evidence.pop("net").rename(surface_id))
        portfolio[surface_id] = evidence
    daily = pd.concat(returns, axis=1).sort_index()
    if daily.isna().any().any() or not np.isfinite(daily.to_numpy()).all():
        raise RuntimeError("S0/S1 daily return evidence is incomplete")
    daily.index.name = "date"
    daily_path = output / "daily-net-returns.csv"
    daily.to_csv(daily_path, lineterminator="\n")
    write_json(output / "surface-manifest.json", {
        "schema": "AQ_P5_H1_SURFACES_V3", "attempt": "ATTEMPT_003_PROCESS_ISOLATED",
        "control_dataset_identity": CONTROL_DATASET_IDENTITY,
        "control_feature_manifest_sha256": control_hash,
        "surface_sha256": preflight["surface_sha256"],
        "row_identity_sha256": sha256(output / "row-identity.parquet"),
        "crosswalk_sha256": sha256(output / "episode-crosswalk.parquet"),
        "row_count": 1_196_594, "s0_column_count": 157, "s1_column_count": 167,
        "s0_columns": control_columns, "s1_increment": list(P5_FEATURES),
        "label": "Ref($close, -2)/Ref($close, -1) - 1",
        "row_order": ["datetime ASC", "episode_id ASC"],
        "fundamental_nan_preserved": True, "feature_fillna_used": False,
    })
    report.update({"status": "VALID_PRIMARY_METRIC", "s0_portfolio": portfolio["S0"],
                   "s1_portfolio": portfolio["S1"],
                   "daily_net_returns_sha256": sha256(daily_path),
                   "daily_return_rows": len(daily)})
    write_json(output / "qlib-report.json", report)


def skfolio_mode(args: argparse.Namespace) -> None:
    import skfolio
    from skfolio.model_selection import CombinatorialPurgedCV, WalkForward

    if skfolio.__version__ != SKFOLIO_VERSION:
        raise RuntimeError("skfolio runtime identity mismatch")
    frame = pd.read_csv(args.daily, parse_dates=["date"]).set_index("date")
    wf_pairs = list(WalkForward(test_size=63, train_size=504, purged_size=2,
                                expand_train=False, reduce_test=False).split(frame.to_numpy()))
    cpcv_pairs = list(CombinatorialPurgedCV(
        n_folds=10, n_test_folds=2, purged_size=2, embargo_size=2,
    ).split(frame.to_numpy()))
    wf_tests = [test for _, test in wf_pairs]
    cpcv_tests = [np.sort(np.concatenate(groups)) for _, groups in cpcv_pairs]
    for train, test in wf_pairs + [(train, test) for (train, _), test in zip(cpcv_pairs, cpcv_tests)]:
        if set(train) & set(test):
            raise RuntimeError("frozen temporal split overlap")
    reference = load_reference(
        args.repo / "40-certification-system" / "historical-rehearsal" / "evaluate_rehearsal.py",
        "aq_existing_rehearsal_evaluator",
    )
    directions = {}
    for name, candidate, control in (("S1_MINUS_S0", "S1", "S0"),
                                     ("S0_MINUS_S1", "S0", "S1")):
        directions[name] = {
            "walkforward": reference.reduce_splits(
                reference.split_evidence(frame, wf_tests, candidate, control)),
            "cpcv": reference.reduce_splits(
                reference.split_evidence(frame, cpcv_tests, candidate, control)),
        }
    write_json(args.output / "skfolio-report.json", {
        "skfolio_version": skfolio.__version__, "input_sha256": sha256(args.daily),
        "directions": directions,
    })


def arch_mode(args: argparse.Namespace) -> None:
    import arch
    from arch.bootstrap import SPA, RealityCheck

    if arch.__version__ != ARCH_VERSION:
        raise RuntimeError("arch runtime identity mismatch")
    frame = pd.read_csv(args.daily, parse_dates=["date"]).set_index("date")
    results = {}
    for direction, benchmark, challenger in (("S1_MINUS_S0", "S0", "S1"),
                                               ("S0_MINUS_S1", "S1", "S0")):
        spa = SPA(-frame[benchmark], -frame[[challenger]], block_size=10, reps=5000,
                  bootstrap="stationary", seed=20260913)
        reality = RealityCheck(-frame[benchmark], -frame[[challenger]], block_size=10,
                               reps=5000, bootstrap="stationary", seed=20260913)
        spa.compute()
        reality.compute()
        results[direction] = {
            "spa_pvalues": {str(k): float(v) for k, v in spa.pvalues.items()},
            "spa_consistent_pvalue": float(spa.pvalues.loc["consistent"]),
            "reality_check_pvalues": {str(k): float(v) for k, v in reality.pvalues.items()},
            "reality_check_consistent_pvalue": float(reality.pvalues.loc["consistent"]),
        }
    report = {
        "arch_version": arch.__version__, "input_sha256": sha256(args.daily),
        "policy": {"bootstrap": "stationary", "block_size": 10, "reps": 5000,
                   "seed": 20260913, "alpha": 0.05, "loss": "negative net daily return"},
        "directions": results,
    }
    write_json(args.output / "arch-report.json", report)
    qlib_report = json.loads((args.output / "qlib-report.json").read_text(encoding="utf-8"))
    skfolio_report = json.loads((args.output / "skfolio-report.json").read_text(encoding="utf-8"))
    classification = classify_h1(
        "ATTEMPT_003_PROCESS_ISOLATED_AUTHORITY_CORRECTED", qlib_report["s0"]["rank_ic"],
        qlib_report["s1"]["rank_ic"], skfolio_report, report,
    )
    write_json(args.output / "classification-report.json", {
        "attempt_001": "INVALID_IMPLEMENTATION_DEVIATION",
        "attempt_002": "AUTHORITY_CORRECTED_RESOURCE_OOM",
        "attempt_003": "PROCESS_ISOLATED_AUTHORITY_CORRECTED",
        "h1_result_classification": classification,
        "p5_complete": classification != "INCONCLUSIVE",
    })


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("mode", choices=("preflight", "fit", "compose", "skfolio", "arch"))
    result.add_argument("--output", required=True, type=Path)
    result.add_argument("--daily", type=Path)
    result.add_argument("--repo", type=Path)
    result.add_argument("--provider", type=Path)
    result.add_argument("--provider-report", type=Path)
    result.add_argument("--calendar-runtime", type=Path)
    result.add_argument("--episode-map", type=Path)
    result.add_argument("--projection-grid", type=Path)
    result.add_argument("--fundamentals", type=Path)
    result.add_argument("--p5-manifest", type=Path)
    result.add_argument("--qlib-source", type=Path)
    result.add_argument("--surface-id", choices=("S0", "S1"))
    return result


def main() -> None:
    args = parser().parse_args()
    if args.mode == "preflight":
        preflight_mode(args)
    elif args.mode == "fit":
        fit_mode(args)
    elif args.mode == "compose":
        compose_mode(args)
    elif args.mode == "skfolio":
        skfolio_mode(args)
    else:
        arch_mode(args)


if __name__ == "__main__":
    main()
