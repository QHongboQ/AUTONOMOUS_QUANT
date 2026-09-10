"""SQLite-supported backup and restore verification primitives."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path

from .canonical import canonical_json_bytes, canonicalize_anchor_payload, parse_json_strict
from .contract import LedgerAnchorManifest, TrialHistorySnapshot
from .storage import Ledger


def backup(ledger: Ledger, destination: str | Path) -> None:
    """Create a consistent SQLite backup; never copy a live database file."""

    ledger.backup_to(destination)


def verify_restored_backup(
    path: str | Path, expected_snapshot: TrialHistorySnapshot,
    anchor: LedgerAnchorManifest | None = None,
) -> bool:
    """Verify integrity, chain/anchor, and deterministic snapshot identity."""

    return Ledger.verify_restored_backup(path, expected_snapshot, anchor)


def write_anchor_artifact(path: str | Path, anchor: LedgerAnchorManifest) -> None:
    """Write a self-verifying manifest outside the authoritative DB directory."""

    destination = Path(path)
    payload = asdict(anchor)
    destination.write_bytes(canonical_json_bytes(payload))


def load_anchor_artifact(path: str | Path) -> LedgerAnchorManifest:
    """Load and validate a canonical external anchor artifact."""

    raw = parse_json_strict(Path(path).read_text(encoding="utf-8"))
    payload = raw["payload"]
    digest = raw["manifest_sha256"]
    if hashlib.sha256(canonicalize_anchor_payload(payload)).hexdigest() != digest:
        raise ValueError("invalid external anchor digest")
    from .contract import LedgerAnchorManifestPayload
    return LedgerAnchorManifest(LedgerAnchorManifestPayload(**payload), digest)
