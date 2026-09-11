"""Single active composition path for the P1 research-ready PIT universe."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .adapters import load_research_inputs
from .domain import ThinCompilation, compile_thin_universe
from .export import ResearchUniverseRowV1, research_universe_rows
from .facts import AcceptedFacts, load_accepted_facts
from .gates.research_ready import ResearchReadyGateResult, assess_research_ready


@dataclass(frozen=True, slots=True)
class ResearchReadyUniverse:
    rows: tuple[ResearchUniverseRowV1, ...]
    compilation: ThinCompilation
    gate: ResearchReadyGateResult
    facts: AcceptedFacts


def build_research_ready_universe(data_root: Path) -> ResearchReadyUniverse:
    """Build twice, verify determinism, then apply the bounded P1 gate."""
    inputs = load_research_inputs(data_root)
    facts = load_accepted_facts()
    first = compile_thin_universe(inputs.observations, facts)
    second = compile_thin_universe(inputs.observations, facts)
    deterministic = first == second and first.output_hash == second.output_hash
    gate = assess_research_ready(
        first,
        facts,
        inputs.historical_ledger,
        deterministic=deterministic,
    )
    if not gate.research_ready:
        raise RuntimeError("PIT_UNIVERSE_RESEARCH_READY blocked: " + ",".join(gate.failures))
    return ResearchReadyUniverse(
        rows=research_universe_rows(first.episodes),
        compilation=first,
        gate=gate,
        facts=facts,
    )
