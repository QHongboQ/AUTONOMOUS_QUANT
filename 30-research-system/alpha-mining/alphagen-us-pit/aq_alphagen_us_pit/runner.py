"""Minimal composition of unchanged upstream AlphaGen runtime owners."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import numpy as np
import torch
from sb3_contrib import MaskablePPO

from alphagen.data.expression import Expression
from alphagen.models.linear_alpha_pool import MseAlphaPool
from alphagen.rl.env.wrapper import AlphaEnv
from alphagen.rl.policy import LSTMSharedNet
from alphagen.utils import reseed_everything

from .calculator import USPitAlphaCalculator
from .data_view import USPitDataView
from .feature_mask import VWAP_ACTION_INDEX, apply_feature_availability_mask


@dataclass(frozen=True)
class AlphaGenRunConfig:
    seed: int
    pool_capacity: int
    ic_lower_bound: float | None
    l1_alpha: float
    total_timesteps: int
    n_steps: int
    batch_size: int
    gamma: float
    entropy_coefficient: float
    lstm_layers: int
    lstm_model_dim: int
    lstm_dropout: float


@dataclass(frozen=True)
class AlphaGenRunResult:
    pool: MseAlphaPool
    calculator: USPitAlphaCalculator
    runtime_seconds: float
    expressions_generated: int
    expressions_evaluated: int
    action_space_size: int
    mask_diff_indices_at_reset: tuple[int, ...]


def run_alphagen(
    data: USPitDataView,
    target: Expression,
    config: AlphaGenRunConfig,
    *,
    device: torch.device,
    callback: Any = None,
) -> AlphaGenRunResult:
    """Compose upstream owners with explicit caller-supplied run parameters."""
    if config.total_timesteps <= 0 or config.n_steps <= 0:
        raise ValueError("AlphaGen run budgets must be positive")
    reseed_everything(config.seed)
    calculator = USPitAlphaCalculator(data, target)
    pool = MseAlphaPool(
        capacity=config.pool_capacity,
        calculator=calculator,
        ic_lower_bound=config.ic_lower_bound,
        l1_alpha=config.l1_alpha,
        device=device,
    )
    base_env = AlphaEnv(pool=pool, device=device, print_expr=False)
    masked_env = apply_feature_availability_mask(base_env)
    upstream_mask = np.asarray(base_env.action_masks(), dtype=bool)
    effective_mask = np.asarray(masked_env.action_masks(), dtype=bool)
    mask_diff = tuple(int(index) for index in np.flatnonzero(upstream_mask != effective_mask))
    if any(index != VWAP_ACTION_INDEX for index in mask_diff):
        raise RuntimeError("AQ feature mask changed a non-VWAP AlphaGen action")
    if effective_mask[VWAP_ACTION_INDEX]:
        raise RuntimeError("VWAP remains selectable after ActionMasker")

    model = MaskablePPO(
        "MlpPolicy",
        masked_env,
        policy_kwargs={
            "features_extractor_class": LSTMSharedNet,
            "features_extractor_kwargs": {
                "n_layers": config.lstm_layers,
                "d_model": config.lstm_model_dim,
                "dropout": config.lstm_dropout,
                "device": device,
            },
        },
        gamma=config.gamma,
        ent_coef=config.entropy_coefficient,
        n_steps=config.n_steps,
        batch_size=config.batch_size,
        device=device,
        seed=config.seed,
        verbose=0,
    )
    started = time.perf_counter()
    model.learn(total_timesteps=config.total_timesteps, callback=callback)
    runtime_seconds = time.perf_counter() - started
    return AlphaGenRunResult(
        pool=pool,
        calculator=calculator,
        runtime_seconds=runtime_seconds,
        expressions_generated=int(base_env.unwrapped.eval_cnt),
        expressions_evaluated=int(pool.eval_cnt),
        action_space_size=int(base_env.action_space.n),
        mask_diff_indices_at_reset=mask_diff,
    )
