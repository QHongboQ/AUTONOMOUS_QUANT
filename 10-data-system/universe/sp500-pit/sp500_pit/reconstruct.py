"""Backward membership reconstruction and explicit market-symbol mappings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Iterable

from .canonical import sha256
from .parser import ChangeEvent, CurrentConstituent
from .identity import CORPORATE_MEMBERSHIP_TRANSITIONS, FROZEN_SOURCE_URL, SecurityIdentityMapping, logical_identity, provider_symbol, transition_mappings


@dataclass(frozen=True)
class MembershipInterval:
    source_symbol: str
    normalized_symbol: str
    logical_security_identity: str
    membership_start: str
    membership_end: str
    source_change_evidence: tuple[str, ...]


SymbolMapping = SecurityIdentityMapping


def reconstruct_membership(current: Iterable[CurrentConstituent], changes: Iterable[ChangeEvent], start: str, cutoff: str) -> list[MembershipInterval]:
    """Reconstruct [start, end) intervals from terminal constituents.

    Every pre-start event is first applied in reverse so no post-start
    constituent leaks backward. Forward replay then uses the source-reported
    *effective* date as the atomic membership boundary.
    """

    start_day, cutoff_day = date.fromisoformat(start), date.fromisoformat(cutoff)
    events = sorted((item for item in changes if date.fromisoformat(item.effective_date) <= cutoff_day), key=lambda item: (item.effective_date, item.source_row))
    state = {logical_identity(item.symbol, item.security, cutoff): item.symbol for item in current}
    reverse_timeline = [(event.effective_date, "source", event) for event in events]
    reverse_timeline += [(item.effective_date, "corporate", item) for item in CORPORATE_MEMBERSHIP_TRANSITIONS]
    for _, kind, event in sorted(reverse_timeline, key=lambda item: (item[0], item[1]), reverse=True):
        if not (start_day < date.fromisoformat(event.effective_date) <= cutoff_day):
            continue
        if kind == "corporate":
            if event.successor_id in state:
                state.pop(event.successor_id)
                for predecessor, symbol in zip(event.predecessor_ids, event.predecessor_symbols):
                    state[predecessor] = symbol
            continue
        if event.added_symbol:
            state.pop(logical_identity(event.added_symbol, event.added_security, event.effective_date), None)
        if event.removed_symbol:
            state[logical_identity(event.removed_symbol, event.removed_security, event.effective_date)] = event.removed_symbol

    opened = {identity: (start, symbol, ("terminal-state-reversed",)) for identity, symbol in state.items()}
    intervals: list[MembershipInterval] = []
    timeline = [(event.effective_date, "source", event) for event in events if start_day <= date.fromisoformat(event.effective_date) <= cutoff_day]
    timeline += [(item.effective_date, "corporate", item) for item in CORPORATE_MEMBERSHIP_TRANSITIONS if start_day <= date.fromisoformat(item.effective_date) <= cutoff_day]
    for _, kind, event in sorted(timeline, key=lambda item: (item[0], item[1])):
        if kind == "corporate":
            active_predecessors = [identity for identity in event.predecessor_ids if identity in opened]
            if not active_predecessors:
                continue
            for identity in active_predecessors:
                prior = opened.pop(identity, None)
                if prior is not None:
                    intervals.append(MembershipInterval(prior[1], identity, identity, prior[0], event.effective_date, prior[2] + (event.transition_type, event.evidence_url)))
            if event.successor_id in opened:
                raise ValueError(f"duplicate corporate successor: {event.successor_id}")
            opened[event.successor_id] = (event.effective_date, event.successor_symbol, (event.transition_type, event.evidence_url))
            continue
        event_day = date.fromisoformat(event.effective_date)
        if event_day < start_day or event_day > cutoff_day:
            continue
        if event.removed_symbol:
            identity = logical_identity(event.removed_symbol, event.removed_security, event.effective_date)
            prior = opened.pop(identity, None)
            if prior is not None and prior[0] < event.effective_date:
                intervals.append(MembershipInterval(prior[1], identity, identity, prior[0], event.effective_date, prior[2] + (f"removed-row-{event.source_row}",)))
        if event.added_symbol:
            identity = logical_identity(event.added_symbol, event.added_security, event.effective_date)
            if identity in opened:
                raise ValueError(f"duplicate active addition: {identity} at {event.effective_date}")
            opened[identity] = (event.effective_date, event.added_symbol, (f"added-row-{event.source_row}",))
    end_exclusive = (cutoff_day + timedelta(days=1)).isoformat()
    for identity, prior in sorted(opened.items()):
        intervals.append(MembershipInterval(prior[1], identity, identity, prior[0], end_exclusive, prior[2] + ("cutoff-terminal",)))
    return sorted(intervals, key=lambda item: (item.logical_security_identity, item.membership_start, item.membership_end))


def build_symbol_mapping(intervals: Iterable[MembershipInterval], start: str, end_exclusive: str) -> list[SymbolMapping]:
    active = {item.logical_security_identity for item in intervals}
    mappings = [item for item in transition_mappings() if item.logical_security_id in active and item.effective_from < end_exclusive and start < item.effective_to]
    covered = {item.logical_security_id for item in mappings}
    for item in sorted(intervals, key=lambda value: (value.logical_security_identity, value.source_symbol)):
        if item.logical_security_identity in covered:
            continue
        mappings.append(SecurityIdentityMapping(item.logical_security_identity, item.source_symbol, item.source_symbol, provider_symbol(item.source_symbol), start, end_exclusive, "DOT_DASH_PROVIDER_FORMAT" if provider_symbol(item.source_symbol) != item.source_symbol else "SOURCE_SYMBOL_DIRECT", None, None, FROZEN_SOURCE_URL, "2024-12-26", None, "MEDIUM", "RESOLVED"))
        covered.add(item.logical_security_identity)
    return sorted(mappings, key=lambda value: (value.logical_security_id, value.effective_from, value.source_symbol))


def active_symbols(intervals: Iterable[MembershipInterval], on_date: str) -> set[str]:
    return {item.logical_security_identity for item in intervals if item.membership_start <= on_date < item.membership_end}


def interval_hash(intervals: Iterable[MembershipInterval]) -> str:
    return sha256([asdict(item) for item in intervals])


def mapping_hash(mappings: Iterable[SymbolMapping]) -> str:
    return sha256([asdict(item) for item in mappings])


def universe_hash(intervals: Iterable[MembershipInterval], mappings: Iterable[SymbolMapping]) -> str:
    return sha256({"schema_version": "SP500_PIT_V2", "membership_intervals": [asdict(item) for item in intervals], "symbol_mapping": [asdict(item) for item in mappings]})
