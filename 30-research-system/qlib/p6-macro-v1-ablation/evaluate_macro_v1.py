"""Execute the frozen P6 Macro V1 M0-versus-M1 research comparison."""

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


PROTOCOL_SHA = "5aad8128f9473558689b602edc91850022b0667826ee0dd8eb126fab7c58b116"
EXPERIMENT = "p6_macro_v1_ablation_001"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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
    protocol_path = repo / "30-research-system/qlib/p6-macro-v1-ablation/macro-v1-ablation-protocol.json"
    if sha256(protocol_path) != PROTOCOL_SHA:
        raise RuntimeError("frozen protocol identity mismatch")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    p5 = load_module(repo / "30-research-system/qlib/p5-h1-evaluation/evaluate_h1.py", "p5_h1_authority")
    if protocol["model"]["config"] != p5.MODEL_CONFIG or canonical_sha(p5.MODEL_CONFIG) != protocol["model"]["config_sha256"]:
        raise RuntimeError("P5 vehicle/model identity mismatch")
    if protocol["control"]["dataset_identity"] != p5.CONTROL_DATASET_IDENTITY:
        raise RuntimeError("control dataset identity mismatch")
    expected = {"train": list(p5.TRAIN), "validation": list(p5.VALID), "historical_research_test": list(p5.TEST)}
    if protocol["splits"] != expected:
        raise RuntimeError("split authority mismatch")
    return protocol, p5


def logical_sha(frame: pd.DataFrame) -> str:
    normalized = frame.sort_index().sort_index(axis=1)
    raw = normalized.to_json(orient="table", date_format="iso", date_unit="ns", double_precision=15).encode()
    return hashlib.sha256(raw).hexdigest()


def verify_macro(protocol: dict, root: Path) -> dict:
    authority = protocol["macro_input_authority"]
    manifest_path = root / "manifest.json"
    if sha256(manifest_path) != authority["manifest_sha256"]:
        raise RuntimeError("Macro manifest identity mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {
        "evidence": authority["evidence_logical_sha256"],
        "macro_state": authority["macro_state_logical_sha256"],
        "provenance": authority["provenance_logical_sha256"],
    }
    paths = {"evidence": "evidence.parquet", "macro_state": "macro-state.parquet", "provenance": "provenance.parquet"}
    actual = {key: logical_sha(pd.read_parquet(root / name)) for key, name in paths.items()}
    if actual != expected or manifest["logical_sha256"] != expected:
        raise RuntimeError("Macro logical content identity mismatch")
    if manifest["feature_ids"] != authority["feature_ids"] or manifest["p2_v2_sealed_oos_accessed"]:
        raise RuntimeError("Macro feature/safety authority mismatch")
    return {"manifest_sha256": sha256(manifest_path), "logical_sha256": actual, "feature_ids": manifest["feature_ids"]}


def validate_surface_inventory(protocol: dict, control: list[str], evaluation: list[str]) -> None:
    macro = protocol["macro_input_authority"]["feature_ids"]
    if len(control) != protocol["control"]["feature_column_count"] or evaluation != control + macro + ["__label__"]:
        raise RuntimeError("frozen M0/M1 surface inventory mismatch")
    forbidden = {"GDP", "GDPC1", "Revenue", "NetIncome", "Assets", "Liabilities", "CommonEquity"}
    if forbidden.intersection(evaluation):
        raise RuntimeError("excluded feature family entered Macro V1 surface")


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


