"""Bounded orchestration for the frozen EdgarTools-native P5 build.

This module owns build accounting, deterministic sampling, checkpoint identity,
and storage admission only. SEC transport, filing parsing, XBRL parsing, fact
materialization, PIT policy, session calendars, persistence, and research
consumption remain with their frozen upstream/project owners.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BUILD_SPEC_VERSION = "AQ_P5_EDGARTOOLS_NATIVE_FULL_BUILD_V1"
EDGARTOOLS_VERSION = "5.58.0"
TOTAL_P1_EPISODES = 832
BOUND_EPISODES = 721
FINAL_BINDING_RECORDS = 722
UNIQUE_BOUND_CIK_COUNT = 711
IDENTITY_EXCLUSION_EPISODES = 111
HISTORY_START = "1994-01-01"
HISTORY_END = "2024-12-31"
MAX_ENUMERATION_CIKS = 25
MAX_EXTRACTION_ACCESSIONS = 200
MAX_ACTIVE_BATCH_SOURCE_BYTES = 2 * 1024**3
MAX_PERSISTENT_BYTES = 176 * 1024**3
MAX_PEAK_BYTES = 192 * 1024**3
PROJECT_STORAGE_BYTES = 256 * 1024**3
RESERVED_SESSION_PROJECTION_BYTES = 20 * 1024**3
RESERVED_MANIFEST_DVC_BYTES = 4 * 1024**3
RESERVED_BUILD_TEMP_BYTES = 16 * 1024**3
NATIVE_PERIODIC_OBJECT_TYPES = frozenset({"TenK", "TenQ", "TwentyF", "FortyF"})
TERMINAL_STATES = frozenset(
    {
        "COMPLETE_WITH_EVIDENCE",
        "COMPLETE_NO_AUTHORIZED_FACTS",
        "COMPLETE_NO_STRUCTURED_FINANCIALS",
        "SKIPPED_OUTSIDE_AUTHORIZED_HISTORY",
        "FAILED_TRANSIENT",
        "FAILED_DETERMINISTIC",
        "FAILED_REQUIRED_ACCESSION",
    }
)
REUSABLE_TERMINAL_STATES = TERMINAL_STATES - {
    "FAILED_TRANSIENT",
    "FAILED_DETERMINISTIC",
    "FAILED_REQUIRED_ACCESSION",
}
NON_NUMERIC_FACT_NOT_ELIGIBLE = "NON_NUMERIC_FACT_NOT_ELIGIBLE_FOR_NUMERIC_EVIDENCE"
NIL_FACT_NOT_ELIGIBLE = "NIL_FACT_NOT_ELIGIBLE_FOR_NUMERIC_EVIDENCE"
NUMERIC_FACT_SELECTED = "NUMERIC_FACT_SELECTED"
REACQUIRABLE_SOURCE_CACHE = "REACQUIRABLE_SOURCE_CACHE"
NON_REACQUIRABLE_OR_ADJUDICATION_SOURCE = "NON_REACQUIRABLE_OR_ADJUDICATION_SOURCE"

# This is a projection from EdgarTools' public StandardConcept enum into the
# already-frozen AQ feature identifiers.  It is deliberately not a raw XBRL
# alias table: EdgarTools alone maps issuer tags/labels to these values.
EDGARTOOLS_STANDARD_CONCEPT_PROJECTION = {
    "Revenue": "Revenue",
    "Net Income": "NetIncome",
    "Total Assets": "Assets",
    "Total Liabilities": "Liabilities",
    "Total Stockholders' Equity": "CommonEquity",
    "Net Cash from Operating Activities": "NetCashFromOperatingActivities",
    "Cash and Cash Equivalents": "CashAndCashEquivalents",
    "Total Current Assets": "CurrentAssetsTotal",
    "Total Current Liabilities": "CurrentLiabilitiesTotal",
    "Short Term Debt": "ShortTermDebt",
    "Long Term Debt": "LongTermDebt",
}
AUTHORIZED_ENTITYFACTS_FORMS = frozenset(
    {
        "10-K",
        "10-K/A",
        "10-Q",
        "10-Q/A",
        "20-F",
        "20-F/A",
        "40-F",
        "40-F/A",
        "6-K",
        "6-K/A",
    }
)


class NumericFactCanonicalizationError(ValueError):
    """A native numeric XBRL fact cannot satisfy the exact-decimal contract."""


class SourceHashMismatchError(ValueError):
    """Reacquired SEC bytes differ from the hash sealed with the evidence."""


def exact_decimal(value: object) -> str:
    """Return the exact canonical decimal spelling used by the build boundary."""

    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise NumericFactCanonicalizationError(
            "upstream-classified numeric fact has an invalid decimal representation"
        ) from exc
    if not decimal.is_finite():
        raise NumericFactCanonicalizationError(
            "upstream-classified numeric fact is not finite"
        )
    text = format(decimal, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text in {"", "-0"} else text


def select_numeric_fact_value(fact: Mapping[str, object]) -> tuple[str, str | None]:
    """Apply EdgarTools-native numeric semantics before AQ decimal admission.

    EdgarTools 5.58.0 documents ``numeric_value is None`` as the marker for a
    non-numeric fact. Its instance parser also treats ``unitRef`` as the XBRL
    numeric-item marker. The parsed float is used only for eligibility; AQ
    canonicalizes the original filed string so no float precision is admitted.
    """

    value = fact.get("value")
    native_numeric_value = fact.get("numeric_value")
    unit_ref = fact.get("unit_ref")
    if value is None or value == "":
        return NIL_FACT_NOT_ELIGIBLE, None
    if native_numeric_value is None and unit_ref is None:
        return NON_NUMERIC_FACT_NOT_ELIGIBLE, None
    return NUMERIC_FACT_SELECTED, exact_decimal(value)


def project_edgartools_standard_concept(
    upstream_standard_concept: str | None,
) -> str | None:
    """Project an upstream StandardConcept value onto the frozen AQ vocabulary."""

    if upstream_standard_concept is None:
        return None
    return EDGARTOOLS_STANDARD_CONCEPT_PROJECTION.get(upstream_standard_concept)


def selective_policy_identity() -> str:
    """Hash the complete finite EntityFacts selection authority."""

    policy = {
        "schema": "AQ_P5_EDGARTOOLS_ENTITYFACTS_SELECTIVE_POLICY_V1",
        "edgartools_version": EDGARTOOLS_VERSION,
        "history": [HISTORY_START, HISTORY_END],
        "authorized_forms": sorted(AUTHORIZED_ENTITYFACTS_FORMS),
        "standard_concept_projection": dict(
            sorted(EDGARTOOLS_STANDARD_CONCEPT_PROJECTION.items())
        ),
        "numeric_eligibility": "EDGARTOOLS_NATIVE_NUMERIC_VALUE_NOT_NULL",
    }
    return "sha256:" + sha256_bytes(canonical_json_bytes(policy))


def select_authorized_entityfacts(
    facts: Iterable[Mapping[str, object]],
    *,
    map_concept: Any,
    history_start: str = HISTORY_START,
    history_end: str = HISTORY_END,
) -> list[dict[str, object]]:
    """Select authorized upstream facts before any filing-source acquisition.

    ``map_concept`` must be EdgarTools' native ``ConceptMapper.map_concept``.
    AQ supplies only its finite authorized StandardConcept projection and
    historical/form eligibility.  It does not map raw issuer tags itself.
    """

    selected: list[dict[str, object]] = []
    mapped_concepts: dict[tuple[str, str], str | None] = {}
    for raw in facts:
        form = str(raw.get("form_type") or raw.get("form") or "")
        filing_date = str(raw.get("filing_date") or "")
        accession = str(raw.get("accession") or "")
        numeric_value = raw.get("numeric_value")
        value = raw.get("value")
        if (
            form not in AUTHORIZED_ENTITYFACTS_FORMS
            or not accession
            or not filing_date
            or filing_date < history_start
            or filing_date > history_end
            or numeric_value is None
            or value is None
        ):
            continue
        concept = str(raw.get("concept") or "")
        label = str(raw.get("label") or concept)
        mapping_key = (concept, label)
        if mapping_key not in mapped_concepts:
            mapped_concepts[mapping_key] = map_concept(concept, label, {})
        upstream_standard = mapped_concepts[mapping_key]
        standard = project_edgartools_standard_concept(upstream_standard)
        if standard is None:
            continue
        selected.append(
            {
                "accession": accession,
                "concept": concept,
                "taxonomy": str(raw.get("taxonomy") or concept.partition(":")[0]),
                "standard_concept": standard,
                "upstream_standard_concept": upstream_standard,
                "form": form,
                "filing_date": filing_date,
                "period_type": scalar(raw.get("period_type")),
                "period_start": scalar(raw.get("period_start")),
                "period_end": scalar(raw.get("period_end")),
                "unit": scalar(raw.get("unit")),
                "context_ref": scalar(raw.get("context_ref")),
                "dimensions": raw.get("dimensions") or {},
            }
        )
    return selected


def canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_provenance_record(
    *,
    accession: str,
    cik: str,
    source_document_identity: str,
    source_document_url: str,
    source_document_sha256: str,
    source_byte_count: int,
    storage_class: str = REACQUIRABLE_SOURCE_CACHE,
) -> dict[str, object]:
    """Project immutable source provenance without retaining ordinary source bytes."""

    if not re.fullmatch(r"[0-9a-f]{64}", source_document_sha256):
        raise ValueError("source SHA-256 is not canonical lowercase hex")
    if storage_class not in {
        REACQUIRABLE_SOURCE_CACHE,
        NON_REACQUIRABLE_OR_ADJUDICATION_SOURCE,
    }:
        raise ValueError("unknown source storage class")
    return {
        "accession": accession,
        "cik": cik,
        "source_document_identity": source_document_identity,
        "source_document_url": source_document_url,
        "source_document_sha256": source_document_sha256,
        "source_byte_count": source_byte_count,
        "source_storage_class": storage_class,
    }


def verify_reacquired_source(
    provenance: Mapping[str, object], payload: bytes
) -> bool:
    """Fail closed unless reacquired SEC bytes equal the sealed source identity."""

    expected_hash = str(provenance.get("source_document_sha256") or "")
    expected_bytes = int(provenance.get("source_byte_count") or -1)
    if sha256_bytes(payload) != expected_hash or len(payload) != expected_bytes:
        raise SourceHashMismatchError("reacquired SEC source bytes do not match sealed provenance")
    return True


def source_cache_evictable(
    checkpoint: Mapping[str, object], *, output_paths: Mapping[str, Path]
) -> bool:
    """Allow ordinary cache eviction only after every derived output is sealed."""

    if checkpoint.get("source_storage_class") != REACQUIRABLE_SOURCE_CACHE:
        return False
    if checkpoint.get("terminal_state") not in REUSABLE_TERMINAL_STATES:
        return False
    if checkpoint.get("evidence_sealed") is not True:
        return False
    source_hash = str(checkpoint.get("source_document_sha256") or "")
    if not re.fullmatch(r"[0-9a-f]{64}", source_hash):
        return False
    expected_outputs = checkpoint.get("output_hashes")
    if not isinstance(expected_outputs, Mapping) or set(expected_outputs) != set(output_paths):
        return False
    return all(
        path.is_file() and sha256_file(path) == expected_outputs[key]
        for key, path in output_paths.items()
    )


def write_json_atomic(path: Path, value: object) -> str:
    payload = canonical_json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_suffix(path.suffix + ".staging")
    staging.write_bytes(payload)
    staging.replace(path)
    return sha256_bytes(payload)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def scalar(value: object) -> object:
    if value is None:
        return None
    if hasattr(value, "item"):
        value = value.item()
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def load_authority(
    *,
    episodes_path: Path,
    bindings_path: Path,
    exclusions_path: Path,
    expected_binding_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Load and reconcile the frozen 832-episode identity population."""

    if sha256_file(bindings_path) != expected_binding_sha256:
        raise RuntimeError("binding ledger hash mismatch")
    episodes = read_jsonl(episodes_path)
    bindings = read_json(bindings_path)["records"]
    exclusions = read_json(exclusions_path)["records"]
    bound_ids = {row["episode_id"] for row in bindings}
    excluded_ids = {row["episode_id"] for row in exclusions}
    episode_ids = {row["episode_id"] for row in episodes}
    if len(episodes) != TOTAL_P1_EPISODES:
        raise RuntimeError("P1 episode count mismatch")
    if len(bindings) != FINAL_BINDING_RECORDS or len(bound_ids) != BOUND_EPISODES:
        raise RuntimeError("binding authority count mismatch")
    if len(exclusions) != IDENTITY_EXCLUSION_EPISODES:
        raise RuntimeError("identity exclusion count mismatch")
    if len({row["cik"] for row in bindings}) != UNIQUE_BOUND_CIK_COUNT:
        raise RuntimeError("bound CIK count mismatch")
    if bound_ids & excluded_ids or bound_ids | excluded_ids != episode_ids:
        raise RuntimeError("identity population is not disjoint and complete")
    return episodes, bindings, exclusions


