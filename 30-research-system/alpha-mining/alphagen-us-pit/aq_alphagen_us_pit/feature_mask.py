"""Project availability mask layered onto AlphaGen's upstream action mask."""

from __future__ import annotations

from typing import Any

import numpy as np
from sb3_contrib.common.wrappers import ActionMasker

from alphagen.rl.env.wrapper import SIZE_OP
from alphagen_qlib.stock_data import FeatureType


VWAP_ACTION_INDEX = SIZE_OP + int(FeatureType.VWAP)


def unavailable_feature_action_mask(env: Any) -> np.ndarray:
    """Preserve AlphaGen semantics and forbid only the unavailable VWAP channel."""
    upstream_mask = np.asarray(env.action_masks(), dtype=bool).copy()
    if upstream_mask.shape != (env.action_space.n,):
        raise ValueError("AlphaGen action mask length does not match its action space")
    if not 0 <= VWAP_ACTION_INDEX < len(upstream_mask):
        raise ValueError("Derived VWAP action index is outside the AlphaGen action space")
    upstream_mask[VWAP_ACTION_INDEX] = False
    return upstream_mask


def apply_feature_availability_mask(env: Any) -> ActionMasker:
    return ActionMasker(env, unavailable_feature_action_mask)
