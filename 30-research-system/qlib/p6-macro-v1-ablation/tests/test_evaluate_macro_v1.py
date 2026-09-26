from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import pandas as pd


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("macro_eval", ROOT / "evaluate_macro_v1.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
PROTOCOL = json.loads((ROOT / "macro-v1-ablation-protocol.json").read_text(encoding="utf-8"))


class MacroEvaluatorTests(unittest.TestCase):
    def test_surface_inventory(self):
        control = [f"f{i}" for i in range(157)]
        evaluation = control + PROTOCOL["macro_input_authority"]["feature_ids"] + ["__label__"]
        MODULE.validate_surface_inventory(PROTOCOL, control, evaluation)
        with self.assertRaises(RuntimeError):
            MODULE.validate_surface_inventory(PROTOCOL, control, evaluation + ["GDP"])

    def test_row_and_label_identity_hash(self):
        index = pd.MultiIndex.from_tuples(
            [(pd.Timestamp("2022-01-03"), "A"), (pd.Timestamp("2022-01-04"), "A")],
            names=["datetime", "instrument"],
        )
        left = pd.DataFrame({"__label__": [0.1, None]}, index=index)
        right = left.copy()
        self.assertEqual(MODULE.frame_hash(left), MODULE.frame_hash(right))
        right.iloc[0, 0] = 0.2
        self.assertNotEqual(MODULE.frame_hash(left), MODULE.frame_hash(right))

    def test_duckdb_macro_broadcast_is_mechanical(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            index = pd.MultiIndex.from_tuples(
                [(pd.Timestamp("2022-01-03"), "A"), (pd.Timestamp("2022-01-03"), "B")],
                names=["datetime", "instrument"],
            )
            pd.DataFrame({"f0": [1.0, 2.0], "__label__": [0.1, 0.2]}, index=index).to_parquet(root / "control.parquet")
            state = pd.DataFrame({
                "macro_v1_cpiaucsl_d2_log": [3.0], "macro_v1_unrate_d1": [4.0],
            }, index=pd.Index([pd.Timestamp("2022-01-03")], name="session"))
            state.to_parquet(root / "state.parquet")
            report = MODULE.broadcast_parquet(root / "control.parquet", root / "state.parquet", root / "result.parquet")
            result = pd.read_parquet(root / "result.parquet")
            self.assertEqual(report["row_count"], 2)
            self.assertEqual(report["manufactured_instrument_session_row_count"], 0)
            self.assertEqual(report["instrument_dependent_macro_value_count"], 0)
            self.assertEqual(result["macro_v1_cpiaucsl_d2_log"].tolist(), [3.0, 3.0])
            self.assertEqual(result.index.names, ["datetime", "instrument"])

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
