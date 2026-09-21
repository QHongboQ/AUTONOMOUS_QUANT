"""Thin P5 S0/S1/S2 composition and native Qlib evaluation boundaries."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
CONTROL_FEATURE_MANIFEST_SHA256 = "7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463"
CONTROL_DATASET_IDENTITY = "P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135"
_CANDLE = "KMID KLEN KMID2 KUP KUP2 KLOW KLOW2 KSFT KSFT2 OPEN0 HIGH0 LOW0".split()
_WINDOWED = "ROC MA STD BETA RSQR RESI MAX MIN QTLU QTLD RANK RSV IMAX IMIN IMXD CORR CORD CNTP CNTN CNTD SUMP SUMN SUMD VMA VSTD WVMA VSUMP VSUMN VSUMD".split()
CONTROL_FEATURES = tuple(_CANDLE + [f"{name}{window}" for name in _WINDOWED for window in (5, 10, 20, 30, 60)])
FUNDAMENTAL_FEATURES = tuple("Revenue NetIncome Assets Liabilities CommonEquity NetCashFromOperatingActivities CashAndCashEquivalents CurrentAssetsTotal CurrentLiabilitiesTotal ShortTermDebt LongTermDebt".split())
FILING_FEATURES = tuple("p5_filing_lag_days_v1 p5_accepted_after_market_close_v1 p5_is_amendment_v1 p5_press_release_exhibit_present_v1 p5_authorized_exhibit_count_v1".split())
KEY_COLUMNS = ("datetime", "episode_id", "cik", "identity_exclusion", "label")
LGB_KWARGS: dict[str, Any] = {
    "loss": "mse", "colsample_bytree": 0.8879, "learning_rate": 0.2,
    "subsample": 0.8789, "lambda_l1": 205.6999, "lambda_l2": 580.9768,
    "max_depth": 8, "num_leaves": 210, "num_threads": 8, "device_type": "cpu",
    "deterministic": True, "force_col_wise": True, "force_row_wise": False,
    "seed": 20260913, "data_random_seed": 1, "feature_fraction_seed": 2,
    "bagging_seed": 3, "drop_seed": 4, "objective_seed": 5, "extra_seed": 6,
    "use_missing": True, "zero_as_missing": False, "bagging_freq": 0,
}
def _digest(value: Path | object) -> str:
    body = value.read_bytes() if isinstance(value, Path) else json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode()
    return hashlib.sha256(body).hexdigest()
def _validate(frame: pd.DataFrame, features: tuple[str, ...]) -> pd.DataFrame:
    import pandera.pandas as pa
    if list(frame) != [*KEY_COLUMNS, *features]:
        raise ValueError("surface column order differs from the frozen manifest")
    schema = pa.DataFrameSchema({
        "datetime": pa.Column(pa.DateTime), "episode_id": pa.Column(str),
        "cik": pa.Column(str, nullable=True), "identity_exclusion": pa.Column(bool),
        "label": pa.Column(float, nullable=True),
        **{name: pa.Column(float, nullable=True) for name in features},
    }, strict=True, coerce=True)
    result = schema.validate(frame)
    if result.duplicated(["datetime", "episode_id"]).any():
        raise ValueError("duplicate (datetime, episode_id) surface index")
    expected = result.sort_values(["datetime", "episode_id"])[["datetime", "episode_id"]].reset_index(drop=True)
    if not expected.equals(result[["datetime", "episode_id"]].reset_index(drop=True)):
        raise ValueError("surface rows are not ordered by datetime then episode_id")
    return result
def _join(left: pd.DataFrame, right: pd.DataFrame, features: tuple[str, ...]) -> pd.DataFrame:
    if list(right) != ["datetime", "episode_id", "cik", *features]:
        raise ValueError("increment has an unexpected feature inventory or order")
    if right.duplicated(["datetime", "episode_id"]).any():
        raise ValueError("duplicate increment index")
    merged = left.merge(right, on=["datetime", "episode_id"], how="left", sort=False,
                        validate="one_to_one", suffixes=("", "_increment"))
    conflict = merged["cik_increment"].notna() & (
        merged["cik_increment"].astype(str).str.zfill(10) != merged["cik"].astype(str).str.zfill(10)
    )
    if conflict.any():
        raise ValueError("cross-CIK increment")
    return merged.drop(columns="cik_increment")
def compose_surfaces(*, base_path: Path, fundamentals_path: Path, filing_path: Path,
                     filing_ledger_path: Path, output_root: Path) -> dict[str, dict[str, object]]:
    """Compose exact S0/S1/S2 surfaces with the P1 grid as left authority."""
    if output_root.exists():
        raise FileExistsError(output_root)
    base, fundamentals, filing, ledger = map(pd.read_parquet, (
        base_path, fundamentals_path, filing_path, filing_ledger_path,
    ))
    if list(base) != [*KEY_COLUMNS, *CONTROL_FEATURES]:
        raise ValueError("S0 feature family/order does not match frozen CONTROL")
    if not ledger.empty:
        bad_zero = ledger["missingness_status"].notna() & (ledger["missingness_status"] != "VALIDATED_ABSENCE") & (ledger["value"] == 0)
        early = pd.to_datetime(ledger["datetime"]) < pd.to_datetime(ledger["first_available_xnys_session"])
        if bad_zero.any():
            raise ValueError("filing null/missingness was converted to zero")
        if early.any():
            raise ValueError("filing feature is visible before its effective session")
    s0 = _validate(base, CONTROL_FEATURES)
    s1 = _validate(_join(s0, fundamentals, FUNDAMENTAL_FEATURES), CONTROL_FEATURES + FUNDAMENTAL_FEATURES)
    s2_features = CONTROL_FEATURES + FUNDAMENTAL_FEATURES + FILING_FEATURES
    surfaces = (("S0", s0, CONTROL_FEATURES), ("S1", s1, CONTROL_FEATURES + FUNDAMENTAL_FEATURES),
                ("S2", _validate(_join(s1, filing, FILING_FEATURES), s2_features), s2_features))
    output_root.mkdir(parents=True)
    result: dict[str, dict[str, object]] = {}
    for surface_id, frame, features in surfaces:
        directory = output_root / surface_id.lower()
        directory.mkdir()
        parquet = directory / "surface.parquet"
        frame.to_parquet(parquet, index=False)
        manifest: dict[str, object] = {
            "schema_version": "P5EvaluationSurfaceV1", "surface_id": surface_id,
            "column_count": len(features), "ordered_features": list(features),
            "ordered_feature_manifest_sha256": _digest(list(features)),
            "control_feature_manifest_sha256": CONTROL_FEATURE_MANIFEST_SHA256,
            "control_dataset_identity": CONTROL_DATASET_IDENTITY,
            "parquet_path": parquet.name, "parquet_sha256": _digest(parquet),
            "row_count": len(frame), "index_unique": True, "schema_validation": "PASS",
            "null_count": int(frame[list(features)].isna().sum().sum()),
        }
        manifest["artifact_identity"] = "sha256:" + _digest(manifest)
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result[surface_id] = manifest
    return result
def evaluate_surface(surface_root: Path, output_root: Path, *, provider_uri: str | None = None,
                     benchmark: str | None = None) -> dict[str, object]:
    """Execute the pinned Qlib/LightGBM/Recorder path for one sealed surface."""
    import lightgbm
    import mlflow
    import qlib
    from qlib.contrib.model.gbdt import LGBModel
    from qlib.data.dataset import DatasetH
    from qlib.data.dataset.handler import DataHandlerLP
    from qlib.data.dataset.loader import StaticDataLoader
    from qlib.workflow import R
    from qlib.workflow.record_temp import PortAnaRecord, SigAnaRecord, SignalRecord
    from qlib.workflow.recorder import Recorder
    if output_root.exists():
        raise FileExistsError(output_root)
    output_root.mkdir(parents=True)
    manifest = json.loads((surface_root / "manifest.json").read_text(encoding="utf-8"))
    parquet = surface_root / str(manifest["parquet_path"])
    if _digest(parquet) != manifest["parquet_sha256"]:
        raise ValueError("surface artifact hash mismatch")
    frame, features = pd.read_parquet(parquet), list(manifest["ordered_features"])
    indexed = frame.set_index(["datetime", "episode_id"]).sort_index()
    indexed.index.names = ["datetime", "instrument"]
    loader = StaticDataLoader(config=pd.concat({"feature": indexed[features], "label": indexed[["label"]]}, axis=1))
    handler = DataHandlerLP(data_loader=loader, shared_processors=[], infer_processors=[], learn_processors=[
        {"class": "DropnaLabel", "kwargs": {"fields_group": "label"}},
        {"class": "CSZScoreNorm", "kwargs": {"fields_group": "label"}},
    ], process_type=DataHandlerLP.PTYPE_A)
    dataset = DatasetH(handler=handler, segments={"train": ("2015-04-01", "2019-12-31"),
        "valid": ("2020-01-01", "2021-12-31"), "test": ("2022-01-03", "2024-12-31")})
    if any(dataset.prepare(segment, col_set=["feature", "label"], data_key=DataHandlerLP.DK_L).empty
           for segment in ("train", "valid", "test")):
        raise ValueError("a Qlib segment is empty")
    previous_cwd = Path.cwd()
    os.chdir(output_root)
    try:
        init: dict[str, object] = {"region": "us", "exp_manager": {"class": "MLflowExpManager",
            "module_path": "qlib.workflow.expm", "kwargs": {
                "uri": f"sqlite:///{(output_root / 'mlflow.db').as_posix()}", "default_exp_name": "Experiment"}}}
        if provider_uri:
            init["provider_uri"] = provider_uri
        qlib.init(**init)
        model, experiment = LGBModel(**LGB_KWARGS), "p5-synthetic-e2e"
        with R.start(experiment_name=experiment, recorder_name=str(manifest["surface_id"])):
            recorder, recorder_id = R.get_recorder(), R.get_recorder().id
            model.fit(dataset, verbose_eval=False)
            prediction = model.predict(dataset, segment="test").rename("score")
            label = dataset.prepare("test", col_set="label", data_key=DataHandlerLP.DK_L).iloc[:, 0].rename("label")
            evidence = pd.concat((prediction, label), axis=1).dropna().sort_index()
            if evidence.empty or not np.isfinite(evidence.to_numpy()).all():
                raise RuntimeError("Qlib prediction evidence is empty or non-finite")
            SignalRecord(model, dataset, recorder).generate()
            SigAnaRecord(recorder, ana_long_short=False, ann_scaler=252).generate()
            portana = "READY_NOT_EXECUTED_SYNTHETIC"
            if provider_uri:
                if not benchmark:
                    raise ValueError("real Qlib evaluation requires an exact benchmark")
                PortAnaRecord(recorder, config={"strategy": {"class": "TopkDropoutStrategy",
                    "module_path": "qlib.contrib.strategy.signal_strategy", "kwargs": {
                        "signal": "<PRED>", "topk": 50, "n_drop": 5}}, "backtest": {
                    "start_time": "2022-01-03", "end_time": "2024-12-31", "account": 100000000,
                    "benchmark": benchmark, "exchange_kwargs": {"limit_threshold": 0.095,
                        "deal_price": "close", "open_cost": 0.0005, "close_cost": 0.0015, "min_cost": 5}}}).generate()
                raw = recorder.load_object("portfolio_analysis/report_normal_1day.pkl")
                pd.DataFrame({"date": raw.index, "net_return": raw["return"] - raw["cost"]}).to_parquet(
                    output_root / "daily-net-return.parquet", index=False)
                portana = "PASS"
            evidence.reset_index().to_parquet(output_root / "predictions.parquet", index=False)
            R.log_params(surface_id=manifest["surface_id"], surface_artifact_identity=manifest["artifact_identity"],
                         synthetic_interface_only=provider_uri is None)
        recorded = R.get_recorder(recorder_id=recorder_id, experiment_name=experiment)
        if recorded.status != Recorder.STATUS_FI:
            raise RuntimeError("Qlib Recorder did not finish")
        report: dict[str, object] = {"schema_version": "P5QlibSurfaceRunV1",
            "surface_id": manifest["surface_id"], "surface_artifact_identity": manifest["artifact_identity"],
            "qlib_version": qlib.__version__, "qlib_source_sha": "2fb9380b342556ddb50a4b24e4fe8655d548b2b8",
            "lightgbm_version": lightgbm.__version__, "mlflow_version": mlflow.__version__,
            "experiment_id": str(R.get_exp(experiment_name=experiment).id), "recorder_id": recorder_id,
            "mlflow_run_id": recorder_id, "recorder_status": recorded.status,
            "prediction_path": "predictions.parquet", "prediction_sha256": _digest(output_root / "predictions.parquet"),
            "signal_record": "PASS", "sigana_record": "PASS", "portana_record_interface": portana}
        if provider_uri:
            report.update({"daily_net_return_path": "daily-net-return.parquet",
                           "daily_net_return_sha256": _digest(output_root / "daily-net-return.parquet")})
        report["run_identity"] = "sha256:" + _digest(report)
        (output_root / "run.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return report
    finally:
        os.chdir(previous_cwd)
__all__ = ["CONTROL_DATASET_IDENTITY", "CONTROL_FEATURE_MANIFEST_SHA256", "CONTROL_FEATURES",
           "FILING_FEATURES", "FUNDAMENTAL_FEATURES", "LGB_KWARGS", "compose_surfaces", "evaluate_surface"]
