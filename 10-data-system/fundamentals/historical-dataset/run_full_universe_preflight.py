"""Run the authorized EdgarTools-native inventory and storage preflight.

This command deliberately stops before broad accession acquisition unless the
frozen storage gate passes. It uses EdgarTools for every SEC/network and XBRL
operation and reuses the existing AQ evidence and PIT policy primitives.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import re
import shutil
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

import pandas as pd

from aq_edgartools_full_build import (
    EDGARTOOLS_STANDARD_CONCEPT_PROJECTION,
    BUILD_SPEC_VERSION,
    EDGARTOOLS_VERSION,
    HISTORY_END,
    HISTORY_START,
    MAX_ACTIVE_BATCH_SOURCE_BYTES,
    MAX_ENUMERATION_CIKS,
    MAX_PEAK_BYTES,
    MAX_PERSISTENT_BYTES,
    NIL_FACT_NOT_ELIGIBLE,
    NON_NUMERIC_FACT_NOT_ELIGIBLE,
    NumericFactCanonicalizationError,
    RESERVED_BUILD_TEMP_BYTES,
    RESERVED_MANIFEST_DVC_BYTES,
    RESERVED_SESSION_PROJECTION_BYTES,
    accession_metadata_row,
    build_spec_identity,
    deduplicate_accessions,
    failure_record,
    hash_inventory,
    load_authority,
    percentile,
    project_storage,
    project_edgartools_standard_concept,
    select_authorized_entityfacts,
    selective_policy_identity,
    select_numeric_fact_value,
    select_stratified_sample,
    sha256_bytes,
    sha256_file,
    write_json_atomic,
)


REPO = Path(__file__).resolve().parents[3]
ROOT_DEFAULT = Path("/mnt/d/AQ_DATA/P5/edgartools-native-full-universe-historical-build-001")
IDENTITY_PATH = Path("/home/zhou/.config/autonomous-quant/p5-edgar.env")
BINDINGS = Path("/mnt/d/AQ_DATA/P5/identity-accounting-final-closeout-001/final_binding_ledger.json")
EXCLUSIONS = REPO / "10-data-system/fundamentals/identity-binding/accepted_episode_sec_cik_exclusions.json"
P1_EPISODES = Path("/mnt/d/AQ_DATA/P1/pit/reconciled/v1/instrument_episodes.jsonl")
DESIGN_CHECKSUMS = Path("/mnt/d/AQ_DATA/P5/edgartools-native-full-universe-build-design-001/checksums.json")
EXPECTED_BINDING_SHA256 = "51f61a3bce916e29a300b075d19b6ffe8de371701c836201621b6a740cbbfee2"
EXPECTED_DESIGN_SHA256 = "bd1e8d07fdece2a11b0aafb0f26d5b1905df3802ba35f9f9ce770a4cd26232b1"
UPSTREAM_IDENTITY = "PYPI_DISTRIBUTION:edgartools==5.58.0"


def load_identity() -> str:
    if not IDENTITY_PATH.is_file() or IDENTITY_PATH.stat().st_mode & 0o077:
        raise RuntimeError("private SEC identity is absent or insecure")
    for raw in IDENTITY_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip().removeprefix("export ").strip()
        key, sep, value = line.partition("=")
        if sep and key.strip() in {"EDGAR_IDENTITY", "SEC_IDENTITY"}:
            identity = value.strip().strip('"').strip("'")
            if re.fullmatch(r".+\s+[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", identity):
                return identity
    raise RuntimeError("meaningful private SEC identity is not configured")


def prepare(root: Path) -> None:
    for name in (
        "inventory/cik",
        "checkpoints",
        "source",
        "evidence",
        "standardized-events",
        "session-projection",
        "manifests",
        "reports",
        "dvc",
        "failures",
        "staging/edgar-data",
        "staging/sample-source",
        "staging/sample-evidence",
        "staging/sample-events",
        "selective/cik",
        "selective/sample-evidence",
        "selective/sample-events",
    ):
        (root / name).mkdir(parents=True, exist_ok=True)


def authority(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str]:
    if sha256_file(DESIGN_CHECKSUMS) != EXPECTED_DESIGN_SHA256:
        raise RuntimeError("design checksum ledger mismatch")
    episodes, bindings, exclusions = load_authority(
        episodes_path=P1_EPISODES,
        bindings_path=BINDINGS,
        exclusions_path=EXCLUSIONS,
        expected_binding_sha256=EXPECTED_BINDING_SHA256,
    )
    hashes = {
        "p1_episodes": sha256_file(P1_EPISODES),
        "bindings": sha256_file(BINDINGS),
        "exclusions": sha256_file(EXCLUSIONS),
        "design": sha256_file(DESIGN_CHECKSUMS),
    }
    spec_id = build_spec_identity(hashes)
    write_json_atomic(
        root / "manifests/build_spec.json",
        {
            "schema": BUILD_SPEC_VERSION,
            "build_spec_identity": spec_id,
            "authority_hashes": hashes,
            "edgartools_version": EDGARTOOLS_VERSION,
            "history": [HISTORY_START, HISTORY_END],
            "population": {
                "total_p1_episodes": len(episodes),
                "binding_records": len(bindings),
                "bound_episodes": len({row["episode_id"] for row in bindings}),
                "excluded_episodes": len(exclusions),
                "bound_ciks": len({row["cik"] for row in bindings}),
            },
        },
    )
    return episodes, bindings, exclusions, spec_id


def configure_edgar(root: Path) -> None:
    identity = load_identity()
    os.environ["EDGAR_IDENTITY"] = identity
    os.environ["EDGAR_RATE_LIMIT_PER_SEC"] = "2"
    os.environ["EDGAR_LOCAL_DATA_DIR"] = str(root / "staging/edgar-data")
    os.environ["EDGAR_CACHE_DIR"] = str(root / "staging/edgar-object-cache")


def enumerate_inventory(root: Path) -> dict[str, Any]:
    _, bindings, _, spec_id = authority(root)
    configure_edgar(root)
    if importlib.metadata.version("edgartools") != EDGARTOOLS_VERSION:
        raise RuntimeError("EdgarTools version drift")
    from edgar import Company, get_obj_info, set_identity

    set_identity(os.environ["EDGAR_IDENTITY"])
    ciks = sorted({row["cik"] for row in bindings})
    all_rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    started = time.monotonic()
    for sequence, cik in enumerate(ciks, 1):
        target = root / "inventory/cik" / f"{cik}.json"
        if target.is_file():
            snapshot = json.loads(target.read_text(encoding="utf-8"))
            if snapshot.get("build_spec_identity") == spec_id:
                all_rows.extend(snapshot["rows"])
                status = "REUSED"
                if sequence % MAX_ENUMERATION_CIKS == 0 or sequence == len(ciks):
                    print(json.dumps({"stage": "inventory", "sequence": sequence, "total": len(ciks), "status": status}), flush=True)
                continue
        error: BaseException | None = None
        for attempt in range(1, 4):
            try:
                company = Company(int(cik))
                native_filings = company.get_filings(
                    filing_date=(HISTORY_START, HISTORY_END),
                    amendments=True,
                    is_xbrl=True,
                    trigger_full_load=True,
                )
                frame = native_filings.to_pandas()
                filer_type = str(company.filer_type)
                family = (
                    "DOMESTIC"
                    if filer_type == "Domestic"
                    else "FOREIGN_PRIVATE_ISSUER"
                    if filer_type in {"Foreign", "Canadian"}
                    else "UNCLASSIFIED"
                )
                rows = []
                for item in frame.to_dict("records"):
                    form = str(item.get("form") or "")
                    _, native_object_type, _ = get_obj_info(form)
                    row = accession_metadata_row(
                        item,
                        cik=cik,
                        issuer_name=str(company.name),
                        issuer_family=family,
                        native_object_type=native_object_type,
                    )
                    if row["native_financial_candidate"]:
                        rows.append(row)
                rows.sort(key=lambda row: (str(row.get("acceptance_datetime") or ""), str(row["accession"])))
                write_json_atomic(
                    target,
                    {
                        "schema": "AQ_P5_EDGARTOOLS_NATIVE_CIK_INVENTORY_V1",
                        "build_spec_identity": spec_id,
                        "cik": cik,
                        "issuer_name": str(company.name),
                        "issuer_family": family,
                        "native_xbrl_filing_count": len(frame),
                        "native_financial_candidate_count": len(rows),
                        "rows": rows,
                    },
                )
                all_rows.extend(rows)
                error = None
                status = "PASS"
                break
            except Exception as exc:
                error = exc
                if attempt < 3:
                    time.sleep(attempt * 2)
        if error is not None:
            status = "FAILED"
            failure = failure_record(
                accession=f"CIK:{cik}", cik=cik, stage="NATIVE_ACCESSION_ENUMERATION", error=error, attempts=3
            )
            failures.append(failure)
            write_json_atomic(root / "failures" / f"inventory-{cik}.json", failure)
        if sequence % MAX_ENUMERATION_CIKS == 0 or sequence == len(ciks):
            print(
                json.dumps(
                    {
                        "stage": "inventory",
                        "sequence": sequence,
                        "total": len(ciks),
                        "status": status,
                        "candidate_rows": len(all_rows),
                        "failures": len(failures),
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                    }
                ),
                flush=True,
            )
    unique = deduplicate_accessions(all_rows)
    form_counts = Counter(str(row["form"]) for row in unique)
    type_counts = Counter(str(row["native_object_type"]) for row in unique)
    inventory = {
        "schema": "AQ_P5_EDGARTOOLS_NATIVE_ACCESSION_INVENTORY_V1",
        "build_spec_identity": spec_id,
        "edgartools_version": EDGARTOOLS_VERSION,
        "history": [HISTORY_START, HISTORY_END],
        "bound_cik_count": len(ciks),
        "completed_cik_count": len(ciks) - len(failures),
        "failed_cik_count": len(failures),
        "candidate_observation_count": len(all_rows),
        "unique_candidate_accession_count": len(unique),
        "counts_by_native_object_type": dict(sorted(type_counts.items())),
        "counts_by_observed_form": dict(sorted(form_counts.items())),
        "accession_is_filing_identity": True,
        "aq_form_whitelist_used": False,
        "rows": unique,
        "failures": failures,
    }
    write_json_atomic(root / "inventory/accession_inventory.json", inventory)
    return inventory


def acceptance_utc(filing: Any) -> datetime:
    accepted = filing.sgml().header.acceptance_datetime
    if accepted is None:
        raise RuntimeError(f"missing SEC acceptance datetime: {filing.accession_no}")
    if accepted.tzinfo is None:
        accepted = accepted.replace(tzinfo=ZoneInfo("America/New_York"))
    return accepted.astimezone(timezone.utc)


def clean_fact(raw: Mapping[str, object]) -> dict[str, object]:
    fact: dict[str, object] = {}
    for key, value in raw.items():
        if isinstance(value, (list, tuple, dict, set)):
            fact[key] = value
            continue
        try:
            missing = bool(pd.isna(value))
        except (TypeError, ValueError):
            missing = False
        fact[key] = None if missing else value
    return fact


def source_url(filing: Any) -> str:
    return str(filing.text_url)


def parse_sample_accession(root: Path, row: Mapping[str, object]) -> dict[str, object]:
    from edgar import Filing
    from edgar.xbrl.core import classify_duration, duration_days
    from edgar.xbrl.standardization import get_default_mapper

    evidence_parent = REPO / "20-intelligence-system/fundamental-factors/evidence-contract"
    historical_parent = REPO / "10-data-system/fundamentals/historical-dataset"
    for parent in (evidence_parent, historical_parent):
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
    from aq_fundamental_evidence.materialize import materialize_edgartools_fact
    from aq_hybrid_fundamentals import (
        FROZEN_STANDARD_CONCEPTS,
        admit_period_class,
        consolidated_projection_events,
    )

    accession = str(row["accession"])
    source_path = root / "staging/sample-source" / f"{accession}.txt"
    if not source_path.is_file():
        filing_ref = Filing(
            cik=int(str(row["cik"])),
            company=str(row["issuer_name"]),
            form=str(row["form"]),
            filing_date=str(row["filing_date"]),
            accession_no=accession,
        )
        source_path.write_text(filing_ref.full_text_submission(), encoding="utf-8")
    raw_source = source_path.read_bytes()
    filing = Filing.from_sgml_text(raw_source.decode("utf-8", errors="replace"))
    if filing.accession_no != accession or str(filing.cik).zfill(10) != str(row["cik"]):
        raise RuntimeError("accession source identity mismatch")
    accepted = acceptance_utc(filing)
    report_period = str(filing.sgml().period_of_report or row.get("report_period") or "")
    if not report_period:
        raise RuntimeError("filing report period is absent")
    source_sha = sha256_bytes(raw_source)
    provenance = {
        "source_document_identity": f"SEC_FULL_SUBMISSION:{accession}",
        "source_document_url": source_url(filing),
        "source_document_sha256": source_sha,
        "source_byte_count": len(raw_source),
        "source_storage_class": "REACQUIRABLE_SOURCE_CACHE",
    }
    xbrl = filing.xbrl()
    if xbrl is None:
        return {
            "accession": accession,
            "cik": str(row["cik"]),
            "terminal_state": "COMPLETE_NO_STRUCTURED_FINANCIALS",
            "source_bytes": len(raw_source),
            "evidence_bytes": 0,
            "event_bytes": 0,
            "projection_bytes": 0,
            "required_exception_source_bytes": 0,
            "persistent_bytes": 0,
            "retained_bytes": 0,
            "temporary_bytes": len(raw_source),
            "raw_fact_count": 0,
            "non_numeric_fact_skipped_count": 0,
            "nil_fact_skipped_count": 0,
            "numeric_fact_selected_count": 0,
            "numeric_fact_canonicalization_failure_count": 0,
            "authorized_evidence_count": 0,
            "dimension_bearing_raw_fact_count": 0,
            "consolidated_admitted_event_count": 0,
            "source_sha256": source_sha,
            **provenance,
            "sample_reasons": list(row.get("sample_reasons") or []),
        }
    mapper = get_default_mapper()
    evidence_rows: list[dict[str, object]] = []
    event_candidates: list[dict[str, object]] = []
    dimension_count = 0
    native_facts = xbrl.facts.to_dataframe().to_dict("records")
    non_numeric_fact_count = 0
    nil_fact_count = 0
    numeric_fact_count = 0
    numeric_canonicalization_failure_count = 0
    for raw_fact in native_facts:
        fact = clean_fact(raw_fact)
        if (
            fact.get("period_type") not in {"instant", "duration"}
            or ":" not in str(fact.get("concept") or "")
        ):
            continue
        try:
            selection, canonical_value = select_numeric_fact_value(fact)
        except NumericFactCanonicalizationError:
            numeric_canonicalization_failure_count += 1
            raise
        if selection == NON_NUMERIC_FACT_NOT_ELIGIBLE:
            non_numeric_fact_count += 1
            continue
        if selection == NIL_FACT_NOT_ELIGIBLE:
            nil_fact_count += 1
            continue
        numeric_fact_count += 1
        fact["value"] = canonical_value
        try:
            evidence = materialize_edgartools_fact(
                filing,
                fact,
                acceptance_datetime=accepted,
                report_period_end=report_period,
                source_document_sha256=source_sha,
                edgartools_version=EDGARTOOLS_VERSION,
                upstream_identity=UPSTREAM_IDENTITY,
                source_document_identity=f"SEC_FULL_SUBMISSION:{accession}",
                source_document_url=source_url(filing),
            )
        except ValueError:
            continue
        payload = evidence.model_dump(mode="json")
        evidence_rows.append(payload)
        dimensions = evidence.fact.dimensions or {}
        dimension_count += int(bool(dimensions))
        standard = mapper.map_concept(
            str(fact["concept"]), str(fact.get("label") or fact["concept"]), {}
        )
        if standard not in FROZEN_STANDARD_CONCEPTS:
            continue
        duration_class = None
        if fact["period_type"] == "duration":
            start = pd.Timestamp(fact["period_start"]).date()
            end = pd.Timestamp(fact["period_end"]).date()
            duration_class = classify_duration(duration_days(start, end))
        period_class = admit_period_class(str(fact["period_type"]), duration_class)
        event_candidates.append(
            {
                "cik": evidence.entity.cik,
                "standard_concept": standard,
                "period_class": period_class,
                "canonical_value": evidence.fact.value,
                "unit": evidence.fact.unit,
                "evidence_id": evidence.evidence_id,
                "accession": accession,
                "first_available_at": evidence.availability.first_available_at.isoformat(),
                "report_period_start": (
                    evidence.fact.period_start.isoformat() if evidence.fact.period_start else None
                ),
                "report_period_end": (
                    evidence.fact.period_end.isoformat()
                    if evidence.fact.period_end
                    else evidence.fact.instant.isoformat()
                ),
                "dimensions": dimensions,
            }
        )
    event_frame = consolidated_projection_events(pd.DataFrame(event_candidates)) if event_candidates else pd.DataFrame()
    event_rows = event_frame.to_dict("records") if not event_frame.empty else []
    evidence_payload = b"".join(
        json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
        for item in evidence_rows
    )
    event_payload = b"".join(
        json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
        for item in event_rows
    )
    evidence_path = root / "staging/sample-evidence" / f"{accession}.jsonl"
    event_path = root / "staging/sample-events" / f"{accession}.jsonl"
    evidence_path.write_bytes(evidence_payload)
    event_path.write_bytes(event_payload)
    return {
        "accession": accession,
        "cik": str(row["cik"]),
        "form": str(row["form"]),
        "native_object_type": row.get("native_object_type"),
        "issuer_family": row.get("issuer_family"),
        "filing_date": row.get("filing_date"),
        "acceptance_datetime": accepted.isoformat(),
        "terminal_state": "COMPLETE_WITH_EVIDENCE" if evidence_rows else "COMPLETE_NO_AUTHORIZED_FACTS",
        "source_bytes": len(raw_source),
        "evidence_bytes": len(evidence_payload),
        "event_bytes": len(event_payload),
        "projection_bytes": 0,
        "required_exception_source_bytes": 0,
        "persistent_bytes": len(evidence_payload) + len(event_payload),
        "retained_bytes": len(evidence_payload) + len(event_payload),
        "temporary_bytes": len(raw_source),
        "raw_fact_count": len(native_facts),
        "non_numeric_fact_skipped_count": non_numeric_fact_count,
        "nil_fact_skipped_count": nil_fact_count,
        "numeric_fact_selected_count": numeric_fact_count,
        "numeric_fact_canonicalization_failure_count": numeric_canonicalization_failure_count,
        "authorized_evidence_count": len(evidence_rows),
        "dimension_bearing_raw_fact_count": dimension_count,
        "consolidated_admitted_event_count": len(event_rows),
        "source_sha256": source_sha,
        **provenance,
        "sample_reasons": list(row.get("sample_reasons") or []),
    }


def sampled_manifest_checkpoint_bytes(root: Path) -> int:
    """Measure the stable sample authority, excluding self-referential manifests."""

    paths = [
        root / "reports/runtime.json",
        root / "reports/stratified_sample_inventory.json",
        root / "reports/stratified_sample_results.json",
    ]
    paths.extend(path for path in (root / "checkpoints").rglob("*") if path.is_file())
    return sum(path.stat().st_size for path in paths if path.is_file())


def remote_first_storage_projection(root: Path) -> dict[str, Any]:
    """Reaccount the frozen sample without network or raw-source acquisition."""

    inventory_path = root / "inventory/accession_inventory.json"
    results_path = root / "reports/stratified_sample_results.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    sample_doc = json.loads(results_path.read_text(encoding="utf-8"))
    if sample_doc["failure_count"] or sample_doc["completed_count"] != sample_doc["sample_count"]:
        raise RuntimeError("frozen sample is not complete and failure-free")
    network_bytes = sum(int(row.get("source_size_bytes") or 0) for row in inventory["rows"])
    storage = project_storage(
        candidate_count=int(inventory["unique_candidate_accession_count"]),
        sample_results=sample_doc["rows"],
        inventory_bytes=inventory_path.stat().st_size,
        sampled_manifest_checkpoint_bytes=sampled_manifest_checkpoint_bytes(root),
        estimated_one_time_network_bytes=network_bytes,
    )
    storage.update(
        {
            "sample_failure_count": 0,
            "dimension_bearing_sample_count": sample_doc["dimension_bearing_sample_count"],
            "non_numeric_fact_skipped_count": sample_doc[
                "non_numeric_fact_skipped_count"
            ],
            "nil_fact_skipped_count": sample_doc["nil_fact_skipped_count"],
            "numeric_fact_selected_count": sample_doc["numeric_fact_selected_count"],
            "numeric_fact_canonicalization_failure_count": sample_doc[
                "numeric_fact_canonicalization_failure_count"
            ],
            "full_sec_source_mirror": False,
            "ordinary_source_bytes_permanent": False,
            "authoritative_structured_evidence_permanent": True,
            "offline_derived_evidence_replay": True,
            "offline_raw_source_reextraction": (
                "NOT_REQUIRED_FOR_ORDINARY_SEALED_ACCESSIONS"
            ),
        }
    )
    write_json_atomic(root / "reports/storage_preflight.json", storage)
    manifest = hash_inventory(
        root,
        exclude_names=("preflight_manifest.json",),
        exclude_prefixes=(
            "staging/sample-source",
            "staging/edgar-data",
            "staging/edgar-object-cache",
        ),
    )
    manifest.update(
        {
            "build_spec_identity": inventory["build_spec_identity"],
            "storage_preflight": storage["storage_preflight"],
            "ordinary_source_cache_dvc_sealed": False,
        }
    )
    write_json_atomic(root / "manifests/preflight_manifest.json", manifest)
    return storage


def _entityfact_mapping(fact: Any) -> dict[str, object]:
    """Expose only the public FinancialFact fields needed by selection."""

    return {
        "accession": fact.accession,
        "concept": fact.concept,
        "taxonomy": fact.taxonomy,
        "label": fact.label,
        "value": fact.value,
        "numeric_value": fact.numeric_value,
        "unit": fact.unit,
        "period_type": fact.period_type,
        "period_start": fact.period_start,
        "period_end": fact.period_end,
        "filing_date": fact.filing_date,
        "form_type": fact.form_type,
        "context_ref": fact.context_ref,
        "dimensions": fact.dimensions,
    }


def _validate_upstream_standard_concepts() -> None:
    """Fail closed if EdgarTools' public StandardConcept authority drifts."""

    from edgar.xbrl.standardization import StandardConcept

    expected = {
        StandardConcept.REVENUE.value,
        StandardConcept.NET_INCOME.value,
        StandardConcept.TOTAL_ASSETS.value,
        StandardConcept.TOTAL_LIABILITIES.value,
        StandardConcept.TOTAL_EQUITY.value,
        StandardConcept.CASH_FROM_OPERATIONS.value,
        StandardConcept.CASH_AND_EQUIVALENTS.value,
        StandardConcept.TOTAL_CURRENT_ASSETS.value,
        StandardConcept.TOTAL_CURRENT_LIABILITIES.value,
        StandardConcept.SHORT_TERM_DEBT.value,
        StandardConcept.LONG_TERM_DEBT.value,
    }
    if expected != set(EDGARTOOLS_STANDARD_CONCEPT_PROJECTION):
        raise RuntimeError("EdgarTools StandardConcept authority drift")


