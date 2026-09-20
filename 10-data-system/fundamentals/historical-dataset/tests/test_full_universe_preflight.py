from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from aq_edgartools_full_build import (
    EDGARTOOLS_STANDARD_CONCEPT_PROJECTION,
    ENTITYFACTS_DISCOVERY_ROLE,
    NIL_FACT_NOT_ELIGIBLE,
    NON_NUMERIC_FACT_NOT_ELIGIBLE,
    NUMERIC_FACT_SELECTED,
    REACQUIRABLE_SOURCE_CACHE,
    SourceHashMismatchError,
    TRANSITION_FINANCIAL_FORMS,
    bounded_batches,
    checkpoint_identity,
    checkpoint_reusable,
    failure_record,
    native_financial_object_info,
    native_xbrl_source_manifest,
    select_authorized_entityfacts,
    select_numeric_fact_value,
    selective_policy_identity,
    sha256_file,
    source_cache_evictable,
    verify_native_xbrl_source_manifest,
)
from aq_fundamental_evidence.materialize import materialize_edgartools_fact
from aq_fundamental_evidence import canonical_decimal_value
from aq_hybrid_fundamentals import (
    FROZEN_STANDARD_CONCEPTS,
    project_edgartools_standard_concept,
)
from run_full_universe_preflight import (
    _HomepageFilingView,
    _canonical_identity,
    _install_transient_native_cache,
    _validate_source_unavailable_record,
    SOURCE_UNAVAILABLE_ACCESSION_COUNT,
    SOURCE_UNAVAILABLE_CLASSIFICATION,
    SOURCE_VERIFIABLE_REQUIRED_ACCESSION_COUNT,
)


def _object_info(form: str) -> tuple[bool, str | None, str | None]:
    return {
        "10-K": (True, "TenK", "annual"),
        "10-K/A": (True, "TenK", "annual amendment"),
        "10-Q": (True, "TenQ", "quarterly"),
        "20-F": (True, "TwentyF", "foreign annual"),
        "40-F": (True, "FortyF", "foreign annual"),
        "6-K": (True, "CurrentReport", "foreign current"),
        "8-K": (True, "EightK", "current"),
        "S-1": (True, "RegistrationS1", "registration"),
    }.get(form, (False, None, None))


@pytest.mark.parametrize("form", ["10-K", "10-K/A", "10-Q", "20-F", "40-F", "6-K"])
def test_native_object_capability_admits_only_financial_surface(form: str) -> None:
    admitted, object_type = native_financial_object_info(form, get_info=_object_info)
    assert admitted
    assert object_type


@pytest.mark.parametrize("form", ["8-K", "S-1", "UNKNOWN"])
def test_native_object_capability_rejects_other_typed_objects(form: str) -> None:
    assert native_financial_object_info(form, get_info=_object_info)[0] is False


def test_pinned_edgartools_object_capability_is_the_runtime_authority() -> None:
    assert native_financial_object_info("10-K") == (True, "TenK")
    assert native_financial_object_info("6-K") == (True, "CurrentReport")
    assert native_financial_object_info("8-K") == (False, "EightK")


@pytest.mark.parametrize("form", sorted(TRANSITION_FINANCIAL_FORMS))
def test_transition_financial_forms_have_a_narrow_admission_leaf(form: str) -> None:
    assert native_financial_object_info(form, get_info=_object_info) == (True, None)


@pytest.mark.parametrize("form", ["10-KT", "10-QT"])
def test_transition_forms_use_the_existing_native_xbrl_asset_path(form: str) -> None:
    filing = _Filing()
    filing.form = form
    manifest = native_xbrl_source_manifest(filing)
    assert manifest["accession"] == filing.accession_no
    assert [row["role"] for row in manifest["assets"]] == [
        "instance",
        "schema",
        "label",
    ]


@pytest.mark.parametrize("form", sorted(TRANSITION_FINANCIAL_FORMS))
def test_transition_form_is_preserved_and_does_not_set_fact_period(form: str) -> None:
    filing = SimpleNamespace(
        accession_no="0000000001-20-000001",
        form=form,
        cik=1,
        company="Issuer",
        filing_date=date(2020, 2, 1),
    )
    evidence = materialize_edgartools_fact(
        filing,
        {
            "concept": "us-gaap:Assets",
            "value": "10",
            "unit_ref": "USD",
            "period_type": "instant",
            "period_instant": "2019-12-31",
        },
        acceptance_datetime=datetime(2020, 2, 1, 22, tzinfo=timezone.utc),
        report_period_end="2019-12-31",
        source_document_sha256="a" * 64,
        source_document_identity="SEC_XBRL_ASSET_MANIFEST:" + "b" * 64,
        source_document_url="https://www.sec.gov/example.xml",
        edgartools_version="5.58.0",
        upstream_identity="PYPI_DISTRIBUTION:edgartools==5.58.0",
    )
    assert evidence.filing.form == form
    assert evidence.fact.instant == date(2019, 12, 31)
    assert evidence.fact.period_start is None
    assert evidence.fact.period_end is None


