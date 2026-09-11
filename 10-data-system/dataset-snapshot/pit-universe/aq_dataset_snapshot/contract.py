"""Small immutable downstream contract for a research universe snapshot."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatasetSnapshotV1:
    schema_version: str
    universe_id: str
    coverage_start: str
    coverage_end: str
    row_count: int
    publication_state: str = "RESEARCH_READY"

    def __post_init__(self) -> None:
        if self.schema_version != "DatasetSnapshotV1":
            raise ValueError("unsupported DatasetSnapshot schema")
        if not self.universe_id or self.row_count <= 0:
            raise ValueError("snapshot identity and row count are required")
        if self.coverage_start >= self.coverage_end:
            raise ValueError("snapshot coverage must be a non-empty half-open interval")
        if self.publication_state != "RESEARCH_READY":
            raise ValueError("P1 DatasetSnapshot accepts research-ready universes only")
