from __future__ import annotations

import asyncio
from datetime import date
import os
from pathlib import Path
import tempfile
import unittest

import duckdb
import pandas as pd
from openbb_core.provider.abstract.annotated_result import AnnotatedResult
from openbb_core.provider.standard_models.equity_historical import EquityHistoricalData

from aq_pit.provider_binding import (
    OpenFigiEvidence,
    QuantiacsEquityHistoricalFetcher,
    SecEvidence,
    SimFinEquityHistoricalFetcher,
    evaluate_provider_bindings,
)


DATES = pd.to_datetime(["2022-01-03", "2022-01-04", "2022-01-05"])


def binding_frames():
    episodes = pd.DataFrame([
        ("DD", "episode-dd", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
        ("ANTM_ELV", "episode-antm", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
        ("STI", "episode-sti", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
        ("FB_META", "episode-fb", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
        ("DISCK", "episode-disck", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
    ], columns=["case_id", "episode_id", "valid_from", "valid_to", "required_sessions"])
    candidates = pd.DataFrame([
        ("DD", "provider-dd-old", "DD", False, False, False),
        ("DD", "provider-dd-new", "DD", False, True, True),
        ("ANTM_ELV", "provider-elv", "ELV", True, True, True),
        ("STI", "provider-sti-old", "STI", True, True, False),
        ("STI", "provider-sti-reuse", "STI", False, False, True),
        ("FB_META", "provider-meta", "META", True, False, True),
    ], columns=["case_id", "provider_asset_identifier", "provider_symbol", "provider_identity_supported", "sec_identity_supported", "openfigi_supported"])
    observations = pd.DataFrame([
        ("provider-elv", when, 100.0 + position) for position, when in enumerate(DATES)
    ] + [("provider-wbd", when, 200.0) for when in DATES], columns=["provider_asset_identifier", "session_date", "close"])
    sessions = pd.DataFrame([
        (case_id, when) for case_id in episodes["case_id"] for when in DATES
    ], columns=["case_id", "session_date"])
    return episodes, candidates, observations, sessions


class FetcherTests(unittest.TestCase):
    def test_quantiacs_fetcher_uses_openbb_standard_model(self):
        raw = [{"time": "2022-01-03", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "vol": 10}]
        result = asyncio.run(QuantiacsEquityHistoricalFetcher.fetch_data(
            {"symbol": "AAA", "provider_asset_identifier": "provider-a"},
            upstream_loader=lambda query: raw,
        ))
        self.assertIsInstance(result, AnnotatedResult)
        self.assertIsInstance(result.result[0], EquityHistoricalData)
        self.assertEqual(result.metadata["provider_asset_identifier"], "provider-a")

    def test_simfin_fetcher_uses_openbb_standard_model(self):
        raw = [{"Date": "2022-01-03", "Open": 1.0, "High": 2.0, "Low": 0.5, "Close": 1.5, "Volume": 10}]
        result = asyncio.run(SimFinEquityHistoricalFetcher.fetch_data(
            {"symbol": "AAA", "simfin_id": 7}, upstream_loader=lambda query: raw,
        ))
        self.assertIsInstance(result.result[0], EquityHistoricalData)
        self.assertEqual(result.metadata["provider"], "SIMFIN")
        self.assertEqual(result.metadata["simfin_id"], 7)


class EvidenceBoundaryTests(unittest.TestCase):
    def test_provider_identifier_is_not_figi(self):
        with self.assertRaises(ValueError):
            OpenFigiEvidence("tts-123", "ticker/exchange")

    def test_standard_figi_is_supporting_evidence(self):
        evidence = OpenFigiEvidence("BBG000BCG930", "ELV/US")
        self.assertEqual(evidence.mapping_identifier, "ELV/US")

    def test_sec_metadata_must_originate_from_edgartools(self):
        os.environ.setdefault("EDGAR_LOCAL_DATA_DIR", str(Path(tempfile.gettempdir()) / "aq-edgar-test"))
        from edgar import Filing
        filing = Filing(1156039, "Elevance Health, Inc.", "8-K", "2022-06-28", "0001193125-22-183957")
        evidence = SecEvidence.from_edgartools(
            filing, effective_date=date(2022, 6, 28), content_hash="a" * 64,
            decision_role="SECURITY_CONTINUITY",
        )
        self.assertEqual(evidence.cik, 1156039)


class DuckDBBindingTests(unittest.TestCase):
    def setUp(self):
        self.connection = duckdb.connect(":memory:")
        frames = binding_frames()
        self.result = evaluate_provider_bindings(
            self.connection, episodes=frames[0], candidates=frames[1],
            observations=frames[2], sessions=frames[3],
        ).set_index("case_id")

    def tearDown(self):
        self.connection.close()

    def test_interval_join_is_owned_by_duckdb(self):
        count = self.connection.sql("SELECT count(*) FROM binding_interval_observations WHERE case_id='ANTM_ELV'").fetchone()[0]
        self.assertEqual(count, 3)

    def test_anti_join_is_owned_by_duckdb(self):
        count = self.connection.sql("SELECT count(*) FROM binding_missing_sessions WHERE case_id='STI'").fetchone()[0]
        self.assertEqual(count, 3)

    def test_conflict_query_fails_dd_closed(self):
        self.assertEqual(self.result.loc["DD", "binding_state"], "PROVIDER_BINDING_AMBIGUOUS")
        self.assertEqual(self.connection.sql("SELECT count(*) FROM binding_conflicts WHERE case_id='DD'").fetchone()[0], 1)

    def test_duplicate_query_fails_closed(self):
        episodes, candidates, observations, sessions = binding_frames()
        candidates = pd.concat([candidates, candidates.iloc[[2]]], ignore_index=True)
        result = evaluate_provider_bindings(
            self.connection, episodes=episodes, candidates=candidates,
            observations=observations, sessions=sessions,
        ).set_index("case_id")
        self.assertEqual(result.loc["ANTM_ELV", "binding_state"], "PROVIDER_BINDING_AMBIGUOUS")
        self.assertEqual(self.connection.sql("SELECT count(*) FROM binding_duplicates WHERE case_id='ANTM_ELV'").fetchone()[0], 1)

    def test_antm_elv_is_uniquely_authorized(self):
        self.assertEqual(self.result.loc["ANTM_ELV", "binding_state"], "PROVIDER_BINDING_AUTHORIZED")

    def test_sti_is_coverage_gap_not_identity_failure(self):
        self.assertEqual(self.result.loc["STI", "binding_state"], "KNOWN_PROVIDER_GAP_CANDIDATE")
        self.assertEqual(self.result.loc["STI", "missing_session_count"], 3)

    def test_openfigi_alone_cannot_backmap_meta_to_fb(self):
        self.assertEqual(self.result.loc["FB_META", "binding_state"], "PROVIDER_BINDING_AMBIGUOUS")

    def test_disck_terminal_gap_does_not_substitute_wbd(self):
        self.assertEqual(self.result.loc["DISCK", "binding_state"], "PROVIDER_BINDING_NOT_AVAILABLE")
        self.assertTrue(pd.isna(self.result.loc["DISCK", "provider_asset_identifier"]))

    def test_states_remain_distinct(self):
        self.assertEqual(len(set(self.result["binding_state"])), 4)

    def test_runtime_contains_no_ticker_specific_branches_or_generic_engine(self):
        root = Path(__file__).parents[1] / "aq_pit"
        source = (root / "provider_binding.py").read_text(encoding="utf-8")
        sql = (root / "provider_binding.sql").read_text(encoding="utf-8")
        for ticker in ("DD", "ANTM", "ELV", "STI", "FB", "META", "DISCK", "WBD"):
            self.assertNotIn(f'"{ticker}"', source)
            self.assertNotIn(f"'{ticker}'", source)
            self.assertNotIn(f"'{ticker}'", sql)
        for forbidden in ("ProviderRegistry", "ProviderRouter", "SecurityMaster", "RelationalEngine"):
            self.assertNotIn(f"class {forbidden}", source)


if __name__ == "__main__":
    unittest.main()
