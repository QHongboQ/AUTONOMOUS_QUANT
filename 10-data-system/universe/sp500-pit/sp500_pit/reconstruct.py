"""Backward membership reconstruction and explicit market-symbol mappings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Iterable

from .canonical import sha256
from .parser import ChangeEvent, CurrentConstituent


# Versioned, narrow identity aliases. They are not a blanket ticker rewrite.
LOGICAL_ALIASES = {"FB": "META", "ANTM": "ELV", "VIAC": "PARA", "HFC": "DINO", "FLT": "CPAY"}
DOT_DASH = {"BRK.B": "BRK-B", "BF.B": "BF-B"}


@dataclass(frozen=True)
class MembershipInterval:
    source_symbol: str
    normalized_symbol: str
    logical_security_identity: str
    membership_start: str
    membership_end: str
    source_change_evidence: tuple[str, ...]


@dataclass(frozen=True)
class SymbolMapping:
    index_source_symbol: str
    logical_security_identity: str
    market_data_symbol: str
    effective_from: str
    effective_to: str
    mapping_reason: str
    evidence: str


def logical_identity(symbol: str, security: str | None = None) -> str:
    """Return a security identity, not merely a ticker string.

    The 2014/2016 Under Armour rows reuse ``UA`` for two share classes.  The
    source security text distinguishes them, so the adapter preserves that
    distinction rather than turning two eligible securities into one ticker.
    """

    ticker = symbol.upper()
    name = (security or "").casefold()
    if ticker == "IR" and "ingersoll-rand" in name:
        return "INGERSOLL_RAND_LEGACY"
    if ticker == "TT" and "trane" in name:
        return "INGERSOLL_RAND_LEGACY"
    if ticker == "IR" and "ingersoll rand" in name:
        return "INGERSOLL_RAND_2020"
    if ticker == "UAA" or (ticker == "UA" and "under armour" in name and "class c" not in name):
        return "UNDER_ARMOUR_CLASS_A"
    if ticker == "UA" and "class c" in name:
        return "UNDER_ARMOUR_CLASS_C"
    return LOGICAL_ALIASES.get(ticker, ticker)


def reconstruct_membership(current: Iterable[CurrentConstituent], changes: Iterable[ChangeEvent], start: str, cutoff: str) -> list[MembershipInterval]:
    """Reconstruct [start, end) intervals from terminal constituents.

    Every pre-start event is first applied in reverse so no post-start
    constituent leaks backward. Forward replay then uses the source-reported
    *effective* date as the atomic membership boundary.
    """

    start_day, cutoff_day = date.fromisoformat(start), date.fromisoformat(cutoff)
    events = sorted((item for item in changes if date.fromisoformat(item.effective_date) <= cutoff_day), key=lambda item: (item.effective_date, item.source_row))
    state = {logical_identity(item.symbol, item.security) for item in current}
    for event in reversed(events):
        if date.fromisoformat(event.effective_date) <= start_day:
            continue
        if event.added_symbol:
            state.discard(logical_identity(event.added_symbol, event.added_security))
        if event.removed_symbol:
            state.add(logical_identity(event.removed_symbol, event.removed_security))

    opened = {identity: (start, identity, ("terminal-state-reversed",)) for identity in state}
    intervals: list[MembershipInterval] = []
    for event in events:
        event_day = date.fromisoformat(event.effective_date)
        if event_day < start_day or event_day > cutoff_day:
            continue
        if event.removed_symbol:
            identity = logical_identity(event.removed_symbol, event.removed_security)
            prior = opened.pop(identity, None)
            if prior is not None and prior[0] < event.effective_date:
                intervals.append(MembershipInterval(prior[1], identity, identity, prior[0], event.effective_date, prior[2] + (f"removed-row-{event.source_row}",)))
        if event.added_symbol:
            identity = logical_identity(event.added_symbol, event.added_security)
            if identity in opened:
                raise ValueError(f"duplicate active addition: {identity} at {event.effective_date}")
            opened[identity] = (event.effective_date, event.added_symbol, (f"added-row-{event.source_row}",))
    end_exclusive = (cutoff_day + timedelta(days=1)).isoformat()
    for identity, prior in sorted(opened.items()):
        intervals.append(MembershipInterval(prior[1], identity, identity, prior[0], end_exclusive, prior[2] + ("cutoff-terminal",)))
    return sorted(intervals, key=lambda item: (item.logical_security_identity, item.membership_start, item.membership_end))


def build_symbol_mapping(intervals: Iterable[MembershipInterval], start: str, end_exclusive: str) -> list[SymbolMapping]:
    mappings = []
    for identity in sorted({item.logical_security_identity for item in intervals}):
        if identity == "UNDER_ARMOUR_CLASS_A":
            market, reason = "UAA", "TICKER_RENAME_SHARE_CLASS"
        elif identity == "UNDER_ARMOUR_CLASS_C":
            market, reason = "UA", "SHARE_CLASS_IDENTITY"
        elif identity == "INGERSOLL_RAND_LEGACY":
            market, reason = "TT", "TICKER_RENAME_CORPORATE_IDENTITY"
        elif identity == "INGERSOLL_RAND_2020":
            market, reason = "IR", "TICKER_REUSE_NEW_SECURITY"
        else:
            market, reason = DOT_DASH.get(identity, identity), "DOT_DASH_PROVIDER_FORMAT" if identity in DOT_DASH else "SOURCE_SYMBOL_DIRECT"
        mappings.append(SymbolMapping(identity, identity, market, start, end_exclusive, reason, "SP500_PIT_MAPPING_V1"))
    return mappings


def active_symbols(intervals: Iterable[MembershipInterval], on_date: str) -> set[str]:
    return {item.logical_security_identity for item in intervals if item.membership_start <= on_date < item.membership_end}


def interval_hash(intervals: Iterable[MembershipInterval]) -> str:
    return sha256([asdict(item) for item in intervals])


def mapping_hash(mappings: Iterable[SymbolMapping]) -> str:
    return sha256([asdict(item) for item in mappings])


def universe_hash(intervals: Iterable[MembershipInterval], mappings: Iterable[SymbolMapping]) -> str:
    return sha256({"schema_version": "SP500_PIT_V1", "membership_intervals": [asdict(item) for item in intervals], "symbol_mapping": [asdict(item) for item in mappings]})
