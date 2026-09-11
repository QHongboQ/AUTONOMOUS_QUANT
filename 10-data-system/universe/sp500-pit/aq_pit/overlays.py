"""Generic detection and evidence-driven ticker observation overlays."""

from __future__ import annotations

from .contracts import (
    FindingSeverity,
    FindingType,
    OverlayOperation,
    ReviewState,
    SnapshotObservationV1,
    TickerEpisodeOverlayV1,
    TickerIdentityEventV1,
    ValidationFindingV1,
    normalize_ticker,
)
from .validation import make_finding


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


def resolve_observation(
    observation: SnapshotObservationV1,
    ticker_events: tuple[TickerIdentityEventV1, ...],
    overlays: tuple[TickerEpisodeOverlayV1, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return resolved tickers and applied overlay IDs without mutating raw evidence."""

    tickers = list(observation.tickers)
    applied: list[str] = []
    events = {item.event_id: item for item in ticker_events}
    for overlay in sorted(overlays, key=lambda item: item.overlay_id):
        if overlay.raw_observation_id != observation.observation_id:
            continue
        if overlay.review_state is not ReviewState.ACCEPTED:
            continue
        event = events.get(overlay.ticker_identity_event_id)
        if event is None or overlay.effective_session != event.effective_session:
            continue
        if observation.effective_session >= event.effective_session:
            continue
        if overlay.operation is OverlayOperation.MAP_SUCCESSOR_TO_PREDECESSOR:
            new = normalize_ticker(event.new_ticker)
            old = normalize_ticker(event.old_ticker)
            if new in tickers and old not in tickers:
                tickers[tickers.index(new)] = old
                applied.append(overlay.overlay_id)
    return tuple(sorted(tickers)), tuple(sorted(applied))


def finding_resolved_by_overlay(
    finding: ValidationFindingV1,
    overlays: tuple[TickerEpisodeOverlayV1, ...],
) -> bool:
    if finding.finding_type is not FindingType.FUTURE_TICKER_BEFORE_RENAME:
        return False
    affected = set(finding.affected_ids)
    return any(
        overlay.review_state is ReviewState.ACCEPTED
        and {overlay.raw_observation_id, overlay.ticker_identity_event_id} <= affected
        for overlay in overlays
    )
