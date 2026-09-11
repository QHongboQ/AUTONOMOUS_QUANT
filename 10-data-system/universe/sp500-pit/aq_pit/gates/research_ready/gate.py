"""Domain-only gate for publishing a PIT universe into research."""

from __future__ import annotations

from dataclasses import dataclass

from ...domain import (
    AmbiguousTickerEpisodeError,
    ThinCompilation,
    lookup_episode,
)
from ...facts import AcceptedFacts


@dataclass(frozen=True, slots=True)
class ResearchReadyGateResult:
    research_ready: bool
    failures: tuple[str, ...]
    metrics: tuple[tuple[str, int], ...]

    def metric(self, name: str) -> int:
        return dict(self.metrics)[name]


def _overlap_count(compilation: ThinCompilation) -> int:
    count = len(compilation.episodes) - len({item.episode_id for item in compilation.episodes})
    by_ticker: dict[str, list[object]] = {}
    for episode in compilation.episodes:
        by_ticker.setdefault(episode.normalized_ticker, []).append(episode)
    for episodes in by_ticker.values():
        ordered = sorted(episodes, key=lambda item: (item.valid_from, item.valid_to))
        count += sum(right.valid_from < left.valid_to for left, right in zip(ordered, ordered[1:]))
    return count


def _unexplained_boundary_count(compilation: ThinCompilation) -> int:
    """Check successor/predecessor labels only inside their adjacent episodes."""
    count = 0
    ordered = tuple(sorted(compilation.resolved_observations, key=lambda item: item.effective_session))
    by_session = {item.effective_session: item for item in ordered}
    for identity in compilation.identity_events:
        before = [item for item in ordered if item.effective_session < identity.effective_session]
        predecessor_run = []
        for observation in reversed(before):
            if identity.old_ticker not in observation.tickers:
                break
            predecessor_run.append(observation)
        if predecessor_run:
            start = predecessor_run[-1].effective_session
            count += sum(
                identity.new_ticker in item.tickers and item.effective_session >= start
                for item in before
            )
        else:
            for observation in reversed(before):
                if identity.new_ticker not in observation.tickers:
                    break
                count += 1

        additions = sorted((
            item for item in compilation.membership_events
            if item.action == "ADD"
            and item.source_ticker == identity.old_ticker
            and item.effective_session >= identity.effective_session
        ), key=lambda item: (item.effective_session, item.event_id))
        removals = sorted((
            item for item in compilation.membership_events
            if item.action == "REMOVE"
            and item.source_ticker == identity.old_ticker
            and item.effective_session >= identity.effective_session
        ), key=lambda item: (item.effective_session, item.event_id))
        reuse = []
        for addition in additions:
            boundary = by_session.get(addition.effective_session)
            if boundary is None or not {identity.old_ticker, identity.new_ticker} <= set(boundary.tickers):
                continue
            end = next(
                (item.effective_session for item in removals
                 if item.effective_session > addition.effective_session),
                None,
            )
            reuse.append((addition.effective_session, end))
        for observation in ordered:
            if (observation.effective_session >= identity.effective_session
                    and identity.old_ticker in observation.tickers
                    and not any(start <= observation.effective_session
                                and (end is None or observation.effective_session < end)
                                for start, end in reuse)):
                count += 1
    return count


def assess_research_ready(
    compilation: ThinCompilation,
    facts: AcceptedFacts,
    historical_ledger: tuple[dict[str, object], ...],
    *,
    deterministic: bool,
) -> ResearchReadyGateResult:
    """Answer only whether the compiled universe is safe for P1 research."""
    failures: list[str] = []
    ledger_ids = {
        str(item.get("finding_id", "")).removeprefix("P1UNRES-")
        for item in historical_ledger
    }
    accepted_ids = {item.finding_id for item in facts.finding_resolutions}
    if ledger_ids != accepted_ids or len(historical_ledger) != facts.expected("canonical_facts"):
        failures.append("ACCEPTED_FACT_ACCOUNTING")

    unexplained = _unexplained_boundary_count(compilation)
    overlaps = _overlap_count(compilation)
    if unexplained:
        failures.append("UNEXPLAINED_TICKER_BOUNDARY")
    if overlaps:
        failures.append("EPISODE_OVERLAP_OR_DUPLICATE")
    if compilation.domain_errors:
        failures.append("MEMBERSHIP_OR_IDENTITY_DOMAIN_ERROR")
    if not deterministic:
        failures.append("NONDETERMINISTIC_COMPILE")

    by_ticker: dict[str, list[object]] = {}
    for episode in compilation.episodes:
        by_ticker.setdefault(episode.normalized_ticker, []).append(episode)
    ambiguous_failures = 0
    for ticker, episodes in by_ticker.items():
        if len(episodes) < 2:
            continue
        try:
            lookup_episode(compilation.episodes, ticker)
        except AmbiguousTickerEpisodeError:
            continue
        ambiguous_failures += 1
    if ambiguous_failures:
        failures.append("TICKER_REUSE_NOT_FAIL_CLOSED")

    actual = {
        "canonical_facts": len(facts.finding_resolutions),
        "identity_events": len(compilation.identity_events),
        "overlay_cases": len({item.case_id for item in compilation.overlays}),
        "overlay_rows": len(compilation.overlays),
        "reconciled_membership_events": len(compilation.membership_events),
        "instrument_episodes": len(compilation.episodes),
        "unexplained_ticker_boundaries": unexplained,
        "episode_overlap_or_duplicate": overlaps,
        "domain_errors": len(compilation.domain_errors),
        "ambiguous_lookup_failures": ambiguous_failures,
    }
    for name in (
        "canonical_facts",
        "identity_events",
        "overlay_cases",
        "overlay_rows",
        "reconciled_membership_events",
        "instrument_episodes",
    ):
        if actual[name] != facts.expected(name):
            failures.append(f"REFERENCE_COUNT:{name}")
    return ResearchReadyGateResult(
        research_ready=not failures,
        failures=tuple(sorted(failures)),
        metrics=tuple(sorted(actual.items())),
    )
