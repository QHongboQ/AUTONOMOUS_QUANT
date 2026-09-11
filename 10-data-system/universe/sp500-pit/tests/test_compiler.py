from dataclasses import replace
import unittest

from aq_pit.compiler import compile_universe
from aq_pit.contracts import (
    AmbiguityState,
    CompilePolicyV1,
    CorrectionOperation,
    FindingSeverity,
    FindingType,
    IndexMembershipEventV1,
    InstrumentEpisodeV1,
    MembershipAction,
    MembershipCorrectionV1,
    ResolutionState,
    ReviewState,
    OverlayOperation,
    SessionBoundary,
    SnapshotObservationV1,
    SourceManifestV1,
    SourceRole,
    TickerIdentityEventV1,
    TickerEpisodeOverlayV1,
)
from aq_pit.validation import PublicationBlockedError, make_finding, validate_episodes, validate_publishable


H = "a" * 64


def source(source_id, role):
    return SourceManifestV1(
        source_id, role, "fixture", "https://example.invalid/source", "v1",
        "2026-09-10T00:00:00Z", "application/json", 1, H, "fixture",
        "2000-01-03", "2030-01-01", (), "adapter-v1",
    )


SOURCES = (
    source("seed", SourceRole.HISTORICAL_SEED),
    source("member", SourceRole.PRECISE_MEMBERSHIP_EVENTS),
    source("ticker", SourceRole.TICKER_IDENTITY_EVIDENCE),
    source("official", SourceRole.OFFICIAL_CONFLICT_RESOLUTION),
)


def policy(start="2020-01-02", end="2021-01-04"):
    return CompilePolicyV1("SP500", start, end, "fixture-calendar-v1", "policy-v1")


def seed(start="2020-01-02", tickers=("AAA",)):
    return SnapshotObservationV1("seed-row", "SP500", start, tickers, "seed", H)


def membership(event_id, action, ticker, session, boundary=SessionBoundary.EFFECTIVE_SESSION):
    return IndexMembershipEventV1(
        event_id, "SP500", action, ticker, None, session, session, boundary,
        "member", H,
    )


