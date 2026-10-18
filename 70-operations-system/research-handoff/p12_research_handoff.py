"""Test-only P12 handoff: P4 synthetic request -> durable claim -> opt-in target.

Real dispatch is deliberately not implemented. The default target is a local
inert executable. Explicit TEST_ONLY targets can run either a backend smoke
or one bounded step of the pinned official RD-Agent fin_quant workflow.
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
from datetime import date
from pathlib import Path
from typing import Any

import rfc8785

REPO_ROOT = Path(__file__).resolve().parents[2]
P4_POLICY_DIR = (
    REPO_ROOT
    / "40-certification-system/champion-challenger/p4-residual-thin-policy"
)
sys.path.insert(0, str(P4_POLICY_DIR))
sys.path.insert(0, str(Path(__file__).with_name("docker-rdagent-smoke")))

import aq_p4_policy as p4  # noqa: E402
import standing_policy as policy_gate  # noqa: E402
from native_experiment_budget import experiment_user_id  # noqa: E402

_REQUEST_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TERMINAL_STATES = {"SUCCEEDED_SYNTHETIC", "FAILED_SYNTHETIC"}
_EXIT_INVALID = 2
_EXIT_BLOCKED = 3
_EXIT_FAILED = 4
_EXIT_INTERRUPTED = 86
TARGET_INERT = "INERT_LOCAL_EXECUTABLE"
TARGET_DOCKER_RDAGENT = "DOCKER_RDAGENT_PROXY_MOCK_SMOKE"
TARGET_DOCKER_FINQUANT = "DOCKER_RDAGENT_FINQUANT_TEST_ONLY"
_DOCKER_TARGETS = {TARGET_DOCKER_RDAGENT, TARGET_DOCKER_FINQUANT}
_TARGETS = {TARGET_INERT, *_DOCKER_TARGETS}


def _identity(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def create_synthetic_request() -> dict[str, Any]:
    """Build a valid P4 no-Champion fixture through the existing policy API."""
    source = _identity("p12-synthetic-source-evidence-v1")
    decision = p4.challenger_needed(
        candidate_id=_identity("p12-synthetic-placeholder-candidate-v1"),
        reason=p4.ChallengerReason.NO_CHAMPION,
        current_champion_state=None,
        source_evidence_identities=(source,),
        test_fixture=True,
    )
    request = p4.build_research_request(
        challenger_decision=decision,
        asset_universe_scope_identity=_identity("p12-synthetic-universe-v1"),
        allowed_research_families=("RD_AGENT",),
        research_budget_identity=_identity("NO_SPENDING_AUTHORITY_SYNTHETIC_FIXTURE"),
        target_protocol_context="SYNTHETIC_HANDOFF_ONLY_NO_CERTIFICATION_AUTHORITY",
        evidence_cutoff=date(2026, 10, 17),
        request_provenance=_identity("p12-synthetic-fixture-provenance-v1"),
    )
    return {
        "p4_decision": decision.model_dump(mode="json"),
        "research_request": request.model_dump(mode="json"),
    }


def write_synthetic_request(output_path: Path) -> dict[str, Any]:
    envelope = create_synthetic_request()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _durable_json_create(output_path, envelope)
    return envelope


def write_synthetic_test_policy(request_path: Path, output_path: Path) -> dict[str, Any]:
    _, decision, request = _validate_envelope(request_path)
    if decision.evidence_classification != "TEST_FIXTURE_NOT_REAL_EVIDENCE":
        raise ValueError("synthetic TEST_ONLY policy requires a P4 test fixture")
    policy = policy_gate.create_synthetic_test_policy(request)
    payload = policy.model_dump(mode="json")
    _durable_json_create(output_path, payload)
    return payload


def _canonical_digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _read_json_nofollow(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        chunks: list[bytes] = []
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            chunks.append(block)
        value = json.loads(b"".join(chunks).decode("utf-8"))
    finally:
        os.close(fd)
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _durable_json_create(path: Path, payload: dict[str, Any]) -> None:
    """Create an immutable marker once, flushing file and directory state."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        encoded = data.encode("utf-8")
        offset = 0
        while offset < len(encoded):
            offset += os.write(fd, encoded[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(path.parent)


def _validate_envelope(path: Path) -> tuple[dict[str, Any], p4.LifecycleDecisionEvidenceV1, p4.ResearchRequestV1]:
    envelope = _read_json_nofollow(path)
    if set(envelope) != {"p4_decision", "research_request"}:
        raise ValueError("expected exactly p4_decision and research_request")
    decision = p4.LifecycleDecisionEvidenceV1.model_validate(envelope["p4_decision"])
    request = p4.ResearchRequestV1.model_validate(envelope["research_request"])
    if decision.decision_kind != p4.DecisionKind.CHALLENGER_NEEDED:
        raise ValueError("P4 decision does not request research")
    if decision.reason.value != request.reason.value:
        raise ValueError("P4 decision reason differs from ResearchRequestV1")
    if decision.source_evidence_identities != request.source_evidence_identities:
        raise ValueError("P4 decision evidence differs from ResearchRequestV1")
    if not _REQUEST_ID_RE.fullmatch(request.request_id):
        raise ValueError("request_id format invalid")
    return envelope, decision, request


def _claim_file(state_dir: Path, request_id: str) -> Path:
    if not _REQUEST_ID_RE.fullmatch(request_id):
        raise ValueError("invalid request_id")
    return state_dir / f"{request_id.removeprefix('sha256:')}.claim.json"


def _status_file(state_dir: Path, request_id: str) -> Path:
    if not _REQUEST_ID_RE.fullmatch(request_id):
        raise ValueError("invalid request_id")
    return state_dir / f"{request_id.removeprefix('sha256:')}.terminal.json"


def _dispatch_file(state_dir: Path, request_id: str) -> Path:
    if not _REQUEST_ID_RE.fullmatch(request_id):
        raise ValueError("invalid request_id")
    return state_dir / f"{request_id.removeprefix('sha256:')}.dispatching.json"


def _valid_attempt_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


def _signature_record_matches(
    marker: dict[str, Any],
    *,
    expected_mode: str,
    expected_metadata: dict[str, Any],
    expected_verification: str,
    owner_approval_evidence_identity: str | None,
) -> bool:
    # Pre-signature PR157/158 markers are accepted only as unsigned synthetic
    # evidence. Older PR159 unsigned records used NOT_PROVIDED and no metadata.
    legacy_unsigned = (
        expected_mode == "UNSIGNED_TEST_ONLY"
        and marker.get("signed_authority_mode") is None
        and marker.get("signature_metadata") is None
        and marker.get("owner_approval_evidence_identity") is None
        and marker.get("policy_signature_verification") in (None, "NOT_PROVIDED")
    )
    if legacy_unsigned:
        return True
    return (
        marker.get("signed_authority_mode") == expected_mode
        and marker.get("signature_metadata") == expected_metadata
        and marker.get("policy_signature_verification") == expected_verification
    )


def _target_record_matches(marker: dict[str, Any], target_identity: str) -> bool:
    if marker.get("target_identity") == target_identity:
        return True
    # Existing PR157-159 inert records predate explicit target identities.
    # They stay replayable only as the inert default and can never match Docker.
    return (
        target_identity == TARGET_INERT
        and marker.get("target_identity") is None
        and marker.get("synthetic_dispatch_target") in (None, TARGET_INERT)
    )


def _replay_result(
    claim_path: Path,
    dispatch_path: Path,
    status_path: Path,
    request_id: str,
    request_digest: str,
    research_budget_identity: str,
    native_experiment_user_id: str,
    standing_policy_id: str,
    owner_approval_evidence_identity: str | None,
    signed_authority_mode: str,
    signature_metadata: dict[str, Any],
    policy_signature_verification: str,
    target_identity: str,
) -> dict[str, Any]:
    try:
        claim = _read_json_nofollow(claim_path)
    except Exception as exc:
        return {
            "classification": "BLOCKED_CORRUPT_OR_INCOMPLETE_CLAIM",
            "reason": type(exc).__name__,
            "dispatch_count_added": 0,
        }
    if (
        claim.get("state") != "CLAIMED"
        or claim.get("request_id") != request_id
        or claim.get("request_digest") != request_digest
        or claim.get("research_budget_identity", research_budget_identity) != research_budget_identity
        or claim.get("native_experiment_user_id", native_experiment_user_id) != native_experiment_user_id
        or not _valid_attempt_id(claim.get("attempt_id"))
        or claim.get("standing_policy_id") != standing_policy_id
        or claim.get("policy_admission") != "ADMITTED_SYNTHETIC_TEST_ONLY"
        or claim.get("owner_approval_evidence_identity") != owner_approval_evidence_identity
        or not _target_record_matches(claim, target_identity)
        or not _signature_record_matches(
            claim,
            expected_mode=signed_authority_mode,
            expected_metadata=signature_metadata,
            expected_verification=policy_signature_verification,
            owner_approval_evidence_identity=owner_approval_evidence_identity,
        )
    ):
        return {
            "classification": "BLOCKED_REQUEST_ID_COLLISION_OR_CONTENT_CHANGE",
            "dispatch_count_added": 0,
        }
    if not dispatch_path.exists():
        return {
            "classification": "BLOCKED_CLAIM_WITHOUT_TERMINAL_STATUS",
            "state": "CLAIMED",
            "dispatch_count_added": 0,
        }
    try:
        dispatch_marker = _read_json_nofollow(dispatch_path)
    except Exception as exc:
        return {
            "classification": "BLOCKED_UNKNOWN_POST_DISPATCH_STATE",
            "reason": type(exc).__name__,
            "dispatch_count_added": 0,
        }
    if (
        dispatch_marker.get("state") != "DISPATCHING_SYNTHETIC"
        or dispatch_marker.get("request_id") != request_id
        or dispatch_marker.get("request_digest") != request_digest
        or dispatch_marker.get("research_budget_identity", research_budget_identity) != research_budget_identity
        or dispatch_marker.get("native_experiment_user_id", native_experiment_user_id) != native_experiment_user_id
        or dispatch_marker.get("attempt_id") != claim.get("attempt_id")
        or dispatch_marker.get("dispatch_mode") != "SYNTHETIC_ONLY"
        or dispatch_marker.get("standing_policy_id") != standing_policy_id
        or dispatch_marker.get("policy_admission") != "ADMITTED_SYNTHETIC_TEST_ONLY"
        or dispatch_marker.get("owner_approval_evidence_identity") != owner_approval_evidence_identity
        or not _target_record_matches(dispatch_marker, target_identity)
        or not _signature_record_matches(
            dispatch_marker,
            expected_mode=signed_authority_mode,
            expected_metadata=signature_metadata,
            expected_verification=policy_signature_verification,
            owner_approval_evidence_identity=owner_approval_evidence_identity,
        )
    ):
        return {
            "classification": "BLOCKED_REQUEST_ID_COLLISION_OR_CONTENT_CHANGE",
            "dispatch_count_added": 0,
        }
    if not status_path.exists():
        return {
            "classification": "BLOCKED_UNKNOWN_POST_DISPATCH_STATE",
            "state": dispatch_marker.get("state", "UNKNOWN"),
            "dispatch_count_added": 0,
        }
    try:
        status = _read_json_nofollow(status_path)
    except Exception as exc:
        return {
            "classification": "BLOCKED_UNKNOWN_POST_DISPATCH_STATE",
            "reason": type(exc).__name__,
            "dispatch_count_added": 0,
        }
    if (
        status.get("request_id") != request_id
        or status.get("request_digest") != request_digest
        or status.get("research_budget_identity", research_budget_identity) != research_budget_identity
        or status.get("native_experiment_user_id", native_experiment_user_id) != native_experiment_user_id
        or status.get("attempt_id") != claim.get("attempt_id")
        or status.get("standing_policy_id") != standing_policy_id
        or status.get("policy_admission") != "ADMITTED_SYNTHETIC_TEST_ONLY"
        or status.get("owner_approval_evidence_identity") != owner_approval_evidence_identity
        or not _target_record_matches(status, target_identity)
        or not _signature_record_matches(
            status,
            expected_mode=signed_authority_mode,
            expected_metadata=signature_metadata,
            expected_verification=policy_signature_verification,
            owner_approval_evidence_identity=owner_approval_evidence_identity,
        )
    ):
        return {
            "classification": "BLOCKED_REQUEST_ID_COLLISION_OR_CONTENT_CHANGE",
            "dispatch_count_added": 0,
        }
    terminal_state = status.get("state")
    return_code = status.get("target_return_code")
    return_code_consistent = (
        type(return_code) is int
        and (
            (terminal_state == "SUCCEEDED_SYNTHETIC" and return_code == 0)
            or (terminal_state == "FAILED_SYNTHETIC" and return_code != 0)
        )
    )
    if (
        terminal_state not in _TERMINAL_STATES
        or not return_code_consistent
        or status.get("dispatch_mode") != "SYNTHETIC_ONLY"
        or status.get("real_dispatch_permission") != "DENIED"
        or status.get("candidate_count") != 0
        or status.get("broker_actions") != 0
        or status.get("sealed_oos_accessed") is not False
    ):
        return {
            "classification": "BLOCKED_UNKNOWN_POST_DISPATCH_STATE",
            "state": status.get("state", "UNKNOWN"),
            "dispatch_count_added": 0,
        }
    successful = terminal_state == "SUCCEEDED_SYNTHETIC"
    return {
        "classification": (
            "REPLAY_TERMINAL_NO_DISPATCH"
            if successful
            else "REPLAY_TERMINAL_FAILED_NO_DISPATCH"
        ),
        "state": terminal_state,
        "request_id": status["request_id"],
        "dispatch_count_added": 0,
        "candidate_count": 0,
        "status": status,
    }


def process_synthetic_request(
    request_path: Path,
    state_dir: Path,
    policy_path: Path | None,
    *,
    target_mode: str = "success",
    test_interrupt_after: str | None = None,
    test_before_claim_delay_ms: int = 0,
    signed_approval: dict[str, Any] | None = None,
    trusted_authority: dict[str, Any] | None = None,
    target_identity: str = TARGET_INERT,
    docker_runtime_dir: Path | None = None,
) -> tuple[dict[str, Any], int]:
    if target_mode not in {"success", "failure"}:
        raise ValueError("synthetic target mode must be success or failure")
    if target_identity not in _TARGETS:
        raise ValueError("unsupported TEST_ONLY target")
    if target_identity in _DOCKER_TARGETS and target_mode != "success":
        return (
            {
                "classification": "DENIED_DOCKER_TARGET_MODE_OVERRIDE",
                "real_dispatch_permission": "DENIED",
                "dispatch_count_added": 0,
            },
            _EXIT_BLOCKED,
        )
    if target_identity in _DOCKER_TARGETS:
        if docker_runtime_dir is None:
            return (
                {
                    "classification": "DENIED_DOCKER_RUNTIME_DIRECTORY_MISSING",
                    "real_dispatch_permission": "DENIED",
                    "dispatch_count_added": 0,
                },
                _EXIT_BLOCKED,
            )
        resolved_runtime = docker_runtime_dir.resolve()
        if resolved_runtime == REPO_ROOT or REPO_ROOT in resolved_runtime.parents:
            return (
                {
                    "classification": "DENIED_DOCKER_RUNTIME_MUST_BE_OUTSIDE_REPOSITORY",
                    "real_dispatch_permission": "DENIED",
                    "dispatch_count_added": 0,
                },
                _EXIT_BLOCKED,
            )
    envelope, decision, request = _validate_envelope(request_path)
    if decision.evidence_classification != "TEST_FIXTURE_NOT_REAL_EVIDENCE":
        return (
            {
                "classification": "BLOCKED_NOT_SYNTHETIC_AUTHORITY_UNVERIFIED",
                "request_id": request.request_id,
                "structurally_valid": True,
                "external_authorization": "UNVERIFIED_DENIED",
                "spending_permission": "NOT_PROVEN_DENIED",
                "real_dispatch_permission": "DENIED",
                "dispatch_count_added": 0,
            },
            _EXIT_BLOCKED,
        )

    if policy_path is None:
        return (
            {
                "classification": "DENIED_POLICY_MISSING",
                "request_id": request.request_id,
                "real_dispatch_permission": "DENIED",
                "dispatch_count_added": 0,
            },
            _EXIT_BLOCKED,
        )
    if (signed_approval is None) != (trusted_authority is None):
        return (
            {
                "classification": "DENIED_SIGNED_AUTHORITY_INCOMPLETE",
                "request_id": request.request_id,
                "real_dispatch_permission": "DENIED",
                "dispatch_count_added": 0,
            },
            _EXIT_BLOCKED,
        )
    try:
        policy_value = _read_json_nofollow(policy_path)
    except Exception as exc:
        return (
            {
                "classification": "DENIED_POLICY_UNAVAILABLE_OR_INVALID",
                "error": type(exc).__name__,
                "request_id": request.request_id,
                "real_dispatch_permission": "DENIED",
                "dispatch_count_added": 0,
            },
            _EXIT_BLOCKED,
        )
    test_policy = policy_gate.P12StandingResearchPolicyV1.model_validate(policy_value)
    admission = policy_gate.evaluate_policy_admission(
        request,
        test_policy,
        p4_is_test_fixture=True,
        evidence=policy_gate.synthetic_admission_evidence(
            approval_source_identity=test_policy.approval_source_identity
        ),
        signed_approval=signed_approval,
        trusted_authority=trusted_authority,
    )
    if admission["classification"] != "ADMITTED_SYNTHETIC_TEST_ONLY":
        return (
            {
                "classification": admission["classification"],
                "request_id": request.request_id,
                "real_dispatch_permission": "DENIED",
                "dispatch_count_added": 0,
            },
            _EXIT_BLOCKED,
        )

    request_digest = _canonical_digest(envelope)
    research_budget_identity = request.research_budget_identity
    native_user_id = experiment_user_id(research_budget_identity)
    owner_approval_evidence_identity = admission.get("owner_approval_evidence_identity")
    signed_authority_mode = admission["signed_authority_mode"]
    signature_metadata = admission["signature_metadata"]
    policy_signature_verification = admission["policy_signature_verification"]
    state_dir.mkdir(parents=True, exist_ok=True)
    claim_path = _claim_file(state_dir, request.request_id)
    dispatch_path = _dispatch_file(state_dir, request.request_id)
    status_path = _status_file(state_dir, request.request_id)
    claim = {
        "state": "CLAIMED",
        "request_id": request.request_id,
        "request_digest": request_digest,
        "research_budget_identity": research_budget_identity,
        "native_experiment_user_id": native_user_id,
        "attempt_id": str(uuid.uuid4()),
        "dispatch_mode": "SYNTHETIC_ONLY",
        "real_dispatch_permission": "DENIED",
        "spending_permission": "NOT_PROVEN_DENIED",
        "standing_policy_id": test_policy.policy_id,
        "policy_admission": admission["classification"],
        "policy_signature_verification": policy_signature_verification,
        "signed_authority_mode": signed_authority_mode,
        "signature_metadata": signature_metadata,
        "owner_approval_evidence_identity": owner_approval_evidence_identity,
        "target_identity": target_identity,
        "synthetic_dispatch_target": target_identity,
    }
    if test_before_claim_delay_ms:
        import time

        time.sleep(test_before_claim_delay_ms / 1000)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(claim_path, flags, 0o600)
    except FileExistsError:
        replay = _replay_result(
            claim_path,
            dispatch_path,
            status_path,
            request.request_id,
            request_digest,
            research_budget_identity,
            native_user_id,
            test_policy.policy_id,
            owner_approval_evidence_identity,
            signed_authority_mode,
            signature_metadata,
            policy_signature_verification,
            target_identity,
        )
        if replay["classification"] == "REPLAY_TERMINAL_NO_DISPATCH":
            return replay, 0
        if replay["classification"] == "REPLAY_TERMINAL_FAILED_NO_DISPATCH":
            return replay, _EXIT_FAILED
        return replay, _EXIT_BLOCKED
    try:
        encoded = json.dumps(claim, sort_keys=True, separators=(",", ":")).encode("utf-8")
        offset = 0
        while offset < len(encoded):
            offset += os.write(fd, encoded[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(state_dir)

    if test_interrupt_after == "claim":
        os._exit(_EXIT_INTERRUPTED)

    status = {
        **claim,
        "state": "DISPATCHING_SYNTHETIC",
        "structurally_valid": True,
        "p4_decision_classification": decision.evidence_classification,
        "external_authorization": "UNVERIFIED_DENIED",
        "spending_permission": "NOT_PROVEN_DENIED",
        "research_budget_identity_is_not_authorization": True,
        "synthetic_dispatch_target": target_identity,
    }
    _durable_json_create(dispatch_path, status)
    if test_interrupt_after == "dispatch-start":
        os._exit(_EXIT_INTERRUPTED)

    target_log = state_dir / f"{request.request_id.removeprefix('sha256:')}.dispatch.jsonl"
    try:
        if target_identity in _DOCKER_TARGETS:
            from docker_rdagent_target import (
                DockerDispatchFailed,
                run_docker_rdagent_proxy_mock_smoke,
                run_docker_rdagent_finquant,
            )

            try:
                if target_identity == TARGET_DOCKER_FINQUANT:
                    docker_evidence = run_docker_rdagent_finquant(
                        request_id=request.request_id,
                        attempt_id=claim["attempt_id"],
                        runtime_directory=resolved_runtime,
                    )
                else:
                    docker_evidence = run_docker_rdagent_proxy_mock_smoke(
                        request_id=request.request_id,
                        attempt_id=claim["attempt_id"],
                        runtime_directory=resolved_runtime,
                    )
                target_return_code = 0
                target_stdout = json.dumps(docker_evidence, sort_keys=True)
                target_stderr = ""
            except DockerDispatchFailed as exc:
                target_return_code = exc.return_code
                target_stdout = json.dumps(exc.evidence, sort_keys=True)
                target_stderr = ""
        else:
            target = Path(__file__).with_name("synthetic_p3_dispatch_target.py")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(target),
                    "--request-id",
                    request.request_id,
                    "--target-log",
                    str(target_log),
                    "--outcome",
                    target_mode,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            target_return_code = completed.returncode
            target_stdout = completed.stdout.strip()
            target_stderr = completed.stderr.strip()
    except Exception as exc:
        # The process may have started before this parent observed an error.
        # Leave DISPATCHING_SYNTHETIC to prevent an unsafe automatic retry.
        detail = (
            str(exc)
            if exc.__class__.__module__ == "docker_rdagent_target"
            else type(exc).__name__
        )
        return (
            {
                "classification": "BLOCKED_UNKNOWN_POST_DISPATCH_STATE",
                "request_id": request.request_id,
                "error": detail,
                "dispatch_count_added": 0,
                "real_dispatch_permission": "DENIED",
            },
            _EXIT_BLOCKED,
        )

    succeeded = target_return_code == 0
    terminal = {
        **status,
        "state": "SUCCEEDED_SYNTHETIC" if succeeded else "FAILED_SYNTHETIC",
        "target_return_code": target_return_code,
        "target_stdout": target_stdout,
        "target_stderr": target_stderr,
        "candidate_count": 0,
        "p2_status": "NOT_EVALUATED_NO_CANDIDATE",
        "p4_lifecycle_status": "NOT_EVALUATED",
        "real_dispatch_permission": "DENIED",
        "broker_actions": 0,
        "sealed_oos_accessed": False,
    }
    _durable_json_create(status_path, terminal)
    return (
        {
            "classification": terminal["state"],
            "request_id": request.request_id,
            "structurally_valid": True,
            "p4_decision_classification": decision.evidence_classification,
            "external_authorization": "UNVERIFIED_DENIED",
            "spending_permission": "NOT_PROVEN_DENIED",
            "real_dispatch_permission": "DENIED",
            "candidate_count": 0,
            "dispatch_count_added": 1,
            "status": terminal,
        },
        0 if succeeded else _EXIT_FAILED,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create-synthetic-request")
    create_parser.add_argument("--output", type=Path, required=True)
    policy_parser = subparsers.add_parser("create-synthetic-test-policy")
    policy_parser.add_argument("--request", type=Path, required=True)
    policy_parser.add_argument("--output", type=Path, required=True)
    process_parser = subparsers.add_parser("process")
    process_parser.add_argument("--request", type=Path, required=True)
    process_parser.add_argument("--policy", type=Path)
    process_parser.add_argument("--state-dir", type=Path, required=True)
    process_parser.add_argument("--synthetic-only", action="store_true")
    process_parser.add_argument("--test-signed-approval", type=Path)
    process_parser.add_argument("--test-trusted-authority", type=Path)
    process_parser.add_argument("--target-mode", choices=("success", "failure"), default="success")
    process_parser.add_argument(
        "--target",
        choices=sorted(_TARGETS),
        default=TARGET_INERT,
        help="TEST_ONLY target; Docker RD-Agent smoke must be explicitly selected.",
    )
    process_parser.add_argument("--docker-runtime-dir", type=Path)
    process_parser.add_argument(
        "--test-interrupt-after", choices=("claim", "dispatch-start"), help=argparse.SUPPRESS
    )
    process_parser.add_argument(
        "--test-before-claim-delay-ms", type=int, default=0, help=argparse.SUPPRESS
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "create-synthetic-request":
            envelope = write_synthetic_request(args.output)
            print(
                json.dumps(
                    {
                        "classification": "P4_SYNTHETIC_TEST_FIXTURE_CREATED",
                        "request_id": envelope["research_request"]["request_id"],
                        "request_provenance": envelope["research_request"]["request_provenance"],
                        "external_authorization": "UNVERIFIED_DENIED",
                        "spending_permission": "NOT_PROVEN_DENIED",
                        "real_dispatch_permission": "DENIED",
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "create-synthetic-test-policy":
            payload = write_synthetic_test_policy(args.request, args.output)
            print(
                json.dumps(
                    {
                        "classification": "TEST_ONLY_STANDING_POLICY_CREATED",
                        "policy_id": payload["policy_id"],
                        "authorization_status": payload["authorization_status"],
                        "evidence_classification": payload["evidence_classification"],
                        "real_dispatch_permission": "DENIED",
                        "real_spending_enforcement": "NOT_PROVEN",
                    },
                    sort_keys=True,
                )
            )
            return 0
        if not args.synthetic_only:
            print(
                json.dumps(
                    {
                        "classification": "BLOCKED_REAL_DISPATCH_DENIED",
                        "real_dispatch_permission": "DENIED",
                        "dispatch_count_added": 0,
                    },
                    sort_keys=True,
                )
            )
            return _EXIT_BLOCKED
        result, exit_code = process_synthetic_request(
            args.request,
            args.state_dir,
            args.policy,
            target_mode=args.target_mode,
            test_interrupt_after=args.test_interrupt_after,
            test_before_claim_delay_ms=args.test_before_claim_delay_ms,
            signed_approval=(
                _read_json_nofollow(args.test_signed_approval)
                if args.test_signed_approval is not None
                else None
            ),
            trusted_authority=(
                _read_json_nofollow(args.test_trusted_authority)
                if args.test_trusted_authority is not None
                else None
            ),
            target_identity=args.target,
            docker_runtime_dir=args.docker_runtime_dir,
        )
        print(json.dumps(result, sort_keys=True))
        return exit_code
    except Exception as exc:
        print(
            json.dumps(
                {
                    "classification": "INVALID_OR_BLOCKED_REQUEST",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "dispatch_count_added": 0,
                    "real_dispatch_permission": "DENIED",
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return _EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
