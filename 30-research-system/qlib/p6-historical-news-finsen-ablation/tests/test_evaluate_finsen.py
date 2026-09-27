from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("finsen_eval", ROOT / "evaluate_finsen.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PROTOCOL = json.loads((ROOT / "finsen-ablation-protocol.json").read_text(encoding="utf-8"))


class FinSenEvaluatorTests(unittest.TestCase):
    def test_surface_inventory(self):
        control = [f"f{i}" for i in range(157)]
        evaluation = control + ["finsen_finbert_market_sentiment", "__label__"]
        MODULE.validate_surface_inventory(PROTOCOL, control, evaluation)
        with self.assertRaises(RuntimeError):
            MODULE.validate_surface_inventory(PROTOCOL, control, evaluation + ["Revenue"])

    def test_duckdb_broadcast_preserves_null_and_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            index = pd.MultiIndex.from_tuples([
                (pd.Timestamp("2022-01-03"), "A"), (pd.Timestamp("2022-01-03"), "B"),
                (pd.Timestamp("2022-01-04"), "A"), (pd.Timestamp("2022-01-04"), "B"),
            ], names=["datetime", "instrument"])
            pd.DataFrame({"f0": range(4), "__label__": [0.1, 0.2, 0.3, 0.4]}, index=index).to_parquet(root / "control.parquet")
            pd.DataFrame({
                "session": pd.to_datetime(["2022-01-03", "2022-01-04"]),
                "source_date": pd.to_datetime(["2022-01-02", None]),
                "finsen_finbert_market_sentiment": [0.25, None],
            }).to_parquet(root / "factor.parquet")
            report = MODULE.broadcast_parquet(
                root / "control.parquet", root / "factor.parquet", root / "result.parquet",
                "finsen_finbert_market_sentiment",
            )
            result = pd.read_parquet(root / "result.parquet")
            self.assertEqual(report["row_count"], 4)
            self.assertEqual(report["supported_interval_null_session_count"], 1)
            self.assertEqual(report["instrument_dependent_finsen_value_count"], 0)
            self.assertEqual(report["manufactured_instrument_session_row_count"], 0)
            self.assertEqual(result["finsen_finbert_market_sentiment"].isna().sum(), 2)

    def test_classification_direction_mapping(self):
        gates = {"directions": {
            "M1_MINUS_M0": {"walkforward": {"gate": True}, "cpcv": {"gate": True}},
            "M0_MINUS_M1": {"walkforward": {"gate": True}, "cpcv": {"gate": True}},
        }}
        significance = {"directions": {
            "M1_MINUS_M0": {"spa_consistent_pvalue": 0.01, "reality_check_consistent_pvalue": 0.01},
            "M0_MINUS_M1": {"spa_consistent_pvalue": 0.01, "reality_check_consistent_pvalue": 0.01},
        }}
        self.assertEqual(MODULE.classify(0.01, 0.02, gates, significance), "INCREMENTAL_VALUE_SUPPORTED")
        self.assertEqual(MODULE.classify(0.02, 0.01, gates, significance), "DEGRADED")
        significance["directions"]["M1_MINUS_M0"]["spa_consistent_pvalue"] = 0.2
        self.assertEqual(MODULE.classify(0.01, 0.02, gates, significance), "NO_MEASURABLE_INCREMENTAL_VALUE")
        self.assertEqual(MODULE.classify(float("nan"), 0.02, gates, significance), "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