class CompilerTests(unittest.TestCase):
    def test_add_present_fails(self):
        result = compile_universe(
            policy=policy(), manifests=SOURCES, observations=(seed(),),
            membership_events=(membership("add", MembershipAction.ADD, "AAA", "2020-06-01"),),
        )
        self.assertIn(FindingType.ADD_PRESENT, {item.finding_type for item in result.findings})
        with self.assertRaises(PublicationBlockedError):
            validate_publishable(result.episodes, result.findings)

    def test_remove_absent_fails(self):
        result = compile_universe(
            policy=policy(), manifests=SOURCES, observations=(seed(tickers=()),),
            membership_events=(membership("remove", MembershipAction.REMOVE, "AAA", "2020-06-01"),),
        )
        self.assertIn(FindingType.REMOVE_ABSENT, {item.finding_type for item in result.findings})

    def test_membership_reentry_new_episode(self):
        events = (
            membership("remove", MembershipAction.REMOVE, "AAA", "2020-03-02"),
            membership("add", MembershipAction.ADD, "AAA", "2020-07-01"),
        )
        result = compile_universe(policy=policy(), manifests=SOURCES, observations=(seed(),), membership_events=events)
        matches = [item for item in result.episodes if item.normalized_ticker == "AAA"]
        self.assertEqual(len(matches), 2)
        self.assertNotEqual(matches[0].episode_id, matches[1].episode_id)
        validate_publishable(result.episodes, result.findings)

    def test_ambiguous_boundary_blocks(self):
        event = membership("ambiguous", MembershipAction.ADD, "BBB", "2020-06-01", SessionBoundary.AMBIGUOUS)
        result = compile_universe(policy=policy(), manifests=SOURCES, observations=(seed(),), membership_events=(event,))
        self.assertIn(FindingType.AMBIGUOUS_SOURCE_BOUNDARY, {item.finding_type for item in result.findings})
        self.assertNotIn("BBB", {item.normalized_ticker for item in result.episodes})

    def test_ambiguous_identity_state_blocks(self):
        event = TickerIdentityEventV1(
            "rename", "AAA", "BBB", None, "2020-06-01", "2020-06-01",
            SessionBoundary.EFFECTIVE_SESSION, "ticker", H,
            ambiguity_state=AmbiguityState.AMBIGUOUS,
        )
        result = compile_universe(policy=policy(), manifests=SOURCES, observations=(seed(),), ticker_events=(event,))
        self.assertIn(FindingType.AMBIGUOUS_SOURCE_BOUNDARY, {item.finding_type for item in result.findings})

    def test_unresolved_correction_blocks(self):
        correction = MembershipCorrectionV1(
            "fix-1", ("seed-row",), CorrectionOperation.ADD, "SP500", "BBB",
            "2020-06-01", "needs evidence", "official", H,
            ReviewState.UNRESOLVED, "R99",
        )
        result = compile_universe(policy=policy(), manifests=SOURCES, observations=(seed(),), corrections=(correction,))
        self.assertIn(FindingType.UNRESOLVED_CORRECTION, {item.finding_type for item in result.findings})
        with self.assertRaises(PublicationBlockedError):
            validate_publishable(result.episodes, result.findings)

    def test_accepted_correction_affects_state(self):
        correction = MembershipCorrectionV1(
            "fix-1", ("missing-event",), CorrectionOperation.ADD, "SP500", "BBB",
            "2020-06-01", "official omission correction", "official", H,
            ReviewState.ACCEPTED, "R99",
        )
        result = compile_universe(policy=policy(), manifests=SOURCES, observations=(seed(),), corrections=(correction,))
        self.assertIn("BBB", {item.normalized_ticker for item in result.episodes})
        validate_publishable(result.episodes, result.findings)

    def test_accepted_ignore_event_resolves_state_conflict(self):
        duplicate_add = membership("bad-add", MembershipAction.ADD, "AAA", "2020-06-01")
        correction = MembershipCorrectionV1(
            "fix-ignore", (duplicate_add.event_id,), CorrectionOperation.IGNORE_EVENT,
            "SP500", "AAA", "2020-06-01", "event was a documented duplicate",
            "official", H, ReviewState.ACCEPTED, "ADD_PRESENT",
        )
        result = compile_universe(
            policy=policy(), manifests=SOURCES, observations=(seed(),),
            membership_events=(duplicate_add,), corrections=(correction,),
        )
        self.assertNotIn(FindingType.ADD_PRESENT, {item.finding_type for item in result.findings})
        self.assertEqual(result.membership_corrections, (correction,))
        validate_publishable(result.episodes, result.findings)

    def test_rejected_correction_remains_visible_but_cannot_mutate_state(self):
        correction = MembershipCorrectionV1(
            "fix-rejected", ("missing-event",), CorrectionOperation.ADD,
            "SP500", "BBB", "2020-06-01", "rejected evidence",
            "official", H, ReviewState.REJECTED, "R99",
        )
        result = compile_universe(
            policy=policy(), manifests=SOURCES, observations=(seed(),), corrections=(correction,),
        )
        self.assertEqual(result.membership_corrections, (correction,))
        self.assertNotIn("BBB", {item.normalized_ticker for item in result.episodes})

    def test_raw_input_not_mutated(self):
        raw = seed(tickers=("BBB", "AAA"))
        before = raw.tickers
        compile_universe(policy=policy(), manifests=SOURCES, observations=(raw,))
        self.assertEqual(raw.tickers, before)

    def test_same_input_compile_twice_identical(self):
        kwargs = dict(policy=policy(), manifests=SOURCES, observations=(seed(),))
        first = compile_universe(**kwargs)
        second = compile_universe(**kwargs)
        self.assertEqual(first.output_hash, second.output_hash)
        self.assertEqual(first, second)

    def test_duplicate_event_blocks(self):
        event = membership("same", MembershipAction.ADD, "BBB", "2020-06-01")
        result = compile_universe(
            policy=policy(), manifests=SOURCES, observations=(seed(),),
            membership_events=(event, replace(event, source_ticker="CCC")),
        )
        self.assertIn(FindingType.DUPLICATE_EVENT, {item.finding_type for item in result.findings})

    def test_duplicate_canonical_event_with_distinct_ids_blocks(self):
        first = membership("first", MembershipAction.ADD, "BBB", "2020-06-01")
        second = replace(first, event_id="second")
        result = compile_universe(
            policy=policy(), manifests=SOURCES, observations=(seed(),),
            membership_events=(first, second),
        )
        self.assertIn(FindingType.DUPLICATE_EVENT, {item.finding_type for item in result.findings})

    def test_overlay_mutation_changes_downstream_hash_and_provenance(self):
        event = TickerIdentityEventV1(
            "rename", "AAA", "BBB", None, "2020-06-01", "2020-06-01",
            SessionBoundary.EFFECTIVE_SESSION, "ticker", H,
        )
        raw = seed(tickers=("BBB",))
        base = TickerEpisodeOverlayV1(
            "overlay", raw.observation_id, event.event_id, event.effective_session,
            OverlayOperation.MAP_SUCCESSOR_TO_PREDECESSOR, "reason one", (H,), ReviewState.ACCEPTED,
        )
        kwargs = dict(policy=policy(), manifests=SOURCES, observations=(raw,), ticker_events=(event,))
        first = compile_universe(**kwargs, overlays=(base,))
        second = compile_universe(**kwargs, overlays=(replace(base, reason="reason two"),))
        self.assertNotEqual(first.output_hash, second.output_hash)
        self.assertNotEqual(first.episodes[0].provenance_hash, second.episodes[0].provenance_hash)

    def test_missing_source_manifest_blocks(self):
        event = replace(membership("add", MembershipAction.ADD, "BBB", "2020-06-01"), source_id="missing")
        result = compile_universe(policy=policy(), manifests=SOURCES, observations=(seed(),), membership_events=(event,))
        self.assertIn(FindingType.MISSING_EVIDENCE, {item.finding_type for item in result.findings})

    def test_diagnostic_source_cannot_authorize_membership(self):
        diagnostic = source("diagnostic", SourceRole.DIAGNOSTIC_REFERENCE)
        event = replace(
            membership("add", MembershipAction.ADD, "BBB", "2020-06-01"),
            source_id=diagnostic.source_id,
        )
        result = compile_universe(
            policy=policy(), manifests=(*SOURCES, diagnostic), observations=(seed(),),
            membership_events=(event,),
        )
        self.assertNotIn("BBB", {item.normalized_ticker for item in result.episodes})
        self.assertIn(FindingType.MISSING_EVIDENCE, {item.finding_type for item in result.findings})

    def test_overlapping_ticker_episodes_blocked(self):
        one = InstrumentEpisodeV1.create(
            index_id="SP500", source_ticker="XYZ", valid_from="2020-01-01", valid_to="2020-06-01",
            membership_from="2020-01-01", membership_to="2020-06-01",
            membership_source_ids=("a",), ticker_source_ids=("a",), source_event_ids=("one",),
            provenance_inputs=("one",),
        )
        two = InstrumentEpisodeV1.create(
            index_id="SP500", source_ticker="XYZ", valid_from="2020-05-01", valid_to="2020-12-01",
            membership_from="2020-05-01", membership_to="2020-12-01",
            membership_source_ids=("b",), ticker_source_ids=("b",), source_event_ids=("two",),
            provenance_inputs=("two",),
        )
        findings = validate_episodes((one, two))
        self.assertEqual(findings[0].finding_type, FindingType.OVERLAPPING_TICKER_EPISODES)
        with self.assertRaises(PublicationBlockedError):
            validate_publishable((one, two), ())

    def test_unresolved_episode_blocks(self):
        episode = InstrumentEpisodeV1.create(
            index_id="SP500", source_ticker="XYZ", valid_from="2020-01-01", valid_to="2020-02-01",
            membership_from="2020-01-01", membership_to="2020-02-01",
            membership_source_ids=("a",), ticker_source_ids=("a",), source_event_ids=("one",),
            provenance_inputs=("one",), resolution_state=ResolutionState.MANUAL_REVIEW_REQUIRED,
        )
        with self.assertRaises(PublicationBlockedError):
            validate_publishable((episode,), ())

    def test_resolved_error_does_not_block(self):
        result = compile_universe(policy=policy(), manifests=SOURCES, observations=(seed(),))
        resolved = make_finding(
            FindingType.TERMINAL_SET_MISMATCH, FindingSeverity.ERROR, ("reference",),
            "reviewed", resolution_state=ResolutionState.RESOLVED,
        )
        validate_publishable(result.episodes, (resolved,))


if __name__ == "__main__":
    unittest.main()
