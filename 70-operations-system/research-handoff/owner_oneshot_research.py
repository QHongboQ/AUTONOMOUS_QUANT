"""Interactive local-owner, single-attempt P12 full fin_quant handoff.

This uses the existing P12 request markers, native LiteLLM APIs, pinned
RD-Agent/Qlib image, and existing Compose stack. It is not an unattended
authorization source; every new attempt requires a local TTY confirmation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import rfc8785

REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOFF = Path(__file__).resolve().parent
SMOKE = HANDOFF / "docker-rdagent-smoke"
P4_DIR = REPO_ROOT / "40-certification-system/champion-challenger/p4-residual-thin-policy"
sys.path.insert(0, str(P4_DIR))
sys.path.insert(0, str(HANDOFF))
sys.path.insert(0, str(SMOKE))

import aq_p4_policy as p4  # noqa: E402
import standing_policy  # noqa: E402
import p12_research_handoff as p12  # noqa: E402
from docker_rdagent_target import (  # noqa: E402
    FINQUANT_DATA_MOUNTS,
    FINQUANT_OUTPUT_ROOT,
    PERSISTENT_LITELLM_ENV_FILE,
    PERSISTENT_LITELLM_PROJECT,
    PINNED_FINQUANT_IMAGE,
    PINNED_FINQUANT_IMAGE_ID,
    _finquant_output_directory,
    _durable_output_write,
    _redact_diagnostics,
    _redact_persisted_selector_logs,
)
from native_experiment_budget import (  # noqa: E402
    OWNER_ONESHOT_MODELS,
    P12ExperimentIdentity,
    experiment_user_id,
)

MAX_POLICY_LIFETIME = timedelta(hours=24)
OWNER_MODEL_ROUTES = frozenset({
    ("deepseek", "deepseek/deepseek-flash", "PAID"),
    ("ollama", "ollama/qwen3-embedding:0.6b", "LOCAL"),
})
REAL_TARGET = "DOCKER_RDAGENT_FINQUANT_OWNER_ONESHOT"
EXIT_BLOCKED = 3
EXIT_FAILED = 4


def _json(path: Path) -> dict[str, Any]:
    value = p12._read_json_nofollow(path)
    return value


def _validate_inputs(request_path: Path, policy_path: Path, now: datetime | None = None):
    envelope = _json(request_path)
    if set(envelope) != {"p4_decision", "research_request"}:
        raise ValueError("expected a P4 decision and ResearchRequestV1")
    decision = p4.LifecycleDecisionEvidenceV1.model_validate(envelope["p4_decision"])
    request = p4.ResearchRequestV1.model_validate(envelope["research_request"])
    if (
        decision.decision_kind != p4.DecisionKind.CHALLENGER_NEEDED
        or decision.evidence_classification != "REAL_EXTERNAL_EVIDENCE"
        or decision.reason.value != request.reason.value
        or decision.source_evidence_identities != request.source_evidence_identities
    ):
        raise ValueError("P4 decision is synthetic or does not match ResearchRequestV1")
    policy = standing_policy.P12StandingResearchPolicyV1.model_validate(_json(policy_path))
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    effective = policy.effective_at.astimezone(timezone.utc)
    expires = policy.expires_at.astimezone(timezone.utc)
    routes = frozenset((route.provider, route.model, route.billing_class) for route in policy.allowed_llm_routes)
    if (
        policy.authorization_status != "APPROVED"
        or policy.evidence_classification != "HUMAN_APPROVED"
        or policy.revoked_at is not None
        or not effective <= current < expires
        or expires - current > MAX_POLICY_LIFETIME
        or policy.maximum_period_spend_usd != 5
        or policy.maximum_run_spend_usd != 5
        or policy.maximum_concurrent_runs != 1
        or policy.spending_limit_semantics != "TRACKED_SPEND_LIMIT_ONLY"
        or routes != OWNER_MODEL_ROUTES
        or policy.research_budget_identity != request.research_budget_identity
        or policy.allowed_universe_scope_identities != (request.asset_universe_scope_identity,)
        or policy.allowed_request_provenance_identities != (request.request_provenance,)
        or policy.allowed_research_families != tuple(request.allowed_research_families)
    ):
        raise ValueError("P12 owner policy does not match the bounded one-shot scope")
    return envelope, decision, request, policy


def _identity_marker(state_dir: Path, budget_identity: str) -> Path:
    return state_dir / ("experiment-" + budget_identity.removeprefix("sha256:") + ".json")


def _ensure_experiment_binding(
    state_dir: Path, request: Any, policy: Any
) -> None:
    path = _identity_marker(state_dir, request.research_budget_identity)
    expected = {
        "research_budget_identity": request.research_budget_identity,
        "request_id": request.request_id,
        "standing_policy_id": policy.policy_id,
        "native_experiment_user_id": experiment_user_id(request.research_budget_identity),
    }
    if path.exists():
        if _json(path) != expected:
            raise ValueError("experiment identity is already bound to another request or policy")
        return
    p12._durable_json_create(path, expected)


def _lock_path(state_dir: Path) -> Path:
    return state_dir / "owner-oneshot-active.lock"


def _acquire_run_lock(state_dir: Path, request_id: str) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(_lock_path(state_dir), flags, 0o600)
    data = json.dumps({"request_id": request_id, "pid": os.getpid()}, sort_keys=True).encode()
    os.write(fd, data)
    os.fsync(fd)
    p12._fsync_directory(state_dir)
    return fd


def _release_run_lock(state_dir: Path, fd: int) -> None:
    os.close(fd)
    try:
        _lock_path(state_dir).unlink()
        p12._fsync_directory(state_dir)
    except FileNotFoundError:
        pass


def _owner_replay(
    state_dir: Path, request_id: str, request_digest: str, budget_identity: str,
    user_id: str, policy_id: str,
) -> tuple[dict[str, Any], int] | None:
    claim_path = p12._claim_file(state_dir, request_id)
    if not claim_path.exists():
        return None
    try:
        claim = _json(claim_path)
        dispatch = _json(p12._dispatch_file(state_dir, request_id))
        terminal = _json(p12._status_file(state_dir, request_id))
    except Exception:
        return ({"classification": "BLOCKED_OWNER_ONESHOT_INCOMPLETE_OR_CORRUPT", "dispatch_count_added": 0}, EXIT_BLOCKED)
    records = (claim, dispatch, terminal)
    expected_attempt = claim.get("attempt_id")
    try:
        if str(uuid.UUID(expected_attempt)) != expected_attempt:
            raise ValueError
    except (ValueError, TypeError, AttributeError):
        return ({"classification": "BLOCKED_OWNER_ONESHOT_ATTEMPT_IDENTITY", "dispatch_count_added": 0}, EXIT_BLOCKED)
    expected = {
        "request_id": request_id,
        "request_digest": request_digest,
        "research_budget_identity": budget_identity,
        "native_experiment_user_id": user_id,
        "standing_policy_id": policy_id,
        "attempt_id": expected_attempt,
        "target_identity": REAL_TARGET,
    }
    if any(any(record.get(key) != value for key, value in expected.items()) for record in records):
        return ({"classification": "BLOCKED_OWNER_ONESHOT_IDENTITY_COLLISION", "dispatch_count_added": 0}, EXIT_BLOCKED)
    if (
        claim.get("state") != "CLAIMED_OWNER_ONESHOT"
        or claim.get("dispatch_mode") != "OWNER_ONESHOT"
        or dispatch.get("dispatch_mode") != "OWNER_ONESHOT"
        or dispatch.get("state") != "DISPATCHING_OWNER_ONESHOT"
        or terminal.get("dispatch_mode") != "OWNER_ONESHOT"
        or terminal.get("key_blocked_after_attempt") is not True
        or terminal.get("real_dispatch_permission") != "LOCAL_INTERACTIVE_OWNER_CONFIRMED"
        or terminal.get("candidate_count") != 0
        or terminal.get("broker_actions") != 0
        or terminal.get("sealed_oos_accessed") is not False
    ):
        return ({"classification": "BLOCKED_OWNER_ONESHOT_UNKNOWN_DISPATCH", "dispatch_count_added": 0}, EXIT_BLOCKED)
    code = terminal.get("target_return_code")
    state = terminal.get("state")
    if type(code) is not int or (state == "SUCCEEDED_OWNER_ONESHOT" and code != 0) or (state == "FAILED_OWNER_ONESHOT" and code == 0):
        return ({"classification": "BLOCKED_OWNER_ONESHOT_TERMINAL_INCONSISTENT", "dispatch_count_added": 0}, EXIT_BLOCKED)
    if state == "SUCCEEDED_OWNER_ONESHOT":
        return ({"classification": state, "status": terminal, "dispatch_count_added": 0}, 0)
    if state == "FAILED_OWNER_ONESHOT":
        return ({"classification": state, "status": terminal, "dispatch_count_added": 0}, EXIT_FAILED)
    return ({"classification": "BLOCKED_OWNER_ONESHOT_UNKNOWN_TERMINAL", "dispatch_count_added": 0}, EXIT_BLOCKED)


def _safe_host_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    names = ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "XDG_RUNTIME_DIR")
    env = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": os.path.expanduser("~"),
    }
    env.update({name: os.environ[name] for name in names if os.environ.get(name)})
    if extra:
        env.update(extra)
    return env


def _compose_args(env_file: Path) -> list[str]:
    return [
        "docker", "compose", "--project-name", PERSISTENT_LITELLM_PROJECT,
        "--env-file", str(env_file),
        "--file", str(SMOKE / "compose.persistent-test.yaml"),
        "--file", str(SMOKE / "compose.deepseek-staging.yaml"),
        "--profile", "deepseek-staging", "--profile", "p12-owner-oneshot",
    ]


def _verify_pinned_chat_token_bound() -> bool:
    probe = r"""
