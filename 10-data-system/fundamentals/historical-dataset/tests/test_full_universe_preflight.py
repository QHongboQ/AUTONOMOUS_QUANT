from __future__ import annotations

import json
from pathlib import Path

import pytest

from aq_edgartools_full_build import (
    EDGARTOOLS_STANDARD_CONCEPT_PROJECTION,
    MAX_PEAK_BYTES,
    MAX_PERSISTENT_BYTES,
    NIL_FACT_NOT_ELIGIBLE,
    NON_REACQUIRABLE_OR_ADJUDICATION_SOURCE,
    NON_NUMERIC_FACT_NOT_ELIGIBLE,
    NUMERIC_FACT_SELECTED,
    REACQUIRABLE_SOURCE_CACHE,
    NumericFactCanonicalizationError,
    SourceHashMismatchError,
    accession_metadata_row,
    build_spec_identity,
    checkpoint_identity,
    checkpoint_reusable,
    deduplicate_accessions,
    failure_record,
    hash_inventory,
    is_native_financial_candidate,
    project_storage,
    project_edgartools_standard_concept,
    select_authorized_entityfacts,
    selective_policy_identity,
    select_numeric_fact_value,
    select_stratified_sample,
    sha256_bytes,
    sha256_file,
    source_cache_evictable,
    source_provenance_record,
    verify_reacquired_source,
    write_json_atomic,
)


def _row(accession: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "accession": accession,
        "cik": accession[:10],
        "issuer_name": "Issuer",
        "issuer_family": "DOMESTIC",
        "form": "10-K",
        "filing_date": "2020-01-01",
        "acceptance_datetime": "2020-01-01T22:00:00+00:00",
        "report_period": "2019-12-31",
        "primary_document": "report.htm",
        "source_size_bytes": 1_000_000,
        "is_xbrl": True,
        "is_inline_xbrl": True,
        "native_object_type": "TenK",
        "native_financial_candidate": True,
        "amendment": False,
    }
    row.update(overrides)
    return row


def test_native_capability_uses_upstream_type_and_structured_6k_boundary() -> None:
    assert is_native_financial_candidate(native_object_type="TenK", form="10-K", is_xbrl=True)
    assert is_native_financial_candidate(native_object_type="TwentyF", form="20-F", is_xbrl=True)
    assert is_native_financial_candidate(native_object_type="CurrentReport", form="6-K", is_xbrl=True)
    assert not is_native_financial_candidate(native_object_type="CurrentReport", form="8-K", is_xbrl=True)
    assert not is_native_financial_candidate(native_object_type="TenQ", form="10-Q", is_xbrl=False)


@pytest.mark.parametrize("value", ["text block", "true", "2024-12-31", "MemberEnum"])
def test_native_non_numeric_facts_are_excluded_before_decimal_conversion(value: str) -> None:
    selection, canonical = select_numeric_fact_value(
        {"value": value, "numeric_value": None, "unit_ref": None}
    )
    assert selection == NON_NUMERIC_FACT_NOT_ELIGIBLE
    assert canonical is None


def test_native_nil_fact_is_excluded_without_becoming_zero() -> None:
    selection, canonical = select_numeric_fact_value(
        {"value": "", "numeric_value": None, "unit_ref": "USD"}
    )
    assert selection == NIL_FACT_NOT_ELIGIBLE
    assert canonical is None


@pytest.mark.parametrize(
    ("value", "native_value", "expected"),
    [
        ("42", 42.0, "42"),
        ("42.500", 42.5, "42.5"),
        ("-7.25", -7.25, "-7.25"),
        ("1.25E+3", 1250.0, "1250"),
    ],
)
def test_native_numeric_facts_are_exactly_canonicalized(
    value: str, native_value: float, expected: str
) -> None:
    selection, canonical = select_numeric_fact_value(
        {"value": value, "numeric_value": native_value, "unit_ref": "USD"}
    )
    assert selection == NUMERIC_FACT_SELECTED
    assert canonical == expected


