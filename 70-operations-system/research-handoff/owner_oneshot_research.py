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
import owner_bootstrap_request as bootstrap  # noqa: E402
import owner_research_request as owner_request  # noqa: E402
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
OWNER_RESEARCH_RESOURCE_CAPS = {
    "maximum_runtime_seconds": 3600,
    "maximum_memory_mb": 4096,
    "maximum_storage_bytes": 100_000_000_000,
}
OWNER_MODEL_ROUTES = frozenset({
    ("deepseek", "deepseek/deepseek-flash", "PAID"),
    ("ollama", "ollama/qwen3-embedding:0.6b", "LOCAL"),
})
EXIT_BLOCKED = 3
BOOTSTRAP_POLICY_NAME = "owner-initial-bootstrap-policy.json"
BOOTSTRAP_REVIEW_ROOT = Path("/mnt/d/AQ/OPERATIONS/P12/owner-bootstrap-review")
OWNER_RESEARCH_REVIEW_ROOT = Path("/mnt/d/AQ/OPERATIONS/P12/owner-research-review")


def _json(path: Path) -> dict[str, Any]:
    return p12._read_json_nofollow(path)


def _parse_request_envelope(envelope: dict[str, Any]):
    if set(envelope) == {"p4_decision", "research_request"}:
        decision = p4.LifecycleDecisionEvidenceV1.model_validate(envelope["p4_decision"])
        request = p4.ResearchRequestV1.model_validate(envelope["research_request"])
        if (
            decision.decision_kind != p4.DecisionKind.CHALLENGER_NEEDED
            or decision.evidence_classification != "REAL_EXTERNAL_EVIDENCE"
            or decision.reason.value != request.reason.value
            or decision.source_evidence_identities != request.source_evidence_identities
        ):
            raise ValueError("P4 decision is synthetic or does not match ResearchRequestV1")
        return p12.P4_LIFECYCLE_ORIGIN, decision, request
    if set(envelope) == {"bootstrap_request"}:
        request = bootstrap.validate_owner_bootstrap_envelope(envelope)
        bootstrap.verify_current_frozen_inputs(request, REPO_ROOT)
        return p12.OWNER_BOOTSTRAP_ORIGIN, None, request
    if set(envelope) == {"owner_research_request"}:
        request = owner_request.validate_owner_research_envelope(envelope)
        owner_request.verify_current_frozen_inputs(request, REPO_ROOT)
        return p12.OWNER_RESEARCH_ORIGIN, None, request
    raise ValueError("request must be an exact P4 lifecycle, bootstrap, or owner research envelope")


def _validate_policy_object(policy: Any, request: Any, now: datetime | None = None):
    policy = standing_policy.P12StandingResearchPolicyV1.model_validate(policy.model_dump(mode="json") if hasattr(policy, "model_dump") else policy)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    effective, expires = policy.effective_at.astimezone(timezone.utc), policy.expires_at.astimezone(timezone.utc)
    routes = frozenset((route.provider, route.model, route.billing_class) for route in policy.allowed_llm_routes)
    owner_research_over_cap = getattr(request, "request_origin", None) == p12.OWNER_RESEARCH_ORIGIN and any(
        getattr(policy, field) > maximum
        for field, maximum in OWNER_RESEARCH_RESOURCE_CAPS.items()
    )
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
        or owner_research_over_cap
        or routes != OWNER_MODEL_ROUTES
        or policy.research_budget_identity != request.research_budget_identity
        or policy.allowed_universe_scope_identities != (request.asset_universe_scope_identity,)
        or policy.allowed_request_provenance_identities != (request.request_provenance,)
        or policy.allowed_research_families != tuple(request.allowed_research_families)
    ):
        raise ValueError("P12 owner policy does not match the bounded one-shot scope")
    return policy


