"""Generic structural validation at the P1 PIT table boundaries.

The validators return ``None`` and never expose pandas or Pandera objects as
domain contracts. Financial truth and evidence authority remain outside this
leaf.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date
from enum import Enum
import re
from typing import Iterable, Mapping

import pandas as pd
import pandera.pandas as pa


_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TICKER = re.compile(r"^[A-Z0-9][A-Z0-9.\-]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

_MEMBERSHIP_ACTIONS = ("ADD", "REMOVE")
_SESSION_BOUNDARIES = (
    "BEFORE_MARKET_OPEN",
    "AFTER_MARKET_CLOSE",
    "EFFECTIVE_SESSION",
    "SOURCE_DEFINED",
    "AMBIGUOUS",
)
_AMBIGUITY_STATES = ("CLEAR", "AMBIGUOUS")
_RESOLUTION_STATES = ("RESOLVED", "MANUAL_REVIEW_REQUIRED", "REJECTED")


def _is_iso_date(value: object) -> bool:
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _is_ticker_tuple(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and value == tuple(sorted(set(value)))
        and all(isinstance(item, str) and _TICKER.fullmatch(item) for item in value)
    )


def _is_sorted_unique_text_tuple(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and value == tuple(sorted(set(value)))
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
    )


def _plain(value: object) -> object:
    return value.value if isinstance(value, Enum) else value


def _records(items: Iterable[object]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for item in items:
        if isinstance(item, Mapping):
            records.append({str(key): _plain(value) for key, value in item.items()})
        elif is_dataclass(item) and not isinstance(item, type):
            records.append({field.name: _plain(getattr(item, field.name)) for field in fields(item)})
        else:
            raise ValueError("table rows must be mappings or dataclass instances")
    return records


def _validate(schema: pa.DataFrameSchema, items: Iterable[object], table_name: str) -> None:
    records = _records(items)
    if not records:
        return
    try:
        schema.validate(pd.DataFrame.from_records(records), lazy=True)
    except (pa.errors.SchemaError, pa.errors.SchemaErrors) as exc:
        raise ValueError(f"{table_name} table failed structural validation") from exc


_NONEMPTY = pa.Check(lambda value: isinstance(value, str) and bool(value.strip()), element_wise=True)
_ISO = pa.Check(_is_iso_date, element_wise=True)
_TICKER_TEXT = pa.Check(
    lambda value: isinstance(value, str) and bool(_TICKER.fullmatch(value)),
    element_wise=True,
)
_HASH = pa.Check(
    lambda value: isinstance(value, str) and bool(_SHA256.fullmatch(value)),
    element_wise=True,
)


FJA_SOURCE_SCHEMA = pa.DataFrameSchema(
    {
        "date": pa.Column(str, checks=[_ISO], nullable=False, unique=True),
        "tickers": pa.Column(str, checks=[_NONEMPTY], nullable=False),
    },
    checks=[
        pa.Check(lambda frame: len(frame) > 0, error="at least one snapshot is required"),
        pa.Check(
            lambda frame: frame["date"].is_monotonic_increasing,
            error="snapshot dates must be strictly increasing",
        ),
    ],
    strict=True,
    ordered=True,
    name="FjaSourceTable",
)


SNAPSHOT_OBSERVATION_SCHEMA = pa.DataFrameSchema(
    {
        "observation_id": pa.Column(str, checks=[_NONEMPTY], nullable=False, unique=True),
        "index_id": pa.Column(str, checks=[_NONEMPTY], nullable=False),
        "effective_session": pa.Column(str, checks=[_ISO], nullable=False),
        "tickers": pa.Column(
            object,
            checks=[pa.Check(_is_ticker_tuple, element_wise=True)],
            nullable=False,
        ),
        "source_id": pa.Column(str, checks=[_NONEMPTY], nullable=False),
        "evidence_hash": pa.Column(str, checks=[_HASH], nullable=False),
        "schema_version": pa.Column(
            str,
            checks=[pa.Check.equal_to("SnapshotObservationV1")],
            nullable=False,
        ),
    },
    strict=True,
    unique=["index_id", "effective_session"],
    name="SnapshotObservationTable",
)


MEMBERSHIP_EVENT_SCHEMA = pa.DataFrameSchema(
    {
        "event_id": pa.Column(str, checks=[_NONEMPTY], nullable=False, unique=True),
        "index_id": pa.Column(str, checks=[_NONEMPTY], nullable=False),
        "action": pa.Column(str, checks=[pa.Check.isin(_MEMBERSHIP_ACTIONS)], nullable=False),
        "source_ticker": pa.Column(str, checks=[_TICKER_TEXT], nullable=False),
        "announcement_date": pa.Column(str, checks=[_ISO], nullable=True),
        "effective_date": pa.Column(str, checks=[_ISO], nullable=False),
        "effective_session": pa.Column(str, checks=[_ISO], nullable=False),
        "boundary_semantics": pa.Column(
            str,
            checks=[pa.Check.isin(_SESSION_BOUNDARIES)],
            nullable=False,
        ),
        "source_id": pa.Column(str, checks=[_NONEMPTY], nullable=False),
        "evidence_hash": pa.Column(str, checks=[_HASH], nullable=False),
        "reason": pa.Column(str, nullable=True),
        "schema_version": pa.Column(
            str,
            checks=[pa.Check.equal_to("IndexMembershipEventV1")],
            nullable=False,
        ),
    },
    strict=True,
    unique=["index_id", "action", "source_ticker", "effective_session", "source_id"],
    name="IndexMembershipEventTable",
)


IDENTITY_EVENT_SCHEMA = pa.DataFrameSchema(
    {
        "event_id": pa.Column(str, checks=[_NONEMPTY], nullable=False, unique=True),
        "old_ticker": pa.Column(str, checks=[_TICKER_TEXT], nullable=False),
        "new_ticker": pa.Column(str, checks=[_TICKER_TEXT], nullable=False),
        "announcement_date": pa.Column(str, checks=[_ISO], nullable=True),
        "effective_date": pa.Column(str, checks=[_ISO], nullable=False),
        "effective_session": pa.Column(str, checks=[_ISO], nullable=False),
        "boundary_semantics": pa.Column(
            str,
            checks=[pa.Check.isin(_SESSION_BOUNDARIES)],
            nullable=False,
        ),
        "source_id": pa.Column(str, checks=[_NONEMPTY], nullable=False),
        "evidence_hash": pa.Column(str, checks=[_HASH], nullable=False),
        "identity_anchor": pa.Column(str, nullable=True),
        "ambiguity_state": pa.Column(
            str,
            checks=[pa.Check.isin(_AMBIGUITY_STATES)],
            nullable=False,
        ),
        "schema_version": pa.Column(
            str,
            checks=[pa.Check.equal_to("TickerIdentityEventV1")],
            nullable=False,
        ),
    },
    strict=True,
    unique=["old_ticker", "new_ticker", "effective_session", "source_id"],
    name="TickerIdentityEventTable",
)


INSTRUMENT_EPISODE_SCHEMA = pa.DataFrameSchema(
    {
        "episode_id": pa.Column(str, checks=[_NONEMPTY], nullable=False, unique=True),
        "index_id": pa.Column(str, checks=[_NONEMPTY], nullable=False),
        "source_ticker": pa.Column(str, checks=[_TICKER_TEXT], nullable=False),
        "normalized_ticker": pa.Column(str, checks=[_TICKER_TEXT], nullable=False),
        "valid_from": pa.Column(str, checks=[_ISO], nullable=False),
        "valid_to": pa.Column(str, checks=[_ISO], nullable=False),
        "membership_from": pa.Column(str, checks=[_ISO], nullable=False),
        "membership_to": pa.Column(str, checks=[_ISO], nullable=False),
        "membership_source_ids": pa.Column(
            object,
            checks=[pa.Check(_is_sorted_unique_text_tuple, element_wise=True)],
            nullable=False,
        ),
        "ticker_source_ids": pa.Column(
            object,
            checks=[pa.Check(_is_sorted_unique_text_tuple, element_wise=True)],
            nullable=False,
        ),
        "source_event_ids": pa.Column(
            object,
            checks=[pa.Check(_is_sorted_unique_text_tuple, element_wise=True)],
            nullable=False,
        ),
        "provenance_hash": pa.Column(str, checks=[_HASH], nullable=False),
        "resolution_state": pa.Column(
            str,
            checks=[pa.Check.isin(_RESOLUTION_STATES)],
            nullable=False,
        ),
        "schema_version": pa.Column(
            str,
            checks=[pa.Check.equal_to("InstrumentEpisodeV1")],
            nullable=False,
        ),
    },
    checks=[
        pa.Check(lambda frame: frame["valid_from"] <= frame["valid_to"]),
        pa.Check(lambda frame: frame["membership_from"] <= frame["membership_to"]),
    ],
    strict=True,
    unique=["index_id", "normalized_ticker", "valid_from", "valid_to"],
    name="InstrumentEpisodeTable",
)


def validate_fja_source_table(items: Iterable[object]) -> None:
    """Validate generic shape and ordering of a decoded FJA CSV table."""
    records = _records(items)
    frame = (
        pd.DataFrame.from_records(records)
        if records
        else pd.DataFrame(columns=("date", "tickers"), dtype="string")
    )
    try:
        FJA_SOURCE_SCHEMA.validate(frame, lazy=True)
    except (pa.errors.SchemaError, pa.errors.SchemaErrors) as exc:
        raise ValueError("FJA source table failed structural validation") from exc


def validate_snapshot_observation_table(items: Iterable[object]) -> None:
    """Validate the external/tabular structure of snapshot observations."""
    _validate(SNAPSHOT_OBSERVATION_SCHEMA, items, "snapshot observation")


def validate_membership_event_table(items: Iterable[object]) -> None:
    """Validate the external/tabular structure of membership events."""
    _validate(MEMBERSHIP_EVENT_SCHEMA, items, "membership event")


def validate_identity_event_table(items: Iterable[object]) -> None:
    """Validate the external/tabular structure of ticker identity events."""
    _validate(IDENTITY_EVENT_SCHEMA, items, "ticker identity event")


def validate_instrument_episode_table(items: Iterable[object]) -> None:
    """Validate the external/tabular structure of instrument episodes."""
    _validate(INSTRUMENT_EPISODE_SCHEMA, items, "instrument episode")
