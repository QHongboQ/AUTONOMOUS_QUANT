"""Bounded tests for the frozen SEC-bulk/EdgarTools transformation seam."""

from __future__ import annotations

import io
import json
import zipfile
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from aq_edgartools_full_build.bulk import (
    SPEC_PATH,
    _acceptance,
    _native_tags,
    _period,
    _submission_index,
)
from aq_fundamental_evidence.materialize import materialize_bulk_entityfact
from aq_hybrid_fundamentals import FROZEN_STANDARD_CONCEPTS


def test_exact_ten_feature_authority() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    assert tuple(spec["structured_fundamentals"]) == FROZEN_STANDARD_CONCEPTS
    assert len(FROZEN_STANDARD_CONCEPTS) == 10
    assert "ShortTermDebt" not in FROZEN_STANDARD_CONCEPTS
    assert "LongTermDebt" in FROZEN_STANDARD_CONCEPTS
    assert len(spec["known_exact_authority_exclusions"]) == 5
    period = spec["evaluation_period_authority"]
    assert period["flow_features"] == [
        "Revenue", "NetIncome", "NetCashFromOperatingActivities",
    ]
    assert period["flow_period_class"] == "DURATION_ANNUAL"
    assert period["stock_period_class"] == "INSTANT"
    assert period["fallback"] == "NONE"
    assert period["flow_derivation_count"] == 0


def test_edgartools_owns_native_concept_synonyms() -> None:
    native = _native_tags()
    assert native["Assets"][0] == "Assets"
    assert native["LongTermDebt"][0] == "LongTermDebt"
    assert not any(concept == "ShortTermDebt" for concept, _ in native.values())


def test_exact_submissions_identity_and_no_filed_date_substitution() -> None:
    recent = {
        "accessionNumber": ["0000000001-20-000001", "0000000001-20-000002"],
        "form": ["10-K", "10-K/A"],
        "acceptanceDateTime": ["2020-02-01T16:04:00Z", ""],
        "filingDate": ["2020-02-01", "2020-02-02"],
        "reportDate": ["2019-12-31", "2019-12-31"],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("CIK0000000001.json", json.dumps({"filings": {"recent": recent}}))
    buffer.seek(0)
    with zipfile.ZipFile(buffer) as archive:
        rows = _submission_index(archive, set(archive.namelist()), "0000000001")
    assert rows["0000000001-20-000001"]["form"] == "10-K"
    assert rows["0000000001-20-000002"]["form"] == "10-K/A"
    assert _acceptance(rows["0000000001-20-000001"]["acceptance_datetime"]) is not None
    assert _acceptance(rows["0000000001-20-000002"]["acceptance_datetime"]) is None
    assert _acceptance("2020-02-02") is None


def test_native_period_classification_and_independent_amendment_vintage() -> None:
    annual = SimpleNamespace(period_type="duration", period_start=date(2019, 1, 1),
                             period_end=date(2019, 12, 31))
    instant = SimpleNamespace(period_type="instant")
    assert _period(annual) == "DURATION_ANNUAL"
    assert _period(instant) == "INSTANT"
    fact = SimpleNamespace(
        accession="0000000001-20-000002", concept="us-gaap:Assets", period_type="instant",
        period_end=date(2019, 12, 31), period_start=None, dimensions=None,
        unit="USD", value=Decimal("123.5"), frame=None,
    )
    evidence = materialize_bulk_entityfact(
        fact, cik="0000000001", issuer_name="Test Issuer", canonical_form="10-K/A",
        canonical_filing_date="2020-02-02", canonical_report_date="2019-12-31",
        acceptance_datetime=datetime(2020, 2, 2, 16, 4, tzinfo=timezone.utc),
        source_member="CIK0000000001.json", source_member_sha256="a" * 64,
        source_zip_sha256="b" * 64,
    )
    assert evidence.filing.form == "10-K/A"
    assert evidence.filing.amendment_status == "AMENDMENT"
    assert evidence.fact.value == "123.5"
    assert evidence.fact.concept == "Assets"
    assert evidence.source.source_document_sha256 == "a" * 64
