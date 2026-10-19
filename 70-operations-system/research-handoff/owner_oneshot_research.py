"""Thin interactive adapter for one owner-initiated P12 fin_quant run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
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
    PINNED_FINQUANT_IMAGE,
    PINNED_FINQUANT_IMAGE_ID,
    PERSISTENT_LITELLM_ENV_FILE,
    PERSISTENT_LITELLM_PROJECT,
    run_docker_rdagent_owner_oneshot,
)

MAX_POLICY_LIFETIME = timedelta(hours=24)
OWNER_MODEL_ROUTES = frozenset({
    ("deepseek", "deepseek/deepseek-flash", "PAID"),
    ("ollama", "ollama/qwen3-embedding:0.6b", "LOCAL"),
})
EXIT_BLOCKED = 3


def _json(path: Path) -> dict[str, Any]:
    return p12._read_json_nofollow(path)


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
    effective, expires = policy.effective_at.astimezone(timezone.utc), policy.expires_at.astimezone(timezone.utc)
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


def _safe_host_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "HOME": os.path.expanduser("~")}
    for name in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "XDG_RUNTIME_DIR"):
        if os.environ.get(name):
            env[name] = os.environ[name]
    if extra:
        env.update(extra)
    return env


def _compose_args(env_file: Path) -> list[str]:
    return [
        "docker", "compose", "--project-name", PERSISTENT_LITELLM_PROJECT,
        "--env-file", str(env_file), "--file", str(SMOKE / "compose.persistent-test.yaml"),
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
    result = subprocess.run([
        "docker", "run", "--rm", "--network", "none", "--read-only", "--user", "10001:10001",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--env", "LITELLM_CHAT_MAX_TOKENS=8192",
        "--env", "LITELLM_CHAT_MODEL=openai/deepseek/deepseek-flash", "--env", "LITELLM_CHAT_MODEL_MAP={}",
        "--entrypoint", "python", PINNED_FINQUANT_IMAGE, "-c", probe,
    ], capture_output=True, text=True, check=False, env=_safe_host_environment(), timeout=90)
    if result.returncode != 0:
        raise ValueError("pinned RD-Agent token-bound runtime probe failed")
    observed = json.loads(result.stdout.strip().splitlines()[-1])
    if observed != {"chat_model": "openai/deepseek/deepseek-flash", "max_tokens": 8192, "chat_model_map": {}, "native_retries": 0}:
        raise ValueError("pinned RD-Agent chat token bound was not effective")
    return True


def _new_provider_secret_path(path: Path) -> Path:
    resolved = path.resolve(strict=True)
    root = Path("/mnt/d/AQ/OPERATIONS/P12").resolve(strict=True)
    if not resolved.is_file() or not resolved.is_relative_to(root) or resolved.is_relative_to(REPO_ROOT.resolve()):
        raise ValueError("new provider secret must be owner-managed under D:/AQ/OPERATIONS/P12 and outside the repository")
    return resolved


def _preflight(env_file: Path, provider_secret_file: Path | None = None) -> dict[str, Any]:
    if not env_file.is_file():
        raise ValueError("owner-managed persistent Compose env file is missing")
    if any(not Path(source).is_dir() for source in FINQUANT_DATA_MOUNTS.values()):
        raise ValueError("approved frozen US/PIT read-only inputs are missing")
    image = subprocess.run(["docker", "image", "inspect", "--format", "{{.Id}}", PINNED_FINQUANT_IMAGE], capture_output=True, text=True, check=False, env=_safe_host_environment(), timeout=30)
    if image.returncode != 0 or image.stdout.strip() != PINNED_FINQUANT_IMAGE_ID:
        raise ValueError("the pinned RD-Agent/Qlib image is missing or has a different identity")
    token_bound = _verify_pinned_chat_token_bound()
    env = _safe_host_environment({
        "P12_RUN_NAMESPACE": "aq-p12-owner-000000000000",
        "P12_FINQUANT_OUTPUT_DIR": "/mnt/d/AQ/OPERATIONS/P12/finquant-output/preflight/preflight",
        "P12_OWNER_SCOPED_PROXY_KEY": "sk-preflight-placeholder-only",
        "P12_DEEPSEEK_API_KEY_FILE": str(provider_secret_file or Path("/dev/null")),
        "LITELLM_DEEPSEEK_STAGING_MASTER_KEY": "sk-preflight-placeholder-only",
        "P12_OLLAMA_API_BASE": "http://127.0.0.1:11434",
        "LITELLM_MASTER_KEY": "sk-preflight-test-only-placeholder",
        "P3_TEST_PROXY_KEY": "sk-test-preflight-placeholder",
        "POSTGRES_PASSWORD": "preflight-only-placeholder",
        "P12_LITELLM_STATE_DIR": "/tmp/p12-preflight-state",
    })
    checked = subprocess.run([*_compose_args(env_file), "config", "--quiet"], capture_output=True, text=True, check=False, env=env, timeout=60)
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


def run_one_shot(request_path: Path, policy_path: Path, state_dir: Path, runtime_dir: Path, env_file: Path, provider_secret_file: Path) -> tuple[dict[str, Any], int]:
    envelope, _, request, policy = _validate_inputs(request_path, policy_path)
    replay = p12.owner_oneshot_replay_if_claimed(envelope, state_dir=state_dir, policy_id=policy.policy_id)
    if replay is not None:
        return replay
    secret = _new_provider_secret_path(provider_secret_file)
    _preflight(env_file, secret)
    if not sys.stdin.isatty():
        return ({"classification": "DENIED_INTERACTIVE_OWNER_TTY_REQUIRED", "real_dispatch_permission": "DENIED", "dispatch_count_added": 0}, EXIT_BLOCKED)
    phrase = f"RUN $5 ONCE {request.request_id}"
    print(
        "Review before confirming: "
        f"scope={request.asset_universe_scope_identity}; families={','.join(request.allowed_research_families)}; "
        "models=DeepSeek Flash + local Ollama; total cap=USD 5.00; "
        f"policy expires={policy.expires_at.isoformat()}; runs=1; concurrency=1; P2/trading authority=none."
    )
    try:
        response = input(f"To activate exactly one run, type: {phrase}\n> ")
    except EOFError:
        response = ""
    if response != phrase:
        return ({"classification": "DENIED_OWNER_ACTIVATION_NOT_CONFIRMED", "real_dispatch_permission": "DENIED", "dispatch_count_added": 0}, EXIT_BLOCKED)
    current, _, current_request, current_policy = _validate_inputs(request_path, policy_path)
    if current_request.request_id != request.request_id or current_policy.policy_id != policy.policy_id:
        return ({"classification": "BLOCKED_OWNER_ONESHOT_INPUT_CHANGED", "dispatch_count_added": 0}, EXIT_BLOCKED)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    if runtime_dir.resolve() == REPO_ROOT or REPO_ROOT in runtime_dir.resolve().parents:
        return ({"classification": "DENIED_RUNTIME_DIRECTORY_INSIDE_REPOSITORY", "dispatch_count_added": 0}, EXIT_BLOCKED)

    def target(attempt_id: str) -> dict[str, Any]:
        return run_docker_rdagent_owner_oneshot(
            request_id=request.request_id,
            attempt_id=attempt_id,
            runtime_directory=runtime_dir,
            research_budget_identity=request.research_budget_identity,
            standing_policy_id=policy.policy_id,
            env_file=env_file,
            provider_secret_file=secret,
            maximum_runtime_seconds=policy.maximum_runtime_seconds,
        )

    return p12.process_owner_oneshot(
        current, state_dir=state_dir, policy_id=current_policy.policy_id,
        owner_confirmed=True, target=target,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "run"):
        command = sub.add_parser(name)
        command.add_argument("--request", type=Path, required=True)
        command.add_argument("--policy", type=Path, required=True)
        command.add_argument("--compose-env-file", type=Path, default=Path(PERSISTENT_LITELLM_ENV_FILE))
        if name == "run":
            command.add_argument("--state-dir", type=Path, required=True)
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
        result, code = run_one_shot(args.request, args.policy, args.state_dir, args.runtime_dir, args.compose_env_file, args.new_provider_secret_file)
        print(json.dumps(result, sort_keys=True))
        return code
    except Exception as exc:
        print(json.dumps({"classification": "DENIED_OWNER_ONESHOT_PREFLIGHT", "error_type": type(exc).__name__, "real_dispatch_permission": "DENIED"}, sort_keys=True), file=sys.stderr)
        return EXIT_BLOCKED


if __name__ == "__main__":
    raise SystemExit(main())
