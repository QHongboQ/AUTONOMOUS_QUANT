from dataclasses import replace
import unittest

from reference_oracle.compiler import compile_universe
from reference_oracle.contracts import (
    CompilePolicyV1,
    FindingType,
    IndexMembershipEventV1,
    MembershipAction,
    OverlayOperation,
    ReviewState,
    SessionBoundary,
    SnapshotObservationV1,
    SourceManifestV1,
    SourceRole,
    TickerEpisodeOverlayV1,
    TickerIdentityEventV1,
)
from reference_oracle.overlays import (
    apply_ticker_overlays,
    detect_episode_scoped_ticker_findings,
)
from reference_oracle.sources.fja_sp500 import (
    build_reconciled_membership_event_manifest,
    derive_reconciled_membership_events,
)
from reference_oracle.validation import (
    AmbiguousTickerEpisodeError,
    PublicationBlockedError,
    lookup_episode,
    validate_publishable,
)


H = "a" * 64
H2 = "b" * 64


def source(source_id, role):
    return SourceManifestV1(
        source_id, role, "fixture", "https://example.invalid/pinned", "v1",
        "2026-09-10T00:00:00Z", "application/json", 1, H, "fixture",
        "2000-01-03", "2030-01-01", (), "fixture-v1",
    )


SEED_SOURCE = source("seed", SourceRole.HISTORICAL_SEED)
TICKER_SOURCE = source("ticker", SourceRole.TICKER_IDENTITY_EVIDENCE)


def observation(session, tickers, suffix=None):
    return SnapshotObservationV1(
        f"obs-{suffix or session}", "SP500", session, tuple(tickers), "seed", H,
    )


def identity(old, new, session, event_id=None):
    return TickerIdentityEventV1(
        event_id or f"identity-{old}-{new}-{session}", old, new, None,
        session, session, SessionBoundary.EFFECTIVE_SESSION, "ticker", H,
        identity_anchor=f"anchor-{old}-{new}",
    )


def overlay(raw, event, operation=OverlayOperation.MAP_SUCCESSOR_TO_PREDECESSOR, *, reason="accepted evidence"):
    return TickerEpisodeOverlayV1(
        f"overlay-{raw.observation_id}", raw.observation_id, event.event_id,
        event.effective_session, operation, reason,
        tuple(sorted({raw.evidence_hash, event.evidence_hash})), ReviewState.ACCEPTED,
    )


def reconcile(raw, identities=(), overlays=()):
    applied = apply_ticker_overlays(tuple(raw), tuple(identities), tuple(overlays))
    manifest = build_reconciled_membership_event_manifest(
        SEED_SOURCE, tuple(raw), applied.observations, tuple(identities), tuple(overlays),
    )
    events = derive_reconciled_membership_events(
        tuple(raw), applied.observations, tuple(identities), manifest,
        seed_manifest=SEED_SOURCE, overlays=tuple(overlays),
    )
    result = compile_universe(
        policy=CompilePolicyV1(
            "SP500", raw[0].effective_session, "2030-01-01",
            "fixture-calendar-v1", "reconciled-policy-v1",
        ),
        manifests=(SEED_SOURCE, TICKER_SOURCE, manifest),
        observations=tuple(raw), membership_events=events,
        ticker_events=tuple(identities), overlays=tuple(overlays),
    )
    return applied, manifest, events, result


def compile_reconciled(raw, manifest, events, identities=(), overlays=()):
    return compile_universe(
        policy=CompilePolicyV1(
            "SP500", raw[0].effective_session, "2030-01-01",
            "fixture-calendar-v1", "reconciled-policy-v1",
        ),
        manifests=(SEED_SOURCE, TICKER_SOURCE, manifest),
        observations=tuple(raw), membership_events=tuple(events),
        ticker_events=tuple(identities), overlays=tuple(overlays),
    )


def forged_reconciled_event(manifest, ticker="BBB", session="2020-06-01"):
    return IndexMembershipEventV1(
        f"forged-{ticker}-{session}", "SP500", MembershipAction.ADD, ticker,
        None, session, session, SessionBoundary.SOURCE_DEFINED,
        manifest.source_id, H2, "forged reconciled event",
    )


