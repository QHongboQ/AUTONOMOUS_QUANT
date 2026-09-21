from __future__ import annotations

import inspect
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

import exchange_calendars as xcals
import pytest
from edgar.attachments import Attachment, Attachments
from edgar.company_reports import CurrentReport, SixK
from pydantic import ValidationError

import aq_p5_filing_features.materialize as materialize_module
from aq_p5_filing_features import (
    FEATURE_IDS,
    FilingFeatureObservationV1,
    materialize_selected_filing_features,
)

UTC = timezone.utc
XNYS = xcals.get_calendar("XNYS")


@dataclass
class _FrozenFiling:
    form: str
    attachments: Attachments
    cik: int = 1
    accession_no: str = "0000000001-24-000001"


def _attachment(
    document_type: str,
    *,
    description: str = "MATERIAL AGREEMENT",
    document: str = "exhibit.htm",
) -> Attachment:
    return Attachment(
        sequence_number="2",
        description=description,
        document=document,
        ixbrl=False,
        path=f"/Archives/local/{document}",
        document_type=document_type,
        size=128,
    )


def _filing(form: str, *attachments: Attachment) -> _FrozenFiling:
    return _FrozenFiling(
        form=form,
        attachments=Attachments(
            document_files=list(attachments),
            data_files=[],
            primary_documents=[],
        ),
    )


def _materialize(
    filing: _FrozenFiling,
    *,
    acceptance: datetime = datetime(2024, 3, 1, 20, 0, tzinfo=UTC),
    report_period: date | None = date(2023, 12, 31),
    report: CurrentReport | SixK | None = None,
    source_available: bool = True,
) -> tuple[FilingFeatureObservationV1, ...]:
    return materialize_selected_filing_features(
        filing,
        sec_acceptance_datetime=acceptance,
        report_period_end=report_period,
        native_report=report,
        calendar=XNYS,
        source_available=source_available,
    )


def _feature(
    observations: tuple[FilingFeatureObservationV1, ...], feature_id: str
) -> FilingFeatureObservationV1:
    return next(item for item in observations if item.feature_id == feature_id)


def test_a_filing_lag_days_normal_positive_value() -> None:
    filing = _filing("10-K")
    item = _feature(_materialize(filing), "p5_filing_lag_days_v1")

    assert item.exact_scalar_value == 61
    assert item.missingness_status is None


def test_b_filing_lag_days_negative_is_invalid_not_clipped() -> None:
    filing = _filing("10-K")
    item = _feature(
        _materialize(filing, report_period=date(2024, 3, 2)),
        "p5_filing_lag_days_v1",
    )

    assert item.exact_scalar_value is None
    assert item.missingness_status == "INVALID_VALUE"


def test_c_acceptance_strictly_after_market_close_is_one() -> None:
    filing = _filing("10-Q")
    item = _feature(
        _materialize(filing, acceptance=datetime(2024, 3, 1, 22, 0, tzinfo=UTC)),
        "p5_accepted_after_market_close_v1",
    )

    assert item.exact_scalar_value == 1
    assert item.first_available_xnys_session == date(2024, 3, 4)


def test_d_intraday_acceptance_is_zero() -> None:
    filing = _filing("10-Q")
    item = _feature(
        _materialize(filing, acceptance=datetime(2024, 3, 1, 20, 0, tzinfo=UTC)),
        "p5_accepted_after_market_close_v1",
    )

    assert item.exact_scalar_value == 0
    assert item.missingness_status is None


def test_e_non_session_acceptance_is_missing() -> None:
    filing = _filing("10-Q")
    item = _feature(
        _materialize(filing, acceptance=datetime(2024, 3, 2, 15, 0, tzinfo=UTC)),
        "p5_accepted_after_market_close_v1",
    )

    assert item.exact_scalar_value is None
    assert item.missingness_status == "NOT_APPLICABLE_FORM"


def test_f_ordinary_filing_is_not_an_amendment() -> None:
    item = _feature(_materialize(_filing("10-K")), "p5_is_amendment_v1")

    assert item.exact_scalar_value == 0
    assert item.amendment_status == "ORIGINAL"


def test_g_exact_form_suffix_marks_an_amendment() -> None:
    item = _feature(_materialize(_filing("10-K/A")), "p5_is_amendment_v1")

    assert item.exact_scalar_value == 1
    assert item.amendment_status == "AMENDMENT"


def test_h_current_report_native_press_release_is_present() -> None:
    filing = _filing(
        "8-K",
        _attachment(
            "EX-99.1",
            description="QUARTERLY EARNINGS RELEASE",
            document="release.htm",
        ),
    )
    item = _feature(
        _materialize(filing, report=CurrentReport(filing)),
        "p5_press_release_exhibit_present_v1",
    )

    assert item.exact_scalar_value == 1
    assert item.missingness_status is None


def test_i_loaded_current_report_without_press_release_is_validated_absence() -> None:
    filing = _filing("8-K", _attachment("EX-10.1"))
    item = _feature(
        _materialize(filing, report=CurrentReport(filing)),
        "p5_press_release_exhibit_present_v1",
    )

    assert item.exact_scalar_value == 0
    assert item.missingness_status == "VALIDATED_ABSENCE"


