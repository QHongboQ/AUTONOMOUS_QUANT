"""Immutable observation contract for the five preregistered P5 filing features."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta
from typing import Annotated, Literal

import rfc8785
from pydantic import (
    BaseModel,
    ConfigDict,
    StrictInt,
    StringConstraints,
    field_validator,
    model_validator,
)

NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Cik = Annotated[str, StringConstraints(pattern=r"^[0-9]{10}$")]
Accession = Annotated[
    str, StringConstraints(pattern=r"^[0-9]{10}-[0-9]{2}-[0-9]{6}$")
]
Sha256Identity = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]

SCHEMA_VERSION = "FilingFeatureObservationV1"
EDGARTOOLS_RUNTIME_IDENTITY = "edgartools==5.58.0"
FEATURE_IDS = (
    "p5_filing_lag_days_v1",
    "p5_accepted_after_market_close_v1",
    "p5_is_amendment_v1",
    "p5_press_release_exhibit_present_v1",
    "p5_authorized_exhibit_count_v1",
)
FeatureId = Literal[
    "p5_filing_lag_days_v1",
    "p5_accepted_after_market_close_v1",
    "p5_is_amendment_v1",
    "p5_press_release_exhibit_present_v1",
    "p5_authorized_exhibit_count_v1",
]
MissingnessStatus = Literal[
    "NOT_APPLICABLE_FORM",
    "NOT_APPLICABLE_SESSION_DATE",
    "NATIVE_OBJECT_UNAVAILABLE",
    "SOURCE_UNAVAILABLE",
    "REQUIRED_METADATA_MISSING",
    "VALIDATED_ABSENCE",
    "INVALID_VALUE",
]


class _FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


class _FilingFeatureObservationProjectionV1(_FrozenModel):
    schema_version: Literal["FilingFeatureObservationV1"]
    feature_id: FeatureId
    source_accession: Accession
    cik: Cik
    form: NonEmptyString
    sec_acceptance_datetime: datetime
    first_available_xnys_session: date
    native_edgartools_object_type: NonEmptyString | None
    exact_scalar_value: StrictInt | None
    missingness_status: MissingnessStatus | None
    amendment_status: Literal["ORIGINAL", "AMENDMENT"]
    source_availability_status: Literal["AVAILABLE", "SOURCE_UNAVAILABLE"]
    edgartools_runtime_identity: Literal["edgartools==5.58.0"]

    @field_validator("sec_acceptance_datetime")
    @classmethod
    def validate_acceptance_datetime(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("sec_acceptance_datetime must be timezone-aware")
        if value.utcoffset() != timedelta(0):
            raise ValueError("sec_acceptance_datetime must use UTC")
        return value

    @model_validator(mode="after")
    def validate_domain_semantics(self) -> "_FilingFeatureObservationProjectionV1":
        expected_amendment = "AMENDMENT" if self.form.endswith("/A") else "ORIGINAL"
        if self.amendment_status != expected_amendment:
            raise ValueError("amendment_status must follow the exact filed form")
        if self.source_availability_status == "SOURCE_UNAVAILABLE":
            if self.missingness_status != "SOURCE_UNAVAILABLE":
                raise ValueError("unavailable source requires SOURCE_UNAVAILABLE missingness")
            if self.exact_scalar_value is not None:
                raise ValueError("unavailable source cannot produce a scalar")
        elif self.missingness_status == "SOURCE_UNAVAILABLE":
            raise ValueError("available source cannot use SOURCE_UNAVAILABLE missingness")
        if self.exact_scalar_value is None and self.missingness_status is None:
            raise ValueError("a missing scalar requires explicit missingness")
        if self.exact_scalar_value is not None and self.missingness_status not in {
            None,
            "VALIDATED_ABSENCE",
        }:
            raise ValueError("a scalar cannot accompany this missingness state")
        if self.missingness_status == "VALIDATED_ABSENCE":
            if self.feature_id not in {
                "p5_press_release_exhibit_present_v1",
                "p5_authorized_exhibit_count_v1",
            } or self.exact_scalar_value != 0:
                raise ValueError("validated absence is a zero-valued exhibit observation")
            if self.native_edgartools_object_type is None:
                raise ValueError("validated absence requires a loaded native object")
        value = self.exact_scalar_value
        if value is not None:
            if self.feature_id == "p5_filing_lag_days_v1" and value < 0:
                raise ValueError("filing lag cannot be negative")
            if self.feature_id in {
                "p5_accepted_after_market_close_v1",
                "p5_is_amendment_v1",
                "p5_press_release_exhibit_present_v1",
            } and value not in {0, 1}:
                raise ValueError("binary filing feature must be zero or one")
            if self.feature_id == "p5_authorized_exhibit_count_v1" and value < 0:
                raise ValueError("authorized exhibit count cannot be negative")
            if (
                self.feature_id == "p5_is_amendment_v1"
                and value != int(self.form.endswith("/A"))
            ):
                raise ValueError("amendment scalar must follow the exact filed form")
            if self.feature_id in {
                "p5_press_release_exhibit_present_v1",
                "p5_authorized_exhibit_count_v1",
            } and self.native_edgartools_object_type is None:
                raise ValueError("an exhibit scalar requires a loaded native object")
        return self


def evidence_id_for(
    fields: dict[str, object] | _FilingFeatureObservationProjectionV1,
) -> str:
    """Return RFC 8785 + SHA-256 identity over every authoritative field."""

    projection = (
        fields
        if isinstance(fields, _FilingFeatureObservationProjectionV1)
        else _FilingFeatureObservationProjectionV1.model_validate(fields)
    )
    canonical = rfc8785.dumps(projection.model_dump(mode="json"))
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


class FilingFeatureObservationV1(_FilingFeatureObservationProjectionV1):
    """One immutable scalar or explicit missing observation for one accession."""

    evidence_id: Sha256Identity

    @model_validator(mode="after")
    def validate_evidence_identity(self) -> "FilingFeatureObservationV1":
        projection = _FilingFeatureObservationProjectionV1.model_validate(
            self.model_dump(mode="python", exclude={"evidence_id"})
        )
        if self.evidence_id != evidence_id_for(projection):
            raise ValueError("evidence_id does not match RFC 8785 identity")
        return self

    @classmethod
    def admit(cls, **authoritative_fields: object) -> "FilingFeatureObservationV1":
        projection = _FilingFeatureObservationProjectionV1.model_validate(
            authoritative_fields
        )
        return cls(
            **projection.model_dump(mode="python"),
            evidence_id=evidence_id_for(projection),
        )


__all__ = [
    "EDGARTOOLS_RUNTIME_IDENTITY",
    "FEATURE_IDS",
    "FilingFeatureObservationV1",
    "SCHEMA_VERSION",
    "evidence_id_for",
]
