"""Pure projection from already-parsed EdgarTools objects into the AQ contract."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from . import FundamentalEvidenceV1, canonical_decimal_value


def _required_attr(value: object, name: str) -> object:
    result = getattr(value, name, None)
    if result is None or str(result).strip() == "":
        raise ValueError(f"EdgarTools filing is missing {name}")
    return result


def _required_fact(fact: Mapping[str, Any], name: str) -> object:
    result = fact.get(name)
    if result is None or str(result).strip() == "":
        raise ValueError(f"EdgarTools fact is missing {name}")
    return result


def _iso_date(value: object, name: str) -> str:
    if isinstance(value, datetime):
        raise ValueError(f"{name} must be a date, not a datetime")
    if isinstance(value, date):
        return value.isoformat()
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError as exc:
        raise ValueError(f"{name} is not an ISO date") from exc


def _exact_value(value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("EdgarTools numeric fact value must avoid binary float")
    return canonical_decimal_value(str(value))


def _dimensions(fact: Mapping[str, Any]) -> dict[str, str] | None:
    dimensions: dict[str, str] = {}
    for key, value in fact.items():
        if not key.startswith("dim_") or value is None or str(value).strip() == "":
            continue
        raw_name = key.removeprefix("dim_")
        if "_" not in raw_name:
            raise ValueError("EdgarTools dimension key lacks namespace boundary")
        prefix, local_name = raw_name.split("_", 1)
        dimensions[f"{prefix}:{local_name}"] = str(value)
    dimension = fact.get("dimension")
    member = fact.get("member")
    if dimension is not None or member is not None:
        if not dimension or not member:
            raise ValueError("EdgarTools dimension/member pair is incomplete")
        dimensions[str(dimension)] = str(member)
    return dict(sorted(dimensions.items())) or None


def materialize_edgartools_fact(
    filing: object,
    fact: Mapping[str, Any],
    *,
    acceptance_datetime: datetime,
    report_period_end: date | str,
    source_document_sha256: str,
    edgartools_version: str,
    upstream_identity: str,
    source_document_identity: str | None = None,
    source_document_url: str | None = None,
) -> FundamentalEvidenceV1:
    """Admit one already-parsed accession-bound fact; performs no I/O or parsing."""

    accession = str(_required_attr(filing, "accession_no"))
    form = str(_required_attr(filing, "form"))
    concept = str(_required_fact(fact, "concept"))
    if ":" not in concept:
        raise ValueError("XBRL concept must retain its taxonomy namespace")
    taxonomy_namespace, concept_name = concept.split(":", 1)

    period_type = str(_required_fact(fact, "period_type"))
    period_start: str | None = None
    period_end: str | None = None
    instant: str | None = None
    if period_type == "duration":
        period_start = _iso_date(_required_fact(fact, "period_start"), "period_start")
        period_end = _iso_date(_required_fact(fact, "period_end"), "period_end")
    elif period_type == "instant":
        instant = _iso_date(_required_fact(fact, "period_instant"), "period_instant")
    else:
        raise ValueError("unsupported EdgarTools fact period_type")

    cik = str(_required_attr(filing, "cik")).zfill(10)
    issuer_name = str(_required_attr(filing, "company"))
    filing_date = _iso_date(_required_attr(filing, "filing_date"), "filing_date")
    source_identity = source_document_identity or f"SEC_FULL_SUBMISSION:{accession}"
    source_url = source_document_url or str(_required_attr(filing, "text_url"))
    is_amendment = form.endswith("/A")

    return FundamentalEvidenceV1.admit(
        schema_version="FundamentalEvidenceV1",
        entity={"cik": cik, "issuer_name": issuer_name},
        filing={
            "accession": accession,
            "form": form,
            "filing_date": filing_date,
            "report_period_end": _iso_date(report_period_end, "report_period_end"),
            "acceptance_datetime": acceptance_datetime,
            "amendment_status": "AMENDMENT" if is_amendment else "ORIGINAL",
            "filing_vintage_role": "AMENDED_FILING" if is_amendment else "ORIGINAL_FILING",
        },
        availability={"first_available_at": acceptance_datetime},
        source={
            "authoritative_source": "SEC_EDGAR",
            "source_document_identity": source_identity,
            "source_document_url": source_url,
            "source_document_sha256": source_document_sha256,
        },
        fact={
            "taxonomy_namespace": taxonomy_namespace,
            "concept": concept_name,
            "value": _exact_value(_required_fact(fact, "value")),
            "unit": str(_required_fact(fact, "unit_ref")),
            "currency": str(fact["currency"]) if fact.get("currency") else None,
            "period_start": period_start,
            "period_end": period_end,
            "instant": instant,
            "context_identity": (
                str(fact["context_ref"]) if fact.get("context_ref") else None
            ),
            "dimensions": _dimensions(fact),
            "statement_classification": (
                str(fact["statement_type"]) if fact.get("statement_type") else None
            ),
        },
        upstream={
            "parser_provider": "EDGARTOOLS",
            "edgartools_version": edgartools_version,
            "upstream_identity": upstream_identity,
        },
    )


def materialize_bulk_entityfact(
    fact: object,
    *,
    cik: str,
    issuer_name: str,
    canonical_form: str,
    canonical_filing_date: str,
    canonical_report_date: str | None,
    acceptance_datetime: datetime,
    source_member: str,
    source_member_sha256: str,
    source_zip_sha256: str,
    edgartools_version: str = "5.58.0",
) -> FundamentalEvidenceV1:
    """Project one native EntityFacts observation into the existing PIT contract.

    Submissions supplies exact filing metadata. The CompanyFacts member supplies
    the raw fact and its immutable source hash; no network or ticker lookup runs.
    """

    accession = str(_required_attr(fact, "accession"))
    concept = str(_required_attr(fact, "concept"))
    if ":" not in concept:
        raise ValueError("native EntityFacts concept lacks taxonomy namespace")
    namespace, tag = concept.split(":", 1)
    period_type = str(_required_attr(fact, "period_type"))
    period_end = _iso_date(_required_attr(fact, "period_end"), "period_end")
    period_start = (
        _iso_date(_required_attr(fact, "period_start"), "period_start")
        if period_type == "duration" else None
    )
    if period_type not in {"instant", "duration"}:
        raise ValueError("unsupported native EntityFacts period type")
    report_date = canonical_report_date or period_end
    dimensions = getattr(fact, "dimensions", None) or None
    if dimensions is not None and not isinstance(dimensions, dict):
        raise ValueError("native EntityFacts dimensions are not a mapping")
    unit = str(_required_attr(fact, "unit"))
    value = _exact_value(_required_attr(fact, "value"))
    return FundamentalEvidenceV1.admit(
        schema_version="FundamentalEvidenceV1",
        entity={"cik": cik, "issuer_name": issuer_name or None},
        filing={
            "accession": accession,
            "form": canonical_form,
            "filing_date": canonical_filing_date,
            "report_period_end": report_date,
            "acceptance_datetime": acceptance_datetime,
            "amendment_status": "AMENDMENT" if canonical_form.endswith("/A") else "ORIGINAL",
            "filing_vintage_role": "AMENDED_FILING" if canonical_form.endswith("/A") else "ORIGINAL_FILING",
        },
        availability={"first_available_at": acceptance_datetime},
        source={
            "authoritative_source": "SEC_EDGAR",
            "source_document_identity": f"SEC_COMPANYFACTS_BULK:{source_zip_sha256}:{source_member}",
            "source_document_url": (
                "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip#"
                + source_member
            ),
            "source_document_sha256": source_member_sha256,
        },
        fact={
            "taxonomy_namespace": namespace,
            "concept": tag,
            "value": value,
            "unit": unit,
            "currency": unit if unit in {"USD", "EUR", "GBP", "CAD", "JPY"} else None,
            "period_start": period_start,
            "period_end": period_end if period_type == "duration" else None,
            "instant": period_end if period_type == "instant" else None,
            "context_identity": getattr(fact, "frame", None),
            "dimensions": dimensions,
            "statement_classification": None,
        },
        upstream={
            "parser_provider": "EDGARTOOLS",
            "edgartools_version": edgartools_version,
            "upstream_identity": "EDGARTOOLS_5_58_ENTITYFACTS_PARSER",
        },
    )


__all__ = ["materialize_edgartools_fact", "materialize_bulk_entityfact"]