def test_source_unavailable_record_is_accounting_only_and_fail_closed() -> None:
    body = {
        "accession": "0001100682-20-000033",
        "cik": "0001100682",
        "entityfacts_observed_form": "10-Q",
        "selected_fact_count": 1,
        "affected_standard_concepts": ["Assets"],
        "affected_periods": [],
        "discovery_source_identity": "SEC_ENTITYFACTS_REPORT_SHA256:example",
        "classification": SOURCE_UNAVAILABLE_CLASSIFICATION,
        "reason": "Exact SEC accession exposes no usable filing attachments.",
    }
    record = {**body, "decision_identity": _canonical_identity(body)}
    assert _validate_source_unavailable_record(record) == record
    for prohibited in ("source_document_sha256", "replacement_accession"):
        altered = {**body, prohibited: "fabricated"}
        altered["decision_identity"] = _canonical_identity(altered)
        with pytest.raises(RuntimeError, match="fail-closed"):
            _validate_source_unavailable_record(altered)
    with pytest.raises(ValueError, match="missing accession_no"):
        materialize_edgartools_fact(
            SimpleNamespace(**record),
            {},
            acceptance_datetime=datetime(2020, 2, 1, tzinfo=timezone.utc),
            report_period_end="2019-12-31",
            source_document_sha256="a" * 64,
            edgartools_version="5.58.0",
            upstream_identity="PYPI_DISTRIBUTION:edgartools==5.58.0",
        )


def test_corrected_execution_accounting_is_exact() -> None:
    assert SOURCE_VERIFIABLE_REQUIRED_ACCESSION_COUNT == 36_204
    assert SOURCE_UNAVAILABLE_ACCESSION_COUNT == 2
    assert (
        SOURCE_VERIFIABLE_REQUIRED_ACCESSION_COUNT
        + SOURCE_UNAVAILABLE_ACCESSION_COUNT
        == 36_206
    )


@pytest.mark.parametrize("value", ["text block", "true", "2024-12-31", "MemberEnum"])
def test_native_non_numeric_facts_are_excluded(value: str) -> None:
    status, canonical = select_numeric_fact_value(
        {"value": value, "numeric_value": None, "unit_ref": None}
    )
    assert status == NON_NUMERIC_FACT_NOT_ELIGIBLE
    assert canonical is None


def test_nil_fact_is_excluded_without_becoming_zero() -> None:
    assert select_numeric_fact_value(
        {"value": "", "numeric_value": None, "unit_ref": "USD"}
    ) == (NIL_FACT_NOT_ELIGIBLE, None)


@pytest.mark.parametrize("value", ["42", "-7.25", "0", "1250"])
def test_numeric_admission_reuses_existing_canonical_decimal_authority(value: str) -> None:
    assert select_numeric_fact_value(
        {"value": value, "numeric_value": 1, "unit_ref": "USD"}
    ) == (NUMERIC_FACT_SELECTED, value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("42.500", "42.5"), ("1.25E+3", "1250"), ("-0", "0")],
)
def test_exact_xbrl_lexical_value_is_normalized_before_existing_authority(
    value: str, expected: str
) -> None:
    assert select_numeric_fact_value(
        {"value": value, "numeric_value": 1, "unit_ref": "USD"}
    ) == (NUMERIC_FACT_SELECTED, expected)
    with pytest.raises(ValueError):
        canonical_decimal_value(value)


def test_nonfinite_native_numeric_value_fails_closed() -> None:
    with pytest.raises(ValueError):
        select_numeric_fact_value(
            {"value": "NaN", "numeric_value": 1, "unit_ref": "USD"}
        )


def test_entityfacts_selects_only_upstream_mapped_accession_discovery() -> None:
    facts = [
        {
            "accession": "0000000001-20-000001",
            "concept": "us-gaap:Assets",
            "label": "Assets",
            "value": "10",
            "numeric_value": 10,
            "filing_date": "2020-02-01",
            "form_type": "10-K",
        },
        {
            "accession": "0000000001-20-000002",
            "concept": "us-gaap:Other",
            "label": "Other",
            "value": "20",
            "numeric_value": 20,
            "filing_date": "2020-02-01",
            "form_type": "10-K",
        },
    ]
    rows = select_authorized_entityfacts(
        facts,
        map_concept=lambda concept, *_: "Total Assets" if concept.endswith("Assets") else None,
        get_info=_object_info,
    )
    assert rows == [
        {
            "accession": "0000000001-20-000001",
            "concept": "us-gaap:Assets",
            "standard_concept": "Assets",
            "form": "10-K",
            "filing_date": "2020-02-01",
            "source_role": ENTITYFACTS_DISCOVERY_ROLE,
        }
    ]


