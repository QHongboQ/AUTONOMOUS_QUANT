"""Thin PIT policy for accession-admitted fundamental event projection."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

FROZEN_STANDARD_METRICS = (
    "Revenue",
    "Net Income",
    "Total Assets",
    "Total Liabilities",
    "Total Stockholders' Equity",
    "Net Cash from Operating Activities",
    "Cash and Cash Equivalents",
    "Total Current Assets",
    "Total Current Liabilities",
    "Short Term Debt",
    "Long Term Debt",
)
ALLOWED_BINDING_CLASSIFICATIONS = frozenset({"PASS_EXACT", "PASS_CORROBORATED"})


def _utc(value: object, name: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"{name} must be timezone-aware")
    return timestamp.tz_convert("UTC")


def effective_session(first_available_at: object, calendar: Any) -> pd.Timestamp:
    """Return the first XNYS session whose open is strictly after availability."""

    available = _utc(first_available_at, "first_available_at")
    start = (available - pd.Timedelta(days=2)).date()
    end = (available + pd.Timedelta(days=14)).date()
    for session in calendar.sessions_in_range(start, end):
        if calendar.session_open(session) > available:
            return pd.Timestamp(session).tz_localize(None).normalize()
    raise ValueError("no future XNYS session found within the bounded search")


def eligible_episode_sessions(
    sessions: Iterable[object],
    *,
    episode: Mapping[str, object],
    binding: Mapping[str, object],
    membership_intervals: Sequence[Mapping[str, object]],
) -> pd.DataFrame:
    """Apply episode, binding, and PIT membership containment fail-closed."""

    if binding.get("episode_id") != episode.get("episode_id"):
        raise ValueError("binding does not name the episode")
    if binding.get("binding_classification") not in ALLOWED_BINDING_CLASSIFICATIONS:
        raise ValueError("binding classification is not admissible")
    episode_from = date.fromisoformat(str(episode["valid_from"]))
    episode_to = date.fromisoformat(str(episode["valid_to"]))
    binding_from = date.fromisoformat(str(binding["valid_from"]))
    binding_to = date.fromisoformat(str(binding["valid_to"]))
    if binding_from < episode_from or binding_to > episode_to:
        raise ValueError("binding exceeds episode authority")
    relevant = [row for row in membership_intervals if row.get("episode_id") == episode["episode_id"]]
    if not relevant:
        raise ValueError("episode has no PIT membership interval")
    rows: list[dict[str, object]] = []
    for raw in sessions:
        session = pd.Timestamp(raw).date()
        in_membership = any(
            date.fromisoformat(str(item["membership_from"])) <= session
            < date.fromisoformat(str(item["membership_to"]))
            for item in relevant
        )
        if episode_from <= session < episode_to and binding_from <= session < binding_to and in_membership:
            rows.append(
                {
                    "session": pd.Timestamp(session),
                    "episode_id": str(episode["episode_id"]),
                    "instrument": str(episode["ticker"]),
                    "historical_ticker": str(episode["ticker"]),
                    "cik": str(binding["cik"]),
                    "binding_id": str(binding["binding_id"]),
                }
            )
    return pd.DataFrame(rows)


def project_events_asof(grid: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """Use pandas.merge_asof for deterministic, CIK-isolated sparse projection."""

    grid_required = {"session", "episode_id", "instrument", "cik", "binding_id"}
    event_required = {
        "cik", "standard_metric", "period_class", "effective_session",
        "evidence_id", "accession", "canonical_value",
    }
    if not grid_required.issubset(grid.columns) or not event_required.issubset(events.columns):
        raise ValueError("projection relation lacks required columns")
    if not bool(events["standard_metric"].isin(FROZEN_STANDARD_METRICS).all()):
        raise ValueError("event uses an unfrozen standard metric")
    left_parts: list[pd.DataFrame] = []
    combinations = events[["cik", "standard_metric", "period_class"]].drop_duplicates()
    for _, key in combinations.iterrows():
        matching = grid[grid["cik"] == key["cik"]].copy()
        if matching.empty:
            continue
        matching["standard_metric"] = key["standard_metric"]
        matching["period_class"] = key["period_class"]
        left_parts.append(matching)
    if not left_parts:
        return pd.DataFrame(columns=[*grid.columns, *event_required])
    left = pd.concat(left_parts, ignore_index=True)
    # pandas requires the two as-of keys to have the exact same datetime unit.
    # Normalize both explicitly because upstream frames may arrive as seconds,
    # microseconds, or nanoseconds depending on their Arrow/Pandas producer.
    left["session"] = pd.to_datetime(left["session"]).astype("datetime64[ns]")
    right = events.copy()
    right["effective_session"] = pd.to_datetime(right["effective_session"]).astype(
        "datetime64[ns]"
    )
    right = right.sort_values(
        ["effective_session", "cik", "standard_metric", "period_class", "accession", "evidence_id"],
        kind="mergesort",
    )
    left = left.sort_values(
        ["session", "cik", "standard_metric", "period_class", "episode_id"],
        kind="mergesort",
    )
    projected = pd.merge_asof(
        left,
        right,
        left_on="session",
        right_on="effective_session",
        by=["cik", "standard_metric", "period_class"],
        direction="backward",
        allow_exact_matches=True,
        suffixes=("", "_event"),
    )
    contaminated = projected[
        projected["evidence_id"].notna()
        & projected["cik_event"].notna()
        & (projected["cik"] != projected["cik_event"])
    ] if "cik_event" in projected.columns else projected.iloc[0:0]
    if not contaminated.empty:
        raise ValueError("cross-CIK contamination")
    early = projected[
        projected["evidence_id"].notna()
        & (projected["effective_session"] > projected["session"])
    ]
    if not early.empty:
        raise ValueError("early fundamental visibility")
    return projected.sort_values(
        ["session", "instrument", "standard_metric", "period_class"], kind="mergesort"
    ).reset_index(drop=True)


def write_exact_event_parquet(rows: Sequence[Mapping[str, object]], root: Path) -> tuple[Path, ...]:
    """Write exact canonical values as strings, partitioned only by availability year."""

    if root.exists():
        raise FileExistsError(f"event root already exists: {root}")
    by_year: dict[int, list[dict[str, object]]] = {}
    for raw in rows:
        row = dict(raw)
        value = str(row["canonical_value"])
        if str(Decimal(value)) != value and format(Decimal(value), "f") != value:
            raise ValueError("canonical_value is not an exact decimal string")
        available = _utc(row["first_available_at"], "first_available_at")
        row["canonical_value"] = value
        row["first_available_at"] = available.isoformat()
        by_year.setdefault(available.year, []).append(row)
    paths: list[Path] = []
    for year, records in sorted(by_year.items()):
        partition = root / f"first_available_year={year}"
        partition.mkdir(parents=True)
        records.sort(key=lambda row: (str(row["cik"]), str(row["first_available_at"]), str(row["accession"]), str(row["evidence_id"])))
        table = pa.Table.from_pylist(records)
        path = partition / "events.parquet"
        pq.write_table(table, path, compression="zstd")
        replay = pq.read_table(path).to_pylist()
        if [row["canonical_value"] for row in replay] != [row["canonical_value"] for row in records]:
            raise ValueError("lossy canonical value Parquet roundtrip")
        paths.append(path)
    return tuple(paths)


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def artifact_identity(paths: Iterable[Path]) -> list[dict[str, object]]:
    result = []
    for path in sorted(paths, key=lambda item: item.as_posix()):
        payload = path.read_bytes()
        result.append({"path": path.as_posix(), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    return result


__all__ = [
    "FROZEN_STANDARD_METRICS",
    "artifact_identity",
    "canonical_sha256",
    "effective_session",
    "eligible_episode_sessions",
    "project_events_asof",
    "write_exact_event_parquet",
]
