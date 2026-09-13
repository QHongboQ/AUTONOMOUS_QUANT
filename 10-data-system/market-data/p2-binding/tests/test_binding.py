from __future__ import annotations

import asyncio
import copy
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import duckdb
import pandas as pd
from openbb_core.provider.abstract.annotated_result import AnnotatedResult
from openbb_core.provider.standard_models.equity_historical import EquityHistoricalData

import aq_market_data_binding.binding as binding_module
from aq_market_data_binding import (
    OpenFigiEvidence,
    QuantiacsEquityHistoricalFetcher,
    SecEvidence,
    SimFinEquityHistoricalFetcher,
    evaluate_provider_bindings,
    load_provider_binding_authority,
)


DATES = pd.to_datetime(["2022-01-03", "2022-01-04", "2022-01-05"])
SOURCE_HASH = "a" * 64


def binding_frames():
    episodes = pd.DataFrame([
        ("DD", "episode-dd", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
        ("ANTM_ELV", "episode-antm", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
        ("STI", "episode-sti", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
        ("FB_META", "episode-fb", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
        ("DISCK", "episode-disck", DATES[0], DATES[-1] + pd.Timedelta(days=1), 3),
    ], columns=["case_id", "episode_id", "valid_from", "valid_to", "required_sessions"])
    candidates = pd.DataFrame([
        ("DD", "QUANTIACS", "provider-dd-old", "DD", False, False, False),
        ("DD", "QUANTIACS", "provider-dd-new", "DD", False, True, True),
        ("ANTM_ELV", "QUANTIACS", "provider-elv", "ELV", True, True, True),
        ("STI", "QUANTIACS", "provider-sti-old", "STI", True, True, False),
        ("STI", "QUANTIACS", "provider-sti-reuse", "STI", False, False, True),
        ("FB_META", "QUANTIACS", "provider-meta", "META", True, False, True),
    ], columns=["case_id", "provider", "provider_asset_identifier", "provider_symbol", "provider_identity_supported", "sec_identity_supported", "openfigi_supported"])
    observations = pd.DataFrame([
        ("provider-elv", when, 100.0 + position) for position, when in enumerate(DATES)
    ] + [("provider-wbd", when, 200.0) for when in DATES], columns=["provider_asset_identifier", "session_date", "close"])
    sessions = pd.DataFrame([
        (case_id, when) for case_id in episodes["case_id"] for when in DATES
    ], columns=["case_id", "session_date"])
    return episodes, candidates, observations, sessions


def single_case_frames(*, required: int, observed: int):
    dates = pd.date_range("2020-01-02", periods=required, freq="B")
    episodes = pd.DataFrame([
        ("GENERIC", "episode-generic", dates[0], dates[-1] + pd.Timedelta(days=1), required),
    ], columns=["case_id", "episode_id", "valid_from", "valid_to", "required_sessions"])
    candidates = pd.DataFrame([
        ("GENERIC", "QUANTIACS", "provider-generic", "GENERIC", True, True, False),
    ], columns=["case_id", "provider", "provider_asset_identifier", "provider_symbol", "provider_identity_supported", "sec_identity_supported", "openfigi_supported"])
    observation_rows = [
        ("provider-generic", when, 100.0 + position)
        for position, when in enumerate(dates[:observed])
    ]
    if not observation_rows:
        observation_rows.append(("provider-generic", dates[0] - pd.Timedelta(days=1), 99.0))
    observations = pd.DataFrame(
        observation_rows,
        columns=["provider_asset_identifier", "session_date", "close"],
    )
    sessions = pd.DataFrame([
        ("GENERIC", when) for when in dates
    ], columns=["case_id", "session_date"])
    return episodes, candidates, observations, sessions


def accepted_authority_fact(historical_ticker: str | None = None):
    path = Path(binding_module.__file__).with_name(
        "accepted_provider_binding_facts.json"
    )
    facts = json.loads(path.read_text(encoding="utf-8"))["facts"]
    if historical_ticker is None:
        return facts[0]
    return next(fact for fact in facts if fact["historical_ticker"] == historical_ticker)


def authority_case_frames(
    *, historical_ticker: str | None = None, required: int = 3,
    observed: int = 3, wrong_asset: bool = False,
    interval_offset_days: int = 0,
):
    fact = accepted_authority_fact(historical_ticker)
    valid_from = pd.Timestamp(fact["valid_from"])
    valid_to = pd.Timestamp(fact["valid_to"]) + pd.Timedelta(days=interval_offset_days)
    dates = pd.date_range(valid_from, periods=required, freq="B")
    asset = fact["provider_asset_identifier"] + ("~wrong" if wrong_asset else "")
    episodes = pd.DataFrame([(
        "AUTHORITY", fact["episode_id"], valid_from, valid_to, required,
    )], columns=["case_id", "episode_id", "valid_from", "valid_to", "required_sessions"])
    candidates = pd.DataFrame([(
        "AUTHORITY", fact["provider"], asset, fact["provider_symbol"],
        False, False, False,
    )], columns=["case_id", "provider", "provider_asset_identifier", "provider_symbol", "provider_identity_supported", "sec_identity_supported", "openfigi_supported"])
    observation_rows = [
        (asset, when, 100.0 + position)
        for position, when in enumerate(dates[:observed])
    ]
    if not observation_rows:
        observation_rows.append((asset, dates[0] - pd.Timedelta(days=1), 99.0))
    observations = pd.DataFrame(
        observation_rows,
        columns=["provider_asset_identifier", "session_date", "close"],
    )
    sessions = pd.DataFrame(
        [("AUTHORITY", when) for when in dates],
        columns=["case_id", "session_date"],
    )
    return episodes, candidates, observations, sessions


class FetcherTests(unittest.TestCase):
    def test_quantiacs_fetcher_uses_openbb_standard_model(self):
        raw = [{"time": "2022-01-03", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "vol": 10}]
        result = asyncio.run(QuantiacsEquityHistoricalFetcher.fetch_data(
            {
                "symbol": "AAA",
                "provider_asset_identifier": "provider-a",
                "provider_symbol": "PROVIDER_AAA",
                "adjustment_semantics": "provider_adjusted",
                "source_observation_sha256": SOURCE_HASH,
            },
            upstream_loader=lambda query: raw,
        ))
        self.assertIsInstance(result, AnnotatedResult)
        self.assertIsInstance(result.result[0], EquityHistoricalData)
        self.assertEqual(result.metadata["provider_asset_identifier"], "provider-a")
        self.assertEqual(result.metadata["provider_symbol"], "PROVIDER_AAA")
        self.assertEqual(result.metadata["adjustment_semantics"], "provider_adjusted")
        self.assertEqual(result.metadata["source_observation_sha256"], SOURCE_HASH)

    def test_simfin_fetcher_uses_openbb_standard_model(self):
        raw = [{"Date": "2022-01-03", "Open": 1.0, "High": 2.0, "Low": 0.5, "Close": 1.5, "Volume": 10}]
        result = asyncio.run(SimFinEquityHistoricalFetcher.fetch_data(
            {
                "symbol": "AAA",
                "simfin_id": 7,
                "provider_symbol": "SIMFIN_AAA",
                "adjustment_semantics": "provider_adjusted",
                "source_observation_sha256": SOURCE_HASH,
            },
            upstream_loader=lambda query: raw,
        ))
        self.assertIsInstance(result.result[0], EquityHistoricalData)
        self.assertEqual(result.metadata["provider"], "SIMFIN")
        self.assertEqual(result.metadata["provider_asset_identifier"], 7)
        self.assertEqual(result.metadata["provider_symbol"], "SIMFIN_AAA")
        self.assertEqual(result.metadata["adjustment_semantics"], "provider_adjusted")
        self.assertEqual(result.metadata["source_observation_sha256"], SOURCE_HASH)


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


class ProviderBindingAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.authority_path = Path(binding_module.__file__).with_name(
            "accepted_provider_binding_facts.json"
        )

    def write_payload(self, directory: str, payload: dict) -> Path:
        path = Path(directory) / "accepted_provider_binding_facts.json"
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n",
        )
        return path

    def test_authority_file_has_exactly_twelve_facts(self):
        authority = load_provider_binding_authority()
        self.assertEqual(len(authority), 12)
        self.assertEqual(authority["episode_id"].nunique(), 12)

    def test_altered_authority_hash_fails_closed(self):
        raw = self.authority_path.read_bytes().replace(b'"expected_count": 12', b'"expected_count": 11')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / self.authority_path.name
            path.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "file hash mismatch"):
                load_provider_binding_authority(path)

    def test_duplicate_authority_fact_fails_closed(self):
        payload = json.loads(self.authority_path.read_text(encoding="utf-8"))
        payload["facts"][1] = copy.deepcopy(payload["facts"][0])
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_payload(directory, payload)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with mock.patch.object(binding_module, "_AUTHORITY_FILE_SHA256", digest):
                with self.assertRaisesRegex(ValueError, "duplicate"):
                    load_provider_binding_authority(path)

    def test_authority_count_is_enforced(self):
        payload = json.loads(self.authority_path.read_text(encoding="utf-8"))
        payload["facts"].pop()
        payload["expected_count"] = 11
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_payload(directory, payload)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            with mock.patch.object(binding_module, "_AUTHORITY_FILE_SHA256", digest):
                with self.assertRaisesRegex(ValueError, "fact count mismatch"):
                    load_provider_binding_authority(path)

    def evaluate_authority_case(self, **kwargs) -> tuple[pd.Series, duckdb.DuckDBPyConnection]:
        connection = duckdb.connect(":memory:")
        frames = authority_case_frames(**kwargs)
        result = evaluate_provider_bindings(
            connection, episodes=frames[0], candidates=frames[1],
            observations=frames[2], sessions=frames[3],
        ).iloc[0]
        return result, connection

    def test_exact_accepted_provider_asset_is_authorized(self):
        result, connection = self.evaluate_authority_case()
        try:
            self.assertEqual(result["identity_state"], "PROVIDER_BINDING_AUTHORIZED")
            self.assertEqual(
                connection.sql(
                    "SELECT authority_supported FROM binding_effective_candidates"
                ).fetchone()[0],
                True,
            )
        finally:
            connection.close()

    def test_same_ticker_wrong_asset_fails_closed(self):
        result, connection = self.evaluate_authority_case(wrong_asset=True)
        try:
            self.assertEqual(result["identity_state"], "PROVIDER_BINDING_AMBIGUOUS")
        finally:
            connection.close()

    def test_out_of_authority_interval_fails_closed(self):
        result, connection = self.evaluate_authority_case(interval_offset_days=1)
        try:
            self.assertEqual(result["identity_state"], "PROVIDER_BINDING_AMBIGUOUS")
        finally:
            connection.close()

    def test_authority_does_not_convert_partial_coverage(self):
        result, connection = self.evaluate_authority_case(required=3, observed=2)
        try:
            self.assertEqual(result["identity_state"], "PROVIDER_BINDING_AUTHORIZED")
            self.assertEqual(result["coverage_state"], "PARTIAL_PROVIDER_COVERAGE")
            self.assertEqual(result["missing_session_count"], 1)
        finally:
            connection.close()

    def test_arnc_hwm_authority_retains_455_missing_sessions(self):
        result, connection = self.evaluate_authority_case(
            historical_ticker="ARNC", required=1323, observed=868,
        )
        try:
            self.assertEqual(result["identity_state"], "PROVIDER_BINDING_AUTHORIZED")
            self.assertEqual(result["coverage_state"], "PARTIAL_PROVIDER_COVERAGE")
            self.assertEqual(result["missing_session_count"], 455)
        finally:
            connection.close()


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
        self.assertEqual(self.result.loc["DD", "identity_state"], "PROVIDER_BINDING_AMBIGUOUS")
        self.assertEqual(self.result.loc["DD", "coverage_state"], "COVERAGE_NOT_EVALUATED")
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

    def test_zero_session_episode_is_preserved_and_fails_closed(self):
        episodes, candidates, observations, sessions = binding_frames()
        sessions = sessions[sessions["case_id"] != "ANTM_ELV"]
        result = evaluate_provider_bindings(
            self.connection, episodes=episodes, candidates=candidates,
            observations=observations, sessions=sessions,
        ).set_index("case_id")
        self.assertIn("ANTM_ELV", result.index)
        self.assertEqual(result.loc["ANTM_ELV", "binding_state"], "PROVIDER_BINDING_AMBIGUOUS")
        self.assertEqual(len(result), len(episodes))

    def test_partial_session_input_fails_closed(self):
        episodes, candidates, observations, sessions = binding_frames()
        sessions = sessions[
            (sessions["case_id"] != "ANTM_ELV")
            | (sessions["session_date"] != DATES[-1])
        ]
        result = evaluate_provider_bindings(
            self.connection, episodes=episodes, candidates=candidates,
            observations=observations, sessions=sessions,
        ).set_index("case_id")
        self.assertEqual(result.loc["ANTM_ELV", "binding_state"], "PROVIDER_BINDING_AMBIGUOUS")
        self.assertEqual(result.loc["ANTM_ELV", "coverage_state"], "COVERAGE_NOT_EVALUATED")

    def test_out_of_episode_session_fails_closed(self):
        episodes, candidates, observations, sessions = binding_frames()
        target = sessions["case_id"] == "ANTM_ELV"
        target_rows = sessions.index[target]
        sessions.loc[target_rows[-1], "session_date"] = DATES[-1] + pd.Timedelta(days=10)
        result = evaluate_provider_bindings(
            self.connection, episodes=episodes, candidates=candidates,
            observations=observations, sessions=sessions,
        ).set_index("case_id")
        self.assertEqual(result.loc["ANTM_ELV", "binding_state"], "PROVIDER_BINDING_AMBIGUOUS")
        self.assertEqual(result.loc["ANTM_ELV", "coverage_state"], "COVERAGE_NOT_EVALUATED")

    def test_decision_cardinality_matches_unique_episodes(self):
        episodes, candidates, observations, sessions = binding_frames()
        result = evaluate_provider_bindings(
            self.connection, episodes=episodes, candidates=candidates,
            observations=observations, sessions=sessions,
        )
        self.assertEqual(len(result), len(episodes))
        self.assertEqual(result["case_id"].nunique(), len(episodes))

    def test_antm_elv_is_uniquely_authorized(self):
        self.assertEqual(self.result.loc["ANTM_ELV", "binding_state"], "PROVIDER_BINDING_AUTHORIZED")
        self.assertEqual(self.result.loc["ANTM_ELV", "identity_state"], "PROVIDER_BINDING_AUTHORIZED")
        self.assertEqual(self.result.loc["ANTM_ELV", "coverage_state"], "COMPLETE_PROVIDER_COVERAGE")

    def test_sti_is_coverage_gap_not_identity_failure(self):
        self.assertEqual(self.result.loc["STI", "binding_state"], "KNOWN_PROVIDER_GAP_CANDIDATE")
        self.assertEqual(self.result.loc["STI", "identity_state"], "PROVIDER_BINDING_AUTHORIZED")
        self.assertEqual(self.result.loc["STI", "coverage_state"], "ZERO_PROVIDER_COVERAGE")
        self.assertEqual(self.result.loc["STI", "missing_session_count"], 3)

    def test_openfigi_alone_cannot_backmap_meta_to_fb(self):
        self.assertEqual(self.result.loc["FB_META", "binding_state"], "PROVIDER_BINDING_AMBIGUOUS")

    def test_disck_terminal_gap_does_not_substitute_wbd(self):
        self.assertEqual(self.result.loc["DISCK", "binding_state"], "PROVIDER_BINDING_NOT_AVAILABLE")
        self.assertEqual(self.result.loc["DISCK", "coverage_state"], "COVERAGE_NOT_EVALUATED")
        self.assertTrue(pd.isna(self.result.loc["DISCK", "provider_asset_identifier"]))

    def evaluate_single_case(self, *, required: int, observed: int) -> pd.Series:
        episodes, candidates, observations, sessions = single_case_frames(
            required=required, observed=observed,
        )
        return evaluate_provider_bindings(
            self.connection, episodes=episodes, candidates=candidates,
            observations=observations, sessions=sessions,
        ).iloc[0]

    def test_complete_provider_coverage(self):
        result = self.evaluate_single_case(required=3, observed=3)
        self.assertEqual(result["identity_state"], "PROVIDER_BINDING_AUTHORIZED")
        self.assertEqual(result["coverage_state"], "COMPLETE_PROVIDER_COVERAGE")
        self.assertEqual(result["decision_state"], "PROVIDER_BINDING_AUTHORIZED")
        self.assertEqual(result["missing_session_count"], 0)

    def test_zero_provider_coverage(self):
        result = self.evaluate_single_case(required=3, observed=0)
        self.assertEqual(result["identity_state"], "PROVIDER_BINDING_AUTHORIZED")
        self.assertEqual(result["coverage_state"], "ZERO_PROVIDER_COVERAGE")
        self.assertEqual(result["decision_state"], "KNOWN_PROVIDER_GAP_CANDIDATE")
        self.assertEqual(result["missing_session_count"], 3)

    def test_partial_provider_observation_coverage(self):
        result = self.evaluate_single_case(required=3, observed=2)
        self.assertEqual(result["identity_state"], "PROVIDER_BINDING_AUTHORIZED")
        self.assertEqual(result["coverage_state"], "PARTIAL_PROVIDER_COVERAGE")
        self.assertEqual(result["decision_state"], "PARTIAL_PROVIDER_COVERAGE")
        self.assertEqual(result["missing_session_count"], 1)

    def test_arnc_hwm_partial_provider_observation_coverage(self):
        result = self.evaluate_single_case(required=1323, observed=868)
        self.assertEqual(result["identity_state"], "PROVIDER_BINDING_AUTHORIZED")
        self.assertEqual(result["coverage_state"], "PARTIAL_PROVIDER_COVERAGE")
        self.assertEqual(result["decision_state"], "PARTIAL_PROVIDER_COVERAGE")
        self.assertEqual(result["missing_session_count"], 455)

    def test_ambiguous_identity_does_not_evaluate_coverage(self):
        self.assertEqual(self.result.loc["DD", "identity_state"], "PROVIDER_BINDING_AMBIGUOUS")
        self.assertEqual(self.result.loc["DD", "coverage_state"], "COVERAGE_NOT_EVALUATED")

    def test_unavailable_provider_does_not_evaluate_coverage(self):
        self.assertEqual(self.result.loc["DISCK", "identity_state"], "PROVIDER_BINDING_NOT_AVAILABLE")
        self.assertEqual(self.result.loc["DISCK", "coverage_state"], "COVERAGE_NOT_EVALUATED")

    def test_combined_decision_retains_binding_state_compatibility_alias(self):
        self.assertTrue((self.result["decision_state"] == self.result["binding_state"]).all())

    def test_states_remain_distinct(self):
        self.assertEqual(len(set(self.result["binding_state"])), 4)

    def test_runtime_contains_no_ticker_specific_branches_or_generic_engine(self):
        root = Path(__file__).parents[1] / "aq_market_data_binding"
        source = "\n".join(
            path.read_text(encoding="utf-8") for path in root.glob("*.py")
        )
        sql = (root / "binding.sql").read_text(encoding="utf-8")
        for ticker in (
            "DD", "ANTM", "ELV", "STI", "FB", "META", "DISCK", "WBD",
            "ARNC", "HWM",
        ):
            self.assertNotIn(f'"{ticker}"', source)
            self.assertNotIn(f"'{ticker}'", source)
            self.assertNotIn(f"'{ticker}'", sql)
        for forbidden in ("ProviderRegistry", "ProviderRouter", "SecurityMaster", "RelationalEngine"):
            self.assertNotIn(f"class {forbidden}", source)


if __name__ == "__main__":
    unittest.main()
