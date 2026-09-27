"""Strict research-only boundary for Qlib's native ``AverageEnsemble``."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype
from qlib.model.ens.ensemble import AverageEnsemble

QLIB_SOURCE_SHA = "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"
UPSTREAM_CLASS = "qlib.model.ens.ensemble.AverageEnsemble"


def validate_complete_predictions(
    predictions: Mapping[str, pd.DataFrame], *, require_nonconstant: bool = True
) -> tuple[dict[str, pd.DataFrame], pd.MultiIndex]:
    """Validate complete, aligned prediction panels without combining them."""
    if not isinstance(predictions, Mapping) or len(predictions) < 2:
        raise ValueError("at least two named prediction components are required")
    if any(not isinstance(name, str) or not name.strip() for name in predictions):
        raise ValueError("component names must be nonempty strings")

    reference_index: pd.MultiIndex | None = None
    validated: dict[str, pd.DataFrame] = {}
    for name, frame in predictions.items():
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"{name}: prediction input must be a DataFrame")
        if list(frame.columns) != ["score"]:
            raise ValueError(f"{name}: exactly one column named 'score' is required")
        if not isinstance(frame.index, pd.MultiIndex) or frame.index.nlevels != 2:
            raise ValueError(f"{name}: a two-level MultiIndex is required")
        if list(frame.index.names) != ["datetime", "instrument"]:
            raise ValueError(f"{name}: index names must be datetime/instrument")
        if not is_datetime64_any_dtype(frame.index.get_level_values("datetime")):
            raise ValueError(f"{name}: datetime index level must be datetime64")
        instruments = frame.index.get_level_values("instrument")
        if any(not isinstance(value, str) or not value for value in instruments):
            raise ValueError(f"{name}: instrument keys must be nonempty strings")
        if frame.index.has_duplicates:
            raise ValueError(f"{name}: duplicate instrument-session keys")
        if not frame.index.is_monotonic_increasing:
            raise ValueError(f"{name}: index must be sorted")
        if reference_index is None:
            reference_index = frame.index
        elif not frame.index.equals(reference_index):
            raise ValueError(f"{name}: row identities do not match")
        if not is_numeric_dtype(frame["score"]):
            raise ValueError(f"{name}: score must be numeric")
        values = frame["score"].to_numpy(dtype=float, copy=False)
        if not np.isfinite(values).all():
            raise ValueError(f"{name}: score contains missing or non-finite values")
        grouped = frame["score"].groupby(level="datetime", sort=False)
        if (grouped.size() < 2).any():
            raise ValueError(f"{name}: each session needs at least two instruments")
        if require_nonconstant and (grouped.nunique(dropna=False) < 2).any():
            raise ValueError(f"{name}: constant cross-sectional component")
        validated[name] = frame

    if reference_index is None:
        raise RuntimeError("prediction validation produced no reference index")
    return validated, reference_index


def combine_complete_predictions(
    predictions: Mapping[str, pd.DataFrame],
) -> pd.DataFrame:
    """Validate complete score panels, then delegate combination to Qlib.

    The POC accepts at least two explicitly named, finite, nonconstant score
    frames with the same sorted ``(datetime, instrument)`` index.  It neither
    repairs nor reweights incomplete inputs.
    """

    validated, reference_index = validate_complete_predictions(predictions)

    result = AverageEnsemble()(validated)
    if not isinstance(result, pd.Series):
        raise RuntimeError("pinned Qlib AverageEnsemble returned an unsupported type")
    if not result.index.equals(reference_index):
        raise RuntimeError("pinned Qlib AverageEnsemble changed row identities")
    if not np.isfinite(result.to_numpy(dtype=float, copy=False)).all():
        raise RuntimeError("pinned Qlib AverageEnsemble produced non-finite output")
    return result.rename("score").to_frame()
