"""Pure projection from native EdgarTools objects to frozen P5 filing features."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from edgar.company_reports import CurrentReport, SixK

from aq_hybrid_fundamentals import effective_session

from .contract import (
    EDGARTOOLS_RUNTIME_IDENTITY,
    FEATURE_IDS,
    FilingFeatureObservationV1,
)

_NEW_YORK = ZoneInfo("America/New_York")
_EVENT_FORMS = frozenset({"8-K", "8-K/A", "6-K", "6-K/A"})


def _native_type(value: object | None) -> str | None:
    if value is None:
        return None
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _accession(filing: object) -> str:
    value = getattr(filing, "accession_no", None)
    if value is None:
        value = getattr(filing, "accession_number", None)
    if value is None:
        raise ValueError("native filing lacks an accession")
    return str(value)


def _cik(filing: object) -> str:
    value = str(getattr(filing, "cik", ""))
    if not value.isdigit() or len(value) > 10:
        raise ValueError("native filing lacks a valid CIK")
    return value.zfill(10)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("SEC acceptance datetime must be timezone-aware")
    return value.astimezone(timezone.utc)


def _report_period(value: date | str | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _record(
    *,
    feature_id: str,
    accession: str,
    cik: str,
    form: str,
    acceptance: datetime,
    first_session: date,
    native_type: str | None,
    value: int | None,
    missingness: str | None,
    source_available: bool,
) -> FilingFeatureObservationV1:
    return FilingFeatureObservationV1.admit(
        schema_version="FilingFeatureObservationV1",
        feature_id=feature_id,
        source_accession=accession,
        cik=cik,
        form=form,
        sec_acceptance_datetime=acceptance,
        first_available_xnys_session=first_session,
        native_edgartools_object_type=native_type,
        exact_scalar_value=value,
        missingness_status=missingness,
        amendment_status="AMENDMENT" if form.endswith("/A") else "ORIGINAL",
        source_availability_status=(
            "AVAILABLE" if source_available else "SOURCE_UNAVAILABLE"
        ),
        edgartools_runtime_identity=EDGARTOOLS_RUNTIME_IDENTITY,
    )


def materialize_selected_filing_features(
    filing: object,
    *,
    sec_acceptance_datetime: datetime,
    report_period_end: date | str | None,
    native_report: CurrentReport | SixK | None,
    calendar: Any,
    source_available: bool = True,
) -> tuple[FilingFeatureObservationV1, ...]:
    """Materialize exactly the five frozen feature IDs without I/O or parsing."""

    accession = _accession(filing)
    cik = _cik(filing)
    form = str(getattr(filing, "form", "")).strip()
    if not form:
        raise ValueError("native filing lacks an exact form")
    acceptance = _utc(sec_acceptance_datetime)
    first_session = effective_session(acceptance, calendar).date()
    filing_type = _native_type(filing)

    if not source_available:
        return tuple(
            _record(
                feature_id=feature_id,
                accession=accession,
                cik=cik,
                form=form,
                acceptance=acceptance,
                first_session=first_session,
                native_type=None,
                value=None,
                missingness="SOURCE_UNAVAILABLE",
                source_available=False,
            )
            for feature_id in FEATURE_IDS
        )

    period = _report_period(report_period_end)
    lag: int | None = None
    lag_missingness: str | None = None
    if period is None:
        lag_missingness = "REQUIRED_METADATA_MISSING"
    else:
        lag = (acceptance.astimezone(_NEW_YORK).date() - period).days
        if lag < 0:
            lag = None
            lag_missingness = "INVALID_VALUE"

    local_acceptance_date = acceptance.astimezone(_NEW_YORK).date()
    after_close: int | None = None
    after_close_missingness: str | None = None
    if not calendar.is_session(local_acceptance_date):
        after_close_missingness = "NOT_APPLICABLE_SESSION_DATE"
    else:
        close = pd.Timestamp(calendar.session_close(local_acceptance_date))
        after_close = int(pd.Timestamp(acceptance) > close)

    observations = [
        _record(
            feature_id="p5_filing_lag_days_v1",
            accession=accession,
            cik=cik,
            form=form,
            acceptance=acceptance,
            first_session=first_session,
            native_type=filing_type,
            value=lag,
            missingness=lag_missingness,
            source_available=True,
        ),
        _record(
            feature_id="p5_accepted_after_market_close_v1",
            accession=accession,
            cik=cik,
            form=form,
            acceptance=acceptance,
            first_session=first_session,
            native_type=filing_type,
            value=after_close,
            missingness=after_close_missingness,
            source_available=True,
        ),
        _record(
            feature_id="p5_is_amendment_v1",
            accession=accession,
            cik=cik,
            form=form,
            acceptance=acceptance,
            first_session=first_session,
            native_type=filing_type,
            value=int(form.endswith("/A")),
            missingness=None,
            source_available=True,
        ),
    ]

    native_type = _native_type(native_report)
    press_value: int | None = None
    press_missingness: str | None = None
    exhibit_value: int | None = None
    exhibit_missingness: str | None = None
    if form not in _EVENT_FORMS:
        press_missingness = exhibit_missingness = "NOT_APPLICABLE_FORM"
    elif (form.startswith("8-K") and not isinstance(native_report, CurrentReport)) or (
        form.startswith("6-K") and not isinstance(native_report, SixK)
    ):
        native_type = None
        press_missingness = exhibit_missingness = "NATIVE_OBJECT_UNAVAILABLE"
    else:
        assert native_report is not None
        press_value = int(bool(native_report.press_releases))
        exhibits = (
            native_report.get_exhibits()
            if isinstance(native_report, CurrentReport)
            else native_report.exhibits
        )
        exhibit_value = len(exhibits)
        if press_value == 0:
            press_missingness = "VALIDATED_ABSENCE"
        if exhibit_value == 0:
            exhibit_missingness = "VALIDATED_ABSENCE"

    observations.extend(
        [
            _record(
                feature_id="p5_press_release_exhibit_present_v1",
                accession=accession,
                cik=cik,
                form=form,
                acceptance=acceptance,
                first_session=first_session,
                native_type=native_type,
                value=press_value,
                missingness=press_missingness,
                source_available=True,
            ),
            _record(
                feature_id="p5_authorized_exhibit_count_v1",
                accession=accession,
                cik=cik,
                form=form,
                acceptance=acceptance,
                first_session=first_session,
                native_type=native_type,
                value=exhibit_value,
                missingness=exhibit_missingness,
                source_available=True,
            ),
        ]
    )
    return tuple(observations)


__all__ = ["materialize_selected_filing_features"]
