from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import unittest

import duckdb
import pandas as pd
from aq_xnys_calendar import sessions_in_range


SQL = Path(__file__).parents[1] / "macro_v1.sql"
FEATURES = ["macro_v1_cpiaucsl_d2_log", "macro_v1_unrate_d1"]


def row(series: str, observed: str, known: str, value: float, revision: str) -> dict:
    identity = hashlib.sha256(json.dumps([series, observed, known, value, revision]).encode()).hexdigest()
    return {
        "entity": f"fred:{series}", "field": f"fred:{series}", "series_id": series,
        "observed_at": pd.Timestamp(observed), "known_at": pd.Timestamp(known),
        "value": float(value), "source": "control", "source_url": "private://control",
        "vintage": revision, "evidence_id": identity,
    }


def execute(rows: list[dict], start: str = "2018-02-01", end: str = "2018-07-10"):
    con = duckdb.connect(":memory:")
    con.register("evidence_input", pd.DataFrame(rows))
    con.register("all_sessions", pd.DataFrame({
        "session": pd.to_datetime(sessions_in_range("2018-01-02", "2018-07-10"))
    }))
    con.register("target_sessions", pd.DataFrame({
        "session": pd.to_datetime(sessions_in_range(start, end))
    }))
    con.execute(SQL.read_text(encoding="utf-8"))
    return (
        con.execute("SELECT * FROM mapped_evidence ORDER BY evidence_id").fetchdf(),
        con.execute("SELECT * FROM state_rows ORDER BY session, series_id").fetchdf(),
        con.execute("SELECT * FROM macro_state ORDER BY session").fetchdf(),
        con.execute("SELECT * FROM provenance").fetchdf(),
    )


class MacroV1Tests(unittest.TestCase):
    def test_frozen_features_and_revision_policy(self):
        rows = [
            row("CPIAUCSL", "2018-01-01", "2018-02-01", 100, "r1"),
            row("CPIAUCSL", "2018-02-01", "2018-03-01", 101, "r1"),
            row("CPIAUCSL", "2018-03-01", "2018-04-01", 103, "r1"),
            row("CPIAUCSL", "2018-02-01", "2018-04-05", 102, "r2"),
            row("UNRATE", "2018-01-01", "2018-02-01", 4.2, "r1"),
            row("UNRATE", "2018-02-01", "2018-03-01", 4.0, "r1"),
        ]
        _, states, wide, provenance = execute(rows)
        self.assertEqual(list(wide.columns), ["session", *FEATURES])
        self.assertNotIn("GDP", " ".join(wide.columns))
        before = states[(states.series_id == "CPIAUCSL") & (states.session == "2018-04-05")].iloc[0]
        after = states[(states.series_id == "CPIAUCSL") & (states.session == "2018-04-06")].iloc[0]
        expected_before = math.log(103) - 2 * math.log(101) + math.log(100)
        expected_after = math.log(103) - 2 * math.log(102) + math.log(100)
        self.assertAlmostEqual(before.transformed_value, expected_before, places=15)
        self.assertAlmostEqual(after.transformed_value, expected_after, places=15)
        unrate = states[states.series_id == "UNRATE"].iloc[-1]
        self.assertAlmostEqual(unrate.transformed_value, -0.2, places=15)
        self.assertTrue((states.state_effective_session <= states.session).all())
        self.assertEqual(
            len(provenance[provenance.feature_id == FEATURES[0]]) % 3, 0
        )
        self.assertEqual(
            len(provenance[provenance.feature_id == FEATURES[1]]) % 2, 0
        )

    def test_missing_and_nonpositive_dependencies_fail_closed(self):
        missing = [
            row("CPIAUCSL", "2018-01-01", "2018-02-01", 100, "r1"),
            row("CPIAUCSL", "2018-03-01", "2018-04-01", 103, "r1"),
            row("UNRATE", "2018-01-01", "2018-02-01", 4.2, "r1"),
            row("UNRATE", "2018-03-01", "2018-04-01", 4.0, "r1"),
        ]
        _, states, _, _ = execute(missing)
        self.assertTrue(states.empty)
        invalid = [
            row("CPIAUCSL", "2018-01-01", "2018-02-01", 100, "r1"),
            row("CPIAUCSL", "2018-02-01", "2018-03-01", 0, "r1"),
            row("CPIAUCSL", "2018-03-01", "2018-04-01", 103, "r1"),
        ]
        _, states, _, _ = execute(invalid)
        self.assertTrue(states.empty)

    def test_strictly_after_known_at_weekend_and_holiday(self):
        rows = [
            row("UNRATE", "2018-01-01", "2018-04-01", 4.2, "weekend"),
            row("UNRATE", "2018-02-01", "2018-07-04", 4.0, "holiday"),
        ]
        mapped, _, _, _ = execute(rows)
        mapped = mapped.set_index("vintage")
        self.assertEqual(mapped.loc["weekend", "effective_session"], pd.Timestamp("2018-04-02"))
        self.assertEqual(mapped.loc["holiday", "effective_session"], pd.Timestamp("2018-07-05"))

    def test_state_carries_without_source_imputation(self):
        rows = [
            row("UNRATE", "2018-01-01", "2018-02-01", 4.2, "r1"),
            row("UNRATE", "2018-02-01", "2018-03-01", 4.0, "r1"),
        ]
        evidence, states, _, _ = execute(rows, "2018-03-02", "2018-03-09")
        self.assertEqual(len(evidence), 2)
        self.assertEqual(states.observed_at.nunique(), 1)
        self.assertGreater(len(states), 1)
        self.assertEqual(states.transformed_value.nunique(), 1)


if __name__ == "__main__":
    unittest.main()
