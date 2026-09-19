from __future__ import annotations

import ast
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ADAPTER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
CIK_ROOT = REPO_ROOT / "10-data-system" / "fundamentals" / "identity-binding"
EVIDENCE_ROOT = (
    REPO_ROOT
    / "20-intelligence-system"
    / "fundamental-factors"
    / "evidence-contract"
)
for path in (ADAPTER_ROOT, CIK_ROOT, EVIDENCE_ROOT):
    sys.path.insert(0, str(path))

from aq_fundamental_evidence import FundamentalEvidenceV1  # noqa: E402
from aq_valuein_adapter import (  # noqa: E402
    FROZEN_VALUEIN_METRIC_MAP,
    admit_exact_valuein_binding,
    classify_valuein_identity,
    map_valuein_metric,
    materialize_valuein_fact,
    prefer_exact_valuein_or_edgartools,
)


def episode(ticker: str, start: str, end: str, marker: str) -> dict[str, object]:
    return {
        "episode_id": "P1EP-" + marker * 64,
        "normalized_ticker": ticker,
        "valid_from": start,
        "valid_to": end,
        "provenance_hash": marker * 64,
    }


def security(
    ticker: str,
    cik: str,
    start: str,
    end: str | None,
    marker: str = "1",
) -> dict[str, object]:
    return {
        "security_id": f"security-{marker}",
        "entity_id": cik,
        "cik": cik,
        "symbol": ticker,
        "valid_from": start,
        "valid_to": end,
    }


def membership(cik: str, start: str, end: str | None) -> dict[str, object]:
    return {
        "cik": cik,
        "effective_date": start,
        "removal_date": end,
        "source": "historical_seed",
    }


CONTROL_CASES = (
    (
        "AAPL",
        episode("AAPL", "2010-01-04", "2025-01-01", "1"),
        [security("AAPL", "0000320193", "1994-01-26", None)],
        "COMPATIBLE_CANDIDATE",
    ),
    (
        "CTL_TO_LUMN",
        episode("CTL", "2010-01-04", "2020-09-18", "2"),
        [],
        "NO_MATCH",
    ),
    (
        "HISTORICAL_BBBY",
        episode("BBBY", "2010-01-04", "2017-07-26", "3"),
        [],
        "NO_MATCH",
    ),
    (
        "DRE",
        episode("DRE", "2017-07-26", "2022-10-03", "4"),
        [security("DRE", "0000783280", "1994-05-12", "2022-10-04")],
        "COMPATIBLE_CANDIDATE",
    ),
    (
        "OLD_DD",
        episode("DD", "2010-01-04", "2017-09-01", "5"),
        [security("DD", "0001666700", "2016-03-01", None)],
        "PARTIAL",
    ),
    (
        "NEW_DD",
        episode("DD", "2019-06-03", "2025-01-01", "6"),
        [security("DD", "0001666700", "2016-03-01", None)],
        "COMPATIBLE_CANDIDATE",
    ),
    (
        "FB_TO_META",
        episode("FB", "2013-12-23", "2022-06-09", "7"),
        [],
        "NO_MATCH",
    ),
    (
        "OLD_CEG",
        episode("CEG", "2010-01-04", "2012-03-13", "8"),
        [],
        "NO_MATCH",
    ),
)


BASE_FILING = {
    "accession_id": "0000320193-21-000105",
    "entity_id": "0000320193",
    "form_type": "10-K",
    "filing_date": "2021-10-29",
    "report_date": "2021-09-25",
    "accepted_at": "2021-10-28T22:04:28Z",
    "is_amendment": False,
    "filing_url": "https://www.sec.gov/example.txt",
    "issuer_name": "APPLE INC",
}
BASE_FACT = {
    "accession_id": "0000320193-21-000105",
    "entity_id": "0000320193",
    "concept": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "standard_concept": "TotalRevenue",
    "value": "9007199254740993",
    "unit": "USD",
    "reporting_currency": "USD",
    "period_start": "2020-09-27",
    "period_end": "2021-09-25",
    "accepted_at": "2021-10-28T22:04:28Z",
    "statement_type": "IncomeStatement",
    "fact_id": "fact-1",
}