def _validate_inputs(request_path: Path, policy_path: Path | None, now: datetime | None = None):
    envelope = _json(request_path)
    origin, decision, request = _parse_request_envelope(envelope)
    if policy_path is None:
        if origin not in {p12.OWNER_BOOTSTRAP_ORIGIN, p12.OWNER_RESEARCH_ORIGIN}:
            raise ValueError("P4 lifecycle input requires its separately approved policy")
        return envelope, decision, request, None
    policy = _validate_policy_object(_json(policy_path), request, now)
    return envelope, decision, request, policy


def _prepare_bootstrap_review_package(output_dir: Path) -> dict[str, Any]:
    output_resolved = output_dir.resolve()
    if not output_resolved.is_relative_to(BOOTSTRAP_REVIEW_ROOT.resolve()) or output_resolved == BOOTSTRAP_REVIEW_ROOT.resolve():
        raise ValueError("bootstrap review package must be stored in the isolated P12 review directory")
    inputs = bootstrap.collect_frozen_us_pit_inputs(REPO_ROOT)
    request = bootstrap.build_owner_bootstrap_request(inputs)
    output_dir.mkdir(parents=True, exist_ok=False)
    request_path = output_dir / "owner-initial-bootstrap-request.json"
    review_path = output_dir / "owner-review.json"
    envelope = {"bootstrap_request": request.model_dump(mode="json")}
    review = {
        "package_version": "P12OwnerBootstrapReviewV1",
        "approval_status": "REVIEW_ONLY_NOT_APPROVED",
        "human_approved": False,
        "request_id": request.request_id,
        "research_budget_identity": request.research_budget_identity,
        "request_origin": request.request_origin,
        "scope": request.scope,
        "provider_market": request.provider_market,
        "data_cutoff": request.data_cutoff,
        "input_manifest_identities": [item.model_dump(mode="json") for item in request.input_manifest_identities],
        "research_family": "RD_AGENT",
        "native_command_after_explicit_owner_activation": "rdagent fin_quant --loop-n 1",
        "research_budget_usd_total_nonresetting": request.maximum_total_spend_usd,
        "budget_duration": request.budget_duration,
        "permitted_routes": list(request.permitted_llm_routes),
        "authorization_lifetime_hours": request.authorization_lifetime_hours,
        "maximum_research_runs": request.maximum_research_runs,
        "maximum_concurrent_runs": request.maximum_concurrent_runs,
        "p2_certification_authority": "NONE",
        "trading_authority": "NONE",
        "p4_lifecycle_evidence": "NOT_ASSERTED_OR_REQUIRED_FOR_INITIAL_BOOTSTRAP",
        "policy_materialized": False,
        "paid_key_created": False,
        "real_dispatch_permission": "DENIED",
    }
    p12._durable_json_create(request_path, envelope)
    p12._durable_json_create(review_path, review)
    return {"classification": review["approval_status"], "request_id": request.request_id,
            "request_path": str(request_path), "review_path": str(review_path),
            "paid_key_created": False, "real_dispatch_permission": "DENIED"}


