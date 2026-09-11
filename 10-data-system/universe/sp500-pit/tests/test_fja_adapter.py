import unittest

from aq_pit.canonical import sha256_hex
from aq_pit.compiler import compile_universe
from aq_pit.contracts import CompilePolicyV1, FindingType, MembershipAction, TickerIdentityEventV1, SessionBoundary
from aq_pit.overlays import detect_future_ticker_backfill
from aq_pit.sources.fja_sp500 import (
    build_fja_manifest,
    build_membership_event_manifest,
    derive_membership_events,
    parse_fja_snapshots,
)


FJA = (
    b'date,tickers\n'
    b'2024-01-02,"AAA,CPRI"\n'
    b'2024-01-03,"AAA,BBB,CPRI"\n'
    b'2024-01-04,"BBB,CPRI"\n'
)


def normalized(raw=FJA):
    manifest = build_fja_manifest(
        raw,
        commit="a2430f2af0c79ddf0748e91de11bdeb1616ab5a7",
        source_file="S&P 500 Historical Components & Changes (Updated).csv",
        retrieved_at="2026-09-10T00:00:00Z",
    )
    observations = parse_fja_snapshots(
        raw, manifest, start_date="2024-01-01", end_date="2024-12-31",
    )
    event_manifest = build_membership_event_manifest(manifest, observations)
    events = derive_membership_events(observations, event_manifest)
    return manifest, observations, event_manifest, events


class FjaAdapterTests(unittest.TestCase):
    def test_as_of_seed_is_carried_to_explicit_first_session(self):
        raw = b'date,tickers\n2009-12-30,"AAA,BBB"\n2010-01-06,"AAA,CCC"\n'
        manifest = build_fja_manifest(
            raw, commit="fixture", source_file="fixture.csv",
            retrieved_at="2026-09-10T00:00:00Z",
        )
        rows = parse_fja_snapshots(
            raw, manifest, start_date="2010-01-01", end_date="2010-12-31",
            start_session="2010-01-04",
        )
        self.assertEqual(rows[0].effective_session, "2010-01-04")
        self.assertEqual(rows[0].tickers, ("AAA", "BBB"))
        self.assertEqual(rows[1].effective_session, "2010-01-06")

    def test_parse_is_deterministic_and_does_not_mutate_source(self):
        before = bytes(FJA)
        first = normalized()
        second = normalized()
        self.assertEqual(first, second)
        self.assertEqual(FJA, before)

    def test_same_bytes_have_same_normalized_hash(self):
        self.assertEqual(sha256_hex(normalized()[1]), sha256_hex(normalized(bytes(FJA))[1]))

    def test_modified_source_bytes_change_source_and_normalized_hashes(self):
        changed = FJA.replace(b"AAA,BBB,CPRI", b"AAA,CCC,CPRI")
        original = normalized()
        modified = normalized(changed)
        self.assertNotEqual(original[0].sha256, modified[0].sha256)
        self.assertNotEqual(sha256_hex(original[1]), sha256_hex(modified[1]))

    def test_snapshot_diff_is_remove_then_add_and_deterministic(self):
        _, _, _, events = normalized()
        self.assertEqual(events, normalized()[3])
        self.assertEqual(
            [(item.effective_session, item.action, item.source_ticker) for item in events],
            [
                ("2024-01-03", MembershipAction.ADD, "BBB"),
                ("2024-01-04", MembershipAction.REMOVE, "AAA"),
            ],
        )

    def test_future_ticker_is_exposed_without_repair(self):
        _, observations, _, _ = normalized()
        identity = TickerIdentityEventV1(
            "audit-kors-cpri", "KORS", "CPRI", None,
            "2024-01-04", "2024-01-04", SessionBoundary.EFFECTIVE_SESSION,
            "diagnostic-only", "a" * 64,
        )
        findings = detect_future_ticker_backfill(observations, (identity,))
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(item.finding_type is FindingType.FUTURE_TICKER_BEFORE_RENAME for item in findings))
        self.assertTrue(all("CPRI" in item.tickers for item in observations))

    def test_compilation_repeats_with_identical_hash(self):
        manifest, observations, event_manifest, events = normalized()
        policy = CompilePolicyV1(
            "SP500", observations[0].effective_session, "2024-01-05",
            "FJA-source-session-calendar-v1", "p1-real-ingestion-v1",
        )
        arguments = {
            "policy": policy,
            "manifests": (manifest, event_manifest),
            "observations": observations,
            "membership_events": events,
        }
        first = compile_universe(**arguments)
        second = compile_universe(**arguments)
        self.assertEqual(first, second)
        self.assertEqual(first.output_hash, second.output_hash)

    def test_manifest_rejects_mismatched_raw_bytes(self):
        manifest = normalized()[0]
        with self.assertRaisesRegex(ValueError, "pinned manifest"):
            parse_fja_snapshots(
                FJA + b"\n", manifest,
                start_date="2024-01-01", end_date="2024-12-31",
            )


if __name__ == "__main__":
    unittest.main()
