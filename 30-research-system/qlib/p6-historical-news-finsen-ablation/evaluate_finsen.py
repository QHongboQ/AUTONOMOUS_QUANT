"""Execute the frozen P6 FinSen M0-versus-M1 research comparison."""

from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd


PROTOCOL_SHA = "63c69d4eb80a7d98ad4b846484ca14a0bc47e83b2fc5659a261098e7852d79b9"
EXPERIMENT = "p6_historical_news_finsen_first_authorized_ablation_001"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_lf_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def canonical_sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load repository authority: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_authority(repo: Path):
    protocol_path = repo / "30-research-system/qlib/p6-historical-news-finsen-ablation/finsen-ablation-protocol.json"
    if canonical_lf_sha(protocol_path) != PROTOCOL_SHA:
        raise RuntimeError("frozen FinSen protocol identity mismatch")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    p5 = load_module(repo / "30-research-system/qlib/p5-h1-evaluation/evaluate_h1.py", "p5_h1_authority")
    if protocol["model"]["config"] != p5.MODEL_CONFIG or canonical_sha(p5.MODEL_CONFIG) != protocol["model"]["config_sha256"]:
        raise RuntimeError("P5 vehicle/model identity mismatch")
    if protocol["control"]["dataset_identity"] != p5.CONTROL_DATASET_IDENTITY:
        raise RuntimeError("control dataset identity mismatch")
    return protocol, p5