def _native_cache_bytes(root: Path) -> int:
    paths = (root / "staging/edgar-data", root / "staging/edgar-object-cache")
    return sum(
        path.stat().st_size
        for parent in paths
        if parent.exists()
        for path in parent.rglob("*")
        if path.is_file()
    )


def _sample_source_bytes(root: Path) -> int:
    parent = root / "staging/sample-source"
    return sum(path.stat().st_size for path in parent.glob("*.txt") if path.is_file())


def _bounded_native_cache(root: Path) -> dict[str, int]:
    """Use EdgarTools' cache eviction when the frozen 2 GiB ceiling is reached."""

    native_bytes = _native_cache_bytes(root)
    total_bytes = native_bytes + _sample_source_bytes(root)
    if total_bytes <= 2 * 1024**3:
        return {"files_deleted": 0, "bytes_freed": 0, "errors": 0}
    from edgar.storage_management import clear_cache

    result = clear_cache(dry_run=False)
    if result["errors"] or _native_cache_bytes(root) + _sample_source_bytes(root) > 2 * 1024**3:
        raise RuntimeError("EdgarTools native cache cannot satisfy the 2 GiB ceiling")
    return result


def _entityfacts_snapshot(
    cik: str, spec_id: str, selection_id: str
) -> tuple[dict[str, object] | None, BaseException | None]:
    """Fetch and reduce one native EntityFacts object without filing-body access."""

    from edgar.entity.entity_facts import get_company_facts
    from edgar.exceptions import CompanyFactsNotFoundError
    from edgar.xbrl.standardization import get_default_mapper

    error: BaseException | None = None
    for attempt in range(1, 4):
        try:
            try:
                entityfacts = get_company_facts(int(cik))
            except CompanyFactsNotFoundError:
                entityfacts = None
            if entityfacts is None:
                return (
                    {
                        "schema": "AQ_P5_EDGARTOOLS_ENTITYFACTS_SELECTIVE_CIK_V1",
                        "build_spec_identity": spec_id,
                        "selective_policy_identity": selection_id,
                        "cik": cik,
                        "entityfacts_available": False,
                        "selected_fact_count": 0,
                        "selected_accessions": [],
                    },
                    None,
                )
            mapper = get_default_mapper()
            selected = select_authorized_entityfacts(
                (_entityfact_mapping(fact) for fact in entityfacts.get_all_facts()),
                map_concept=mapper.map_concept,
            )
            grouped: dict[str, dict[str, object]] = {}
            for fact in selected:
                accession = str(fact["accession"])
                current = grouped.setdefault(
                    accession,
                    {
                        "accession": accession,
                        "cik": cik,
                        "form": fact["form"],
                        "filing_date": fact["filing_date"],
                        "selected_fact_count": 0,
                        "standard_concept_counts": Counter(),
                        "raw_concept_count": set(),
                    },
                )
                if current["form"] != fact["form"] or current["filing_date"] != fact["filing_date"]:
                    raise RuntimeError(f"EntityFacts accession metadata conflict: {accession}")
                current["selected_fact_count"] = int(current["selected_fact_count"]) + 1
                current["standard_concept_counts"][str(fact["standard_concept"])] += 1
                current["raw_concept_count"].add(str(fact["concept"]))
            rows = [
                {
                    **value,
                    "standard_concept_counts": dict(sorted(value["standard_concept_counts"].items())),
                    "raw_concept_count": len(value["raw_concept_count"]),
                    "source_role": "ENTITYFACTS_DISCOVERY_REQUIRES_ACCESSION_VALIDATION",
                }
                for value in grouped.values()
            ]
            rows.sort(key=lambda value: (str(value["filing_date"]), str(value["accession"])))
            return (
                {
                    "schema": "AQ_P5_EDGARTOOLS_ENTITYFACTS_SELECTIVE_CIK_V1",
                    "build_spec_identity": spec_id,
                    "selective_policy_identity": selection_id,
                    "cik": cik,
                    "entityfacts_available": True,
                    "selected_fact_count": len(selected),
                    "selected_accessions": rows,
                },
                None,
            )
        except Exception as exc:
            error = exc
            if attempt < 3:
                time.sleep(attempt)
    return None, error


