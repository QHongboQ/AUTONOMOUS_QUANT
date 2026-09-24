from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

MODULE = Path(__file__).parents[1] / "evaluate_h1.py"
SPEC = importlib.util.spec_from_file_location("evaluate_h1", MODULE)
assert SPEC and SPEC.loader
h1 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h1)


class H1ThinAdapterTests(unittest.TestCase):
    def test_crosswalk_is_date_valid_and_fail_closed(self) -> None:
        projection = pd.DataFrame({
            "session": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
            "episode_id": ["new-a", "new-a", "new-b"],
            "historical_ticker": ["A", "A", "B"],
            "identity_excluded": [False, False, True],
        })
        rows = [
            {"episode_id": "old-a", "instrument": "P2A", "historical_ticker": "A",
             "start": "2020-01-02", "end_inclusive": "2020-01-03"},
            {"episode_id": "old-b", "instrument": "P2B", "historical_ticker": "B",
             "start": "2020-01-06", "end_inclusive": "2020-01-06"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "episode-map.jsonl"
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "incomplete or ambiguous"):
                h1.build_crosswalk(projection, path)

    def test_model_and_feature_authority_is_exact(self) -> None:
        self.assertEqual(len(h1.P5_FEATURES), 10)
        self.assertNotIn("ShortTermDebt", h1.P5_FEATURES)
        self.assertEqual(h1.MODEL_CONFIG["num_threads"], 8)
        self.assertTrue(h1.MODEL_CONFIG["deterministic"])
        self.assertFalse(h1.MODEL_CONFIG["zero_as_missing"])

    def test_frozen_processor_chain_is_label_only(self) -> None:
        self.assertEqual(
            h1.LEARN_PROCESSORS,
            (
                {"class": "DropnaLabel", "kwargs": {"fields_group": "label"}},
                {"class": "CSZScoreNorm", "kwargs": {"fields_group": "label"}},
            ),
        )
        self.assertFalse(any(
            processor.get("kwargs", {}).get("fields_group") == "feature"
            for processor in h1.LEARN_PROCESSORS
        ))

    def test_attempt_001_is_never_finally_classified(self) -> None:
        with self.assertRaisesRegex(ValueError, "attempt-001"):
            h1.classify_h1("ATTEMPT_001", 0.01, 0.02)

    def test_undefined_primary_metric_is_inconclusive(self) -> None:
        self.assertEqual(
            h1.classify_h1("ATTEMPT_002_AUTHORITY_CORRECTED", np.nan, 0.02),
            "INCONCLUSIVE",
        )

    def test_projected_s0_s1_row_identity_is_exact(self) -> None:
        index = pd.MultiIndex.from_tuples(
            [(pd.Timestamp("2020-01-02"), "P2A"), (pd.Timestamp("2020-01-03"), "P2A")],
            names=["datetime", "instrument"],
        )
        frame = pd.DataFrame({"x": [1.0, 2.0]}, index=index)
        crosswalk = pd.DataFrame({
            "p2_instrument": ["P2A"], "p2_start": [pd.Timestamp("2020-01-02")],
            "p2_end": [pd.Timestamp("2020-01-03")], "p5_episode_id": ["P1A"],
        })
        s0, _ = h1.project_index(frame, crosswalk)
        s1, _ = h1.project_index(frame.assign(fundamental=[3.0, 4.0]), crosswalk)
        self.assertTrue(s0.index.equals(s1.index))

    def test_h2_remains_unexecuted(self) -> None:
        self.assertFalse(h1.H2_EXECUTED)


if __name__ == "__main__":
    unittest.main()