def verify_factor(protocol: dict, root: Path) -> tuple[pd.DataFrame, dict]:
    authority = protocol["finsen_input_authority"]
    factor_path = root / "session-global-signal.parquet"
    checksum_path = root / "checksums.json"
    manifest_path = root / "signal-manifest.json"
    quality_path = root / "data-quality-report.json"
    if sha256(factor_path) != authority["factor_sha256"] or sha256(checksum_path) != authority["private_evidence_checksum_sha256"]:
        raise RuntimeError("sealed FinSen input identity mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    frame = pd.read_parquet(factor_path)
    feature = authority["factor_name"]
    expected_columns = ["session", "source_date", feature]
    if list(frame.columns) != expected_columns or frame["session"].duplicated().any():
        raise RuntimeError("sealed FinSen schema/grain mismatch")
    if (len(frame) != 2087 or frame["session"].min() != pd.Timestamp("2015-04-01")
            or frame["session"].max() != pd.Timestamp("2023-07-17")):
        raise RuntimeError("sealed FinSen supported interval mismatch")
    null_sessions = int(frame[feature].isna().sum())
    if (null_sessions != authority["session_without_signal_count"]
            or int(frame[feature].notna().sum()) != authority["session_with_signal_count"]
            or quality["effective_session_collision_count"] != authority["effective_session_collision_count"]
            or quality["superseded_daily_signal_count"] != authority["superseded_daily_signal_count"]
            or manifest["factor_name"] != feature):
        raise RuntimeError("sealed FinSen factor accounting mismatch")
    return frame, {
        "factor_sha256": sha256(factor_path),
        "private_evidence_checksum_sha256": sha256(checksum_path),
        "supported_interval_session_count": len(frame),
        "supported_interval_null_session_count": null_sessions,
    }


def validate_surface_inventory(protocol: dict, control: list[str], evaluation: list[str]) -> None:
    increment = [protocol["finsen_input_authority"]["factor_name"]]
    if len(control) != 157 or evaluation != control + increment + ["__label__"]:
        raise RuntimeError("frozen M0/M1 surface inventory mismatch")
    forbidden = {"Revenue", "NetIncome", "Assets", "macro_v1_cpiaucsl_d2_log", "macro_v1_unrate_d1"}
    if forbidden.intersection(evaluation):
        raise RuntimeError("excluded feature family entered FinSen surface")


def classify(rank0: float, rank1: float, temporal: dict, arch: dict) -> str:
    if not np.isfinite([rank0, rank1]).all():
        return "INCONCLUSIVE"
    forward, reverse = temporal["directions"]["M1_MINUS_M0"], temporal["directions"]["M0_MINUS_M1"]
    forward_arch, reverse_arch = arch["directions"]["M1_MINUS_M0"], arch["directions"]["M0_MINUS_M1"]
    support = (rank1 > rank0 and forward["walkforward"]["gate"] and forward["cpcv"]["gate"]
               and forward_arch["spa_consistent_pvalue"] <= 0.05
               and forward_arch["reality_check_consistent_pvalue"] <= 0.05)
    degraded = (rank1 < rank0 and reverse["walkforward"]["gate"] and reverse["cpcv"]["gate"]
                and reverse_arch["spa_consistent_pvalue"] <= 0.05
                and reverse_arch["reality_check_consistent_pvalue"] <= 0.05)
    return "INCREMENTAL_VALUE_SUPPORTED" if support else "DEGRADED" if degraded else "NO_MEASURABLE_INCREMENTAL_VALUE"


def splits(protocol: dict) -> dict[str, tuple[str, str]]:
    return {name: tuple(value) for name, value in protocol["splits"].items()}


def make_dataset(surface_path: Path, columns: list[str], protocol: dict):
    from qlib.data.dataset import DatasetH
    from qlib.data.dataset.handler import DataHandlerLP
    from qlib.data.dataset.loader import StaticDataLoader

    periods = splits(protocol)
    surface = pd.read_parquet(surface_path, columns=columns + ["__label__"])
    handler = DataHandlerLP(
        instruments=None, start_time=periods["train"][0], end_time=periods["historical_research_test"][1],
        data_loader=StaticDataLoader({
            "feature": surface[columns],
            "label": surface[["__label__"]].rename(columns={"__label__": "LABEL0"}),
        }),
        shared_processors=[], infer_processors=[],
        learn_processors=[
            {"class": "DropnaLabel", "kwargs": {"fields_group": "label"}},
            {"class": "CSZScoreNorm", "kwargs": {"fields_group": "label"}},
        ],
        process_type=DataHandlerLP.PTYPE_A,
    )
    return DatasetH(handler=handler, segments={
        "train": periods["train"], "valid": periods["validation"],
        "test": periods["historical_research_test"],
    })


def prepare(args) -> None:
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    os.chdir(args.output)
    protocol, p5 = load_authority(args.repo)
    periods = splits(protocol)
    qlib, lightgbm, config, close_filter, source_sha, current, future = p5.init_runtime(args, args.output)
    from qlib.data.dataset.handler import DataHandlerLP

    columns, control_hash = p5.control_manifest(config)
    if control_hash != protocol["control"]["feature_manifest_sha256"]:
        raise RuntimeError("BASE_157 manifest mismatch")
    projection = pd.read_parquet(args.projection_grid, columns=["session", "episode_id", "historical_ticker", "identity_excluded"])
    crosswalk = p5.build_crosswalk(projection, args.episode_map)
    crosswalk.to_parquet(args.output / "episode-crosswalk.parquet", index=False)
    handler = config(
        instruments="p2_pit", start_time=periods["train"][0], end_time=periods["historical_research_test"][1],
        fit_start_time=periods["train"][0], fit_end_time=periods["train"][1], infer_processors=[],
        learn_processors=list(p5.LEARN_PROCESSORS), filter_pipe=[close_filter()],
    )
    raw = handler.fetch(slice(periods["train"][0], periods["historical_research_test"][1]),
                        col_set=["feature", "label"], data_key=DataHandlerLP.DK_I)
    raw, mapped = p5.project_index(raw, crosswalk)
    surface = pd.concat((raw["feature"], raw["label"].iloc[:, 0].rename("__label__")), axis=1)
    validate_surface_inventory(protocol, columns, columns + [protocol["finsen_input_authority"]["factor_name"], "__label__"])
    if list(surface.columns) != columns + ["__label__"] or surface.index.has_duplicates or not surface.index.is_monotonic_increasing:
        raise RuntimeError("BASE row/column authority mismatch")
    surface.to_parquet(args.output / "control-surface.parquet", compression="zstd")
    mapped.to_parquet(args.output / "row-identity.parquet", index=False, compression="zstd")
    write_json(args.output / "prepare-report.json", {
        "protocol_sha256": PROTOCOL_SHA, "qlib_version": qlib.__version__,
        "lightgbm_version": lightgbm.__version__, "qlib_source_sha": source_sha,
        "control_feature_manifest_sha256": control_hash,
        "control_dataset_identity": protocol["control"]["dataset_identity"],
        "control_feature_count": len(columns), "row_count": len(surface),
        "row_identity_sha256": sha256(args.output / "row-identity.parquet"),
        "calendar": {"last_data_session": current[-1], "future_session": future[-1]},
        "control_surface_sha256": sha256(args.output / "control-surface.parquet"),
    })


def broadcast_parquet(source: Path, factor: Path, target: Path, factor_name: str) -> dict[str, int]:
    import duckdb

    if duckdb.__version__ != "1.5.5":
        raise RuntimeError("DuckDB runtime identity mismatch")
    temporary = target.with_name(target.stem + ".duckdb.parquet")
    if target.exists() or temporary.exists():
        raise FileExistsError(target)
    con = duckdb.connect()
    source_sql, factor_sql, target_sql = (str(item).replace("'", "''") for item in (source, factor, temporary))
    con.execute(f"CREATE VIEW base AS SELECT * FROM read_parquet('{source_sql}')")
    con.execute(f"CREATE VIEW finsen AS SELECT session,{factor_name} FROM read_parquet('{factor_sql}')")
    con.execute(f"COPY (SELECT b.* EXCLUDE (__label__), f.{factor_name}, b.__label__ FROM base b LEFT JOIN finsen f ON b.datetime=f.session ORDER BY b.datetime,b.instrument) TO '{target_sql}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    base_rows = con.execute("SELECT count(*) FROM base").fetchone()[0]
    rows = con.execute("SELECT count(*) FROM read_parquet(?)", [str(temporary)]).fetchone()[0]
    dependent = con.execute(f"SELECT count(*) FROM (SELECT datetime FROM read_parquet(?) GROUP BY datetime HAVING count(DISTINCT {factor_name}) FILTER (WHERE {factor_name} IS NOT NULL)>1)", [str(temporary)]).fetchone()[0]
    null_sessions = con.execute(f"SELECT count(*) FROM (SELECT datetime FROM read_parquet(?) GROUP BY datetime HAVING count({factor_name})=0)", [str(temporary)]).fetchone()[0]
    con.close()
    if rows != base_rows or dependent:
        raise RuntimeError("FinSen mechanical broadcast violated row/global-state authority")
    expanded = pd.read_parquet(temporary).set_index(["datetime", "instrument"])
    if expanded.index.has_duplicates or not expanded.index.is_monotonic_increasing:
        raise RuntimeError("DuckDB broadcast did not preserve canonical row order")
    expanded.to_parquet(target, compression="zstd")
    temporary.unlink()
    return {
        "row_count": rows,
        "instrument_dependent_finsen_value_count": dependent,
        "manufactured_instrument_session_row_count": rows - base_rows,
        "supported_interval_null_session_count": null_sessions,
    }


def broadcast(args) -> None:
    protocol, _ = load_authority(args.repo)
    _, factor_evidence = verify_factor(protocol, args.finsen_root)
    factor = args.finsen_root / "session-global-signal.parquet"
    report = broadcast_parquet(
        args.output / "control-surface.parquet", factor,
        args.output / "evaluation-surface.parquet", protocol["finsen_input_authority"]["factor_name"],
    )
    write_json(args.output / "finsen-broadcast-report.json", {
        "duckdb_version": "1.5.5", "factor_authority": factor_evidence, **report,
        "evaluation_surface_sha256": sha256(args.output / "evaluation-surface.parquet"),
        "zero_fill_used": False, "forward_fill_used": False, "backfill_used": False,
        "row_drop_due_to_finsen_null": False,
    })


def frame_hash(frame: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(frame, index=True).to_numpy().tobytes()).hexdigest()


def processor_gate(protocol: dict, path: Path, control: list[str], factor_name: str) -> dict:
    from qlib.data.dataset.handler import DataHandlerLP

    hashes, masks = {}, {}
    for surface, columns in (("M0", control), ("M1", control + [factor_name])):
        dataset = make_dataset(path, columns, protocol)
        identity = "->".join(type(item).__name__ for item in dataset.handler.learn_processors)
        if identity != "DropnaLabel->CSZScoreNorm":
            raise RuntimeError("frozen label processor authority mismatch")
        labels = [dataset.prepare(split, col_set="label", data_key=DataHandlerLP.DK_L) for split in ("train", "valid")]
        hashes[surface] = frame_hash(pd.concat(labels))
        raw = dataset.prepare("train", col_set="feature", data_key=DataHandlerLP.DK_R)
        learned = dataset.prepare("train", col_set="feature", data_key=DataHandlerLP.DK_L)
        masks[surface] = bool(raw.loc[learned.index].isna().equals(learned.isna()))
        del dataset, labels, raw, learned
        gc.collect()
    if hashes["M0"] != hashes["M1"] or not all(masks.values()):
        raise RuntimeError("M0/M1 transformed label or feature missingness mismatch")
    return {"processor_identity": "DropnaLabel->CSZScoreNorm(label)",
            "transformed_label_sha256": hashes["M0"], "feature_nan_positions_preserved": True}


def preflight(args) -> None:
    import pyarrow.parquet as pq

    protocol, p5 = load_authority(args.repo)
    os.chdir(args.output)
    qlib, lightgbm, config, _, source_sha, _, _ = p5.init_runtime(args, args.output)
    control, control_hash = p5.control_manifest(config)
    factor_name = protocol["finsen_input_authority"]["factor_name"]
    names = [name for name in pq.ParquetFile(args.output / "evaluation-surface.parquet").schema_arrow.names
             if name not in ("datetime", "instrument")]
    validate_surface_inventory(protocol, control, names)
    base = pd.read_parquet(args.output / "control-surface.parquet", columns=["__label__"])
    evaluation = pd.read_parquet(args.output / "evaluation-surface.parquet", columns=[factor_name, "__label__"])
    row_equal = len(base) == len(evaluation) and base.index.equals(evaluation.index)
    label_equal = base["__label__"].equals(evaluation["__label__"])
    broadcast_report = json.loads((args.output / "finsen-broadcast-report.json").read_text())
    factor_frame, factor_evidence = verify_factor(protocol, args.finsen_root)
    factor_sessions = set(factor_frame.loc[factor_frame[factor_name].isna(), "session"])
    observed_null_sessions = set(evaluation.loc[evaluation[factor_name].isna()].index.get_level_values("datetime"))
    membership_hash = sha256(args.output / "row-identity.parquet")
    if (not row_equal or not label_equal or control_hash != protocol["control"]["feature_manifest_sha256"]
            or factor_sessions != observed_null_sessions
            or broadcast_report["instrument_dependent_finsen_value_count"] != 0
            or broadcast_report["manufactured_instrument_session_row_count"] != 0
            or canonical_sha(p5.MODEL_CONFIG) != protocol["model"]["config_sha256"]):
        raise RuntimeError("FinSen preflight authority mismatch")
    gate = processor_gate(protocol, args.output / "evaluation-surface.parquet", control, factor_name)
    write_json(args.output / "preflight-report.json", {
        "schema": "AQ_P6_FINSEN_PREFLIGHT_V1", "all_gates_pass": True,
        "protocol_hash": "PASS", "control_manifest": "PASS", "control_dataset_identity": "PASS",
        "finsen_factor_identity": "PASS", "split_identity": "PASS", "surface_inventory": "PASS",
        "row_identity": "PASS", "label_identity": "PASS", "membership_identity": "PASS",
        "null_preservation": "PASS", "global_broadcast": "PASS", "qlib_runtime_identity": "PASS",
        "model_config_identity": "PASS", "protocol_sha256": PROTOCOL_SHA,
        "qlib_version": qlib.__version__, "lightgbm_version": lightgbm.__version__, "qlib_source_sha": source_sha,
        "model_config_sha256": canonical_sha(p5.MODEL_CONFIG),
        "control_feature_manifest_sha256": control_hash,
        "control_dataset_identity_value": protocol["control"]["dataset_identity"],
        "finsen_factor_sha256": factor_evidence["factor_sha256"],
        "m0_feature_count": 157, "m1_feature_count": 158,
        "m0_row_count": len(base), "m1_row_count": len(evaluation),
        "m0_m1_row_identity_equal": row_equal, "m0_m1_label_identity_equal": label_equal,
        "m0_m1_membership_identity_equal": True, "membership_identity_sha256": membership_hash,
        "supported_interval_null_session_count": len(observed_null_sessions),
        "zero_fill_used": False, "forward_fill_used": False, "backfill_used": False,
        "row_drop_due_to_finsen_null": False,
        "instrument_dependent_finsen_value_count": 0,
        "manufactured_instrument_session_row_count": 0,
        "processor_gate": gate, "p2_v2_sealed_oos_accessed": False,
    })


def fit(args) -> None:
    protocol, p5 = load_authority(args.repo)
    if args.surface_id not in ("M0", "M1"):
        raise RuntimeError("fit requires one frozen surface")
    preflight = json.loads((args.output / "preflight-report.json").read_text())
    if not preflight["all_gates_pass"]:
        raise RuntimeError("fit requires passed preflight")
    attempt = args.output / f"{args.surface_id.lower()}-fit-attempt.json"
    write_json(attempt, {"surface": args.surface_id, "model_fit_attempt_count": 1, "protocol_sha256": PROTOCOL_SHA})
    os.chdir(args.output)
    _, _, config, _, _, _, _ = p5.init_runtime(args, args.output)
    control, _ = p5.control_manifest(config)
    factor_name = protocol["finsen_input_authority"]["factor_name"]
    columns = control + ([factor_name] if args.surface_id == "M1" else [])
    from qlib.contrib.model.gbdt import LGBModel
    from qlib.workflow import R
    from qlib.workflow.record_temp import SigAnaRecord, SignalRecord

    dataset, model = make_dataset(args.output / "evaluation-surface.parquet", columns, protocol), LGBModel(**p5.MODEL_CONFIG)
    with R.start(experiment_name=EXPERIMENT, recorder_name=args.surface_id):
        recorder = R.get_recorder()
        recorder.log_params(
            task="AUTONOMOUS_QUANT_P6_HISTORICAL_NEWS_FINSEN_FIRST_AUTHORIZED_ABLATION_001",
            surface=args.surface_id, protocol_sha256=PROTOCOL_SHA,
            model_config_sha256=protocol["model"]["config_sha256"],
            control_dataset_identity=protocol["control"]["dataset_identity"], column_count=len(columns),
        )
        model.fit(dataset, verbose_eval=20)
        SignalRecord(model=model, dataset=dataset, recorder=recorder).generate()
        SigAnaRecord(recorder=recorder, ana_long_short=False, ann_scaler=252).generate()
        recorder_id = recorder.id
    recorded = R.get_recorder(recorder_id=recorder_id, experiment_name=EXPERIMENT)
    prediction, rank_ic = recorded.load_object("pred.pkl"), recorded.load_object("sig_analysis/ric.pkl")
    prediction = (prediction.iloc[:, 0] if isinstance(prediction, pd.DataFrame) else prediction).rename("score").sort_index()
    prediction_path, rank_path = args.output / f"{args.surface_id.lower()}-prediction.pkl", args.output / f"{args.surface_id.lower()}-rank-ic.pkl"
    prediction.to_pickle(prediction_path)
    pd.to_pickle(rank_ic, rank_path)
    write_json(args.output / f"{args.surface_id.lower()}-fit-report.json", {
        "surface": args.surface_id, "recorder_id": recorder_id, "feature_count": len(columns),
        "model_fit_completed_count": 1, "prediction_count": 1, "prediction_rows": len(prediction),
        "prediction_sha256": sha256(prediction_path), "rank_ic": float(rank_ic.mean()),
        "rank_ic_sha256": sha256(rank_path), "best_iteration": int(model.model.best_iteration),
    })


def compose(args) -> None:
    protocol, p5 = load_authority(args.repo)
    os.chdir(args.output)
    qlib, lightgbm, config, _, source_sha, _, _ = p5.init_runtime(args, args.output)
    results = {surface: json.loads((args.output / f"{surface.lower()}-fit-report.json").read_text()) for surface in ("M0", "M1")}
    crosswalk = pd.read_parquet(args.output / "episode-crosswalk.parquet")
    rehearsal = load_module(args.repo / "40-certification-system/historical-rehearsal/qlib_rehearsal.py", "qlib_rehearsal")
    test = protocol["splits"]["historical_research_test"]
    # The shared P2 reference owns the backtest mechanics but carries P2's
    # longer module-level test interval. Bind that public mechanic to this
    # preregistered comparison's shorter common-support interval.
    rehearsal.TEST = tuple(test)
    (args.output / "portfolio").mkdir()
    portfolio, returns = {}, []
    for surface in ("M0", "M1"):
        prediction = pd.read_pickle(args.output / f"{surface.lower()}-prediction.pkl")
        evidence = rehearsal.run_backtest(surface, p5.p2_prediction(prediction, crosswalk), 30, 3, "BASE", (0.0005, 0.0015), args.output)
        returns.append(evidence.pop("net").rename(surface))
        portfolio[surface] = evidence
    daily = pd.concat(returns, axis=1).sort_index()
    if (daily.isna().any().any() or not np.isfinite(daily.to_numpy()).all()
            or daily.index.min().strftime("%Y-%m-%d") != test[0]
            or daily.index.max().strftime("%Y-%m-%d") != test[1]):
        raise RuntimeError("M0/M1 daily return evidence is incomplete")
    daily.index.name = "date"
    daily.to_csv(args.output / "daily-net-returns.csv", lineterminator="\n", float_format="%.17g")
    control, control_hash = p5.control_manifest(config)
    preflight = json.loads((args.output / "preflight-report.json").read_text())
    write_json(args.output / "surface-manifest.json", {
        "protocol_sha256": PROTOCOL_SHA, "control_dataset_identity": protocol["control"]["dataset_identity"],
        "control_feature_manifest_sha256": control_hash,
        "evaluation_surface_sha256": sha256(args.output / "evaluation-surface.parquet"),
        "row_identity_sha256": sha256(args.output / "row-identity.parquet"),
        "row_count": preflight["m0_row_count"], "m0_columns": control,
        "m1_increment": [protocol["finsen_input_authority"]["factor_name"]],
        "label": protocol["label_and_processors"]["label"], "finsen_null_pattern_preserved": True,
    })
    write_json(args.output / "qlib-report.json", {
        "qlib_version": qlib.__version__, "qlib_source_sha": source_sha,
        "lightgbm_version": lightgbm.__version__, "model": protocol["model"]["class"],
        "model_config_sha256": protocol["model"]["config_sha256"], "m0": results["M0"], "m1": results["M1"],
        "rank_ic_delta": results["M1"]["rank_ic"] - results["M0"]["rank_ic"],
        "portfolio": portfolio, "daily_return_rows": len(daily),
        "daily_net_returns_sha256": sha256(args.output / "daily-net-returns.csv"),
    })


def statistics(args) -> None:
    import arch as arch_package
    import skfolio
    from arch.bootstrap import RealityCheck, SPA
    from skfolio.model_selection import CombinatorialPurgedCV, WalkForward

    protocol, _ = load_authority(args.repo)
    if (skfolio.__version__ != protocol["upstream_identities"]["skfolio_version"]
            or arch_package.__version__ != protocol["upstream_identities"]["arch_version"]):
        raise RuntimeError("statistics runtime identity mismatch")
    frame = pd.read_csv(args.output / "daily-net-returns.csv", parse_dates=["date"]).set_index("date")
    try:
        wf = list(WalkForward(test_size=63, train_size=504, purged_size=2,
                              expand_train=False, reduce_test=False).split(frame.to_numpy()))
        cpcv = list(CombinatorialPurgedCV(n_folds=10, n_test_folds=2, purged_size=2,
                                          embargo_size=2).split(frame.to_numpy()))
    except ValueError as error:
        write_json(args.output / "statistical-failure-report.json", {
            "classification": "INCOMPLETE_REQUIRED_STATISTICAL_EVIDENCE",
            "error_type": type(error).__name__, "error": str(error),
            "observation_count": len(frame), "walkforward_train_size": 504,
            "walkforward_purged_size": 2, "protocol_changed": False,
        })
        write_json(args.output / "classification-report.json", {
            "final_scientific_classification": "INCONCLUSIVE",
            "next_task": "P6_HISTORICAL_NEWS_FINSEN_INCONCLUSIVE_CLOSEOUT_OR_EXACT_RECOVERY_001",
            "reason": "FROZEN_WALKFORWARD_REQUIRES_AT_LEAST_506_OBSERVATIONS_BUT_TEST_HAS_385",
            "scientific_hypothesis_count": 1, "ablation_count": 1,
            "model_training_count": 2, "prediction_count": 2, "backtest_count": 2,
            "aq_outcome_data_accessed": True, "performance_based_branching_between_fits": False,
            "p2_v2_sealed_oos_accessed": False, "p2_v2_sealed_oos_result_used": False,
        })
        return
    reference = load_module(args.repo / "40-certification-system/historical-rehearsal/evaluate_rehearsal.py", "rehearsal_evaluator")
    temporal, arch_results = {}, {}
    for name, candidate, control in (("M1_MINUS_M0", "M1", "M0"), ("M0_MINUS_M1", "M0", "M1")):
        temporal[name] = {
            "walkforward": reference.reduce_splits(reference.split_evidence(frame, [test for _, test in wf], candidate, control)),
            "cpcv": reference.reduce_splits(reference.split_evidence(frame, [np.sort(np.concatenate(groups)) for _, groups in cpcv], candidate, control)),
        }
        spa = SPA(-frame[control], -frame[[candidate]], block_size=10, reps=5000, bootstrap="stationary", seed=20260913)
        reality = RealityCheck(-frame[control], -frame[[candidate]], block_size=10, reps=5000, bootstrap="stationary", seed=20260913)
        spa.compute()
        reality.compute()
        arch_results[name] = {
            "spa_consistent_pvalue": float(spa.pvalues.loc["consistent"]),
            "reality_check_consistent_pvalue": float(reality.pvalues.loc["consistent"]),
        }
    temporal_report = {"skfolio_version": skfolio.__version__, "directions": temporal}
    arch_report = {"arch_version": arch_package.__version__, "policy": protocol["arch_tests"], "directions": arch_results}
    write_json(args.output / "skfolio-report.json", temporal_report)
    write_json(args.output / "arch-report.json", arch_report)
    qlib_report = json.loads((args.output / "qlib-report.json").read_text())
    result = classify(qlib_report["m0"]["rank_ic"], qlib_report["m1"]["rank_ic"], temporal_report, arch_report)
    next_task = {
        "INCREMENTAL_VALUE_SUPPORTED": "P6_HISTORICAL_NEWS_FINSEN_POSITIVE_RESULT_CLOSEOUT_001",
        "NO_MEASURABLE_INCREMENTAL_VALUE": "P6_HISTORICAL_NEWS_FINSEN_NEGATIVE_RESULT_CLOSEOUT_001",
        "DEGRADED": "P6_HISTORICAL_NEWS_FINSEN_NEGATIVE_RESULT_CLOSEOUT_001",
        "INCONCLUSIVE": "P6_HISTORICAL_NEWS_FINSEN_INCONCLUSIVE_CLOSEOUT_OR_EXACT_RECOVERY_001",
    }[result]
    write_json(args.output / "classification-report.json", {
        "final_scientific_classification": result, "next_task": next_task,
        "scientific_hypothesis_count": 1, "ablation_count": 1,
        "model_training_count": 2, "prediction_count": 2, "backtest_count": 2,
        "aq_outcome_data_accessed": True, "performance_based_branching_between_fits": False,
        "p2_v2_sealed_oos_accessed": False, "p2_v2_sealed_oos_result_used": False,
    })


def finalize(args) -> None:
    common = (
        "prepare-report.json", "finsen-broadcast-report.json", "preflight-report.json",
        "m0-fit-attempt.json", "m1-fit-attempt.json", "m0-fit-report.json", "m1-fit-report.json",
        "qlib-report.json", "daily-net-returns.csv", "classification-report.json", "surface-manifest.json",
    )
    complete_statistics = all((args.output / name).is_file() for name in ("skfolio-report.json", "arch-report.json"))
    exact_failure = (args.output / "statistical-failure-report.json").is_file()
    if not all((args.output / name).is_file() for name in common) or not (complete_statistics or exact_failure):
        raise RuntimeError("required final FinSen evidence is incomplete")
    write_json(args.output / "attempt-ledger.json", {
        "authorized_ablation_count": 1, "model_training_count": 2,
        "m0_fit_attempt_count": 1, "m1_fit_attempt_count": 1,
        "model_refit_count_after_initial_compose_boundary_failure": 0,
        "initial_compose_boundary_failure": "SHARED_P2_REFERENCE_TEST_END_2024_12_31",
        "exact_recovery": "REBIND_SHARED_BACKTEST_TO_FROZEN_FINSEN_TEST_INTERVAL",
        "required_statistics_completed": complete_statistics,
        "terminal_runtime_classification": "INCONCLUSIVE" if exact_failure else "COMPLETE",
        "protocol_changing_rerun_authorized": False,
    })
    files = sorted(path for path in args.output.rglob("*") if path.is_file() and path.name != "checksums.json")
    write_json(args.output / "checksums.json", {
        str(path.relative_to(args.output)).replace("\\", "/"): sha256(path) for path in files
    })


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("mode", choices=("prepare", "broadcast", "preflight", "fit", "compose", "statistics", "finalize"))
    result.add_argument("--repo", required=True, type=Path)
    result.add_argument("--output", required=True, type=Path)
    result.add_argument("--provider", type=Path)
    result.add_argument("--provider-report", type=Path)
    result.add_argument("--calendar-runtime", type=Path)
    result.add_argument("--episode-map", type=Path)
    result.add_argument("--projection-grid", type=Path)
    result.add_argument("--qlib-source", type=Path)
    result.add_argument("--finsen-root", type=Path)
    result.add_argument("--surface-id", choices=("M0", "M1"))
    return result


def main() -> None:
    args = parser().parse_args()
    {"prepare": prepare, "broadcast": broadcast, "preflight": preflight, "fit": fit,
     "compose": compose, "statistics": statistics, "finalize": finalize}[args.mode](args)


if __name__ == "__main__":
    main()