def valuein_evidence(
    filing: dict[str, object] | None = None,
    fact: dict[str, object] | None = None,
    source_hash: str = "f" * 64,
) -> FundamentalEvidenceV1:
    return materialize_valuein_fact(
        BASE_FILING if filing is None else filing,
        BASE_FACT if fact is None else fact,
        source_document_sha256=source_hash,
        valuein_sdk_version="5.2.0",
        upstream_identity="PYPI_DISTRIBUTION:valuein-sdk==5.2.0",
    )


def edgartools_evidence() -> FundamentalEvidenceV1:
    return FundamentalEvidenceV1.admit(
        schema_version="FundamentalEvidenceV1",
        entity={"cik": "0000320193", "issuer_name": "APPLE INC"},
        filing={
            "accession": "0000320193-21-000105",
            "form": "10-K",
            "filing_date": "2021-10-29",
            "report_period_end": "2021-09-25",
            "acceptance_datetime": datetime(
                2021, 10, 28, 22, 4, 28, tzinfo=timezone.utc
            ),
            "amendment_status": "ORIGINAL",
            "filing_vintage_role": "ORIGINAL_FILING",
        },
        availability={
            "first_available_at": datetime(
                2021, 10, 28, 22, 4, 28, tzinfo=timezone.utc
            )
        },
        source={
            "authoritative_source": "SEC_EDGAR",
            "source_document_identity": "SEC_FULL_SUBMISSION:0000320193-21-000105",
            "source_document_url": "https://www.sec.gov/example.txt",
            "source_document_sha256": "f" * 64,
        },
        fact={
            "taxonomy_namespace": "us-gaap",
            "concept": "RevenueFromContractWithCustomerExcludingAssessedTax",
            "value": "9007199254740993",
            "unit": "USD",
            "currency": "USD",
            "period_start": "2020-09-27",
            "period_end": "2021-09-25",
            "instant": None,
            "context_identity": "context-1",
            "dimensions": None,
            "statement_classification": "IncomeStatement",
        },
        upstream={
            "parser_provider": "EDGARTOOLS",
            "edgartools_version": "5.58.0",
            "upstream_identity": "PYPI_DISTRIBUTION:edgartools==5.58.0",
        },
    )


class ValueinIdentityAdapterTests(unittest.TestCase):
    def test_eight_authoritative_control_boundaries(self) -> None:
        for name, item, rows, expected in CONTROL_CASES:
            with self.subTest(name=name):
                decision = classify_valuein_identity(item, rows, [])
                self.assertEqual(expected, decision.classification)

    def test_exact_interval_admits_deterministically(self) -> None:
        item = episode("FRC", "2019-01-02", "2023-05-04", "a")
        rows = [security("FRC", "0001132979", "2019-01-02", "2023-05-04")]
        memberships = [membership("0001132979", "2019-01-02", "2023-05-04")]
        decision = classify_valuein_identity(item, rows, memberships)
        self.assertEqual("EXACT", decision.classification)
        first = admit_exact_valuein_binding(
            decision,
            authoritative_episodes=[item],
            episode=item,
            snapshot_identity="a" * 64,
        )
        second = admit_exact_valuein_binding(
            decision,
            authoritative_episodes=[item],
            episode=item,
            snapshot_identity="a" * 64,
        )
        self.assertEqual(first.binding_id, second.binding_id)
        self.assertEqual("0001132979", first.cik)

    def test_compatible_partial_ambiguous_and_no_match_never_admit(self) -> None:
        item = episode("TEST", "2020-01-01", "2021-01-01", "b")
        cases = (
            [security("TEST", "0000000001", "2019-01-01", "2022-01-01")],
            [security("TEST", "0000000001", "2020-06-01", "2022-01-01")],
            [
                security("TEST", "0000000001", "2019-01-01", "2022-01-01", "1"),
                security("TEST", "0000000002", "2019-01-01", "2022-01-01", "2"),
            ],
            [],
        )
        for rows in cases:
            decision = classify_valuein_identity(item, rows, [])
            with self.subTest(classification=decision.classification), self.assertRaises(
                ValueError
            ):
                admit_exact_valuein_binding(
                    decision,
                    authoritative_episodes=[item],
                    episode=item,
                    snapshot_identity="a" * 64,
                )

    def test_conflicting_accepted_cik_fails_closed(self) -> None:
        item = episode("REUSE", "2020-01-01", "2021-01-01", "c")
        decision = classify_valuein_identity(
            item,
            [security("REUSE", "0000000002", "2020-01-01", "2021-01-01")],
            [],
            accepted_cik="0000000001",
        )
        self.assertEqual("CONFLICT", decision.classification)

    def test_exact_identity_requires_membership_containment(self) -> None:
        item = episode("FRC", "2019-01-02", "2023-05-04", "d")
        decision = classify_valuein_identity(
            item,
            [security("FRC", "0001132979", "2019-01-02", "2023-05-04")],
            [membership("0001132979", "2020-01-01", "2023-05-04")],
        )
        with self.assertRaisesRegex(ValueError, "membership"):
            admit_exact_valuein_binding(
                decision,
                authoritative_episodes=[item],
                episode=item,
                snapshot_identity="a" * 64,
            )


