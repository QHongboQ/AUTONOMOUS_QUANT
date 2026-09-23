"""The selected PIT surface reaches Qlib without model execution."""

from __future__ import annotations

import importlib.util
import json

import pandas as pd

if importlib.util.find_spec("qlib") is None:
    import pytest

    pytest.skip("Qlib is validated in the pinned rdagent4qlib runtime", allow_module_level=True)

from aq_p5_qlib_handoff import validate_dataset


FEATURES = [
    "Revenue", "NetIncome", "Assets", "Liabilities", "CommonEquity",
    "NetCashFromOperatingActivities", "CashAndCashEquivalents",
    "CurrentAssetsTotal", "CurrentLiabilitiesTotal", "LongTermDebt",
]


def test_native_qlib_handoff_keeps_excluded_rows_missing(tmp_path) -> None:
    projection = tmp_path / "projection"
    streams = projection / "streams"
    streams.mkdir(parents=True)
    grid = pd.DataFrame({
        "session": pd.to_datetime(["2020-01-02", "2020-01-03"]),
        "instrument": ["P1", "P2"],
        "identity_excluded": [False, True],
    })
    grid.to_parquet(projection / "episode_sessions.parquet", index=False)
    (projection / "manifest.json").write_text(json.dumps({"session_rows": 2}), encoding="utf-8")
    pd.DataFrame([{
        "session": pd.Timestamp("2020-01-02"), "instrument": "P1",
        "standard_concept": "Assets", "period_class": "INSTANT", "canonical_value": "123",
    }]).to_parquet(streams / "CIK0000000001.parquet", index=False)
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({
        "ordered_features": FEATURES,
        "period_class_by_feature": {
            feature: "DURATION_ANNUAL"
            if feature in {"Revenue", "NetIncome", "NetCashFromOperatingActivities"}
            else "INSTANT"
            for feature in FEATURES
        },
        "period_class_fallback": "NONE",
        "flow_derivation_count": 0,
    }), encoding="utf-8")
    report = validate_dataset(projection_root=projection, selection_path=selection, output=tmp_path / "qlib")
    assert report["qlib_dataset_h"] == "PASS"
    assert report["session_rows"] == 2
    assert report["feature_count"] == 10
    wide = pd.read_parquet(tmp_path / "qlib" / "fundamentals.parquet")
    assert wide.loc[(pd.Timestamp("2020-01-02"), "P1"), "Assets"] == 123
    assert wide.loc[(pd.Timestamp("2020-01-03"), "P2")].isna().all()
