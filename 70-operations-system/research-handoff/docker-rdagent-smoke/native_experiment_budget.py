"""P12 control-side binding to LiteLLM's native persistent user budget.

This module is not a billing engine. It uses LiteLLM's user/key APIs and
deliberately exposes only a synthetic TEST_ONLY creation path. Real issuance
fails closed until an independently trusted owner-approval source exists.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


USER_ID_DOMAIN = b"AUTONOMOUS_QUANT:P12:LITELLM_EXPERIMENT_BUDGET:V1\0"
ALLOWED_MODELS = ("deepseek-chat", "qwen3-embedding:0.6b")
OWNER_ONESHOT_MODELS = ("deepseek/deepseek-flash", "ollama/qwen3-embedding:0.6b")
MAX_EXPERIMENT_BUDGET_USD = 5.00
MAX_KEY_DURATION = timedelta(hours=24)
MAX_PARALLEL_REQUESTS = 1
TEST_ONLY_MAX_BUDGET_USD = 0.001
_IDENTITY_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_DURATION_RE = re.compile(r"^([1-9][0-9]*)(s|m|h|d)$")


class BudgetBoundaryDenied(RuntimeError):
    def __init__(self, classification: str):
        super().__init__(classification)
        self.classification = classification


@dataclass(frozen=True)
class P12ExperimentIdentity:
    research_budget_identity: str
    request_id: str
    standing_policy_id: str

    def __post_init__(self) -> None:
        _identity(self.research_budget_identity)
        _identity(self.request_id)
        _identity(self.standing_policy_id)

    @classmethod
    def from_p12(cls, request: Any, policy: Any) -> "P12ExperimentIdentity":
        request_value = _as_mapping(request)
        policy_value = _as_mapping(policy)
        budget_identity = request_value.get("research_budget_identity")
        if budget_identity != policy_value.get("research_budget_identity"):
            raise BudgetBoundaryDenied("DENIED_EXPERIMENT_IDENTITY_MISMATCH")
        return cls(
            research_budget_identity=_identity(budget_identity),
            request_id=_identity(request_value.get("request_id")),
            standing_policy_id=_identity(policy_value.get("policy_id")),
        )

    @property
    def user_id(self) -> str:
        return experiment_user_id(self.research_budget_identity)


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        result = value.model_dump(mode="json")
        if isinstance(result, dict):
            return result
    raise BudgetBoundaryDenied("DENIED_P12_IDENTITY_MALFORMED")


def _identity(value: Any) -> str:
    if not isinstance(value, str) or not _IDENTITY_RE.fullmatch(value):
        raise BudgetBoundaryDenied("DENIED_P12_IDENTITY_MALFORMED")
    return value


def experiment_user_id(research_budget_identity: str) -> str:
    identity = _identity(research_budget_identity)
    digest = hashlib.sha256(USER_ID_DOMAIN + identity.encode("ascii")).hexdigest()
    return f"aq-p12-exp-{digest}"


def _finite_positive(value: Any, classification: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        raise BudgetBoundaryDenied(classification) from None
    if not math.isfinite(result) or result <= 0:
        raise BudgetBoundaryDenied(classification)
    return result


def _duration_seconds(value: str) -> int:
    match = _DURATION_RE.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise BudgetBoundaryDenied("DENIED_KEY_DURATION_INVALID")
    amount = int(match.group(1))
    seconds = amount * {"s": 1, "m": 60, "h": 3600, "d": 86400}[match.group(2)]
    if seconds > MAX_KEY_DURATION.total_seconds():
        raise BudgetBoundaryDenied("DENIED_KEY_DURATION_EXCEEDS_24H")
    return seconds


class LiteLLMNativeAPI:
    """Narrow wrapper around official LiteLLM user and key endpoints."""

    def __init__(self, base_url: str, admin_key: str, *, timeout: float = 20):
        if not base_url.startswith("http://127.0.0.1:"):
            raise ValueError("control API must use the local LiteLLM endpoint")
        if not isinstance(admin_key, str) or not admin_key.startswith("sk-"):
            raise ValueError("LiteLLM control credential required")
        self.base_url = base_url.rstrip("/")
        self._admin_key = admin_key
        self.timeout = timeout

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        headers = {"Authorization": f"Bearer {self._admin_key}", "Content-Type": "application/json"}
        encoded = None if body is None else json.dumps(body, separators=(",", ":")).encode()
        request = urllib.request.Request(self.base_url + path, data=encoded, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
                value = json.loads(payload) if payload else {}
                return response.status, value if isinstance(value, dict) else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            try:
                value = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                value = {}
            return exc.code, value if isinstance(value, dict) else {}

    def user_info(self, user_id: str) -> dict[str, Any] | None:
        query = urllib.parse.urlencode({"user_id": user_id})
        status, payload = self.request("GET", f"/user/info?{query}")
        if status == 404:
            return None
        if status != 200:
            raise BudgetBoundaryDenied("DENIED_NATIVE_USER_LOOKUP_FAILED")
        info = payload.get("user_info")
        if not isinstance(info, dict):
            raise BudgetBoundaryDenied("DENIED_NATIVE_USER_RECORD_INVALID")
        info = dict(info)
        info.setdefault("user_id", payload.get("user_id"))
        return info

    def key_info(self, token: str) -> dict[str, Any]:
        query = urllib.parse.urlencode({"key": token})
        status, payload = self.request("GET", f"/key/info?{query}")
        if status != 200:
            raise BudgetBoundaryDenied("DENIED_NATIVE_KEY_LOOKUP_FAILED")
        info = payload.get("info", payload)
        if not isinstance(info, dict):
            raise BudgetBoundaryDenied("DENIED_NATIVE_KEY_RECORD_INVALID")
        return info

    def spend_logs_v2(
        self, *, user_id: str, api_key_hash: str, start_date: str, end_date: str,
        page: int, page_size: int = 100,
    ) -> dict[str, Any]:
        """Read one bounded page from LiteLLM's native SpendLogs endpoint."""
        if (
            not user_id or not api_key_hash or type(page) is not int or page < 1
            or type(page_size) is not int or not 1 <= page_size <= 1000
            or not start_date or not end_date
        ):
            raise BudgetBoundaryDenied("DENIED_NATIVE_SPEND_LOG_QUERY_INVALID")
        query = urllib.parse.urlencode({
            "user_id": user_id,
            "api_key": api_key_hash,
            "start_date": start_date,
            "end_date": end_date,
            "page": page,
            "page_size": page_size,
        })
        status, payload = self.request("GET", f"/spend/logs/v2?{query}")
        if status != 200:
            raise BudgetBoundaryDenied("DENIED_NATIVE_SPEND_LOG_LOOKUP_FAILED")
        return payload