def entityfacts_selective_census(root: Path) -> dict[str, Any]:
    """Build the 711-CIK fact-index/accession census without filing-body reads."""

    _, bindings, _, spec_id = authority(root)
    configure_edgar(root)
    if importlib.metadata.version("edgartools") != EDGARTOOLS_VERSION:
        raise RuntimeError("EdgarTools version drift")
    _validate_upstream_standard_concepts()
    from edgar import set_identity

    set_identity(os.environ["EDGAR_IDENTITY"])
    selection_id = selective_policy_identity()
    ciks = sorted({str(row["cik"]).zfill(10) for row in bindings})
    selected_fact_count = 0
    available_count = 0
    unavailable_count = 0
    failures: list[dict[str, object]] = []
    accession_rows: list[dict[str, object]] = []
    native_cache_evictions = {"files_deleted": 0, "bytes_freed": 0}
    started = time.monotonic()
    pending: list[str] = []
    completed = 0
    for cik in ciks:
        target = root / "selective/cik" / f"{cik}.json"
        if target.is_file():
            cached = json.loads(target.read_text(encoding="utf-8"))
            if (
                cached.get("build_spec_identity") == spec_id
                and cached.get("selective_policy_identity") == selection_id
            ):
                available_count += int(cached["entityfacts_available"])
                unavailable_count += int(not cached["entityfacts_available"])
                selected_fact_count += int(cached["selected_fact_count"])
                accession_rows.extend(cached["selected_accessions"])
                completed += 1
                continue
        pending.append(cik)
    if completed:
        print(json.dumps({"stage": "entityfacts", "sequence": completed, "total": len(ciks), "status": "REUSED"}), flush=True)
    for batch_start in range(0, len(pending), 16):
        batch = pending[batch_start : batch_start + 16]
        with ThreadPoolExecutor(max_workers=len(batch), thread_name_prefix="entityfacts") as pool:
            results = list(
                pool.map(
                    lambda value: _entityfacts_snapshot(value, spec_id, selection_id),
                    batch,
                )
            )
        for cik, (snapshot, error) in zip(batch, results, strict=True):
            completed += 1
            if error is not None or snapshot is None:
                failures.append(
                    {
                        "cik": cik,
                        "stage": "ENTITYFACTS_METADATA_DISCOVERY",
                        "error_class": type(error).__name__ if error else "UnknownError",
                        "error_message": str(error) if error else "missing snapshot",
                        "attempt_count": 3,
                    }
                )
                status = "FAILED"
            else:
                write_json_atomic(root / "selective/cik" / f"{cik}.json", snapshot)
                available_count += int(snapshot["entityfacts_available"])
                unavailable_count += int(not snapshot["entityfacts_available"])
                selected_fact_count += int(snapshot["selected_fact_count"])
                accession_rows.extend(snapshot["selected_accessions"])
                status = "COMPLETE"
            if completed % 25 == 0 or completed == len(ciks) or status == "FAILED":
                print(
                    json.dumps(
                        {
                            "stage": "entityfacts",
                            "sequence": completed,
                            "total": len(ciks),
                            "cik": cik,
                            "status": status,
                            "elapsed_seconds": round(time.monotonic() - started, 1),
                        }
                    ),
                    flush=True,
                )
        evicted = _bounded_native_cache(root)
        native_cache_evictions["files_deleted"] += int(evicted["files_deleted"])
        native_cache_evictions["bytes_freed"] += int(evicted["bytes_freed"])
    by_accession: dict[str, dict[str, object]] = {}
    for row in accession_rows:
        accession = str(row["accession"])
        prior = by_accession.get(accession)
        if prior is None:
            by_accession[accession] = row
            continue
        if prior["form"] != row["form"] or prior["filing_date"] != row["filing_date"]:
            raise RuntimeError(f"cross-CIK EntityFacts accession conflict: {accession}")
        prior["selected_fact_count"] = int(prior["selected_fact_count"]) + int(row["selected_fact_count"])
    unique_rows = sorted(by_accession.values(), key=lambda value: (str(value["filing_date"]), str(value["accession"])))
    domestic = sum(str(row["form"]).startswith(("10-K", "10-Q")) for row in unique_rows)
    foreign = len(unique_rows) - domestic
    inventory = {
        "schema": "AQ_P5_EDGARTOOLS_ENTITYFACTS_SELECTIVE_ACCESSION_INVENTORY_V1",
        "build_spec_identity": spec_id,
        "selective_policy_identity": selection_id,
        "bound_cik_count": len(ciks),
        "cik_entityfacts_available_count": available_count,
        "cik_entityfacts_unavailable_count": unavailable_count,
        "failed_cik_count": len(failures),
        "entityfacts_selected_fact_count": selected_fact_count,
        "selective_required_accession_count": len(unique_rows),
        "domestic_selected_accession_count": domestic,
        "foreign_selected_accession_count": foreign,
        "native_cache_evictions": native_cache_evictions,
        "native_cache_bytes_at_close": _native_cache_bytes(root),
        "rows": unique_rows,
        "failures": failures,
    }
    write_json_atomic(root / "selective/entityfacts_selective_accessions.json", inventory)
    return inventory


