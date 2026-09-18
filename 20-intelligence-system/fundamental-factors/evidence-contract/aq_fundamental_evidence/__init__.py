"""Immutable PIT admission contract for one accession-bound SEC numeric fact."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal

import rfc8785
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Cik = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}$")]
Accession = Annotated[
    str, StringConstraints(pattern=r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")
]
Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Sha256Identity = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]

SCHEMA_VERSION = "FundamentalEvidenceV1"
RFC8785_IMPLEMENTATION = "rfc8785==0.1.4"
VALUE_CANONICALIZATION_POLICY = "EXACT_CANONICAL_DECIMAL_STRING_V1"


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


def _require_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{field_name} must use UTC")
    return value


def canonical_decimal_value(value: str) -> str:
    """Return the exact V1 decimal spelling, rejecting rounding and exponents."""

    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("fact value must be an exact decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError("fact value must be finite")
    canonical = format(decimal_value, "f")
    if "." in canonical:
        canonical = canonical.rstrip("0").rstrip(".")
    if canonical in {"-0", ""}:
        canonical = "0"
    if value != canonical:
        raise ValueError(
            "fact value is not canonical; exponents, redundant zeros, and -0 are prohibited"
        )
    return canonical


class EntityIdentityV1(_FrozenModel):
    cik: Cik
    issuer_name: NonEmptyString | None = None


class FilingIdentityV1(_FrozenModel):
    accession: Accession
    form: NonEmptyString
    filing_date: date
    report_period_end: date
    acceptance_datetime: datetime
    amendment_status: Literal["ORIGINAL", "AMENDMENT"] | None = None
    filing_vintage_role: NonEmptyString | None = None

    @field_validator("acceptance_datetime")
    @classmethod
    def validate_acceptance_datetime(cls, value: datetime) -> datetime:
        return _require_utc(value, "acceptance_datetime")


class AvailabilityIdentityV1(_FrozenModel):
    first_available_at: datetime

    @field_validator("first_available_at")
    @classmethod
    def validate_first_available_at(cls, value: datetime) -> datetime:
        return _require_utc(value, "first_available_at")


class SourceIdentityV1(_FrozenModel):
    authoritative_source: Literal["SEC_EDGAR"]
    source_document_identity: NonEmptyString
    source_document_url: NonEmptyString | None = None
    source_document_sha256: Sha256Hex


class FundamentalFactV1(_FrozenModel):
    taxonomy_namespace: NonEmptyString
    concept: NonEmptyString
    value: NonEmptyString
    unit: NonEmptyString
    currency: NonEmptyString | None = None
    period_start: date | None = None
    period_end: date | None = None
    instant: date | None = None
    context_identity: NonEmptyString | None = None
    dimensions: dict[NonEmptyString, NonEmptyString] | None = None
    statement_classification: NonEmptyString | None = None

    @field_validator("value")
    @classmethod
    def validate_canonical_value(cls, value: str) -> str:
        return canonical_decimal_value(value)

    @model_validator(mode="after")
    def validate_period_and_dimensions(self) -> "FundamentalFactV1":
        is_instant = self.instant is not None
        is_duration = self.period_start is not None or self.period_end is not None
        if is_instant == is_duration:
            raise ValueError("fact requires exactly one instant or one duration period")
        if is_duration:
            if self.period_start is None or self.period_end is None:
                raise ValueError("duration fact requires period_start and period_end")
            if self.period_end < self.period_start:
                raise ValueError("fact duration period is reversed")
        if self.dimensions is not None and not self.dimensions:
            raise ValueError("dimensions must be null or a non-empty mapping")
        return self


class UpstreamIdentityV1(_FrozenModel):
    parser_provider: Literal["EDGARTOOLS"]
    edgartools_version: NonEmptyString
    upstream_identity: NonEmptyString


class FundamentalEvidenceProjectionV1(_FrozenModel):
    """All authoritative fields participating in the immutable identity."""

    schema_version: Literal["FundamentalEvidenceV1"]
    entity: EntityIdentityV1
    filing: FilingIdentityV1
    availability: AvailabilityIdentityV1
    source: SourceIdentityV1
    fact: FundamentalFactV1
    upstream: UpstreamIdentityV1

    @model_validator(mode="after")
    def validate_pit_boundary(self) -> "FundamentalEvidenceProjectionV1":
        if self.availability.first_available_at != self.filing.acceptance_datetime:
            raise ValueError(
                "first_available_at must equal the SEC acceptance_datetime"
            )
        return self


def evidence_id_for(fields: dict[str, object] | FundamentalEvidenceProjectionV1) -> str:
    """Compute RFC 8785 + SHA-256 over every validated authoritative non-ID field."""

    projection = (
        fields
        if isinstance(fields, FundamentalEvidenceProjectionV1)
        else FundamentalEvidenceProjectionV1.model_validate(fields)
    )
    canonical = rfc8785.dumps(projection.model_dump(mode="json"))
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


class FundamentalEvidenceV1(FundamentalEvidenceProjectionV1):
    """One numeric XBRL fact from one filing vintage and one availability time."""

    evidence_id: Sha256Identity

    @model_validator(mode="after")
    def validate_evidence_identity(self) -> "FundamentalEvidenceV1":
        projection = FundamentalEvidenceProjectionV1.model_validate(
            self.model_dump(mode="python", exclude={"evidence_id"})
        )
        expected = evidence_id_for(projection)
        if self.evidence_id != expected:
            raise ValueError("evidence_id does not match RFC 8785 identity")
        return self

    @classmethod
    def admit(cls, **authoritative_fields: object) -> "FundamentalEvidenceV1":
        """Validate authoritative fields and return the admitted immutable record."""

        projection = FundamentalEvidenceProjectionV1.model_validate(authoritative_fields)
        return cls(
            **projection.model_dump(mode="python"),
            evidence_id=evidence_id_for(projection),
        )


__all__ = [
    "FundamentalEvidenceV1",
    "FundamentalEvidenceProjectionV1",
    "SCHEMA_VERSION",
    "RFC8785_IMPLEMENTATION",
    "VALUE_CANONICALIZATION_POLICY",
    "canonical_decimal_value",
    "evidence_id_for",
]
