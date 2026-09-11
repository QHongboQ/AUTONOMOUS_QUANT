"""Convert a public AQ DatasetSnapshot into Qlib's instrument-range format."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date, timedelta
import json
from pathlib import Path

from .contract import QlibUniverseHandoffV1


_ROW_FIELDS = {"episode_id", "ticker", "membership_from", "membership_to"}
_METADATA_FIELDS = {
    "schema_version", "universe_id", "coverage_start", "coverage_end",
    "row_count", "publication_state",
}


def _json_line(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def _load_snapshot(snapshot_directory: Path) -> tuple[dict[str, object], tuple[dict[str, str], ...]]:
    metadata = json.loads((snapshot_directory / "snapshot.json").read_text(encoding="utf-8"))
    if set(metadata) != _METADATA_FIELDS:
        raise ValueError("unexpected DatasetSnapshot metadata shape")
    if metadata["schema_version"] != "DatasetSnapshotV1" or metadata["publication_state"] != "RESEARCH_READY":
        raise ValueError("Qlib handoff accepts only research-ready DatasetSnapshotV1")
    rows = tuple(
        json.loads(line)
        for line in (snapshot_directory / "episodes.jsonl").read_text(encoding="utf-8").splitlines()
    )
    if len(rows) != metadata["row_count"] or any(set(row) != _ROW_FIELDS for row in rows):
        raise ValueError("DatasetSnapshot row count or shape differs from its contract")
    episode_ids = [row["episode_id"] for row in rows]
    if len(episode_ids) != len(set(episode_ids)):
        raise ValueError("duplicate episode_id cannot be collapsed into Qlib")
    return metadata, rows


def prepare_qlib_universe(
    snapshot_directory: Path,
    output_directory: Path,
    *,
    market: str = "aq_pit",
) -> QlibUniverseHandoffV1:
    """Create Qlib's inclusive instrument spans while preserving AQ episode IDs."""
    _, rows = _load_snapshot(snapshot_directory)
    converted = []
    for row in rows:
        start = date.fromisoformat(row["membership_from"])
        end_exclusive = date.fromisoformat(row["membership_to"])
        end_inclusive = end_exclusive - timedelta(days=1)
        if start > end_inclusive:
            raise ValueError("Qlib instrument range would be empty")
        converted.append({
            **row,
            "qlib_end_inclusive": end_inclusive.isoformat(),
        })
    converted.sort(key=lambda row: (
        row["ticker"], row["membership_from"],
        row["qlib_end_inclusive"], row["episode_id"],
    ))
    by_ticker: dict[str, list[dict[str, str]]] = {}
    for row in converted:
        by_ticker.setdefault(row["ticker"], []).append(row)
    for ticker, ranges in by_ticker.items():
        for left, right in zip(ranges, ranges[1:]):
            if right["membership_from"] < left["membership_to"]:
                raise ValueError(f"overlapping membership episodes for {ticker}")

    instruments_directory = output_directory / "instruments"
    instruments_directory.mkdir(parents=True, exist_ok=True)
    instruments_path = instruments_directory / f"{market}.txt"
    episode_map_path = output_directory / "episode-map.jsonl"
    instruments_path.write_text("".join(
        f"{row['ticker']}\t{row['membership_from']}\t{row['qlib_end_inclusive']}\n"
        for row in converted
    ), encoding="utf-8", newline="")
    episode_map_path.write_text(
        "".join(_json_line(row) for row in converted),
        encoding="utf-8", newline="",
    )
    handoff = QlibUniverseHandoffV1(
        schema_version="QlibUniverseHandoffV1",
        market=market,
        episode_count=len(rows),
        instrument_range_count=len(converted),
        instruments_file=f"instruments/{market}.txt",
        episode_map_file="episode-map.jsonl",
    )
    (output_directory / "handoff.json").write_text(
        _json_line(asdict(handoff)), encoding="utf-8", newline="",
    )
    return handoff
