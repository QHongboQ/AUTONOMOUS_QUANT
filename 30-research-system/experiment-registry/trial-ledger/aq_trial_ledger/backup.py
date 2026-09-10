"""SQLite-supported backup and restore verification primitives."""

from __future__ import annotations

from pathlib import Path

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
