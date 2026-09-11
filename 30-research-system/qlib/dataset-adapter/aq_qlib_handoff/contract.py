"""Small result contract for the Qlib instruments handoff."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QlibUniverseHandoffV1:
    schema_version: str
    market: str
    episode_count: int
    instrument_range_count: int
    instruments_file: str
    episode_map_file: str

    def __post_init__(self) -> None:
        if self.schema_version != "QlibUniverseHandoffV1":
            raise ValueError("unsupported Qlib handoff schema")
        if not self.market or self.episode_count <= 0:
            raise ValueError("Qlib handoff requires a market and episodes")
        if self.instrument_range_count != self.episode_count:
            raise ValueError("every episode must remain one Qlib membership range")
