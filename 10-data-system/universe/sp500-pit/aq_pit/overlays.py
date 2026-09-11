"""Generic detection and one authoritative overlay validation/application path."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    AmbiguityState,
    FindingSeverity,
    FindingType,
    OverlayOperation,
    ReviewState,
    SessionBoundary,
    SnapshotObservationV1,
    TickerEpisodeOverlayV1,
    TickerIdentityEventV1,
    ValidationFindingV1,
    normalize_ticker,
)
from .validation import make_finding


@dataclass(frozen=True, slots=True)
class ResolvedObservation:
    observation_id: str
    index_id: str
    effective_session: str
    tickers: tuple[str, ...]
    source_id: str
    evidence_hash: str
    applied_overlay_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OverlayApplicationResult:
    observations: tuple[ResolvedObservation, ...]
    applied_pairs: tuple[tuple[str, str], ...]
    findings: tuple[ValidationFindingV1, ...]


def detect_future_ticker_backfill(
    observations: tuple[SnapshotObservationV1, ...],
    ticker_events: tuple[TickerIdentityEventV1, ...],
) -> tuple[ValidationFindingV1, ...]:
    """Detect successor-before-boundary and predecessor-after-boundary observations."""

    findings: list[ValidationFindingV1] = []
    for event in sorted(ticker_events, key=lambda item: (item.effective_session, item.event_id)):
        old = normalize_ticker(event.old_ticker)
        new = normalize_ticker(event.new_ticker)
        for observation in sorted(observations, key=lambda item: (item.effective_session, item.observation_id)):
            if new in observation.tickers and observation.effective_session < event.effective_session:
                findings.append(make_finding(
                    FindingType.FUTURE_TICKER_BEFORE_RENAME,
                    FindingSeverity.ERROR,
                    (observation.observation_id, event.event_id),
                    f"{new} observed before identity boundary {event.effective_session}",
                ))
            if old in observation.tickers and observation.effective_session >= event.effective_session:
                findings.append(make_finding(
                    FindingType.STALE_OLD_TICKER_AFTER_RENAME,
                    FindingSeverity.ERROR,
                    (observation.observation_id, event.event_id),
                    f"{old} observed at or after identity boundary {event.effective_session}",
                ))
    return tuple(findings)


def detect_episode_scoped_ticker_findings(
    observations: tuple[ResolvedObservation, ...],
    ticker_events: tuple[TickerIdentityEventV1, ...],
    membership_events: tuple[object, ...] = (),
) -> tuple[ValidationFindingV1, ...]:
    """Detect rename-label defects within the membership episode near each boundary.

    Successor checks are limited to the contiguous successor run immediately before
    the identity boundary.  This prevents a disconnected historical owner of the
    same ticker text from being attributed to a later identity event.  A later use
    of the predecessor is exempt only inside an independently derived membership
    episode that starts while both the renamed successor and reused predecessor are
    observed.
    """

    from .contracts import IndexMembershipEventV1, MembershipAction

    ordered = tuple(sorted(
        observations,
        key=lambda item: (item.effective_session, item.observation_id),
    ))
    by_session = {item.effective_session: item for item in ordered}
    findings: list[ValidationFindingV1] = []
    accepted_membership_events = tuple(
        item for item in membership_events
        if isinstance(item, IndexMembershipEventV1)
    )

    for event in sorted(ticker_events, key=lambda item: (item.effective_session, item.event_id)):
        old = normalize_ticker(event.old_ticker)
        new = normalize_ticker(event.new_ticker)

        before = [item for item in ordered if item.effective_session < event.effective_session]
        predecessor_run: list[ResolvedObservation] = []
        for observation in reversed(before):
            if old not in observation.tickers:
                break
            predecessor_run.append(observation)
        if predecessor_run:
            scope_start = predecessor_run[-1].effective_session
            future_rows = [
                item for item in before
                if item.effective_session >= scope_start and new in item.tickers
            ]
        else:
            future_rows = []
            for observation in reversed(before):
                if new not in observation.tickers:
                    break
                future_rows.append(observation)
            future_rows.reverse()
        for observation in future_rows:
            findings.append(make_finding(
                FindingType.FUTURE_TICKER_BEFORE_RENAME,
                FindingSeverity.ERROR,
                (observation.observation_id, event.event_id),
                f"{new} observed in the predecessor episode before identity boundary {event.effective_session}",
            ))

        reuse_intervals: list[tuple[str, str | None]] = []
        additions = sorted(
            (
                item for item in accepted_membership_events
                if item.action is MembershipAction.ADD
                and normalize_ticker(item.source_ticker) == old
                and item.effective_session >= event.effective_session
            ),
            key=lambda item: (item.effective_session, item.event_id),
        )
        removals = sorted(
            (
                item for item in accepted_membership_events
                if item.action is MembershipAction.REMOVE
                and normalize_ticker(item.source_ticker) == old
                and item.effective_session >= event.effective_session
            ),
            key=lambda item: (item.effective_session, item.event_id),
        )
        for addition in additions:
            boundary_observation = by_session.get(addition.effective_session)
            if boundary_observation is None or not {
                old, new,
            } <= set(boundary_observation.tickers):
                continue
            end = next(
                (
                    removal.effective_session for removal in removals
                    if removal.effective_session > addition.effective_session
                ),
                None,
            )
            reuse_intervals.append((addition.effective_session, end))

        for observation in ordered:
            if observation.effective_session < event.effective_session or old not in observation.tickers:
                continue
            inside_reuse = any(
                start <= observation.effective_session
                and (end is None or observation.effective_session < end)
                for start, end in reuse_intervals
            )
            if not inside_reuse:
                findings.append(make_finding(
                    FindingType.STALE_OLD_TICKER_AFTER_RENAME,
                    FindingSeverity.ERROR,
                    (observation.observation_id, event.event_id),
                    f"{old} observed outside an established episode at or after identity boundary {event.effective_session}",
                ))
    return tuple(sorted(findings, key=lambda item: item.finding_id))


def apply_ticker_overlays(
    observations: tuple[SnapshotObservationV1, ...],
    ticker_events: tuple[TickerIdentityEventV1, ...],
    overlays: tuple[TickerEpisodeOverlayV1, ...],
) -> OverlayApplicationResult:
    """Validate and apply overlays; only returned applied pairs may suppress findings."""

    observation_map = {item.observation_id: item for item in observations}
    event_map = {item.event_id: item for item in ticker_events}
    resolved = {item.observation_id: list(item.tickers) for item in observations}
    applied_by_observation: dict[str, list[str]] = {
        item.observation_id: [] for item in observations
    }
    applied_pairs: list[tuple[str, str]] = []
    findings: list[ValidationFindingV1] = []

    for overlay in sorted(overlays, key=lambda item: item.overlay_id):
        if overlay.review_state is not ReviewState.ACCEPTED:
            continue
        observation = observation_map.get(overlay.raw_observation_id)
        event = event_map.get(overlay.ticker_identity_event_id)
        valid = observation is not None and event is not None
        if valid:
            assert observation is not None and event is not None
            evidence = set(overlay.evidence_hashes)
            old = normalize_ticker(event.old_ticker)
            new = normalize_ticker(event.new_ticker)
            common = (
                overlay.effective_session == event.effective_session
                and observation.effective_session < event.effective_session
                and new in observation.tickers
                and {observation.evidence_hash, event.evidence_hash} <= evidence
                and event.boundary_semantics is not SessionBoundary.AMBIGUOUS
                and event.ambiguity_state is AmbiguityState.CLEAR
            )
            valid = common and (
                overlay.operation is OverlayOperation.MAP_SUCCESSOR_TO_PREDECESSOR
                and old not in observation.tickers
                or overlay.operation is OverlayOperation.DROP_DUPLICATE_SUCCESSOR_BEFORE_BOUNDARY
                and old in observation.tickers
            )
        if not valid:
            findings.append(make_finding(
                FindingType.INVALID_AUTHORITY_REFERENCE,
                FindingSeverity.ERROR,
                (overlay.overlay_id, overlay.raw_observation_id, overlay.ticker_identity_event_id),
                "accepted ticker overlay is unbound or not applicable",
            ))
            continue
        assert observation is not None and event is not None
        tickers = resolved[observation.observation_id]
        old = normalize_ticker(event.old_ticker)
        new = normalize_ticker(event.new_ticker)
        map_successor = overlay.operation is OverlayOperation.MAP_SUCCESSOR_TO_PREDECESSOR
        applicable = new in tickers and (
            map_successor and old not in tickers
            or not map_successor and old in tickers
        )
        if not applicable:
            findings.append(make_finding(
                FindingType.INVALID_AUTHORITY_REFERENCE,
                FindingSeverity.ERROR,
                (overlay.overlay_id, observation.observation_id, event.event_id),
                "accepted ticker overlay conflicts with another applied overlay",
            ))
            continue
        if map_successor:
            tickers[tickers.index(new)] = old
        else:
            tickers.remove(new)
        applied_by_observation[observation.observation_id].append(overlay.overlay_id)
        applied_pairs.append((observation.observation_id, event.event_id))

    rows = tuple(
        ResolvedObservation(
            observation_id=observation.observation_id,
            index_id=observation.index_id,
            effective_session=observation.effective_session,
            tickers=tuple(sorted(resolved[observation.observation_id])),
            source_id=observation.source_id,
            evidence_hash=observation.evidence_hash,
            applied_overlay_ids=tuple(sorted(applied_by_observation[observation.observation_id])),
        )
        for observation in sorted(observations, key=lambda item: item.observation_id)
    )
    return OverlayApplicationResult(
        observations=rows,
        applied_pairs=tuple(sorted(applied_pairs)),
        findings=tuple(sorted(findings, key=lambda item: item.finding_id)),
    )


def resolve_observation(
    observation: SnapshotObservationV1,
    ticker_events: tuple[TickerIdentityEventV1, ...],
    overlays: tuple[TickerEpisodeOverlayV1, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Compatibility wrapper over the single authoritative application path."""

    result = apply_ticker_overlays((observation,), ticker_events, overlays)
    row = result.observations[0]
    return row.tickers, row.applied_overlay_ids
