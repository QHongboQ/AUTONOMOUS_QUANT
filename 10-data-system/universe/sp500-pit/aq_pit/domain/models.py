"""Minimum immutable contracts owned by the active P1 research path."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable

from ..canonical import deterministic_id, sha256_hex


_TICKER = re.compile(r"^[A-Z0-9][A-Z0-9.\-]*$")


def _iso(value: str | None, name: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO date")
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO date") from exc


def normalize_ticker(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("ticker must be non-empty text")
    normalized = value.strip().upper()
    if not _TICKER.fullmatch(normalized):
        raise ValueError(f"unsupported ticker token: {value!r}")
    return normalized


@dataclass(frozen=True, slots=True)
class SnapshotObservationV1:
    observation_id: str
    index_id: str
    effective_session: str
    tickers: tuple[str, ...]
    source_id: str
    evidence_hash: str
    schema_version: str = "SnapshotObservationV1"

    def __post_init__(self) -> None:
        _iso(self.effective_session, "effective_session")
        normalized = tuple(sorted(normalize_ticker(item) for item in self.tickers))
        if not normalized or len(normalized) != len(set(normalized)):
            raise ValueError("snapshot tickers must be non-empty and unique")
        object.__setattr__(self, "tickers", normalized)


@dataclass(frozen=True, slots=True)
class ResolvedObservationV1:
    observation_id: str
    index_id: str
    effective_session: str
    tickers: tuple[str, ...]
    source_id: str
    evidence_hash: str
    applied_overlay_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TickerIdentityEventV1:
    event_id: str
    old_ticker: str
    new_ticker: str
    announcement_date: str | None
    effective_date: str
    effective_session: str
    boundary_semantics: str
    source_id: str
    evidence_hash: str
    identity_anchor: str | None
    ambiguity_state: str = "CLEAR"
    schema_version: str = "TickerIdentityEventV1"


@dataclass(frozen=True, slots=True)
class IndexMembershipEventV1:
    event_id: str
    index_id: str
    action: str
    source_ticker: str
    announcement_date: str | None
    effective_date: str
    effective_session: str
    boundary_semantics: str
    source_id: str
    evidence_hash: str
    reason: str | None
    schema_version: str = "IndexMembershipEventV1"


@dataclass(frozen=True, slots=True)
class InstrumentEpisodeV1:
    episode_id: str
    index_id: str
    source_ticker: str
    normalized_ticker: str
    valid_from: str
    valid_to: str
    membership_from: str
    membership_to: str
    membership_source_ids: tuple[str, ...]
    ticker_source_ids: tuple[str, ...]
    source_event_ids: tuple[str, ...]
    provenance_hash: str
    resolution_state: str = "RESOLVED"
    schema_version: str = "InstrumentEpisodeV1"

    @classmethod
    def create(
        cls,
        *,
        index_id: str,
        ticker: str,
        valid_from: str,
        valid_to: str,
        membership_source_ids: Iterable[str],
        ticker_source_ids: Iterable[str],
        source_event_ids: Iterable[str],
        provenance_inputs: object,
    ) -> "InstrumentEpisodeV1":
        normalized = normalize_ticker(ticker)
        membership_sources = tuple(sorted(set(membership_source_ids)))
        ticker_sources = tuple(sorted(set(ticker_source_ids)))
        event_ids = tuple(sorted(set(source_event_ids)))
        identity = {
            "index_id": index_id,
            "ticker": normalized,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "membership_source_ids": membership_sources,
            "ticker_source_ids": ticker_sources,
            "source_event_ids": event_ids,
        }
        return cls(
            episode_id=deterministic_id("P1EP-", identity),
            index_id=index_id,
            source_ticker=normalized,
            normalized_ticker=normalized,
            valid_from=valid_from,
            valid_to=valid_to,
            membership_from=valid_from,
            membership_to=valid_to,
            membership_source_ids=membership_sources,
            ticker_source_ids=ticker_sources,
            source_event_ids=event_ids,
            provenance_hash=sha256_hex(provenance_inputs),
        )


class AmbiguousTickerEpisodeError(LookupError):
    pass


def lookup_episode(
    episodes: Iterable[InstrumentEpisodeV1],
    ticker: str,
    session: str | None = None,
) -> InstrumentEpisodeV1:
    normalized = normalize_ticker(ticker)
    matches = sorted(
        (item for item in episodes if item.normalized_ticker == normalized),
        key=lambda item: (item.valid_from, item.valid_to, item.episode_id),
    )
    if session is None:
        if len(matches) > 1:
            raise AmbiguousTickerEpisodeError("AMBIGUOUS_TICKER_EPISODE")
        if not matches:
            raise KeyError(normalized)
        return matches[0]
    dated = [item for item in matches if item.valid_from <= session < item.valid_to]
    if len(dated) > 1:
        raise AmbiguousTickerEpisodeError("AMBIGUOUS_TICKER_EPISODE")
    if not dated:
        raise KeyError((normalized, session))
    return dated[0]