def _prepare_owner_research_review_package(output_dir: Path, research_objective: str) -> dict[str, Any]:
    output_resolved = output_dir.resolve()
    review_root = OWNER_RESEARCH_REVIEW_ROOT.resolve()
    if not output_resolved.is_relative_to(review_root) or output_resolved == review_root:
        raise ValueError("owner research review package must stay in the isolated P12 review directory")
    inputs = bootstrap.collect_frozen_us_pit_inputs(REPO_ROOT)
    request = owner_request.build_owner_research_request(inputs, research_objective)
    output_dir.mkdir(parents=True, exist_ok=False)
    envelope_path = output_dir / "owner-research-request.json"
    review_path = output_dir / "owner-review.json"
    envelope = {"owner_research_request": request.model_dump(mode="json")}
    review = {
        "package_version": "P12OwnerResearchReviewV1",
        "approval_status": "REVIEW_ONLY_NOT_APPROVED",
        "human_approved": False,
        "request_id": request.request_id,
        "authorization_identity": request.authorization_identity,
        "research_budget_identity": request.research_budget_identity,
        "request_origin": request.request_origin,
        "research_objective": request.research_objective,
        "scope": request.scope,
        "provider_market": request.provider_market,
        "data_cutoff": request.data_cutoff,
        "input_manifest_identities": [item.model_dump(mode="json") for item in request.input_manifest_identities],
        "research_family": "RD_AGENT",
        "native_command_after_exact_owner_confirmation": "rdagent fin_quant --loop-n 1",
        "research_objective_is_worker_prompt": False,
        "research_budget_usd_total_nonresetting": request.maximum_total_spend_usd,
        "budget_duration": request.budget_duration,
        "permitted_routes": list(request.permitted_llm_routes),
        "authorization_lifetime_hours": request.authorization_lifetime_hours,
        "maximum_research_runs": request.maximum_research_runs,
        "maximum_concurrent_runs": request.maximum_concurrent_runs,
        "p2_certification_authority": "NONE",
        "trading_authority": "NONE",
        "p4_lifecycle_evidence": "NOT_ASSERTED_OR_REQUIRED",
        "authorization_identity_is_approval_evidence": False,
        "paid_key_created": False,
        "real_dispatch_permission": "DENIED",
    }
    p12._durable_json_create(envelope_path, envelope)
    p12._durable_json_create(review_path, review)
    return {"classification": review["approval_status"], "request_id": request.request_id,
            "request_path": str(envelope_path), "review_path": str(review_path),
            "paid_key_created": False, "real_dispatch_permission": "DENIED"}


def _materialize_owner_research_policy_after_confirmation(
    request: Any, *, state_dir: Path, confirmation: str, now: datetime | None = None,
) -> standing_policy.P12StandingResearchPolicyV1:
    expected = f"AUTHORIZE $5 RESEARCH REQUEST {request.request_id}"
    if confirmation != expected:
        raise ValueError("DENIED_OWNER_RESEARCH_CONFIRMATION_MISMATCH")
    if state_dir.resolve() != p12.OWNER_RESEARCH_STATE_DIR.resolve():
        raise ValueError("DENIED_OWNER_RESEARCH_NONCANONICAL_STATE")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    record_id = "sha256:" + hashlib.sha256(rfc8785.dumps({
        "request_id": request.request_id,
        "authorization_identity": request.authorization_identity,
        "approved_at": current.isoformat(),
        "confirmation_method": "LOCAL_INTERACTIVE_TTY_EXACT_REQUEST_PHRASE",
    })).hexdigest()
    fields: dict[str, Any] = {
        "contract_version": "P12StandingResearchPolicyV1",
        "authorization_status": "APPROVED",
        "evidence_classification": "HUMAN_APPROVED",
        "approval_source_identity": "sha256:" + hashlib.sha256(b"AQ:P12:LOCAL_OWNER_INTERACTIVE_TTY:V1").hexdigest(),
        "approval_record_identity": record_id,
        "effective_at": current.isoformat().replace("+00:00", "Z"),
        "expires_at": (current + MAX_POLICY_LIFETIME).isoformat().replace("+00:00", "Z"),
        "revoked_at": None,
        "allowed_universe_scope_identities": [request.asset_universe_scope_identity],
        "allowed_request_provenance_identities": [request.request_provenance],
        "allowed_research_families": ["RD_AGENT"],
        "allowed_llm_routes": [
            {"provider": "deepseek", "model": "deepseek/deepseek-flash", "billing_class": "PAID"},
            {"provider": "ollama", "model": "ollama/qwen3-embedding:0.6b", "billing_class": "LOCAL"},
        ],
        "research_budget_identity": request.research_budget_identity,
        "maximum_period_spend_usd": "5.00",
        "maximum_run_spend_usd": "5.00",
        "spending_reset_window_seconds": 86400,
        "spending_limit_semantics": "TRACKED_SPEND_LIMIT_ONLY",
        "maximum_concurrent_runs": 1,
        "maximum_runtime_seconds": 3600,
        "maximum_memory_mb": 4096,
        "maximum_storage_bytes": 100000000000,
    }
    fields["policy_id"] = standing_policy.policy_identity(fields)
    policy = standing_policy.P12StandingResearchPolicyV1.model_validate(fields)
    path = state_dir / ("owner-research-" + request.request_id.removeprefix("sha256:") + ".policy.json")
    p12._durable_json_create(path, policy.model_dump(mode="json"))
    return policy