def test_entityfacts_aggregate_is_never_final_source_authority() -> None:
    row = select_authorized_entityfacts(
        [
            {
                "accession": "0000000001-20-000001",
                "concept": "us-gaap:Assets",
                "value": "10",
                "numeric_value": 10,
                "filing_date": "2020-02-01",
                "form_type": "10-K",
            }
        ],
        map_concept=lambda *_: "Total Assets",
        get_info=_object_info,
    )[0]
    assert row["source_role"] == ENTITYFACTS_DISCOVERY_ROLE
    assert "source_document_sha256" not in row
    assert "source_document_identity" not in row


def test_concept_projection_has_one_existing_semantic_owner() -> None:
    assert set(EDGARTOOLS_STANDARD_CONCEPT_PROJECTION.values()) == set(
        FROZEN_STANDARD_CONCEPTS
    )
    assert project_edgartools_standard_concept("Total Assets") == "Assets"
    assert project_edgartools_standard_concept("us-gaap:Assets") is None
    assert selective_policy_identity().startswith("sha256:")


class _Attachment:
    def __init__(self, role: str, payload: bytes) -> None:
        types = {
            "instance": "EX-101.INS",
            "schema": "EX-101.SCH",
            "label": "EX-101.LAB",
            "presentation": "EX-101.PRE",
            "calculation": "EX-101.CAL",
            "definition": "EX-101.DEF",
        }
        extensions = {"schema": ".xsd"}
        extension = extensions.get(role, ".xml")
        self.document_type = types[role]
        self.document = f"report-{role}{extension}"
        self.path = f"/Archives/edgar/data/1/2/{self.document}"
        self.url = f"https://www.sec.gov{self.path}"
        self.content = payload.decode("utf-8")

    @property
    def extension(self) -> str:
        return Path(self.document).suffix


class _Filing:
    accession_no = "0000000001-20-000001"

    def __init__(self) -> None:
        payloads = {
            "instance": b"<xbrl>facts</xbrl>",
            "schema": b"<schema/>",
            "label": b"<linkbase>labels</linkbase>",
        }
        self.attachments = SimpleNamespace(
            data_files=[_Attachment(role, payload) for role, payload in payloads.items()]
        )

    def full_text_submission(self) -> str:
        raise AssertionError("full submission must not be used")


def test_native_asset_manifest_is_deterministic_and_avoids_full_submission() -> None:
    filing = _Filing()
    first = native_xbrl_source_manifest(filing)
    second = native_xbrl_source_manifest(filing)
    assert first == second
    assert [row["role"] for row in first["assets"]] == ["instance", "schema", "label"]
    assert first["source_document_identity"].startswith("SEC_XBRL_ASSET_MANIFEST:")
    assert first["source_storage_class"] == REACQUIRABLE_SOURCE_CACHE


def test_homepage_view_and_lazy_cache_do_not_touch_sgml_or_unselected_files(
    tmp_path: Path,
) -> None:
    class LazyAttachment:
        def __init__(self, document_type: str, document: str, payload: str) -> None:
            self.document_type = document_type
            self.document = document
            self.path = f"/Archives/{document}"
            self.url = f"https://www.sec.gov{self.path}"
            self.payload = payload
            self.read_count = 0

        @property
        def extension(self) -> str:
            return Path(self.document).suffix

        @property
        def content(self) -> str:
            override = getattr(self, "_content_override", None)
            if override is not None:
                return override() if callable(override) else override
            self.read_count += 1
            return self.payload

        @content.setter
        def content(self, value: object) -> None:
            self._content_override = value

    instance = LazyAttachment("EX-101.INS", "instance.xml", "<xbrl></xbrl>")
    unselected = LazyAttachment("OTHER", "other.txt", "not xbrl")
    attachments = SimpleNamespace(data_files=[instance, unselected])
    original = SimpleNamespace(accession_no="0000000001-20-000001", form="10-K")
    view = _HomepageFilingView(
        original, attachments, period_of_report="2019-12-31"
    )
    stats = {"current_bytes": 0, "max_bytes": 0, "breach_count": 0}
    _install_transient_native_cache(attachments, tmp_path, stats)
    assert instance.read_count == 0
    assert unselected.read_count == 0
    manifest = native_xbrl_source_manifest(view)
    assert [row["role"] for row in manifest["assets"]] == ["instance"]
    assert instance.read_count == 1
    assert unselected.read_count == 0
    assert view.sgml() is None


