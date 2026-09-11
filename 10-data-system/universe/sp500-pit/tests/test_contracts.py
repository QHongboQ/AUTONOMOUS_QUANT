from dataclasses import FrozenInstanceError
import unittest

from aq_pit.canonical import CanonicalizationError, canonical_bytes, deterministic_id, sha256_hex
from aq_pit.domain import IndexMembershipEventV1, SnapshotObservationV1, TickerIdentityEventV1


H = "1" * 64


class ActiveContractTests(unittest.TestCase):
    def test_canonical_hash_is_deterministic(self):
        left = {"b": (2, 3), "a": "é"}
        right = {"a": "é", "b": [2, 3]}
        self.assertEqual(canonical_bytes(left), canonical_bytes(right))
        self.assertEqual(sha256_hex(left), sha256_hex(right))

    def test_unsupported_custom_object_is_rejected(self):
        with self.assertRaises(CanonicalizationError):
            canonical_bytes(object())

    def test_float_is_rejected(self):
        with self.assertRaises(CanonicalizationError):
            canonical_bytes({"metric": 1.25})

    def test_absolute_path_is_not_allowed_in_identity(self):
        logical = {"source": "fixture", "revision": "v1"}
        self.assertEqual(
            deterministic_id("ID-", logical),
            deterministic_id("ID-", logical),
        )
        for physical in (r"D:\one\raw.json", "/tmp/raw.json", "file:///tmp/raw.json"):
            with self.subTest(physical=physical):
                with self.assertRaises(CanonicalizationError):
                    deterministic_id("ID-", {**logical, "physical": physical})

    def test_active_contracts_are_immutable(self):
        value = SnapshotObservationV1(
            "snapshot-1", "SP500", "2020-01-02", ("ABC",), "fixture", H
        )
        with self.assertRaises(FrozenInstanceError):
            value.source_id = "changed"

    def test_membership_event_is_not_identity_event(self):
        event = IndexMembershipEventV1(
            "membership-1", "SP500", "ADD", "ABC", None,
            "2020-01-02", "2020-01-02", "EFFECTIVE_SESSION",
            "fixture", H, None,
        )
        self.assertNotIsInstance(event, TickerIdentityEventV1)


if __name__ == "__main__":
    unittest.main()
