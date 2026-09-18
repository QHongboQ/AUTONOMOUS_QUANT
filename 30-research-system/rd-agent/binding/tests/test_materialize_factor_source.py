from __future__ import annotations

import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).parents[1]))

from aq_rdagent_us_binding.materialize_factor_source import FIELDS, attach_frozen_factors, debug_subset


class MaterializeFactorSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.index = pd.MultiIndex.from_tuples(
            [
                (pd.Timestamp("2018-01-02"), "P2SECA"),
                (pd.Timestamp("2018-01-02"), "P2SECB"),
                (pd.Timestamp("2018-01-03"), "P2SECA"),
            ],
            names=("datetime", "instrument"),
        )
        self.frame = pd.DataFrame(
            [[10, 11, 12, 9, 100], [20, 21, 22, 19, 200], [np.nan] * 5],
            index=self.index,
            columns=FIELDS,
        )
        self.episodes = {
            "EA": {
                "instrument": "P2SECA", "provider_asset_identifier": "ASSET_A",
                "observed_primary_rows": 1, "observed_secondary_rows": 0,
                "known_provider_gap_rows": 1, "known_terminal_gap_rows": 0,
                "partial_coverage_missing_rows": 0, "no_provider_asset_rows": 0,
                "identity_ambiguous_rows": 0, "terminal_policy_unresolved_rows": 0,
                "unresolved_error_rows": 0,
            },
            "EB": {
                "instrument": "P2SECB", "provider_asset_identifier": "ASSET_B",
                "observed_primary_rows": 0, "observed_secondary_rows": 1,
                "known_provider_gap_rows": 0, "known_terminal_gap_rows": 0,
                "partial_coverage_missing_rows": 0, "no_provider_asset_rows": 0,
                "identity_ambiguous_rows": 0, "terminal_policy_unresolved_rows": 0,
                "unresolved_error_rows": 0,
            },
        }
        rows = [
            {"date": "2018-01-02", "episode_id": "EA", "instrument": "P2SECA", "reason": "OBSERVED_PRIMARY"},
            {"date": "2018-01-02", "episode_id": "EB", "instrument": "P2SECB", "reason": "OBSERVED_SECONDARY"},
            {"date": "2018-01-03", "episode_id": "EA", "instrument": "P2SECA", "reason": "KNOWN_PROVIDER_GAP"},
        ]
        self.availability = self.root / "availability.jsonl.gz"
        with gzip.open(self.availability, "wt", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row) + "\n")
        self.source_values = np.array([[[0.5, 1.0], [1.0, 1.0]]])

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_exact_episode_asset_session_join_and_nan_policy(self) -> None:
        result, report = attach_frozen_factors(
            self.frame, self.availability, self.episodes,
            {"2018-01-02": 0, "2018-01-03": 1},
            {"ASSET_A": 0, "ASSET_B": 1}, self.source_values, 0,
        )
        self.assertEqual(result["$factor"].iloc[0], 0.5)
        self.assertTrue(np.isnan(result["$factor"].iloc[1]))
        self.assertTrue(np.isnan(result["$factor"].iloc[2]))
        self.assertEqual(report["quantiacs_backed_rows"], 1)
        self.assertEqual(report["simfin_only_rows"], 1)
        self.assertEqual(report["constant_one_fallback_rows"], 0)

    def test_invalid_primary_factor_fails_closed(self) -> None:
        bad = self.source_values.copy()
        bad[0, 0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "invalid authoritative"):
            attach_frozen_factors(
                self.frame, self.availability, self.episodes,
                {"2018-01-02": 0, "2018-01-03": 1},
                {"ASSET_A": 0, "ASSET_B": 1}, bad, 0,
            )

    def test_identity_order_mismatch_fails_closed(self) -> None:
        changed = self.frame.copy()
        changed.index = pd.MultiIndex.from_tuples(
            [
                (pd.Timestamp("2018-01-02"), "WRONG"),
                *list(changed.index[1:]),
            ],
            names=("datetime", "instrument"),
        )
        with self.assertRaisesRegex(ValueError, "identity ordering mismatch"):
            attach_frozen_factors(
                changed, self.availability, self.episodes,
                {"2018-01-02": 0, "2018-01-03": 1},
                {"ASSET_A": 0, "ASSET_B": 1}, self.source_values, 0,
            )

    def test_masked_row_with_values_fails_closed(self) -> None:
        changed = self.frame.copy()
        changed.iloc[2] = [30, 31, 32, 29, 300]
        with self.assertRaisesRegex(ValueError, "masked observation contains"):
            attach_frozen_factors(
                changed, self.availability, self.episodes,
                {"2018-01-02": 0, "2018-01-03": 1},
                {"ASSET_A": 0, "ASSET_B": 1}, self.source_values, 0,
            )

    def test_debug_selection_is_identity_ordered_and_bounded(self) -> None:
        with_factor = self.frame.copy()
        with_factor["$factor"] = [0.5, np.nan, np.nan]
        debug, rule = debug_subset(with_factor)
        self.assertEqual(list(debug.index), list(with_factor.index))
        self.assertIn("lexicographic identity order", rule["selection"])


if __name__ == "__main__":
    unittest.main()