def selective_sample_and_storage(root: Path) -> dict[str, Any]:
    """Filter the frozen sample, then project only selective persistent surfaces."""

    from edgar.xbrl.standardization import get_default_mapper

    census_path = root / "selective/entityfacts_selective_accessions.json"
    sample_path = root / "reports/stratified_sample_results.json"
    original_inventory_path = root / "inventory/accession_inventory.json"
    if not census_path.is_file() or not sample_path.is_file() or not original_inventory_path.is_file():
        raise RuntimeError("selective census and frozen sample/inventory are required")
    census = json.loads(census_path.read_text(encoding="utf-8"))
    if census["failed_cik_count"]:
        raise RuntimeError("EntityFacts selective census has failed CIKs")
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    if sample["sample_count"] != 32 or sample["failure_count"]:
        raise RuntimeError("frozen 32-accession sample is unavailable")
    mapper = get_default_mapper()
    selected_evidence_count = 0
    selected_evidence_bytes = 0
    selected_event_count = 0
    selected_event_bytes = 0
    selected_accessions: set[str] = set()
    provenance_failures: list[str] = []
    for row in sample["rows"]:
        accession = str(row["accession"])
        source = root / "staging/sample-evidence" / f"{accession}.jsonl"
        destination = root / "selective/sample-evidence" / f"{accession}.jsonl"
        retained: list[bytes] = []
        if source.is_file():
            for line in source.read_bytes().splitlines():
                evidence = json.loads(line)
                fact = evidence["fact"]
                namespace = str(fact.get("taxonomy_namespace") or "")
                raw_concept = str(fact.get("concept") or "")
                concept = f"{namespace}:{raw_concept}" if namespace else raw_concept
                upstream_standard = mapper.map_concept(concept, raw_concept, {})
                if project_edgartools_standard_concept(upstream_standard) is None:
                    continue
                if (
                    evidence.get("filing", {}).get("accession") != accession
                    or not evidence.get("filing", {}).get("acceptance_datetime")
                    or not evidence.get("source", {}).get("source_document_identity")
                    or not evidence.get("source", {}).get("source_document_url")
                    or not re.fullmatch(
                        r"[0-9a-f]{64}",
                        str(evidence.get("source", {}).get("source_document_sha256") or ""),
                    )
                ):
                    provenance_failures.append(accession)
                    continue
                retained.append(line + b"\n")
        payload = b"".join(retained)
        destination.write_bytes(payload)
        selected_evidence_count += len(retained)
        selected_evidence_bytes += len(payload)
        if retained:
            selected_accessions.add(accession)

        event_source = root / "staging/sample-events" / f"{accession}.jsonl"
        event_destination = root / "selective/sample-events" / f"{accession}.jsonl"
        event_payload = event_source.read_bytes() if event_source.is_file() else b""
        event_destination.write_bytes(event_payload)
        selected_event_count += len(event_payload.splitlines())
        selected_event_bytes += len(event_payload)
    if provenance_failures:
        raise RuntimeError(
            "selective sample lost exact accession/source provenance: "
            + ",".join(sorted(set(provenance_failures)))
        )
    sample_report = {
        "schema": "AQ_P5_EDGARTOOLS_ENTITYFACTS_SELECTIVE_SAMPLE_V1",
        "sample_identity": "sha256:a0e66a31b443ef4a8dae69d7d585c197f7d0f615e9870a055b40aac6893caaf3",
        "sampled_accession_count": 32,
        "old_all_numeric_fact_count": 59315,
        "new_authorized_raw_fact_count": selected_evidence_count,
        "new_fundamental_evidence_count": selected_evidence_count,
        "new_unique_required_accession_count": len(selected_accessions),
        "standardized_event_count": selected_event_count,
        "exact_accession_provenance_preserved": True,
        "evidence_bytes": selected_evidence_bytes,
        "event_bytes": selected_event_bytes,
    }
    write_json_atomic(root / "reports/entityfacts_selective_sample.json", sample_report)

    original_inventory = json.loads(original_inventory_path.read_text(encoding="utf-8"))
    size_by_accession = {
        str(row["accession"]): int(row["source_size_bytes"])
        for row in original_inventory["rows"]
        if row.get("source_size_bytes") is not None
    }
    required_accessions = [str(row["accession"]) for row in census["rows"]]
    known_sizes = [size_by_accession[value] for value in required_accessions if value in size_by_accession]
    missing_size_count = len(required_accessions) - len(known_sizes)
    missing_size_estimate = percentile(known_sizes, 0.95) if known_sizes else 0
    estimated_network = sum(known_sizes) + missing_size_count * missing_size_estimate
    total_selected_facts = int(census["entityfacts_selected_fact_count"])
    evidence_per_fact = selected_evidence_bytes / selected_evidence_count if selected_evidence_count else 0
    event_per_fact = selected_event_bytes / selected_evidence_count if selected_evidence_count else 0
    projected_evidence = int(round(total_selected_facts * evidence_per_fact))
    projected_events = int(round(total_selected_facts * event_per_fact))
    metadata_paths = [root / "selective/entityfacts_selective_accessions.json"]
    metadata_paths.extend((root / "selective/cik").glob("*.json"))
    metadata_paths.append(root / "reports/entityfacts_selective_sample.json")
    projected_metadata = sum(path.stat().st_size for path in metadata_paths if path.is_file())
    projected_projection = RESERVED_SESSION_PROJECTION_BYTES
    projected_persistent = (
        projected_evidence
        + projected_events
        + projected_projection
        + projected_metadata
        + RESERVED_MANIFEST_DVC_BYTES
    )
    projected_total_peak = projected_persistent + max(
        RESERVED_BUILD_TEMP_BYTES, MAX_ACTIVE_BATCH_SOURCE_BYTES
    )
    storage_status = (
        "PASS"
        if projected_persistent <= MAX_PERSISTENT_BYTES
        and projected_total_peak <= MAX_PEAK_BYTES
        else "BLOCKED_STORAGE_PREFLIGHT"
    )
    storage = {
        "schema": "AQ_P5_EDGARTOOLS_ENTITYFACTS_SELECTIVE_STORAGE_PREFLIGHT_V1",
        "source_storage_architecture": "REMOTE_FIRST_BOUNDED_CACHE",
        "projected_selective_evidence_bytes": projected_evidence,
        "projected_event_bytes": projected_events,
        "projected_projection_bytes": projected_projection,
        "projected_metadata_bytes": projected_metadata,
        "projected_persistent_bytes": projected_persistent,
        "projected_active_cache_peak_bytes": MAX_ACTIVE_BATCH_SOURCE_BYTES,
        "projected_total_peak_bytes": projected_total_peak,
        "estimated_one_time_network_bytes": estimated_network,
        "network_size_known_accession_count": len(known_sizes),
        "network_size_missing_accession_count": missing_size_count,
        "network_missing_accession_p95_estimate_bytes": missing_size_estimate,
        "target_max_persistent_bytes": MAX_PERSISTENT_BYTES,
        "target_max_peak_bytes": MAX_PEAK_BYTES,
        "storage_preflight": storage_status,
    }
    write_json_atomic(root / "reports/entityfacts_selective_storage_preflight.json", storage)
    report = {
        "schema": "AQ_P5_EDGARTOOLS_ENTITYFACTS_FIRST_REALIGNMENT_V1",
        **{key: value for key, value in census.items() if key != "rows"},
        **sample_report,
        **storage,
        "native_accession_superset_count": 36582,
        "accession_reduction_count": 36582 - int(census["selective_required_accession_count"]),
        "accession_reduction_rate": (
            (36582 - int(census["selective_required_accession_count"])) / 36582
        ),
        "selected_historical_build_path": "EDGARTOOLS_ENTITYFACTS_FIRST_SELECTIVE_BACKFILL",
        "broad_accession_acquisition_started": False,
        "full_historical_build_started": False,
    }
    write_json_atomic(root / "reports/entityfacts_first_realign_report.json", report)
    manifest = hash_inventory(
        root,
        exclude_names=("entityfacts_selective_manifest.json",),
        exclude_prefixes=(
            "staging/sample-source",
            "staging/edgar-data",
            "staging/edgar-object-cache",
        ),
    )
    manifest.update(
        {
            "selective_required_accession_count": census["selective_required_accession_count"],
            "ordinary_source_cache_dvc_sealed": False,
        }
    )
    write_json_atomic(root / "manifests/entityfacts_selective_manifest.json", manifest)
    return report


