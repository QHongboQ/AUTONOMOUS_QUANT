from __future__ import annotations

import unittest

from aq_pit.canonical import sha256_hex
from aq_pit.domain import (
    AmbiguousTickerEpisodeError,
    SnapshotObservationV1,
    compile_thin_universe,
    lookup_episode,
)
from aq_pit.facts import AcceptedFacts, IdentityFact, OverlayCaseFact
from fixture_loader import load_fixture


H = "b" * 64
CASES = {
    item["id"]: item
    for item in load_fixture("frozen_regressions_v1.json")["cases"]
}


def _facts(case_id: str, run: dict[str, object]) -> AcceptedFacts:
    identities = tuple(
        IdentityFact(
            old_ticker=item["old_ticker"],
            new_ticker=item["new_ticker"],
            announcement_date=item.get("announcement_date"),
            effective_session=item["effective_session"],
            evidence_id=f"fixture-{case_id}-{position}",
        )
        for position, item in enumerate(run.get("identities", ()), start=1)
    )
    overlays = tuple(OverlayCaseFact(**item) for item in run.get("overlays", ()))
    return AcceptedFacts(
        schema_version="PITFrozenRegressionFactsV1",
        identity_events=identities,
        overlay_cases=overlays,
        finding_resolutions=(),
        expected_counts=(),
        facts_hash=sha256_hex({"case_id": case_id, "run": run}),
    )


def _observations(case_id: str, run_name: str, run: dict[str, object]):
    return tuple(
        SnapshotObservationV1(
            observation_id=f"{case_id}-{run_name}-{position}",
            index_id="SP500",
            effective_session=item["session"],
            tickers=tuple(item["tickers"]),
            source_id="frozen-fixture-v1",
            evidence_hash=H,
        )
        for position, item in enumerate(run["observations"], start=1)
    )


class FrozenFixtureBlackBoxRegressions(unittest.TestCase):
    def _assert_case(self, case_id: str) -> None:
        case = CASES[case_id]
        if "invalid_observation" in case:
            invalid = case["invalid_observation"]
            with self.assertRaisesRegex(ValueError, case["expected_error"]):
                SnapshotObservationV1(
                    observation_id=f"{case_id}-invalid",
                    index_id="SP500",
                    effective_session=invalid["session"],
                    tickers=tuple(invalid["tickers"]),
                    source_id="frozen-fixture-v1",
                    evidence_hash=H,
                )
            return

        for position, run in enumerate(case["runs"], start=1):
            run_name = run.get("name", str(position))
            with self.subTest(run=run_name):
                result = compile_thin_universe(
                    _observations(case_id, run_name, run),
                    _facts(case_id, run),
                    end_session=run["end_session"],
                )
                actual_episodes = [
                    [item.normalized_ticker, item.valid_from, item.valid_to]
                    for item in result.episodes
                ]
                expected = run["expected"]
                self.assertEqual(actual_episodes, expected["episodes"])
                self.assertEqual(len(result.overlays), expected["overlay_count"])
                self.assertEqual(
                    len(result.membership_events),
                    expected["membership_event_count"],
                )
                self.assertEqual(result.domain_errors, ())

                present = {item.normalized_ticker for item in result.episodes}
                for ticker in expected.get("excluded_tickers", ()):
                    self.assertNotIn(ticker, present)
                for ticker in expected.get("ambiguous_undated", ()):
                    with self.assertRaisesRegex(
                        AmbiguousTickerEpisodeError,
                        "AMBIGUOUS_TICKER_EPISODE",
                    ):
                        lookup_episode(result.episodes, ticker)
                for lookup in expected.get("dated_lookups", ()):
                    episode = lookup_episode(
                        result.episodes,
                        lookup["ticker"],
                        lookup["session"],
                    )
                    self.assertEqual(
                        [episode.normalized_ticker, episode.valid_from, episode.valid_to],
                        lookup["episode"],
                    )

    def test_r01_invalid_date(self):
        self._assert_case("R01")

    def test_r02_fb_to_meta(self):
        self._assert_case("R02")

    def test_r03_cday_to_day_backfill(self):
        self._assert_case("R03")

    def test_r04_re_to_eg(self):
        self._assert_case("R04")

    def test_r05_wltw_to_wtw_effective_boundary(self):
        self._assert_case("R05")

    def test_r06_kors_to_cpri(self):
        self._assert_case("R06")

    def test_r07_q_reuse_then_iqv(self):
        self._assert_case("R07")

    def test_r08_dlph_exit_reentry(self):
        self._assert_case("R08")

    def test_r09_corporate_action_membership_firewall(self):
        self._assert_case("R09")

    def test_r10_aptv_future_ticker_guard(self):
        self._assert_case("R10")

    def test_r11_cpri_future_ticker_guard(self):
        self._assert_case("R11")

    def test_r12_iqv_future_ticker_guard(self):
        self._assert_case("R12")

    def test_r13_generic_ticker_reuse(self):
        self._assert_case("R13")


if __name__ == "__main__":
    unittest.main()
