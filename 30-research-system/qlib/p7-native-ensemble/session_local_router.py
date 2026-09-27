"""Session-local routing for the frozen P7 nonconstant-component policy."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd
from average_ensemble_boundary import (
    combine_complete_predictions,
    validate_complete_predictions,
)

POLICY = "SESSION_LOCAL_NONCONSTANT_COMPONENT_EQUAL_WEIGHT"


def combine_session_local_nonconstant(
    predictions: Mapping[str, pd.DataFrame],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Route each session's nonconstant components to the strict Qlib boundary."""

    validated, reference_index = validate_complete_predictions(
        predictions, require_nonconstant=False
    )
    combined_sessions: list[pd.DataFrame] = []
    qualification: list[dict[str, object]] = []
    datetimes = reference_index.get_level_values("datetime").unique()
    for session in datetimes:
        active: dict[str, pd.DataFrame] = {}
        inactive: list[str] = []
        for name, frame in validated.items():
            session_frame = frame.xs(session, level="datetime", drop_level=False)
            if session_frame["score"].nunique(dropna=False) < 2:
                inactive.append(name)
            else:
                active[name] = session_frame
        if len(active) < 2:
            raise ValueError(f"{session}: fewer than two active components")
        combined = combine_complete_predictions(active)
        combined_sessions.append(combined)
        qualification.append(
            {
                "datetime": session,
                "active_component_count": len(active),
                "inactive_components": tuple(inactive),
                "combined_has_ranking_information": (
                    combined["score"].nunique(dropna=False) >= 2
                ),
            }
        )

    result = pd.concat(combined_sessions)
    if not result.index.equals(reference_index):
        raise RuntimeError("session routing changed eligible row identity or order")
    report = pd.DataFrame.from_records(qualification).set_index("datetime")
    return result, report
