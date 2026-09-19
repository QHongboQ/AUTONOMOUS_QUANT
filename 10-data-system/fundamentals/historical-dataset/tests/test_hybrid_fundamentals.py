from __future__ import annotations

import json
import tempfile
from pathlib import Path

import exchange_calendars as xcals
import pandas as pd
import pyarrow.parquet as pq
import pytest
from aq_hybrid_fundamentals import (
    canonical_sha256,
    effective_session,
    eligible_episode_sessions,
    project_events_asof,
    write_exact_event_parquet,
)

EPISODE = {"episode_id": "P1EP-" + "a" * 64, "ticker": "OLD", "valid_from": "2020-01-01", "valid_to": "2020-02-01"}
BINDING = {"episode_id": EPISODE["episode_id"], "cik": "0000000001", "valid_from": "2020-01-02", "valid_to": "2020-01-31", "binding_classification": "PASS_EXACT", "binding_id": "sha256:" + "b" * 64}
MEMBERSHIP = [{"episode_id": EPISODE["episode_id"], "membership_from": "2020-01-03", "membership_to": "2020-01-30"}]


def test_effective_session_boundaries() -> None:
    calendar = xcals.get_calendar("XNYS")
    cases = {
        "2020-01-02T13:00:00Z": "2020-01-02",  # before open
        "2020-01-02T14:30:00Z": "2020-01-03",  # exactly at open
        "2020-01-02T16:00:00Z": "2020-01-03",  # during session
        "2020-01-02T22:00:00Z": "2020-01-03",  # after close
        "2020-01-04T12:00:00Z": "2020-01-06",  # weekend
        "2020-01-20T12:00:00Z": "2020-01-21",  # holiday
    }
    for value, expected in cases.items():
        assert effective_session(value, calendar) == pd.Timestamp(expected)


def test_episode_binding_membership_containment_and_negative_identity() -> None:
    sessions = pd.date_range("2020-01-01", "2020-02-01", freq="D")
    frame = eligible_episode_sessions(sessions, episode=EPISODE, binding=BINDING, membership_intervals=MEMBERSHIP)
    assert frame["session"].min() == pd.Timestamp("2020-01-03")
    assert frame["session"].max() == pd.Timestamp("2020-01-29")
    rejected = {**BINDING, "binding_classification": "AMBIGUOUS_FAIL_CLOSED"}
    with pytest.raises(ValueError, match="not admissible"):
        eligible_episode_sessions(sessions, episode=EPISODE, binding=rejected, membership_intervals=MEMBERSHIP)


def _grid(cik: str = "0000000001") -> pd.DataFrame:
    return pd.DataFrame({
        "session": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
        "episode_id": [EPISODE["episode_id"]] * 3,
        "instrument": ["OLD"] * 3,
        "cik": [cik] * 3,
        "binding_id": [BINDING["binding_id"]] * 3,
    })


def test_asof_no_lookahead_amendment_precedence_and_missing_stays_missing() -> None:
    events = pd.DataFrame([
        {"cik": "0000000001", "standard_metric": "Revenue", "period_class": "FY", "effective_session": "2020-01-03", "evidence_id": "original", "accession": "0000000001-20-000001", "canonical_value": "10"},
        {"cik": "0000000001", "standard_metric": "Revenue", "period_class": "FY", "effective_session": "2020-01-06", "evidence_id": "amendment", "accession": "0000000001-20-000002", "canonical_value": "11"},
    ])
    projected = project_events_asof(_grid(), events)
    assert pd.isna(projected.loc[0, "evidence_id"])
    assert projected.loc[1, "evidence_id"] == "original"
    assert projected.loc[2, "evidence_id"] == "amendment"


def test_cross_cik_isolation() -> None:
    events = pd.DataFrame([{"cik": "0000000002", "standard_metric": "Revenue", "period_class": "FY", "effective_session": "2020-01-02", "evidence_id": "wrong", "accession": "0000000002-20-000001", "canonical_value": "99"}])
    projected = project_events_asof(_grid(), events)
    assert projected.empty


def test_parquet_exact_value_and_partition_policy() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "events"
        paths = write_exact_event_parquet([{
            "cik": "0000000001", "standard_metric": "Revenue", "canonical_value": "9007199254740993",
            "first_available_at": "2020-01-02T21:00:00Z", "evidence_id": "e", "accession": "0000000001-20-000001",
        }], root)
        assert paths[0].parent.name == "first_available_year=2020"
        assert pq.read_table(paths[0]).to_pylist()[0]["canonical_value"] == "9007199254740993"


def test_manifest_identity_is_deterministic() -> None:
    left = {"b": 2, "a": [1, {"z": True}]}
    right = json.loads(json.dumps(left, sort_keys=False))
    assert canonical_sha256(left) == canonical_sha256(right)


def test_qlib_shape_keeps_provenance_out_of_features() -> None:
    projected = pd.DataFrame({
        "session": pd.to_datetime(["2020-01-02"]), "instrument": ["OLD"],
        "standard_metric": ["Revenue"], "canonical_value": ["10"],
        "episode_id": [EPISODE["episode_id"]], "cik": ["0000000001"],
        "evidence_id": ["e"], "accession": ["a"],
    })
    features = projected.pivot(index=["session", "instrument"], columns="standard_metric", values="canonical_value")
    assert list(features.columns) == ["Revenue"]
    assert "evidence_id" not in features.columns