def build_spec_identity(authority_hashes: Mapping[str, str]) -> str:
    spec = {
        "schema": BUILD_SPEC_VERSION,
        "edgartools_version": EDGARTOOLS_VERSION,
        "history": [HISTORY_START, HISTORY_END],
        "population": {
            "episodes": TOTAL_P1_EPISODES,
            "bound_episodes": BOUND_EPISODES,
            "binding_records": FINAL_BINDING_RECORDS,
            "bound_ciks": UNIQUE_BOUND_CIK_COUNT,
            "exclusions": IDENTITY_EXCLUSION_EPISODES,
        },
        "batch_limits": {
            "enumeration_ciks": MAX_ENUMERATION_CIKS,
            "extraction_accessions": MAX_EXTRACTION_ACCESSIONS,
            "active_source_bytes": MAX_ACTIVE_BATCH_SOURCE_BYTES,
        },
        "storage_limits": {
            "persistent": MAX_PERSISTENT_BYTES,
            "peak": MAX_PEAK_BYTES,
            "project": PROJECT_STORAGE_BYTES,
        },
        "authority_hashes": dict(sorted(authority_hashes.items())),
    }
    return "sha256:" + sha256_bytes(canonical_json_bytes(spec))


def is_native_financial_candidate(
    *, native_object_type: str | None, form: str, is_xbrl: bool
) -> bool:
    """Apply upstream object capability plus the frozen structured-6-K boundary."""

    if not is_xbrl or native_object_type is None:
        return False
    if native_object_type in NATIVE_PERIODIC_OBJECT_TYPES:
        return True
    return native_object_type == "CurrentReport" and form.split("/", 1)[0] == "6-K"