def _materialize_bootstrap_policy_after_confirmation(
    request: Any, *, state_dir: Path, confirmation: str, now: datetime | None = None,
) -> standing_policy.P12StandingResearchPolicyV1:
    expected = f"AUTHORIZE INITIAL $5 RUN {request.request_id}"
    if confirmation != expected:
        raise ValueError("DENIED_OWNER_BOOTSTRAP_CONFIRMATION_MISMATCH")
    if state_dir.resolve() != p12.OWNER_BOOTSTRAP_STATE_DIR.resolve():
        raise ValueError("DENIED_OWNER_BOOTSTRAP_NONCANONICAL_STATE")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    record_id = "sha256:" + hashlib.sha256(rfc8785.dumps({
        "request_id": request.request_id,
        "approved_at": current.isoformat(),
        "confirmation_method": "LOCAL_INTERACTIVE_TTY_EXACT_REQUEST_PHRASE",
    })).hexdigest()
    fields: dict[str, Any] = {
        "contract_version": "P12StandingResearchPolicyV1",
        "authorization_status": "APPROVED",
        "evidence_classification": "HUMAN_APPROVED",
        "approval_source_identity": "sha256:" + hashlib.sha256(b"AQ:P12:LOCAL_OWNER_INTERACTIVE_TTY:V1").hexdigest(),
        "approval_record_identity": record_id,
        "effective_at": current.isoformat().replace("+00:00", "Z"),
        "expires_at": (current + MAX_POLICY_LIFETIME).isoformat().replace("+00:00", "Z"),
        "revoked_at": None,
        "allowed_universe_scope_identities": [request.asset_universe_scope_identity],
        "allowed_request_provenance_identities": [request.request_provenance],
        "allowed_research_families": ["RD_AGENT"],
        "allowed_llm_routes": [
            {"provider": "deepseek", "model": "deepseek/deepseek-flash", "billing_class": "PAID"},
            {"provider": "ollama", "model": "ollama/qwen3-embedding:0.6b", "billing_class": "LOCAL"},
        ],
        "research_budget_identity": request.research_budget_identity,
        "maximum_period_spend_usd": "5.00",
        "maximum_run_spend_usd": "5.00",
        "spending_reset_window_seconds": 86400,
        "spending_limit_semantics": "TRACKED_SPEND_LIMIT_ONLY",
        "maximum_concurrent_runs": 1,
        "maximum_runtime_seconds": 3600,
        "maximum_memory_mb": 4096,
        "maximum_storage_bytes": 100000000000,
    }
    fields["policy_id"] = standing_policy.policy_identity(fields)
    policy = standing_policy.P12StandingResearchPolicyV1.model_validate(fields)
    path = state_dir / BOOTSTRAP_POLICY_NAME
    try:
        p12._durable_json_create(path, policy.model_dump(mode="json"))
    except FileExistsError:
        existing = standing_policy.P12StandingResearchPolicyV1.model_validate(_json(path))
        _validate_policy_object(existing, request, current)
        return existing
    return policy


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