class ReconciliationRuntimeGapTests(unittest.TestCase):
    def assert_context_blocked(self, result):
        self.assertIn(FindingType.INVALID_AUTHORITY_REFERENCE, {
            item.finding_type for item in result.findings
        })
        with self.assertRaises(PublicationBlockedError):
            validate_publishable(result.episodes, result.findings)

    def test_forged_extra_reconciled_event_is_blocked(self):
        raw = (
            observation("2020-01-02", ("AAA",)),
            observation("2020-06-01", ("AAA",)),
        )
        _, manifest, expected, _ = reconcile(raw)
        self.assertEqual(expected, ())
        result = compile_reconciled(
            raw, manifest, (forged_reconciled_event(manifest),),
        )
        self.assert_context_blocked(result)
        self.assertNotIn("BBB", {item.normalized_ticker for item in result.episodes})

    def test_omitted_required_reconciled_event_is_blocked(self):
        raw = (
            observation("2020-01-02", ()),
            observation("2020-06-01", ("AAA",)),
        )
        _, manifest, expected, _ = reconcile(raw)
        self.assertEqual(len(expected), 1)
        result = compile_reconciled(raw, manifest, ())
        self.assert_context_blocked(result)
        self.assertFalse(result.episodes)

    def test_modified_reconciled_event_ticker_is_blocked(self):
        raw = (
            observation("2020-01-02", ()),
            observation("2020-06-01", ("AAA",)),
        )
        _, manifest, expected, _ = reconcile(raw)
        changed = replace(expected[0], source_ticker="BBB")
        result = compile_reconciled(raw, manifest, (changed,))
        self.assert_context_blocked(result)
        self.assertFalse(result.episodes)

    def test_modified_reconciled_event_session_is_blocked(self):
        raw = (
            observation("2020-01-02", ()),
            observation("2020-06-01", ("AAA",)),
        )
        _, manifest, expected, _ = reconcile(raw)
        changed = replace(
            expected[0],
            effective_date="2020-06-02",
            effective_session="2020-06-02",
        )
        result = compile_reconciled(raw, manifest, (changed,))
        self.assert_context_blocked(result)
        self.assertFalse(result.episodes)

    def test_extra_reconciled_event_is_blocked(self):
        raw = (
            observation("2020-01-02", ()),
            observation("2020-06-01", ("AAA",)),
        )
        _, manifest, expected, _ = reconcile(raw)
        actual = (*expected, forged_reconciled_event(manifest))
        result = compile_reconciled(raw, manifest, actual)
        self.assert_context_blocked(result)
        self.assertFalse(result.episodes)

    def test_exact_reconciled_event_stream_is_accepted(self):
        raw = (
            observation("2020-01-02", ()),
            observation("2020-06-01", ("AAA",)),
        )
        _, manifest, expected, _ = reconcile(raw)
        result = compile_reconciled(raw, manifest, expected)
        self.assertNotIn(FindingType.INVALID_AUTHORITY_REFERENCE, {
            item.finding_type for item in result.findings
        })
        self.assertEqual(
            {item.normalized_ticker for item in result.episodes},
            {"AAA"},
        )
        validate_publishable(result.episodes, result.findings)

    def test_zero_event_rename_exact_stream_is_accepted(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD",)),
            observation("2020-06-01", ("NEW",)),
        )
        _, manifest, expected, _ = reconcile(raw, (event,))
        self.assertEqual(expected, ())
        result = compile_reconciled(raw, manifest, (), (event,))
        self.assertNotIn(FindingType.INVALID_AUTHORITY_REFERENCE, {
            item.finding_type for item in result.findings
        })
        validate_publishable(result.episodes, result.findings)

    def test_zero_event_rename_with_injected_event_is_blocked(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD",)),
            observation("2020-06-01", ("NEW",)),
        )
        _, manifest, expected, _ = reconcile(raw, (event,))
        self.assertEqual(expected, ())
        result = compile_reconciled(
            raw, manifest, (forged_reconciled_event(manifest),), (event,),
        )
        self.assert_context_blocked(result)
        self.assertNotIn("BBB", {item.normalized_ticker for item in result.episodes})

    def test_tampered_resolved_ticker_set_is_blocked(self):
        raw = (
            observation("2020-01-02", ("AAA",)),
            observation("2020-02-03", ("AAA",)),
        )
        applied = apply_ticker_overlays(raw, (), ())
        forged = (
            applied.observations[0],
            replace(applied.observations[1], tickers=("AAA", "BBB")),
        )
        with self.assertRaisesRegex(ValueError, "deterministic output"):
            build_reconciled_membership_event_manifest(
                SEED_SOURCE, raw, forged, (), (),
            )

        manifest = build_reconciled_membership_event_manifest(
            SEED_SOURCE, raw, applied.observations, (), (),
        )
        with self.assertRaisesRegex(ValueError, "deterministic output"):
            derive_reconciled_membership_events(
                raw, forged, (), manifest,
                seed_manifest=SEED_SOURCE, overlays=(),
            )

    def test_omitted_identity_context_is_blocked(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD",)),
            observation("2020-06-01", ("NEW",)),
        )
        _, manifest, events, _ = reconcile(raw, (event,))
        self.assertEqual(events, ())
        result = compile_universe(
            policy=CompilePolicyV1(
                "SP500", raw[0].effective_session, "2030-01-01",
                "fixture-calendar-v1", "reconciled-policy-v1",
            ),
            manifests=(SEED_SOURCE, TICKER_SOURCE, manifest),
            observations=raw, membership_events=events, ticker_events=(),
        )
        self.assert_context_blocked(result)

    def test_changed_identity_context_is_blocked(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD",)),
            observation("2020-06-01", ("NEW",)),
        )
        _, manifest, events, _ = reconcile(raw, (event,))
        changed = replace(
            event,
            effective_date="2020-06-02",
            effective_session="2020-06-02",
        )
        result = compile_universe(
            policy=CompilePolicyV1(
                "SP500", raw[0].effective_session, "2030-01-01",
                "fixture-calendar-v1", "reconciled-policy-v1",
            ),
            manifests=(SEED_SOURCE, TICKER_SOURCE, manifest),
            observations=raw, membership_events=events, ticker_events=(changed,),
        )
        self.assert_context_blocked(result)

    def test_omitted_overlay_context_is_blocked(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ()),
            observation("2020-02-03", ("NEW",)),
            observation("2020-06-01", ("NEW",)),
        )
        accepted = overlay(raw[1], event)
        _, manifest, events, _ = reconcile(raw, (event,), (accepted,))
        result = compile_universe(
            policy=CompilePolicyV1(
                "SP500", raw[0].effective_session, "2030-01-01",
                "fixture-calendar-v1", "reconciled-policy-v1",
            ),
            manifests=(SEED_SOURCE, TICKER_SOURCE, manifest),
            observations=raw, membership_events=events, ticker_events=(event,),
            overlays=(),
        )
        self.assert_context_blocked(result)
        self.assertFalse(result.episodes)

    def test_changed_overlay_context_is_blocked(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ()),
            observation("2020-02-03", ("NEW",)),
            observation("2020-06-01", ("NEW",)),
        )
        accepted = overlay(raw[1], event)
        _, manifest, events, _ = reconcile(raw, (event,), (accepted,))
        changed = replace(accepted, reason="altered accepted evidence")
        result = compile_universe(
            policy=CompilePolicyV1(
                "SP500", raw[0].effective_session, "2030-01-01",
                "fixture-calendar-v1", "reconciled-policy-v1",
            ),
            manifests=(SEED_SOURCE, TICKER_SOURCE, manifest),
            observations=raw, membership_events=events, ticker_events=(event,),
            overlays=(changed,),
        )
        self.assert_context_blocked(result)
        self.assertFalse(result.episodes)

    def test_exact_reconciliation_context_is_accepted(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ()),
            observation("2020-02-03", ("NEW",)),
            observation("2020-06-01", ("NEW",)),
        )
        accepted = overlay(raw[1], event)
        _, _, _, result = reconcile(raw, (event,), (accepted,))
        self.assertNotIn(FindingType.INVALID_AUTHORITY_REFERENCE, {
            item.finding_type for item in result.findings
        })
        validate_publishable(result.episodes, result.findings)

    def test_zero_membership_event_rename_remains_context_bound(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD",)),
            observation("2020-06-01", ("NEW",)),
        )
        _, manifest, events, exact = reconcile(raw, (event,))
        self.assertEqual(events, ())
        validate_publishable(exact.episodes, exact.findings)

        missing = compile_universe(
            policy=CompilePolicyV1(
                "SP500", raw[0].effective_session, "2030-01-01",
                "fixture-calendar-v1", "reconciled-policy-v1",
            ),
            manifests=(SEED_SOURCE, TICKER_SOURCE, manifest),
            observations=raw, membership_events=(), ticker_events=(),
        )
        self.assert_context_blocked(missing)

    def test_incompatible_reconciled_manifest_version_is_blocked(self):
        raw = (
            observation("2020-01-02", ()),
            observation("2020-02-03", ("AAA",)),
        )
        _, manifest, events, _ = reconcile(raw)
        incompatible = replace(manifest, adapter_version="incompatible-v2")
        result = compile_universe(
            policy=CompilePolicyV1(
                "SP500", raw[0].effective_session, "2030-01-01",
                "fixture-calendar-v1", "reconciled-policy-v1",
            ),
            manifests=(SEED_SOURCE, TICKER_SOURCE, incompatible),
            observations=raw, membership_events=events,
        )
        self.assert_context_blocked(result)
        self.assertFalse(result.episodes)

    def test_duplicate_successor_before_boundary_drops_successor_only(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = observation("2020-01-02", ("OLD", "NEW"))
        accepted = overlay(raw, event, OverlayOperation.DROP_DUPLICATE_SUCCESSOR_BEFORE_BOUNDARY)
        applied = apply_ticker_overlays((raw,), (event,), (accepted,))
        self.assertEqual(applied.observations[0].tickers, ("OLD",))
        self.assertEqual(applied.observations[0].applied_overlay_ids, (accepted.overlay_id,))
        self.assertEqual(raw.tickers, ("NEW", "OLD"))

        invalid = replace(accepted, overlay_id="invalid", evidence_hashes=(H2,))
        rejected = apply_ticker_overlays((raw,), (event,), (invalid,))
        self.assertEqual(rejected.observations[0].tickers, ("NEW", "OLD"))
        self.assertEqual(rejected.findings[0].finding_type, FindingType.INVALID_AUTHORITY_REFERENCE)

        successor_only = observation("2020-02-03", ("NEW",), "successor-only")
        inapplicable = overlay(
            successor_only, event,
            OverlayOperation.DROP_DUPLICATE_SUCCESSOR_BEFORE_BOUNDARY,
        )
        rejected = apply_ticker_overlays((successor_only,), (event,), (inapplicable,))
        self.assertEqual(rejected.observations[0].tickers, ("NEW",))
        self.assertEqual(rejected.findings[0].finding_type, FindingType.INVALID_AUTHORITY_REFERENCE)

    def test_simple_boundary_rename_has_no_membership_churn(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD",)),
            observation("2020-06-01", ("NEW",)),
        )
        _, _, events, result = reconcile(raw, (event,))
        self.assertEqual(events, ())
        self.assertFalse({FindingType.ADD_PRESENT, FindingType.REMOVE_ABSENT} & {
            item.finding_type for item in result.findings
        })
        old = next(item for item in result.episodes if item.normalized_ticker == "OLD")
        new = next(item for item in result.episodes if item.normalized_ticker == "NEW")
        self.assertEqual(old.valid_to, new.valid_from)
        validate_publishable(result.episodes, result.findings)

    def test_identity_between_sparse_observations_has_no_membership_churn(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD",)),
            observation("2020-06-05", ("NEW",)),
        )
        _, _, events, result = reconcile(raw, (event,))
        self.assertEqual(events, ())
        old = next(item for item in result.episodes if item.normalized_ticker == "OLD")
        new = next(item for item in result.episodes if item.normalized_ticker == "NEW")
        self.assertEqual((old.valid_to, new.valid_from), ("2020-06-01", "2020-06-01"))
        validate_publishable(result.episodes, result.findings)

    def test_successor_backfill_entry_derives_predecessor_add(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ()),
            observation("2020-02-03", ("NEW",)),
            observation("2020-05-29", ("NEW",)),
            observation("2020-06-01", ("NEW",)),
        )
        overlays = tuple(overlay(item, event) for item in raw[1:3])
        _, _, events, result = reconcile(raw, (event,), overlays)
        self.assertEqual(
            [(item.action, item.source_ticker, item.effective_session) for item in events],
            [(MembershipAction.ADD, "OLD", "2020-02-03")],
        )
        self.assertFalse(any(
            item.normalized_ticker == "NEW" and item.valid_from < event.effective_session
            for item in result.episodes
        ))
        validate_publishable(result.episodes, result.findings)

    def test_predecessor_successor_overlap_is_reconciled_generically(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD", "NEW")),
            observation("2020-05-29", ("OLD",)),
            observation("2020-06-01", ("NEW",)),
        )
        unresolved = apply_ticker_overlays(raw, (event,), ())
        self.assertIn(FindingType.FUTURE_TICKER_BEFORE_RENAME, {
            item.finding_type for item in detect_episode_scoped_ticker_findings(
                unresolved.observations, (event,), (),
            )
        })
        drop = overlay(raw[0], event, OverlayOperation.DROP_DUPLICATE_SUCCESSOR_BEFORE_BOUNDARY)
        _, _, events, result = reconcile(raw, (event,), (drop,))
        self.assertEqual(events, ())
        self.assertNotIn(FindingType.FUTURE_TICKER_BEFORE_RENAME, {
            item.finding_type for item in result.findings
        })
        validate_publishable(result.episodes, result.findings)

    def test_historical_reuse_is_not_future_but_current_backfill_is(self):
        event = identity("Y", "X", "2011-12-16")
        raw = (
            observation("2011-01-03", ("X",)),
            observation("2011-12-12", ()),
            observation("2011-12-13", ("X",)),
            observation("2011-12-16", ("X",)),
        )
        unapplied = apply_ticker_overlays(raw, (event,), ())
        raw_manifest = build_reconciled_membership_event_manifest(
            SEED_SOURCE, raw, unapplied.observations, (event,), (),
        )
        raw_events = derive_reconciled_membership_events(
            raw, unapplied.observations, (event,), raw_manifest,
            seed_manifest=SEED_SOURCE, overlays=(),
        )
        self.assertIn(FindingType.FUTURE_TICKER_BEFORE_RENAME, {
            item.finding_type for item in detect_episode_scoped_ticker_findings(
                unapplied.observations, (event,), raw_events,
            )
        })

        repair = overlay(raw[2], event)
        _, _, events, result = reconcile(raw, (event,), (repair,))
        self.assertNotIn(FindingType.FUTURE_TICKER_BEFORE_RENAME, {
            item.finding_type for item in result.findings
        })
        x_episodes = [item for item in result.episodes if item.normalized_ticker == "X"]
        self.assertEqual(len(x_episodes), 2)
        with self.assertRaises(AmbiguousTickerEpisodeError):
            lookup_episode(result.episodes, "X")
        validate_publishable(result.episodes, result.findings)

    def test_reused_predecessor_is_episode_scoped_but_true_stale_blocks(self):
        event = identity("X", "Y", "2020-03-03")
        valid_raw = (
            observation("2020-01-02", ("X",)),
            observation("2020-03-03", ("X", "Y")),
        )
        _, _, events, result = reconcile(valid_raw, (event,))
        self.assertEqual(
            [(item.action, item.source_ticker) for item in events],
            [(MembershipAction.ADD, "X")],
        )
        self.assertNotIn(FindingType.STALE_OLD_TICKER_AFTER_RENAME, {
            item.finding_type for item in result.findings
        })
        with self.assertRaises(AmbiguousTickerEpisodeError):
            lookup_episode(result.episodes, "X")
        validate_publishable(result.episodes, result.findings)

        stale_raw = (
            observation("2020-01-02", ("X",), "stale-start"),
            observation("2020-03-03", ("X",), "stale-boundary"),
        )
        _, _, _, stale_result = reconcile(stale_raw, (event,))
        self.assertIn(FindingType.STALE_OLD_TICKER_AFTER_RENAME, {
            item.finding_type for item in stale_result.findings
        })

    def test_unaccepted_membership_event_cannot_establish_reuse_episode(self):
        event = identity("X", "Y", "2020-03-03")
        raw = (
            observation("2020-01-02", ("X",)),
            observation("2020-03-03", ("X", "Y")),
        )
        diagnostic = source("diagnostic", SourceRole.DIAGNOSTIC_REFERENCE)
        unaccepted_add = IndexMembershipEventV1(
            "unaccepted-x-add", "SP500", MembershipAction.ADD, "X", None,
            "2020-03-03", "2020-03-03", SessionBoundary.EFFECTIVE_SESSION,
            diagnostic.source_id, H,
        )
        result = compile_universe(
            policy=CompilePolicyV1(
                "SP500", raw[0].effective_session, "2030-01-01",
                "fixture-calendar-v1", "reconciled-policy-v1",
            ),
            manifests=(SEED_SOURCE, TICKER_SOURCE, diagnostic), observations=raw,
            membership_events=(unaccepted_add,), ticker_events=(event,),
        )
        types = {item.finding_type for item in result.findings}
        self.assertIn(FindingType.MISSING_EVIDENCE, types)
        self.assertIn(FindingType.STALE_OLD_TICKER_AFTER_RENAME, types)

    def test_real_membership_exit_reentry_creates_distinct_episodes(self):
        raw = (
            observation("2020-01-02", ("X",)),
            observation("2020-06-01", ()),
            observation("2022-01-03", ("X",)),
        )
        _, _, events, result = reconcile(raw)
        self.assertEqual([item.action for item in events], [MembershipAction.REMOVE, MembershipAction.ADD])
        matches = [item for item in result.episodes if item.normalized_ticker == "X"]
        self.assertEqual(len(matches), 2)
        self.assertNotEqual(matches[0].episode_id, matches[1].episode_id)
        validate_publishable(result.episodes, result.findings)

    def test_same_session_rename_then_exit_removes_successor(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD",)),
            observation("2020-06-01", ()),
        )
        _, _, events, result = reconcile(raw, (event,))
        self.assertEqual(
            [(item.action, item.source_ticker) for item in events],
            [(MembershipAction.REMOVE, "NEW")],
        )
        self.assertNotIn(FindingType.REMOVE_ABSENT, {item.finding_type for item in result.findings})
        validate_publishable(result.episodes, result.findings)

    def test_identity_when_predecessor_inactive_does_not_create_membership(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD",)),
            observation("2020-03-02", ()),
            observation("2020-06-01", ()),
        )
        _, _, events, result = reconcile(raw, (event,))
        self.assertEqual(
            [(item.action, item.source_ticker) for item in events],
            [(MembershipAction.REMOVE, "OLD")],
        )
        self.assertNotIn("NEW", {item.normalized_ticker for item in result.episodes})
        validate_publishable(result.episodes, result.findings)

    def test_reconciliation_is_deterministic(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ("OLD", "NEW")),
            observation("2020-06-01", ("NEW",)),
        )
        drop = overlay(raw[0], event, OverlayOperation.DROP_DUPLICATE_SUCCESSOR_BEFORE_BOUNDARY)
        first = reconcile(raw, (event,), (drop,))
        second = reconcile(raw, (event,), (drop,))
        self.assertEqual(first[1:], second[1:])
        self.assertEqual(first[3].output_hash, second[3].output_hash)

    def test_reconciliation_provenance_mutation_changes_downstream_hashes(self):
        event = identity("OLD", "NEW", "2020-06-01")
        raw = (
            observation("2020-01-02", ()),
            observation("2020-02-03", ("NEW",)),
            observation("2020-06-01", ("NEW",)),
        )
        base = overlay(raw[1], event, reason="first accepted evidence reason")
        changed = replace(base, reason="changed accepted evidence reason")
        first = reconcile(raw, (event,), (base,))
        second = reconcile(raw, (event,), (changed,))
        self.assertNotEqual(first[1].manifest_hash, second[1].manifest_hash)
        self.assertNotEqual(first[2][0].event_id, second[2][0].event_id)
        self.assertNotEqual(first[3].output_hash, second[3].output_hash)
        self.assertNotEqual(first[3].episodes[0].provenance_hash, second[3].episodes[0].provenance_hash)


if __name__ == "__main__":
    unittest.main()
