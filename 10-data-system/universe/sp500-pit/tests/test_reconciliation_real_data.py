import hashlib
import json
import os
from pathlib import Path
import unittest

from aq_pit.reconciliation import all_gates_pass, build_reconciliation, parse_terminal_roster
from aq_pit.sources.fja_sp500 import build_fja_manifest, parse_fja_snapshots
from aq_pit.validation import AmbiguousTickerEpisodeError, lookup_episode


FJA_COMMIT = "a2430f2af0c79ddf0748e91de11bdeb1616ab5a7"
FJA_FILE = "S&P 500 Historical Components & Changes (Updated).csv"
FJA_SHA256 = "646b2e47284abfb675abebacd4a4035ba22a79ea1ccdeccce7fbe5f0e27bab3a"


@unittest.skipUnless(os.environ.get("AQ_PIT_DATA_ROOT"), "AQ_PIT_DATA_ROOT not configured")
class RealDataReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ["AQ_PIT_DATA_ROOT"])
        raw = (cls.root / "raw" / "fja_sp500" / "repo" / FJA_FILE).read_bytes()
        if hashlib.sha256(raw).hexdigest() != FJA_SHA256:
            raise AssertionError("unexpected immutable FJA input")
        seed = build_fja_manifest(
            raw, commit=FJA_COMMIT, source_file=FJA_FILE,
            retrieved_at="2026-09-11T01:08:50Z",
        )
        observations = parse_fja_snapshots(
            raw, seed, start_date="2010-01-01", end_date="2024-12-31",
            start_session="2010-01-04",
        )
        ledger = tuple(json.loads(
            (cls.root / "audit" / "unresolved_findings" / "unresolved_findings.json").read_text(encoding="utf-8")
        ))
        terminal = parse_terminal_roster(
            (cls.root / "raw" / "terminal_reference" / "wikipedia-sp500-oldid-1265285344.wikitext").read_bytes()
        )
        cls.bundle = build_reconciliation(
            seed_manifest=seed, observations=observations,
            historical_ledger=ledger, terminal_roster=terminal,
        )

    def test_real_data_counts_and_all_gates(self):
        self.assertEqual(len(self.bundle.identity_events), 20)
        self.assertEqual(len(self.bundle.overlays), 3236)
        self.assertEqual(len(self.bundle.membership_events), 630)
        self.assertEqual(len(self.bundle.compilation.episodes), 832)
        self.assertTrue(all_gates_pass(self.bundle.gate_results))

    def test_exact_overlay_case_row_counts(self):
        counts = {}
        for overlay in self.bundle.overlays:
            case = overlay.reason.rsplit(" ", 1)[-1]
            counts[case] = counts.get(case, 0) + 1
        self.assertEqual(counts, {
            "O1": 385, "O2": 564, "O3": 358, "O4": 26, "O5": 3,
            "O6": 2, "O7": 340, "O8": 622, "O9": 936,
        })

    def test_reuse_and_reentry_remain_separate_episodes(self):
        episodes = self.bundle.compilation.episodes
        for ticker in ("GAS", "Q", "IR", "CEG", "DELL", "DD", "DOW"):
            with self.assertRaises(AmbiguousTickerEpisodeError, msg=ticker):
                lookup_episode(episodes, ticker)
        dlph = [item for item in episodes if item.normalized_ticker == "DLPH"]
        aptv = [item for item in episodes if item.normalized_ticker == "APTV"]
        self.assertEqual(len(dlph), 1)
        self.assertEqual(dlph[0].valid_to, "2017-12-05")
        self.assertTrue(any(item.valid_from == "2017-12-05" for item in aptv))
        for ticker in ("AMD", "TER", "JBL", "FSLR", "EQT", "PCG"):
            matches = [item for item in episodes if item.normalized_ticker == ticker]
            self.assertGreaterEqual(len(matches), 2, ticker)
            for left, right in zip(matches, matches[1:]):
                self.assertLessEqual(left.valid_to, right.valid_from, ticker)

    def test_all_historical_finding_ids_close_without_deletion(self):
        self.assertEqual(len(self.bundle.resolved_ledger), 37)
        self.assertEqual(len({item["finding_id"] for item in self.bundle.resolved_ledger}), 37)
        self.assertTrue(all(item["resolution_state"] == "RESOLVED" for item in self.bundle.resolved_ledger))
        self.assertTrue(all(item["blocking_after_implementation"] == "NO" for item in self.bundle.resolved_ledger))


if __name__ == "__main__":
    unittest.main()
