"""Thin, generic PIT membership/identity/episode composition for research."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..canonical import deterministic_id, sha256_hex
from .models import (
    IndexMembershipEventV1,
    InstrumentEpisodeV1,
    ResolvedObservationV1,
    SnapshotObservationV1,
    TickerIdentityEventV1,
    normalize_ticker,
)
from ..schema.pandera import (
    validate_identity_event_table,
    validate_instrument_episode_table,
    validate_membership_event_table,
    validate_snapshot_observation_table,
)

if TYPE_CHECKING:
    from ..facts import AcceptedFacts


_FACT_SOURCE_ID = "accepted-reconciliation-facts-v1"


@dataclass(frozen=True, slots=True)
class AppliedOverlayV1:
    overlay_id: str
    case_id: str
    observation_id: str
    identity_event_id: str
    operation: str


@dataclass(frozen=True, slots=True)
class ThinCompilation:
    resolved_observations: tuple[ResolvedObservationV1, ...]
    identity_events: tuple[TickerIdentityEventV1, ...]
    overlays: tuple[AppliedOverlayV1, ...]
    membership_events: tuple[IndexMembershipEventV1, ...]
    episodes: tuple[InstrumentEpisodeV1, ...]
    domain_errors: tuple[str, ...]
    facts_hash: str
    output_hash: str


@dataclass(slots=True)
class _ActiveEpisode:
    ticker: str
    opened: str
    membership_source_ids: set[str]
    ticker_source_ids: set[str]
    source_event_ids: set[str]
    provenance: list[object]


def _identity_events(facts: AcceptedFacts) -> tuple[TickerIdentityEventV1, ...]:
    events = []
    for fact in facts.identity_events:
        logical = {
            "facts_hash": facts.facts_hash,
            "old_ticker": fact.old_ticker,
            "new_ticker": fact.new_ticker,
            "effective_session": fact.effective_session,
            "evidence_id": fact.evidence_id,
        }
        evidence_hash = sha256_hex({"facts_hash": facts.facts_hash, "evidence_id": fact.evidence_id})
        events.append(TickerIdentityEventV1(
            event_id=deterministic_id("P1TID-", logical),
            old_ticker=fact.old_ticker,
            new_ticker=fact.new_ticker,
            announcement_date=fact.announcement_date,
            effective_date=fact.effective_session,
            effective_session=fact.effective_session,
            boundary_semantics="EFFECTIVE_SESSION",
            source_id=_FACT_SOURCE_ID,
            evidence_hash=evidence_hash,
            identity_anchor=deterministic_id("P1ANCHOR-", logical),
            ambiguity_state="CLEAR",
        ))
    result = tuple(sorted(events, key=lambda item: (item.effective_session, item.event_id)))
    validate_identity_event_table(result)
    return result


def _resolve_observations(
    observations: tuple[SnapshotObservationV1, ...],
    identities: tuple[TickerIdentityEventV1, ...],
    facts: AcceptedFacts,
) -> tuple[tuple[ResolvedObservationV1, ...], tuple[AppliedOverlayV1, ...]]:
    event_by_key = {
        (item.old_ticker, item.new_ticker, item.effective_session): item
        for item in identities
    }
    applied: list[AppliedOverlayV1] = []
    resolved: list[ResolvedObservationV1] = []
    cases_by_key = {
        (item.old_ticker, item.new_ticker, item.effective_session): item
        for item in facts.overlay_cases
    }
    applied_by_observation: dict[str, list[str]] = {item.observation_id: [] for item in observations}
    adjusted = {item.observation_id: list(item.tickers) for item in observations}
    for key, case in cases_by_key.items():
        event = event_by_key[key]
        for observation in sorted(observations, key=lambda item: item.observation_id):
            if observation.effective_session >= case.effective_session:
                continue
            if case.start_session is not None and observation.effective_session < case.start_session:
                continue
            if case.new_ticker not in observation.tickers:
                continue
            operation = (
                "DROP_DUPLICATE_SUCCESSOR_BEFORE_BOUNDARY"
                if case.old_ticker in observation.tickers
                else "MAP_SUCCESSOR_TO_PREDECESSOR"
            )
            logical = {
                "case_id": case.case_id,
                "observation_id": observation.observation_id,
                "identity_event_id": event.event_id,
                "operation": operation,
            }
            overlay_id = deterministic_id("P1OVR-", logical)
            tickers = adjusted[observation.observation_id]
            if case.new_ticker not in tickers:
                raise ValueError("accepted declarative overlay is not applicable")
            if operation == "MAP_SUCCESSOR_TO_PREDECESSOR":
                if case.old_ticker in tickers:
                    raise ValueError("accepted declarative overlay conflicts")
                tickers[tickers.index(case.new_ticker)] = case.old_ticker
            else:
                if case.old_ticker not in tickers:
                    raise ValueError("duplicate-successor overlay lacks predecessor")
                tickers.remove(case.new_ticker)
            applied_by_observation[observation.observation_id].append(overlay_id)
            applied.append(AppliedOverlayV1(
                overlay_id=overlay_id,
                case_id=case.case_id,
                observation_id=observation.observation_id,
                identity_event_id=event.event_id,
                operation=operation,
            ))
    for observation in observations:
        resolved.append(ResolvedObservationV1(
            observation_id=observation.observation_id,
            index_id=observation.index_id,
            effective_session=observation.effective_session,
            tickers=tuple(sorted(adjusted[observation.observation_id])),
            source_id=observation.source_id,
            evidence_hash=observation.evidence_hash,
            applied_overlay_ids=tuple(sorted(applied_by_observation[observation.observation_id])),
        ))
    return tuple(resolved), tuple(sorted(applied, key=lambda item: item.overlay_id))


def _membership_events(
    observations: tuple[ResolvedObservationV1, ...],
    identities: tuple[TickerIdentityEventV1, ...],
    facts_hash: str,
) -> tuple[IndexMembershipEventV1, ...]:
    ordered = tuple(sorted(observations, key=lambda item: (item.effective_session, item.observation_id)))
    events: list[IndexMembershipEventV1] = []
    for prior, current in zip(ordered, ordered[1:]):
        if prior.index_id != current.index_id:
            raise ValueError("cannot derive membership across different indexes")
        transformed = set(prior.tickers)
        between = tuple(
            item for item in identities
            if prior.effective_session < item.effective_session <= current.effective_session
        )
        for identity in between:
            old = normalize_ticker(identity.old_ticker)
            new = normalize_ticker(identity.new_ticker)
            if old not in transformed:
                continue
            if new in transformed:
                raise ValueError("identity transition overlaps an active successor")
            transformed.remove(old)
            transformed.add(new)
        current_set = set(current.tickers)
        transitions = (
            *(("REMOVE", item) for item in sorted(transformed - current_set)),
            *(("ADD", item) for item in sorted(current_set - transformed)),
        )
        evidence_hash = sha256_hex({
            "facts_hash": facts_hash,
            "prior": prior,
            "current": current,
            "identities": between,
            "removed": tuple(sorted(transformed - current_set)),
            "added": tuple(sorted(current_set - transformed)),
        })
        for action, ticker in transitions:
            logical = {
                "action": action,
                "effective_session": current.effective_session,
                "index_id": current.index_id,
                "ticker": ticker,
                "facts_hash": facts_hash,
            }
            events.append(IndexMembershipEventV1(
                event_id=deterministic_id("P1MEMR-", logical),
                index_id=current.index_id,
                action=action,
                source_ticker=ticker,
                announcement_date=None,
                effective_date=current.effective_session,
                effective_session=current.effective_session,
                boundary_semantics="SOURCE_DEFINED",
                source_id=_FACT_SOURCE_ID,
                evidence_hash=evidence_hash,
                reason="thin identity-aware resolved-snapshot difference",
            ))
    result = tuple(events)
    validate_membership_event_table(result)
    return result


def _close(active: _ActiveEpisode, index_id: str, boundary: str, extra: object | None = None) -> InstrumentEpisodeV1:
    provenance = (*active.provenance, *((extra,) if extra is not None else ()))
    source_event_ids = set(active.source_event_ids)
    closing_event_id = getattr(extra, "event_id", None)
    if closing_event_id:
        source_event_ids.add(closing_event_id)
    return InstrumentEpisodeV1.create(
        index_id=index_id,
        ticker=active.ticker,
        valid_from=active.opened,
        valid_to=boundary,
        membership_source_ids=active.membership_source_ids,
        ticker_source_ids=active.ticker_source_ids,
        source_event_ids=source_event_ids,
        provenance_inputs=provenance,
    )


def _episodes(
    observations: tuple[ResolvedObservationV1, ...],
    identities: tuple[TickerIdentityEventV1, ...],
    membership_events: tuple[IndexMembershipEventV1, ...],
    end_session: str,
) -> tuple[tuple[InstrumentEpisodeV1, ...], tuple[str, ...]]:
    if not observations:
        raise ValueError("thin compile requires observations")
    seed = min(observations, key=lambda item: (item.effective_session, item.observation_id))
    active = {
        ticker: _ActiveEpisode(
            ticker=ticker,
            opened=seed.effective_session,
            membership_source_ids={seed.source_id},
            ticker_source_ids={seed.source_id},
            source_event_ids={seed.observation_id},
            provenance=[seed],
        )
        for ticker in seed.tickers
    }
    episodes: list[InstrumentEpisodeV1] = []
    errors: list[str] = []
    operations = sorted(
        (*identities, *membership_events),
        key=lambda item: (
            item.effective_session,
            0 if isinstance(item, TickerIdentityEventV1) else 1 if item.action == "REMOVE" else 2,
            item.event_id,
        ),
    )
    for operation in operations:
        session = operation.effective_session
        if isinstance(operation, TickerIdentityEventV1):
            old = normalize_ticker(operation.old_ticker)
            new = normalize_ticker(operation.new_ticker)
            if old not in active:
                continue
            if new in active:
                errors.append(f"IDENTITY_OVERLAP:{operation.event_id}")
                continue
            prior = active.pop(old)
            if prior.opened != session:
                episodes.append(_close(prior, seed.index_id, session, operation))
            active[new] = _ActiveEpisode(
                ticker=new,
                opened=session,
                membership_source_ids=set(prior.membership_source_ids),
                ticker_source_ids={*prior.ticker_source_ids, operation.source_id},
                source_event_ids={*prior.source_event_ids, operation.event_id},
                provenance=[*prior.provenance, operation],
            )
            continue
        ticker = normalize_ticker(operation.source_ticker)
        if operation.action == "ADD":
            if ticker in active:
                errors.append(f"ADD_PRESENT:{operation.event_id}")
                continue
            active[ticker] = _ActiveEpisode(
                ticker=ticker,
                opened=session,
                membership_source_ids={operation.source_id},
                ticker_source_ids={operation.source_id},
                source_event_ids={operation.event_id},
                provenance=[operation],
            )
        else:
            if ticker not in active:
                errors.append(f"REMOVE_ABSENT:{operation.event_id}")
                continue
            prior = active.pop(ticker)
            if prior.opened != session:
                episodes.append(_close(prior, seed.index_id, session, operation))
    for ticker in sorted(active):
        episodes.append(_close(active[ticker], seed.index_id, end_session))
    result = tuple(sorted(
        episodes,
        key=lambda item: (item.valid_from, item.normalized_ticker, item.valid_to, item.episode_id),
    ))
    validate_instrument_episode_table(result)
    return result, tuple(sorted(errors))


def compile_thin_universe(
    observations: tuple[SnapshotObservationV1, ...],
    facts: AcceptedFacts,
    *,
    end_session: str = "2025-01-01",
) -> ThinCompilation:
    """Compose the single active P1 research-universe domain path."""
    validate_snapshot_observation_table(observations)
    identities = _identity_events(facts)
    resolved, overlays = _resolve_observations(observations, identities, facts)
    membership = _membership_events(resolved, identities, facts.facts_hash)
    episodes, errors = _episodes(resolved, identities, membership, end_session)
    logical = {
        "facts_hash": facts.facts_hash,
        "resolved_observations": resolved,
        "identity_events": identities,
        "overlays": overlays,
        "membership_events": membership,
        "episodes": episodes,
        "domain_errors": errors,
    }
    return ThinCompilation(
        resolved_observations=resolved,
        identity_events=identities,
        overlays=overlays,
        membership_events=membership,
        episodes=episodes,
        domain_errors=errors,
        facts_hash=facts.facts_hash,
        output_hash=sha256_hex(logical),
    )
