import unittest

from aq_pit.compiler import compile_universe
from aq_pit.contracts import (
    CompilePolicyV1,
    CorporateActionEventV1,
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
from aq_pit.overlays import detect_future_ticker_backfill
from aq_pit.validation import AmbiguousTickerEpisodeError, lookup_episode, validate_publishable


H = "b" * 64


def source(source_id, role):
    return SourceManifestV1(
        source_id, role, "fixture", "https://example.invalid/source", "v1",
        "2026-09-10T00:00:00Z", "application/json", 1, H, "fixture",
        "1990-01-02", "2030-01-01", (), "adapter-v1",
    )


SOURCES = (
    source("seed", SourceRole.HISTORICAL_SEED),
    source("member", SourceRole.PRECISE_MEMBERSHIP_EVENTS),
    source("ticker", SourceRole.TICKER_IDENTITY_EVIDENCE),
    source("corp", SourceRole.DIAGNOSTIC_REFERENCE),
)


def rename_event(old, new, boundary, event_id=None, announcement=None):
    return TickerIdentityEventV1(
        event_id or f"rename-{old}-{new}", old, new, announcement,
        boundary, boundary, SessionBoundary.EFFECTIVE_SESSION, "ticker", H,
    )


def membership(event_id, action, ticker, boundary):
    return IndexMembershipEventV1(
        event_id, "SP500", action, ticker, None, boundary, boundary,
        SessionBoundary.EFFECTIVE_SESSION, "member", H,
    )


def overlay(observation_id, event, overlay_id=None):
    return TickerEpisodeOverlayV1(
        overlay_id or f"overlay-{event.event_id}", observation_id, event.event_id,
        event.effective_session, OverlayOperation.MAP_SUCCESSOR_TO_PREDECESSOR,
        "evidence-backed continuous ticker rename", (H,), ReviewState.ACCEPTED,
    )


def compile_rename(old, new, boundary, *, start, end, raw_ticker=None, announcement=None):
    event = rename_event(old, new, boundary, announcement=announcement)
    observation = SnapshotObservationV1("seed-row", "SP500", start, (raw_ticker or old,), "seed", H)
    overlays = (overlay(observation.observation_id, event),) if raw_ticker == new else ()
    result = compile_universe(
        policy=CompilePolicyV1("SP500", start, end, "fixture-calendar-v1", "policy-v1"),
        manifests=SOURCES,
        observations=(observation,),
        ticker_events=(event,),
        overlays=overlays,
    )
    validate_publishable(result.episodes, result.findings)
    old_episode = next(item for item in result.episodes if item.normalized_ticker == old)
    new_episode = next(item for item in result.episodes if item.normalized_ticker == new)
    return result, old_episode, new_episode


class FrozenBlueprintRegressions(unittest.TestCase):
    def test_r01_mmm_parser_date_regression(self):
        with self.assertRaisesRegex(ValueError, "ISO date"):
            IndexMembershipEventV1(
                "bad-date", "SP500", MembershipAction.ADD, "MMM", None,
                "MMM", "2020-01-02", SessionBoundary.EFFECTIVE_SESSION,
                "member", H,
            )

    def test_r02_fb_to_meta(self):
        _, old, new = compile_rename(
            "FB", "META", "2022-06-09", start="2022-01-03", end="2023-01-03",
        )
        self.assertEqual(old.valid_to, new.valid_from)
        self.assertEqual(new.valid_from, "2022-06-09")
        self.assertNotEqual(old.episode_id, new.episode_id)

    def test_r03_cday_to_day(self):
        _, old, new = compile_rename(
            "CDAY", "DAY", "2024-02-01", start="2024-01-02", end="2024-06-03",
            raw_ticker="DAY",
        )
        self.assertEqual(old.valid_to, new.valid_from)
        self.assertGreaterEqual(new.valid_from, "2024-02-01")

    def test_r04_re_to_eg(self):
        _, old, new = compile_rename(
            "RE", "EG", "2023-07-10", start="2023-01-03", end="2024-01-03",
        )
        self.assertEqual((old.valid_to, new.valid_from), ("2023-07-10", "2023-07-10"))

    def test_r05_wltw_to_wtw_announcement_not_effective(self):
        _, old, new = compile_rename(
            "WLTW", "WTW", "2022-01-10", start="2021-12-01", end="2022-03-01",
            announcement="2022-01-05",
        )
        self.assertEqual(old.valid_to, "2022-01-10")
        self.assertEqual(new.valid_from, "2022-01-10")
        self.assertNotEqual(new.valid_from, "2022-01-05")

    def test_r06_kors_to_cpri(self):
        _, old, new = compile_rename(
            "KORS", "CPRI", "2019-01-02", start="2018-01-02", end="2020-01-02",
        )
        self.assertEqual(old.valid_to, new.valid_from)
        self.assertGreaterEqual(new.valid_from, "2019-01-02")

    def test_r07_q_to_iqv_and_historical_q(self):
        policy = CompilePolicyV1("SP500", "2000-01-03", "2019-01-02", "fixture-calendar-v1", "policy-v1")
        events = (
            membership("old-q-exit", MembershipAction.REMOVE, "Q", "2001-01-02"),
            membership("new-q-entry", MembershipAction.ADD, "Q", "2016-01-04"),
        )
        identity = rename_event("Q", "IQV", "2017-11-15")
        result = compile_universe(
            policy=policy, manifests=SOURCES,
            observations=(SnapshotObservationV1("seed-row", "SP500", policy.start_session, ("Q",), "seed", H),),
            membership_events=events, ticker_events=(identity,),
        )
        validate_publishable(result.episodes, result.findings)
        q_episodes = [item for item in result.episodes if item.normalized_ticker == "Q"]
        iqv = next(item for item in result.episodes if item.normalized_ticker == "IQV")
        self.assertEqual(len(q_episodes), 2)
        self.assertNotEqual(q_episodes[0].episode_id, q_episodes[1].episode_id)
        self.assertEqual(q_episodes[1].valid_to, iqv.valid_from)

    def test_r08_old_new_dlph(self):
        policy = CompilePolicyV1("SP500", "2008-01-02", "2013-01-02", "fixture-calendar-v1", "policy-v1")
        result = compile_universe(
            policy=policy, manifests=SOURCES,
            observations=(SnapshotObservationV1("seed-row", "SP500", policy.start_session, ("DLPH",), "seed", H),),
            membership_events=(
                membership("old-exit", MembershipAction.REMOVE, "DLPH", "2009-01-02"),
                membership("new-entry", MembershipAction.ADD, "DLPH", "2011-01-03"),
            ),
        )
        validate_publishable(result.episodes, result.findings)
        matches = [item for item in result.episodes if item.normalized_ticker == "DLPH"]
        self.assertEqual(len(matches), 2)
        self.assertLessEqual(matches[0].valid_to, matches[1].valid_from)
        self.assertNotEqual(matches[0].episode_id, matches[1].episode_id)
        with self.assertRaisesRegex(AmbiguousTickerEpisodeError, "AMBIGUOUS_TICKER_EPISODE"):
            lookup_episode(result.episodes, "DLPH")

    def test_r09_disck_wbd_corporate_firewall(self):
        policy = CompilePolicyV1("SP500", "2021-01-04", "2023-01-03", "fixture-calendar-v1", "policy-v1")
        observation = SnapshotObservationV1("seed-row", "SP500", policy.start_session, ("DISCK",), "seed", H)
        actions = tuple(
            CorporateActionEventV1(
                f"corp-{action_type.lower()}", action_type, "DISCK", "WBD",
                "2022-04-11", "2022-04-11", "corp", H,
                "context-only successor evidence",
            )
            for action_type in ("MERGER", "SPINOFF", "ACQUISITION")
        )
        for action in actions:
            with self.subTest(action_type=action.action_type):
                context_only = compile_universe(
                    policy=policy, manifests=SOURCES, observations=(observation,),
                    corporate_events=(action,),
                )
                self.assertNotIn("WBD", {item.normalized_ticker for item in context_only.episodes})
        explicit = compile_universe(
            policy=policy, manifests=SOURCES, observations=(observation,), corporate_events=actions,
            membership_events=(membership("wbd-add", MembershipAction.ADD, "WBD", "2022-04-11"),),
        )
        self.assertIn("WBD", {item.normalized_ticker for item in explicit.episodes})

    def test_r10_aptv_future_ticker_guard(self):
        event = rename_event("DLPH", "APTV", "2017-12-05")
        raw = SnapshotObservationV1("seed-row", "SP500", "2017-01-03", ("APTV",), "seed", H)
        before = raw.tickers
        findings = detect_future_ticker_backfill((raw,), (event,))
        self.assertEqual(findings[0].finding_type, FindingType.FUTURE_TICKER_BEFORE_RENAME)
        self.assertEqual(raw.tickers, before)
        result, old, new = compile_rename(
            "DLPH", "APTV", "2017-12-05", start="2017-01-03", end="2018-06-01",
            raw_ticker="APTV",
        )
        self.assertEqual(old.valid_to, "2017-12-05")
        self.assertFalse(any(item.normalized_ticker == "APTV" and item.valid_from < "2017-12-05" for item in result.episodes))
        self.assertEqual(new.valid_from, "2017-12-05")

    def test_r11_cpri_future_ticker_guard(self):
        result, _, new = compile_rename(
            "KORS", "CPRI", "2019-01-02", start="2018-01-02", end="2020-01-02",
            raw_ticker="CPRI",
        )
        self.assertFalse(any(item.normalized_ticker == "CPRI" and item.valid_from < "2019-01-02" for item in result.episodes))
        self.assertEqual(new.valid_from, "2019-01-02")

    def test_r12_iqv_future_ticker_guard(self):
        result, _, new = compile_rename(
            "Q", "IQV", "2017-11-15", start="2017-01-03", end="2018-06-01",
            raw_ticker="IQV",
        )
        self.assertFalse(any(item.normalized_ticker == "IQV" and item.valid_from < "2017-11-15" for item in result.episodes))
        self.assertEqual(new.valid_from, "2017-11-15")

    def test_r13_generic_ticker_reuse(self):
        policy = CompilePolicyV1("SP500", "2020-01-02", "2023-01-03", "fixture-calendar-v1", "policy-v1")
        result = compile_universe(
            policy=policy, manifests=SOURCES,
            observations=(SnapshotObservationV1("seed-row", "SP500", policy.start_session, ("XYZ",), "seed", H),),
            membership_events=(
                membership("xyz-exit", MembershipAction.REMOVE, "XYZ", "2020-06-01"),
                membership("xyz-reentry", MembershipAction.ADD, "XYZ", "2022-01-03"),
            ),
        )
        validate_publishable(result.episodes, result.findings)
        matches = [item for item in result.episodes if item.normalized_ticker == "XYZ"]
        self.assertEqual(len(matches), 2)
        self.assertNotEqual(matches[0].episode_id, matches[1].episode_id)
        with self.assertRaisesRegex(AmbiguousTickerEpisodeError, "AMBIGUOUS_TICKER_EPISODE"):
            lookup_episode(matches, "XYZ")
        self.assertEqual(lookup_episode(matches, "XYZ", "2020-03-02").episode_id, matches[0].episode_id)
        self.assertEqual(lookup_episode(matches, "XYZ", "2022-03-01").episode_id, matches[1].episode_id)


if __name__ == "__main__":
    unittest.main()
