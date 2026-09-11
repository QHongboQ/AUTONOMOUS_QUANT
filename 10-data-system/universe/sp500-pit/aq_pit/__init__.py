"""Public contracts for the bounded S&P 500 PIT universe foundation."""

from .compiler import compile_universe
from .contracts import *  # noqa: F403 - contracts are the intended public surface
from .contracts import __all__ as _contract_exports
from .overlays import detect_future_ticker_backfill, resolve_observation
from .validation import (
    AmbiguousTickerEpisodeError,
    PublicationBlockedError,
    lookup_episode,
    sources_are_independent,
    validate_publishable,
)

__all__ = [*_contract_exports,
    "compile_universe",
    "detect_future_ticker_backfill",
    "resolve_observation",
    "lookup_episode",
    "sources_are_independent",
    "validate_publishable",
    "AmbiguousTickerEpisodeError",
    "PublicationBlockedError",
]
