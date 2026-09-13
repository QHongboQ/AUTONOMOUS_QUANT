from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd


LEAF = Path(__file__).parents[1]
import sys
sys.path.insert(0, str(LEAF))

from aq_qlib_handoff import build_ragged_staging, qlib_instrument_id


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RaggedPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.dates = ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"]
        (self.source / "source_manifest.json").write_text('{"fixture":true}\n', encoding="utf-8")
        (self.source / "coordinates.json").write_text(json.dumps({
            "field": ["open", "high", "low", "close", "vol"],
            "time": self.dates,
        }), encoding="utf-8")
        (self.source / "provider_assets.json").write_text(json.dumps([
            {"id": "NYS:A", "symbol": "A"},
        ]), encoding="utf-8")
        values = np.full((5, 4, 1), np.nan, dtype=float)
        values[:, 0, 0] = [10, 11, 9, 10.5, 100]
        values[:, 2, 0] = [12, 13, 11, 12.5, 120]
        np.save(self.source / "values.npy", values)
        self.simfin = self.root / "simfin.csv"
        self.simfin.write_text(
            "Ticker;SimFinId;Date;Open;High;Low;Close;Volume\n",
            encoding="utf-8",
        )
        identity_a = "P2AUDITSEC-" + "a" * 64
        identity_b = "P2AUDITSEC-" + "b" * 64
        base = {
            "observed_secondary_rows": 0,
            "known_terminal_gap_rows": 0,
            "partial_coverage_missing_rows": 0,
            "identity_ambiguous_rows": 0,
            "terminal_policy_unresolved_rows": 0,
            "unresolved_error_rows": 0,
            "original_49_episode": False,
        }
        episodes = [
            {**base, "episode_id": "ep-a1", "security_identity": identity_a,
             "ticker": "A", "scope_required_from": self.dates[0], "scope_required_to": self.dates[1],
             "required_sessions": 2, "provider_asset_identifier": "NYS:A", "binding_basis": "TEST",
             "observed_primary_rows": 1, "known_provider_gap_rows": 1, "no_provider_asset_rows": 0},
            {**base, "episode_id": "ep-a2", "security_identity": identity_a,
             "ticker": "AA", "scope_required_from": self.dates[2], "scope_required_to": self.dates[2],
             "required_sessions": 1, "provider_asset_identifier": "NYS:A", "binding_basis": "TEST",
             "observed_primary_rows": 1, "known_provider_gap_rows": 0, "no_provider_asset_rows": 0},
            {**base, "episode_id": "ep-b", "security_identity": identity_b,
             "ticker": "B", "scope_required_from": self.dates[3], "scope_required_to": self.dates[3],
             "required_sessions": 1, "provider_asset_identifier": None, "binding_basis": "TEST",
             "observed_primary_rows": 0, "known_provider_gap_rows": 0, "no_provider_asset_rows": 1},
        ]
        self.inventory = self.root / "inventory.json"
        self.inventory.write_text(json.dumps({
            "frozen_scope_start": self.dates[0],
            "frozen_scope_end": self.dates[-1],
            "unique_security_identities": 2,
            "instrument_episodes": 3,
            "total_member_session_rows": 4,
            "episodes": episodes,
        }, sort_keys=True), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def build(self):
        return build_ragged_staging(
            self.inventory, self.source, self.simfin, self.root / "output",
            expected_inventory_sha256=sha256(self.inventory),
            expected_quantiacs_manifest_sha256=sha256(self.source / "source_manifest.json"),
            expected_simfin_sha256=sha256(self.simfin),
            expected_identities=2, expected_episodes=3, expected_member_rows=4,
            expected_primary_rows=2, expected_secondary_rows=0,
        )

    def test_security_identity_is_the_only_instrument_key(self) -> None:
        result = self.build()
        self.assertEqual(result.unique_security_identities, 2)
        lines = (self.root / "output/staging/instruments/p2_pit.txt").read_text().splitlines()
        instrument = qlib_instrument_id("P2AUDITSEC-" + "a" * 64)
        self.assertEqual(sum(line.startswith(instrument + "\t") for line in lines), 2)
        self.assertNotIn("\tA\t", "\n".join(lines))

    def test_missing_observation_is_nan_and_reason_is_preserved(self) -> None:
        self.build()
        instrument = qlib_instrument_id("P2AUDITSEC-" + "a" * 64)
        frame = pd.read_csv(self.root / f"output/staging/csv/{instrument.lower()}.csv")
        missing = frame.loc[frame["date"] == "2020-01-03"]
        self.assertTrue(missing[["open", "high", "low", "close", "volume"]].isna().all(axis=None))
        with gzip.open(self.root / "output/staging/availability.jsonl.gz", "rt", encoding="utf-8") as stream:
            reasons = [json.loads(line)["reason"] for line in stream]
        self.assertEqual(reasons.count("KNOWN_PROVIDER_GAP"), 1)
        self.assertEqual(reasons.count("NO_PROVIDER_ASSET"), 1)

    def test_no_episode_overlap_is_silently_collapsed(self) -> None:
        payload = json.loads(self.inventory.read_text())
        payload["episodes"][1]["scope_required_from"] = "2020-01-03"
        payload["episodes"][1]["scope_required_to"] = "2020-01-03"
        self.inventory.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "overlapping episodes"):
            self.build()

    def test_secondary_source_uses_same_security_identity_chain(self) -> None:
        self.simfin.write_text(
            "Ticker;SimFinId;Date;Open;High;Low;Close;Volume\n"
            "AA;99;2020-01-03;20;21;19;20.5;200\n",
            encoding="utf-8",
        )
        payload = json.loads(self.inventory.read_text())
        payload["episodes"][0]["observed_secondary_rows"] = 1
        payload["episodes"][0]["known_provider_gap_rows"] = 0
        self.inventory.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        result = build_ragged_staging(
            self.inventory, self.source, self.simfin, self.root / "output",
            expected_inventory_sha256=sha256(self.inventory),
            expected_quantiacs_manifest_sha256=sha256(self.source / "source_manifest.json"),
            expected_simfin_sha256=sha256(self.simfin),
            expected_identities=2, expected_episodes=3, expected_member_rows=4,
            expected_primary_rows=2, expected_secondary_rows=1,
        )
        self.assertEqual(result.simfin_selected_rows, 1)
        with gzip.open(self.root / "output/staging/availability.jsonl.gz", "rt", encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream]
        selected = [row for row in rows if row["date"] == "2020-01-03"]
        self.assertEqual(selected[0]["reason"], "OBSERVED_SECONDARY")

    def test_cross_security_ticker_reuse_cannot_select_secondary(self) -> None:
        self.simfin.write_text(
            "Ticker;SimFinId;Date;Open;High;Low;Close;Volume\n"
            "A;99;2020-01-03;20;21;19;20.5;200\n",
            encoding="utf-8",
        )
        payload = json.loads(self.inventory.read_text())
        payload["episodes"][2]["ticker"] = "A"
        self.inventory.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        result = self.build()
        self.assertEqual(result.simfin_selected_rows, 0)

    def test_runtime_has_no_case_specific_identity_literals(self) -> None:
        source = (LEAF / "aq_qlib_handoff" / "ragged_panel.py").read_text(encoding="utf-8")
        forbidden = ('"DISCK"', '"FB"', '"META"', '"WBD"', "2022-04-08", "NAS:", "NYS:")
        self.assertTrue(all(value not in source for value in forbidden))

    def test_output_path_is_fail_closed(self) -> None:
        (self.root / "output").mkdir()
        with self.assertRaises(FileExistsError):
            self.build()


if __name__ == "__main__":
    unittest.main()
