"""Canonical encoding and hashing for the PIT universe boundary."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
import hashlib
import json
import re
from typing import Any


SCHEMA_VERSION = "aq-pit-canonical-v1"
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


class CanonicalizationError(ValueError):
    """Raised when a value has no authoritative canonical representation."""


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        raise CanonicalizationError("floats are forbidden in authoritative hashes")
    if isinstance(value, Enum):
        return _normalize(value.value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _normalize(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise CanonicalizationError("canonical object keys must be strings")
        return {key: _normalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    raise CanonicalizationError(f"unsupported canonical type: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """Return strict UTF-8 canonical JSON bytes."""

    return json.dumps(
        _normalize(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _contains_absolute_path(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.lower()
        return (
            value.startswith(("/", "\\"))
            or lowered.startswith("file://")
            or bool(_WINDOWS_ABSOLUTE.match(value))
        )
    if isinstance(value, dict):
        return any(_contains_absolute_path(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_absolute_path(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        return any(_contains_absolute_path(getattr(value, field.name)) for field in fields(value))
    return False


def deterministic_id(prefix: str, logical_identity: Any) -> str:
    """Hash logical identity while rejecting machine-local absolute paths."""

    if not prefix or not prefix.isascii():
        raise CanonicalizationError("ID prefix must be non-empty ASCII")
    if _contains_absolute_path(logical_identity):
        raise CanonicalizationError("absolute paths cannot participate in logical identity")
    return f"{prefix}{sha256_hex(logical_identity)}"
