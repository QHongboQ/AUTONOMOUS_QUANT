"""Immutable contracts for the S&P 500 PIT universe runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import re
from typing import Iterable

from .canonical import deterministic_id, sha256_hex


__all__ = [
    "AmbiguityState", "CompilationResultV1", "CompilePolicyV1",
    "CorporateActionEventV1", "CorrectionOperation", "FindingSeverity",
    "FindingType", "IndexMembershipEventV1", "InstrumentEpisodeV1",
    "MembershipAction", "MembershipCorrectionV1", "OverlayOperation",
    "ResolutionState", "ReviewState", "SessionBoundary",
    "SnapshotObservationV1", "SourceManifestV1", "SourceRole",
    "TickerEpisodeOverlayV1", "TickerIdentityEventV1",
    "ValidationFindingV1", "normalize_ticker",
]


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-]*$")


def _require_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")


def _date(value: str | None, name: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if not isinstance(value, str):
        raise ValueError(f"{name} must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO date: {value!r}") from exc


def _hash(value: str, name: str) -> None:
    if not SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256")


def normalize_ticker(value: str) -> str:
    _require_text(value, "ticker")
    normalized = value.strip().upper()
    if not TICKER_RE.fullmatch(normalized):
        raise ValueError(f"unsupported ticker token: {value!r}")
    return normalized


def _sorted_unique(values: Iterable[str], name: str) -> tuple[str, ...]:
    result = tuple(sorted(values))
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must not contain duplicates")
    if any(not item for item in result):
        raise ValueError(f"{name} must contain non-empty values")
    return result


class SourceRole(str, Enum):
    HISTORICAL_SEED = "HISTORICAL_SEED"
    PRECISE_MEMBERSHIP_EVENTS = "PRECISE_MEMBERSHIP_EVENTS"
    TICKER_IDENTITY_EVIDENCE = "TICKER_IDENTITY_EVIDENCE"
    OFFICIAL_CONFLICT_RESOLUTION = "OFFICIAL_CONFLICT_RESOLUTION"
    DIAGNOSTIC_REFERENCE = "DIAGNOSTIC_REFERENCE"


class MembershipAction(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"


class SessionBoundary(str, Enum):
    BEFORE_MARKET_OPEN = "BEFORE_MARKET_OPEN"
    AFTER_MARKET_CLOSE = "AFTER_MARKET_CLOSE"
    EFFECTIVE_SESSION = "EFFECTIVE_SESSION"
    SOURCE_DEFINED = "SOURCE_DEFINED"
    AMBIGUOUS = "AMBIGUOUS"


class AmbiguityState(str, Enum):
    CLEAR = "CLEAR"
    AMBIGUOUS = "AMBIGUOUS"


class ResolutionState(str, Enum):
    RESOLVED = "RESOLVED"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"
    REJECTED = "REJECTED"


class ReviewState(str, Enum):
    ACCEPTED = "ACCEPTED"
    UNRESOLVED = "UNRESOLVED"
    REJECTED = "REJECTED"


class OverlayOperation(str, Enum):
    MAP_SUCCESSOR_TO_PREDECESSOR = "MAP_SUCCESSOR_TO_PREDECESSOR"
    DROP_DUPLICATE_SUCCESSOR_BEFORE_BOUNDARY = "DROP_DUPLICATE_SUCCESSOR_BEFORE_BOUNDARY"


class CorrectionOperation(str, Enum):
    ADD = "ADD"
    REMOVE = "REMOVE"
    IGNORE_EVENT = "IGNORE_EVENT"


class FindingSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class FindingType(str, Enum):
    AMBIGUOUS_SOURCE_BOUNDARY = "AMBIGUOUS_SOURCE_BOUNDARY"
    ADD_PRESENT = "ADD_PRESENT"
    REMOVE_ABSENT = "REMOVE_ABSENT"
    DUPLICATE_EVENT = "DUPLICATE_EVENT"
    DUPLICATE_EPISODE = "DUPLICATE_EPISODE"
    OVERLAPPING_TICKER_EPISODES = "OVERLAPPING_TICKER_EPISODES"
    FUTURE_TICKER_BEFORE_RENAME = "FUTURE_TICKER_BEFORE_RENAME"
    STALE_OLD_TICKER_AFTER_RENAME = "STALE_OLD_TICKER_AFTER_RENAME"
    AMBIGUOUS_TICKER_EPISODE = "AMBIGUOUS_TICKER_EPISODE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    UNRESOLVED_CORRECTION = "UNRESOLVED_CORRECTION"
    YEAR_CONTINUITY_BREAK = "YEAR_CONTINUITY_BREAK"
    TERMINAL_SET_MISMATCH = "TERMINAL_SET_MISMATCH"
    DUPLICATE_SOURCE = "DUPLICATE_SOURCE"
    FOREIGN_INDEX_INPUT = "FOREIGN_INDEX_INPUT"
    INVALID_AUTHORITY_REFERENCE = "INVALID_AUTHORITY_REFERENCE"


@dataclass(frozen=True, slots=True)
class SourceManifestV1:
    source_id: str
    source_role: SourceRole
    source_type: str
    source_url_or_repo: str
    source_commit_or_revision: str
    retrieved_at: str
    media_type: str
    byte_length: int
    sha256: str
    license_observation: str
    coverage_start: str
    coverage_end: str
    ancestry: tuple[str, ...]
    adapter_version: str
    schema_version: str = "SourceManifestV1"

    def __post_init__(self) -> None:
        for name in (
            "source_id", "source_type", "source_url_or_repo",
            "source_commit_or_revision", "retrieved_at", "media_type",
            "license_observation", "adapter_version",
        ):
            _require_text(getattr(self, name), name)
        if self.byte_length < 0:
            raise ValueError("byte_length cannot be negative")
        _hash(self.sha256, "sha256")
        _date(self.coverage_start, "coverage_start")
        _date(self.coverage_end, "coverage_end")
        if self.coverage_start > self.coverage_end:
            raise ValueError("source coverage is reversed")
        object.__setattr__(self, "ancestry", _sorted_unique(self.ancestry, "ancestry"))

    @property
    def manifest_hash(self) -> str:
        return sha256_hex(self)


@dataclass(frozen=True, slots=True)
class IndexMembershipEventV1:
    event_id: str
    index_id: str
    action: MembershipAction
    source_ticker: str
    announcement_date: str | None
    effective_date: str
    effective_session: str
    boundary_semantics: SessionBoundary
    source_id: str
    evidence_hash: str
    reason: str | None = None
    schema_version: str = "IndexMembershipEventV1"

    def __post_init__(self) -> None:
        _require_text(self.event_id, "event_id")
        _require_text(self.index_id, "index_id")
        normalize_ticker(self.source_ticker)
        _date(self.announcement_date, "announcement_date", optional=True)
        _date(self.effective_date, "effective_date")
        _date(self.effective_session, "effective_session")
        _require_text(self.source_id, "source_id")
        _hash(self.evidence_hash, "evidence_hash")


@dataclass(frozen=True, slots=True)
class TickerIdentityEventV1:
    event_id: str
    old_ticker: str
    new_ticker: str
    announcement_date: str | None
    effective_date: str
    effective_session: str
    boundary_semantics: SessionBoundary
    source_id: str
    evidence_hash: str
    identity_anchor: str | None = None
    ambiguity_state: AmbiguityState = AmbiguityState.CLEAR
    schema_version: str = "TickerIdentityEventV1"

    def __post_init__(self) -> None:
        _require_text(self.event_id, "event_id")
        old = normalize_ticker(self.old_ticker)
        new = normalize_ticker(self.new_ticker)
        if old == new:
            raise ValueError("ticker identity event must change ticker")
        _date(self.announcement_date, "announcement_date", optional=True)
        _date(self.effective_date, "effective_date")
        _date(self.effective_session, "effective_session")
        _require_text(self.source_id, "source_id")
        _hash(self.evidence_hash, "evidence_hash")


@dataclass(frozen=True, slots=True)
class CorporateActionEventV1:
    event_id: str
    action_type: str
    source_ticker: str
    contra_ticker: str | None
    effective_date: str
    effective_session: str | None
    source_id: str
    evidence_hash: str
    reason: str
    schema_version: str = "CorporateActionEventV1"

    def __post_init__(self) -> None:
        for name in ("event_id", "action_type", "source_id", "reason"):
            _require_text(getattr(self, name), name)
        normalize_ticker(self.source_ticker)
        if self.contra_ticker is not None:
            normalize_ticker(self.contra_ticker)
        _date(self.effective_date, "effective_date")
        _date(self.effective_session, "effective_session", optional=True)
        _hash(self.evidence_hash, "evidence_hash")


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
        _require_text(self.observation_id, "observation_id")
        _require_text(self.index_id, "index_id")
        _date(self.effective_session, "effective_session")
        normalized = tuple(sorted(normalize_ticker(ticker) for ticker in self.tickers))
        if len(normalized) != len(set(normalized)):
            raise ValueError("snapshot contains duplicate ticker")
        object.__setattr__(self, "tickers", normalized)
        _require_text(self.source_id, "source_id")
        _hash(self.evidence_hash, "evidence_hash")


@dataclass(frozen=True, slots=True)
class TickerEpisodeOverlayV1:
    overlay_id: str
    raw_observation_id: str
    ticker_identity_event_id: str
    effective_session: str
    operation: OverlayOperation
    reason: str
    evidence_hashes: tuple[str, ...]
    review_state: ReviewState
    schema_version: str = "TickerEpisodeOverlayV1"

    def __post_init__(self) -> None:
        for name in ("overlay_id", "raw_observation_id", "ticker_identity_event_id", "reason"):
            _require_text(getattr(self, name), name)
        _date(self.effective_session, "effective_session")
        hashes = _sorted_unique(self.evidence_hashes, "evidence_hashes")
        if not hashes:
            raise ValueError("overlay requires evidence hashes")
        for value in hashes:
            _hash(value, "evidence_hashes item")
        object.__setattr__(self, "evidence_hashes", hashes)


@dataclass(frozen=True, slots=True)
class MembershipCorrectionV1:
    correction_id: str
    target_source_or_event_ids: tuple[str, ...]
    operation: CorrectionOperation
    index_id: str
    ticker: str
    effective_session: str
    reason: str
    source_id: str
    evidence_hash: str
    review_state: ReviewState
    regression_test_id: str
    schema_version: str = "MembershipCorrectionV1"

    def __post_init__(self) -> None:
        for name in ("correction_id", "index_id", "reason", "source_id", "regression_test_id"):
            _require_text(getattr(self, name), name)
        targets = _sorted_unique(self.target_source_or_event_ids, "target_source_or_event_ids")
        if not targets:
            raise ValueError("correction requires a target")
        object.__setattr__(self, "target_source_or_event_ids", targets)
        normalize_ticker(self.ticker)
        _date(self.effective_session, "effective_session")
        _hash(self.evidence_hash, "evidence_hash")


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
    resolution_state: ResolutionState
    schema_version: str = "InstrumentEpisodeV1"

    def __post_init__(self) -> None:
        _require_text(self.episode_id, "episode_id")
        _require_text(self.index_id, "index_id")
        normalize_ticker(self.source_ticker)
        if normalize_ticker(self.normalized_ticker) != self.normalized_ticker:
            raise ValueError("normalized_ticker is not normalized")
        for name in ("valid_from", "valid_to", "membership_from", "membership_to"):
            _date(getattr(self, name), name)
        if self.resolution_state is ResolutionState.RESOLVED and not (
            self.valid_from <= self.membership_from < self.membership_to <= self.valid_to
        ):
            raise ValueError("resolved episode violates half-open interval invariants")
        for name in ("membership_source_ids", "ticker_source_ids", "source_event_ids"):
            object.__setattr__(self, name, _sorted_unique(getattr(self, name), name))
        if self.resolution_state is ResolutionState.RESOLVED and not (
            self.membership_source_ids and self.ticker_source_ids and self.source_event_ids
        ):
            raise ValueError("resolved episode requires source and event provenance")
        _hash(self.provenance_hash, "provenance_hash")

    @classmethod
    def create(
        cls,
        *,
        index_id: str,
        source_ticker: str,
        valid_from: str,
        valid_to: str,
        membership_from: str,
        membership_to: str,
        membership_source_ids: Iterable[str],
        ticker_source_ids: Iterable[str],
        source_event_ids: Iterable[str],
        provenance_inputs: object,
        resolution_state: ResolutionState = ResolutionState.RESOLVED,
    ) -> "InstrumentEpisodeV1":
        normalized = normalize_ticker(source_ticker)
        membership_sources = tuple(sorted(set(membership_source_ids)))
        ticker_sources = tuple(sorted(set(ticker_source_ids)))
        event_ids = tuple(sorted(set(source_event_ids)))
        identity = {
            "schema_version": "InstrumentEpisodeV1",
            "index_id": index_id,
            "normalized_ticker": normalized,
            "valid_from": valid_from,
            "valid_to": valid_to,
            "membership_from": membership_from,
            "membership_to": membership_to,
            "membership_source_ids": membership_sources,
            "ticker_source_ids": ticker_sources,
            "source_event_ids": event_ids,
        }
        return cls(
            episode_id=deterministic_id("P1EP-", identity),
            index_id=index_id,
            source_ticker=source_ticker,
            normalized_ticker=normalized,
            valid_from=valid_from,
            valid_to=valid_to,
            membership_from=membership_from,
            membership_to=membership_to,
            membership_source_ids=membership_sources,
            ticker_source_ids=ticker_sources,
            source_event_ids=event_ids,
            provenance_hash=sha256_hex(provenance_inputs),
            resolution_state=resolution_state,
        )


@dataclass(frozen=True, slots=True)
class ValidationFindingV1:
    finding_id: str
    finding_type: FindingType
    severity: FindingSeverity
    affected_ids: tuple[str, ...]
    message: str
    resolution_state: ResolutionState
    schema_version: str = "ValidationFindingV1"

    def __post_init__(self) -> None:
        _require_text(self.finding_id, "finding_id")
        _require_text(self.message, "message")
        object.__setattr__(self, "affected_ids", _sorted_unique(self.affected_ids, "affected_ids"))


@dataclass(frozen=True, slots=True)
class CompilePolicyV1:
    index_id: str
    start_session: str
    end_session: str
    calendar_version: str
    policy_version: str
    schema_version: str = "CompilePolicyV1"

    def __post_init__(self) -> None:
        _require_text(self.index_id, "index_id")
        _date(self.start_session, "start_session")
        _date(self.end_session, "end_session")
        if self.start_session >= self.end_session:
            raise ValueError("compile interval must be non-empty")
        _require_text(self.calendar_version, "calendar_version")
        _require_text(self.policy_version, "policy_version")


@dataclass(frozen=True, slots=True)
class CompilationResultV1:
    episodes: tuple[InstrumentEpisodeV1, ...]
    findings: tuple[ValidationFindingV1, ...]
    ticker_overlays: tuple[TickerEpisodeOverlayV1, ...]
    membership_corrections: tuple[MembershipCorrectionV1, ...]
    corporate_action_events: tuple[CorporateActionEventV1, ...]
    output_hash: str
    schema_version: str = "CompilationResultV1"

    def __post_init__(self) -> None:
        _hash(self.output_hash, "output_hash")
