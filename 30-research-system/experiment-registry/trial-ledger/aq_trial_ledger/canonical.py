"""AQ canonical JSON V1; no serializer defaults define identity."""
from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

RESEARCH_CANONICAL_V1 = "AQ_RESEARCH_SPEC_CANONICAL_V1"
ANCHOR_CANONICAL_V1 = "AQ_LEDGER_ANCHOR_CANONICAL_V1"
EVENT_HASH_DOMAIN_V1 = "AQ_LEDGER_EVENT_HASH_V1"


class CanonicalizationError(ValueError):
    """Raised for an input outside a V1 canonical contract."""


_FORBIDDEN_RESEARCH_FIELDS = {
    "trial_id", "idempotency_key", "request_id", "registered_at",
    "registration_actor", "execution_id", "result", "results",
    "performance", "performance_metrics", "sealed_oos_content",
    "sealed_oos_data", "sealed_oos_payload", "account_data",
    "broker_credentials",
}
_SEMANTIC_TEXT_FIELDS = {"hypothesis_text", "research_objective", "semantic_text"}
_TOP_LEVEL_FIELDS = {
    "generator", "generator_version", "hypothesis_id", "hypothesis_hash",
    "hypothesis_text", "factor_spec_hash", "model_spec_hash",
    "hyperparameter_hash", "dataset_snapshot_id", "universe_id",
    "universe_hash", "label_spec_hash", "feature_set_hash", "train_window",
    "validation_window", "evaluation_window_policy", "exchange_calendar",
    "calendar_version", "portfolio_rule_hash", "cost_assumption_hash",
    "benchmark_policy_hash", "git_commit_sha", "environment_fingerprint",
    "random_seed", "family_policy_inputs_hash", "family_inputs", "parameters",
    "research_objective", "semantic_text", "extensions",
}


def parse_json_strict(text: str) -> Any:
    """Parse JSON while rejecting duplicate object keys and non-finite numbers."""

    def object_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise CanonicalizationError("duplicate JSON object key")
            result[key] = value
        return result

    def reject_constant(_: str) -> None:
        raise CanonicalizationError("non-finite JSON number")

    try:
        return json.loads(text, object_pairs_hook=object_pairs, parse_constant=reject_constant)
    except (TypeError, ValueError, json.JSONDecodeError) as error:
        raise CanonicalizationError(str(error)) from error


def _validate_scalar_string(value: str) -> str:
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise CanonicalizationError("lone UTF-16 surrogate")
    return value


