"""Thin fixed-surface Parquet handoff to Qlib's public dataset path."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from qlib.data.dataset import DatasetH
from qlib.data.dataset.handler import DataHandlerLP
from qlib.data.dataset.loader import StaticDataLoader

P5_V1_FEATURES = (
    "Revenue", "NetIncome", "Assets", "Liabilities", "CommonEquity",
    "NetCashFromOperatingActivities", "CashAndCashEquivalents",
    "CurrentAssetsTotal", "CurrentLiabilitiesTotal", "LongTermDebt",
)
P5_V1_PERIODS = {
    "Revenue": "DURATION_ANNUAL",
    "NetIncome": "DURATION_ANNUAL",
    "Assets": "INSTANT",
    "Liabilities": "INSTANT",
    "CommonEquity": "INSTANT",
    "NetCashFromOperatingActivities": "DURATION_ANNUAL",
    "CashAndCashEquivalents": "INSTANT",
    "CurrentAssetsTotal": "INSTANT",
    "CurrentLiabilitiesTotal": "INSTANT",
    "LongTermDebt": "INSTANT",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_dataset(
    *, projection_root: Path, selection_path: Path, output: Path,
) -> dict[str, object]:
    """Select ten frozen native period streams; never synthesize missing facts."""

    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    concepts = selection["ordered_features"]
    period_map = selection["period_class_by_feature"]
    if tuple(concepts) != P5_V1_FEATURES or period_map != P5_V1_PERIODS:
        raise ValueError("P5 V1 ten-feature/period authority mismatch")
    if selection.get("period_class_fallback") != "NONE" or selection.get("flow_derivation_count") != 0:
        raise ValueError("P5 V1 period fallback or flow derivation is prohibited")
    manifest = json.loads((projection_root / "manifest.json").read_text(encoding="utf-8"))
    grid = pd.read_parquet(projection_root / "episode_sessions.parquet")
    if len(grid) != manifest["session_rows"]:
        raise ValueError("P1 session grid count changed")
    selected: list[pd.DataFrame] = []
    for source in sorted((projection_root / "streams").glob("CIK*.parquet")):
        frame = pd.read_parquet(source, columns=[
            "session", "instrument", "standard_concept", "period_class", "canonical_value",
        ])
        frame = frame[
            frame["standard_concept"].isin(concepts)
            & frame["standard_concept"].map(period_map).eq(frame["period_class"])
        ].copy()
        if not frame.empty:
            if frame.duplicated(["session", "instrument", "standard_concept"]).any():
                raise ValueError("duplicate selected session feature")
            frame["canonical_value"] = pd.to_numeric(frame["canonical_value"], errors="raise")
            selected.append(frame.pivot(
                index=["session", "instrument"], columns="standard_concept", values="canonical_value",
            ))
    if not selected:
        raise ValueError("no admitted selected PIT observations")
    wide = pd.concat(selected)
    if wide.index.has_duplicates:
        raise ValueError("duplicate Qlib instrument/session identity across CIKs")
    wide.index = wide.index.set_names(["datetime", "instrument"])
    index = pd.MultiIndex.from_frame(
        grid[["session", "instrument"]].rename(columns={"session": "datetime"}),
        names=["datetime", "instrument"],
    )
    if index.has_duplicates:
        raise ValueError("duplicate Qlib instrument/session identity")
    wide = wide.reindex(index).reindex(columns=concepts).astype("float64")
    wide.columns.name = None
    if np.isinf(wide.to_numpy(copy=False)).any():
        raise ValueError("non-finite selected Qlib feature")
    excluded = grid["identity_excluded"].to_numpy()
    if wide.iloc[excluded].notna().any().any():
        raise ValueError("identity-excluded episode received a fundamental")
    output.mkdir(parents=True, exist_ok=True)
    feature_path = output / "fundamentals.parquet"
    wide.to_parquet(feature_path, compression="zstd")
    handler = DataHandlerLP(
        instruments=None,
        start_time=str(index.get_level_values("datetime").min().date()),
        end_time=str(index.get_level_values("datetime").max().date()),
        data_loader=StaticDataLoader({"feature": wide}),
        infer_processors=[], learn_processors=[],
    )
    dataset = DatasetH(handler=handler, segments={
        "historical": (str(index.get_level_values("datetime").min().date()),
                       str(index.get_level_values("datetime").max().date())),
    })
    prepared = dataset.prepare("historical", col_set="feature", data_key=DataHandlerLP.DK_I)
    if len(prepared) != len(grid) or list(prepared.columns) != concepts:
        raise ValueError("Qlib DatasetH changed the frozen handoff surface")
    result = {
        "schema": "AQ_P5_MINIMAL_QLIB_HANDOFF_V1",
        "projection_manifest_sha256": _sha256(projection_root / "manifest.json"),
        "selection_sha256": _sha256(selection_path),
        "feature_parquet_sha256": _sha256(feature_path),
        "session_rows": len(prepared),
        "feature_count": len(concepts),
        "features": concepts,
        "period_class_by_feature": period_map,
        "period_class_fallback": "NONE",
        "flow_derivation_count": 0,
        "identity_exclusion_session_rows": int(excluded.sum()),
        "non_missing_feature_cells": int(prepared.notna().sum().sum()),
        "qlib_static_data_loader": "PASS",
        "qlib_data_handler_lp": "PASS",
        "qlib_dataset_h": "PASS",
        "model_training_count": 0,
        "prediction_count": 0,
        "backtest_count": 0,
    }
    (output / "manifest.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result
