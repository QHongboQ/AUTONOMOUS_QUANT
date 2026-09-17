"""Thin AUTONOMOUS_QUANT boundary for upstream AlphaGen on the US PIT panel."""

from .calculator import TargetAuthority, USPitAlphaCalculator, load_authoritative_target
from .data_view import (
    FEATURE_FIELDS,
    USPitDataView,
    load_us_pit_view,
    membership_covering_instruments,
)
from .feature_mask import (
    VWAP_ACTION_INDEX,
    apply_feature_availability_mask,
    unavailable_feature_action_mask,
)
from .runner import AlphaGenRunConfig, AlphaGenRunResult, run_alphagen

__all__ = [
    "AlphaGenRunConfig",
    "AlphaGenRunResult",
    "FEATURE_FIELDS",
    "TargetAuthority",
    "USPitAlphaCalculator",
    "USPitDataView",
    "VWAP_ACTION_INDEX",
    "apply_feature_availability_mask",
    "load_authoritative_target",
    "load_us_pit_view",
    "membership_covering_instruments",
    "run_alphagen",
    "unavailable_feature_action_mask",
]
