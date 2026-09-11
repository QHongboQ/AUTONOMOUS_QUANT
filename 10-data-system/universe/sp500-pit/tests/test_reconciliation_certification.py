from dataclasses import replace
import hashlib
from pathlib import Path
import tempfile
import unittest

from aq_pit.certification import (
    CANONICAL_LEDGER_SHA256,
    build_retained_input_manifest,
    evaluate_certification,
    historical_sample_authority_complete,
    is_official_terminal_authority,
    is_retained_primary_evidence,
    verify_content_hash,
)
from aq_pit.contracts import SourceRole
from aq_pit.contracts import InstrumentEpisodeV1
from aq_pit.overlays import ResolvedObservation
from aq_pit.reconciliation import build_evidence_manifests
from scripts.run_pit_certification_closeout import artifact_tree_snapshot, promote_artifact_tree


class CertificationAuthorityTests(unittest.TestCase):
    def test_modified_canonical_ledger_content_fails_closed(self):
        original = b'[{"finding_id":"P1UNRES-fixed","finding_type":"FUTURE_TICKER_BACKFILL"}]'
        tampered = b'[{"finding_id":"P1UNRES-fixed","finding_type":"FALSE_DIAGNOSTIC_BOUNDARY"}]'
        with self.assertRaisesRegex(ValueError, "canonical ledger content hash mismatch"):
            verify_content_hash(
                tampered, hashlib.sha256(original).hexdigest(), "canonical ledger",
            )

    def test_modified_terminal_reference_content_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "terminal reference content hash mismatch"):
            verify_content_hash(b"modified", "0" * 64, "terminal reference")

    def test_locator_metadata_hash_is_not_primary_content(self):
        locator = build_evidence_manifests()[0]
        self.assertFalse(is_retained_primary_evidence(locator, {locator.sha256: b"locator"}))

    def test_missing_primary_evidence_content_blocks(self):
        locator = build_evidence_manifests()[0]
        self.assertFalse(is_retained_primary_evidence(locator, {}))

    def test_diagnostic_terminal_cannot_be_official(self):
        raw = b"AAPL\n"
        diagnostic = build_retained_input_manifest(
            raw=raw, expected_sha256=hashlib.sha256(raw).hexdigest(), label="terminal",
            source_type="pinned_wikipedia_terminal_roster", source_url_or_repo="https://example.invalid",
            source_commit_or_revision="1", retrieved_at="now", media_type="text/plain",
            coverage_start="2024-12-23", coverage_end="2024-12-23",
        )
        self.assertFalse(is_official_terminal_authority(diagnostic, {diagnostic.sha256: raw}))

    def test_missing_required_historical_samples_block(self):
        self.assertFalse(historical_sample_authority_complete((), {}))

    def test_artifact_run_a_equals_run_b_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "a"
            second = root / "b"
            first.mkdir()
            second.mkdir()
            (first / "artifact.json").write_bytes(b"deterministic\n")
            (second / "artifact.json").write_bytes(b"deterministic\n")
            self.assertEqual(artifact_tree_snapshot(first), artifact_tree_snapshot(second))

    def test_stale_final_file_cannot_contaminate_promoted_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            staging = root / "staging"
            final = root / "final"
            staging.mkdir()
            final.mkdir()
            (staging / "current.json").write_bytes(b"current")
            (final / "stale.json").write_bytes(b"stale")
            promote_artifact_tree(staging, final)
            self.assertEqual([item.name for item in final.iterdir()], ["current.json"])
            self.assertTrue((root / ".final.previous" / "stale.json").exists())

    def test_compiled_terminal_episode_mismatch_blocks(self):
        locator = build_evidence_manifests()[0]
        ledger = replace(locator, sha256=CANONICAL_LEDGER_SHA256)
        episode = InstrumentEpisodeV1.create(
            index_id="SP500", source_ticker="AAA", valid_from="2020-01-02",
            valid_to="2025-01-01", membership_from="2020-01-02",
            membership_to="2025-01-01", membership_source_ids=("source",),
            ticker_source_ids=("source",), source_event_ids=("event",),
            provenance_inputs={"source": "fixture"},
        )
        observation = ResolvedObservation(
            "observation", "SP500", "2024-12-23", ("BBB",),
            "source", "0" * 64, (),
        )
        decision = evaluate_certification(
            primary_evidence_manifests=(locator,), retained_primary_bytes_by_hash={},
            canonical_ledger_manifest=ledger, official_terminal_manifest=None,
            official_terminal_bytes_by_hash={}, historical_sample_manifests=(),
            historical_sample_bytes_by_hash={}, episodes=(episode,),
            resolved_observations=(observation,), artifact_hashes_twice_identical=True,
        )
        self.assertEqual(decision.compiled_terminal_set_gate, "FAIL")
        self.assertIn("COMPILED_TERMINAL_SET_MISMATCH", decision.blockers)
