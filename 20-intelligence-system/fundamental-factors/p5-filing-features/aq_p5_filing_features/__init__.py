"""Thin P5 filing-feature contract and pure native-object projection."""

from .contract import (
    EDGARTOOLS_RUNTIME_IDENTITY,
    FEATURE_IDS,
    FilingFeatureObservationV1,
    SCHEMA_VERSION,
    evidence_id_for,
)
from .materialize import materialize_selected_filing_features

__all__ = [
    "EDGARTOOLS_RUNTIME_IDENTITY",
    "FEATURE_IDS",
    "FilingFeatureObservationV1",
    "SCHEMA_VERSION",
    "evidence_id_for",
    "materialize_selected_filing_features",
]
