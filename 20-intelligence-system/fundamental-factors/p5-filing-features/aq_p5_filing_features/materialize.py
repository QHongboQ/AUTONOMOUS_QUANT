"""Pure projection from native EdgarTools objects to frozen P5 filing features."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from collections.abc import Callable, Iterable
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


def discover_native_filing_observations(
    ciks: Iterable[str], *, filing_date: str, calendar: Any,
    company_factory: Callable[[int], object] | None = None,
) -> tuple[FilingFeatureObservationV1, ...]:
    """Use EdgarTools' native collection/object routing; tests inject a factory."""
    if company_factory is None:
        from edgar import Company
        company_factory = Company
    output: list[FilingFeatureObservationV1] = []
    for cik in sorted({str(int(value)) for value in ciks}, key=int):
        filings = company_factory(int(cik)).get_filings(
            filing_date=filing_date, amendments=True, trigger_full_load=True)
        for filing in filings:
            form = str(getattr(filing, "form", ""))
            acceptance = getattr(filing, "acceptance_datetime", None)
            if not isinstance(acceptance, datetime):
                raise ValueError("native filing lacks an exact acceptance datetime")
            output.extend(materialize_selected_filing_features(
                filing, sec_acceptance_datetime=acceptance,
                report_period_end=getattr(filing, "period_of_report", None),
                native_report=filing.obj() if form in _EVENT_FORMS else None,
                calendar=calendar))
    return tuple(output)


def project_historical_filing_features(
    observations: Iterable[FilingFeatureObservationV1], *, session_grid: pd.DataFrame,
    bindings: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Project sparse observations onto exact episode sessions, fail closed."""
    if not {"datetime", "episode_id", "cik"}.issubset(session_grid) or not {
        "episode_id", "cik", "valid_from", "valid_to"}.issubset(bindings):
        raise ValueError("session grid or binding contract is incomplete")
    grid = session_grid.copy()
    grid["datetime"] = pd.to_datetime(grid["datetime"]).dt.normalize()
    if grid.duplicated(["datetime", "episode_id"]).any():
        raise ValueError("duplicate (datetime, episode_id) in session authority")
    bind = bindings.copy()
    bind["cik"] = bind["cik"].astype(str).str.zfill(10)
    bind["valid_from"] = pd.to_datetime(bind["valid_from"]).dt.normalize()
    bind["valid_to"] = pd.to_datetime(bind["valid_to"]).dt.normalize()
    rows: list[dict[str, object]] = []
    for item in observations:
        session = pd.Timestamp(item.first_available_xnys_session)
        eligible = bind.loc[(bind["cik"] == item.cik) & (bind["valid_from"] <= session) & (bind["valid_to"] >= session)]
        if len(eligible) > 1:
            raise ValueError("filing maps to multiple date-valid episode bindings")
        if eligible.empty:
            continue
        episode_id = str(eligible.iloc[0]["episode_id"])
        session_match = grid.loc[(grid["datetime"] == session) & (grid["episode_id"] == episode_id)]
        if session_match.empty:
            continue
        if str(session_match.iloc[0]["cik"]).zfill(10) != item.cik:
            raise ValueError("cross-CIK filing projection")
        rows.append({"datetime": session, "episode_id": episode_id, "cik": item.cik,
            "feature_id": item.feature_id, "value": item.exact_scalar_value,
            "missingness_status": item.missingness_status, "source_accession": item.source_accession,
            "sec_acceptance_datetime": item.sec_acceptance_datetime,
            "first_available_xnys_session": item.first_available_xnys_session,
            "evidence_id": item.evidence_id})
    columns = ["datetime", "episode_id", "cik", "feature_id", "value", "missingness_status",
               "source_accession", "sec_acceptance_datetime", "first_available_xnys_session", "evidence_id"]
    long = pd.DataFrame(rows)
    if long.empty:
        long = pd.DataFrame(columns=columns)
    else:
        key = ["datetime", "episode_id", "feature_id"]
        order = [*key, "sec_acceptance_datetime", "source_accession"]
        ordered = long.sort_values(order)
        equal = ordered.loc[ordered.duplicated(order, keep=False)].groupby(order, dropna=False)["evidence_id"].nunique()
        if (equal > 1).any():
            raise ValueError("conflicting filing evidence has an equal ordering key")
        long = ordered.drop_duplicates(key, keep="last").reset_index(drop=True)
    empty_index = pd.MultiIndex.from_arrays([[], []], names=["datetime", "episode_id"])
    wide = long.pivot(index=["datetime", "episode_id"], columns="feature_id", values="value") if not long.empty else pd.DataFrame(index=empty_index)
    wide = wide.reindex(columns=list(FEATURE_IDS)).reset_index()
    if not wide.empty:
        ciks = grid[["datetime", "episode_id", "cik"]].copy()
        ciks["cik"] = ciks["cik"].astype(str).str.zfill(10)
        wide = wide.merge(ciks, on=["datetime", "episode_id"], validate="one_to_one")[["datetime", "episode_id", "cik", *FEATURE_IDS]]
    else:
        wide.insert(2, "cik", pd.Series(dtype="object"))
    return long, wide


def seal_historical_filing_features(
    observations: Iterable[FilingFeatureObservationV1], *, session_grid: pd.DataFrame,
    bindings: pd.DataFrame, output_root: Path,
) -> dict[str, object]:
    """Persist the two frozen public filing artifacts and one identity manifest."""
    if output_root.exists():
        raise FileExistsError(output_root)
    output_root.mkdir(parents=True)
    items = tuple(observations)
    long, wide = project_historical_filing_features(items, session_grid=session_grid, bindings=bindings)
    sparse_path = output_root / "filing-observations.parquet"
    projection_path = output_root / "filing-session-projection.parquet"
    pd.DataFrame([item.model_dump(mode="json") for item in items]).to_parquet(sparse_path, index=False)
    long.to_parquet(output_root / "filing-provenance-ledger.parquet", index=False)
    wide.to_parquet(projection_path, index=False)

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    manifest: dict[str, object] = {
        "schema_version": "P5FilingFeatureHistoryV1", "feature_ids": list(FEATURE_IDS),
        "observation_count": len(items), "edgartools_runtime_identity": EDGARTOOLS_RUNTIME_IDENTITY,
        "projected_cell_count": int(wide[list(FEATURE_IDS)].notna().sum().sum()),
        "artifacts": {"sparse_observations": {"path": sparse_path.name, "sha256": digest(sparse_path)},
                      "session_projection": {"path": projection_path.name, "sha256": digest(projection_path)}},
    }
    identity_payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest["artifact_identity"] = "sha256:" + hashlib.sha256(identity_payload.encode()).hexdigest()
    (output_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


__all__ = [
    "discover_native_filing_observations",
    "materialize_selected_filing_features",
    "project_historical_filing_features",
    "seal_historical_filing_features",
]
