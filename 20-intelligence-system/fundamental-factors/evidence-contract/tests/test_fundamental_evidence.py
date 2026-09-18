from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from pydantic import ValidationError

CONTRACT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONTRACT_ROOT))

from aq_fundamental_evidence import (  # noqa: E402
    FundamentalEvidenceV1,
    VALUE_CANONICALIZATION_POLICY,
    evidence_id_for,
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"


class FundamentalEvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(CONTRACT_ROOT / "fundamental-evidence-v1.schema.json")
        Draft202012Validator.check_schema(cls.schema)
        cls.schema_validator = Draft202012Validator(cls.schema)
        cls.apple_2021 = load_json(FIXTURE_ROOT / "apple-2021-10k-net-sales.json")
        cls.apple_2009 = load_json(FIXTURE_ROOT / "apple-2009-10k-sales.json")
        cls.apple_2009_amendment = load_json(
            FIXTURE_ROOT / "apple-2009-10ka-sales.json"
        )

    def assert_rejected(self, payload: dict[str, object]) -> None:
        with self.assertRaises(ValidationError):
            FundamentalEvidenceV1.model_validate(payload)

    def test_schema_and_three_historical_safe_fixtures_pass(self) -> None:
        for fixture in (self.apple_2021, self.apple_2009, self.apple_2009_amendment):
            with self.subTest(accession=fixture["filing"]["accession"]):
                self.schema_validator.validate(fixture)
                record = FundamentalEvidenceV1.model_validate(fixture)
                self.assertEqual(
                    record.evidence_id,
                    evidence_id_for(record.model_dump(exclude={"evidence_id"})),
                )

    def test_exact_top_level_contract(self) -> None:
        expected = {
            "schema_version",
            "evidence_id",
            "entity",
            "filing",
            "availability",
            "source",
            "fact",
            "upstream",
        }
        self.assertEqual(expected, set(self.schema["required"]))
        self.assertEqual(8, len(self.schema["required"]))
        self.assertFalse(self.schema["additionalProperties"])

    def test_materialized_schema_matches_pydantic_model(self) -> None:
        generated = FundamentalEvidenceV1.model_json_schema()
        generated = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://qhongboq.github.io/AUTONOMOUS_QUANT/fundamental-evidence-v1.schema.json",
            **generated,
        }
        self.assertEqual(self.schema, generated)

    def test_same_semantics_produce_same_id(self) -> None:
        first = FundamentalEvidenceV1.model_validate(self.apple_2021)
        second = FundamentalEvidenceV1.model_validate(copy.deepcopy(self.apple_2021))
        self.assertEqual(first.evidence_id, second.evidence_id)

    def test_missing_accession_rejected(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        del payload["filing"]["accession"]
        self.assert_rejected(payload)

    def test_missing_acceptance_datetime_rejected(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        del payload["filing"]["acceptance_datetime"]
        self.assert_rejected(payload)

    def test_first_available_at_mismatch_rejected(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        payload["availability"]["first_available_at"] = "2021-10-29T00:00:00Z"
        self.assert_rejected(payload)

    def test_report_period_end_cannot_substitute_for_availability(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        payload["availability"]["first_available_at"] = "2021-09-25T00:00:00Z"
        self.assert_rejected(payload)

    def test_missing_source_hash_rejected(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        del payload["source"]["source_document_sha256"]
        self.assert_rejected(payload)

    def test_ticker_only_identity_rejected(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        payload["entity"] = {"ticker": "AAPL"}
        self.assert_rejected(payload)

    def test_original_and_amendment_are_distinct_vintages(self) -> None:
        original = FundamentalEvidenceV1.model_validate(self.apple_2009)
        amendment = FundamentalEvidenceV1.model_validate(self.apple_2009_amendment)
        self.assertEqual(original.filing.report_period_end, amendment.filing.report_period_end)
        self.assertNotEqual(original.filing.accession, amendment.filing.accession)
        self.assertNotEqual(original.evidence_id, amendment.evidence_id)
        self.assertGreater(
            amendment.availability.first_available_at,
            original.availability.first_available_at,
        )

    def test_amendment_cannot_overwrite_original_identity(self) -> None:
        payload = copy.deepcopy(self.apple_2009_amendment)
        payload["evidence_id"] = self.apple_2009["evidence_id"]
        self.assert_rejected(payload)

    def test_different_accession_cannot_reuse_evidence_id(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        payload["filing"]["accession"] = "0000320193-21-000106"
        self.assert_rejected(payload)

    def test_different_acceptance_time_cannot_reuse_evidence_id(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        changed = "2021-10-28T22:04:29Z"
        payload["filing"]["acceptance_datetime"] = changed
        payload["availability"]["first_available_at"] = changed
        self.assert_rejected(payload)

    def test_different_value_cannot_reuse_evidence_id(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        payload["fact"]["value"] = "365817000001"
        self.assert_rejected(payload)

    def test_dimensions_participate_in_identity(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        payload["fact"]["dimensions"] = {
            "us-gaap:StatementBusinessSegmentsAxis": "aapl:AmericasSegmentMember"
        }
        self.assert_rejected(payload)
        projection = {key: value for key, value in payload.items() if key != "evidence_id"}
        payload["evidence_id"] = evidence_id_for(projection)
        changed = FundamentalEvidenceV1.model_validate(payload)
        base = FundamentalEvidenceV1.model_validate(self.apple_2021)
        self.assertNotEqual(base.evidence_id, changed.evidence_id)

    def test_openbb_only_value_is_rejected(self) -> None:
        openbb_only = {
            "provider": "openbb_sec",
            "symbol": "AAPL",
            "period_ending": "2021-09-25",
            "revenue": "365817000000",
        }
        self.assert_rejected(openbb_only)

    def test_noncanonical_values_are_rejected_without_rounding(self) -> None:
        self.assertEqual("EXACT_CANONICAL_DECIMAL_STRING_V1", VALUE_CANONICALIZATION_POLICY)
        for value in ("1.0", "01", "1e3", "-0", "NaN", "Infinity"):
            payload = copy.deepcopy(self.apple_2021)
            payload["fact"]["value"] = value
            with self.subTest(value=value):
                self.assert_rejected(payload)

    def test_extra_fields_fail_closed(self) -> None:
        payload = copy.deepcopy(self.apple_2021)
        payload["ticker"] = "AAPL"
        self.assert_rejected(payload)


if __name__ == "__main__":
    unittest.main()
