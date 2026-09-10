"""PIT invariants and legacy-Qlib active-set comparison."""

from __future__ import annotations

from pathlib import Path
from datetime import date, timedelta
from typing import Iterable

from .parser import CurrentConstituent
from .identity import SecurityIdentityMapping, logical_identity
from .reconstruct import MembershipInterval, active_symbols


class ValidationError(ValueError):
    pass


def validate_intervals(intervals: Iterable[MembershipInterval]) -> None:
    seen = set()
    prior: dict[str, str] = {}
    for item in sorted(intervals, key=lambda value: (value.logical_security_identity, value.membership_start)):
        key = (item.logical_security_identity, item.membership_start, item.membership_end)
        if key in seen:
            raise ValidationError(f"duplicate interval: {key}")
        seen.add(key)
        if item.membership_end <= item.membership_start:
            raise ValidationError(f"invalid interval: {key}")
        if item.logical_security_identity in prior and item.membership_start < prior[item.logical_security_identity]:
            raise ValidationError(f"overlapping intervals: {item.logical_security_identity}")
        prior[item.logical_security_identity] = item.membership_end


def unresolved_mappings(intervals: Iterable[MembershipInterval], mappings: Iterable[SecurityIdentityMapping]) -> list[str]:
    mapped = {item.logical_security_id for item in mappings if item.market_data_symbol and item.evidence_url and item.resolution_state == "RESOLVED"}
    return sorted({item.logical_security_identity for item in intervals} - mapped)


def parse_qlib_sp500(path: Path) -> list[MembershipInterval]:
    answer = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 3:
            symbol, start, end = parts
            logical = logical_identity(symbol, on_date=start)
            # Qlib's instrument files use inclusive end dates; the project
            # contract uses half-open intervals.
            end_exclusive = (date.fromisoformat(end) + timedelta(days=1)).isoformat()
            answer.append(MembershipInterval(symbol, logical, logical, start, end_exclusive, ("QLIB_REFERENCE",)))
    return answer


def compare_qlib_overlap(new: Iterable[MembershipInterval], old: Iterable[MembershipInterval], dates: Iterable[str]) -> list[dict[str, object]]:
    new, old = list(new), list(old)
    new_labels: dict[str, set[str]] = {}
    old_labels: dict[str, set[str]] = {}
    for item in new:
        new_labels.setdefault(item.logical_security_identity, set()).add(item.source_symbol)
    for item in old:
        old_labels.setdefault(item.logical_security_identity, set()).add(item.source_symbol)
    rows = []
    for day in dates:
        new_set, old_set = active_symbols(new, day), active_symbols(old, day)
        new_only, old_only = sorted(new_set - old_set), sorted(old_set - new_set)
        rows.append({"date": day, "new_count": len(new_set), "old_qlib_count": len(old_set), "intersection_count": len(new_set & old_set), "new_only": new_only, "old_only": old_only, "new_only_symbols": {key: sorted(new_labels.get(key, ())) for key in new_only}, "old_only_symbols": {key: sorted(old_labels.get(key, ())) for key in old_only}, "unexplained_difference_count": len(new_only) + len(old_only), "acceptance_policy": "Every remaining identity is a blocker until first-party membership or identity evidence resolves it; no percentage threshold is used."})
    return rows


def terminal_state_difference(current: Iterable[CurrentConstituent], intervals: Iterable[MembershipInterval], cutoff: str) -> dict[str, object]:
    """Compare reconstructed terminal membership with the frozen current table."""

    expected = {logical_identity(item.symbol, item.security, cutoff) for item in current}
    actual = active_symbols(intervals, cutoff)
    return {
        "expected_current_count": len(expected),
        "reconstructed_terminal_count": len(actual),
        "missing_from_reconstruction": sorted(expected - actual),
        "unexpected_in_reconstruction": sorted(actual - expected),
        "matches": expected == actual,
    }