def accession_metadata_row(
    raw: Mapping[str, object],
    *,
    cik: str,
    issuer_name: str,
    issuer_family: str,
    native_object_type: str | None,
) -> dict[str, object]:
    form = str(raw.get("form") or "")
    accession = str(raw.get("accession_number") or raw.get("accession") or "")
    is_xbrl = bool(raw.get("isXBRL") or raw.get("is_xbrl"))
    return {
        "accession": accession,
        "cik": str(cik).zfill(10),
        "issuer_name": issuer_name,
        "issuer_family": issuer_family,
        "form": form,
        "filing_date": scalar(raw.get("filing_date")),
        "acceptance_datetime": scalar(
            raw.get("acceptanceDateTime") or raw.get("acceptance_datetime")
        ),
        "report_period": scalar(raw.get("reportDate") or raw.get("report_period")),
        "primary_document": scalar(
            raw.get("primaryDocument") or raw.get("primary_document")
        ),
        "source_size_bytes": scalar(raw.get("size") or raw.get("source_size_bytes")),
        "is_xbrl": is_xbrl,
        "is_inline_xbrl": bool(raw.get("isInlineXBRL") or raw.get("is_inline_xbrl")),
        "native_object_type": native_object_type,
        "native_financial_candidate": is_native_financial_candidate(
            native_object_type=native_object_type, form=form, is_xbrl=is_xbrl
        ),
        "amendment": form.endswith("/A"),
    }


