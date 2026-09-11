from dataclasses import FrozenInstanceError, replace
import unittest

from aq_pit.canonical import CanonicalizationError, canonical_bytes, deterministic_id, sha256_hex
from aq_pit.contracts import (
    CorporateActionEventV1,
    IndexMembershipEventV1,
    MembershipAction,
    SourceManifestV1,
    SourceRole,
    SessionBoundary,
    TickerIdentityEventV1,
)
from aq_pit.validation import sources_are_independent


H1 = "1" * 64
H2 = "2" * 64


def manifest(source_id="seed", sha=H1, ancestry=(), role=SourceRole.HISTORICAL_SEED):
    return SourceManifestV1(
        source_id=source_id,
        source_role=role,
        source_type="fixture",
        source_url_or_repo="https://example.invalid/pinned",
        source_commit_or_revision="fixture-v1",
        retrieved_at="2026-09-10T00:00:00Z",
        media_type="application/json",
        byte_length=12,
        sha256=sha,
        license_observation="fixture only",
        coverage_start="2000-01-03",
        coverage_end="2026-01-01",
        ancestry=ancestry,
        adapter_version="fixture-adapter-v1",
    )


class CanonicalContractTests(unittest.TestCase):
    def test_canonical_hash_deterministic(self):
        left = {"b": (2, 3), "a": "é"}
        right = {"a": "é", "b": [2, 3]}
        self.assertEqual(canonical_bytes(left), canonical_bytes(right))
        self.assertEqual(sha256_hex(left), sha256_hex(right))

    def test_unsupported_custom_object_rejected(self):
        with self.assertRaises(CanonicalizationError):
            canonical_bytes(object())

    def test_float_rejected(self):
        with self.assertRaises(CanonicalizationError):
            canonical_bytes({"metric": 1.25})

    def test_absolute_path_not_in_identity(self):
        logical = {"source": "fixture", "revision": "v1"}
        first = deterministic_id("ID-", logical)
        second = deterministic_id("ID-", logical)
        self.assertEqual(first, second)
        with self.assertRaises(CanonicalizationError):
            deterministic_id("ID-", {**logical, "physical": r"D:\\one\\raw.json"})
        with self.assertRaises(CanonicalizationError):
            deterministic_id("ID-", {**logical, "physical": "/tmp/raw.json"})
        with self.assertRaises(CanonicalizationError):
            deterministic_id("ID-", {**logical, "physical": "file:///tmp/raw.json"})

    def test_source_mutation_changes_hash(self):
        original = manifest()
        mutated = replace(original, sha256=H2)
        self.assertNotEqual(original.manifest_hash, mutated.manifest_hash)

    def test_contracts_are_immutable(self):
        value = manifest()
        with self.assertRaises(FrozenInstanceError):
            value.byte_length = 99

    def test_shared_ancestry_not_independent_vote(self):
        first = manifest("derived-a", ancestry=("upstream-root",))
        second = manifest("derived-b", ancestry=("upstream-root",))
        independent = manifest("independent", ancestry=("other-root",))
        self.assertFalse(sources_are_independent(first, second))
        self.assertTrue(sources_are_independent(first, independent))

    def test_membership_event_not_rename_event(self):
        event = IndexMembershipEventV1(
            "m1", "SP500", MembershipAction.ADD, "ABC", None,
            "2020-01-02", "2020-01-02", SessionBoundary.EFFECTIVE_SESSION,
            "member", H1,
        )
        self.assertNotIsInstance(event, TickerIdentityEventV1)

    def test_corporate_action_not_membership_event(self):
        event = CorporateActionEventV1(
            "c1", "MERGER", "ABC", "XYZ", "2020-01-02", "2020-01-02",
            "corp", H1, "context only",
        )
        self.assertNotIsInstance(event, IndexMembershipEventV1)

    def test_invalid_sha_rejected(self):
        with self.assertRaises(ValueError):
            manifest(sha="not-a-hash")

    def test_source_manifest_sorts_ancestry(self):
        value = manifest(ancestry=("z", "a"))
        self.assertEqual(value.ancestry, ("a", "z"))


if __name__ == "__main__":
    unittest.main()
