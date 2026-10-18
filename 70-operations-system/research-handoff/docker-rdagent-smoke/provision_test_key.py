"""Control-side provisioning and verification for per-run TEST_ONLY keys."""

from __future__ import annotations

import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = "http://127.0.0.1:4000"
MOCK_URL = "http://mock:8000"
MODELS = ["deepseek-chat", "qwen3-embedding:0.6b"]
RESET_PERIOD = "1h"
KEY_DURATION = "1h"
MAX_PARALLEL_REQUESTS = 1


def request(method: str, path: str, *, key: str, body=None):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        payload = exc.read()
        try:
            result = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            result = {}
        return exc.code, result


def master_key() -> str:
    return os.environ["LITELLM_MASTER_KEY"]


def virtual_key() -> str:
    value = os.environ["P3_TEST_PROXY_KEY"]
    if not value.startswith("sk-"):
        raise ValueError("invalid scoped key")
    return value


def key_info(token: str) -> dict:
    path = "/key/info?" + urllib.parse.urlencode({"key": token})
    status, payload = request("GET", path, key=master_key())
    if status != 200:
        raise RuntimeError(f"key info returned HTTP {status}")
    info = payload.get("info", payload)
    if not isinstance(info, dict):
        raise RuntimeError("key info response malformed")
    return info


def info_is_scoped(info: dict, max_budget: float) -> bool:
    try:
        observed_budget = float(info.get("max_budget"))
    except (TypeError, ValueError):
        return False
    return (
        math.isfinite(observed_budget)
        and info.get("models") == MODELS
        and math.isclose(observed_budget, max_budget, rel_tol=0, abs_tol=1e-12)
        and info.get("budget_duration") == RESET_PERIOD
        and bool(info.get("expires"))
        and info.get("max_parallel_requests") == MAX_PARALLEL_REQUESTS
    )


def settled_spend(token: str, *, timeout: float = 90, stable_reads: int = 8) -> tuple[dict, float]:
    """Wait for native key spend to stop changing before the exhaustion probe."""
    deadline = time.monotonic() + timeout
    previous = None
    stable_count = 0
    latest_info = {}
    latest_spend = 0.0
    while time.monotonic() < deadline:
        latest_info = key_info(token)
        try:
            latest_spend = float(latest_info.get("spend", 0.0))
        except (TypeError, ValueError):
            raise RuntimeError("LiteLLM native spend was not numeric") from None
        if not math.isfinite(latest_spend) or latest_spend < 0:
            raise RuntimeError("LiteLLM native spend was invalid")
        if previous is not None and math.isclose(latest_spend, previous, rel_tol=0, abs_tol=1e-12):
            stable_count += 1
        else:
            stable_count = 0
        if latest_spend > 0 and stable_count >= stable_reads:
            return latest_info, latest_spend
        previous = latest_spend
        time.sleep(1)
    raise RuntimeError("LiteLLM native spend did not settle before the bounded timeout")


def create(max_budget: float, key_alias: str) -> dict:
    if not math.isfinite(max_budget) or max_budget <= 0:
        raise ValueError("synthetic TEST_ONLY max_budget must be positive and finite")
    if not key_alias.startswith("aq-p12-finquant-test-only-") or len(key_alias) > 64:
        raise ValueError("TEST_ONLY key alias must be request-scoped")
    status, payload = request(
        "POST", "/key/generate", key=master_key(),
        body={
            "key_alias": key_alias,
            "models": MODELS,
            "max_budget": max_budget,
            "budget_duration": RESET_PERIOD,
            "duration": KEY_DURATION,
            "max_parallel_requests": MAX_PARALLEL_REQUESTS,
        },
    )
    if status not in (200, 201):
        raise RuntimeError(f"native key generation returned HTTP {status}")
    token = payload.get("key") or payload.get("token")
    if not isinstance(token, str) or not token.startswith("sk-"):
        raise RuntimeError("native key generation returned no token")
    info = key_info(token)
    if not info_is_scoped(info, max_budget):
        request("POST", "/key/block", key=master_key(), body={"key": token})
        raise RuntimeError("native key info did not match requested TEST_ONLY limits")
    return {
        "classification": "TEST_PROXY_KEY_CREATED",
        "token": token,
        "key_alias": key_alias,
        "verified": True,
        "max_budget": max_budget,
        "budget_duration": RESET_PERIOD,
        "duration": KEY_DURATION,
        "max_parallel_requests": MAX_PARALLEL_REQUESTS,
        "models": MODELS,
        "key_expires": info.get("expires"),
    }


def mock_counts() -> dict:
    with urllib.request.urlopen(MOCK_URL + "/counts", timeout=5) as response:
        value = json.load(response)
    if not isinstance(value, dict) or set(value) != {"chat", "embedding"}:
        raise RuntimeError("Mock count response malformed")
    return value


def verify_exhaustion() -> dict:
    token = virtual_key()
    info, spent = settled_spend(token)

    # Lower only the synthetic test key's native cap to its already-recorded
    # spend so the next chargeable probe exercises LiteLLM's native gate.
    status, _ = request(
        "POST", "/key/update", key=master_key(),
        body={"key": token, "max_budget": spent},
    )
    if status not in (200, 201):
        raise RuntimeError(f"native key budget update returned HTTP {status}")
    info = key_info(token)
    if not math.isclose(float(info.get("max_budget", -1)), spent, rel_tol=0, abs_tol=1e-12):
        raise RuntimeError("native test budget update was not persisted")

    before = mock_counts()
    status, body = request(
        "POST", "/v1/chat/completions", key=token,
        body={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "TEST_ONLY budget exhaustion probe"}],
            "max_tokens": 20,
        },
    )
    error = body.get("error", {}) if isinstance(body, dict) else {}
    after = mock_counts()
    if status != 422 or error.get("type") != "budget_exceeded" or after != before:
        raise RuntimeError("native budget exhaustion probe was not denied before Mock")
    return {
        "classification": "TEST_PROXY_BUDGET_ENFORCED",
        "http_status": status,
        "spend": spent,
        "max_budget": float(info["max_budget"]),
        "excess_denied_before_mock": True,
        "mock_counts_unchanged": True,
        "mock_counts": after,
    }


def block_key() -> dict:
    token = virtual_key()
    status, payload = request("POST", "/key/block", key=master_key(), body={"key": token})
    if status not in (200, 201) or payload.get("blocked") is not True:
        raise RuntimeError(f"native key block returned HTTP {status}")
    info = key_info(token)
    if info.get("blocked") is not True:
        raise RuntimeError("native key block state was not persisted")
    return {
        "classification": "TEST_PROXY_KEY_BLOCKED",
        "blocked": True,
        "spend": float(info.get("spend", 0.0)),
        "models": info.get("models"),
    }


def main() -> int:
    try:
        mode = sys.argv[1]
        if mode == "create" and len(sys.argv) == 4:
            result = create(float(sys.argv[2]), sys.argv[3])
        elif mode == "verify-exhaustion" and len(sys.argv) == 2:
            result = verify_exhaustion()
        elif mode == "block" and len(sys.argv) == 2:
            result = block_key()
        else:
            raise ValueError("invalid control command")
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except Exception as exc:
        print(json.dumps({"classification": "TEST_PROXY_CONTROL_FAILED", "error_type": type(exc).__name__}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
