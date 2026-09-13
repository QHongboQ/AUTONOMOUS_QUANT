"""Thin upstream adapters and AQ's fail-closed episode-binding boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from pathlib import Path
from typing import Any, Callable

import duckdb
import pandas as pd
import pandera.pandas as pa
from openbb_core.provider.abstract.annotated_result import AnnotatedResult
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_historical import (
    EquityHistoricalData,
    EquityHistoricalQueryParams,
)
from pydantic import Field


_HASH = re.compile(r"^[0-9a-f]{64}$")
_FIGI = re.compile(r"^[A-Z0-9]{12}$")
_ACCESSION = re.compile(r"^\d{10}-\d{2}-\d{6}$")


class QuantiacsEquityHistoricalQuery(EquityHistoricalQueryParams):
    provider_asset_identifier: str = Field(min_length=1)


class SimFinEquityHistoricalQuery(EquityHistoricalQueryParams):
    simfin_id: int = Field(gt=0)


class QuantiacsEquityHistoricalFetcher(
    Fetcher[QuantiacsEquityHistoricalQuery, AnnotatedResult[list[EquityHistoricalData]]]
):
    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> QuantiacsEquityHistoricalQuery:
        return QuantiacsEquityHistoricalQuery(**params)

    @staticmethod
    def extract_data(query, credentials, *, upstream_loader: Callable, **kwargs):
        return upstream_loader(query)

    @staticmethod
    def transform_data(query, data, **kwargs):
        rows = data.to_dict("records") if hasattr(data, "to_dict") else data
        result = [EquityHistoricalData(
            date=row["time"], open=row["open"], high=row["high"],
            low=row["low"], close=row["close"], volume=row.get("vol"),
        ) for row in rows]
        return AnnotatedResult(result=result, metadata={
            "provider": "QUANTIACS",
            "provider_asset_identifier": query.provider_asset_identifier,
            "symbol": query.symbol,
            "start_date": query.start_date,
            "end_date": query.end_date,
        })


class SimFinEquityHistoricalFetcher(
    Fetcher[SimFinEquityHistoricalQuery, AnnotatedResult[list[EquityHistoricalData]]]
):
    require_credentials = False

    @staticmethod
    def transform_query(params: dict[str, Any]) -> SimFinEquityHistoricalQuery:
        return SimFinEquityHistoricalQuery(**params)

    @staticmethod
    def extract_data(query, credentials, *, upstream_loader: Callable, **kwargs):
        return upstream_loader(query)

    @staticmethod
    def transform_data(query, data, **kwargs):
        rows = data.to_dict("records") if hasattr(data, "to_dict") else data
        result = [EquityHistoricalData(
            date=row["Date"], open=row["Open"], high=row["High"],
            low=row["Low"], close=row["Close"], volume=row.get("Volume"),
        ) for row in rows]
        return AnnotatedResult(result=result, metadata={
            "provider": "SIMFIN", "simfin_id": query.simfin_id,
            "symbol": query.symbol, "start_date": query.start_date,
            "end_date": query.end_date,
        })


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
        cls, filing: object, *, effective_date: date, content_hash: str, decision_role: str
    ) -> "SecEvidence":
        from edgar import Filing

        if not isinstance(filing, Filing):
            raise TypeError("SEC evidence must originate from edgartools")
        return cls(
            cik=int(getattr(filing, "cik")), accession=str(getattr(filing, "accession_no")),
            filing_type=str(getattr(filing, "form")), filed_date=date.fromisoformat(str(getattr(filing, "filing_date"))),
            effective_date=effective_date, content_hash=content_hash, decision_role=decision_role,
        )

    def __post_init__(self) -> None:
        if self.cik <= 0 or not _ACCESSION.fullmatch(self.accession):
            raise ValueError("invalid SEC filing identity")
        if not _HASH.fullmatch(self.content_hash) or not self.decision_role.strip():
            raise ValueError("invalid SEC decision evidence")


_SCHEMAS = {
    "binding_episodes": pa.DataFrameSchema({
        "case_id": pa.Column(str, unique=True), "episode_id": pa.Column(str, unique=True),
        "valid_from": pa.Column("datetime64[ns]"), "valid_to": pa.Column("datetime64[ns]"),
        "required_sessions": pa.Column(int, checks=pa.Check.ge(1)),
    }, strict=True),
    "binding_candidates": pa.DataFrameSchema({
        "case_id": pa.Column(str), "provider_asset_identifier": pa.Column(str),
        "provider_symbol": pa.Column(str), "provider_identity_supported": pa.Column(bool),
        "sec_identity_supported": pa.Column(bool), "openfigi_supported": pa.Column(bool),
    }, strict=True),
    "binding_observations": pa.DataFrameSchema({
        "provider_asset_identifier": pa.Column(str), "session_date": pa.Column("datetime64[ns]"),
        "close": pa.Column(float, nullable=False),
    }, strict=True),
    "binding_sessions": pa.DataFrameSchema({
        "case_id": pa.Column(str), "session_date": pa.Column("datetime64[ns]"),
    }, strict=True),
}


def evaluate_provider_bindings(
    connection: duckdb.DuckDBPyConnection,
    *, episodes: pd.DataFrame, candidates: pd.DataFrame,
    observations: pd.DataFrame, sessions: pd.DataFrame,
) -> pd.DataFrame:
    """Validate inputs, then delegate every relational operation to DuckDB."""
    tables = {
        "binding_episodes": episodes, "binding_candidates": candidates,
        "binding_observations": observations, "binding_sessions": sessions,
    }
    for name, frame in tables.items():
        connection.register(name, _SCHEMAS[name].validate(frame))
    sql = Path(__file__).with_name("provider_binding.sql").read_text(encoding="utf-8")
    for statement in sql.split(";"):
        if statement.strip():
            connection.execute(statement)
    return connection.sql("SELECT * FROM binding_decisions ORDER BY case_id").df()
