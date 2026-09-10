"""Read-only deterministic snapshot entry point."""

from __future__ import annotations

from typing import Any

from .contract import LedgerAnchorManifest, TrialHistorySnapshot
from .storage import Ledger


def issue_snapshot(
    ledger: Ledger, auth_context: Any, *, as_of_ledger_sequence: int | None = None,
    anchor: LedgerAnchorManifest | None = None,
) -> TrialHistorySnapshot:
    """Issue a fail-closed snapshot without adding a new ledger event."""

    return ledger.snapshot(auth_context, as_of_ledger_sequence=as_of_ledger_sequence, anchor=anchor)
