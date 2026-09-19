from __future__ import annotations

import json
import tempfile
from pathlib import Path

import exchange_calendars as xcals
import pandas as pd
import pyarrow.parquet as pq
import pytest
from aq_hybrid_fundamentals import (
    FROZEN_STANDARD_CONCEPTS,
    PERIOD_CLASSES,
    admit_period_class,
    canonical_sha256,
    consolidated_projection_events,
    effective_session,
    eligible_episode_sessions,
    feature_identity,
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


def _event(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "cik": "0000000001",
        "standard_concept": "Revenue",
        "period_class": "DURATION_QUARTERLY",
        "effective_session": "2020-01-03",
        "evidence_id": "original",
        "accession": "0000000001-20-000001",
        "canonical_value": "10",
        "report_period_start": "2019-10-01",
        "report_period_end": "2019-12-31",
        "dimensions": {},
    }
    row.update(overrides)
    return row


def test_upstream_machine_concept_identity_is_frozen_not_display_label() -> None:
    assert len(FROZEN_STANDARD_CONCEPTS) == 11
    assert {"ShortTermDebt", "LongTermDebt"} <= set(FROZEN_STANDARD_CONCEPTS)
    assert "Short-Term Debt" not in FROZEN_STANDARD_CONCEPTS
    assert feature_identity("ShortTermDebt", "INSTANT") == "ShortTermDebt__INSTANT"
    with pytest.raises(ValueError, match="unfrozen"):
        feature_identity("Short-Term Debt", "INSTANT")


def test_upstream_period_result_admission_covers_frozen_classes() -> None:
    assert admit_period_class("instant") == "INSTANT"
    assert admit_period_class("duration", "Quarterly") == "DURATION_QUARTERLY"
    assert admit_period_class("duration", "Semi-Annual") == "DURATION_SEMI_ANNUAL"
    assert admit_period_class("duration", "Nine Months") == "DURATION_NINE_MONTHS"
    assert admit_period_class("duration", "Annual") == "DURATION_ANNUAL"
    assert admit_period_class("duration", "Period") == "DURATION_OTHER"
    assert admit_period_class("duration", "future upstream class") == "DURATION_OTHER"
    assert len(PERIOD_CLASSES) == 6
    with pytest.raises(ValueError, match="period type"):
        admit_period_class("forever")


def test_asof_no_lookahead_amendment_precedence_and_missing_stays_missing() -> None:
    events = pd.DataFrame([
        _event(),
        _event(effective_session="2020-01-06", evidence_id="amendment", accession="0000000001-20-000002", canonical_value="11"),
    ])
    projected = project_events_asof(_grid(), events)
    assert pd.isna(projected.loc[0, "evidence_id"])
    assert projected.loc[1, "evidence_id"] == "original"
    assert projected.loc[2, "evidence_id"] == "amendment"


def test_cross_cik_isolation() -> None:
    events = pd.DataFrame([_event(cik="0000000002", effective_session="2020-01-02", evidence_id="wrong", accession="0000000002-20-000001", canonical_value="99")])
    projected = project_events_asof(_grid(), events)
    assert projected.empty


def test_period_streams_and_display_labels_are_orthogonal() -> None:
    events = pd.DataFrame([
        _event(metric_display_name="Revenue (punctuation one)"),
        _event(period_class="DURATION_ANNUAL", effective_session="2020-01-06", evidence_id="annual", accession="0000000001-20-000002", canonical_value="100", report_period_start="2019-01-01", metric_display_name="REVENUE!!!"),
        _event(period_class="DURATION_SEMI_ANNUAL", evidence_id="semi", canonical_value="40"),
        _event(period_class="DURATION_NINE_MONTHS", evidence_id="nine", canonical_value="70"),
        _event(standard_concept="Assets", period_class="INSTANT", evidence_id="instant", canonical_value="200", report_period_start=None),
    ])
    projected = project_events_asof(_grid(), events)
    streams = set(zip(projected["standard_concept"], projected["period_class"], strict=True))
    assert ("Revenue", "DURATION_QUARTERLY") in streams
    assert ("Revenue", "DURATION_ANNUAL") in streams
    assert ("Revenue", "DURATION_SEMI_ANNUAL") in streams
    assert ("Revenue", "DURATION_NINE_MONTHS") in streams
    assert ("Assets", "INSTANT") in streams
    quarterly = projected[projected["period_class"] == "DURATION_QUARTERLY"]
    annual = projected[projected["period_class"] == "DURATION_ANNUAL"]
    assert set(quarterly["evidence_id"].dropna()) == {"original"}
    assert set(annual["evidence_id"].dropna()) == {"annual"}


def test_dimensioned_evidence_is_retained_but_not_projected() -> None:
    dimensioned = _event(evidence_id="segment", canonical_value="7", dimensions={"srt:ProductOrServiceAxis": "us-gaap:ServiceMember"})
    consolidated = _event(evidence_id="consolidated", canonical_value="10")
    evidence = pd.DataFrame([dimensioned, consolidated])
    admitted = consolidated_projection_events(evidence)
    assert set(evidence["evidence_id"]) == {"segment", "consolidated"}
    assert admitted["evidence_id"].tolist() == ["consolidated"]
    assert project_events_asof(_grid(), admitted)["canonical_value"].dropna().tolist() == ["10", "10"]
    with pytest.raises(ValueError, match="dimension-bearing"):
        project_events_asof(_grid(), evidence)


def test_pre_membership_same_cik_and_predecessor_cik_fail_closed() -> None:
    grid = _grid().iloc[1:].reset_index(drop=True)
    old_same_cik = pd.DataFrame([_event(effective_session="2019-12-31")])
    projected = project_events_asof(grid, old_same_cik)
    assert projected["evidence_id"].notna().all()
    assert (projected["session"] >= pd.Timestamp("2020-01-03")).all()
    predecessor = pd.DataFrame([_event(cik="0000000009", effective_session="2019-12-31")])
    assert project_events_asof(grid, predecessor).empty


def test_parquet_exact_value_and_partition_policy() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "events"
        paths = write_exact_event_parquet([{
            "cik": "0000000001", "standard_concept": "Revenue", "canonical_value": "9007199254740993",
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
        "standard_concept": ["Revenue"], "period_class": ["DURATION_QUARTERLY"], "canonical_value": ["10"],
        "episode_id": [EPISODE["episode_id"]], "cik": ["0000000001"],
        "evidence_id": ["e"], "accession": ["a"],
    })
    projected["feature_identity"] = [feature_identity(row.standard_concept, row.period_class) for row in projected.itertuples()]
    features = projected.pivot(index=["session", "instrument"], columns="feature_identity", values="canonical_value")
    assert list(features.columns) == ["Revenue__DURATION_QUARTERLY"]
    assert "evidence_id" not in features.columns