import inspect, json
from rdagent.oai.backend.litellm import LITELLM_SETTINGS, LiteLLMAPIBackend
settings = LITELLM_SETTINGS
backend = object.__new__(LiteLLMAPIBackend)
kwargs = backend.get_complete_kwargs()
source = inspect.getsource(LiteLLMAPIBackend._create_chat_completion_inner_function)
assert settings.chat_max_tokens == 8192
assert settings.chat_model == 'openai/deepseek/deepseek-flash'
assert settings.chat_model_map == {}
assert kwargs['max_tokens'] == 8192
assert 'max_retries=0' in source and '**complete_kwargs' in source
print(json.dumps({'chat_model': kwargs['model'], 'max_tokens': kwargs['max_tokens'], 'chat_model_map': settings.chat_model_map, 'native_retries': 0}))
"""
    result = subprocess.run(
        [
            "docker", "run", "--rm", "--network", "none", "--read-only",
            "--user", "10001:10001", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "--env", "LITELLM_CHAT_MAX_TOKENS=8192",
            "--env", "LITELLM_CHAT_MODEL=openai/deepseek/deepseek-flash",
            "--env", "LITELLM_CHAT_MODEL_MAP={}",
            "--entrypoint", "python", PINNED_FINQUANT_IMAGE, "-c", probe,
        ],
        capture_output=True, text=True, check=False,
        env=_safe_host_environment(), timeout=90,
    )
    if result.returncode != 0:
        raise ValueError("pinned RD-Agent token-bound runtime probe failed")
    try:
        observed = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise ValueError("pinned RD-Agent token-bound runtime probe output was invalid") from None
    if observed != {
        "chat_model": "openai/deepseek/deepseek-flash",
        "max_tokens": 8192,
        "chat_model_map": {},
        "native_retries": 0,
    }:
        raise ValueError("pinned RD-Agent chat token bound was not effective")
    return True


def _new_provider_secret_path(path: Path) -> Path:
    resolved = path.resolve(strict=True)
    approved_root = Path("/mnt/d/AQ/OPERATIONS/P12").resolve(strict=True)
    if (
        not resolved.is_file()
        or not resolved.is_relative_to(approved_root)
        or resolved.is_relative_to(REPO_ROOT.resolve())
        or resolved.is_relative_to(Path("/mnt/d/AQ_DATA/P3").resolve())
    ):
        raise ValueError("new provider secret must be an owner-managed file under D:/AQ/OPERATIONS/P12, outside the repository and P3 data")
    return resolved


def _preflight(
    env_file: Path,
    output_directory: Path | None = None,
    provider_secret_file: Path | None = None,
) -> dict[str, Any]:
    if not env_file.is_file():
        raise ValueError("owner-managed persistent Compose env file is missing")
    missing = [f"{target}<-{source}" for target, source in FINQUANT_DATA_MOUNTS.items() if not Path(source).is_dir()]
    if missing:
        raise ValueError("approved frozen US/PIT read-only inputs are missing")
    image = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{.Id}}", PINNED_FINQUANT_IMAGE],
        capture_output=True, text=True, check=False, env=_safe_host_environment(), timeout=30,
    )
    if image.returncode != 0 or image.stdout.strip() != PINNED_FINQUANT_IMAGE_ID:
        raise ValueError("the pinned RD-Agent/Qlib image is missing or has a different identity")
    token_bound = _verify_pinned_chat_token_bound()
    output = output_directory or Path("/mnt/d/AQ/OPERATIONS/P12/finquant-output/preflight/preflight")
    env = _safe_host_environment({
        "P12_RUN_NAMESPACE": "aq-p12-owner-000000000000",
        "P12_FINQUANT_OUTPUT_DIR": str(output),
        "P12_OWNER_SCOPED_PROXY_KEY": "sk-preflight-placeholder-only",
        "P12_DEEPSEEK_API_KEY_FILE": "/dev/null",
        "LITELLM_DEEPSEEK_STAGING_MASTER_KEY": "sk-preflight-placeholder-only",
        "P12_OLLAMA_API_BASE": "http://127.0.0.1:11434",
        "LITELLM_MASTER_KEY": "sk-preflight-test-only-placeholder",
        "P3_TEST_PROXY_KEY": "sk-test-preflight-placeholder",
        "POSTGRES_PASSWORD": "preflight-only-placeholder",
        "P12_LITELLM_STATE_DIR": "/tmp/p12-preflight-state",
    })
    if provider_secret_file is not None:
        env["P12_DEEPSEEK_API_KEY_FILE"] = str(_new_provider_secret_path(provider_secret_file))
    compose = _compose_args(env_file)
    checked = subprocess.run(
        [*compose, "config", "--quiet"], capture_output=True, text=True,
        check=False, env=env, timeout=60,
    )
    if checked.returncode != 0:
        raise ValueError("combined persistent/staging/worker Compose config is invalid")
    return {
        "classification": "OWNER_ONESHOT_CONFIGURATION_PREFLIGHT_PASS",
        "pinned_image_verified": True,
        "read_only_us_pit_inputs_present": True,
        "compose_valid": True,
        "native_full_loop_command": "rdagent fin_quant --loop-n 1",
        "litellm_chat_max_tokens": 8192,
        "pinned_rdagent_token_bound_verified": token_bound,
        "worker_network": "internal worker_proxy only",
        "paid_key_created": False,
        "provider_calls": 0,
        "research_dispatched": False,
    }


def _control_call(compose: list[str], env: dict[str, str], runtime: Path, payload: dict[str, Any]) -> dict[str, Any]:
    completed = subprocess.run(
        [*compose, "exec", "-T", "litellm-deepseek-staging",
         "python", "/app/owner_oneshot_proxy_control.py"],
        input=json.dumps(payload, sort_keys=True), capture_output=True, text=True,
        check=False, env=env, cwd=runtime, timeout=90,
    )
    try:
        value = json.loads(completed.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise RuntimeError("native Proxy control response was missing or corrupt") from None
    if completed.returncode != 0 or not isinstance(value, dict):
        raise RuntimeError(value.get("classification", "native Proxy control operation failed"))
    return value


def _verify_container(worker_name: str, expected_key: str, expected_output: Path, run_namespace: str) -> dict[str, Any]:
    env = _safe_host_environment()
    inspect = subprocess.run([
        "docker", "container", "inspect", "--format",
        "{{.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.Config.Image}}|{{json .Config.Entrypoint}}|{{json .Config.Cmd}}|{{.Config.User}}|{{.HostConfig.ReadonlyRootfs}}",
        worker_name,
    ], capture_output=True, text=True, check=False, env=env, timeout=30)
    if inspect.returncode != 0:
        raise RuntimeError("one-shot worker terminal state could not be inspected")
    fields = inspect.stdout.strip().split("|", 7)
    if len(fields) != 8:
        raise RuntimeError("one-shot worker identity record was corrupt")
    image_id, state, code, image_name, entrypoint, command, user, readonly = fields
    if (
        image_id != PINNED_FINQUANT_IMAGE_ID or state != "exited"
        or image_name != PINNED_FINQUANT_IMAGE or json.loads(entrypoint) != ["rdagent"]
        or json.loads(command) != ["fin_quant", "--loop-n", "1"]
        or user != "10001:10001" or readonly != "true"
    ):
        raise RuntimeError("one-shot worker process identity or isolation mismatch")
    code_int = int(code)
    mounts_raw = subprocess.run(
        ["docker", "container", "inspect", "--format", "{{json .Mounts}}", worker_name],
        capture_output=True, text=True, check=False, env=env, timeout=30)
    nets_raw = subprocess.run(
        ["docker", "container", "inspect", "--format", "{{json .NetworkSettings.Networks}}", worker_name],
        capture_output=True, text=True, check=False, env=env, timeout=30)
    env_raw = subprocess.run(
        ["docker", "container", "inspect", "--format", "{{json .Config.Env}}", worker_name],
        capture_output=True, text=True, check=False, env=env, timeout=30)
    if any(result.returncode != 0 for result in (mounts_raw, nets_raw, env_raw)):
        raise RuntimeError("one-shot worker isolation could not be inspected")
    mounts = json.loads(mounts_raw.stdout)
    networks = json.loads(nets_raw.stdout)
    worker_env = dict(item.split("=", 1) for item in json.loads(env_raw.stdout) if "=" in item)
    mounted = {entry.get("Destination"): entry for entry in mounts if isinstance(entry, dict)}
    ro_inputs = all(
        mounted.get(target, {}).get("Source") == source
        and mounted.get(target, {}).get("RW") is False
        and mounted.get(target, {}).get("Type") == "bind"
        for target, source in FINQUANT_DATA_MOUNTS.items()
    )
    output = mounted.get("/workspace", {})
    if (
        len(mounted) != 4 or not ro_inputs
        or output.get("Source") != str(expected_output) or output.get("RW") is not True
        or output.get("Type") != "bind"
        or list(networks) != ["aq-p12-litellm-worker-proxy"]
        or worker_env.get("OPENAI_API_BASE") != "http://litellm-deepseek-staging:4000/v1"
        or worker_env.get("OPENAI_API_KEY") != expected_key
        or worker_env.get("LITELLM_CHAT_MAX_TOKENS") != "8192"
        or worker_env.get("LITELLM_CHAT_MODEL_MAP") != "{}"
        or any(name in worker_env for name in (
            "DEEPSEEK_API_KEY", "LITELLM_DEEPSEEK_STAGING_MASTER_KEY", "POSTGRES_PASSWORD",
            "LITELLM_MASTER_KEY", "OWNER_SIGNING_PRIVATE_KEY",
        ))
        or worker_env.get("WORKSPACE_PATH") != f"/workspace/runs/{run_namespace}/workspaces"
    ):
        raise RuntimeError("one-shot worker network, mount, model, token, or credential isolation mismatch")
    return {"return_code": code_int, "image_id": image_id, "mounts_valid": True, "network_valid": True, "credential_isolation": True}


def run_one_shot(
    request_path: Path, policy_path: Path, state_dir: Path, runtime_dir: Path,
    env_file: Path, provider_secret_file: Path, *, activate: bool = True,
) -> tuple[dict[str, Any], int]:
    envelope, decision, request, policy = _validate_inputs(request_path, policy_path)
    request_digest = hashlib.sha256(rfc8785.dumps(envelope)).hexdigest()
    budget_identity = request.research_budget_identity
    user_id = experiment_user_id(budget_identity)
    prior = _owner_replay(
        state_dir, request.request_id, request_digest, budget_identity, user_id, policy.policy_id
    )
    if prior is not None:
        return prior
    secret_file = _new_provider_secret_path(provider_secret_file)
    _preflight(env_file, provider_secret_file=secret_file)
    if not activate:
        return ({"classification": "OWNER_ACTIVATION_REQUIRED", "real_dispatch_permission": "DENIED", "dispatch_count_added": 0}, EXIT_BLOCKED)
    if not sys.stdin.isatty():
        return ({"classification": "DENIED_INTERACTIVE_OWNER_TTY_REQUIRED", "real_dispatch_permission": "DENIED", "dispatch_count_added": 0}, EXIT_BLOCKED)
    phrase = f"RUN $5 ONCE {request.request_id}"
    print("This local trusted-host authorization starts one real full RD-Agent/Qlib run.")
    print(f"Experiment user: {user_id}")
    print(
        "Review before confirming: "
        f"scope={request.asset_universe_scope_identity}; "
        f"families={','.join(request.allowed_research_families)}; "
        "models=DeepSeek Flash + local Ollama; total cap=USD 5.00; "
        f"policy expires={policy.expires_at.isoformat()}; "
        "runs=1; concurrency=1; P2/trading authority=none."
    )
    try:
        response = input(f"To activate exactly one run, type: {phrase}\n> ")
    except EOFError:
        response = ""
    if response != phrase:
        return ({"classification": "DENIED_OWNER_ACTIVATION_NOT_CONFIRMED", "real_dispatch_permission": "DENIED", "dispatch_count_added": 0}, EXIT_BLOCKED)

    state_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    if runtime_dir.resolve() == REPO_ROOT or REPO_ROOT in runtime_dir.resolve().parents:
        raise ValueError("owner one-shot runtime directory must be outside the repository")
    lock_fd = _acquire_run_lock(state_dir, request.request_id)
    attempt_id = str(uuid.uuid4())
    run_namespace = "aq-p12-owner-" + hashlib.sha256(
        f"{request.request_id}:{attempt_id}".encode("ascii")
    ).hexdigest()[:12]
    output_directory = _finquant_output_directory(request.request_id, attempt_id, FINQUANT_OUTPUT_ROOT)
    key: str | None = None
    key_blocked = False
    dispatched = False
    keep_lock = False
    staging_started_by_run = False
    staging_stopped = False
    claim = {
        "state": "CLAIMED_OWNER_ONESHOT",
        "request_id": request.request_id,
        "request_digest": request_digest,
        "research_budget_identity": budget_identity,
        "native_experiment_user_id": user_id,
        "attempt_id": attempt_id,
        "standing_policy_id": policy.policy_id,
        "dispatch_mode": "OWNER_ONESHOT",
        "real_dispatch_permission": "LOCAL_INTERACTIVE_OWNER_CONFIRMED",
        "policy_admission": "LOCAL_OWNER_ONESHOT_POLICY_VERIFIED",
        "target_identity": REAL_TARGET,
    }
    try:
        _ensure_experiment_binding(state_dir, request, policy)
        # P12's request-ID exclusive claim is the no-redispatch boundary shared
        # with the existing TEST_ONLY intake.
        try:
            p12._durable_json_create(p12._claim_file(state_dir, request.request_id), claim)
        except FileExistsError:
            replay = _owner_replay(state_dir, request.request_id, request_digest, budget_identity, user_id, policy.policy_id)
            return replay or ({"classification": "BLOCKED_OWNER_ONESHOT_CLAIM_COLLISION", "dispatch_count_added": 0}, EXIT_BLOCKED)
        attempt_record = {
            "request_id": request.request_id,
            "attempt_id": attempt_id,
            "run_namespace": run_namespace,
            "native_cli_command": "rdagent fin_quant --loop-n 1",
            "image": PINNED_FINQUANT_IMAGE,
            "image_id": PINNED_FINQUANT_IMAGE_ID,
            "p2_status": "NOT_EVALUATED_NO_CANDIDATE",
        }
        _durable_output_write(output_directory, "p12-attempt.json", json.dumps(attempt_record, sort_keys=True) + "\n")
        compose = _compose_args(env_file)
        env = _safe_host_environment({
            "P12_RUN_NAMESPACE": run_namespace,
            "P12_FINQUANT_OUTPUT_DIR": str(output_directory),
            "P12_OWNER_SCOPED_PROXY_KEY": "sk-preflight-placeholder-only",
            "P12_DEEPSEEK_API_KEY_FILE": str(secret_file),
        })
        prior_proxy = subprocess.run(
            [*compose, "ps", "-q", "litellm-deepseek-staging"],
            capture_output=True, text=True, check=False, env=env, cwd=runtime_dir, timeout=30,
        )
        if prior_proxy.returncode != 0:
            raise RuntimeError("staging Proxy state could not be checked")
        staging_started_by_run = not bool(prior_proxy.stdout.strip())
        started = subprocess.run(
            [*compose, "up", "--no-build", "--pull", "never", "--detach", "--wait", "--wait-timeout", "180", "postgres", "redis", "litellm-deepseek-staging"],
            capture_output=True, text=True, check=False, env=env, cwd=runtime_dir, timeout=240,
        )
        if started.returncode != 0:
            raise RuntimeError("staging Proxy dependencies did not become healthy")
        # A local owner activation is rechecked against the current policy
        # immediately before native key creation; no cached approval is used.
        _, _, request, policy = _validate_inputs(request_path, policy_path)
        if request.request_id != claim["request_id"] or policy.policy_id != claim["standing_policy_id"]:
            raise RuntimeError("P4 request or P12 policy changed after the durable one-shot claim")
        key_record = _control_call(compose, env, runtime_dir, {
            "operation": "prepare",
            "owner_activation_confirmed": True,
            "research_budget_identity": budget_identity,
            "request_id": request.request_id,
            "standing_policy_id": policy.policy_id,
        })
        key = key_record.get("token")
        expected_alias = "aq-p12-owner-once-" + hashlib.sha256(
            (request.request_id + ":key").encode("ascii")
        ).hexdigest()[:20]
        if (
            key_record.get("classification") != "OWNER_ONESHOT_NATIVE_KEY_READY"
            or not isinstance(key, str) or not key.startswith("sk-")
            or key_record.get("user_id") != user_id
            or key_record.get("user_budget_usd") != 5.0
            or key_record.get("user_spend_usd") != 0.0
            or key_record.get("key_alias") != expected_alias
            or key_record.get("key_budget_usd") > 5.0
            or key_record.get("budget_duration") is not None
            or key_record.get("max_parallel_requests") != 1
            or key_record.get("models") != list(OWNER_ONESHOT_MODELS)
        ):
            raise RuntimeError("native experiment user/key state did not match the approved one-shot")
        dispatch = {
            **claim,
            "state": "DISPATCHING_OWNER_ONESHOT",
            "key_alias": expected_alias,
            "key_expiry": key_record.get("expires"),
            "native_user_budget_usd": 5.0,
            "native_key_budget_usd": key_record.get("key_budget_usd"),
            "native_user_id": user_id,
            "real_dispatch_permission": "LOCAL_INTERACTIVE_OWNER_CONFIRMED",
        }
        p12._durable_json_create(p12._dispatch_file(state_dir, request.request_id), dispatch)
        dispatched = True
        env["P12_OWNER_SCOPED_PROXY_KEY"] = key
        worker_name = run_namespace + "-finquant"
        worker = subprocess.run(
            [*compose, "run", "--no-deps", "--name", worker_name, "rdagent-owner-oneshot-worker"],
            capture_output=True, text=True, check=False, env=env, cwd=runtime_dir,
            timeout=policy.maximum_runtime_seconds,
        )
        _redact_persisted_selector_logs(output_directory)
        _durable_output_write(output_directory, "rdagent.stdout.redacted.log", _redact_diagnostics(worker.stdout, (key,)))
        _durable_output_write(output_directory, "rdagent.stderr.redacted.log", _redact_diagnostics(worker.stderr, (key,)))
        worker_record = _verify_container(worker_name, key, output_directory, run_namespace)
        if worker_record["return_code"] != worker.returncode:
            raise RuntimeError("Compose return code differs from native worker exit code")
        blocked = _control_call(compose, env, runtime_dir, {"operation": "block", "token": key})
        if blocked.get("classification") != "OWNER_ONESHOT_KEY_BLOCKED" or blocked.get("blocked") is not True:
            keep_lock = True
            raise RuntimeError("native one-shot key revocation was not verified")
        key_blocked = True
        removed = subprocess.run(
            ["docker", "container", "rm", worker_name],
            capture_output=True, text=True, check=False,
            env=_safe_host_environment(), timeout=30,
        )
        if removed.returncode != 0:
            keep_lock = True
            raise RuntimeError("one-shot worker container cleanup was not verified")
        if staging_started_by_run:
            stopped = subprocess.run(
                [*compose, "stop", "litellm-deepseek-staging"],
                capture_output=True, text=True, check=False, env=env, cwd=runtime_dir, timeout=60,
            )
            if stopped.returncode != 0:
                keep_lock = True
                raise RuntimeError("temporary staging Proxy could not be stopped")
            staging_stopped = True
        terminal = {
            **dispatch,
            "state": "SUCCEEDED_OWNER_ONESHOT" if worker.returncode == 0 else "FAILED_OWNER_ONESHOT",
            "target_return_code": worker.returncode,
            "candidate_count": 0,
            "candidate_status": "NOT_MATERIALIZED",
            "p2_status": "NOT_EVALUATED_NO_CANDIDATE",
            "p4_lifecycle_status": "NOT_EVALUATED",
            "broker_actions": 0,
            "sealed_oos_accessed": False,
            "worker_identity_verified": True,
            "network_isolation_verified": True,
            "read_only_us_pit_mounts_verified": True,
            "chat_max_tokens": 8192,
            "native_user_budget_usd": 5.0,
            "native_key_budget_usd": key_record["key_budget_usd"],
            "native_user_spend_usd": blocked["spend"],
            "key_blocked_after_attempt": True,
        }
        p12._durable_json_create(p12._status_file(state_dir, request.request_id), terminal)
        return ({"classification": terminal["state"], "request_id": request.request_id, "status": terminal, "dispatch_count_added": 1}, 0 if worker.returncode == 0 else EXIT_FAILED)
    except subprocess.TimeoutExpired:
        keep_lock = True
        worker_name = locals().get("worker_name")
        if worker_name:
            try:
                subprocess.run(
                    ["docker", "container", "stop", "--time", "30", worker_name],
                    capture_output=True, text=True, check=False,
                    env=_safe_host_environment(), timeout=45,
                )
            except Exception:
                pass
        return ({"classification": "BLOCKED_OWNER_ONESHOT_RUNTIME_AMBIGUOUS", "request_id": request.request_id, "dispatch_count_added": 0}, EXIT_BLOCKED)
    except Exception as exc:
        keep_lock = dispatched
        classification = "BLOCKED_OWNER_ONESHOT_UNKNOWN_DISPATCH" if dispatched else "FAILED_OWNER_ONESHOT_BEFORE_DISPATCH"
        try:
            _durable_output_write(output_directory, "p12-target-failure.json", json.dumps({"classification": classification, "error_type": type(exc).__name__}, sort_keys=True) + "\n")
        except Exception:
            pass
        return ({"classification": classification, "request_id": request.request_id, "dispatch_count_added": 0}, EXIT_BLOCKED if dispatched else EXIT_FAILED)
    finally:
        if key is not None and not key_blocked:
            try:
                blocked = _control_call(compose, env, runtime_dir, {"operation": "block", "token": key})
                if blocked.get("classification") != "OWNER_ONESHOT_KEY_BLOCKED" or blocked.get("blocked") is not True:
                    keep_lock = True
            except Exception:
                keep_lock = True
        if staging_started_by_run and not staging_stopped:
            try:
                stopped = subprocess.run(
                    [*_compose_args(env_file), "stop", "litellm-deepseek-staging"],
                    capture_output=True, text=True, check=False,
                    env=_safe_host_environment({"P12_DEEPSEEK_API_KEY_FILE": str(secret_file)}),
                    cwd=runtime_dir, timeout=60,
                )
                if stopped.returncode != 0:
                    keep_lock = True
            except Exception:
                keep_lock = True
        if not keep_lock:
            _release_run_lock(state_dir, lock_fd)
        else:
            os.close(lock_fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "run"):
        command = sub.add_parser(name)
        command.add_argument("--request", type=Path, required=True)
        command.add_argument("--policy", type=Path, required=True)
        command.add_argument("--compose-env-file", type=Path, default=Path(PERSISTENT_LITELLM_ENV_FILE))
        if name == "run":
            command.add_argument("--state-dir", type=Path, required=True, help="the existing P12 durable state directory for this request")
            command.add_argument("--runtime-dir", type=Path, default=Path("/mnt/d/AQ/OPERATIONS/P12/owner-one-shot-runtime"))
            command.add_argument("--new-provider-secret-file", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            _, _, _, policy = _validate_inputs(args.request, args.policy)
            result = _preflight(args.compose_env_file)
            result["standing_policy_id"] = policy.policy_id
            print(json.dumps(result, sort_keys=True))
            return 0
        result, code = run_one_shot(
            args.request, args.policy, args.state_dir, args.runtime_dir,
            args.compose_env_file, args.new_provider_secret_file,
        )
        print(json.dumps(result, sort_keys=True))
        return code
    except Exception as exc:
        print(json.dumps({"classification": "DENIED_OWNER_ONESHOT_PREFLIGHT", "error_type": type(exc).__name__, "real_dispatch_permission": "DENIED"}, sort_keys=True), file=sys.stderr)
        return EXIT_BLOCKED


if __name__ == "__main__":
    raise SystemExit(main())
