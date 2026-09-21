"""Thin P5 filing-feature contract and pure native-object projection."""

from .contract import (
    EDGARTOOLS_RUNTIME_IDENTITY,
    FEATURE_IDS,
    FilingFeatureObservationV1,
    SCHEMA_VERSION,
    evidence_id_for,
)
from .materialize import (
    discover_native_filing_observations,
    materialize_selected_filing_features,
    project_historical_filing_features,
    seal_historical_filing_features,
)

__all__ = [
    "EDGARTOOLS_RUNTIME_IDENTITY",
    "FEATURE_IDS",
    "FilingFeatureObservationV1",
    "SCHEMA_VERSION",
    "evidence_id_for",
    "discover_native_filing_observations",
    "materialize_selected_filing_features",
    "project_historical_filing_features",
    "seal_historical_filing_features",
]
