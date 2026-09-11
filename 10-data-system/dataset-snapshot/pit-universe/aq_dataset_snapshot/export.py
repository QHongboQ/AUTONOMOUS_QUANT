"""Deterministic JSONL export from the public PIT research contract."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import TYPE_CHECKING

from .contract import DatasetSnapshotV1

if TYPE_CHECKING:
    from aq_pit import ResearchReadyUniverse


_ROW_FIELDS = ("episode_id", "ticker", "membership_from", "membership_to")


def _json_bytes(value: object) -> bytes:
    if isinstance(value, DatasetSnapshotV1):
        value = asdict(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _validated_rows(universe: ResearchReadyUniverse) -> tuple[dict[str, str], ...]:
    if not universe.gate.research_ready:
        raise ValueError("DatasetSnapshot input is not research ready")
    rows = tuple(
        {
            "episode_id": row.episode_id,
            "ticker": row.ticker,
            "membership_from": row.membership_from,
            "membership_to": row.membership_to,
        }
        for row in universe.rows
    )
    if any(tuple(row) != _ROW_FIELDS for row in rows):
        raise ValueError("unexpected public research-universe row shape")
    if len({row["episode_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate episode_id in DatasetSnapshot input")
    if any(row["membership_from"] >= row["membership_to"] for row in rows):
        raise ValueError("DatasetSnapshot membership intervals must be non-empty")
    ordered = tuple(sorted(
        rows,
        key=lambda row: (
            row["membership_from"], row["ticker"],
            row["membership_to"], row["episode_id"],
        ),
    ))
    if rows != ordered:
        raise ValueError("public research-universe rows are not deterministically ordered")
    return rows


def export_dataset_snapshot(
    universe: ResearchReadyUniverse,
    output_directory: Path,
) -> DatasetSnapshotV1:
    """Write only the stable row JSONL and its small logical contract metadata."""
    rows = _validated_rows(universe)
    snapshot = DatasetSnapshotV1(
        schema_version="DatasetSnapshotV1",
        universe_id="SP500_PIT_RESEARCH_V1",
        coverage_start=min(row["membership_from"] for row in rows),
        coverage_end=max(row["membership_to"] for row in rows),
        row_count=len(rows),
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    rows_path = output_directory / "episodes.jsonl"
    metadata_path = output_directory / "snapshot.json"
    rows_path.write_bytes(b"".join(_json_bytes(row) + b"\n" for row in rows))
    metadata_path.write_bytes(_json_bytes(snapshot) + b"\n")
    return snapshot