def prepare(args) -> None:
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    os.chdir(args.output)
    protocol, p5 = load_authority(args.repo)
    qlib, lightgbm, config, close_filter, source_sha, current, future = p5.init_runtime(args, args.output)
    from qlib.data.dataset.handler import DataHandlerLP

    columns, control_hash = p5.control_manifest(config)
    if control_hash != protocol["control"]["feature_manifest_sha256"]:
        raise RuntimeError("BASE_157 manifest mismatch")
    projection = pd.read_parquet(args.projection_grid, columns=["session", "episode_id", "historical_ticker", "identity_excluded"])
    crosswalk = p5.build_crosswalk(projection, args.episode_map)
    crosswalk.to_parquet(args.output / "episode-crosswalk.parquet", index=False)
    handler = config(instruments="p2_pit", start_time=p5.TRAIN[0], end_time=p5.TEST[1],
                     fit_start_time=p5.TRAIN[0], fit_end_time=p5.TRAIN[1], infer_processors=[],
                     learn_processors=list(p5.LEARN_PROCESSORS), filter_pipe=[close_filter()])
    raw = handler.fetch(slice(p5.TRAIN[0], p5.TEST[1]), col_set=["feature", "label"], data_key=DataHandlerLP.DK_I)
    raw, mapped = p5.project_index(raw, crosswalk)
    surface = pd.concat((raw["feature"], raw["label"].iloc[:, 0].rename("__label__")), axis=1)
    planned = columns + protocol["macro_input_authority"]["feature_ids"] + ["__label__"]
    validate_surface_inventory(protocol, columns, planned)
    if list(surface.columns) != columns + ["__label__"] or surface.index.has_duplicates or not surface.index.is_monotonic_increasing:
        raise RuntimeError("BASE row/column authority mismatch")
    surface.to_parquet(args.output / "control-surface.parquet", compression="zstd")
    mapped.to_parquet(args.output / "row-identity.parquet", index=False, compression="zstd")
    write_json(args.output / "prepare-report.json", {
        "protocol_sha256": PROTOCOL_SHA, "qlib_version": qlib.__version__, "lightgbm_version": lightgbm.__version__,
        "qlib_source_sha": source_sha, "control_feature_manifest_sha256": control_hash,
        "control_dataset_identity": protocol["control"]["dataset_identity"], "control_feature_count": len(columns),
        "row_count": len(surface), "calendar": {"last_data_session": current[-1], "future_session": future[-1]},
        "control_surface_sha256": sha256(args.output / "control-surface.parquet"),
        "p5_projection_used_for_row_identity_only": True, "p5_fundamental_feature_value_count": 0,
    })


