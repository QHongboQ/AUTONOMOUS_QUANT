"""Pinned-source adapters retained only for the test reference oracle."""

from .fja_sp500 import (
    FJA_ADAPTER_VERSION,
    RECONCILED_DERIVATION_VERSION,
    build_fja_manifest,
    build_membership_event_manifest,
    build_reconciled_membership_event_manifest,
    derive_membership_events,
    derive_reconciled_membership_events,
    parse_fja_snapshots,
    raw_sha256,
)

__all__ = [
    "FJA_ADAPTER_VERSION",
    "RECONCILED_DERIVATION_VERSION",
    "build_fja_manifest",
    "build_membership_event_manifest",
    "build_reconciled_membership_event_manifest",
    "derive_membership_events",
    "derive_reconciled_membership_events",
    "parse_fja_snapshots",
    "raw_sha256",
]
