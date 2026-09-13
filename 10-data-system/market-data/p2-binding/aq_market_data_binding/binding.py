"""AQ's thin evidence and fail-closed policy boundary over DuckDB relations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

import duckdb
import pandas as pd
import pandera.pandas as pa


_HASH = re.compile(r"^[0-9a-f]{64}$")
_FIGI = re.compile(r"^[A-Z0-9]{12}$")
_ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")


@dataclass(frozen=True, slots=True)
class OpenFigiEvidence:
    figi: str
    mapping_identifier: str

    def __post_init__(self) -> None:
        if self.figi.lower().startswith("tts-") or not _FIGI.fullmatch(self.figi):
            raise ValueError("OpenFIGI evidence requires a standard 12-character FIGI")


@dataclass(frozen=True, slots=True)
class SecEvidence:
    cik: int
    accession: str
    filing_type: str
    filed_date: date
    effective_date: date
    content_hash: str
    decision_role: str

    @classmethod
    def from_edgartools(
        cls, filing: object, *, effective_date: date, content_hash: str,
        decision_role: str,
    ) -> "SecEvidence":
        from edgar import Filing

        if not isinstance(filing, Filing):
            raise TypeError("SEC evidence must originate from edgartools")
        return cls(
            cik=int(filing.cik), accession=str(filing.accession_no),
            filing_type=str(filing.form),
            filed_date=date.fromisoformat(str(filing.filing_date)),
            effective_date=effective_date, content_hash=content_hash,
            decision_role=decision_role,
        )

    def __post_init__(self) -> None:
        if self.cik <= 0 or not _ACCESSION.fullmatch(self.accession):
            raise ValueError("invalid SEC filing identity")
        if not _HASH.fullmatch(self.content_hash) or not self.decision_role.strip():
            raise ValueError("invalid SEC decision evidence")


_SCHEMAS = {
    "binding_episodes": pa.DataFrameSchema({
        "case_id": pa.Column(str, unique=True),
        "episode_id": pa.Column(str, unique=True),
        "valid_from": pa.Column("datetime64[ns]"),
        "valid_to": pa.Column("datetime64[ns]"),
        "required_sessions": pa.Column(int, checks=pa.Check.ge(1)),
    }, strict=True),
    "binding_candidates": pa.DataFrameSchema({
        "case_id": pa.Column(str),
        "provider_asset_identifier": pa.Column(str),
        "provider_symbol": pa.Column(str),
        "provider_identity_supported": pa.Column(bool),
        "sec_identity_supported": pa.Column(bool),
        "openfigi_supported": pa.Column(bool),
    }, strict=True),
    "binding_observations": pa.DataFrameSchema({
        "provider_asset_identifier": pa.Column(str),
        "session_date": pa.Column("datetime64[ns]"),
        "close": pa.Column(float, nullable=False),
    }, strict=True),
    "binding_sessions": pa.DataFrameSchema({
        "case_id": pa.Column(str),
        "session_date": pa.Column("datetime64[ns]"),
    }, strict=True),
}


def evaluate_provider_bindings(
    connection: duckdb.DuckDBPyConnection,
    *, episodes: pd.DataFrame, candidates: pd.DataFrame,
    observations: pd.DataFrame, sessions: pd.DataFrame,
) -> pd.DataFrame:
    """Validate public relations, then delegate their composition to DuckDB."""
    tables = {
        "binding_episodes": episodes,
        "binding_candidates": candidates,
        "binding_observations": observations,
        "binding_sessions": sessions,
    }
    for name, frame in tables.items():
        connection.register(name, _SCHEMAS[name].validate(frame))
    sql = Path(__file__).with_name("binding.sql").read_text(encoding="utf-8")
    for statement in sql.split(";"):
        if statement.strip():
            connection.execute(statement)
    return connection.sql("SELECT * FROM binding_decisions ORDER BY case_id").df()
