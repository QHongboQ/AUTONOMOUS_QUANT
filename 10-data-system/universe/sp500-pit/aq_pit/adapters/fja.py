"""Convert the pinned local FJA source shape into thin PIT domain inputs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path

import pandas as pd

from ..canonical import deterministic_id, sha256_hex
from ..domain import SnapshotObservationV1, normalize_ticker
from ..schema.pandera import validate_fja_source_table, validate_snapshot_observation_table


FJA_COMMIT = "a2430f2af0c79ddf0748e91de11bdeb1616ab5a7"
FJA_SOURCE_FILE = "S&P 500 Historical Components & Changes (Updated).csv"
FJA_SHA256 = "646b2e47284abfb675abebacd4a4035ba22a79ea1ccdeccce7fbe5f0e27bab3a"


@dataclass(frozen=True, slots=True)
class ResearchInputs:
    observations: tuple[SnapshotObservationV1, ...]
    historical_ledger: tuple[dict[str, object], ...]


def load_research_inputs(data_root: Path) -> ResearchInputs:
    """Read only the pinned local inputs needed by the P1 research path."""
    source_path = data_root / "raw" / "fja_sp500" / "repo" / FJA_SOURCE_FILE
    raw = source_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FJA_SHA256:
        raise ValueError("immutable FJA source differs from the accepted P1 input")
    try:
        frame = pd.read_csv(
            io.StringIO(raw.decode("utf-8-sig"), newline=""),
            dtype="string",
            keep_default_na=False,
        )
    except (UnicodeDecodeError, pd.errors.ParserError, ValueError) as exc:
        raise ValueError("FJA source must be a UTF-8 two-column CSV") from exc
    if "date" in frame:
        frame["date"] = frame["date"].str.strip()
    validate_fja_source_table(frame.to_dict(orient="records"))
    source_id = deterministic_id("P1SRC-", {
        "adapter": "thin-fja-pit-v1",
        "commit": FJA_COMMIT,
        "sha256": FJA_SHA256,
    })
    rows = tuple(
        (
            row.date,
            tuple(sorted(normalize_ticker(value) for value in row.tickers.split(",") if value.strip())),
        )
        for row in frame.itertuples(index=False)
    )
    start_session = "2010-01-04"
    seeds = [row for row in rows if row[0] <= start_session]
    if not seeds:
        raise ValueError("FJA source has no as-of seed for the research window")
    selected = ((start_session, seeds[-1][0], seeds[-1][1]),) + tuple(
        (session, session, tickers)
        for session, tickers in rows
        if start_session < session <= "2024-12-31"
    )
    observations = tuple(
        SnapshotObservationV1(
            observation_id=deterministic_id("P1OBS-", {
                "index_id": "SP500", "session": session,
                "source_id": source_id, "tickers": tickers,
            }),
            index_id="SP500",
            effective_session=session,
            tickers=tickers,
            source_id=source_id,
            evidence_hash=sha256_hex({
                "raw_source_sha256": FJA_SHA256,
                "source_session": source_session,
                "session": session,
                "tickers": tickers,
            }),
        )
        for session, source_session, tickers in selected
    )
    validate_snapshot_observation_table(observations)
    ledger_path = data_root / "audit" / "unresolved_findings" / "unresolved_findings.json"
    ledger = tuple(json.loads(ledger_path.read_text(encoding="utf-8")))
    return ResearchInputs(observations=observations, historical_ledger=ledger)
