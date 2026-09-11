"""Pure deterministic compiler from pinned PIT evidence to ticker episodes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .canonical import sha256_hex
from .contracts import (
    AmbiguityState,
    CompilationResultV1,
    CompilePolicyV1,
    CorporateActionEventV1,
    CorrectionOperation,
    FindingSeverity,
    FindingType,
    IndexMembershipEventV1,
    InstrumentEpisodeV1,
    MembershipAction,
    MembershipCorrectionV1,
    ResolutionState,
    ReviewState,
    SessionBoundary,
    SnapshotObservationV1,
    SourceManifestV1,
    SourceRole,
    TickerEpisodeOverlayV1,
    TickerIdentityEventV1,
    ValidationFindingV1,
    normalize_ticker,
)
from .overlays import detect_future_ticker_backfill, finding_resolved_by_overlay, resolve_observation
from .validation import make_finding, validate_episodes


@dataclass(slots=True)
class _ActiveEpisode:
    ticker: str
    opened: str
    membership_source_ids: set[str]
    ticker_source_ids: set[str]
    source_event_ids: set[str]
    provenance_records: list[object]


def _close(
    active: _ActiveEpisode,
    index_id: str,
    boundary: str,
    extra_records: Iterable[object] = (),
    extra_event_ids: Iterable[str] = (),
) -> InstrumentEpisodeV1:
    events = {*active.source_event_ids, *extra_event_ids}
    provenance = [*active.provenance_records, *extra_records]
    return InstrumentEpisodeV1.create(
        index_id=index_id,
        source_ticker=active.ticker,
        valid_from=active.opened,
        valid_to=boundary,
        membership_from=active.opened,
        membership_to=boundary,
        membership_source_ids=active.membership_source_ids,
        ticker_source_ids=active.ticker_source_ids,
        source_event_ids=events,
        provenance_inputs=provenance,
    )


def _event_key(event: object) -> tuple[str, int, str]:
    if isinstance(event, TickerIdentityEventV1):
        return (event.effective_session, 0, event.event_id)
    if isinstance(event, IndexMembershipEventV1):
        priority = 1 if event.action is MembershipAction.REMOVE else 2
        return (event.effective_session, priority, event.event_id)
    if isinstance(event, MembershipCorrectionV1):
        priority = 1 if event.operation is CorrectionOperation.REMOVE else 2
        return (event.effective_session, priority, event.correction_id)
    raise TypeError(type(event).__name__)


def compile_universe(
    *,
    policy: CompilePolicyV1,
    manifests: tuple[SourceManifestV1, ...],
    observations: tuple[SnapshotObservationV1, ...],
    membership_events: tuple[IndexMembershipEventV1, ...] = (),
    ticker_events: tuple[TickerIdentityEventV1, ...] = (),
    corporate_events: tuple[CorporateActionEventV1, ...] = (),
    overlays: tuple[TickerEpisodeOverlayV1, ...] = (),
    corrections: tuple[MembershipCorrectionV1, ...] = (),
) -> CompilationResultV1:
    """Compile canonical inputs without I/O, clocks, caches, or global state."""

    # Corporate events are retained in the result hash but never enter membership state.
    findings: list[ValidationFindingV1] = []
    episodes: list[InstrumentEpisodeV1] = []
    active: dict[str, _ActiveEpisode] = {}
    manifests_by_id = {manifest.source_id: manifest for manifest in manifests}

    all_ids: list[str] = [event.event_id for event in membership_events]
    all_ids += [event.event_id for event in ticker_events]
    duplicates = sorted({item for item in all_ids if all_ids.count(item) > 1})
    for event_id in duplicates:
        findings.append(make_finding(
            FindingType.DUPLICATE_EVENT,
            FindingSeverity.ERROR,
            (event_id,),
            "event_id is duplicated",
        ))
    canonical_events: dict[str, list[str]] = {}
    for event in (*membership_events, *ticker_events):
        if isinstance(event, IndexMembershipEventV1):
            content = {
                "kind": "membership",
                "index_id": event.index_id,
                "action": event.action,
                "source_ticker": event.source_ticker,
                "announcement_date": event.announcement_date,
                "effective_date": event.effective_date,
                "effective_session": event.effective_session,
                "boundary_semantics": event.boundary_semantics,
                "source_id": event.source_id,
                "evidence_hash": event.evidence_hash,
                "reason": event.reason,
            }
        else:
            content = {
                "kind": "ticker_identity",
                "old_ticker": event.old_ticker,
                "new_ticker": event.new_ticker,
                "announcement_date": event.announcement_date,
                "effective_date": event.effective_date,
                "effective_session": event.effective_session,
                "boundary_semantics": event.boundary_semantics,
                "source_id": event.source_id,
                "evidence_hash": event.evidence_hash,
                "identity_anchor": event.identity_anchor,
                "ambiguity_state": event.ambiguity_state,
            }
        canonical_events.setdefault(sha256_hex(content), []).append(event.event_id)
    for event_ids in canonical_events.values():
        if len(event_ids) > 1:
            findings.append(make_finding(
                FindingType.DUPLICATE_EVENT,
                FindingSeverity.ERROR,
                event_ids,
                "canonical event content is duplicated under multiple IDs",
            ))

    ignored_event_ids = {
        target
        for correction in corrections
        if correction.review_state is ReviewState.ACCEPTED
        and correction.operation is CorrectionOperation.IGNORE_EVENT
        for target in correction.target_source_or_event_ids
    }
    for correction in corrections:
        if correction.review_state is ReviewState.UNRESOLVED:
            findings.append(make_finding(
                FindingType.UNRESOLVED_CORRECTION,
                FindingSeverity.ERROR,
                (correction.correction_id,),
                "correction is visible but not accepted",
            ))

    detector_findings = detect_future_ticker_backfill(observations, ticker_events)
    findings.extend(
        finding for finding in detector_findings
        if not finding_resolved_by_overlay(finding, overlays)
    )

    seed_candidates = [
        observation for observation in observations
        if observation.index_id == policy.index_id
        and observation.effective_session == policy.start_session
    ]
    if len(seed_candidates) != 1:
        findings.append(make_finding(
            FindingType.MISSING_EVIDENCE,
            FindingSeverity.CRITICAL,
            tuple(item.observation_id for item in seed_candidates),
            "exactly one start-session seed observation is required",
        ))
    else:
        seed = seed_candidates[0]
        seed_manifest = manifests_by_id.get(seed.source_id)
        if seed_manifest is None or seed_manifest.source_role is not SourceRole.HISTORICAL_SEED:
            findings.append(make_finding(
                FindingType.MISSING_EVIDENCE,
                FindingSeverity.CRITICAL,
                (seed.observation_id, seed.source_id),
                "seed observation requires a HISTORICAL_SEED manifest",
            ))
            resolved_tickers, applied_overlay_ids = (), ()
        else:
            resolved_tickers, applied_overlay_ids = resolve_observation(seed, ticker_events, overlays)
        applied_overlays = [item for item in overlays if item.overlay_id in applied_overlay_ids]
        for ticker in resolved_tickers:
            relevant = [
                item for item in applied_overlays
                if normalize_ticker(next(
                    event.old_ticker for event in ticker_events
                    if event.event_id == item.ticker_identity_event_id
                )) == ticker
            ]
            active[ticker] = _ActiveEpisode(
                ticker=ticker,
                opened=policy.start_session,
                membership_source_ids={seed.source_id},
                ticker_source_ids={seed.source_id, *(item.overlay_id for item in relevant)},
                source_event_ids={seed.observation_id, *(item.overlay_id for item in relevant)},
                provenance_records=[seed, *relevant],
            )

    operations: list[object] = [
        event for event in (*ticker_events, *membership_events)
        if getattr(event, "event_id") not in ignored_event_ids
        and policy.start_session < event.effective_session < policy.end_session
    ]
    operations.extend(
        correction for correction in corrections
        if correction.review_state is ReviewState.ACCEPTED
        and correction.operation in {CorrectionOperation.ADD, CorrectionOperation.REMOVE}
        and policy.start_session < correction.effective_session < policy.end_session
    )
    operations.sort(key=_event_key)

    seen_ids: set[str] = set()
    for operation in operations:
        operation_id = getattr(operation, "event_id", getattr(operation, "correction_id", ""))
        if operation_id in seen_ids:
            continue
        seen_ids.add(operation_id)
        source_id = operation.source_id
        evidence_hash = operation.evidence_hash
        source_manifest = manifests_by_id.get(source_id)
        allowed_roles: set[SourceRole]
        if isinstance(operation, IndexMembershipEventV1):
            allowed_roles = {
                SourceRole.PRECISE_MEMBERSHIP_EVENTS,
                SourceRole.OFFICIAL_CONFLICT_RESOLUTION,
            }
        elif isinstance(operation, TickerIdentityEventV1):
            allowed_roles = {
                SourceRole.TICKER_IDENTITY_EVIDENCE,
                SourceRole.OFFICIAL_CONFLICT_RESOLUTION,
            }
        else:
            allowed_roles = {SourceRole.OFFICIAL_CONFLICT_RESOLUTION}
        if source_manifest is None or source_manifest.source_role not in allowed_roles or not evidence_hash:
            findings.append(make_finding(
                FindingType.MISSING_EVIDENCE,
                FindingSeverity.ERROR,
                (operation_id, source_id),
                "event source manifest, accepted source role, or evidence hash is missing",
            ))
            continue
        if isinstance(operation, (IndexMembershipEventV1, TickerIdentityEventV1)) and (
            operation.boundary_semantics is SessionBoundary.AMBIGUOUS
            or isinstance(operation, TickerIdentityEventV1)
            and operation.ambiguity_state is AmbiguityState.AMBIGUOUS
        ):
            findings.append(make_finding(
                FindingType.AMBIGUOUS_SOURCE_BOUNDARY,
                FindingSeverity.ERROR,
                (operation_id,),
                "ambiguous source boundary cannot produce resolved output",
            ))
            continue

        if isinstance(operation, TickerIdentityEventV1):
            old = normalize_ticker(operation.old_ticker)
            new = normalize_ticker(operation.new_ticker)
            if old not in active:
                continue
            if new in active:
                findings.append(make_finding(
                    FindingType.OVERLAPPING_TICKER_EPISODES,
                    FindingSeverity.CRITICAL,
                    (operation.event_id,),
                    f"rename successor {new} is already active",
                ))
                continue
            prior = active.pop(old)
            episodes.append(_close(prior, policy.index_id, operation.effective_session, (operation,), (operation.event_id,)))
            active[new] = _ActiveEpisode(
                ticker=new,
                opened=operation.effective_session,
                membership_source_ids=set(prior.membership_source_ids),
                ticker_source_ids={*prior.ticker_source_ids, operation.source_id},
                source_event_ids={*prior.source_event_ids, operation.event_id},
                provenance_records=[*prior.provenance_records, operation],
            )
            continue

        ticker = normalize_ticker(operation.source_ticker if isinstance(operation, IndexMembershipEventV1) else operation.ticker)
        action = operation.action if isinstance(operation, IndexMembershipEventV1) else MembershipAction(operation.operation.value)
        session = operation.effective_session
        if action is MembershipAction.ADD:
            if ticker in active:
                findings.append(make_finding(
                    FindingType.ADD_PRESENT,
                    FindingSeverity.ERROR,
                    (operation_id,),
                    f"cannot add already-active ticker {ticker}",
                ))
                continue
            active[ticker] = _ActiveEpisode(
                ticker=ticker,
                opened=session,
                membership_source_ids={source_id},
                ticker_source_ids={source_id},
                source_event_ids={operation_id},
                provenance_records=[operation],
            )
        else:
            if ticker not in active:
                findings.append(make_finding(
                    FindingType.REMOVE_ABSENT,
                    FindingSeverity.ERROR,
                    (operation_id,),
                    f"cannot remove inactive ticker {ticker}",
                ))
                continue
            episodes.append(_close(active.pop(ticker), policy.index_id, session, (operation,), (operation_id,)))

    for ticker in sorted(active):
        episodes.append(_close(active[ticker], policy.index_id, policy.end_session))
    episodes.sort(key=lambda item: (item.valid_from, item.normalized_ticker, item.valid_to, item.episode_id))
    findings.extend(validate_episodes(episodes))
    findings.sort(key=lambda item: item.finding_id)
    payload = {
        "schema_version": "CompilationResultV1",
        "policy": policy,
        "manifests": tuple(sorted(manifests, key=lambda item: item.source_id)),
        "observations": tuple(sorted(observations, key=lambda item: item.observation_id)),
        "membership_events": tuple(sorted(membership_events, key=lambda item: item.event_id)),
        "ticker_events": tuple(sorted(ticker_events, key=lambda item: item.event_id)),
        "corporate_events": tuple(sorted(corporate_events, key=lambda item: item.event_id)),
        "overlays": tuple(sorted(overlays, key=lambda item: item.overlay_id)),
        "corrections": tuple(sorted(corrections, key=lambda item: item.correction_id)),
        "episodes": tuple(episodes),
        "findings": tuple(findings),
    }
    return CompilationResultV1(
        episodes=tuple(episodes),
        findings=tuple(findings),
        ticker_overlays=tuple(sorted(overlays, key=lambda item: item.overlay_id)),
        membership_corrections=tuple(sorted(corrections, key=lambda item: item.correction_id)),
        corporate_action_events=tuple(sorted(corporate_events, key=lambda item: item.event_id)),
        output_hash=sha256_hex(payload),
    )