def run_sample(root: Path, *, target_count: int) -> dict[str, Any]:
    configure_edgar(root)
    inventory_path = root / "inventory/accession_inventory.json"
    if not inventory_path.is_file():
        raise RuntimeError("run inventory before sample")
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    if inventory["failed_cik_count"]:
        raise RuntimeError("native inventory has failed CIKs")
    sample = select_stratified_sample(inventory["rows"], target_count=target_count)
    write_json_atomic(
        root / "reports/stratified_sample_inventory.json",
        {
            "schema": "AQ_P5_EDGARTOOLS_NATIVE_STRATIFIED_SAMPLE_V1",
            "selection_rule": "deterministic native type, amendment, year, issuer-family and provider-size strata plus hash fill",
            "target_count": target_count,
            "sample_count": len(sample),
            "rows": sample,
        },
    )
    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for sequence, row in enumerate(sample, 1):
        try:
            result = parse_sample_accession(root, row)
            results.append(result)
            status = result["terminal_state"]
        except Exception as exc:
            failure = failure_record(
                accession=str(row["accession"]),
                cik=str(row["cik"]),
                stage="STRATIFIED_SOURCE_BYTE_SAMPLE",
                error=exc,
                attempts=1,
            )
            failures.append(failure)
            write_json_atomic(root / "failures" / f"sample-{row['accession']}.json", failure)
            status = failure["terminal_state"]
        print(
            json.dumps(
                {
                    "stage": "sample",
                    "sequence": sequence,
                    "total": len(sample),
                    "accession": row["accession"],
                    "status": status,
                }
            ),
            flush=True,
        )
    terminal_counts = Counter(str(row["terminal_state"]) for row in results)
    failure_counts = Counter(str(row["terminal_state"]) for row in failures)
    sample_doc = {
        "schema": "AQ_P5_EDGARTOOLS_NATIVE_STRATIFIED_SAMPLE_RESULTS_V1",
        "sample_count": len(sample),
        "completed_count": len(results),
        "failure_count": len(failures),
        "dimension_bearing_sample_count": sum(
            int(row["dimension_bearing_raw_fact_count"] > 0) for row in results
        ),
        "terminal_state_counts": dict(sorted(terminal_counts.items())),
        "failure_state_counts": dict(sorted(failure_counts.items())),
        "non_numeric_fact_skipped_count": sum(
            int(row.get("non_numeric_fact_skipped_count") or 0) for row in results
        ),
        "nil_fact_skipped_count": sum(
            int(row.get("nil_fact_skipped_count") or 0) for row in results
        ),
        "numeric_fact_selected_count": sum(
            int(row.get("numeric_fact_selected_count") or 0) for row in results
        ),
        "numeric_fact_canonicalization_failure_count": sum(
            int(row.get("numeric_fact_canonicalization_failure_count") or 0)
            for row in results
        )
        + sum(
            int(row.get("error_class") == "NumericFactCanonicalizationError")
            for row in failures
        ),
        "rows": results,
        "failures": failures,
    }
    write_json_atomic(root / "reports/stratified_sample_results.json", sample_doc)
    if failures or not sample_doc["dimension_bearing_sample_count"]:
        storage = {
            "schema": "AQ_P5_EDGARTOOLS_REMOTE_FIRST_STORAGE_PREFLIGHT_V2",
            "storage_preflight": "BLOCKED_SOURCE_AUTHORITY_GAP",
            "sample_failure_count": len(failures),
        }
        write_json_atomic(root / "reports/storage_preflight.json", storage)
    else:
        storage = remote_first_storage_projection(root)
    print(json.dumps(storage, indent=2, sort_keys=True), flush=True)
    return storage