def test_native_asset_manifest_reacquisition_hash_mismatch_fails_closed() -> None:
    manifest = native_xbrl_source_manifest(_Filing())
    good = {
        "instance": b"<xbrl>facts</xbrl>",
        "schema": b"<schema/>",
        "label": b"<linkbase>labels</linkbase>",
    }
    assert verify_native_xbrl_source_manifest(manifest, good)
    with pytest.raises(SourceHashMismatchError):
        verify_native_xbrl_source_manifest(manifest, {**good, "instance": b"changed"})


def test_same_accession_fact_retains_native_manifest_provenance() -> None:
    manifest = native_xbrl_source_manifest(_Filing())
    filing = SimpleNamespace(
        accession_no="0000000001-20-000001",
        form="10-K",
        cik=1,
        company="Issuer",
        filing_date=date(2020, 2, 1),
    )
    evidence = materialize_edgartools_fact(
        filing,
        {
            "concept": "us-gaap:Assets",
            "value": "10",
            "unit_ref": "USD",
            "period_type": "instant",
            "period_instant": "2019-12-31",
        },
        acceptance_datetime=datetime(2020, 2, 1, 22, tzinfo=timezone.utc),
        report_period_end="2019-12-31",
        source_document_sha256=str(manifest["source_document_sha256"]),
        source_document_identity=str(manifest["source_document_identity"]),
        source_document_url=str(manifest["source_document_url"]),
        edgartools_version="5.58.0",
        upstream_identity="PYPI_DISTRIBUTION:edgartools==5.58.0",
    )
    assert evidence.filing.accession == manifest["accession"]
    assert evidence.source.source_document_sha256 == manifest["manifest_sha256"]
    assert evidence.source.source_document_identity == manifest["source_document_identity"]


def test_bounded_batches_enforce_count_and_source_byte_limits() -> None:
    rows = [{"accession": str(index), "expected_native_asset_bytes": 4} for index in range(5)]
    batches = list(bounded_batches(rows, max_count=3, max_expected_bytes=8))
    assert [len(batch) for batch in batches] == [2, 2, 1]
    with pytest.raises(ValueError):
        list(
            bounded_batches(
                [{"accession": "x", "expected_native_asset_bytes": 9}],
                max_expected_bytes=8,
            )
        )


def test_checkpoint_reuse_and_cache_eviction_require_sealed_hashes(tmp_path: Path) -> None:
    output = tmp_path / "evidence.jsonl"
    output.write_text("sealed", encoding="utf-8")
    hashes = {"evidence": sha256_file(output)}
    checkpoint = {
        "accession": "0000000001-20-000001",
        "build_spec_identity": "sha256:" + "a" * 64,
        "source_manifest_sha256": "b" * 64,
        "source_storage_class": REACQUIRABLE_SOURCE_CACHE,
        "terminal_state": "COMPLETE_WITH_EVIDENCE",
        "evidence_sealed": True,
        "output_hashes": hashes,
    }
    checkpoint["checkpoint_identity"] = checkpoint_identity(
        build_spec_identity=str(checkpoint["build_spec_identity"]),
        accession=str(checkpoint["accession"]),
        source_manifest_sha256=str(checkpoint["source_manifest_sha256"]),
        output_hashes=hashes,
    )
    paths = {"evidence": output}
    assert checkpoint_reusable(
        checkpoint,
        build_spec_identity=str(checkpoint["build_spec_identity"]),
        output_paths=paths,
    )
    assert source_cache_evictable(checkpoint, output_paths=paths)
    output.write_text("changed", encoding="utf-8")
    assert not source_cache_evictable(checkpoint, output_paths=paths)


def test_failure_accounting_never_blindly_retries_deterministic_errors() -> None:
    transient = failure_record(
        accession="a", cik="1", stage="source", error=TimeoutError("wait"), attempts=3
    )
    deterministic = failure_record(
        accession="a", cik="1", stage="parse", error=ValueError("bad"), attempts=1
    )
    assert transient["terminal_state"] == "FAILED_TRANSIENT"
    assert transient["retry_disposition"] == "MAXIMUM_3_BOUNDED_ATTEMPTS"
    assert deterministic["terminal_state"] == "FAILED_DETERMINISTIC"
    assert deterministic["retry_disposition"] == "NO_BLIND_RETRY"