class NativeExperimentBudgetController:
    def __init__(self, api: LiteLLMNativeAPI):
        self.api = api

    def _verify_user(
        self,
        identity: P12ExperimentIdentity,
        user: dict[str, Any] | None,
        expected_budget: float,
    ) -> dict[str, Any]:
        if not isinstance(user, dict):
            raise BudgetBoundaryDenied("DENIED_NATIVE_USER_BUDGET_MISSING")
        try:
            observed_budget = float(user.get("max_budget"))
            spend = float(user.get("spend", 0.0))
        except (TypeError, ValueError, OverflowError):
            raise BudgetBoundaryDenied("DENIED_NATIVE_USER_BUDGET_INVALID") from None
        if (
            user.get("user_id") != identity.user_id
            or not math.isfinite(observed_budget)
            or not math.isclose(observed_budget, expected_budget, rel_tol=0, abs_tol=1e-12)
            or user.get("budget_duration") is not None
            or user.get("models") != list(ALLOWED_MODELS)
            or user.get("max_parallel_requests") != MAX_PARALLEL_REQUESTS
            or not math.isfinite(spend)
            or spend < 0
            or spend > observed_budget + 1e-9
        ):
            raise BudgetBoundaryDenied("DENIED_NATIVE_USER_BUDGET_MISMATCH")
        return user

    def ensure_test_user(
        self,
        identity: P12ExperimentIdentity,
        *,
        budget_usd: float,
        synthetic_fixture_verified: bool,
        p12_replay: bool,
    ) -> dict[str, Any]:
        budget = _finite_positive(budget_usd, "DENIED_TEST_BUDGET_INVALID")
        if budget > TEST_ONLY_MAX_BUDGET_USD or not synthetic_fixture_verified:
            raise BudgetBoundaryDenied("DENIED_TEST_ONLY_SCOPE_INVALID")
        existing = self.api.user_info(identity.user_id)
        if existing is not None:
            return self._verify_user(identity, existing, budget)
        if p12_replay:
            raise BudgetBoundaryDenied("DENIED_NATIVE_USER_BUDGET_MISSING_ON_REPLAY")
        status, payload = self.api.request(
            "POST",
            "/user/new",
            {
                "user_id": identity.user_id,
                "user_alias": "p12-test-only-experiment",
                "max_budget": budget,
                "budget_duration": None,
                "models": list(ALLOWED_MODELS),
                "max_parallel_requests": MAX_PARALLEL_REQUESTS,
                "auto_create_key": False,
            },
        )
        if status not in (200, 201):
            # Never retry creation on a duplicate or an ambiguous response.
            raise BudgetBoundaryDenied("DENIED_NATIVE_USER_CREATE_FAILED")
        if payload.get("user_id") != identity.user_id:
            raise BudgetBoundaryDenied("DENIED_NATIVE_USER_ID_MISMATCH")
        return self._verify_user(identity, self.api.user_info(identity.user_id), budget)

    def issue_test_key(
        self,
        identity: P12ExperimentIdentity,
        *,
        key_alias: str,
        budget_usd: float,
        user_budget_usd: float,
        duration: str = "24h",
        synthetic_fixture_verified: bool,
        p12_replay: bool,
    ) -> str:
        budget = _finite_positive(budget_usd, "DENIED_TEST_KEY_BUDGET_INVALID")
        user_budget = _finite_positive(user_budget_usd, "DENIED_TEST_BUDGET_INVALID")
        if (
            budget > TEST_ONLY_MAX_BUDGET_USD
            or user_budget > TEST_ONLY_MAX_BUDGET_USD
            or not synthetic_fixture_verified
        ):
            raise BudgetBoundaryDenied("DENIED_TEST_ONLY_SCOPE_INVALID")
        if p12_replay:
            raise BudgetBoundaryDenied("DENIED_KEY_ISSUANCE_ON_P12_REPLAY")
        _duration_seconds(duration)
        if not isinstance(key_alias, str) or not key_alias.startswith("aq-p12-exp-test-") or len(key_alias) > 64:
            raise BudgetBoundaryDenied("DENIED_TEST_KEY_ALIAS_INVALID")
        user = self._verify_user(identity, self.api.user_info(identity.user_id), user_budget)
        if budget > float(user["max_budget"]):
            raise BudgetBoundaryDenied("DENIED_KEY_BUDGET_EXCEEDS_USER_BUDGET")
        status, payload = self.api.request(
            "POST",
            "/key/generate",
            {
                "key_alias": key_alias,
                "user_id": identity.user_id,
                "models": list(ALLOWED_MODELS),
                "max_budget": budget,
                "budget_duration": None,
                "duration": duration,
                "max_parallel_requests": MAX_PARALLEL_REQUESTS,
            },
        )
        if status not in (200, 201):
            raise BudgetBoundaryDenied("DENIED_NATIVE_KEY_CREATE_FAILED")
        token = payload.get("key") or payload.get("token")
        if not isinstance(token, str) or not token.startswith("sk-"):
            raise BudgetBoundaryDenied("DENIED_NATIVE_KEY_RESPONSE_INVALID")
        info = self.api.key_info(token)
        try:
            key_budget = float(info.get("max_budget"))
        except (TypeError, ValueError, OverflowError):
            key_budget = math.nan
        expiry_value = info.get("expires")
        try:
            if isinstance(expiry_value, (int, float)):
                expiry = datetime.fromtimestamp(float(expiry_value), tz=timezone.utc)
            elif isinstance(expiry_value, str):
                expiry = datetime.fromisoformat(expiry_value.replace("Z", "+00:00"))
                if expiry.tzinfo is None or expiry.utcoffset() is None:
                    raise ValueError("timezone required")
                expiry = expiry.astimezone(timezone.utc)
            else:
                raise ValueError("expiry required")
        except (ValueError, TypeError, OverflowError, OSError):
            expiry = None
        now = datetime.now(timezone.utc)
        max_expiry = now + timedelta(seconds=_duration_seconds(duration) + 120)
        if (
            info.get("user_id") != identity.user_id
            or info.get("models") != list(ALLOWED_MODELS)
            or info.get("budget_duration") is not None
            or info.get("max_parallel_requests") != MAX_PARALLEL_REQUESTS
            or expiry is None
            or expiry <= now
            or expiry > max_expiry
            or not math.isfinite(key_budget)
            or key_budget > user_budget
            or key_budget > budget + 1e-12
        ):
            self.api.request("POST", "/key/block", {"key": token})
            raise BudgetBoundaryDenied("DENIED_NATIVE_KEY_SCOPE_MISMATCH")
        return token

    def verify_real_issuance_authority(self, owner_authorization: Any) -> None:
        # The installed P12 verifier and policy evidence are TEST_ONLY, and no
        # independent owner-controlled approval/revocation source is present.
        # Do not accept caller-provided booleans or local signed snapshots here.
        del owner_authorization
        raise BudgetBoundaryDenied("DENIED_OWNER_AUTHORIZATION_UNVERIFIED")

    def issue_real_key(self, *args: Any, owner_authorization: Any = None, **kwargs: Any) -> None:
        self.verify_real_issuance_authority(owner_authorization)

    def prepare_owner_oneshot(
        self,
        identity: P12ExperimentIdentity,
        *,
        owner_activation_confirmed: bool,
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """Create and verify the single owner-initiated run's native user/key.

        This deliberately narrow local-host exception is called only by the
        interactive P12 one-shot command after it obtains terminal input. It
        does not change the existing TEST_ONLY issuance path or accept AWS
        snapshots, API booleans, or worker-side authorization.
        """
        if owner_activation_confirmed is not True:
            raise BudgetBoundaryDenied("DENIED_INTERACTIVE_OWNER_ACTIVATION_REQUIRED")

        budget = MAX_EXPERIMENT_BUDGET_USD
        user_alias = "aq-p12-owner-once-" + hashlib.sha256(
            identity.request_id.encode("ascii")
        ).hexdigest()[:20]
        user = self.api.user_info(identity.user_id)
        if user is None:
            status, payload = self.api.request(
                "POST",
                "/user/new",
                {
                    "user_id": identity.user_id,
                    "user_alias": user_alias,
                    "max_budget": budget,
                    "budget_duration": None,
                    "models": list(OWNER_ONESHOT_MODELS),
                    "max_parallel_requests": MAX_PARALLEL_REQUESTS,
                    "auto_create_key": False,
                },
            )
            if status not in (200, 201) or payload.get("user_id") != identity.user_id:
                raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_USER_CREATE_FAILED")
            user = self.api.user_info(identity.user_id)
        user = self._verify_owner_user(identity, user, user_alias)

        self._assert_no_owner_oneshot_keys(identity)

        key_alias = "aq-p12-owner-once-" + hashlib.sha256(
            (identity.request_id + ":key").encode("ascii")
        ).hexdigest()[:20]
        status, payload = self.api.request(
            "POST",
            "/key/generate",
            {
                "key_alias": key_alias,
                "user_id": identity.user_id,
                "models": list(OWNER_ONESHOT_MODELS),
                "max_budget": budget,
                "budget_duration": None,
                "duration": "24h",
                "max_parallel_requests": MAX_PARALLEL_REQUESTS,
            },
        )
        token = payload.get("key") or payload.get("token")
        if status not in (200, 201) or not isinstance(token, str) or not token.startswith("sk-"):
            raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_KEY_CREATE_FAILED")
        try:
            key = self.api.key_info(token)
            self._verify_owner_key(identity, key, key_alias, budget)
        except Exception as exc:
            # Do not leave an unverified one-shot credential active. If native
            # revocation cannot be confirmed, surface that as the failure.
            blocked_status, blocked_payload = self.api.request("POST", "/key/block", {"key": token})
            if blocked_status not in (200, 201) or blocked_payload.get("blocked") is not True:
                raise BudgetBoundaryDenied("DENIED_OWNER_UNVERIFIED_KEY_BLOCK_UNCONFIRMED") from None
            blocked_key = self.api.key_info(token)
            if blocked_key.get("blocked") is not True:
                raise BudgetBoundaryDenied("DENIED_OWNER_UNVERIFIED_KEY_BLOCK_UNCONFIRMED") from None
            if isinstance(exc, BudgetBoundaryDenied):
                raise
            raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_KEY_SCOPE_MISMATCH") from None
        return token, user, key

    def _assert_no_owner_oneshot_keys(self, identity: P12ExperimentIdentity) -> None:
        """Reject any prior key on the unique experiment user, including revoked keys."""
        for status_filter in ("active", "expired", "revoked", "deleted"):
            page = 1
            while True:
                query = urllib.parse.urlencode({
                    "user_id": identity.user_id,
                    "status": status_filter,
                    "page": page,
                    "size": 100,
                    "return_full_object": "true",
                })
                status, payload = self.api.request("GET", f"/key/list?{query}")
                keys = payload.get("keys")
                total_pages = payload.get("total_pages")
                if (
                    status != 200
                    or not isinstance(keys, list)
                    or type(total_pages) is not int
                    or total_pages < page
                ):
                    if status == 200 and total_pages == 0 and keys == []:
                        break
                    raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_KEY_HISTORY_UNAVAILABLE")
                if keys:
                    raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_KEY_ALREADY_ISSUED")
                if page >= total_pages:
                    break
                page += 1

    def _verify_owner_user(
        self,
        identity: P12ExperimentIdentity,
        user: dict[str, Any] | None,
        expected_alias: str,
    ) -> dict[str, Any]:
        if not isinstance(user, dict):
            raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_USER_MISSING")
        try:
            observed_budget = float(user.get("max_budget"))
            spend = float(user.get("spend", 0.0))
        except (TypeError, ValueError, OverflowError):
            raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_USER_INVALID") from None
        if (
            user.get("user_id") != identity.user_id
            or user.get("user_alias") != expected_alias
            or not math.isclose(observed_budget, MAX_EXPERIMENT_BUDGET_USD, rel_tol=0, abs_tol=1e-12)
            or user.get("budget_duration") is not None
            or user.get("models") != list(OWNER_ONESHOT_MODELS)
            or user.get("max_parallel_requests") != MAX_PARALLEL_REQUESTS
            or not math.isfinite(spend)
            or spend != 0
        ):
            raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_USER_SCOPE_OR_SPEND_MISMATCH")
        return user

    def _verify_owner_key(
        self,
        identity: P12ExperimentIdentity,
        key: dict[str, Any],
        expected_alias: str,
        budget: float,
    ) -> dict[str, Any]:
        try:
            key_budget = float(key.get("max_budget"))
            expiry_value = key.get("expires")
            if isinstance(expiry_value, (int, float)):
                expiry = datetime.fromtimestamp(float(expiry_value), tz=timezone.utc)
            elif isinstance(expiry_value, str):
                expiry = datetime.fromisoformat(expiry_value.replace("Z", "+00:00"))
                if expiry.tzinfo is None or expiry.utcoffset() is None:
                    raise ValueError("timezone required")
                expiry = expiry.astimezone(timezone.utc)
            else:
                raise ValueError("expiry required")
        except (ValueError, TypeError, OverflowError, OSError):
            raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_KEY_INVALID") from None
        now = datetime.now(timezone.utc)
        if (
            key.get("user_id") != identity.user_id
            or key.get("key_alias") != expected_alias
            or key.get("models") != list(OWNER_ONESHOT_MODELS)
            or key.get("budget_duration") is not None
            or key.get("max_parallel_requests") != MAX_PARALLEL_REQUESTS
            or not math.isfinite(key_budget)
            or key_budget <= 0
            or key_budget > budget
            or expiry <= now
            or expiry > now + timedelta(hours=24, minutes=2)
        ):
            raise BudgetBoundaryDenied("DENIED_OWNER_NATIVE_KEY_SCOPE_MISMATCH")
        return key