def run_one_shot(request_path: Path, policy_path: Path | None, state_dir: Path, runtime_dir: Path, env_file: Path, provider_secret_file: Path) -> tuple[dict[str, Any], int]:
    envelope = _json(request_path)
    origin, _, request = _parse_request_envelope(envelope)
    policy: standing_policy.P12StandingResearchPolicyV1 | None = None
    if origin == p12.OWNER_BOOTSTRAP_ORIGIN:
        if state_dir.resolve() != p12.OWNER_BOOTSTRAP_STATE_DIR.resolve():
            return ({"classification": "DENIED_OWNER_BOOTSTRAP_NONCANONICAL_STATE", "real_dispatch_permission": "DENIED", "dispatch_count_added": 0}, EXIT_BLOCKED)
        if policy_path is not None:
            return ({"classification": "DENIED_BOOTSTRAP_POLICY_MUST_BE_MATERIALIZED_AFTER_CONFIRMATION", "real_dispatch_permission": "DENIED", "dispatch_count_added": 0}, EXIT_BLOCKED)
        persisted_policy = state_dir / BOOTSTRAP_POLICY_NAME
        if persisted_policy.exists():
            policy = _validate_policy_object(_json(persisted_policy), request)
        claim_path = p12._claim_file(state_dir, request.request_id)
        if claim_path.exists() and policy is None:
            return ({"classification": "BLOCKED_OWNER_BOOTSTRAP_POLICY_MISSING_AFTER_CLAIM", "dispatch_count_added": 0}, EXIT_BLOCKED)
    elif origin == p12.OWNER_RESEARCH_ORIGIN:
        if state_dir.resolve() != p12.OWNER_RESEARCH_STATE_DIR.resolve():
            return ({"classification": "DENIED_OWNER_RESEARCH_NONCANONICAL_STATE", "dispatch_count_added": 0}, EXIT_BLOCKED)
        if policy_path is not None:
            envelope, _, request, policy = _validate_inputs(request_path, policy_path)
        else:
            persisted_policy = state_dir / ("owner-research-" + request.request_id.removeprefix("sha256:") + ".policy.json")
            if persisted_policy.exists():
                policy = _validate_policy_object(_json(persisted_policy), request)
                policy_path = persisted_policy
        claim_path = p12._claim_file(state_dir, request.request_id)
        if claim_path.exists() and policy is None:
            return ({"classification": "BLOCKED_OWNER_RESEARCH_POLICY_MISSING_AFTER_CLAIM", "dispatch_count_added": 0}, EXIT_BLOCKED)
    else:
        envelope, _, request, policy = _validate_inputs(request_path, policy_path)
    if policy is not None:
        replay = p12.owner_oneshot_replay_if_claimed(envelope, state_dir=state_dir, policy_id=policy.policy_id)
        if replay is not None:
            return replay
    secret = _new_provider_secret_path(provider_secret_file)
    _preflight(env_file, secret)
    if not sys.stdin.isatty():
        return ({"classification": "DENIED_INTERACTIVE_OWNER_TTY_REQUIRED", "real_dispatch_permission": "DENIED", "dispatch_count_added": 0}, EXIT_BLOCKED)
    phrase = (
        f"AUTHORIZE INITIAL $5 RUN {request.request_id}"
        if origin == p12.OWNER_BOOTSTRAP_ORIGIN else
        f"AUTHORIZE $5 RESEARCH REQUEST {request.request_id}"
        if origin == p12.OWNER_RESEARCH_ORIGIN else f"RUN $5 ONCE {request.request_id}"
    )
    expiry = policy.expires_at.isoformat() if policy is not None else "24 hours after this exact confirmation"
    run_spend_limit = policy.maximum_run_spend_usd if policy is not None else Decimal("5.00")
    runtime_limit = policy.maximum_runtime_seconds if policy is not None else OWNER_RESEARCH_RESOURCE_CAPS["maximum_runtime_seconds"]
    memory_limit = policy.maximum_memory_mb if policy is not None else OWNER_RESEARCH_RESOURCE_CAPS["maximum_memory_mb"]
    storage_limit = policy.maximum_storage_bytes if policy is not None else OWNER_RESEARCH_RESOURCE_CAPS["maximum_storage_bytes"]
    print(
        "Review before confirming: "
        f"origin={origin}; scope={request.asset_universe_scope_identity}; families={','.join(request.allowed_research_families)}; "
        "models=DeepSeek Flash + local Ollama; "
        f"tracked-spend limit=USD {run_spend_limit:.2f} (not a worst-case charge guarantee); "
        f"maximum runtime={runtime_limit}s; memory={memory_limit}MB; "
        f"storage={storage_limit} bytes; policy expires={expiry}; "
        "runs=1; concurrency=1; P2/trading authority=none."
    )
    try:
        response = input(f"To activate exactly one run, type: {phrase}\n> ")
    except EOFError:
        response = ""
    if response != phrase:
        return ({"classification": "DENIED_OWNER_ACTIVATION_NOT_CONFIRMED", "real_dispatch_permission": "DENIED", "dispatch_count_added": 0}, EXIT_BLOCKED)
    current_envelope = _json(request_path)
    current_origin, _, current_request = _parse_request_envelope(current_envelope)
    if current_request.request_id != request.request_id or current_origin != origin:
        return ({"classification": "BLOCKED_OWNER_ONESHOT_INPUT_CHANGED", "dispatch_count_added": 0}, EXIT_BLOCKED)
    if origin == p12.OWNER_BOOTSTRAP_ORIGIN:
        current_policy = _materialize_bootstrap_policy_after_confirmation(
            current_request, state_dir=state_dir, confirmation=response,
        )
        _validate_policy_object(current_policy, current_request)
    elif origin == p12.OWNER_RESEARCH_ORIGIN:
        if policy is None:
            current_policy = _materialize_owner_research_policy_after_confirmation(
                current_request, state_dir=state_dir, confirmation=response,
            )
        else:
            current_envelope, _, current_request, current_policy = _validate_inputs(request_path, policy_path)
            if current_policy.policy_id != policy.policy_id:
                return ({"classification": "BLOCKED_OWNER_ONESHOT_INPUT_CHANGED", "dispatch_count_added": 0}, EXIT_BLOCKED)
        _validate_policy_object(current_policy, current_request)
    else:
        current_envelope, _, current_request, current_policy = _validate_inputs(request_path, policy_path)
        if policy is None or current_policy.policy_id != policy.policy_id:
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
            standing_policy_id=current_policy.policy_id,
            env_file=env_file,
            provider_secret_file=secret,
            maximum_runtime_seconds=current_policy.maximum_runtime_seconds,
        )

    return p12.process_owner_oneshot(
        current_envelope, state_dir=state_dir, policy_id=current_policy.policy_id,
        owner_confirmed=True, target=target,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    review_parser = sub.add_parser("prepare-bootstrap-review")
    review_parser.add_argument("--output-dir", type=Path, required=True)
    owner_review_parser = sub.add_parser("prepare-owner-research-review")
    owner_review_parser.add_argument("--output-dir", type=Path, required=True)
    owner_review_parser.add_argument("--objective", required=True)
    for name in ("preflight", "run"):
        command = sub.add_parser(name)
        command.add_argument("--request", type=Path, required=True)
        command.add_argument("--policy", type=Path)
        command.add_argument("--compose-env-file", type=Path, default=Path(PERSISTENT_LITELLM_ENV_FILE))
        if name == "run":
            command.add_argument("--state-dir", type=Path, required=True)
            command.add_argument("--runtime-dir", type=Path, default=Path("/mnt/d/AQ/OPERATIONS/P12/owner-one-shot-runtime"))
            command.add_argument("--new-provider-secret-file", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare-bootstrap-review":
            result = _prepare_bootstrap_review_package(args.output_dir)
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "prepare-owner-research-review":
            result = _prepare_owner_research_review_package(args.output_dir, args.objective)
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == "preflight":
            envelope, _, request, policy = _validate_inputs(args.request, args.policy)
            result = _preflight(args.compose_env_file)
            result["request_origin"] = (
                p12.OWNER_BOOTSTRAP_ORIGIN if set(envelope) == {"bootstrap_request"}
                else p12.OWNER_RESEARCH_ORIGIN if set(envelope) == {"owner_research_request"}
                else p12.P4_LIFECYCLE_ORIGIN
            )
            result["request_id"] = request.request_id
            result["standing_policy_id"] = policy.policy_id if policy is not None else None
            result["owner_review_only"] = policy is None
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
