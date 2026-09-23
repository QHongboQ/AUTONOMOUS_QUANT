"""Thin P5 PIT session projection over immutable bulk evidence."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import exchange_calendars as xcals
import pandas as pd
import pandera as pa

from aq_hybrid_fundamentals import project_events_asof


GRID_SCHEMA = pa.DataFrameSchema({
    "session": pa.Column(pa.DateTime, nullable=False),
    "episode_id": pa.Column(str, nullable=False),
    "instrument": pa.Column(str, nullable=False),
}, strict=False)
STREAM_SCHEMA = pa.DataFrameSchema({
    "session": pa.Column(pa.DateTime, nullable=False),
    "episode_id": pa.Column(str, nullable=False),
    "standard_concept": pa.Column(str, nullable=False),
    "period_class": pa.Column(str, nullable=False),
}, strict=False)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _latest_economic_period_events(facts: pd.DataFrame) -> pd.DataFrame:
    """Choose the newest reported period within each native period stream.

    CompanyFacts repeats older comparative periods in later accessions. Those
    observations remain in evidence, but must not regress the current PIT
    feature to an older economic period. This does not classify or derive a
    period; EdgarTools has already assigned the native period class.
    """

    selected = facts.copy()
    selected["economic_period_end"] = pd.to_datetime(selected["period_end"], errors="raise")
    keys = ["standard_concept", "period_class"]
    selected = selected.sort_values(
        [*keys, "effective_session", "economic_period_end", "native_group_priority",
         "accession", "evidence_id"],
        ascending=[True, True, True, False, True, False, True],
        kind="mergesort",
    )
    selected = selected.drop_duplicates([*keys, "effective_session"], keep="first")
    cumulative_latest = selected.groupby(keys, sort=False)["economic_period_end"].cummax()
    previous_latest = cumulative_latest.groupby([selected[key] for key in keys], sort=False).shift()
    selected = selected[previous_latest.isna() | (selected["economic_period_end"] >= previous_latest)]
    return selected.drop(columns="economic_period_end")


def _grid(episodes_path: Path, binding_path: Path, historical_end: date) -> pd.DataFrame:
    episodes = [json.loads(line) for line in episodes_path.read_text(encoding="utf-8").splitlines() if line]
    bindings_doc = json.loads(binding_path.read_text(encoding="utf-8"))
    if len(episodes) != 832 or bindings_doc["bound_episode_count"] != 721:
        raise ValueError("P1/P5 frozen episode population changed")
    grouped = defaultdict(list)
    for binding in bindings_doc["records"]:
        grouped[binding["episode_id"]].append(binding)
    calendar = xcals.get_calendar("XNYS")
    rows: list[dict[str, object]] = []
    for episode in episodes:
        start = max(date.fromisoformat(episode["valid_from"]), date.fromisoformat(episode["membership_from"]))
        stop = min(date.fromisoformat(episode["valid_to"]),
                   date.fromisoformat(episode["membership_to"]), historical_end + timedelta(days=1))
        if start >= stop:
            continue
        for session in calendar.sessions_in_range(start, stop - timedelta(days=1)):
            day = session.date()
            candidates = [binding for binding in grouped[episode["episode_id"]]
                          if date.fromisoformat(binding["valid_from"]) <= day
                          < date.fromisoformat(binding["valid_to"])]
            if len(candidates) > 1:
                raise ValueError("overlapping CIK bindings on one P1 episode session")
            binding = candidates[0] if candidates else None
            rows.append({"session": pd.Timestamp(day), "episode_id": episode["episode_id"],
                         "instrument": episode["episode_id"], "historical_ticker": episode["normalized_ticker"],
                         "cik": str(binding["cik"]) if binding else None,
                         "binding_id": str(binding["binding_id"]) if binding else None,
                         "identity_excluded": binding is None})
    grid = GRID_SCHEMA.validate(pd.DataFrame.from_records(rows), lazy=True)
    if grid.duplicated(["session", "episode_id"]).any():
        raise ValueError("duplicate P1 episode session")
    return grid.sort_values(["session", "episode_id"], kind="mergesort").reset_index(drop=True)


def build_projection(
    *,
    bulk_root: Path,
    episodes_path: Path,
    binding_path: Path,
    output: Path,
    historical_end: str = "2024-12-31",
) -> dict[str, object]:
    """Materialize per-CIK, period-isolated as-of streams; leave NaNs missing."""

    bulk_manifest = json.loads((bulk_root / "manifest.json").read_text(encoding="utf-8"))
    if bulk_manifest["bound_cik_count"] != 711 or bulk_manifest["unresolved_exact_acceptance_exclusion_count"] != 5:
        raise ValueError("full 711-CIK bulk evidence is not sealed")
    grid = _grid(episodes_path, binding_path, date.fromisoformat(historical_end))
    output.mkdir(parents=True, exist_ok=True)
    grid.to_parquet(output / "episode_sessions.parquet", index=False, compression="zstd")
    stream_root = output / "streams"
    stream_root.mkdir(exist_ok=True)
    counts = {"session_rows": len(grid), "identity_exclusion_session_rows": int(grid["identity_excluded"].sum()),
              "projected_stream_rows": 0, "early_visibility_count": 0,
              "cross_cik_contamination_count": 0, "duplicate_final_event_id_count": 0}
    for cik, eligible in grid[grid["cik"].notna()].groupby("cik", sort=True):
        fact_file = bulk_root / f"CIK{cik}.parquet"
        if not fact_file.is_file():
            continue
        facts = pd.read_parquet(fact_file)
        if not bool((facts["cik"] == cik).all()):
            raise ValueError(f"cross-CIK bulk evidence in {fact_file.name}")
        counts["duplicate_final_event_id_count"] += int(facts["evidence_id"].duplicated().sum())
        facts = facts[facts["dimensions"] == "{}"].copy()
        if facts.empty:
            continue
        # Native group priority resolves same-grain aliases without an AQ tag
        # dictionary. Each period class remains an independent PIT stream.
        facts = facts.sort_values(["effective_session", "accession", "standard_concept",
                                   "period_class", "period_end", "native_group_priority", "evidence_id"],
                                  kind="mergesort")
        facts = facts.drop_duplicates(["accession", "standard_concept", "period_class",
                                      "period_start", "period_end", "unit"], keep="first")
        facts = _latest_economic_period_events(facts)
        events = facts.rename(columns={"period_start": "report_period_start",
                                      "period_end": "report_period_end"})[[
            "cik", "standard_concept", "period_class", "effective_session", "evidence_id",
            "accession", "canonical_value", "report_period_start", "report_period_end",
        ]].copy()
        projected = project_events_asof(eligible, events)
        if projected.empty:
            continue
        projected = STREAM_SCHEMA.validate(projected, lazy=True)
        projected.to_parquet(stream_root / fact_file.name, index=False, compression="zstd")
        counts["projected_stream_rows"] += len(projected)
        counts["early_visibility_count"] += int((
            projected["evidence_id"].notna() &
            (projected["effective_session"] > projected["session"])).sum())
        if "cik_event" in projected.columns:
            counts["cross_cik_contamination_count"] += int((
                projected["evidence_id"].notna() & projected["cik_event"].notna() &
                (projected["cik"] != projected["cik_event"])).sum())
    if any(counts[key] for key in ("early_visibility_count", "cross_cik_contamination_count",
                                    "duplicate_final_event_id_count")):
        raise ValueError("PIT projection quality gate failed")
    result = {"schema": "AQ_P5_MINIMAL_PIT_PROJECTION_V1",
              "bulk_manifest_sha256": _sha256(bulk_root / "manifest.json"),
              "episodes_sha256": _sha256(episodes_path), "bindings_sha256": _sha256(binding_path),
              "historical_end": historical_end, **counts}
    (output / "manifest.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result