def test_native_numeric_fact_with_invalid_decimal_fails_closed() -> None:
    with pytest.raises(NumericFactCanonicalizationError):
        select_numeric_fact_value(
            {"value": "not-a-decimal", "numeric_value": None, "unit_ref": "USD"}
        )


def test_entityfacts_selection_uses_upstream_standard_concepts_before_accessions() -> None:
    facts = [
        {
            "accession": "0000000001-20-000001",
            "concept": "us-gaap:Assets",
            "taxonomy": "us-gaap",
            "label": "Assets",
            "value": 10,
            "numeric_value": 10.0,
            "unit": "USD",
            "period_type": "instant",
            "period_start": None,
            "period_end": "2019-12-31",
            "filing_date": "2020-02-01",
            "form_type": "10-K",
            "context_ref": "c1",
            "dimensions": {},
        },
        {
            "accession": "0000000001-20-000002",
            "concept": "us-gaap:IrrelevantNumeric",
            "taxonomy": "us-gaap",
            "label": "Irrelevant",
            "value": 20,
            "numeric_value": 20.0,
            "unit": "USD",
            "period_type": "instant",
            "period_end": "2019-12-31",
            "filing_date": "2020-02-01",
            "form_type": "10-K",
        },
    ]

    def upstream_mapper(concept: str, _label: str, _context: object) -> str | None:
        return "Total Assets" if concept == "us-gaap:Assets" else None

    selected = select_authorized_entityfacts(facts, map_concept=upstream_mapper)
    assert len(selected) == 1
    assert selected[0]["accession"] == "0000000001-20-000001"
    assert selected[0]["standard_concept"] == "Assets"


def test_entityfacts_selection_rejects_nonnumeric_unapproved_form_and_missing_accession() -> None:
    base = {
        "accession": "0000000001-20-000001",
        "concept": "us-gaap:Assets",
        "taxonomy": "us-gaap",
        "label": "Assets",
        "value": 10,
        "numeric_value": 10.0,
        "unit": "USD",
        "period_type": "instant",
        "period_end": "2019-12-31",
        "filing_date": "2020-02-01",
        "form_type": "10-K",
    }
    rows = [
        {**base, "numeric_value": None},
        {**base, "form_type": "8-K"},
        {**base, "accession": ""},
    ]
    assert not select_authorized_entityfacts(
        rows,
        map_concept=lambda *_args: "Total Assets",
    )


def test_standard_concept_projection_is_finite_and_not_a_raw_alias_dictionary() -> None:
    assert len(EDGARTOOLS_STANDARD_CONCEPT_PROJECTION) == 11
    assert project_edgartools_standard_concept("Total Assets") == "Assets"
    assert project_edgartools_standard_concept("us-gaap:Assets") is None
    assert selective_policy_identity().startswith("sha256:")
    assert len(selective_policy_identity()) == 71


def test_metadata_projection_records_native_surface_without_form_router() -> None:
    raw = {
        "accession_number": "0000000001-20-000001",
        "form": "10-Q",
        "filing_date": "2020-04-01",
        "acceptanceDateTime": "2020-04-01T20:00:00Z",
        "reportDate": "2020-03-31",
        "primaryDocument": "q.htm",
        "size": 123,
        "isXBRL": 1,
    }
    row = accession_metadata_row(
        raw,
        cik="1",
        issuer_name="Issuer",
        issuer_family="DOMESTIC",
        native_object_type="TenQ",
    )
    assert row["cik"] == "0000000001"
    assert row["native_financial_candidate"] is True
    assert row["source_size_bytes"] == 123


def test_accession_deduplication_rejects_conflict() -> None:
    row = _row("0000000001-20-000001")
    assert len(deduplicate_accessions([row, row])) == 1
    related = deduplicate_accessions([row, {**row, "cik": "0000000002"}])[0]
    assert related["observed_for_bound_ciks"] == ["0000000001", "0000000002"]
    assert related["retrieval_cik_hint"] == "0000000001"
    with pytest.raises(ValueError, match="conflicting accession"):
        deduplicate_accessions([row, {**row, "form": "10-Q"}])


