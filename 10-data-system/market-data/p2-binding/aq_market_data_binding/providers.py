"""Two thin OpenBB provider translations; transport remains upstream-owned."""

from __future__ import annotations

from typing import Any, Callable

from openbb_core.provider.abstract.annotated_result import AnnotatedResult
from openbb_core.provider.abstract.fetcher import Fetcher
from openbb_core.provider.standard_models.equity_historical import (
    EquityHistoricalData,
    EquityHistoricalQueryParams,
)
from pydantic import Field


class QuantiacsEquityHistoricalQuery(EquityHistoricalQueryParams):
    provider_asset_identifier: str = Field(min_length=1)
    provider_symbol: str = Field(min_length=1)
    adjustment_semantics: str = Field(min_length=1)
    source_observation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class SimFinEquityHistoricalQuery(EquityHistoricalQueryParams):
    simfin_id: int = Field(gt=0)
    provider_symbol: str = Field(min_length=1)
    adjustment_semantics: str = Field(min_length=1)
    source_observation_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


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
        result = [
            EquityHistoricalData(
                date=row["time"], open=row["open"], high=row["high"],
                low=row["low"], close=row["close"], volume=row.get("vol"),
            )
            for row in rows
        ]
        return AnnotatedResult(result=result, metadata={
            "provider": "QUANTIACS",
            "provider_asset_identifier": query.provider_asset_identifier,
            "provider_symbol": query.provider_symbol,
            "adjustment_semantics": query.adjustment_semantics,
            "source_observation_sha256": query.source_observation_sha256,
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
        result = [
            EquityHistoricalData(
                date=row["Date"], open=row["Open"], high=row["High"],
                low=row["Low"], close=row["Close"], volume=row.get("Volume"),
            )
            for row in rows
        ]
        return AnnotatedResult(result=result, metadata={
            "provider": "SIMFIN",
            "provider_asset_identifier": query.simfin_id,
            "provider_symbol": query.provider_symbol,
            "adjustment_semantics": query.adjustment_semantics,
            "source_observation_sha256": query.source_observation_sha256,
        })
