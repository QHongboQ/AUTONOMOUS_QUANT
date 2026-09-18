"""Bounded US PIT research policy built from upstream AlphaGen configuration."""

from __future__ import annotations

import pandas as pd

from .runner import AlphaGenRunConfig


FAST_CONFIG_ID = "ALPHAGEN_MSE_LSTSQ_FAST_V1"
L1_REFERENCE_CONFIG_ID = "ALPHAGEN_MSE_L1_REFERENCE_V1"
HISTORICAL_TEST_AUTHORITY = (
    pd.Timestamp("2022-01-03"),
    pd.Timestamp("2024-12-31"),
)
SEALED_OOS_START = pd.Timestamp("2026-09-14")


def make_lstsq_fast_config(seed: int, total_timesteps: int) -> AlphaGenRunConfig:
    """Return the fixed upstream-supported least-squares research configuration."""
    return AlphaGenRunConfig(
        seed=seed,
        pool_capacity=20,
        ic_lower_bound=None,
        l1_alpha=0.0,
        total_timesteps=total_timesteps,
        n_steps=2048,
        batch_size=128,
        gamma=1.0,
        entropy_coefficient=0.01,
        lstm_layers=2,
        lstm_model_dim=128,
        lstm_dropout=0.1,
    )


def resolve_effective_partition(
    calendar: pd.DatetimeIndex,
    authority_start: pd.Timestamp,
    authority_end: pd.Timestamp,
    lookahead_sessions: int,
    max_backtrack_days: int = 0,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Resolve sessions whose complete label and required history stay in authority."""
    start_index = max(
        int(calendar.searchsorted(authority_start)),
        max_backtrack_days,
    )
    end_index = int(calendar.searchsorted(authority_end, side="right") - 1)
    if start_index >= len(calendar) or end_index - lookahead_sessions < start_index:
        raise ValueError("Partition cannot support the frozen target horizon")
    effective_start = pd.Timestamp(calendar[start_index])
    effective_end = pd.Timestamp(calendar[end_index - lookahead_sessions])
    if effective_end >= HISTORICAL_TEST_AUTHORITY[0]:
        raise ValueError("Research partition reaches historical TEST")
    return effective_start, effective_end


def assert_research_window(start: pd.Timestamp, end: pd.Timestamp) -> None:
    """Fail closed on historical TEST or sealed-OOS access."""
    if start > end:
        raise ValueError("Research window is inverted")
    test_start, test_end = HISTORICAL_TEST_AUTHORITY
    if start <= test_end and end >= test_start:
        raise ValueError("Historical TEST access is prohibited")
    if end >= SEALED_OOS_START:
        raise ValueError("Sealed OOS access is prohibited")