def test_stratified_sample_is_deterministic_and_not_small_only() -> None:
    rows = []
    for index in range(50):
        accession = f"{index + 1:010d}-20-000001"
        rows.append(
            _row(
                accession,
                filing_date=f"{2010 + index % 15}-01-01",
                source_size_bytes=(index + 1) * 1_000_000,
                native_object_type="TenQ" if index % 2 else "TenK",
                form="10-Q" if index % 2 else "10-K",
                amendment=index == 4,
            )
        )
    rows.append(
        _row(
            "0000000100-20-000001",
            native_object_type="TwentyF",
            form="20-F",
            issuer_family="FOREIGN_PRIVATE_ISSUER",
        )
    )
    first = select_stratified_sample(rows, target_count=16)
    second = select_stratified_sample(rows, target_count=16)
    assert first == second
    reasons = {reason for row in first for reason in row["sample_reasons"]}
    assert {"DOMESTIC_10K", "DOMESTIC_10Q", "AMENDMENT", "FOREIGN_20F"} <= reasons
    assert "LARGEST_PROVIDER_REPORTED" in reasons


def test_storage_gate_passes_and_blocks_at_frozen_thresholds() -> None:
    small = [
        {"source_bytes": 1000, "evidence_bytes": 100, "event_bytes": 10, "retained_bytes": 1110}
        for _ in range(32)
    ]
    passed = project_storage(candidate_count=100, sample_results=small, inventory_bytes=1000)
    assert passed["storage_preflight"] == "PASS"
    huge = [
        {
            "source_bytes": MAX_PERSISTENT_BYTES,
            "evidence_bytes": MAX_PERSISTENT_BYTES,
            "event_bytes": 1,
            "retained_bytes": MAX_PERSISTENT_BYTES + 2,
        }
        for _ in range(32)
    ]
    blocked = project_storage(candidate_count=2, sample_results=huge, inventory_bytes=1)
    assert blocked["projected_persistent_bytes"] > MAX_PERSISTENT_BYTES
    assert blocked["projected_total_peak_bytes"] > MAX_PEAK_BYTES
    assert blocked["storage_preflight"] == "BLOCKED_STORAGE_PREFLIGHT"


def test_remote_first_storage_excludes_ordinary_source_cache() -> None:
    source_bytes = 1024**3
    rows = [
        {
            "source_bytes": source_bytes,
            "evidence_bytes": 100,
            "event_bytes": 10,
            "required_exception_source_bytes": 0,
        }
        for _ in range(2)
    ]
    candidate_count = 1000
    result = project_storage(
        candidate_count=candidate_count,
        sample_results=rows,
        inventory_bytes=1000,
        estimated_one_time_network_bytes=candidate_count * source_bytes,
    )
    assert result["sampled_raw_source_cache_bytes"] == 2 * source_bytes
    assert result["estimated_one_time_network_bytes"] == candidate_count * source_bytes
    assert result["projected_persistent_bytes"] < MAX_PERSISTENT_BYTES
    assert result["storage_preflight"] == "PASS"


def test_adjudication_source_remains_persistent() -> None:
    row = {
        "source_bytes": 100,
        "evidence_bytes": 1,
        "event_bytes": 1,
        "required_exception_source_bytes": MAX_PERSISTENT_BYTES,
    }
    result = project_storage(candidate_count=2, sample_results=[row], inventory_bytes=1)
    assert result["projected_required_exception_source_bytes"] == 2 * MAX_PERSISTENT_BYTES
    assert result["storage_preflight"] == "BLOCKED_STORAGE_PREFLIGHT"