def runtime_report(root: Path) -> dict[str, object]:
    packages = {}
    for name in ("edgartools", "pyarrow", "pandas", "exchange-calendars"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    report = {
        "schema": "AQ_P5_EDGARTOOLS_NATIVE_BUILD_RUNTIME_V1",
        "python": sys.version,
        "executable": sys.executable,
        "packages": packages,
        "build_root": str(root),
        "start_available_disk_bytes": shutil.disk_usage(root).free,
        "network_identity_configured": bool(load_identity()),
        "credentials_recorded": False,
    }
    write_json_atomic(root / "reports/runtime.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("inventory", "sample", "reaccount", "selective", "all"),
    )
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--sample-count", type=int, default=32)
    args = parser.parse_args()
    prepare(args.root)
    runtime_report(args.root)
    if args.command in {"inventory", "all"}:
        enumerate_inventory(args.root)
    if args.command in {"sample", "all"}:
        run_sample(args.root, target_count=args.sample_count)
    elif args.command == "reaccount":
        print(
            json.dumps(remote_first_storage_projection(args.root), indent=2, sort_keys=True),
            flush=True,
        )
    elif args.command == "selective":
        entityfacts_selective_census(args.root)
        print(
            json.dumps(selective_sample_and_storage(args.root), indent=2, sort_keys=True),
            flush=True,
        )


if __name__ == "__main__":
    main()
