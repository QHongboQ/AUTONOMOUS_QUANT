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
from .overlays import apply_ticker_overlays, detect_episode_scoped_ticker_findings
from .sources.fja_sp500 import (
    RECONCILED_DERIVATION_VERSION,
    build_reconciled_membership_event_manifest,
)
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


def _duplicate_ids(items: Iterable[object], attribute: str) -> set[str]:
    values = [getattr(item, attribute) for item in items]
    return {value for value in values if values.count(value) > 1}


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
    duplicate_source_ids = _duplicate_ids(manifests, "source_id")
    for source_id in sorted(duplicate_source_ids):
        matches = [manifest for manifest in manifests if manifest.source_id == source_id]
        identical = all(item == matches[0] for item in matches[1:])
        findings.append(make_finding(
            FindingType.DUPLICATE_SOURCE,
            FindingSeverity.ERROR if identical else FindingSeverity.CRITICAL,
            (source_id,),
            "duplicate source_id is forbidden"
            if identical else "conflicting manifests share one source_id",
        ))
    manifests_by_id = {
        manifest.source_id: manifest
        for manifest in manifests
        if manifest.source_id not in duplicate_source_ids
    }

    reconciled_event_source_ids = {
        event.source_id for event in membership_events
        if event.event_id.startswith("P1MEMR-")
        or (event.reason or "").startswith(RECONCILED_DERIVATION_VERSION)
    }
    invalid_reconciled_source_ids: set[str] = set()
    for manifest in manifests:
        is_reconciled_authority = (
            manifest.adapter_version == RECONCILED_DERIVATION_VERSION
            or manifest.source_type == "derived_identity_aware_resolved_snapshot_difference"
            or manifest.media_type
            == "application/vnd.aq.pit-reconciled-membership-events+json"
            or manifest.source_id in reconciled_event_source_ids
        )
        if not is_reconciled_authority:
            continue
        seed_manifests = [
            item for item in manifests
            if item.source_role is SourceRole.HISTORICAL_SEED
            and item.source_id in manifest.ancestry
        ]
        context_valid = len(seed_manifests) == 1
        if context_valid:
            try:
                canonical_resolution = apply_ticker_overlays(
                    observations,
                    ticker_events,
                    overlays,
                )
                expected = build_reconciled_membership_event_manifest(
                    seed_manifests[0],
                    observations,
                    canonical_resolution.observations,
                    ticker_events,
                    overlays,
                )
                context_valid = manifest == expected
            except ValueError:
                context_valid = False
        if not context_valid:
            invalid_reconciled_source_ids.add(manifest.source_id)
            findings.append(make_finding(
                FindingType.INVALID_AUTHORITY_REFERENCE,
                FindingSeverity.CRITICAL,
                (manifest.source_id,),
                "reconciled membership authority does not match the exact derivation context",
            ))

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

    membership_by_id = {event.event_id: event for event in membership_events}
    valid_corrections: list[MembershipCorrectionV1] = []
    for correction in corrections:
        if correction.review_state is ReviewState.UNRESOLVED:
            findings.append(make_finding(
                FindingType.UNRESOLVED_CORRECTION,
                FindingSeverity.ERROR,
                (correction.correction_id,),
                "correction is visible but not accepted",
            ))
            continue
        if correction.review_state is not ReviewState.ACCEPTED:
            continue
        correction_source = manifests_by_id.get(correction.source_id)
        valid_authority = (
            correction_source is not None
            and correction_source.source_role is SourceRole.OFFICIAL_CONFLICT_RESOLUTION
        )
        same_index = correction.index_id == policy.index_id
        valid_targets = True
        if correction.operation is CorrectionOperation.IGNORE_EVENT:
            targets = [membership_by_id.get(item) for item in correction.target_source_or_event_ids]
            valid_targets = bool(targets) and all(
                target is not None and target.index_id == policy.index_id
                for target in targets
            )
        if not valid_authority or not same_index or not valid_targets:
            finding_type = (
                FindingType.FOREIGN_INDEX_INPUT
                if not same_index
                or correction.operation is CorrectionOperation.IGNORE_EVENT
                and any(
                    target is not None and target.index_id != policy.index_id
                    for target in (membership_by_id.get(item) for item in correction.target_source_or_event_ids)
                )
                else FindingType.INVALID_AUTHORITY_REFERENCE
            )
            findings.append(make_finding(
                finding_type,
                FindingSeverity.ERROR,
                (correction.correction_id, *correction.target_source_or_event_ids),
                "accepted correction failed authority, index, or target validation",
            ))
            continue
        valid_corrections.append(correction)

    ignored_event_ids = {
        target
        for correction in valid_corrections
        if correction.operation is CorrectionOperation.IGNORE_EVENT
        for target in correction.target_source_or_event_ids
    }

    foreign_membership_ids = {
        event.event_id for event in membership_events
        if event.index_id != policy.index_id
    }
    for event_id in sorted(foreign_membership_ids):
        findings.append(make_finding(
            FindingType.FOREIGN_INDEX_INPUT,
            FindingSeverity.ERROR,
            (event_id,),
            "foreign-index membership event cannot mutate this compile",
        ))

    overlay_application = apply_ticker_overlays(observations, ticker_events, overlays)
    findings.extend(overlay_application.findings)
    detector_membership_events = tuple(
        event for event in membership_events
        if event.event_id not in ignored_event_ids
        and event.event_id not in foreign_membership_ids
        and event.source_id not in invalid_reconciled_source_ids
        and event.boundary_semantics is not SessionBoundary.AMBIGUOUS
        and (
            source := manifests_by_id.get(event.source_id)
        ) is not None
        and source.source_role in {
            SourceRole.PRECISE_MEMBERSHIP_EVENTS,
            SourceRole.OFFICIAL_CONFLICT_RESOLUTION,
        }
    )
    findings.extend(
        detect_episode_scoped_ticker_findings(
            overlay_application.observations,
            ticker_events,
            detector_membership_events,
        )
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
            resolved_seed = next(
                item for item in overlay_application.observations
                if item.observation_id == seed.observation_id
            )
            resolved_tickers = resolved_seed.tickers
            applied_overlay_ids = resolved_seed.applied_overlay_ids
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
        and getattr(event, "event_id") not in foreign_membership_ids
        and not (
            isinstance(event, IndexMembershipEventV1)
            and event.source_id in invalid_reconciled_source_ids
        )
        and policy.start_session < event.effective_session < policy.end_session
    ]
    operations.extend(
        correction for correction in valid_corrections
        if correction.operation in {CorrectionOperation.ADD, CorrectionOperation.REMOVE}
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
            closing = active.pop(ticker)
            if closing.opened != session:
                episodes.append(_close(closing, policy.index_id, session, (operation,), (operation_id,)))

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