class ValueinFundamentalsAdapterTests(unittest.TestCase):
    def test_frozen_metric_mapping_is_exact_and_complete(self) -> None:
        self.assertEqual(11, len(FROZEN_VALUEIN_METRIC_MAP))
        self.assertEqual("Revenue", map_valuein_metric("TotalRevenue"))
        with self.assertRaisesRegex(ValueError, "frozen 11"):
            map_valuein_metric("ConvenientNewSynonym")

    def test_provenance_complete_valuein_fact_uses_existing_contract(self) -> None:
        record = valuein_evidence()
        self.assertEqual("VALUEIN", record.upstream.parser_provider)
        self.assertEqual("5.2.0", record.upstream.valuein_sdk_version)
        self.assertEqual("9007199254740993", record.fact.value)
        self.assertEqual(record.filing.acceptance_datetime, record.availability.first_available_at)

    def test_missing_source_provenance_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "source_document_sha256"):
            valuein_evidence(source_hash="")

    def test_accepted_at_mismatch_fails_closed(self) -> None:
        fact = {**BASE_FACT, "accepted_at": "2021-10-28T22:04:29Z"}
        with self.assertRaisesRegex(ValueError, "accepted_at"):
            valuein_evidence(fact=fact)

    def test_binary_float_and_noncanonical_values_fail_closed(self) -> None:
        for value in (1.5, "1.0", "01", "1e3"):
            fact = {**BASE_FACT, "value": value}
            with self.subTest(value=value), self.assertRaises(ValueError):
                valuein_evidence(fact=fact)

    def test_amendment_is_a_distinct_vintage(self) -> None:
        original = valuein_evidence()
        filing = {
            **BASE_FILING,
            "accession_id": "0000320193-21-000106",
            "form_type": "10-K/A",
            "accepted_at": "2021-11-01T22:04:28Z",
            "is_amendment": True,
        }
        fact = {
            **BASE_FACT,
            "accession_id": "0000320193-21-000106",
            "accepted_at": "2021-11-01T22:04:28Z",
        }
        amendment = valuein_evidence(filing=filing, fact=fact, source_hash="e" * 64)
        self.assertEqual("AMENDMENT", amendment.filing.amendment_status)
        self.assertNotEqual(original.evidence_id, amendment.evidence_id)

    def test_exact_source_precedence_and_disagreement(self) -> None:
        valuein = valuein_evidence()
        edgar = edgartools_evidence()
        self.assertIs(
            valuein,
            prefer_exact_valuein_or_edgartools(
                valuein_evidence=valuein, edgartools_evidence=edgar
            ),
        )
        self.assertIs(
            edgar,
            prefer_exact_valuein_or_edgartools(
                valuein_evidence=None, edgartools_evidence=edgar
            ),
        )
        conflicting = valuein_evidence(source_hash="e" * 64)
        with self.assertRaisesRegex(ValueError, "disagree"):
            prefer_exact_valuein_or_edgartools(
                valuein_evidence=conflicting, edgartools_evidence=edgar
            )

    def test_module_contains_no_framework_or_network_client(self) -> None:
        source = (ADAPTER_ROOT / "aq_valuein_adapter" / "__init__.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        forbidden_classes = {
            "ProviderRegistry",
            "ProviderBase",
            "ProviderProtocol",
            "AdapterRegistry",
            "AdapterFactory",
            "GenericAdapter",
            "SecurityMaster",
            "IdentityResolverEngine",
            "FundamentalEngine",
        }
        self.assertFalse(
            forbidden_classes.intersection(
                node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
            )
        )
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertFalse(imported.intersection({"requests", "httpx", "valuein_sdk"}))


if __name__ == "__main__":
    unittest.main()
