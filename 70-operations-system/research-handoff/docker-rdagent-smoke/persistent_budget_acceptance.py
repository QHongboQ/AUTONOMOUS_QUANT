"""Acceptance probes for native LiteLLM key budgets in the TEST_ONLY stack.

This script is executed inside the Proxy control container. It contains no
budget/accounting implementation; it calls LiteLLM's native HTTP APIs and the
existing local Mock. Durable test state is held in a separately mounted,
ACL-protected operations directory, never in the repository.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = "http://127.0.0.1:4000"
MOCK_URL = "http://mock:8000"
ADMIN_KEY = os.environ["LITELLM_MASTER_KEY"]
STATE_DIR = Path("/test-state")
KEY_FILE = STATE_DIR / "virtual-key.txt"
OUTAGE_KEY_FILE = STATE_DIR / "outage-probe-key.txt"
RESULT_FILE = STATE_DIR / "acceptance-results.json"
EXPECTED_BUDGET = 0.0001  # synthetic fixture only; not owner spending approval


def http(method: str, path: str, *, key: str | None = None, body=None, timeout=12):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(BASE_URL + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {}
        return exc.code, payload


def require(condition: bool, label: str, detail: str = "") -> None:
    if not condition:
        raise RuntimeError(f"FAIL {label}" + (f": {detail}" if detail else ""))
    print(f"PASS {label}", flush=True)


def mock_counts() -> dict:
    with urllib.request.urlopen(MOCK_URL + "/counts", timeout=5) as response:
        return json.load(response)


def key_info(token: str) -> dict:
    query = urllib.parse.urlencode({"key": token})
    status, body = http("GET", f"/key/info?{query}", key=ADMIN_KEY)
    require(status == 200, "native key info available", f"HTTP {status}")
    info = body.get("info", body)
    require(isinstance(info, dict), "native key info is structured")
    return info


def create_key(alias: str, budget: float) -> str:
    status, body = http(
        "POST", "/key/generate", key=ADMIN_KEY,
        body={
            "key_alias": alias,
            "models": ["deepseek-chat"],
            "max_budget": budget,
            "budget_duration": "1h",
            "duration": "1h",
            "max_parallel_requests": 1,
        },
    )
    require(status in (200, 201), "native LiteLLM key generation", f"HTTP {status}")
    token = body.get("key") or body.get("token")
    require(isinstance(token, str) and token.startswith("sk-"), "scoped virtual key returned")
    return token


def write_secret(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def chat(token: str, model="deepseek-chat") -> tuple[int, dict]:
    return http(
        "POST", "/v1/chat/completions", key=token,
        body={"model": model, "messages": [{"role": "user", "content": "x"}], "max_tokens": 20},
        timeout=30,
    )


def spend(info: dict) -> float:
    value = info.get("spend")
    if not isinstance(value, (float, int)):
        raise RuntimeError("LiteLLM native key info has no numeric spend")
    return float(value)


def setup() -> None:
    require(not KEY_FILE.exists() and not RESULT_FILE.exists(), "fresh isolated acceptance state")
    token = create_key("aq-p12-persistent-budget-test-only", EXPECTED_BUDGET)
    write_secret(KEY_FILE, token)
    info = key_info(token)
    require(info.get("models") == ["deepseek-chat"], "native model allowlist persisted")
    require(float(info.get("max_budget", -1)) == EXPECTED_BUDGET, "native synthetic budget persisted")
    require(info.get("budget_duration") == "1h", "native reset period persisted")
    require(info.get("max_parallel_requests") == 1, "native concurrency bound persisted")
    require(bool(info.get("expires")), "native key expiration persisted")

    before = mock_counts()
    status, _ = chat(token, "not-allowlisted")
    require(status in (400, 401, 403), "non-allowlisted model denied", f"HTTP {status}")
    require(mock_counts() == before, "model denial occurred before Mock")

    successful = 0
    while successful < 12:
        status, _ = chat(token)
        if status == 200:
            successful += 1
            continue
        break
    require(successful > 0, "allowed chat routed through LiteLLM to Mock")
    require(status in (400, 402, 403, 422, 429), "native budget exhaustion denied next request", f"HTTP {status}")
    after = mock_counts()
    require(after["chat"] == before["chat"] + successful, "only successful chargeable calls reached Mock")
    deadline = time.monotonic() + 30
    native_spend = 0.0
    while time.monotonic() < deadline:
        native_spend = spend(key_info(token))
        if native_spend > 0:
            break
        time.sleep(1)
    require(native_spend > 0, "native LiteLLM spending recorded")
    require(native_spend <= EXPECTED_BUDGET + 1e-9, "native budget not exceeded", str(native_spend))
    status, _ = chat(token)
    require(status in (400, 402, 403, 422, 429), "budget replay denied", f"HTTP {status}")
    require(mock_counts() == after, "exhausted replay did not reach Mock")

    RESULT_FILE.write_text(json.dumps({"spend": native_spend, "mock_counts": after, "successes": successful}), encoding="utf-8")
    print(f"NATIVE_SPEND={native_spend:.12f} SUCCESSFUL_MOCK_CALLS={successful}", flush=True)


def after_restart() -> None:
    token = KEY_FILE.read_text(encoding="utf-8").strip()
    prior = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
    info = key_info(token)
    require(abs(spend(info) - float(prior["spend"])) < 1e-12, "key spend survived Proxy/PostgreSQL restart")
    require(info.get("models") == ["deepseek-chat"], "key allowlist survived restart")
    status, _ = chat(token)
    require(status in (400, 402, 403, 422, 429), "budget remains exhausted after restart", f"HTTP {status}")
    require(mock_counts() == prior["mock_counts"], "restart replay caused no additional Mock dispatch")
    print("RESTART_SPEND_PRESERVED=1", flush=True)


def prepare_outage_probe() -> None:
    require(not OUTAGE_KEY_FILE.exists(), "fresh outage probe state")
    token = create_key("aq-p12-db-outage-probe-test-only", 0.001)
    write_secret(OUTAGE_KEY_FILE, token)
    print("OUTAGE_PROBE_READY=1", flush=True)


def outage_check() -> None:
    token = OUTAGE_KEY_FILE.read_text(encoding="utf-8").strip()
    before = mock_counts()
    status, _ = chat(token)
    after = mock_counts()
    require(status >= 400, "database outage fails closed", f"HTTP {status}")
    require(after == before, "database outage denied before Mock")
    print(f"DATABASE_OUTAGE_HTTP={status}", flush=True)


def after_outage_recovery() -> None:
    token = KEY_FILE.read_text(encoding="utf-8").strip()
    prior = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
    info = key_info(token)
    require(abs(spend(info) - float(prior["spend"])) < 1e-12, "spend unchanged after database outage recovery")
    status, _ = chat(token)
    require(status in (400, 402, 403, 422, 429), "exhausted key remains blocked after outage recovery")
    require(mock_counts() == prior["mock_counts"], "outage recovery caused no duplicate dispatch")


def main() -> int:
    phases = {
        "setup": setup,
        "after-restart": after_restart,
        "prepare-outage": prepare_outage_probe,
        "outage-check": outage_check,
        "after-outage": after_outage_recovery,
    }
    try:
        phase = sys.argv[1]
        if phase not in phases:
            raise RuntimeError("unknown acceptance phase")
        phases[phase]()
        print(f"RESULT {phase.upper().replace('-', '_')}=PASS", flush=True)
        return 0
    except Exception as exc:
        print(f"RESULT {sys.argv[1] if len(sys.argv) > 1 else 'unknown'}=FAIL ({type(exc).__name__}: {exc})", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