def _canonical_decimal(value: Any) -> str:
    if isinstance(value, bool) or isinstance(value, float):
        raise CanonicalizationError("binary float decimal identity")
    try:
        decimal = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise CanonicalizationError("invalid decimal value") from error
    if not decimal.is_finite():
        raise CanonicalizationError("non-finite decimal value")
    if decimal.is_zero():
        return "0"
    result = format(decimal.normalize(), "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


def _validate_research_spec(spec: Mapping[str, Any]) -> None:
    if not spec:
        raise CanonicalizationError("ResearchSpec cannot be empty")
    if any(not isinstance(key, str) for key in spec):
        raise CanonicalizationError("ResearchSpec keys must be strings")
    unknown = set(spec) - _TOP_LEVEL_FIELDS
    if unknown:
        raise CanonicalizationError(f"undeclared ResearchSpec field: {sorted(unknown)!r}")
    forbidden = set(spec) & _FORBIDDEN_RESEARCH_FIELDS
    if forbidden:
        raise CanonicalizationError(f"forbidden field: {sorted(forbidden)!r}")
    required = {
        "generator", "generator_version", "factor_spec_hash", "model_spec_hash",
        "hyperparameter_hash", "dataset_snapshot_id", "label_spec_hash", "feature_set_hash",
        "train_window", "validation_window", "exchange_calendar", "calendar_version",
        "portfolio_rule_hash", "cost_assumption_hash", "benchmark_policy_hash",
        "git_commit_sha", "environment_fingerprint", "random_seed", "family_policy_inputs_hash",
    }
    missing = required - set(spec)
    if missing:
        raise CanonicalizationError(f"missing ResearchSpec field: {sorted(missing)!r}")
    if not ({"hypothesis_id", "hypothesis_hash", "hypothesis_text"} & set(spec)):
        raise CanonicalizationError("ResearchSpec needs hypothesis identity")
    if not ({"universe_id", "universe_hash"} & set(spec)):
        raise CanonicalizationError("ResearchSpec needs universe identity")

    def visit(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                if not isinstance(key, str):
                    raise CanonicalizationError("ResearchSpec keys must be strings")
                if key in _FORBIDDEN_RESEARCH_FIELDS:
                    raise CanonicalizationError(f"forbidden nested field: {key}")
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(spec)

    parameters = spec.get("parameters")
    if parameters is not None:
        if not isinstance(parameters, Mapping) or any(not isinstance(key, str) for key in parameters):
            raise CanonicalizationError("parameters must be a string-keyed object")
        for name, parameter in parameters.items():
            if not isinstance(parameter, Mapping) or set(parameter) != {"type", "value"}:
                raise CanonicalizationError(f"parameter {name!r} needs exactly type and value")
            if parameter["type"] not in {"decimal", "string"}:
                raise CanonicalizationError(f"parameter {name!r} has unsupported type")
            if parameter["type"] == "string" and not isinstance(parameter["value"], str):
                raise CanonicalizationError(f"string parameter {name!r} needs a string value")


def _normalise(value: Any, path: tuple[str, ...] = ()) -> Any:
    field = path[-1] if path else ""
    dotted = ".".join(path)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise CanonicalizationError("non-string object key")
        if path == ("parameters",):
            return {
                key: {
                    "type": item["type"],
                    "value": _canonical_decimal(item["value"]) if item["type"] == "decimal" else _validate_scalar_string(item["value"]),
                }
                for key, item in value.items()
            }
        return {key: _normalise(item, path + (key,)) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalise(item, path) for item in value]
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise CanonicalizationError("naive datetime")
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        raise CanonicalizationError("native float is not a ResearchSpec identity value")
    if isinstance(value, str):
        value = _validate_scalar_string(value)
        return unicodedata.normalize("NFC", value) if field in _SEMANTIC_TEXT_FIELDS else value
    return value


def canonical_json_bytes(value: Any) -> bytes:
    """Emit fixed V1 JSON: direct UTF-8, lower-case control escapes, no newline."""

    def quote(text: str) -> str:
        text = _validate_scalar_string(text)
        escaped: list[str] = ['"']
        for character in text:
            codepoint = ord(character)
            if character == '"':
                escaped.append('\\"')
            elif character == "\\":
                escaped.append("\\\\")
            elif codepoint <= 0x1F:
                escaped.append(f"\\u{codepoint:04x}")
            else:
                escaped.append(character)
        escaped.append('"')
        return "".join(escaped)

    def encode(item: Any) -> str:
        if item is None:
            return "null"
        if item is True:
            return "true"
        if item is False:
            return "false"
        if isinstance(item, str):
            return quote(item)
        if isinstance(item, int) and not isinstance(item, bool):
            return str(item)
        if isinstance(item, list) or isinstance(item, tuple):
            return "[" + ",".join(encode(element) for element in item) + "]"
        if isinstance(item, Mapping):
            if any(not isinstance(key, str) for key in item):
                raise CanonicalizationError("non-string object key")
            return "{" + ",".join(
                quote(key) + ":" + encode(item[key]) for key in sorted(item)
            ) + "}"
        raise CanonicalizationError(f"unsupported canonical JSON type: {type(item).__name__}")

    return encode(value).encode("utf-8")


def canonicalize_research_spec(
    spec: Mapping[str, Any], *, version: str = RESEARCH_CANONICAL_V1,
) -> bytes:
    if version != RESEARCH_CANONICAL_V1:
        raise CanonicalizationError("unknown canonicalization version")
    if not isinstance(spec, Mapping):
        raise CanonicalizationError("ResearchSpec must be an object")
    _validate_research_spec(spec)
    return canonical_json_bytes({
        "canonicalization_version": version,
        "research_spec": _normalise(spec),
    })


def hash_research_spec(spec: Mapping[str, Any]) -> tuple[bytes, str]:
    canonical = canonicalize_research_spec(spec)
    return canonical, hashlib.sha256(canonical).hexdigest()


def canonicalize_anchor_payload(payload: Mapping[str, Any]) -> bytes:
    if payload.get("canonicalization_version", ANCHOR_CANONICAL_V1) != ANCHOR_CANONICAL_V1:
        raise CanonicalizationError("unknown anchor canonicalization version")
    return canonical_json_bytes({
        "canonicalization_version": ANCHOR_CANONICAL_V1,
        "payload": _normalise(payload),
    })


def event_hash(event_envelope: Mapping[str, Any]) -> str:
    if event_envelope.get("hash_domain_version") != EVENT_HASH_DOMAIN_V1:
        raise CanonicalizationError("unknown event hash domain")
    return hashlib.sha256(canonical_json_bytes(event_envelope)).hexdigest()
