"""Primitive-only rows for the future DatasetSnapshot boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..domain import InstrumentEpisodeV1


@dataclass(frozen=True, slots=True)
class ResearchUniverseRowV1:
    episode_id: str
    ticker: str
    membership_from: str
    membership_to: str


def research_universe_rows(
    episodes: Iterable[InstrumentEpisodeV1],
) -> tuple[ResearchUniverseRowV1, ...]:
    """Serialize domain episodes without leaking internal or upstream objects."""
    return tuple(
        ResearchUniverseRowV1(
            episode_id=item.episode_id,
            ticker=item.normalized_ticker,
            membership_from=item.membership_from,
            membership_to=item.membership_to,
        )
        for item in sorted(
            episodes,
            key=lambda row: (row.membership_from, row.normalized_ticker, row.membership_to, row.episode_id),
        )
    )
