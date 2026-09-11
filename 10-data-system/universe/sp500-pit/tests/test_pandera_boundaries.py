"""Focused tests for generic PIT table-boundary validation."""

from pathlib import Path
import unittest

from aq_pit.schema.pandera import (
    validate_identity_event_table,
    validate_instrument_episode_table,
    validate_membership_event_table,
    validate_snapshot_observation_table,
)


H = "a" * 64


def snapshot(**updates):
    row = {
        "observation_id": "obs-1",
        "index_id": "TEST_INDEX",
        "effective_session": "2024-01-02",
        "tickers": ("AAA", "BBB"),
        "source_id": "source-1",
        "evidence_hash": H,
        "schema_version": "SnapshotObservationV1",
    }
    row.update(updates)
    return row


def membership(**updates):
    row = {
        "event_id": "event-1",
        "index_id": "TEST_INDEX",
        "action": "ADD",
        "source_ticker": "AAA",
        "announcement_date": None,
        "effective_date": "2024-01-02",
        "effective_session": "2024-01-02",
        "boundary_semantics": "EFFECTIVE_SESSION",
        "source_id": "source-1",
        "evidence_hash": H,
        "reason": None,
        "schema_version": "IndexMembershipEventV1",
    }
    row.update(updates)
    return row


def identity(**updates):
    row = {
        "event_id": "identity-1",
        "old_ticker": "AAA",
        "new_ticker": "BBB",
        "announcement_date": None,
        "effective_date": "2024-01-02",
        "effective_session": "2024-01-02",
        "boundary_semantics": "EFFECTIVE_SESSION",
        "source_id": "source-1",
        "evidence_hash": H,
        "identity_anchor": None,
        "ambiguity_state": "CLEAR",
        "schema_version": "TickerIdentityEventV1",
    }
    row.update(updates)
    return row


def episode(**updates):
    row = {
        "episode_id": "episode-1",
        "index_id": "TEST_INDEX",
        "source_ticker": "AAA",
        "normalized_ticker": "AAA",
        "valid_from": "2024-01-02",
        "valid_to": "2024-04-01",
        "membership_from": "2024-01-02",
        "membership_to": "2024-04-01",
        "membership_source_ids": ("source-1",),
        "ticker_source_ids": ("source-1",),
        "source_event_ids": ("event-1",),
        "provenance_hash": H,
        "resolution_state": "RESOLVED",
        "schema_version": "InstrumentEpisodeV1",
    }
    row.update(updates)
    return row


class PanderaBoundaryTests(unittest.TestCase):
    def test_valid_snapshot_passes(self):
        self.assertIsNone(validate_snapshot_observation_table((snapshot(),)))

    def test_valid_membership_event_passes(self):
        self.assertIsNone(validate_membership_event_table((membership(),)))

    def test_valid_identity_event_passes(self):
        self.assertIsNone(validate_identity_event_table((identity(),)))

    def test_valid_episode_passes(self):
        self.assertIsNone(validate_instrument_episode_table((episode(),)))

    def test_missing_required_column_fails(self):
        row = snapshot()
        del row["source_id"]
        with self.assertRaises(ValueError):
            validate_snapshot_observation_table((row,))

    def test_wrong_column_type_fails(self):
        with self.assertRaises(ValueError):
            validate_snapshot_observation_table((snapshot(index_id=7),))

    def test_null_prohibited_field_fails(self):
        with self.assertRaises(ValueError):
            validate_membership_event_table((membership(event_id=None),))

    def test_invalid_ticker_format_fails(self):
        with self.assertRaises(ValueError):
            validate_membership_event_table((membership(source_ticker="bad ticker"),))

    def test_malformed_date_fails(self):
        with self.assertRaises(ValueError):
            validate_identity_event_table((identity(effective_date="2024-02-30"),))

    def test_duplicate_unique_id_fails(self):
        second = identity(new_ticker="CCC")
        with self.assertRaises(ValueError):
            validate_identity_event_table((identity(), second))

    def test_duplicate_logical_event_fails(self):
        second = membership(event_id="event-2")
        with self.assertRaises(ValueError):
            validate_membership_event_table((membership(), second))

    def test_reversed_structural_interval_fails(self):
        with self.assertRaises(ValueError):
            validate_instrument_episode_table(
                (episode(membership_from="2024-04-01", membership_to="2024-01-02"),)
            )

    def test_unsupported_structural_enum_fails(self):
        with self.assertRaises(ValueError):
            validate_membership_event_table((membership(action="RENAME"),))

    def test_schema_source_has_no_symbol_specific_conditions(self):
        source = (
            Path(__file__).parents[1]
            / "aq_pit"
            / "schema"
            / "pandera"
            / "boundaries.py"
        ).read_text(encoding="utf-8")
        for symbol in ("META", "APTV", "CPRI", "IQV", "DLPH", "GAS", "IR"):
            with self.subTest(symbol=symbol):
                self.assertNotIn(f'"{symbol}"', source)
                self.assertNotIn(f"'{symbol}'", source)


if __name__ == "__main__":
    unittest.main()
