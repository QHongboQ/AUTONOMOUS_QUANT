"""Fail-closed certification authority checks for the reconciled PIT universe."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .canonical import deterministic_id
from .contracts import (
    InstrumentEpisodeV1,
    SourceManifestV1,
    SourceRole,
)
from .overlays import ResolvedObservation


CANONICAL_LEDGER_SHA256 = "d227a9c514e4a13752b0f35ddfc3a7e7292270570b96ff9f4342dfcbaed38734"
DIAGNOSTIC_TERMINAL_SHA256 = "597d7d170a35c6ec4ade33fc56b38d6f0c45db9029c515216ec03deee106b065"


@dataclass(frozen=True, slots=True)
class CertificationDecision:
    primary_evidence_content_addressed: bool
    canonical_ledger_pinned: bool
    official_terminal_authority: str
    historical_sample_gate: str
    compiled_terminal_set_gate: str
    artifact_hashes_twice_identical: str
    provenance_complete: bool
    pit_universe_certified: bool
    blockers: tuple[str, ...]


def verify_content_hash(raw: bytes, expected_sha256: str, label: str) -> str:
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise ValueError(f"{label} content hash mismatch")
    return actual


def build_retained_input_manifest(
    *,
    raw: bytes,
    expected_sha256: str,
    label: str,
    source_type: str,
    source_url_or_repo: str,
    source_commit_or_revision: str,
    retrieved_at: str,
    media_type: str,
    coverage_start: str,
    coverage_end: str,
    source_role: SourceRole = SourceRole.DIAGNOSTIC_REFERENCE,
    license_observation: str = "retained evidence; attribution recorded by source ingestion",
) -> SourceManifestV1:
    digest = verify_content_hash(raw, expected_sha256, label)
    logical = {
        "label": label,
        "source_type": source_type,
        "source_url_or_repo": source_url_or_repo,
        "source_commit_or_revision": source_commit_or_revision,
        "sha256": digest,
    }
    return SourceManifestV1(
        source_id=deterministic_id("P1SRC-", logical),
        source_role=source_role,
        source_type=source_type,
        source_url_or_repo=source_url_or_repo,
        source_commit_or_revision=source_commit_or_revision,
        retrieved_at=retrieved_at,
        media_type=media_type,
        byte_length=len(raw),
        sha256=digest,
        license_observation=license_observation,
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        ancestry=(),
        adapter_version="retained-certification-input-v1",
    )


def is_retained_primary_evidence(
    manifest: SourceManifestV1,
    retained_bytes_by_hash: dict[str, bytes],
) -> bool:
    """A locator digest is never sufficient; actual retained bytes must match."""

    if manifest.source_role not in {
        SourceRole.TICKER_IDENTITY_EVIDENCE,
        SourceRole.OFFICIAL_CONFLICT_RESOLUTION,
    }:
        return False
    if manifest.source_type != "retained_primary_official_evidence_bytes":
        return False
    raw = retained_bytes_by_hash.get(manifest.sha256)
    return raw is not None and len(raw) == manifest.byte_length and (
        hashlib.sha256(raw).hexdigest() == manifest.sha256
    )


def is_official_terminal_authority(
    manifest: SourceManifestV1 | None,
    retained_bytes_by_hash: dict[str, bytes],
) -> bool:
    if manifest is None:
        return False
    if manifest.source_role is not SourceRole.OFFICIAL_CONFLICT_RESOLUTION:
        return False
    if manifest.source_type != "official_terminal_roster":
        return False
    raw = retained_bytes_by_hash.get(manifest.sha256)
    return raw is not None and len(raw) == manifest.byte_length and hashlib.sha256(raw).hexdigest() == manifest.sha256


def historical_sample_authority_complete(
    manifests: tuple[SourceManifestV1, ...],
    retained_bytes_by_hash: dict[str, bytes],
) -> bool:
    if not manifests:
        return False
    return all(
        item.source_role is SourceRole.OFFICIAL_CONFLICT_RESOLUTION
        and item.source_type == "preregistered_historical_roster_sample"
        and (raw := retained_bytes_by_hash.get(item.sha256)) is not None
        and len(raw) == item.byte_length
        and hashlib.sha256(raw).hexdigest() == item.sha256
        for item in manifests
    )


def compiled_terminal_set(
    episodes: tuple[InstrumentEpisodeV1, ...],
    terminal_session: str,
) -> tuple[str, ...]:
    return tuple(sorted(
        item.normalized_ticker for item in episodes
        if item.membership_from <= terminal_session < item.membership_to
    ))


def evaluate_certification(
    *,
    primary_evidence_manifests: tuple[SourceManifestV1, ...],
    retained_primary_bytes_by_hash: dict[str, bytes],
    canonical_ledger_manifest: SourceManifestV1,
    official_terminal_manifest: SourceManifestV1 | None,
    official_terminal_bytes_by_hash: dict[str, bytes],
    historical_sample_manifests: tuple[SourceManifestV1, ...],
    historical_sample_bytes_by_hash: dict[str, bytes],
    episodes: tuple[InstrumentEpisodeV1, ...],
    resolved_observations: tuple[ResolvedObservation, ...],
    artifact_hashes_twice_identical: bool,
) -> CertificationDecision:
    primary_ok = bool(primary_evidence_manifests) and all(
        is_retained_primary_evidence(item, retained_primary_bytes_by_hash)
        for item in primary_evidence_manifests
    )
    ledger_ok = canonical_ledger_manifest.sha256 == CANONICAL_LEDGER_SHA256
    official_terminal_ok = is_official_terminal_authority(
        official_terminal_manifest, official_terminal_bytes_by_hash,
    )
    samples_ok = historical_sample_authority_complete(
        historical_sample_manifests, historical_sample_bytes_by_hash,
    )
    terminal = max(resolved_observations, key=lambda item: item.effective_session)
    compiled_ok = compiled_terminal_set(episodes, terminal.effective_session) == terminal.tickers
    blockers = []
    if not primary_ok:
        blockers.append("PRIMARY_EVIDENCE_CONTENT_MISSING")
    if not ledger_ok:
        blockers.append("CANONICAL_LEDGER_AUTHORITY_INVALID")
    if not official_terminal_ok:
        blockers.append("OFFICIAL_TERMINAL_AUTHORITY_MISSING")
    if not samples_ok:
        blockers.append("HISTORICAL_SAMPLE_AUTHORITY_MISSING")
    if not compiled_ok:
        blockers.append("COMPILED_TERMINAL_SET_MISMATCH")
    if not artifact_hashes_twice_identical:
        blockers.append("ARTIFACT_DETERMINISM_FAILED")
    provenance_complete = not blockers
    return CertificationDecision(
        primary_evidence_content_addressed=primary_ok,
        canonical_ledger_pinned=ledger_ok,
        official_terminal_authority="PASS" if official_terminal_ok else "MISSING",
        historical_sample_gate="PASS" if samples_ok else "MISSING",
        compiled_terminal_set_gate="PASS" if compiled_ok else "FAIL",
        artifact_hashes_twice_identical="PASS" if artifact_hashes_twice_identical else "FAIL",
        provenance_complete=provenance_complete,
        pit_universe_certified=provenance_complete,
        blockers=tuple(blockers),
    )
