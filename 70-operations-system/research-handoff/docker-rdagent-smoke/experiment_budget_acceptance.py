"""Live acceptance for one small native LiteLLM user budget on local Mock."""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from typing import Any

from native_experiment_budget import (
    ALLOWED_MODELS,
    BudgetBoundaryDenied,
    LiteLLMNativeAPI,
    NativeExperimentBudgetController,
    P12ExperimentIdentity,
)


STATE_DIR = Path("/test-state/p12-native-experiment-budget-001")
REQUEST_FILE = STATE_DIR / "request.json"
POLICY_FILE = STATE_DIR / "policy.json"
P12_STATE_DIR = STATE_DIR / "p12-state"
RESULT_FILE = STATE_DIR / "acceptance-result.json"
KEYS_FILE = STATE_DIR / "temporary-keys.json"
FIXTURE_BUDGET = 0.00012
ADMIN_KEY = os.environ["LITELLM_MASTER_KEY"]
API = LiteLLMNativeAPI("http://127.0.0.1:4000", ADMIN_KEY)
CONTROLLER = NativeExperimentBudgetController(API)


def require(condition: bool, label: str) -> None:
    if not condition:
        raise RuntimeError(f"FAIL {label}")
    print(f"PASS {label}", flush=True)


def load_p12_identity() -> tuple[P12ExperimentIdentity, dict[str, Any]]:
    envelope = json.loads(REQUEST_FILE.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    request = envelope["research_request"]
    identity = P12ExperimentIdentity.from_p12(request, policy)
    claim_path = P12_STATE_DIR / f"{identity.request_id.removeprefix('sha256:')}.claim.json"
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    require(claim.get("request_id") == identity.request_id, "existing P12 durable claim matches request")
    require(claim.get("standing_policy_id") == identity.standing_policy_id, "P12 claim binds standing policy")
    require(claim.get("research_budget_identity") == identity.research_budget_identity, "P12 claim binds experiment identity")
    require(claim.get("native_experiment_user_id") == identity.user_id, "P12 claim binds deterministic native user")
    return identity, claim


def mock_counts() -> dict[str, int]:
    with urllib.request.urlopen("http://mock:8000/counts", timeout=5) as response:
        value = json.load(response)
    if set(value) != {"chat", "embedding"}:
        raise RuntimeError("Mock counts malformed")
    return value


def user_spend(identity: P12ExperimentIdentity) -> tuple[dict[str, Any], float]:
    info = API.user_info(identity.user_id)
    if not isinstance(info, dict):
        raise RuntimeError("native experiment user is missing")
    try:
        spend = float(info.get("spend"))
    except (TypeError, ValueError):
        raise RuntimeError("native user spend is not numeric") from None
    if spend < 0 or spend != spend or spend == float("inf"):
        raise RuntimeError("native user spend is invalid")
    return info, spend


def wait_for_spend_increase(identity: P12ExperimentIdentity, previous: float) -> tuple[dict[str, Any], float]:
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        info, spend = user_spend(identity)
        if spend > previous:
            return info, spend
        time.sleep(1)
    raise RuntimeError("native user spend did not increase")


def issue_key(identity: P12ExperimentIdentity, label: str, run_id: str) -> str:
    return CONTROLLER.issue_test_key(
        identity,
        key_alias=f"aq-p12-exp-test-{run_id}-{label}",
        budget_usd=FIXTURE_BUDGET,
        user_budget_usd=FIXTURE_BUDGET,
        duration="24h",
        synthetic_fixture_verified=True,
        p12_replay=False,
    )


def persist_keys(keys: list[str]) -> None:
    KEYS_FILE.write_text(json.dumps(keys), encoding="utf-8")
    KEYS_FILE.chmod(0o600)


def block_and_verify(token: str) -> bool:
    status, _ = API.request("POST", "/key/block", {"key": token})
    if status != 200:
        return False
    return API.key_info(token).get("blocked") is True


def worker_chat(token: str) -> tuple[int, dict[str, Any]]:
    body = json.dumps(
        {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "P12 synthetic experiment budget probe"}],
            "max_tokens": 20,
        }
    ).encode()
    request = urllib.request.Request(
        API.base_url + "/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError):
            raw = exc.read()
            try:
                return exc.code, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return exc.code, {}
        raise


def tracked_requests():
    seen: list[tuple[str, str]] = []
    original = API.request

    def wrapped(method: str, path: str, body=None):
        seen.append((method, path.split("?", 1)[0]))
        return original(method, path, body)

    API.request = wrapped  # type: ignore[method-assign]
    return seen


def setup() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if RESULT_FILE.exists() or KEYS_FILE.exists():
        raise RuntimeError("acceptance state already exists; use replay or after-restart")
    identity, claim = load_p12_identity()
    existing = API.user_info(identity.user_id)
    if existing is None:
        user = CONTROLLER.ensure_test_user(
            identity,
            budget_usd=FIXTURE_BUDGET,
            synthetic_fixture_verified=True,
            p12_replay=False,
        )
        print("PASS native user allocated once for synthetic fixture", flush=True)
    else:
        user = CONTROLLER._verify_user(identity, existing, FIXTURE_BUDGET)
        require(float(user.get("spend", -1)) == 0.0, "interrupted setup has no prior spend")
        print("PASS interrupted setup reuses the same native user without replenishment", flush=True)
    require(user.get("user_id") == identity.user_id, "native user id is deterministic from P12 budget identity")
    require(float(user.get("max_budget", -1)) == FIXTURE_BUDGET, "native user has the small synthetic total budget")
    require(user.get("budget_duration") is None, "native user budget has no reset")
    require(user.get("models") == list(ALLOWED_MODELS), "native user model allowlist persisted")
    require(user.get("max_parallel_requests") == 1, "native user concurrency is one")

    keys: list[str] = []
    persist_keys(keys)
    run_id = uuid.uuid4().hex[:12]
    before = mock_counts()
    info_a = CONTROLLER._verify_user(identity, API.user_info(identity.user_id), FIXTURE_BUDGET)
    spend_before = float(info_a["spend"])
    key_a = issue_key(identity, "key-a", run_id)
    keys.append(key_a)
    persist_keys(keys)
    key_a_info = API.key_info(key_a)
    require(key_a_info.get("user_id") == identity.user_id, "Key A attaches to experiment user")
    require(key_a_info.get("budget_duration") is None, "Key A budget has no reset")
    status, _ = worker_chat(key_a)
    require(status == 200, "Key A consumes part of native user budget through Mock")
    user_after_a, spend_after_a = wait_for_spend_increase(identity, spend_before)
    require(spend_after_a < FIXTURE_BUDGET, "Key A leaves part of aggregate budget")

    key_b = issue_key(identity, "key-b", run_id)
    keys.append(key_b)
    persist_keys(keys)
    key_b_info = API.key_info(key_b)
    require(key_b_info.get("user_id") == key_a_info.get("user_id") == identity.user_id, "Key B shares the SAME native user")
    require(key_b_info.get("budget_duration") is None, "Key B budget has no reset")
    status, _ = worker_chat(key_b)
    require(status == 200, "Key B consumes the shared remaining budget through Mock")
    user_after_b, spend_after_b = wait_for_spend_increase(identity, spend_after_a)
    require(spend_after_b > spend_after_a, "Key B spend accrued to the same native user")

    key_c = issue_key(identity, "key-c", run_id)
    keys.append(key_c)
    persist_keys(keys)
    key_c_info = API.key_info(key_c)
    require(key_c_info.get("user_id") == identity.user_id, "new Key C remains attached to same user")
    user_after_c, spend_after_c = user_spend(identity)
    require(float(user_after_c["max_budget"]) == FIXTURE_BUDGET, "new key did not allocate or replenish user budget")
    require(spend_after_c == spend_after_b, "key issuance did not alter native user spend")
    before_denied = mock_counts()
    status, _ = worker_chat(key_c)
    after_denied = mock_counts()
    require(status >= 400, "exhausted aggregate budget denied Key C")
    require(after_denied == before_denied, "aggregate denial did not reach Mock")
    require(after_denied["chat"] == before["chat"] + 2, "only Key A and Key B reached Mock")

    seen = tracked_requests()
    replay_user = CONTROLLER.ensure_test_user(
        identity,
        budget_usd=FIXTURE_BUDGET,
        synthetic_fixture_verified=True,
        p12_replay=True,
    )
    require(replay_user.get("user_id") == identity.user_id, "P12 replay reuses existing native user")
    try:
        CONTROLLER.issue_test_key(
            identity,
            key_alias="aq-p12-exp-test-key-replay",
            budget_usd=FIXTURE_BUDGET,
            user_budget_usd=FIXTURE_BUDGET,
            synthetic_fixture_verified=True,
            p12_replay=True,
        )
    except BudgetBoundaryDenied as exc:
        require(exc.classification == "DENIED_KEY_ISSUANCE_ON_P12_REPLAY", "P12 replay cannot issue a new key")
    else:
        raise RuntimeError("P12 replay unexpectedly issued a key")
    require(not any(path in ("/user/new", "/key/generate") for _, path in seen), "P12 replay made no allocation or key API call")

    result = {
        "request_id": identity.request_id,
        "standing_policy_id": identity.standing_policy_id,
        "research_budget_identity": identity.research_budget_identity,
        "user_id": identity.user_id,
        "max_budget": FIXTURE_BUDGET,
        "spend_after_key_a": spend_after_a,
        "spend_after_key_b": spend_after_b,
        "mock_counts_after_denial": after_denied,
        "p12_claim_attempt_id": claim["attempt_id"],
    }
    RESULT_FILE.write_text(json.dumps(result, sort_keys=True), encoding="utf-8")
    print("RESULT EXPERIMENT_BUDGET_SETUP=PASS", flush=True)


def replay() -> None:
    prior = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
    identity, claim = load_p12_identity()
    require(identity.request_id == prior["request_id"], "replay request identity unchanged")
    require(claim["attempt_id"] == prior["p12_claim_attempt_id"], "P12 durable claim attempt unchanged")
    seen = tracked_requests()
    user = CONTROLLER.ensure_test_user(
        identity,
        budget_usd=FIXTURE_BUDGET,
        synthetic_fixture_verified=True,
        p12_replay=True,
    )
    require(user.get("user_id") == prior["user_id"], "replay resolves to the original native user")
    try:
        CONTROLLER.issue_test_key(
            identity,
            key_alias="aq-p12-exp-test-key-replay",
            budget_usd=FIXTURE_BUDGET,
            user_budget_usd=FIXTURE_BUDGET,
            synthetic_fixture_verified=True,
            p12_replay=True,
        )
    except BudgetBoundaryDenied as exc:
        require(exc.classification == "DENIED_KEY_ISSUANCE_ON_P12_REPLAY", "replay refuses key renewal")
    else:
        raise RuntimeError("replay unexpectedly issued a key")
    require(not any(path in ("/user/new", "/key/generate") for _, path in seen), "replay cannot reissue native allocation")
    current, spend_now = user_spend(identity)
    require(float(current["max_budget"]) == FIXTURE_BUDGET, "replay preserves original user budget")
    require(spend_now >= float(prior["spend_after_key_b"]), "replay preserves accumulated user spend")
    print("RESULT EXPERIMENT_BUDGET_REPLAY=PASS", flush=True)


def after_restart() -> None:
    prior = json.loads(RESULT_FILE.read_text(encoding="utf-8"))
    identity, _ = load_p12_identity()
    user, current_spend = user_spend(identity)
    require(user.get("user_id") == prior["user_id"], "native user identity survived PostgreSQL restart")
    require(float(user.get("max_budget", -1)) == FIXTURE_BUDGET, "native total budget survived PostgreSQL restart")
    require(user.get("budget_duration") is None, "native user budget remains non-resetting after restart")
    require(current_spend == float(prior["spend_after_key_b"]), "native aggregate spend survived PostgreSQL restart")
    keys = json.loads(KEYS_FILE.read_text(encoding="utf-8"))
    key_c = keys[2]
    before = mock_counts()
    status, _ = worker_chat(key_c)
    after = mock_counts()
    require(status >= 400, "exhausted shared budget remains denied after PostgreSQL restart")
    require(after == before, "post-restart denial did not reach Mock")
    for index, token in enumerate(keys, start=1):
        require(block_and_verify(token), f"temporary TEST_ONLY key {index} blocked")
    KEYS_FILE.unlink(missing_ok=True)
    prior["post_restart_spend"] = current_spend
    RESULT_FILE.write_text(json.dumps(prior, sort_keys=True), encoding="utf-8")
    print("RESULT EXPERIMENT_BUDGET_POSTGRES_RESTART=PASS", flush=True)


def main() -> int:
    phases = {"setup": setup, "replay": replay, "after-restart": after_restart}
    try:
        if len(sys.argv) != 2 or sys.argv[1] not in phases:
            raise RuntimeError("usage: experiment_budget_acceptance.py setup|replay|after-restart")
        phases[sys.argv[1]]()
        return 0
    except Exception as exc:
        # A failed setup must not leave temporary TEST_ONLY credentials active.
        if len(sys.argv) == 2 and sys.argv[1] == "setup" and KEYS_FILE.exists() and not RESULT_FILE.exists():
            try:
                for token in json.loads(KEYS_FILE.read_text(encoding="utf-8")):
                    if not block_and_verify(token):
                        raise RuntimeError("could not verify temporary TEST_ONLY key block")
                KEYS_FILE.unlink(missing_ok=True)
            except Exception:
                print("RESULT TEST_ONLY_KEY_CLEANUP=UNVERIFIED", file=sys.stderr, flush=True)
        print(f"RESULT EXPERIMENT_BUDGET=FAIL ({type(exc).__name__}: {exc})", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