def test_source_provenance_survives_cache_eviction_and_reacquisition(tmp_path: Path) -> None:
    payload = b"authoritative SEC source"
    provenance = source_provenance_record(
        accession="0000000001-20-000001",
        cik="0000000001",
        source_document_identity="SEC_FULL_SUBMISSION:0000000001-20-000001",
        source_document_url="https://www.sec.gov/source.txt",
        source_document_sha256=sha256_bytes(payload),
        source_byte_count=len(payload),
    )
    assert provenance == {
        "accession": "0000000001-20-000001",
        "cik": "0000000001",
        "source_document_identity": "SEC_FULL_SUBMISSION:0000000001-20-000001",
        "source_document_url": "https://www.sec.gov/source.txt",
        "source_document_sha256": sha256_bytes(payload),
        "source_byte_count": len(payload),
        "source_storage_class": REACQUIRABLE_SOURCE_CACHE,
    }
    assert verify_reacquired_source(provenance, payload)
    with pytest.raises(SourceHashMismatchError):
        verify_reacquired_source(provenance, b"changed")

    output = tmp_path / "evidence.jsonl"
    output.write_text("sealed", encoding="utf-8")
    checkpoint = {
        **provenance,
        "terminal_state": "COMPLETE_WITH_EVIDENCE",
        "evidence_sealed": False,
        "output_hashes": {"evidence": sha256_file(output)},
    }
    assert not source_cache_evictable(checkpoint, output_paths={"evidence": output})
    checkpoint["evidence_sealed"] = True
    assert source_cache_evictable(checkpoint, output_paths={"evidence": output})
    checkpoint["source_storage_class"] = NON_REACQUIRABLE_OR_ADJUDICATION_SOURCE
    assert not source_cache_evictable(checkpoint, output_paths={"evidence": output})


def test_dvc_manifest_excludes_transient_source_mirror(tmp_path: Path) -> None:
    source = tmp_path / "staging/sample-source/source.txt"
    evidence = tmp_path / "evidence/fact.jsonl"
    source.parent.mkdir(parents=True)
    evidence.parent.mkdir(parents=True)
    source.write_text("temporary", encoding="utf-8")
    evidence.write_text("persistent", encoding="utf-8")
    manifest = hash_inventory(tmp_path, exclude_prefixes=("staging/sample-source",))
    assert [row["path"] for row in manifest["files"]] == ["evidence/fact.jsonl"]
    assert manifest["excluded_transient_prefixes"] == ["staging/sample-source"]


def test_checkpoint_resume_requires_all_identities_and_hashes(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    output = tmp_path / "output.json"
    source.write_text("source", encoding="utf-8")
    output.write_text("output", encoding="utf-8")
    outputs = {"evidence": sha256_file(output)}
    identity = checkpoint_identity(
        build_spec_id="sha256:" + "a" * 64,
        accession="0000000001-20-000001",
        source_sha256=sha256_file(source),
        output_hashes=outputs,
    )
    checkpoint = {
        "accession": "0000000001-20-000001",
        "terminal_state": "COMPLETE_WITH_EVIDENCE",
        "build_spec_identity": "sha256:" + "a" * 64,
        "source_sha256": sha256_file(source),
        "output_hashes": outputs,
        "checkpoint_identity": identity,
    }
    assert checkpoint_reusable(
        checkpoint,
        build_spec_id="sha256:" + "a" * 64,
        source_path=source,
        output_paths={"evidence": output},
    )
    output.write_text("changed", encoding="utf-8")
    assert not checkpoint_reusable(
        checkpoint,
        build_spec_id="sha256:" + "a" * 64,
        source_path=source,
        output_paths={"evidence": output},
    )


def test_manifest_writes_atomically_and_build_identity_is_stable(tmp_path: Path) -> None:
    path = tmp_path / "manifest.json"
    first = write_json_atomic(path, {"b": 2, "a": 1})
    second = write_json_atomic(path, {"a": 1, "b": 2})
    assert first == second
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1, "b": 2}
    assert build_spec_identity({"b": "2", "a": "1"}) == build_spec_identity({"a": "1", "b": "2"})


def test_failure_ledger_distinguishes_transient_and_deterministic() -> None:
    transient = failure_record(
        accession="a", cik="1", stage="download", error=TimeoutError("wait"), attempts=3
    )
    deterministic = failure_record(
        accession="a", cik="1", stage="parse", error=ValueError("bad"), attempts=1
    )
    assert transient["terminal_state"] == "FAILED_TRANSIENT"
    assert transient["retry_disposition"] == "MAXIMUM_3_BOUNDED_ATTEMPTS"
    assert deterministic["terminal_state"] == "FAILED_DETERMINISTIC"
    assert deterministic["retry_disposition"] == "NO_BLIND_RETRY"