def deduplicate_accessions(rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Deduplicate filings while retaining every bound-CIK observation.

    SEC submissions history can expose the same filing accession through more
    than one related bound issuer. CIK/name/family are therefore observation
    metadata, not accession-level filing metadata. A CIK chosen for retrieval
    is only a transport hint; downloaded SEC bytes remain authoritative.
    """

    by_accession: dict[str, dict[str, object]] = {}
    observations: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for raw in rows:
        row = dict(raw)
        accession = str(row.get("accession") or "")
        if not accession:
            raise ValueError("candidate filing is missing accession")
        observations[accession].append(
            {
                "cik": str(row.get("cik") or ""),
                "issuer_name": row.get("issuer_name"),
                "issuer_family": row.get("issuer_family"),
            }
        )
        prior = by_accession.get(accession)
        if prior is None:
            by_accession[accession] = row
            continue
        compared = {
            key: row.get(key)
            for key in (
                "form",
                "filing_date",
                "acceptance_datetime",
                "report_period",
                "native_object_type",
            )
        }
        prior_compared = {key: prior.get(key) for key in compared}
        if compared != prior_compared:
            raise ValueError(f"conflicting accession metadata: {accession}")

    unique: list[dict[str, object]] = []
    for accession, row in by_accession.items():
        observed = sorted(
            observations[accession],
            key=lambda value: (
                str(value.get("cik") or ""),
                str(value.get("issuer_name") or ""),
                str(value.get("issuer_family") or ""),
            ),
        )
        observed_ciks = sorted({str(value["cik"]) for value in observed if value.get("cik")})
        if not observed_ciks:
            raise ValueError(f"candidate filing is missing observed CIK: {accession}")
        accession_prefix_cik = accession.split("-", 1)[0].zfill(10)
        retrieval_cik = (
            accession_prefix_cik
            if accession_prefix_cik in observed_ciks
            else observed_ciks[0]
        )
        retrieval_observation = next(value for value in observed if value["cik"] == retrieval_cik)
        unique.append(
            {
                **row,
                "cik": retrieval_cik,
                "issuer_name": retrieval_observation.get("issuer_name"),
                "issuer_family": retrieval_observation.get("issuer_family"),
                "observed_for_bound_ciks": observed_ciks,
                "observations": observed,
                "accession_prefix_cik_non_authoritative": accession_prefix_cik,
                "retrieval_cik_hint": retrieval_cik,
                "retrieval_cik_hint_role": (
                    "NON_AUTHORITATIVE_TRANSPORT_HINT_VALIDATED_AGAINST_SOURCE"
                ),
            }
        )
    return sorted(
        unique,
        key=lambda row: (
            str(row.get("acceptance_datetime") or ""),
            str(row.get("cik") or ""),
            str(row["accession"]),
        ),
    )


def _sample_score(accession: str, label: str) -> str:
    return hashlib.sha256(f"{BUILD_SPEC_VERSION}|{label}|{accession}".encode()).hexdigest()


def select_stratified_sample(
    inventory: Sequence[Mapping[str, object]], *, target_count: int = 32
) -> list[dict[str, object]]:
    """Select a deterministic, non-small-biased native-financial sample."""

    candidates = [dict(row) for row in inventory if row.get("native_financial_candidate")]
    if not candidates:
        raise ValueError("native financial inventory is empty")
    selected: dict[str, dict[str, object]] = {}

    def add(rows: Sequence[dict[str, object]], label: str, *, largest: bool = False) -> None:
        if not rows:
            return
        if largest:
            chosen = max(
                rows,
                key=lambda row: (
                    int(row.get("source_size_bytes") or 0), str(row["accession"])
                ),
            )
        else:
            chosen = min(rows, key=lambda row: _sample_score(str(row["accession"]), label))
        accession = str(chosen["accession"])
        admitted = selected.setdefault(accession, {**chosen, "sample_reasons": []})
        admitted["sample_reasons"] = sorted(set(admitted["sample_reasons"]) | {label})

    add([row for row in candidates if row.get("native_object_type") == "TenK" and not row.get("amendment")], "DOMESTIC_10K")
    add([row for row in candidates if row.get("native_object_type") == "TenQ" and not row.get("amendment")], "DOMESTIC_10Q")
    add([row for row in candidates if row.get("amendment")], "AMENDMENT")
    add([row for row in candidates if row.get("native_object_type") == "TwentyF"], "FOREIGN_20F")
    add(
        [
            row
            for row in candidates
            if row.get("native_object_type") == "CurrentReport"
            and str(row.get("form") or "").split("/", 1)[0] == "6-K"
        ],
        "STRUCTURED_6K",
    )
    dated = [row for row in candidates if row.get("filing_date")]
    if dated:
        earliest_year = min(str(row["filing_date"])[:4] for row in dated)
        latest_year = max(str(row["filing_date"])[:4] for row in dated)
        add([row for row in dated if str(row["filing_date"]).startswith(earliest_year)], "OLDEST_ACCEPTANCE_YEAR")
        add([row for row in dated if str(row["filing_date"]).startswith(latest_year)], "LATEST_ACCEPTANCE_YEAR")
        for year in sorted({str(row["filing_date"])[:4] for row in dated})[::3]:
            add([row for row in dated if str(row["filing_date"]).startswith(year)], f"YEAR_{year}")
    positive_sizes = sorted(
        (row for row in candidates if int(row.get("source_size_bytes") or 0) > 0),
        key=lambda row: (int(row.get("source_size_bytes") or 0), str(row["accession"])),
    )
    if positive_sizes:
        add([positive_sizes[0]], "SMALLEST_PROVIDER_REPORTED")
        add([positive_sizes[len(positive_sizes) // 2]], "MEDIAN_PROVIDER_REPORTED")
        add([positive_sizes[math.ceil(0.90 * len(positive_sizes)) - 1]], "P90_PROVIDER_REPORTED")
        add([positive_sizes[math.ceil(0.95 * len(positive_sizes)) - 1]], "P95_PROVIDER_REPORTED")
        add(positive_sizes, "LARGEST_PROVIDER_REPORTED", largest=True)
    for family in sorted({str(row.get("issuer_family") or "") for row in candidates}):
        add([row for row in candidates if row.get("issuer_family") == family], f"ISSUER_FAMILY_{family}")
    remaining = sorted(
        (row for row in candidates if str(row["accession"]) not in selected),
        key=lambda row: _sample_score(str(row["accession"]), "FILL"),
    )
    for row in remaining:
        if len(selected) >= target_count:
            break
        add([row], "DETERMINISTIC_FILL")
    return sorted(
        selected.values(),
        key=lambda row: (str(row.get("filing_date") or ""), str(row["accession"])),
    )


def percentile(values: Sequence[int], fraction: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    return int(ordered[min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)])


def _upper_mean(values: Sequence[int]) -> int:
    if not values:
        raise ValueError("storage projection requires a nonempty sample")
    mean = statistics.fmean(values)
    standard_error = statistics.stdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0
    return math.ceil(max(mean + 1.96 * standard_error, percentile(values, 0.90)))


def project_storage(
    *,
    candidate_count: int,
    sample_results: Sequence[Mapping[str, object]],
    inventory_bytes: int,
    sampled_manifest_checkpoint_bytes: int = 0,
    estimated_one_time_network_bytes: int | None = None,
) -> dict[str, object]:
    """Project remote-first persistent and peak gates from the sealed sample."""

    source_values = [int(row["source_bytes"]) for row in sample_results]
    evidence_values = [int(row["evidence_bytes"]) for row in sample_results]
    event_values = [int(row["event_bytes"]) for row in sample_results]
    projection_values = [int(row.get("projection_bytes") or 0) for row in sample_results]
    exception_source_values = [
        int(row.get("required_exception_source_bytes") or 0) for row in sample_results
    ]
    persistent_values = [
        evidence + event + projection + exception_source
        for evidence, event, projection, exception_source in zip(
            evidence_values,
            event_values,
            projection_values,
            exception_source_values,
        )
    ]
    evidence_upper = _upper_mean(evidence_values)
    event_upper = _upper_mean(event_values)
    exception_source_upper = max(exception_source_values, default=0)
    projected_evidence = evidence_upper * candidate_count
    projected_events = event_upper * candidate_count
    projected_exception_source = exception_source_upper * candidate_count
    projected_persistent = (
        projected_evidence
        + projected_events
        + projected_exception_source
        + inventory_bytes
        + RESERVED_SESSION_PROJECTION_BYTES
        + RESERVED_MANIFEST_DVC_BYTES
    )
    largest_sample_source = max(source_values, default=0)
    projected_active_cache_peak = max(
        largest_sample_source,
        MAX_ACTIVE_BATCH_SOURCE_BYTES if source_values else 0,
    )
    projected_total_peak = projected_persistent + max(
        RESERVED_BUILD_TEMP_BYTES, projected_active_cache_peak
    )
    status = (
        "PASS"
        if projected_persistent <= MAX_PERSISTENT_BYTES
        and projected_total_peak <= MAX_PEAK_BYTES
        else "BLOCKED_STORAGE_PREFLIGHT"
    )
    network_bytes = (
        estimated_one_time_network_bytes
        if estimated_one_time_network_bytes is not None
        else _upper_mean(source_values) * candidate_count
    )
    return {
        "schema": "AQ_P5_EDGARTOOLS_REMOTE_FIRST_STORAGE_PREFLIGHT_V2",
        "source_storage_architecture": "REMOTE_FIRST_BOUNDED_CACHE",
        "candidate_accession_count": candidate_count,
        "sampled_accession_count": len(sample_results),
        "sampled_raw_source_cache_bytes": sum(source_values),
        "sampled_persistent_evidence_bytes": sum(evidence_values),
        "sampled_standardized_event_bytes": sum(event_values),
        "sampled_projection_bytes": sum(projection_values),
        "sampled_manifest_checkpoint_bytes": sampled_manifest_checkpoint_bytes,
        "sampled_required_exception_source_bytes": sum(exception_source_values),
        "sampled_persistent_bytes": sum(persistent_values)
        + sampled_manifest_checkpoint_bytes,
        "median_persistent_bytes": percentile(persistent_values, 0.50),
        "p90_persistent_bytes": percentile(persistent_values, 0.90),
        "p95_persistent_bytes": percentile(persistent_values, 0.95),
        "max_persistent_bytes": max(persistent_values),
        "per_accession_upper_evidence_bytes": evidence_upper,
        "per_accession_upper_event_bytes": event_upper,
        "per_accession_upper_exception_source_bytes": exception_source_upper,
        "projected_evidence_bytes": projected_evidence,
        "projected_event_bytes": projected_events,
        "projected_required_exception_source_bytes": projected_exception_source,
        "inventory_bytes": inventory_bytes,
        "reserved_session_projection_bytes": RESERVED_SESSION_PROJECTION_BYTES,
        "reserved_manifest_dvc_bytes": RESERVED_MANIFEST_DVC_BYTES,
        "reserved_build_temp_bytes": RESERVED_BUILD_TEMP_BYTES,
        "projected_persistent_bytes": projected_persistent,
        "projected_active_cache_peak_bytes": projected_active_cache_peak,
        "projected_total_peak_bytes": projected_total_peak,
        "estimated_one_time_network_bytes": network_bytes,
        "target_max_persistent_bytes": MAX_PERSISTENT_BYTES,
        "target_max_peak_bytes": MAX_PEAK_BYTES,
        "project_storage_constraint_bytes": PROJECT_STORAGE_BYTES,
        "storage_preflight": status,
    }


def checkpoint_identity(
    *,
    build_spec_id: str,
    accession: str,
    source_sha256: str,
    output_hashes: Mapping[str, str],
) -> str:
    payload = {
        "build_spec_identity": build_spec_id,
        "accession": accession,
        "source_sha256": source_sha256,
        "output_hashes": dict(sorted(output_hashes.items())),
    }
    return "sha256:" + sha256_bytes(canonical_json_bytes(payload))


def checkpoint_reusable(
    checkpoint: Mapping[str, object],
    *,
    build_spec_id: str,
    source_path: Path,
    output_paths: Mapping[str, Path],
) -> bool:
    if checkpoint.get("terminal_state") not in REUSABLE_TERMINAL_STATES:
        return False
    if checkpoint.get("build_spec_identity") != build_spec_id or not source_path.is_file():
        return False
    source_sha = sha256_file(source_path)
    if checkpoint.get("source_sha256") != source_sha:
        return False
    expected_outputs = checkpoint.get("output_hashes")
    if not isinstance(expected_outputs, Mapping) or set(expected_outputs) != set(output_paths):
        return False
    actual_outputs: dict[str, str] = {}
    for key, path in output_paths.items():
        if not path.is_file():
            return False
        actual_outputs[key] = sha256_file(path)
    if actual_outputs != dict(expected_outputs):
        return False
    expected_identity = checkpoint_identity(
        build_spec_id=build_spec_id,
        accession=str(checkpoint.get("accession") or ""),
        source_sha256=source_sha,
        output_hashes=actual_outputs,
    )
    return checkpoint.get("checkpoint_identity") == expected_identity


def failure_record(
    *, accession: str, cik: str, stage: str, error: BaseException, attempts: int
) -> dict[str, object]:
    deterministic = not isinstance(error, (ConnectionError, TimeoutError))
    return {
        "accession": accession,
        "cik": cik,
        "stage": stage,
        "error_class": type(error).__name__,
        "error_message": str(error),
        "attempt_count": attempts,
        "terminal_state": "FAILED_DETERMINISTIC" if deterministic else "FAILED_TRANSIENT",
        "retry_disposition": "NO_BLIND_RETRY" if deterministic else "MAXIMUM_3_BOUNDED_ATTEMPTS",
    }


def hash_inventory(
    root: Path,
    *,
    exclude_names: Sequence[str] = (),
    exclude_prefixes: Sequence[str] = (),
) -> dict[str, object]:
    excluded = set(exclude_names)
    prefixes = tuple(prefix.rstrip("/") + "/" for prefix in exclude_prefixes)
    rows: list[dict[str, object]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if (
            path.name in excluded
            or path.name.endswith(".staging")
            or relative.startswith(prefixes)
        ):
            continue
        rows.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "root": root.as_posix(),
        "file_count": len(rows),
        "excluded_transient_prefixes": list(exclude_prefixes),
        "files": rows,
    }


def count_source_lines(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return sum(
        1
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


__all__ = [
    "BOUND_EPISODES",
    "BUILD_SPEC_VERSION",
    "AUTHORIZED_ENTITYFACTS_FORMS",
    "EDGARTOOLS_STANDARD_CONCEPT_PROJECTION",
    "EDGARTOOLS_VERSION",
    "FINAL_BINDING_RECORDS",
    "IDENTITY_EXCLUSION_EPISODES",
    "MAX_ACTIVE_BATCH_SOURCE_BYTES",
    "MAX_ENUMERATION_CIKS",
    "MAX_EXTRACTION_ACCESSIONS",
    "MAX_PEAK_BYTES",
    "MAX_PERSISTENT_BYTES",
    "NATIVE_PERIODIC_OBJECT_TYPES",
    "NON_REACQUIRABLE_OR_ADJUDICATION_SOURCE",
    "REACQUIRABLE_SOURCE_CACHE",
    "PROJECT_STORAGE_BYTES",
    "REUSABLE_TERMINAL_STATES",
    "TERMINAL_STATES",
    "TOTAL_P1_EPISODES",
    "UNIQUE_BOUND_CIK_COUNT",
    "SourceHashMismatchError",
    "accession_metadata_row",
    "build_spec_identity",
    "canonical_json_bytes",
    "checkpoint_identity",
    "checkpoint_reusable",
    "count_source_lines",
    "deduplicate_accessions",
    "failure_record",
    "hash_inventory",
    "is_native_financial_candidate",
    "load_authority",
    "percentile",
    "project_storage",
    "project_edgartools_standard_concept",
    "read_json",
    "read_jsonl",
    "scalar",
    "source_cache_evictable",
    "source_provenance_record",
    "verify_reacquired_source",
    "select_stratified_sample",
    "select_authorized_entityfacts",
    "selective_policy_identity",
    "sha256_bytes",
    "sha256_file",
    "write_json_atomic",
]
