"""Trusted control-side LiteLLM native user/key operations for one run."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from native_experiment_budget import (
    LiteLLMNativeAPI,
    NativeExperimentBudgetController,
    OWNER_ONESHOT_MODELS,
    P12ExperimentIdentity,
)


EVIDENCE_VERSION = "P12_LITELLM_CALL_EVIDENCE_V1"
LITELLM_IMAGE = "ghcr.io/berriai/litellm@sha256:b7b9e2c306343721802253d0dd9436b9634a2eb4e14da7c7cf06c5c7b7530802"
PROXY_CONFIG_PATH = Path("/app/config.deepseek-staging.yaml")
MAX_SPEND_LOG_PAGES = 4
MAX_SETTLEMENT_POLLS = 4
SPEND_LOG_PAGE_SIZE = 100


def _native_key_hash(token: str) -> str:
    # Use the pinned LiteLLM implementation. Never expose or persist this value.
    from litellm.proxy.utils import hash_token

    value = hash_token(token)
    if not isinstance(value, str) or not value:
        raise ValueError("native key identity unavailable")
    return value


def _decimal(value: Any) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite() or result < 0:
        raise ValueError("invalid native spend value")
    return result


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            return {}
    return value if isinstance(value, dict) else {}


def _row_time(row: dict[str, Any]) -> str | None:
    value = row.get("startTime", row.get("start_time"))
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return None
            return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            return None
    return None


def _safe_row(row: dict[str, Any], *, expected_user: str, expected_key_hash: str,
              started_at: datetime, ended_at: datetime) -> dict[str, Any]:
    # User and key columns are native SpendLog ownership fields. Metadata is
    # client-controlled and is never used to establish row ownership.
    if row.get("user") != expected_user or row.get("api_key") != expected_key_hash:
        raise ValueError("spend log ownership mismatch")
    row_id = row.get("request_id")
    call_id = row.get("litellm_call_id")
    if not isinstance(row_id, str) or not row_id or not isinstance(call_id, str) or not call_id:
        raise ValueError("native call identity missing")
    timestamp = _row_time(row)
    if timestamp is None:
        raise ValueError("native call time missing")
    parsed_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed_time < started_at or parsed_time > ended_at:
        raise ValueError("native call outside attempt window")
    status = row.get("status")
    if not isinstance(status, str) or status.lower() not in {"success", "failure", "failed", "error"}:
        raise ValueError("native call status missing")
    route = row.get("model_group")
    if not isinstance(route, str) or not route:
        raise ValueError("native route identity missing")
    meta = _metadata(row)
    for metadata_key, expected in (
        ("user_api_key_user_id", expected_user),
        ("user_api_key_hash", expected_key_hash),
    ):
        if meta.get(metadata_key) is not None and meta.get(metadata_key) != expected:
            raise ValueError("client metadata ownership conflicts with native SpendLog")
    fallback = meta.get("attempted_fallbacks")
    retries = meta.get("attempted_retries")
    fallback_state = fallback if type(fallback) is int and fallback >= 0 else "UNKNOWN"
    retry_state = retries if type(retries) is int and retries >= 0 else "UNKNOWN"
    original = meta.get("original_model_group")
    if fallback_state == 0 and original is not None and original != route:
        raise ValueError("native original route conflicts with route")
    token_values = {}
    for output, keys in {
        "prompt_tokens": ("prompt_tokens", "promptTokens"),
        "completion_tokens": ("completion_tokens", "completionTokens"),
        "total_tokens": ("total_tokens", "totalTokens"),
    }.items():
        value = next((row[key] for key in keys if key in row), None)
        token_values[output] = value if type(value) is int and value >= 0 else None
    amount = _decimal(row.get("spend", 0))
    return {
        "spend_log_request_id": row_id,
        "litellm_call_id": call_id,
        "call_type": row.get("call_type") if isinstance(row.get("call_type"), str) else "UNKNOWN",
        "status": status.lower(),
        "observed_at_utc": timestamp,
        "routed_model_group": route,
        "proxy_model_field": row.get("model") if isinstance(row.get("model"), str) else None,
        **token_values,
        "spend_usd": format(amount, "f"),
        "attempted_fallbacks": fallback_state,
        "original_model_group": original if isinstance(original, str) else None,
        "attempted_retries": retry_state,
        "provider_model_identity_kind": "UNAVAILABLE",
        "missing_fields": [
            name for name, value in (
                ("attempted_fallbacks", fallback_state), ("attempted_retries", retry_state),
                ("token_usage", [token_values[key] for key in token_values]),
                ("call_type", row.get("call_type")),
                ("original_model_group", original if fallback_state not in (0, "UNKNOWN") else "observed-or-not-required"),
            ) if value == "UNKNOWN" or value is None or (name == "token_usage" and any(v is None for v in value))
        ],
    }


def _spend_snapshot(api: LiteLLMNativeAPI, *, user_id: str, key_hash: str,
                    started_at: datetime, ended_at: datetime) -> tuple[list[dict[str, Any]], Decimal]:
    start = started_at.isoformat().replace("+00:00", "Z")
    end = ended_at.isoformat().replace("+00:00", "Z")
    rows: list[dict[str, Any]] = []
    page = 1
    declared_pages = None
    declared_total = None
    while page <= MAX_SPEND_LOG_PAGES:
        result = api.spend_logs_v2(
            user_id=user_id, api_key_hash=key_hash, start_date=start, end_date=end,
            page=page, page_size=SPEND_LOG_PAGE_SIZE,
        )
        data = result.get("data")
        if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
            raise ValueError("native spend log page malformed")
        if result.get("total_pages") == 0 and data:
            raise ValueError("native spend log page count conflicts with data")
        if result.get("total_is_capped") is True:
            raise ValueError("native spend log total capped")
        total_pages = result.get("total_pages")
        total = result.get("total")
        if total_pages is not None and (type(total_pages) is not int or total_pages < 0):
            raise ValueError("native spend log page count malformed")
        if total is not None and (type(total) is not int or total < 0):
            raise ValueError("native spend log total malformed")
        if declared_pages is None:
            declared_pages, declared_total = total_pages, total
        elif (total_pages, total) != (declared_pages, declared_total):
            raise ValueError("native spend log pagination changed")
        rows.extend(data)
        if total_pages is not None:
            if total_pages > MAX_SPEND_LOG_PAGES:
                raise ValueError("native spend log page bound exceeded")
            if page >= total_pages:
                break
        elif len(data) < SPEND_LOG_PAGE_SIZE:
            break
        page += 1
    else:
        raise ValueError("native spend log page bound exceeded")
    if declared_total is not None and declared_total != len(rows):
        raise ValueError("native spend log total mismatch")
    safe_rows = [
        _safe_row(row, expected_user=user_id, expected_key_hash=key_hash,
                  started_at=started_at, ended_at=ended_at)
        for row in rows
    ]
    request_ids = [row["spend_log_request_id"] for row in safe_rows]
    call_ids = [row["litellm_call_id"] for row in safe_rows]
    if len(set(request_ids)) != len(request_ids) or len(set(call_ids)) != len(call_ids):
        raise ValueError("duplicate native call identity")
    safe_rows.sort(key=lambda row: (row["observed_at_utc"], row["spend_log_request_id"]))
    total_spend = sum((_decimal(row["spend_usd"]) for row in safe_rows), Decimal("0"))
    return safe_rows, total_spend


def collect_call_evidence(api: LiteLLMNativeAPI, *, token: str, request_id: str,
                          attempt_id: str, research_budget_identity: str,
                          attempt_started_at_utc: str, now=None, sleep=None) -> dict[str, Any]:
    """Return a redacted native evidence record; uncertain fields stay partial."""
    from native_experiment_budget import experiment_user_id

    now = now or (lambda: datetime.now(timezone.utc))
    sleep = sleep or time.sleep
    if hasattr(api, "timeout"):
        api.timeout = min(api.timeout, 2.5)
    missing: list[str] = []
    calls: list[dict[str, Any]] = []
    try:
        started_at = datetime.fromisoformat(attempt_started_at_utc.replace("Z", "+00:00"))
        if started_at.tzinfo is None:
            raise ValueError("attempt start must be timezone aware")
        started_at = started_at.astimezone(timezone.utc)
        expected_user = experiment_user_id(research_budget_identity)
        expected_alias = "aq-p12-owner-once-" + hashlib.sha256((request_id + ":key").encode("ascii")).hexdigest()[:20]
        key_info = api.key_info(token)
        user_info = api.user_info(expected_user)
        if (key_info.get("user_id") != expected_user or key_info.get("key_alias") != expected_alias
                or key_info.get("blocked") is not True or not isinstance(user_info, dict)
                or user_info.get("user_id") != expected_user
                or key_info.get("models") != list(OWNER_ONESHOT_MODELS)):
            raise ValueError("native key scope or blocked state mismatch")
        key_hash = _native_key_hash(token)
        fingerprint = hashlib.sha256(b"AQ:P12:LITELLM_KEY_FINGERPRINT:V1\0" + key_hash.encode("utf-8")).hexdigest()
        last_signature = None
        stable_count = 0
        final_spend = None
        final_log_spend = None
        settled_at = None
        for poll in range(MAX_SETTLEMENT_POLLS):
            ended_at = now().astimezone(timezone.utc)
            calls, log_spend = _spend_snapshot(
                api, user_id=expected_user, key_hash=key_hash,
                started_at=started_at, ended_at=ended_at,
            )
            key_info = api.key_info(token)
            if (key_info.get("blocked") is not True or key_info.get("user_id") != expected_user
                    or key_info.get("key_alias") != expected_alias
                    or key_info.get("models") != list(OWNER_ONESHOT_MODELS)):
                raise ValueError("native key block or ownership changed")
            key_spend = _decimal(key_info.get("spend", 0))
            signature = json.dumps({"calls": calls, "log_spend": format(log_spend, "f"),
                                   "key_spend": format(key_spend, "f")}, sort_keys=True, separators=(",", ":"))
            if signature == last_signature:
                stable_count += 1
            else:
                stable_count = 1
            last_signature = signature
            final_spend = key_spend
            final_log_spend = log_spend
            settled_at = ended_at
            if stable_count >= 2 and abs(log_spend - key_spend) <= Decimal("0.00000001"):
                break
            if poll + 1 < MAX_SETTLEMENT_POLLS:
                sleep(1)
        else:
            missing.append("spend_logs_not_settled_or_totals_mismatch")
        if any(call["attempted_fallbacks"] == "UNKNOWN" for call in calls):
            missing.append("attempted_fallbacks_missing_from_native_spendlog")
        if any(call["attempted_retries"] == "UNKNOWN" for call in calls):
            missing.append("attempted_retries_missing_from_native_spendlog")
        if not calls:
            # An empty ledger cannot distinguish a true no-call run from an
            # asynchronously delayed zero-cost SpendLog row.
            missing.append("no_native_call_rows_to_seal")
        if any(call["call_type"] == "UNKNOWN" for call in calls):
            missing.append("call_type_missing_from_native_spendlog")
        if any(call["attempted_fallbacks"] not in (0, "UNKNOWN") and call["original_model_group"] is None for call in calls):
            missing.append("original_model_group_missing_for_fallback")
        if any(call[field] is None for call in calls for field in ("prompt_tokens", "completion_tokens", "total_tokens")):
            missing.append("token_usage_missing_from_native_spendlog")
        status = "COMPLETE" if not missing else "PARTIAL"
        return {
            "format_version": EVIDENCE_VERSION,
            "request_id": request_id,
            "attempt_id": attempt_id,
            "native_experiment_user_id": expected_user,
            "scoped_key_identity": "sha256:" + fingerprint,
            "attempt_window_started_at_utc": started_at.isoformat().replace("+00:00", "Z"),
            "spend_log_settled_at_utc": None if settled_at is None else settled_at.isoformat().replace("+00:00", "Z"),
            "configured_allowed_models": list(OWNER_ONESHOT_MODELS),
            "litellm_proxy_version": "1.105.1",
            "litellm_proxy_image": LITELLM_IMAGE,
            "proxy_config_sha256": hashlib.sha256(PROXY_CONFIG_PATH.read_bytes()).hexdigest(),
            "calls": calls,
            "call_count": len(calls),
            "total_spend_usd": None if final_spend is None else format(final_spend, "f"),
            "spend_logs_total_usd": None if final_log_spend is None else format(final_log_spend, "f"),
            "provider_model_identity_kind": "UNAVAILABLE",
            "missing_fields": sorted(set(missing)),
            "evidence_status": status,
        }
    except Exception as exc:
        # Never persist raw exception text or API payloads.
        return {
            "format_version": EVIDENCE_VERSION,
            "request_id": request_id,
            "attempt_id": attempt_id,
            "native_experiment_user_id": None,
            "scoped_key_identity": None,
            "attempt_window_started_at_utc": attempt_started_at_utc,
            "spend_log_settled_at_utc": None,
            "configured_allowed_models": None,
            "litellm_proxy_version": "1.105.1",
            "litellm_proxy_image": LITELLM_IMAGE,
            "proxy_config_sha256": None,
            "calls": [],
            "call_count": None,
            "total_spend_usd": None,
            "spend_logs_total_usd": None,
            "provider_model_identity_kind": "UNAVAILABLE",
            "missing_fields": ["native_evidence_unavailable", type(exc).__name__],
            "evidence_status": "PARTIAL",
        }


def main() -> int:
    try:
        request = json.load(sys.stdin)
        if not isinstance(request, dict):
            raise ValueError("control request must be an object")
        admin_key = os.environ.get("LITELLM_DEEPSEEK_STAGING_MASTER_KEY", "")
        api = LiteLLMNativeAPI("http://127.0.0.1:4000", admin_key)
        if request.get("operation") == "prepare":
            identity = P12ExperimentIdentity(
                research_budget_identity=request["research_budget_identity"],
                request_id=request["request_id"],
                standing_policy_id=request["standing_policy_id"],
            )
            token, user, key = NativeExperimentBudgetController(api).prepare_owner_oneshot(
                identity,
                owner_activation_confirmed=request.get("owner_activation_confirmed") is True,
            )
            print(json.dumps({
                "classification": "OWNER_ONESHOT_NATIVE_KEY_READY",
                "token": token,
                "user_id": identity.user_id,
                "user_alias": user["user_alias"],
                "user_budget_usd": float(user["max_budget"]),
                "user_spend_usd": float(user.get("spend", 0)),
                "models": key["models"],
                "key_alias": key["key_alias"],
                "key_budget_usd": float(key["max_budget"]),
                "budget_duration": key.get("budget_duration"),
                "expires": key["expires"],
                "max_parallel_requests": key["max_parallel_requests"],
            }, sort_keys=True))
            return 0
        if request.get("operation") == "block":
            token = request.get("token")
            if not isinstance(token, str) or not token.startswith("sk-"):
                raise ValueError("scoped key required")
            status, payload = api.request("POST", "/key/block", {"key": token})
            if status not in (200, 201) or payload.get("blocked") is not True:
                raise RuntimeError("native key block was not confirmed")
            info = api.key_info(token)
            if info.get("blocked") is not True:
                raise RuntimeError("native key blocked state did not persist")
            response = {
                "classification": "OWNER_ONESHOT_KEY_BLOCKED",
                "blocked": True,
                "spend": float(info.get("spend", 0)),
                "models": info.get("models"),
            }
            if all(isinstance(request.get(name), str) for name in (
                "request_id", "attempt_id", "research_budget_identity", "attempt_started_at_utc"
            )):
                if not re.fullmatch(r"sha256:[0-9a-f]{64}", request["request_id"]):
                    raise ValueError("invalid P12 request identity")
                if not re.fullmatch(r"[0-9a-f-]{36}", request["attempt_id"]):
                    raise ValueError("invalid P12 attempt identity")
                response["call_evidence"] = collect_call_evidence(
                    api, token=token, request_id=request["request_id"], attempt_id=request["attempt_id"],
                    research_budget_identity=request["research_budget_identity"],
                    attempt_started_at_utc=request["attempt_started_at_utc"],
                )
            print(json.dumps(response, sort_keys=True))
            return 0
        raise ValueError("unsupported control operation")
    except Exception as exc:
        print(json.dumps({
            "classification": "DENIED_OWNER_ONESHOT_PROXY_CONTROL",
            "error_type": type(exc).__name__,
        }, sort_keys=True), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
