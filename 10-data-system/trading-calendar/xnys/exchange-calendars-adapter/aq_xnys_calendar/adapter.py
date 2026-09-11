"""Pinned, deterministic XNYS session semantics.

The public boundary accepts and returns only ISO ``YYYY-MM-DD`` strings.
Pandas and exchange_calendars objects never cross this module boundary.
"""

from __future__ import annotations

from datetime import date
import re
from typing import Literal

import exchange_calendars as xcals


Direction = Literal["next", "previous", "none"]

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CALENDAR_START = "2000-01-01"
_CALENDAR_END = "2035-12-31"


def _validated_iso(value: str, name: str) -> str:
    if not isinstance(value, str) or not _ISO_DATE.fullmatch(value):
        raise ValueError(f"{name} must be an ISO YYYY-MM-DD date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an ISO YYYY-MM-DD date") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{name} must be an ISO YYYY-MM-DD date")
    return value


def _calendar():
    # Explicit bounds prevent exchange_calendars' default construction window
    # from depending on the wall clock. No calendar object is exposed or mutated.
    return xcals.get_calendar(
        "XNYS",
        start=_CALENDAR_START,
        end=_CALENDAR_END,
    )


def _as_iso(session) -> str:
    return session.strftime("%Y-%m-%d")


def is_session(value: str) -> bool:
    """Return whether *value* is an XNYS session within the pinned range."""
    session_date = _validated_iso(value, "date")
    try:
        return bool(_calendar().is_session(session_date))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"date is outside supported XNYS range: {value}") from exc


def date_to_session(value: str, direction: Direction = "none") -> str:
    """Resolve a date to an XNYS session under an explicit direction policy."""
    session_date = _validated_iso(value, "date")
    if direction not in ("next", "previous", "none"):
        raise ValueError("direction must be next, previous, or none")
    try:
        return _as_iso(_calendar().date_to_session(session_date, direction=direction))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"date cannot resolve to an XNYS session with direction={direction}: {value}"
        ) from exc


def previous_session(value: str) -> str:
    """Return the XNYS session immediately before a valid session."""
    session_date = date_to_session(value, direction="none")
    try:
        return _as_iso(_calendar().previous_session(session_date))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"no previous XNYS session is available for: {value}") from exc


def next_session(value: str) -> str:
    """Return the XNYS session immediately after a valid session."""
    session_date = date_to_session(value, direction="none")
    try:
        return _as_iso(_calendar().next_session(session_date))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"no next XNYS session is available for: {value}") from exc


def sessions_in_range(start_session: str, end_session: str) -> tuple[str, ...]:
    """Return the inclusive XNYS session range between two valid sessions."""
    start = date_to_session(start_session, direction="none")
    end = date_to_session(end_session, direction="none")
    if start > end:
        raise ValueError("start_session must not be after end_session")
    try:
        return tuple(_as_iso(item) for item in _calendar().sessions_in_range(start, end))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid XNYS session range: {start} to {end}") from exc
