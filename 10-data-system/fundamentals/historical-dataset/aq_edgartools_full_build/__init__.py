"""Thin orchestration primitives for the selective EdgarTools P5 build.

EdgarTools owns SEC access, filing-object routing, XBRL attachment selection,
and XBRL parsing. Existing AQ contracts own decimal admission and the frozen
fundamental vocabulary. This module only binds the frozen selective inventory
to bounded batches, deterministic native-source manifests, and fail-closed
resume/seal accounting.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable, Mapping, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

import rfc8785

from aq_fundamental_evidence import canonical_decimal_value
from aq_hybrid_fundamentals import (
    EDGARTOOLS_STANDARD_CONCEPT_PROJECTION,
    project_edgartools_standard_concept,
)


BUILD_SPEC_VERSION = "AQ_P5_EDGARTOOLS_SELECTIVE_BUILD_V2"
EDGARTOOLS_VERSION = "5.58.0"
HISTORY_START = "1994-01-01"
HISTORY_END = "2024-12-31"
SELECTIVE_REQUIRED_ACCESSION_COUNT = 36_206
SELECTIVE_POLICY_IDENTITY = (
    "sha256:0191c9bbab3cdbc1d48000b3cf58bfe2aded164547419fad6bca48d63f7c0fc1"
)
MAX_EXTRACTION_ACCESSIONS = 200
MAX_ACTIVE_BATCH_SOURCE_BYTES = 2 * 1024**3
NATIVE_PERIODIC_OBJECT_TYPES = frozenset({"TenK", "TenQ", "TwentyF", "FortyF"})
XBRL_ASSET_ROLES = (
    "instance",
    "schema",
    "label",
    "presentation",
    "calculation",
    "definition",
)
TERMINAL_STATES = frozenset(
    {
        "COMPLETE_WITH_EVIDENCE",
        "COMPLETE_NO_AUTHORIZED_FACTS",
        "COMPLETE_NO_STRUCTURED_FINANCIALS",
        "FAILED_TRANSIENT",
        "FAILED_DETERMINISTIC",
    }
)
REUSABLE_TERMINAL_STATES = TERMINAL_STATES - {
    "FAILED_TRANSIENT",
    "FAILED_DETERMINISTIC",
}
ENTITYFACTS_DISCOVERY_ROLE = "ENTITYFACTS_DISCOVERY_REQUIRES_ACCESSION_VALIDATION"
REACQUIRABLE_SOURCE_CACHE = "REACQUIRABLE_SOURCE_CACHE"
NON_NUMERIC_FACT_NOT_ELIGIBLE = "NON_NUMERIC_FACT_NOT_ELIGIBLE_FOR_NUMERIC_EVIDENCE"
NIL_FACT_NOT_ELIGIBLE = "NIL_FACT_NOT_ELIGIBLE_FOR_NUMERIC_EVIDENCE"
NUMERIC_FACT_SELECTED = "NUMERIC_FACT_SELECTED"


class SourceHashMismatchError(ValueError):
    """Reacquired native SEC assets differ from their sealed manifest."""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _identity(value: object) -> str:
    return "sha256:" + sha256_bytes(rfc8785.dumps(value))


def select_numeric_fact_value(fact: Mapping[str, object]) -> tuple[str, str | None]:
    """Apply native numeric eligibility, then the existing AQ decimal authority."""

    value = fact.get("value")
    if value is None or value == "":
        return NIL_FACT_NOT_ELIGIBLE, None
    if fact.get("numeric_value") is None and fact.get("unit_ref") is None:
        return NON_NUMERIC_FACT_NOT_ELIGIBLE, None
    try:
        exact = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("native XBRL numeric value is not an exact decimal") from exc
    if not exact.is_finite():
        raise ValueError("native XBRL numeric value must be finite")
    canonical = format(exact, "f")
    if "." in canonical:
        canonical = canonical.rstrip("0").rstrip(".")
    if canonical in {"-0", ""}:
        canonical = "0"
    return NUMERIC_FACT_SELECTED, canonical_decimal_value(canonical)


def native_financial_object_info(
    form: str,
    *,
    get_info: Callable[[str], tuple[bool, str | None, str | None]] | None = None,
) -> tuple[bool, str | None]:
    """Use EdgarTools object capability; retain only the structured 6-K policy leaf."""

    if get_info is None:
        from edgar import get_obj_info

        get_info = get_obj_info
    has_object, object_type, _description = get_info(form)
    base_form = form.split("/", 1)[0]
    admitted = bool(
        has_object
        and (
            object_type in NATIVE_PERIODIC_OBJECT_TYPES
            or (object_type == "CurrentReport" and base_form == "6-K")
        )
    )
    return admitted, object_type


def selective_policy_identity() -> str:
    """Return the already-frozen selective-policy identity unchanged."""

    return SELECTIVE_POLICY_IDENTITY


def select_authorized_entityfacts(
    facts: Iterable[Mapping[str, object]],
    *,
    map_concept: Callable[[str, str, object], str | None],
    get_info: Callable[[str], tuple[bool, str | None, str | None]] | None = None,
) -> list[dict[str, object]]:
    """Reduce EntityFacts to accession discovery rows, never final evidence."""

    selected: list[dict[str, object]] = []
    mapped: dict[tuple[str, str], str | None] = {}
    for raw in facts:
        form = str(raw.get("form_type") or raw.get("form") or "")
        filing_date = str(raw.get("filing_date") or "")
        accession = str(raw.get("accession") or "")
        capable, _object_type = native_financial_object_info(form, get_info=get_info)
        if (
            not capable
            or not accession
            or not (HISTORY_START <= filing_date <= HISTORY_END)
            or raw.get("numeric_value") is None
            or raw.get("value") is None
        ):
            continue
        concept = str(raw.get("concept") or "")
        label = str(raw.get("label") or concept)
        key = (concept, label)
        if key not in mapped:
            mapped[key] = map_concept(concept, label, {})
        standard = project_edgartools_standard_concept(mapped[key])
        if standard is None:
            continue
        selected.append(
            {
                "accession": accession,
                "concept": concept,
                "standard_concept": standard,
                "form": form,
                "filing_date": filing_date,
                "source_role": ENTITYFACTS_DISCOVERY_ROLE,
            }
        )
    return selected


def _asset_payload(attachment: object) -> bytes:
    content = getattr(attachment, "content")
    return content if isinstance(content, bytes) else str(content).encode("utf-8")


def native_xbrl_source_manifest(
    filing: object,
    *,
    payload_reader: Callable[[object], bytes] = _asset_payload,
) -> dict[str, object]:
    """Seal exactly the deterministic attachment set consumed by EdgarTools XBRL."""

    from edgar.xbrl.xbrl import XBRLAttachments

    accession = str(getattr(filing, "accession_no"))
    native = XBRLAttachments(getattr(filing, "attachments"))
    assets: list[dict[str, object]] = []
    for role in XBRL_ASSET_ROLES:
        attachment = native.get(role)
        if attachment is None:
            continue
        payload = payload_reader(attachment)
        assets.append(
            {
                "role": role,
                "relative_sec_asset_identity": str(getattr(attachment, "path")),
                "url": str(getattr(attachment, "url")),
                "sha256": sha256_bytes(payload),
                "byte_count": len(payload),
            }
        )
    body = {
        "schema": "AQ_P5_SEC_XBRL_NATIVE_ASSET_MANIFEST_V1",
        "accession": accession,
        "assets": assets,
    }
    manifest_hash = sha256_bytes(rfc8785.dumps(body))
    return {
        **body,
        "manifest_sha256": manifest_hash,
        "source_document_identity": f"SEC_XBRL_ASSET_MANIFEST:{manifest_hash}",
        "source_document_sha256": manifest_hash,
        "source_document_url": next(
            (str(row["url"]) for row in assets if row["role"] == "instance"),
            str(assets[0]["url"]) if assets else None,
        ),
        "source_byte_count": sum(int(row["byte_count"]) for row in assets),
        "source_storage_class": REACQUIRABLE_SOURCE_CACHE,
    }


def verify_native_xbrl_source_manifest(
    manifest: Mapping[str, object],
    payloads_by_role: Mapping[str, bytes],
) -> bool:
    """Fail closed on missing, extra, changed, or differently-sized native assets."""

    assets = manifest.get("assets")
    if not isinstance(assets, Sequence):
        raise SourceHashMismatchError("native source manifest lacks assets")
    expected_roles = {str(row["role"]) for row in assets if isinstance(row, Mapping)}
    if set(payloads_by_role) != expected_roles:
        raise SourceHashMismatchError("native source asset role set changed")
    for row in assets:
        if not isinstance(row, Mapping):
            raise SourceHashMismatchError("native source manifest row is invalid")
        payload = payloads_by_role[str(row["role"])]
        if sha256_bytes(payload) != row.get("sha256") or len(payload) != row.get("byte_count"):
            raise SourceHashMismatchError("native SEC source asset bytes changed")
    body = {
        "schema": manifest.get("schema"),
        "accession": manifest.get("accession"),
        "assets": list(assets),
    }
    if sha256_bytes(rfc8785.dumps(body)) != manifest.get("manifest_sha256"):
        raise SourceHashMismatchError("native source manifest identity changed")
    return True


def bounded_batches(
    rows: Sequence[Mapping[str, object]],
    *,
    max_count: int = MAX_EXTRACTION_ACCESSIONS,
    max_expected_bytes: int = MAX_ACTIVE_BATCH_SOURCE_BYTES,
) -> Iterable[list[dict[str, object]]]:
    """Partition the frozen inventory by two explicit resource ceilings."""

    batch: list[dict[str, object]] = []
    batch_bytes = 0
    for source in rows:
        row = dict(source)
        expected = int(row.get("expected_native_asset_bytes") or 0)
        if expected > max_expected_bytes:
            raise ValueError("one accession exceeds the active source-byte ceiling")
        if batch and (len(batch) >= max_count or batch_bytes + expected > max_expected_bytes):
            yield batch
            batch, batch_bytes = [], 0
        batch.append(row)
        batch_bytes += expected
    if batch:
        yield batch


def checkpoint_identity(
    *,
    build_spec_identity: str,
    accession: str,
    source_manifest_sha256: str,
    output_hashes: Mapping[str, str],
) -> str:
    return _identity(
        {
            "build_spec_identity": build_spec_identity,
            "accession": accession,
            "source_manifest_sha256": source_manifest_sha256,
            "output_hashes": dict(sorted(output_hashes.items())),
        }
    )


def checkpoint_reusable(
    checkpoint: Mapping[str, object],
    *,
    build_spec_identity: str,
    output_paths: Mapping[str, Path],
) -> bool:
    """Reuse only sealed terminal outputs with a complete identity match."""

    if (
        checkpoint.get("terminal_state") not in REUSABLE_TERMINAL_STATES
        or checkpoint.get("build_spec_identity") != build_spec_identity
        or checkpoint.get("evidence_sealed") is not True
    ):
        return False
    expected = checkpoint.get("output_hashes")
    if not isinstance(expected, Mapping) or set(expected) != set(output_paths):
        return False
    actual = {
        name: sha256_file(path)
        for name, path in output_paths.items()
        if path.is_file()
    }
    if actual != dict(expected):
        return False
    expected_identity = checkpoint_identity(
        build_spec_identity=build_spec_identity,
        accession=str(checkpoint.get("accession") or ""),
        source_manifest_sha256=str(checkpoint.get("source_manifest_sha256") or ""),
        output_hashes=actual,
    )
    return checkpoint.get("checkpoint_identity") == expected_identity


def failure_record(
    *, accession: str, cik: str, stage: str, error: BaseException, attempts: int
) -> dict[str, object]:
    transient = isinstance(error, (ConnectionError, TimeoutError))
    return {
        "accession": accession,
        "cik": cik,
        "stage": stage,
        "error_class": type(error).__name__,
        "error_message": str(error),
        "attempt_count": attempts,
        "terminal_state": "FAILED_TRANSIENT" if transient else "FAILED_DETERMINISTIC",
        "retry_disposition": "MAXIMUM_3_BOUNDED_ATTEMPTS" if transient else "NO_BLIND_RETRY",
    }


def source_cache_evictable(
    checkpoint: Mapping[str, object], *, output_paths: Mapping[str, Path]
) -> bool:
    """Transient native assets are evictable only after sealed-output verification."""

    return bool(
        checkpoint.get("source_storage_class") == REACQUIRABLE_SOURCE_CACHE
        and checkpoint_reusable(
            checkpoint,
            build_spec_identity=str(checkpoint.get("build_spec_identity") or ""),
            output_paths=output_paths,
        )
    )


__all__ = [
    "BUILD_SPEC_VERSION",
    "EDGARTOOLS_STANDARD_CONCEPT_PROJECTION",
    "EDGARTOOLS_VERSION",
    "ENTITYFACTS_DISCOVERY_ROLE",
    "MAX_ACTIVE_BATCH_SOURCE_BYTES",
    "MAX_EXTRACTION_ACCESSIONS",
    "NIL_FACT_NOT_ELIGIBLE",
    "NON_NUMERIC_FACT_NOT_ELIGIBLE",
    "NUMERIC_FACT_SELECTED",
    "REACQUIRABLE_SOURCE_CACHE",
    "SELECTIVE_POLICY_IDENTITY",
    "SELECTIVE_REQUIRED_ACCESSION_COUNT",
    "SourceHashMismatchError",
    "bounded_batches",
    "checkpoint_identity",
    "checkpoint_reusable",
    "failure_record",
    "native_financial_object_info",
    "native_xbrl_source_manifest",
    "select_authorized_entityfacts",
    "select_numeric_fact_value",
    "selective_policy_identity",
    "sha256_bytes",
    "sha256_file",
    "source_cache_evictable",
    "verify_native_xbrl_source_manifest",
]
