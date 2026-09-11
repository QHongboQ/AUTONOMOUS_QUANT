"""Structured, fail-closed validation for PIT universe outputs."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .canonical import deterministic_id
from .contracts import (
    FindingSeverity,
    FindingType,
    InstrumentEpisodeV1,
    ResolutionState,
    SourceManifestV1,
    ValidationFindingV1,
    normalize_ticker,
)


class PublicationBlockedError(RuntimeError):
    """Raised when authoritative defects prevent snapshot publication."""


class AmbiguousTickerEpisodeError(LookupError):
    """Raised when an undated ticker lookup has multiple valid episodes."""


def make_finding(
    finding_type: FindingType,
    severity: FindingSeverity,
    affected_ids: Iterable[str],
    message: str,
    *,
    resolution_state: ResolutionState = ResolutionState.MANUAL_REVIEW_REQUIRED,
) -> ValidationFindingV1:
    ids = tuple(sorted(set(affected_ids)))
    logical = {
        "schema_version": "ValidationFindingV1",
        "finding_type": finding_type.value,
        "severity": severity.value,
        "affected_ids": ids,
        "message": message,
        "resolution_state": resolution_state.value,
    }
    return ValidationFindingV1(
        finding_id=deterministic_id("P1VF-", logical),
        finding_type=finding_type,
        severity=severity,
        affected_ids=ids,
        message=message,
        resolution_state=resolution_state,
    )


def sources_are_independent(first: SourceManifestV1, second: SourceManifestV1) -> bool:
    """Shared provenance ancestry is one lineage, never multiple votes."""

    first_lineage = {first.source_id, *first.ancestry}
    second_lineage = {second.source_id, *second.ancestry}
    return first_lineage.isdisjoint(second_lineage)


def validate_episodes(episodes: Iterable[InstrumentEpisodeV1]) -> tuple[ValidationFindingV1, ...]:
    findings: list[ValidationFindingV1] = []
    episodes_tuple = tuple(episodes)
    by_id: dict[str, list[InstrumentEpisodeV1]] = defaultdict(list)
    by_ticker: dict[str, list[InstrumentEpisodeV1]] = defaultdict(list)
    for episode in episodes_tuple:
        by_id[episode.episode_id].append(episode)
        if episode.resolution_state is ResolutionState.RESOLVED:
            by_ticker[episode.normalized_ticker].append(episode)
    for episode_id, matches in sorted(by_id.items()):
        if len(matches) > 1:
            findings.append(make_finding(
                FindingType.DUPLICATE_EPISODE,
                FindingSeverity.ERROR,
                (episode_id,),
                "duplicate episode_id",
            ))
    for ticker, matches in sorted(by_ticker.items()):
        ordered = sorted(matches, key=lambda item: (item.valid_from, item.valid_to, item.episode_id))
        for left, right in zip(ordered, ordered[1:]):
            if right.valid_from < left.valid_to:
                findings.append(make_finding(
                    FindingType.OVERLAPPING_TICKER_EPISODES,
                    FindingSeverity.CRITICAL,
                    (left.episode_id, right.episode_id),
                    f"resolved ownership overlaps for ticker {ticker}",
                ))
    return tuple(findings)


def lookup_episode(
    episodes: Iterable[InstrumentEpisodeV1],
    ticker: str,
    session: str | None = None,
) -> InstrumentEpisodeV1:
    normalized = normalize_ticker(ticker)
    matches = sorted(
        (
            item for item in episodes
            if item.normalized_ticker == normalized
            and item.resolution_state is ResolutionState.RESOLVED
        ),
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


def validate_year_continuity(
    prior_close: Iterable[str],
    next_open: Iterable[str],
    boundary_event_ids: Iterable[str] = (),
) -> tuple[ValidationFindingV1, ...]:
    if set(prior_close) == set(next_open):
        return ()
    return (make_finding(
        FindingType.YEAR_CONTINUITY_BREAK,
        FindingSeverity.ERROR,
        boundary_event_ids,
        "year boundary rosters differ without a fully reconciled transition",
    ),)


def validate_terminal_set(
    actual: Iterable[str],
    expected: Iterable[str],
    evidence_ids: Iterable[str] = (),
) -> tuple[ValidationFindingV1, ...]:
    if set(actual) == set(expected):
        return ()
    return (make_finding(
        FindingType.TERMINAL_SET_MISMATCH,
        FindingSeverity.ERROR,
        evidence_ids,
        "terminal roster differs from pinned accepted reference",
    ),)


def validate_publishable(
    episodes: Iterable[InstrumentEpisodeV1],
    findings: Iterable[ValidationFindingV1],
) -> None:
    episodes_tuple = tuple(episodes)
    all_findings = tuple(findings) + validate_episodes(episodes_tuple)
    unresolved = [
        finding for finding in all_findings
        if finding.severity in {FindingSeverity.ERROR, FindingSeverity.CRITICAL}
        and finding.resolution_state is not ResolutionState.RESOLVED
    ]
    non_resolved = [
        episode.episode_id for episode in episodes_tuple
        if episode.resolution_state is not ResolutionState.RESOLVED
    ]
    if unresolved or non_resolved:
        ids = [finding.finding_id for finding in unresolved] + non_resolved
        raise PublicationBlockedError("publication blocked: " + ",".join(sorted(ids)))
