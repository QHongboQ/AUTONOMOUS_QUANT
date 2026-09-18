"""Thin AUTONOMOUS_QUANT boundary for upstream AlphaGen on the US PIT panel."""

from .calculator import TargetAuthority, USPitAlphaCalculator, load_authoritative_target
from .data_view import (
    FEATURE_FIELDS,
    USPitDataView,
    load_us_pit_view,
    membership_covering_instruments,
    membership_overlapping_instruments,
)
from .feature_mask import (
    VWAP_ACTION_INDEX,
    apply_feature_availability_mask,
    unavailable_feature_action_mask,
)
from .runner import AlphaGenRunConfig, AlphaGenRunResult, run_alphagen
from .research_config import (
    FAST_CONFIG_ID,
    L1_REFERENCE_CONFIG_ID,
    assert_research_window,
    make_lstsq_fast_config,
    resolve_effective_partition,
)

__all__ = [
    "AlphaGenRunConfig",
    "AlphaGenRunResult",
    "FAST_CONFIG_ID",
    "FEATURE_FIELDS",
    "L1_REFERENCE_CONFIG_ID",
    "TargetAuthority",
    "USPitAlphaCalculator",
    "USPitDataView",
    "VWAP_ACTION_INDEX",
    "apply_feature_availability_mask",
    "assert_research_window",
    "load_authoritative_target",
    "load_us_pit_view",
    "membership_covering_instruments",
    "membership_overlapping_instruments",
    "make_lstsq_fast_config",
    "resolve_effective_partition",
    "run_alphagen",
    "unavailable_feature_action_mask",
]