def test_j_sixk_uses_native_press_release_path() -> None:
    filing = _filing(
        "6-K",
        _attachment(
            "EX-99.1",
            description="PRESS RELEASE",
            document="foreign-release.htm",
        ),
    )
    item = _feature(
        _materialize(filing, report=SixK(filing)),
        "p5_press_release_exhibit_present_v1",
    )

    assert item.exact_scalar_value == 1
    assert item.native_edgartools_object_identity == "edgar.company_reports.sixk.SixK"


def test_k_authorized_exhibit_count_is_exact_native_count() -> None:
    filing = _filing(
        "8-K",
        _attachment("EX-99.1", document="release.htm"),
        _attachment("EX-10.1", document="agreement.htm"),
        _attachment("GRAPHIC", document="logo.png"),
    )
    item = _feature(
        _materialize(filing, report=CurrentReport(filing)),
        "p5_authorized_exhibit_count_v1",
    )

    assert item.exact_scalar_value == 2
    assert item.missingness_status is None


def test_l_non_event_form_exhibit_features_are_not_applicable() -> None:
    observations = _materialize(_filing("10-K"))

    for feature_id in (
        "p5_press_release_exhibit_present_v1",
        "p5_authorized_exhibit_count_v1",
    ):
        item = _feature(observations, feature_id)
        assert item.exact_scalar_value is None
        assert item.missingness_status == "NOT_APPLICABLE_FORM"


def test_m_missing_report_period_is_explicit_required_metadata_missing() -> None:
    item = _feature(
        _materialize(_filing("10-K"), report_period=None),
        "p5_filing_lag_days_v1",
    )

    assert item.exact_scalar_value is None
    assert item.missingness_status == "REQUIRED_METADATA_MISSING"


def test_n_source_unavailable_produces_no_scalar() -> None:
    observations = _materialize(_filing("8-K"), source_available=False)

    assert len(observations) == 5
    assert all(item.exact_scalar_value is None for item in observations)
    assert all(item.missingness_status == "SOURCE_UNAVAILABLE" for item in observations)
    assert all(
        item.source_availability_status == "SOURCE_UNAVAILABLE"
        for item in observations
    )


def test_o_duplicate_identical_observation_has_identical_evidence_id() -> None:
    filing = _filing("10-Q")
    first = _materialize(filing)
    second = _materialize(filing)

    assert [item.evidence_id for item in first] == [item.evidence_id for item in second]


def test_p_changed_authoritative_input_changes_evidence_id() -> None:
    filing = _filing("10-Q")
    first = _feature(
        _materialize(filing, acceptance=datetime(2024, 3, 1, 19, 0, tzinfo=UTC)),
        "p5_is_amendment_v1",
    )
    second = _feature(
        _materialize(filing, acceptance=datetime(2024, 3, 1, 20, 0, tzinfo=UTC)),
        "p5_is_amendment_v1",
    )

    assert first.evidence_id != second.evidence_id


def test_event_form_without_native_report_is_explicitly_unavailable() -> None:
    observations = _materialize(_filing("8-K"), report=None)

    for feature_id in (
        "p5_press_release_exhibit_present_v1",
        "p5_authorized_exhibit_count_v1",
    ):
        item = _feature(observations, feature_id)
        assert item.exact_scalar_value is None
        assert item.missingness_status == "NATIVE_OBJECT_UNAVAILABLE"
        assert item.native_edgartools_object_identity is None


def test_exact_contract_is_immutable_and_identity_fails_closed() -> None:
    item = _feature(_materialize(_filing("10-K")), "p5_is_amendment_v1")

    assert set(FilingFeatureObservationV1.model_fields) == {
        "schema_version",
        "feature_id",
        "source_accession",
        "cik",
        "form",
        "sec_acceptance_datetime",
        "first_available_xnys_session",
        "native_edgartools_object_identity",
        "exact_scalar_value",
        "missingness_status",
        "amendment_status",
        "source_availability_status",
        "edgartools_runtime_identity",
        "evidence_id",
    }
    with pytest.raises(ValidationError):
        item.exact_scalar_value = 1
    changed = item.model_dump(mode="python")
    changed["sec_acceptance_datetime"] += timedelta(minutes=1)
    with pytest.raises(ValidationError, match="evidence_id"):
        FilingFeatureObservationV1.model_validate(changed)


def test_exact_feature_inventory_and_no_early_visibility() -> None:
    acceptance = datetime(2024, 3, 1, 22, 0, tzinfo=UTC)
    observations = _materialize(_filing("10-Q"), acceptance=acceptance)

    assert tuple(item.feature_id for item in observations) == FEATURE_IDS
    assert len({item.feature_id for item in observations}) == 5
    for item in observations:
        assert XNYS.session_open(item.first_available_xnys_session) > acceptance


def test_materializer_has_no_network_parser_or_generic_engine() -> None:
    source = inspect.getsource(materialize_module)

    for forbidden in (
        "requests",
        "httpx",
        "sec.gov",
        "download(",
        "parse_html",
        "FeatureRegistry",
        "ProviderRegistry",
    ):
        assert forbidden not in source
