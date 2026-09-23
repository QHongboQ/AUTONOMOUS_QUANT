"""Fail-closed PIT projection tests without private SEC or P1 payloads."""

from __future__ import annotations

import json

import pandas as pd
import pytest

import aq_p5_projection


def _facts() -> pd.DataFrame:
    return pd.DataFrame([{
        "cik": "0000000001", "accession": "0000000001-20-000001",
        "standard_concept": "Assets", "period_class": "INSTANT",
        "effective_session": "2020-01-03", "evidence_id": "e1",
        "canonical_value": "123", "period_start": None,
        "period_end": "2019-12-31", "dimensions": "{}",
        "native_group_priority": 0, "unit": "USD",
    }])


def _grid() -> pd.DataFrame:
    return pd.DataFrame({
        "session": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
        "episode_id": ["P1", "P1", "P2"],
        "instrument": ["P1", "P1", "P2"],
        "historical_ticker": ["X", "X", "Y"],
        "cik": ["0000000001", "0000000001", None],
        "binding_id": ["b1", "b1", None],
        "identity_excluded": [False, False, True],
    })


def _inputs(tmp_path, monkeypatch, facts):
    bulk = tmp_path / "bulk"
    bulk.mkdir()
    (bulk / "manifest.json").write_text(json.dumps({
        "bound_cik_count": 711,
        "unresolved_exact_acceptance_exclusion_count": 5,
    }), encoding="utf-8")
    facts.to_parquet(bulk / "CIK0000000001.parquet", index=False)
    episodes = tmp_path / "episodes.jsonl"
    bindings = tmp_path / "bindings.json"
    episodes.write_text("test\n", encoding="utf-8")
    bindings.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(aq_p5_projection, "_grid", lambda *_: _grid())
    return bulk, episodes, bindings


def test_no_early_visibility_and_identity_exclusion_remains_missing(tmp_path, monkeypatch) -> None:
    bulk, episodes, bindings = _inputs(tmp_path, monkeypatch, _facts())
    result = aq_p5_projection.build_projection(
        bulk_root=bulk, episodes_path=episodes, binding_path=bindings,
        output=tmp_path / "projection",
    )
    assert result["identity_exclusion_session_rows"] == 1
    assert result["early_visibility_count"] == 0
    assert result["cross_cik_contamination_count"] == 0
    grid = pd.read_parquet(tmp_path / "projection" / "episode_sessions.parquet")
    assert bool(grid.loc[grid["episode_id"] == "P2", "identity_excluded"].all())
    stream = pd.read_parquet(tmp_path / "projection" / "streams" / "CIK0000000001.parquet")
    assert pd.isna(stream.iloc[0]["evidence_id"])
    assert stream.iloc[1]["evidence_id"] == "e1"


def test_duplicate_evidence_identity_rejected(tmp_path, monkeypatch) -> None:
    facts = pd.concat([_facts(), _facts()], ignore_index=True)
    bulk, episodes, bindings = _inputs(tmp_path, monkeypatch, facts)
    with pytest.raises(ValueError, match="quality gate"):
        aq_p5_projection.build_projection(
            bulk_root=bulk, episodes_path=episodes, binding_path=bindings,
            output=tmp_path / "projection",
        )


def test_comparative_period_does_not_regress_current_pit_value() -> None:
    facts = pd.DataFrame([
        {**_facts().iloc[0].to_dict(), "period_end": "2020-12-31", "evidence_id": "fy20",
         "effective_session": "2021-02-01", "accession": "0000000001-21-000001"},
        {**_facts().iloc[0].to_dict(), "period_end": "2020-12-31", "evidence_id": "comparative",
         "effective_session": "2022-02-01", "accession": "0000000001-22-000001"},
        {**_facts().iloc[0].to_dict(), "period_end": "2021-12-31", "evidence_id": "fy21",
         "effective_session": "2022-02-01", "accession": "0000000001-22-000001"},
        {**_facts().iloc[0].to_dict(), "period_end": "2020-12-31", "evidence_id": "old-amendment",
         "effective_session": "2022-03-01", "accession": "0000000001-22-000002"},
        {**_facts().iloc[0].to_dict(), "period_end": "2021-12-31", "evidence_id": "current-amendment",
         "effective_session": "2022-04-01", "accession": "0000000001-22-000003"},
    ])
    selected = aq_p5_projection._latest_economic_period_events(facts)
    assert selected["evidence_id"].tolist() == ["fy20", "fy21", "current-amendment"]