def broadcast_parquet(source: Path, state: Path, target: Path) -> dict[str, int]:
    import duckdb

    if duckdb.__version__ != "1.5.5":
        raise RuntimeError("DuckDB runtime identity mismatch")
    temporary = target.with_name(target.stem + ".duckdb.parquet")
    if target.exists() or temporary.exists():
        raise FileExistsError(target)
    con = duckdb.connect()
    source_sql = str(source).replace("'", "''")
    state_sql = str(state).replace("'", "''")
    target_sql = str(temporary).replace("'", "''")
    con.execute(f"CREATE VIEW base AS SELECT * FROM read_parquet('{source_sql}')")
    con.execute(f"CREATE VIEW macro AS SELECT * FROM read_parquet('{state_sql}')")
    con.execute(f"COPY (SELECT b.* EXCLUDE (__label__), m.macro_v1_cpiaucsl_d2_log, m.macro_v1_unrate_d1, b.__label__ FROM base b LEFT JOIN macro m ON b.datetime=m.session ORDER BY b.datetime,b.instrument) TO '{target_sql}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    rows = con.execute("SELECT count(*), count(*) FILTER (WHERE macro_v1_cpiaucsl_d2_log IS NULL OR macro_v1_unrate_d1 IS NULL) FROM read_parquet(?)", [str(temporary)]).fetchone()
    dependent = con.execute("SELECT count(*) FROM (SELECT datetime FROM read_parquet(?) GROUP BY datetime HAVING count(DISTINCT macro_v1_cpiaucsl_d2_log)>1 OR count(DISTINCT macro_v1_unrate_d1)>1)", [str(temporary)]).fetchone()[0]
    base_rows = con.execute("SELECT count(*) FROM read_parquet(?)", [str(source)]).fetchone()[0]
    if rows[0] != base_rows or rows[1] or dependent:
        raise RuntimeError("Macro mechanical broadcast violated row/global-state authority")
    con.close()
    expanded = pd.read_parquet(temporary).set_index(["datetime", "instrument"])
    if expanded.index.has_duplicates or not expanded.index.is_monotonic_increasing:
        raise RuntimeError("DuckDB broadcast did not preserve canonical row order")
    expanded.to_parquet(target, compression="zstd")
    temporary.unlink()
    return {"row_count": rows[0], "instrument_dependent_macro_value_count": dependent,
            "manufactured_instrument_session_row_count": rows[0] - base_rows}


def broadcast(args) -> None:
    protocol, _ = load_authority(args.repo)
    macro = verify_macro(protocol, args.macro_root)
    source = args.output / "control-surface.parquet"
    state = args.macro_root / "macro-state.parquet"
    target = args.output / "evaluation-surface.parquet"
    report = broadcast_parquet(source, state, target)
    write_json(args.output / "macro-broadcast-report.json", {
        "duckdb_version": "1.5.5", "macro_authority": macro, **report,
        "evaluation_surface_sha256": sha256(target), "fred_network_request_count": 0,
    })


def frame_hash(frame: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(frame, index=True).to_numpy().tobytes()).hexdigest()


def processor_gate(p5, path: Path, control: list[str], macro: list[str]) -> dict:
    from qlib.data.dataset.handler import DataHandlerLP

    hashes, identities = {}, {}
    for surface, columns in (("M0", control), ("M1", control + macro)):
        dataset = p5.make_dataset(path, columns)
        identity = "->".join(type(item).__name__ for item in dataset.handler.learn_processors)
        if identity != "DropnaLabel->CSZScoreNorm":
            raise RuntimeError("frozen label processor authority mismatch")
        labels = [dataset.prepare(split, col_set="label", data_key=DataHandlerLP.DK_L) for split in ("train", "valid")]
        hashes[surface] = frame_hash(pd.concat(labels))
        identities[surface] = identity + "(label)"
        del dataset, labels
        gc.collect()
    if hashes["M0"] != hashes["M1"]:
        raise RuntimeError("M0/M1 transformed labels differ")
    return {"processor_identity": identities, "transformed_label_sha256": hashes["M0"]}


def preflight(args) -> None:
    import pyarrow.parquet as pq

    protocol, p5 = load_authority(args.repo)
    os.chdir(args.output)
    qlib, lightgbm, config, _, source_sha, _, _ = p5.init_runtime(args, args.output)
    control, control_hash = p5.control_manifest(config)
    macro = protocol["macro_input_authority"]["feature_ids"]
    names = [name for name in pq.ParquetFile(args.output / "evaluation-surface.parquet").schema_arrow.names if name not in ("datetime", "instrument")]
    validate_surface_inventory(protocol, control, names)
    base = pd.read_parquet(args.output / "control-surface.parquet", columns=["__label__"])
    evaluation = pd.read_parquet(args.output / "evaluation-surface.parquet", columns=["__label__"])
    row_equal, index_equal = len(base) == len(evaluation), base.index.equals(evaluation.index)
    label_equal = base["__label__"].equals(evaluation["__label__"])
    missing_equal = base["__label__"].isna().equals(evaluation["__label__"].isna())
    broadcast_report = json.loads((args.output / "macro-broadcast-report.json").read_text())
    if not all((row_equal, index_equal, label_equal, missing_equal)) or control_hash != protocol["control"]["feature_manifest_sha256"]:
        raise RuntimeError("M0/M1 row or label identity mismatch")
    gate = processor_gate(p5, args.output / "evaluation-surface.parquet", control, macro)
    write_json(args.output / "preflight-report.json", {
        "schema": "AQ_P6_MACRO_V1_PREFLIGHT_V1", "protocol_sha256": PROTOCOL_SHA,
        "qlib_version": qlib.__version__, "lightgbm_version": lightgbm.__version__, "qlib_source_sha": source_sha,
        "model_config_sha256": canonical_sha(p5.MODEL_CONFIG), "control_feature_manifest_sha256": control_hash,
        "control_dataset_identity": protocol["control"]["dataset_identity"], "m0_feature_count": len(control),
        "m1_feature_count": len(control + macro), "macro_increment_feature_count": len(macro), "row_count": len(base),
        "m0_m1_row_count_equal": row_equal, "m0_m1_index_equal": index_equal,
        "m0_m1_label_values_equal": label_equal, "m0_m1_label_missingness_equal": missing_equal,
        "instrument_dependent_macro_value_count": broadcast_report["instrument_dependent_macro_value_count"],
        "manufactured_instrument_session_row_count": broadcast_report["manufactured_instrument_session_row_count"],
        "processor_gate": gate, "p5_fundamental_feature_value_count_m0": 0,
        "p5_fundamental_feature_value_count_m1": 0, "p2_v2_sealed_oos_accessed": False,
    })


def fit(args) -> None:
    protocol, p5 = load_authority(args.repo)
    if not (args.output / "preflight-report.json").is_file() or args.surface_id not in ("M0", "M1"):
        raise RuntimeError("fit requires a passed preflight and one frozen surface")
    attempt = args.output / f"{args.surface_id.lower()}-fit-attempt.json"
    write_json(attempt, {"surface": args.surface_id, "model_fit_attempt_count": 1, "protocol_sha256": PROTOCOL_SHA})
    os.chdir(args.output)
    _, _, config, _, _, _, _ = p5.init_runtime(args, args.output)
    control, _ = p5.control_manifest(config)
    columns = control + (protocol["macro_input_authority"]["feature_ids"] if args.surface_id == "M1" else [])
    from qlib.contrib.model.gbdt import LGBModel
    from qlib.workflow import R
    from qlib.workflow.record_temp import SigAnaRecord, SignalRecord

    dataset, model = p5.make_dataset(args.output / "evaluation-surface.parquet", columns), LGBModel(**p5.MODEL_CONFIG)
    with R.start(experiment_name=EXPERIMENT, recorder_name=args.surface_id):
        recorder = R.get_recorder()
        recorder.log_params(task="AUTONOMOUS_QUANT_P6_MACRO_V1_FIRST_AUTHORIZED_ABLATION_EXECUTION_001",
                            surface=args.surface_id, protocol_sha256=PROTOCOL_SHA,
                            model_config_sha256=protocol["model"]["config_sha256"],
                            control_dataset_identity=protocol["control"]["dataset_identity"], column_count=len(columns))
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
    (args.output / "portfolio").mkdir()
    portfolio, returns = {}, []
    for surface in ("M0", "M1"):
        prediction = pd.read_pickle(args.output / f"{surface.lower()}-prediction.pkl")
        evidence = rehearsal.run_backtest(surface, p5.p2_prediction(prediction, crosswalk), 30, 3, "BASE", (0.0005, 0.0015), args.output)
        returns.append(evidence.pop("net").rename(surface))
        portfolio[surface] = evidence
    daily = pd.concat(returns, axis=1).sort_index()
    test = protocol["splits"]["historical_research_test"]
    if daily.isna().any().any() or not np.isfinite(daily.to_numpy()).all() or daily.index.min().strftime("%Y-%m-%d") != test[0] or daily.index.max().strftime("%Y-%m-%d") != test[1]:
        raise RuntimeError("M0/M1 daily return evidence is incomplete")
    daily.index.name = "date"
    daily.to_csv(args.output / "daily-net-returns.csv", lineterminator="\n", float_format="%.17g")
    control, control_hash = p5.control_manifest(config)
    write_json(args.output / "surface-manifest.json", {
        "protocol_sha256": PROTOCOL_SHA, "control_dataset_identity": protocol["control"]["dataset_identity"],
        "control_feature_manifest_sha256": control_hash, "evaluation_surface_sha256": sha256(args.output / "evaluation-surface.parquet"),
        "row_identity_sha256": sha256(args.output / "row-identity.parquet"), "row_count": json.loads((args.output / "preflight-report.json").read_text())["row_count"],
        "m0_columns": control, "m1_increment": protocol["macro_input_authority"]["feature_ids"], "label": protocol["label_and_processors"]["label"],
    })
    write_json(args.output / "qlib-report.json", {
        "qlib_version": qlib.__version__, "qlib_source_sha": source_sha, "lightgbm_version": lightgbm.__version__,
        "model": protocol["model"]["class"], "model_config_sha256": protocol["model"]["config_sha256"],
        "m0": results["M0"], "m1": results["M1"], "rank_ic_delta": results["M1"]["rank_ic"] - results["M0"]["rank_ic"],
        "portfolio": portfolio, "daily_return_rows": len(daily), "daily_net_returns_sha256": sha256(args.output / "daily-net-returns.csv"),
    })


def statistics(args) -> None:
    import arch as arch_package
    import skfolio
    from arch.bootstrap import RealityCheck, SPA
    from skfolio.model_selection import CombinatorialPurgedCV, WalkForward

    protocol, _ = load_authority(args.repo)
    if skfolio.__version__ != protocol["upstream_identities"]["skfolio_version"] or arch_package.__version__ != protocol["upstream_identities"]["arch_version"]:
        raise RuntimeError("statistics runtime identity mismatch")
    frame = pd.read_csv(args.output / "daily-net-returns.csv", parse_dates=["date"]).set_index("date")
    wf = list(WalkForward(test_size=63, train_size=504, purged_size=2, expand_train=False, reduce_test=False).split(frame.to_numpy()))
    cpcv = list(CombinatorialPurgedCV(n_folds=10, n_test_folds=2, purged_size=2, embargo_size=2).split(frame.to_numpy()))
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
        arch_results[name] = {"spa_consistent_pvalue": float(spa.pvalues.loc["consistent"]),
                              "reality_check_consistent_pvalue": float(reality.pvalues.loc["consistent"])}
    temporal_report = {"skfolio_version": skfolio.__version__, "directions": temporal}
    arch_report = {"arch_version": arch_package.__version__, "policy": protocol["arch_tests"], "directions": arch_results}
    write_json(args.output / "skfolio-report.json", temporal_report)
    write_json(args.output / "arch-report.json", arch_report)
    qlib_report = json.loads((args.output / "qlib-report.json").read_text())
    result = classify(qlib_report["m0"]["rank_ic"], qlib_report["m1"]["rank_ic"], temporal_report, arch_report)
    next_task = {"INCREMENTAL_VALUE_SUPPORTED": "P6_MACRO_V1_POSITIVE_RESULT_CLOSEOUT_001",
                 "NO_MEASURABLE_INCREMENTAL_VALUE": "P6_MACRO_V1_NEGATIVE_RESULT_CLOSEOUT_001",
                 "DEGRADED": "P6_MACRO_V1_DEGRADED_RESULT_CLOSEOUT_001", "INCONCLUSIVE": "P6_MACRO_V1_EXACT_RECOVERY_DECISION_001"}[result]
    write_json(args.output / "classification-report.json", {
        "final_scientific_classification": result, "post_result_macro_v1_status": protocol["classifications"][result]["retention"],
        "next_task": next_task, "scientific_hypothesis_count": 1, "ablation_count": 1,
        "model_fit_attempt_count": 2, "model_fit_completed_count": 2, "prediction_count": 2, "backtest_surface_count": 2,
        "performance_based_branching_between_fits": False, "p2_v2_sealed_oos_accessed": False, "p2_v2_sealed_oos_result_used": False,
    })


def finalize(args) -> None:
    required = ("preflight-report.json", "qlib-report.json", "skfolio-report.json",
                "arch-report.json", "classification-report.json")
    if not all((args.output / name).is_file() for name in required):
        raise RuntimeError("required final evidence is incomplete")
    files = sorted(path for path in args.output.rglob("*") if path.is_file() and path.name != "checksums.json")
    write_json(args.output / "checksums.json", {str(path.relative_to(args.output)).replace("\\", "/"): sha256(path) for path in files})


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
    result.add_argument("--macro-root", type=Path)
    result.add_argument("--surface-id", choices=("M0", "M1"))
    return result


def main() -> None:
    args = parser().parse_args()
    {"prepare": prepare, "broadcast": broadcast, "preflight": preflight, "fit": fit,
     "compose": compose, "statistics": statistics, "finalize": finalize}[args.mode](args)


if __name__ == "__main__":
    main()
