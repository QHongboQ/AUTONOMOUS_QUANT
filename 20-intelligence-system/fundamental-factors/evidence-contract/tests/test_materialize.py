from __future__ import annotations

import ast
import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

CONTRACT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONTRACT_ROOT))

from aq_fundamental_evidence.materialize import materialize_edgartools_fact  # noqa: E402


class FakeFiling:
    cik = 320193
    company = "APPLE INC"
    form = "10-K"
    filing_date = "2021-10-29"
    accession_no = "0000320193-21-000105"
    text_url = "https://www.sec.gov/example.txt"


BASE_FACT = {
    "concept": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    "value": "365817000000",
    "unit_ref": "usd",
    "currency": "USD",
    "period_type": "duration",
    "period_start": "2020-09-27",
    "period_end": "2021-09-25",
    "context_ref": "context-annual",
    "statement_type": "IncomeStatement",
}


def materialize(fact: dict[str, object] | None = None):
    return materialize_edgartools_fact(
        FakeFiling(),
        BASE_FACT if fact is None else fact,
        acceptance_datetime=datetime(2021, 10, 28, 22, 4, 28, tzinfo=timezone.utc),
        report_period_end="2021-09-25",
        source_document_sha256="f" * 64,
        edgartools_version="5.58.0",
        upstream_identity="PYPI_DISTRIBUTION:edgartools==5.58.0",
    )


class ThinMaterializerTests(unittest.TestCase):
    def test_duration_fact_projects_into_contract(self) -> None:
        record = materialize()
        self.assertEqual("0000320193-21-000105", record.filing.accession)
        self.assertEqual(record.filing.acceptance_datetime, record.availability.first_available_at)
        self.assertEqual("365817000000", record.fact.value)
        self.assertEqual("SEC_EDGAR", record.source.authoritative_source)
        self.assertEqual("EDGARTOOLS", record.upstream.parser_provider)

    def test_instant_fact_projects_into_contract(self) -> None:
        fact = copy.deepcopy(BASE_FACT)
        fact.update(
            {
                "concept": "us-gaap:Assets",
                "value": "351002000000",
                "period_type": "instant",
                "period_instant": "2021-09-25",
            }
        )
        fact.pop("period_start")
        fact.pop("period_end")
        record = materialize(fact)
        self.assertEqual("2021-09-25", record.fact.instant.isoformat())
        self.assertIsNone(record.fact.period_start)

    def test_dimensions_are_preserved_and_change_identity(self) -> None:
        base = materialize()
        fact = copy.deepcopy(BASE_FACT)
        fact.update(
            {
                "value": "297392000000",
                "dim_srt_ProductOrServiceAxis": "us-gaap:ProductMember",
                "dimension": "srt:ProductOrServiceAxis",
                "member": "us-gaap:ProductMember",
            }
        )
        dimensioned = materialize(fact)
        self.assertEqual(
            {"srt:ProductOrServiceAxis": "us-gaap:ProductMember"},
            dimensioned.fact.dimensions,
        )
        self.assertNotEqual(base.evidence_id, dimensioned.evidence_id)

    def test_binary_float_value_fails_closed(self) -> None:
        fact = copy.deepcopy(BASE_FACT)
        fact["value"] = 365817000000.0
        with self.assertRaises(ValueError):
            materialize(fact)

    def test_missing_accession_fails_closed(self) -> None:
        filing = FakeFiling()
        filing.accession_no = ""
        with self.assertRaises(ValueError):
            materialize_edgartools_fact(
                filing,
                BASE_FACT,
                acceptance_datetime=datetime(
                    2021, 10, 28, 22, 4, 28, tzinfo=timezone.utc
                ),
                report_period_end="2021-09-25",
                source_document_sha256="f" * 64,
                edgartools_version="5.58.0",
                upstream_identity="PYPI_DISTRIBUTION:edgartools==5.58.0",
            )

    def test_materializer_has_no_network_parser_or_openbb_imports(self) -> None:
        source = (CONTRACT_ROOT / "aq_fundamental_evidence" / "materialize.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0
        )
        self.assertFalse(
            imports.intersection(
                {"edgar", "openbb", "requests", "httpx", "urllib", "pandas", "sqlalchemy"}
            )
        )


if __name__ == "__main__":
    unittest.main()
