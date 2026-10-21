"""One TEST_ONLY Docker target for the official RD-Agent proxy/mock smoke."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DockerDispatchAmbiguous(RuntimeError):
    """Docker may have started work but P12 cannot prove its terminal result."""


class DockerDispatchFailed(RuntimeError):
    """The worker completed and returned an observed nonzero result."""

    def __init__(self, return_code: int, evidence: dict[str, Any]):
        super().__init__("RD-Agent native TEST_ONLY smoke completed with failure")
        self.return_code = return_code if return_code else 1
        self.evidence = evidence


_FILES = (
    "compose.yaml",
    "config.yaml",
    "mock_provider.py",
    "Dockerfile.worker",
    "native_smoke.py",
    "provision_test_key.py",
)


def _compose_env(master_key: str, database_password: str, virtual_key: str) -> dict[str, str]:
    # Do not forward the P12 process environment (which may contain credentials).
    env = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": os.path.expanduser("~"),
        "LITELLM_MASTER_KEY": master_key,
        "POSTGRES_PASSWORD": database_password,
        "P3_TEST_PROXY_KEY": virtual_key,
    }
    for name in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "XDG_RUNTIME_DIR"):
        if os.environ.get(name):
            env[name] = os.environ[name]
    return env


def _run(
    command: list[str],
    *,
    env: dict[str, str],
    timeout: int = 180,
    input_text: str | None = None,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        input=input_text,
        env=env,
        cwd=cwd,
        timeout=timeout,
        check=False,
    )


def _json_line(text: str, classification: str) -> dict[str, Any] | None:
    for line in reversed(text.splitlines()):
        try:
            value = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict) and value.get("classification") == classification:
            return value
    return None


def _ensure_cleaned(project: str, env: dict[str, str], cwd: Path) -> None:
    for resource, args in (
        ("container", ["ps", "-aq", "--filter", f"label=com.docker.compose.project={project}"]),
        ("network", ["network", "ls", "-q", "--filter", f"label=com.docker.compose.project={project}"]),
        ("volume", ["volume", "ls", "-q", "--filter", f"label=com.docker.compose.project={project}"]),
    ):
        completed = _run(["docker", *args], env=env, timeout=30, cwd=cwd)
        if completed.returncode != 0 or completed.stdout.strip():
            raise DockerDispatchAmbiguous(f"temporary Compose {resource} cleanup could not be verified")


def run_docker_rdagent_proxy_mock_smoke(
    *, request_id: str, attempt_id: str, runtime_directory: Path
) -> dict[str, Any]:
    """Build and invoke a fresh, bounded Compose smoke, then remove its resources."""
    source_directory = Path(__file__).with_name("docker-rdagent-smoke")
    runtime_directory = runtime_directory.resolve()
    runtime_directory.mkdir(parents=True, exist_ok=True)
    project = "aq-p12-rdagent-" + hashlib.sha256(
        f"{request_id}:{attempt_id}".encode("utf-8")
    ).hexdigest()[:12]
    run_directory = runtime_directory / project
    run_directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in _FILES:
        shutil.copyfile(source_directory / name, run_directory / name)

    master_key = "sk-" + secrets.token_urlsafe(32)
    database_password = secrets.token_urlsafe(32)
    # A placeholder only satisfies Compose interpolation while infrastructure
    # starts. The worker is not started until replaced by a fresh scoped key.
    env = _compose_env(master_key, database_password, "sk-test-key-not-yet-provisioned")
    compose_file = str(run_directory / "compose.yaml")
    compose = ["docker", "compose", "--project-name", project, "--file", compose_file]
    try:
        build = _run([*compose, "build", "rdagent-worker"], env=env, timeout=900, cwd=run_directory)
        if build.returncode != 0:
            raise DockerDispatchAmbiguous("Docker worker image build failed")

        started = _run(
            [*compose, "up", "--detach", "--wait", "--wait-timeout", "180", "litellm"],
            env=env,
            timeout=240,
            cwd=run_directory,
        )
        if started.returncode != 0:
            raise DockerDispatchAmbiguous("Compose dependencies did not become healthy")

        provision = _run(
            [*compose, "exec", "--no-TTY", "litellm", "python", "/app/provision_test_key.py"],
            env=env,
            timeout=30,
            cwd=run_directory,
        )
        # Provisioning emits only a TEST_ONLY virtual key JSON line. Never copy
        # this command output into a durable marker or exception message.
        key_record = _json_line(provision.stdout, "TEST_PROXY_KEY_CREATED")
        if provision.returncode != 0 or not key_record or not isinstance(key_record.get("token"), str):
            raise DockerDispatchAmbiguous("Proxy failed to provision its scoped test key")
        env["P3_TEST_PROXY_KEY"] = key_record["token"]

        worker = _run(
            [*compose, "run", "--rm", "rdagent-worker", "--mode", "native"],
            env=env,
            timeout=240,
            cwd=run_directory,
        )
        worker_evidence = _json_line(worker.stdout, "NATIVE_RDAGENT_PROXY_SMOKE")
        if worker.returncode != 0 or not worker_evidence:
            observed_failure = _json_line(worker.stdout, "EXPECTED_DENIAL")
            if observed_failure is not None:
                raise DockerDispatchFailed(
                    worker.returncode,
                    {"classification": "DOCKER_RDAGENT_SMOKE_FAILED", "worker": observed_failure},
                )
            raise DockerDispatchAmbiguous("Docker worker returned without a verified native result")

        invalid_key_run = _run(
            [*compose, "run", "--rm", "rdagent-worker", "--mode", "invalid-key"],
            env=env,
            timeout=120,
            cwd=run_directory,
        )
        invalid_key_evidence = _json_line(invalid_key_run.stdout, "EXPECTED_DENIAL_INVALID_KEY")
        if invalid_key_run.returncode != 0 or not invalid_key_evidence:
            raise DockerDispatchFailed(
                invalid_key_run.returncode or 1,
                {"classification": "DOCKER_RDAGENT_SMOKE_FAILED_INVALID_KEY_DENIAL"},
            )

        counts_run = _run(
            [
                *compose,
                "exec",
                "--no-TTY",
                "mock",
                "python",
                "-c",
                "import json,urllib.request; print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:8000/counts'))))",
            ],
            env=env,
            timeout=30,
            cwd=run_directory,
        )
        if counts_run.returncode != 0:
            raise DockerDispatchAmbiguous("Mock request counts could not be verified")
        try:
            counts = json.loads(counts_run.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            raise DockerDispatchAmbiguous("Mock request counts were corrupt") from None
        evidence = {
            "classification": "DOCKER_RDAGENT_PROXY_MOCK_SMOKE",
            "worker": worker_evidence,
            "invalid_virtual_key_denied": True,
            "mock_chat_count": counts.get("chat"),
            "mock_embedding_count": counts.get("embedding"),
            "proxy_virtual_key_scope": ["deepseek-chat", "qwen3-embedding:0.6b"],
            "paid_provider_calls": 0,
            "training_runs": 0,
            "broker_actions": 0,
            "sealed_oos_accessed": False,
        }
        if counts != {"chat": 1, "embedding": 1}:
            raise DockerDispatchFailed(
                1,
                {**evidence, "classification": "DOCKER_RDAGENT_SMOKE_FAILED_COUNTS"},
            )
        isolation = worker_evidence.get("isolation", {})
        expected_true = ("public_egress_blocked", "proxy_key_only")
        expected_false = (
            "forbidden_credentials_present",
            "docker_socket_present",
            "host_p3_env_visible",
            "host_drive_visible",
        )
        if (
            worker_evidence.get("chat_mock_marker") is not True
            or worker_evidence.get("embedding_dimension") != 3
            or isolation.get("uid") != 10001
            or any(isolation.get(key) is not True for key in expected_true)
            or any(isolation.get(key) is not False for key in expected_false)
        ):
            raise DockerDispatchFailed(1, {**evidence, "classification": "DOCKER_RDAGENT_SMOKE_FAILED_ISOLATION"})
        return evidence
    finally:
        down = _run(
            [*compose, "down", "--volumes", "--remove-orphans"],
            env=env,
            timeout=120,
            cwd=run_directory,
        )
        if down.returncode != 0:
            details = (down.stderr or down.stdout or "no Docker Compose detail").strip()
            for secret in (master_key, database_password, env.get("P3_TEST_PROXY_KEY", "")):
                if secret:
                    details = details.replace(secret, "[REDACTED]")
            raise DockerDispatchAmbiguous(f"temporary Compose teardown failed: {details[:400]}")
        _ensure_cleaned(project, env, run_directory)


PINNED_FINQUANT_IMAGE = "aq/p3-rdagent-qlib:rdagent-1.0.0-qlib-0.9.8.dev26-v1"
PINNED_FINQUANT_IMAGE_ID = "sha256:f0caceba9e06a618dda72bd999de78c13e34e0773831c8796936c80793e4eea2"
PERSISTENT_LITELLM_PROJECT = "aq-p12-litellm-persistent-test"
PERSISTENT_LITELLM_NETWORK = "aq-p12-litellm-worker-proxy"
PERSISTENT_LITELLM_ENV_FILE = "/mnt/d/AQ/OPERATIONS/P12/persistent-litellm-budget-001/compose.env"
FINQUANT_TEST_ONLY_MAX_BUDGET = "0.1"
FINQUANT_DATA_MOUNTS = {
    "/data/factor-source": "/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source",
    "/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data": "/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data",
    "/mnt/d/AQ_DATA/P2/certification-historical-rehearsal-001/qlib-calendar-runtime": "/mnt/d/AQ_DATA/P2/certification-historical-rehearsal-001/qlib-calendar-runtime",
}
FINQUANT_OUTPUT_ROOT = Path("/mnt/d/AQ/OPERATIONS/P12/finquant-output")


def _persistent_finquant_env(virtual_key: str = "sk-test-key-not-yet-provisioned") -> dict[str, str]:
    """Build a Docker control environment without inheriting provider secrets."""
    env = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": os.path.expanduser("~"),
        "P3_TEST_PROXY_KEY": virtual_key,
        "P12_RUN_NAMESPACE": "p12-test-run-placeholder",
        "P12_FINQUANT_OUTPUT_DIR": "/tmp/p12-finquant-output-placeholder",
    }
    for name in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "XDG_RUNTIME_DIR"):
        if os.environ.get(name):
            env[name] = os.environ[name]
    return env


def _finquant_output_directory(
    request_id: str, attempt_id: str, root: Path | None = None
) -> Path:
    root = FINQUANT_OUTPUT_ROOT if root is None else root
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", request_id):
        raise ValueError("fin_quant output requires a canonical P12 request identity")
    try:
        normalized_attempt = str(uuid.UUID(attempt_id))
    except (ValueError, TypeError, AttributeError):
        raise ValueError("fin_quant output requires a UUID attempt identity") from None

    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    resolved_root = root.resolve(strict=True)
    request_directory = resolved_root / request_id.removeprefix("sha256:")
    request_directory.mkdir(mode=0o700, exist_ok=True)
    output_directory = request_directory / normalized_attempt
    output_directory.mkdir(mode=0o700, exist_ok=False)
    resolved_output = output_directory.resolve(strict=True)
    if not resolved_output.is_relative_to(resolved_root):
        raise ValueError("fin_quant output path escaped its P12 operations root")
    return resolved_output


def _durable_output_write(output_directory: Path, name: str, content: str) -> None:
    destination = output_directory / name
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(destination, flags, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        directory_fd = os.open(output_directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise


def _hash_regular_file(path: Path, root: Path) -> tuple[str, int]:
    resolved_root = root.resolve(strict=True)
    parent = path.parent.resolve(strict=True)
    if not parent.is_relative_to(resolved_root) or parent != path.parent:
        raise ValueError("research evidence path escaped or traversed a symlink")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    digest = hashlib.sha256()
    size = 0
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError("research evidence entry is not a regular file")
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            digest.update(block)
            size += len(block)
    finally:
        os.close(fd)
    return digest.hexdigest(), size


def _native_file_manifest(root: Path, *, suffixes: set[str] | None = None) -> dict[str, Any]:
    """Return path and byte identities only; never read or persist file contents."""
    try:
        root_info = root.lstat()
    except FileNotFoundError:
        return {"status": "UNAVAILABLE", "reason": "SOURCE_DIRECTORY_MISSING", "files": []}
    if stat.S_ISLNK(root_info.st_mode):
        return {"status": "UNAVAILABLE", "reason": "SOURCE_ROOT_SYMLINK", "files": []}
    resolved_root = root.resolve(strict=True)
    if root != resolved_root or not resolved_root.is_dir():
        return {"status": "UNAVAILABLE", "reason": "SOURCE_ROOT_SYMLINK_OR_NOT_DIRECTORY", "files": []}
    entries: list[dict[str, Any]] = []
    try:
        paths = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
        for path in paths:
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ValueError("SYMLINK_IN_RESEARCH_SOURCE")
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("NON_REGULAR_RESEARCH_SOURCE")
            if suffixes is not None and path.suffix.lower() not in suffixes:
                continue
            digest, size = _hash_regular_file(path, root)
            entries.append({
                "relative_path": path.relative_to(root).as_posix(),
                "size_bytes": size,
                "sha256": digest,
            })
    except (OSError, ValueError) as exc:
        return {"status": "UNAVAILABLE", "reason": str(exc), "files": []}
    if not entries:
        return {"status": "UNAVAILABLE", "reason": "NO_ELIGIBLE_REGULAR_FILES", "files": []}
    canonical = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "status": "OBSERVED",
        "files": entries,
        "manifest_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def _sha256_file(path: Path) -> str:
    digest, _ = _hash_regular_file(path, path.parent)
    return digest


def build_native_research_evidence(
    *, request_id: str, attempt_id: str, run_namespace: str,
    output: Path, observed_worker: dict[str, Any], qlib_evidence: dict[str, Any],
    artifact_volume: str, llm_evidence_sha256: str | None = None,
    llm_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a minimal identity manifest from native evidence already inspected."""
    runs = output / "runs" / run_namespace
    trace = _native_file_manifest(runs / "trace")
    workspace = _native_file_manifest(runs / "workspaces", suffixes={".py"})
    source = Path(__file__).with_name("docker-rdagent-smoke")
    config_files = {
        name: _sha256_file(source / name)
        for name in ("compose.persistent-test.yaml", "compose.deepseek-staging.yaml", "config.deepseek-staging.yaml")
    }
    llm_evidence = llm_evidence or {}
    proxy_config_sha = llm_evidence.get("proxy_config_sha256")
    configured_models = llm_evidence.get("configured_allowed_models")
    proxy_identity = {
        "status": (
            "OBSERVED"
            if isinstance(proxy_config_sha, str) and re.fullmatch(r"[0-9a-f]{64}", proxy_config_sha)
            and llm_evidence.get("litellm_proxy_version") == "1.105.1"
            and isinstance(llm_evidence.get("litellm_proxy_image"), str)
            and isinstance(configured_models, list)
            and all(isinstance(model, str) and model for model in configured_models)
            else "UNAVAILABLE"
        ),
        "proxy_config_sha256": proxy_config_sha if isinstance(proxy_config_sha, str) else None,
        "proxy_version": llm_evidence.get("litellm_proxy_version"),
        "proxy_image": llm_evidence.get("litellm_proxy_image"),
        "configured_model_groups": configured_models if isinstance(configured_models, list) else None,
    }
    safe_effective_config = {
        "rdagent_runtime_version": {"status": "CONFIGURED", "value": "1.0.0"},
        "rdagent_source_git_sha": {"status": "CONFIGURED", "value": "484776c211e4fbbeef03e0ec00d6bbee7362a4f4"},
        "qlib_runtime_version": {"status": "CONFIGURED", "value": "0.9.8.dev26"},
        "qlib_source_git_sha": {"status": "CONFIGURED", "value": "2fb9380b342556ddb50a4b24e4fe8655d548b2b8"},
        "worker_image_id_observed": observed_worker.get("image_id"),
        "worker_entrypoint_verified": observed_worker.get("entrypoint_verified") is True,
        "worker_command_verified": observed_worker.get("command_verified") is True,
        "worker_mounts_valid": observed_worker.get("mounts_valid") is True,
        "artifact_volume": artifact_volume,
        "litellm_proxy_configuration": proxy_identity,
        "config_file_sha256": config_files,
        "observed_nonsecret_worker_settings": {
            "chat_max_tokens": 8192,
            "chat_model_map": "{}",
            "workspace_path": f"/workspace/runs/{run_namespace}/workspaces",
        },
    }
    config_bytes = json.dumps(
        safe_effective_config, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    qlib_status = qlib_evidence.get("classification", "RESEARCH_EVIDENCE_INCOMPLETE")
    qlib_identity_complete = (
        qlib_status == "RESEARCH_EVIDENCE_COMPLETE"
        and isinstance(qlib_evidence.get("experiment_id"), str)
        and isinstance(qlib_evidence.get("recorder_id"), str)
        and isinstance(qlib_evidence.get("artifact_manifest"), dict)
    )
    research_identity = {
        "status": "PARTIAL",
        "hypothesis": {"status": "UNAVAILABLE", "reason": "NO_TRUSTED_STRUCTURED_SERIALIZATION_READER"},
        "task_semantics": {"status": "UNAVAILABLE", "reason": "TASK_OBJECT_NOT_SAFELY_EXTRACTED"},
        "experiment_lineage": {"status": "UNAVAILABLE", "reason": "RDAGENT_LINEAGE_NOT_SAFELY_EXTRACTED"},
        "generated_code": {
            "status": "CONTENT_IDENTITIES_ONLY" if workspace["status"] == "OBSERVED" else "UNAVAILABLE",
            "files": workspace["files"],
            "semantic_binding": "UNAVAILABLE",
        },
    }
    return {
        "format_version": "P12_NATIVE_RESEARCH_EVIDENCE_V1",
        "request_id": request_id,
        "attempt_id": attempt_id,
        "provenance_status": "PARTIAL",
        "qlib_research_status": "QLIB_RESEARCH_COMPLETE" if qlib_identity_complete else "QLIB_RESEARCH_INCOMPLETE",
        "qlib": {
            "experiment_id": qlib_evidence.get("experiment_id"),
            "recorder_id": qlib_evidence.get("recorder_id"),
            "recorder_status": qlib_evidence.get("recorder_status"),
            "artifact_volume": artifact_volume,
            "artifact_uri": qlib_evidence.get("artifact_uri"),
            "artifact_manifest": qlib_evidence.get("artifact_manifest", {}),
            "metric_names": qlib_evidence.get("metric_names", []),
        },
        "rdagent_provenance_status": "PARTIAL",
        "rdagent": {
            "runtime_image": PINNED_FINQUANT_IMAGE,
            "runtime_image_id": observed_worker.get("image_id"),
            "trace_manifest": trace,
            "research_identity": research_identity,
        },
        "llm_evidence_status_observed": "COMPLETE" if llm_evidence_sha256 else "PARTIAL",
        "llm_evidence_sha256": llm_evidence_sha256,
        "effective_config_identity": {
            # Some runtime facts are observed above, but the full effective config is
            # not. Keep the aggregate grade configured until every relevant value is
            # independently observed from the running worker.
            "status": "CONFIGURED",
            "sha256": hashlib.sha256(config_bytes).hexdigest(),
            "identity": safe_effective_config,
        },
    }


def _redact_diagnostics(text: str, secrets_to_redact: tuple[str, ...]) -> str:
    for secret in secrets_to_redact:
        if secret:
            text = text.replace(secret, "[REDACTED_TEST_SECRET]")
    text = re.sub(r"(?i)\bsk-[A-Za-z0-9_-]{16,}\b", "[REDACTED_TEST_TOKEN]", text)
    return re.sub(
        r"(?i)(Bearer\s+)[A-Za-z0-9._~+/-]{12,}",
        r"\1[REDACTED_BEARER_TOKEN]",
        text,
    )


def _redact_persisted_selector_logs(output_directory: Path) -> int:
    """Redact plain selector logs without changing signed native artifacts."""
    patterns = (
        re.compile(rb"(?i)\bsk-[A-Za-z0-9_-]{16,}\b"),
        re.compile(rb"(?i)(Bearer\s+)[A-Za-z0-9._~+/-]{12,}"),
    )
    redacted_files = 0
    for path in output_directory.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        if path.name != "selector.log":
            continue
        original = path.read_bytes()
        redacted = original
        for pattern in patterns:
            redacted = pattern.sub(
                lambda match: match.group(1) + b"X" * (len(match.group(0)) - len(match.group(1)))
                if match.lastindex
                else b"X" * len(match.group(0)),
                redacted,
            )
        if redacted == original:
            continue
        descriptor = os.open(path, os.O_WRONLY | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0))
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(redacted)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise
        redacted_files += 1
    if redacted_files:
        directory_fd = os.open(output_directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    return redacted_files


def _persist_failure_record(output_directory: Path, classification: str, message: str) -> None:
    _durable_output_write(
        output_directory,
        "p12-target-failure.json",
        json.dumps({"classification": classification, "message": message}, sort_keys=True) + "\n",
    )


def _compose_json_counts(compose: list[str], env: dict[str, str], cwd: Path) -> dict[str, Any]:
    counts_run = _run(
        [
            *compose,
            "exec",
            "--no-TTY",
            "mock",
            "python",
            "-c",
            "import json,urllib.request; print(json.dumps(json.load(urllib.request.urlopen('http://127.0.0.1:8000/counts'))))",
        ],
        env=env,
        timeout=30,
        cwd=cwd,
    )
    if counts_run.returncode != 0:
        raise DockerDispatchAmbiguous("Mock request counts could not be verified")
    try:
        counts = json.loads(counts_run.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise DockerDispatchAmbiguous("Mock request counts were corrupt") from None
    if (
        not isinstance(counts, dict)
        or set(counts) != {"chat", "embedding"}
        or any(type(counts[key]) is not int or counts[key] < 0 for key in counts)
    ):
        raise DockerDispatchAmbiguous("Mock request counts had an invalid shape")
    return counts


def run_docker_rdagent_finquant(
    *, request_id: str, attempt_id: str, runtime_directory: Path
) -> dict[str, Any]:
    """Run one P12 fin_quant proposal through the persistent TEST_ONLY Proxy."""
    source_directory = Path(__file__).with_name("docker-rdagent-smoke")
    runtime_directory = runtime_directory.resolve()
    runtime_directory.mkdir(parents=True, exist_ok=True)
    run_namespace = "aq-p12-finquant-" + hashlib.sha256(
        f"{request_id}:{attempt_id}".encode("utf-8")
    ).hexdigest()[:12]
    output_directory = _finquant_output_directory(request_id, attempt_id)
    # The trusted host loads persistent control secrets only through Compose's
    # protected external env file. They are not copied into this subprocess env.
    env = _persistent_finquant_env()
    env["P12_RUN_NAMESPACE"] = run_namespace
    env["P12_FINQUANT_OUTPUT_DIR"] = str(output_directory)
    _durable_output_write(
        output_directory,
        "p12-attempt.json",
        json.dumps(
            {
                "request_id": request_id,
                "attempt_id": attempt_id,
                "run_namespace": run_namespace,
                "native_cli_command": "rdagent fin_quant --step-n 1 --loop-n 1",
                "image": PINNED_FINQUANT_IMAGE,
                "image_id": PINNED_FINQUANT_IMAGE_ID,
            },
            sort_keys=True,
        )
        + "\n",
    )
    compose = [
        "docker", "compose", "--project-name", PERSISTENT_LITELLM_PROJECT,
        "--env-file", PERSISTENT_LITELLM_ENV_FILE,
        "--file", str(source_directory / "compose.persistent-test.yaml"),
        "--profile", "p12-test-run",
    ]
    worker_name = run_namespace + "-finquant"
    worker_dispatch_attempted = False
    key_revoked = False
    try:
        image = _run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", PINNED_FINQUANT_IMAGE],
            env=env,
            timeout=30,
            cwd=runtime_directory,
        )
        observed_image_id = image.stdout.strip() if image.returncode == 0 else None
        if observed_image_id != PINNED_FINQUANT_IMAGE_ID:
            raise DockerDispatchFailed(
                image.returncode or 1,
                {
                    "classification": "PINNED_FINQUANT_IMAGE_MISMATCH",
                    "expected_image_id": PINNED_FINQUANT_IMAGE_ID,
                    "observed_image_id": observed_image_id,
                    "worker_launched": False,
                    "paid_provider_calls": 0,
                    "training_runs": 0,
                    "broker_actions": 0,
                    "sealed_oos_accessed": False,
                },
            )

        missing_mounts = [
            f"{target}<-{source}"
            for target, source in FINQUANT_DATA_MOUNTS.items()
            if not Path(source).is_dir()
        ]
        if missing_mounts:
            raise DockerDispatchFailed(
                1,
                {
                    "classification": "PINNED_FINQUANT_DATA_MOUNT_MISSING",
                    "missing_mounts": missing_mounts,
                    "worker_launched": False,
                    "paid_provider_calls": 0,
                    "training_runs": 0,
                    "broker_actions": 0,
                    "sealed_oos_accessed": False,
                },
            )

        compose_check = _run([*compose, "config", "--quiet"], env=env, timeout=30, cwd=runtime_directory)
        if compose_check.returncode != 0:
            raise DockerDispatchFailed(
                compose_check.returncode or 1,
                {
                    "classification": "FINQUANT_COMPOSE_CONFIGURATION_INVALID",
                    "worker_launched": False,
                    "paid_provider_calls": 0,
                    "training_runs": 0,
                    "broker_actions": 0,
                    "sealed_oos_accessed": False,
                },
            )

        started = _run(
            [*compose, "up", "--no-build", "--pull", "never", "--detach", "--wait", "--wait-timeout", "180", "postgres", "redis", "mock", "litellm"],
            env=env, timeout=240, cwd=runtime_directory,
        )
        if started.returncode != 0:
            raise DockerDispatchAmbiguous("persistent Proxy dependencies did not become healthy")

        # Ensure the trusted Proxy can see its core dependencies, but the
        # research worker will receive only the dedicated internal network.
        topology = _run(
            ["docker", "network", "inspect", "--format", "{{.Internal}}", PERSISTENT_LITELLM_NETWORK],
            env=env, timeout=30, cwd=runtime_directory,
        )
        if topology.returncode != 0 or topology.stdout.strip() != "true":
            raise DockerDispatchAmbiguous("persistent worker Proxy network is not verified internal")

        provision = _run(
            [
                *compose, "exec", "--no-TTY", "litellm", "python",
                "/app/provision_test_key.py", "create", FINQUANT_TEST_ONLY_MAX_BUDGET,
                "aq-p12-finquant-test-only-" + run_namespace.removeprefix("aq-p12-finquant-"),
            ],
            env=env, timeout=45, cwd=runtime_directory,
        )
        key_record = _json_line(provision.stdout, "TEST_PROXY_KEY_CREATED")
        if (
            provision.returncode != 0 or not key_record
            or key_record.get("verified") is not True
            or not isinstance(key_record.get("token"), str)
            or key_record.get("key_alias") != "aq-p12-finquant-test-only-" + run_namespace.removeprefix("aq-p12-finquant-")
            or key_record.get("max_budget") != float(FINQUANT_TEST_ONLY_MAX_BUDGET)
            or key_record.get("models") != ["deepseek-chat", "qwen3-embedding:0.6b"]
            or key_record.get("budget_duration") != "1h"
            or key_record.get("duration") != "1h"
            or key_record.get("max_parallel_requests") != 1
        ):
            raise DockerDispatchAmbiguous("Proxy failed to provision its scoped TEST_ONLY key")
        env["P3_TEST_PROXY_KEY"] = key_record["token"]
        env["P12_RUN_NAMESPACE"] = run_namespace
        env["P12_FINQUANT_OUTPUT_DIR"] = str(output_directory)
        counts_before = _compose_json_counts(compose, env, runtime_directory)

        worker_dispatch_attempted = True
        worker = _run(
            [
                *compose,
                "run",
                "--no-deps",
                "--name",
                worker_name,
                "rdagent-finquant-worker",
            ],
            env=env,
            timeout=420,
            cwd=runtime_directory,
        )
        redacted_selector_log_count = _redact_persisted_selector_logs(output_directory)
        redaction_values = (
            env.get("P3_TEST_PROXY_KEY", ""),
        )
        _durable_output_write(
            output_directory,
            "rdagent.stdout.redacted.log",
            _redact_diagnostics(worker.stdout, redaction_values),
        )
        _durable_output_write(
            output_directory,
            "rdagent.stderr.redacted.log",
            _redact_diagnostics(worker.stderr, redaction_values),
        )

        inspect = _run(
            [
                "docker",
                "container",
                "inspect",
                "--format",
                "{{.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.Config.Image}}|{{json .Config.Entrypoint}}|{{json .Config.Cmd}}|{{.Config.User}}|{{.HostConfig.ReadonlyRootfs}}",
                worker_name,
            ],
            env=env,
            timeout=30,
            cwd=runtime_directory,
        )
        if inspect.returncode != 0:
            raise DockerDispatchAmbiguous("Native fin_quant container terminal state could not be inspected")
        try:
            (
                image_id,
                state,
                inspect_return_code,
                configured_image,
                entrypoint,
                command,
                configured_user,
                read_only_root,
            ) = inspect.stdout.strip().split("|", 7)
            inspect_return_code = int(inspect_return_code)
            entrypoint_value = json.loads(entrypoint)
            command_value = json.loads(command)
        except (TypeError, ValueError, json.JSONDecodeError):
            raise DockerDispatchAmbiguous("Native fin_quant container identity was corrupt") from None

        mounts_result = _run(
            ["docker", "container", "inspect", "--format", "{{json .Mounts}}", worker_name],
            env=env,
            timeout=30,
            cwd=runtime_directory,
        )
        env_result = _run(
            ["docker", "container", "inspect", "--format", "{{json .Config.Env}}", worker_name],
            env=env,
            timeout=30,
            cwd=runtime_directory,
        )
        networks_result = _run(
            ["docker", "container", "inspect", "--format", "{{json .NetworkSettings.Networks}}", worker_name],
            env=env,
            timeout=30,
            cwd=runtime_directory,
        )
        if any(result.returncode != 0 for result in (mounts_result, env_result, networks_result)):
            raise DockerDispatchAmbiguous("Native fin_quant isolation could not be inspected")
        try:
            mounts = json.loads(mounts_result.stdout)
            worker_env = dict(value.split("=", 1) for value in json.loads(env_result.stdout) if "=" in value)
            networks = json.loads(networks_result.stdout)
        except (ValueError, TypeError, json.JSONDecodeError):
            raise DockerDispatchAmbiguous("Native fin_quant isolation record was corrupt") from None

        mounted = {mount.get("Destination"): mount for mount in mounts if isinstance(mount, dict)}
        data_mounts_valid = len(mounted) == len(FINQUANT_DATA_MOUNTS) + 1 and all(
            target in mounted
            and mounted[target].get("Source") == source
            and mounted[target].get("RW") is False
            and mounted[target].get("Type") == "bind"
            for target, source in FINQUANT_DATA_MOUNTS.items()
        )
        output_mount = mounted.get("/workspace", {})
        durable_host_mount_valid = (
            output_mount.get("Source") == str(output_directory)
            and output_mount.get("RW") is True
            and output_mount.get("Type") == "bind"
        )
        mounts_valid = data_mounts_valid and durable_host_mount_valid
        expected_env = {
            "OPENAI_API_BASE": "http://litellm:4000/v1",
            "BACKEND": "rdagent.oai.backend.LiteLLMAPIBackend",
            "LITELLM_CHAT_MODEL": "openai/deepseek-chat",
            "LITELLM_EMBEDDING_MODEL": "openai/qwen3-embedding:0.6b",
            "MODEL_COSTEER_ENV_TYPE": "conda",
            "FACTOR_COSTEER_PYTHON_BIN": "/opt/conda/envs/rdagent4qlib/bin/python",
            "FACTOR_COSTEER_DATA_FOLDER": "/data/factor-source/full",
            "FACTOR_COSTEER_DATA_FOLDER_DEBUG": "/data/factor-source/debug",
            "QLIB_QUANT_FACTOR_HYPOTHESIS2EXPERIMENT": "aq_rdagent_official_us_binding.USQlibFactorHypothesis2Experiment",
            "QLIB_QUANT_MODEL_HYPOTHESIS2EXPERIMENT": "aq_rdagent_official_us_binding.USQlibModelHypothesis2Experiment",
            "WORKSPACE_PATH": f"/workspace/runs/{run_namespace}/workspaces",
            "PICKLE_CACHE_FOLDER_PATH_STR": f"/workspace/runs/{run_namespace}/pickle-cache",
            "LOG_TRACE_PATH": f"/workspace/runs/{run_namespace}/trace",
            "QLIB_MLFLOW_URI": f"sqlite:////workspace/runs/{run_namespace}/mlflow.db",
        }
        for prefix in ("QLIB_QUANT", "QLIB_FACTOR", "QLIB_MODEL"):
            expected_env.update(
                {
                    f"{prefix}_TRAIN_START": "2015-01-02",
                    f"{prefix}_TRAIN_END": "2019-12-31",
                    f"{prefix}_VALID_START": "2020-01-02",
                    f"{prefix}_VALID_END": "2021-12-31",
                    f"{prefix}_TEST_START": "2022-01-03",
                    f"{prefix}_TEST_END": "2024-12-31",
                }
            )
        env_valid = (
            all(worker_env.get(name) == value for name, value in expected_env.items())
            and worker_env.get("OPENAI_API_KEY") == worker_env.get("P3_TEST_PROXY_KEY")
            and bool(worker_env.get("P3_TEST_PROXY_KEY"))
            and not any(
                re.search(r"(?i)(?:API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|MASTER_KEY)", name)
                and name not in {"OPENAI_API_KEY", "P3_TEST_PROXY_KEY"}
                for name in worker_env
            )
            and not any(
                name in worker_env
                for name in (
                    "DEEPSEEK_API_KEY",
                    "LITELLM_MASTER_KEY",
                    "POSTGRES_PASSWORD",
                    "OWNER_SIGNING_PRIVATE_KEY",
                )
            )
        )
        expected_command = ["fin_quant", "--step-n", "1", "--loop-n", "1"]
        process_identity_valid = (
            image_id == PINNED_FINQUANT_IMAGE_ID
            and configured_image == PINNED_FINQUANT_IMAGE
            and state == "exited"
            and inspect_return_code == worker.returncode
            and entrypoint_value == ["rdagent"]
            and command_value == expected_command
            and configured_user == "10001:10001"
            and read_only_root == "true"
        )
        internal_network = _run(
            [
                "docker",
                "network",
                "inspect",
                "--format",
                "{{.Internal}}",
                PERSISTENT_LITELLM_NETWORK,
            ],
            env=env,
            timeout=30,
            cwd=runtime_directory,
        )
        if internal_network.returncode != 0:
            raise DockerDispatchAmbiguous("Worker-only Proxy network could not be verified")
        worker_network_valid = (
            internal_network.stdout.strip() == "true"
            and list(networks) == [PERSISTENT_LITELLM_NETWORK]
        )

        counts = _compose_json_counts(compose, env, runtime_directory)
        counts_delta = {
            name: counts[name] - counts_before[name]
            for name in ("chat", "embedding")
        }
        # Verify native persisted per-key spend and prove its enforced limit
        # rejects one excess call before Mock sees it. Revoke the ephemeral
        # TEST_ONLY key immediately afterwards while preserving DB evidence.
        budget_run = _run(
            [*compose, "exec", "--no-TTY", "-e", "P3_TEST_PROXY_KEY", "litellm", "python", "/app/provision_test_key.py", "verify-exhaustion"],
            env=env, timeout=90, cwd=runtime_directory,
        )
        budget_record = _json_line(budget_run.stdout, "TEST_PROXY_BUDGET_ENFORCED")
        if budget_run.returncode != 0 or not budget_record or budget_record.get("excess_denied_before_mock") is not True:
            raise DockerDispatchAmbiguous("native persistent Proxy budget enforcement was not verified")
        revoke = _run(
            [*compose, "exec", "--no-TTY", "-e", "P3_TEST_PROXY_KEY", "litellm", "python", "/app/provision_test_key.py", "block"],
            env=env, timeout=45, cwd=runtime_directory,
        )
        revoke_record = _json_line(revoke.stdout, "TEST_PROXY_KEY_BLOCKED")
        if revoke.returncode != 0 or not revoke_record or revoke_record.get("blocked") is not True:
            raise DockerDispatchAmbiguous("per-run TEST_ONLY key revocation could not be verified")
        key_revoked = True
        combined_output = f"{worker.stdout}\n{worker.stderr}"
        proposal_phase_reached = bool(
            re.search(r"Start Loop\s+0,\s*Step\s+0:\s*direct_exp_gen", combined_output)
        )
        # In the pinned upstream loop, direct_exp_gen is its first workflow
        # step and is entered only after QuantRDLoop has initialized the
        # default QlibQuantScenario and its hypothesis generator.
        scenario_initialized = proposal_phase_reached
        evidence = {
            "classification": "P12_NATIVE_FINQUANT_TEST_ONLY",
            "pinned_image": PINNED_FINQUANT_IMAGE,
            "pinned_image_id": image_id,
            "worker_image_verified": process_identity_valid,
            "native_cli_command": "rdagent fin_quant --step-n 1 --loop-n 1",
            "official_finquant_process_started": process_identity_valid,
            "scenario_initialized": scenario_initialized,
            "scenario_class": "rdagent.scenarios.qlib.experiment.quant_experiment.QlibQuantScenario",
            "us_pit_binding_selected": env_valid,
            "us_pit_data_mounts_read_only": mounts_valid,
            "worker_proxy_network_internal": worker_network_valid,
            "run_namespace": run_namespace,
            "durable_output_path": str(output_directory),
            "durable_host_mount_valid": durable_host_mount_valid,
            "diagnostics_preserved": True,
            "selector_logs_redacted": redacted_selector_log_count,
            "worker_non_root": configured_user == "10001:10001",
            "worker_root_read_only": read_only_root == "true",
            "proposal_phase_reached": proposal_phase_reached,
            "proposal_phase_marker": "Start Loop 0, Step 0: direct_exp_gen" if proposal_phase_reached else None,
            "proxy_mock_request_observed": counts_delta["chat"] > 0 or counts_delta["embedding"] > 0,
            "proxy_mock_chat_count": counts_delta["chat"],
            "proxy_mock_embedding_count": counts_delta["embedding"],
            "proxy_native_scoped_key_verified": True,
            "proxy_key_alias": key_record["key_alias"],
            "proxy_key_models": key_record["models"],
            "proxy_key_synthetic_max_budget": key_record["max_budget"],
            "proxy_key_budget_duration": key_record["budget_duration"],
            "proxy_key_expiration": key_record["duration"],
            "proxy_key_max_parallel_requests": key_record["max_parallel_requests"],
            "proxy_key_revoked_after_attempt": revoke_record["blocked"],
            "native_budget_enforced": budget_record["excess_denied_before_mock"],
            "persistent_proxy_spend": budget_record["spend"],
            "post_exhaustion_mock_counts": budget_record["mock_counts"],
            "worker_return_code": worker.returncode,
            "container_return_code": inspect_return_code,
            "paid_provider_calls": 0,
            "training_runs": 0,
            "certification_runs": 0,
            "candidate_count": 0,
            "broker_actions": 0,
            "sealed_oos_accessed": False,
        }
        _durable_output_write(
            output_directory,
            "p12-target-evidence.json",
            json.dumps(evidence, sort_keys=True) + "\n",
        )
        if not (
            process_identity_valid
            and env_valid
            and mounts_valid
            and worker_network_valid
            and scenario_initialized
            and proposal_phase_reached
            and evidence["proxy_mock_request_observed"]
            and all(value >= 0 for value in counts_delta.values())
            and budget_record["mock_counts_unchanged"] is True
            and budget_record["spend"] > 0
            and evidence["proxy_key_revoked_after_attempt"]
            and worker.returncode == 0
        ):
            raise DockerDispatchFailed(worker.returncode or 1, evidence)
        return evidence
    except DockerDispatchFailed as exc:
        _persist_failure_record(
            output_directory,
            str(exc.evidence.get("classification", "NATIVE_FINQUANT_FAILED")),
            json.dumps(exc.evidence, sort_keys=True),
        )
        raise
    except DockerDispatchAmbiguous as exc:
        _persist_failure_record(output_directory, "NATIVE_FINQUANT_AMBIGUOUS", str(exc))
        raise
    except Exception as exc:
        _persist_failure_record(
            output_directory,
            "NATIVE_FINQUANT_UNEXPECTED_ERROR",
            type(exc).__name__,
        )
        raise DockerDispatchAmbiguous(
            f"Native fin_quant target failed with an unexpected local error ({type(exc).__name__})"
        ) from None
    finally:
        cleanup_error = None
        if env.get("P3_TEST_PROXY_KEY") not in (None, "", "sk-test-key-not-yet-provisioned") and not key_revoked:
            revoke = _run(
                [
                    *compose, "exec", "--no-TTY", "-e", "P3_TEST_PROXY_KEY",
                    "litellm", "python", "/app/provision_test_key.py", "block",
                ],
                env=env, timeout=45, cwd=runtime_directory,
            )
            revoke_record = _json_line(revoke.stdout, "TEST_PROXY_KEY_BLOCKED")
            if revoke.returncode != 0 or not revoke_record or revoke_record.get("blocked") is not True:
                cleanup_error = "per-run TEST_ONLY key cleanup could not be verified"
        if worker_dispatch_attempted:
            remove = _run(
                ["docker", "container", "rm", "--force", worker_name],
                env=env, timeout=120, cwd=runtime_directory,
            )
            if remove.returncode != 0 and "No such container" not in (remove.stderr + remove.stdout):
                cleanup_error = "one-off fin_quant worker cleanup could not be verified"
        if cleanup_error:
            raise DockerDispatchAmbiguous(cleanup_error)


def validate_owner_worker_inspection(
    inspection: dict[str, Any], *, expected_key: str, expected_output: Path,
    run_namespace: str, expected_artifact_volume: str,
    expected_command: tuple[str, ...] = ("fin_quant", "--loop-n", "1"),
) -> dict[str, Any]:
    """Validate the actual profiled worker configuration, including its shell gate."""
    config = inspection.get("Config", {})
    state = inspection.get("State", {})
    host = inspection.get("HostConfig", {})
    entrypoint = config.get("Entrypoint")
    command = config.get("Cmd")
    if not isinstance(entrypoint, list) or len(entrypoint) != 4:
        raise DockerDispatchAmbiguous("Owner worker entrypoint shape was invalid")
    script = entrypoint[2]
    if (
        entrypoint[0:2] != ["/bin/sh", "-ec"] or entrypoint[3] != "--"
        or not isinstance(script, str)
        or 'exec rdagent "$@"' not in script
        or "test -f /workspace/p12-attempt.json" not in script
        or "LITELLM_CHAT_MAX_TOKENS" not in script
        or "LITELLM_CHAT_MODEL_MAP" not in script
        or "owner-scoped paid Proxy key required" not in script
    ):
        raise DockerDispatchAmbiguous("Owner worker shell preflight was missing or bypassed")
    if (
        inspection.get("Image") != PINNED_FINQUANT_IMAGE_ID
        or config.get("Image") != PINNED_FINQUANT_IMAGE
        or state.get("Status") != "exited"
        or type(state.get("ExitCode")) is not int
        or state.get("ExitCode") != inspection.get("expected_return_code", state.get("ExitCode"))
        or tuple(command or ()) != expected_command
        or config.get("User") != "10001:10001"
        or host.get("ReadonlyRootfs") is not True
    ):
        raise DockerDispatchAmbiguous("Owner worker image, command, or terminal identity mismatch")
    environment = dict(
        item.split("=", 1) for item in config.get("Env", [])
        if isinstance(item, str) and "=" in item
    )
    mounts = inspection.get("Mounts")
    networks = inspection.get("NetworkSettings", {}).get("Networks", {})
    if not isinstance(mounts, list) or not isinstance(networks, dict):
        raise DockerDispatchAmbiguous("Owner worker mounts or networks were unavailable")
    if any(not isinstance(item, dict) for item in mounts):
        raise DockerDispatchAmbiguous("Owner worker mount record was invalid")
    mounted = {item.get("Destination"): item for item in mounts if isinstance(item, dict)}
    if len(mounted) != len(mounts):
        raise DockerDispatchAmbiguous("Owner worker had duplicate mount destinations")
    data_mounts_valid = all(
        target in mounted
        and mounted[target].get("Source") == source
        and mounted[target].get("RW") is False
        and mounted[target].get("Type") == "bind"
        for target, source in FINQUANT_DATA_MOUNTS.items()
    )
    output = mounted.get("/workspace", {})
    output_valid = (
        output.get("Source") == str(expected_output.resolve())
        and output.get("RW") is True
        and output.get("Type") == "bind"
    )
    artifact_mount = mounted.get("/qlib-artifacts", {})
    artifact_volume_valid = (
        artifact_mount.get("Name") == expected_artifact_volume
        and artifact_mount.get("RW") is True
        and artifact_mount.get("Type") == "volume"
    )
    sensitive_names = {
        "DEEPSEEK_API_KEY", "LITELLM_DEEPSEEK_STAGING_MASTER_KEY",
        "POSTGRES_PASSWORD", "LITELLM_MASTER_KEY", "OWNER_SIGNING_PRIVATE_KEY",
    }
    if (
        not data_mounts_valid or len(mounted) != len(FINQUANT_DATA_MOUNTS) + 2
        or not output_valid or not artifact_volume_valid
        or list(networks) != [PERSISTENT_LITELLM_NETWORK]
        or environment.get("OPENAI_API_BASE") != "http://litellm-deepseek-staging:4000/v1"
        or environment.get("OPENAI_API_KEY") != expected_key
        or environment.get("P12_OWNER_SCOPED_PROXY_KEY") != expected_key
        or environment.get("LITELLM_CHAT_MAX_TOKENS") != "8192"
        or environment.get("LITELLM_CHAT_MODEL_MAP") != "{}"
        or environment.get("WORKSPACE_PATH") != f"/workspace/runs/{run_namespace}/workspaces"
        or any(name in environment for name in sensitive_names)
    ):
        raise DockerDispatchAmbiguous("Owner worker network, mounts, key, or credential isolation mismatch")
    return {
        "return_code": state["ExitCode"],
        "image_id": inspection["Image"],
        "entrypoint_verified": True,
        "command_verified": True,
        "mounts_valid": True,
        "artifact_volume": expected_artifact_volume,
        "artifact_volume_valid": True,
        "network_valid": True,
        "credential_isolation": True,
    }


def _owner_safe_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": os.path.expanduser("~"),
    }
    for name in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_CONFIG", "XDG_RUNTIME_DIR"):
        if os.environ.get(name):
            env[name] = os.environ[name]
    if extra:
        env.update(extra)
    return env


def _owner_artifact_volume_name(request_id: str, attempt_id: str) -> str:
    if (
        not re.fullmatch(r"sha256:[0-9a-f]{64}", request_id)
        or not re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            attempt_id,
        )
    ):
        raise DockerDispatchAmbiguous("Owner artifact store identity was invalid")
    suffix = hashlib.sha256(f"{request_id}:{attempt_id}".encode()).hexdigest()[:16]
    return "aq-p12-owner-artifacts-" + suffix


def _owner_artifact_container_command(
    *, output: Path, volume: str, tracking_uri: str, helper: str, prepare: bool,
    request_id: str, attempt_id: str,
) -> subprocess.CompletedProcess[str]:
    image_python = "/opt/conda/envs/rdagent4qlib/bin/python"
    return subprocess.run(
        [
            "docker", "run", "--rm", "--network", "none", "--read-only",
            "--user", "10001:10001", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true",
            "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m,uid=10001,gid=10001",
            "--tmpfs", "/home/rdagent:rw,nosuid,nodev,size=64m,uid=10001,gid=10001",
            "--mount", f"type=bind,src={output},dst=/workspace",
            "--mount", f"type=volume,src={volume},dst=/qlib-artifacts",
            "--entrypoint", image_python, PINNED_FINQUANT_IMAGE,
            f"/workspace/{helper}", "--tracking-uri", tracking_uri,
            "--request-id", request_id, "--attempt-id", attempt_id,
            "--artifact-volume", volume,
            *( ["--prepare"] if prepare else [] ),
        ],
        capture_output=True, text=True, env=_owner_safe_environment(), timeout=120,
    )


def run_docker_rdagent_owner_oneshot(
    *, request_id: str, attempt_id: str, runtime_directory: Path,
    research_budget_identity: str, standing_policy_id: str,
    env_file: Path, provider_secret_file: Path, maximum_runtime_seconds: int,
) -> dict[str, Any]:
    """Execute one P12-authorized full native run and return observed evidence."""
    from native_experiment_budget import OWNER_ONESHOT_MODELS

    source = Path(__file__).with_name("docker-rdagent-smoke")
    runtime = runtime_directory.resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    run_namespace = "aq-p12-owner-" + hashlib.sha256(f"{request_id}:{attempt_id}".encode()).hexdigest()[:12]
    output = _finquant_output_directory(request_id, attempt_id)
    artifact_volume = _owner_artifact_volume_name(request_id, attempt_id)
    attempt = {
        "request_id": request_id, "attempt_id": attempt_id,
        "run_namespace": run_namespace, "native_cli_command": "rdagent fin_quant --loop-n 1",
        "image": PINNED_FINQUANT_IMAGE, "image_id": PINNED_FINQUANT_IMAGE_ID,
        "mlflow_artifact_volume": artifact_volume,
        "p2_status": "NOT_EVALUATED_NO_CANDIDATE",
    }
    _durable_output_write(output, "p12-attempt.json", json.dumps(attempt, sort_keys=True) + "\n")
    helper_source = Path(__file__).with_name("docker-rdagent-smoke") / "p12_mlflow_evidence.py"
    helper_name = "p12_mlflow_evidence.py"
    shutil.copyfile(helper_source, output / helper_name)
    compose = [
        "docker", "compose", "--project-name", PERSISTENT_LITELLM_PROJECT,
        "--env-file", str(env_file), "--file", str(source / "compose.persistent-test.yaml"),
        "--file", str(source / "compose.deepseek-staging.yaml"),
        "--profile", "deepseek-staging", "--profile", "p12-owner-oneshot",
    ]
    env = _owner_safe_environment({
        "P12_RUN_NAMESPACE": run_namespace,
        "P12_FINQUANT_OUTPUT_DIR": str(output),
        "P12_OWNER_SCOPED_PROXY_KEY": "sk-preflight-placeholder-only",
        "P12_DEEPSEEK_API_KEY_FILE": str(provider_secret_file),
        "P12_OWNER_RESEARCH_BUDGET_IDENTITY": research_budget_identity,
        "P12_MLFLOW_ARTIFACT_VOLUME": artifact_volume,
    })
    worker_name = run_namespace + "-finquant"
    staging_started = False
    key: str | None = None
    key_blocked = False
    worker_started = False
    try:
        volume_check = subprocess.run(
            ["docker", "volume", "inspect", artifact_volume],
            capture_output=True, text=True, env=_owner_safe_environment(), timeout=30,
        )
        if volume_check.returncode == 0:
            raise DockerDispatchAmbiguous("Per-attempt MLflow artifact volume already exists")
        created_volume = subprocess.run(
            [
                "docker", "volume", "create", "--label", f"aq.p12.request={request_id}",
                "--label", f"aq.p12.attempt={attempt_id}", artifact_volume,
            ],
            capture_output=True, text=True, env=_owner_safe_environment(), timeout=30,
        )
        if created_volume.returncode != 0 or created_volume.stdout.strip() != artifact_volume:
            raise DockerDispatchAmbiguous("Per-attempt MLflow artifact volume could not be created")
        initialize_volume = subprocess.run(
            [
                "docker", "run", "--rm", "--network", "none", "--read-only",
                "--user", "0:0", "--cap-drop", "ALL", "--cap-add", "CHOWN", "--cap-add", "FOWNER",
                "--security-opt", "no-new-privileges:true",
                "--mount", f"type=volume,src={artifact_volume},dst=/qlib-artifacts",
                "--entrypoint", "/bin/sh", PINNED_FINQUANT_IMAGE,
                "-ec", "chown 10001:10001 /qlib-artifacts && chmod 0750 /qlib-artifacts",
            ],
            capture_output=True, text=True, env=_owner_safe_environment(), timeout=60,
        )
        if initialize_volume.returncode != 0:
            raise DockerDispatchAmbiguous("Per-attempt MLflow artifact volume ownership could not be verified")
        config = subprocess.run([*compose, "config", "--quiet"], capture_output=True, text=True, env=env, cwd=runtime, timeout=60)
        if config.returncode != 0:
            raise DockerDispatchFailed(config.returncode or 1, {"classification": "OWNER_COMPOSE_INVALID"})
        prior = subprocess.run([*compose, "ps", "-q", "litellm-deepseek-staging"], capture_output=True, text=True, env=env, cwd=runtime, timeout=30)
        if prior.returncode != 0:
            raise DockerDispatchAmbiguous("Staging Proxy state could not be checked")
        staging_started = not bool(prior.stdout.strip())
        started = subprocess.run(
            [*compose, "up", "--no-build", "--pull", "never", "--detach", "--wait", "--wait-timeout", "180", "postgres", "redis", "litellm-deepseek-staging"],
            capture_output=True, text=True, env=env, cwd=runtime, timeout=240,
        )
        if started.returncode != 0:
            raise DockerDispatchAmbiguous("Staging Proxy dependencies did not become healthy")
        tracking_uri = f"sqlite:////workspace/runs/{run_namespace}/mlflow.db"
        prepare_artifacts = _owner_artifact_container_command(
            output=output, volume=artifact_volume, tracking_uri=tracking_uri,
            helper=helper_name, request_id=request_id, attempt_id=attempt_id,
            prepare=True,
        )
        try:
            artifact_store_record = json.loads(prepare_artifacts.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            artifact_store_record = {}
        if (
            prepare_artifacts.returncode != 0
            or artifact_store_record.get("classification") != "MLFLOW_ARTIFACT_ROOT_READY"
            or artifact_store_record.get("artifact_location") != "file:///qlib-artifacts"
            or artifact_store_record.get("request_id") != request_id
            or artifact_store_record.get("attempt_id") != attempt_id
            or artifact_store_record.get("artifact_volume") != artifact_volume
        ):
            raise DockerDispatchAmbiguous("Native MLflow experiment could not be bound to its per-attempt artifact volume")
        prepared = subprocess.run(
            [*compose, "exec", "-T", "litellm-deepseek-staging", "python", "/app/owner_oneshot_proxy_control.py"],
            input=json.dumps({
                "operation": "prepare", "owner_activation_confirmed": True,
                "research_budget_identity": research_budget_identity,
                "request_id": request_id,
                "standing_policy_id": standing_policy_id,
            }), capture_output=True, text=True, env=env, cwd=runtime, timeout=90,
        )
        if prepared.returncode != 0:
            raise DockerDispatchAmbiguous("Native LiteLLM experiment user/key provisioning failed")
        lines = prepared.stdout.strip().splitlines()
        record = json.loads(lines[-1]) if lines else {}
        key = record.get("token")
        if (
            record.get("classification") != "OWNER_ONESHOT_NATIVE_KEY_READY"
            or not isinstance(key, str) or not key.startswith("sk-")
            or record.get("user_budget_usd") != 5.0
            or record.get("user_spend_usd") != 0.0
            or record.get("key_budget_usd") is None or record.get("key_budget_usd") > 5.0
            or record.get("budget_duration") is not None
            or record.get("max_parallel_requests") != 1
            or record.get("models") != list(OWNER_ONESHOT_MODELS)
        ):
            raise DockerDispatchAmbiguous("Native LiteLLM user/key scope verification failed")
        env["P12_OWNER_SCOPED_PROXY_KEY"] = key
        attempt_started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        worker_started = True
        launched = subprocess.run(
            [*compose, "run", "--no-deps", "--name", worker_name, "rdagent-owner-oneshot-worker"],
            capture_output=True, text=True, env=env, cwd=runtime, timeout=maximum_runtime_seconds,
        )
        _redact_persisted_selector_logs(output)
        _durable_output_write(output, "rdagent.stdout.redacted.log", _redact_diagnostics(launched.stdout, (key,)))
        _durable_output_write(output, "rdagent.stderr.redacted.log", _redact_diagnostics(launched.stderr, (key,)))
        raw = subprocess.run(["docker", "container", "inspect", "--format", "{{json .}}", worker_name], capture_output=True, text=True, env=_owner_safe_environment(), timeout=30)
        if raw.returncode != 0:
            raise DockerDispatchAmbiguous("Owner worker terminal state could not be inspected")
        try:
            inspection = json.loads(raw.stdout)
            observed = validate_owner_worker_inspection(
                inspection, expected_key=key, expected_output=output,
                run_namespace=run_namespace, expected_artifact_volume=artifact_volume,
            )
        except Exception as exc:
            raise DockerDispatchAmbiguous(f"Owner worker inspection failed ({type(exc).__name__})") from None
        if observed["return_code"] != launched.returncode:
            raise DockerDispatchAmbiguous("Compose and inspected worker return codes differed")
        evidence_result = _owner_artifact_container_command(
            output=output, volume=artifact_volume, tracking_uri=tracking_uri,
            helper=helper_name, request_id=request_id, attempt_id=attempt_id,
            prepare=False,
        )
        try:
            research_evidence = json.loads(evidence_result.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            raise DockerDispatchAmbiguous("Native Qlib Recorder evidence could not be read") from None
        if evidence_result.returncode not in (0, 2):
            raise DockerDispatchAmbiguous("Native Qlib Recorder evidence inspection failed")
        blocked = subprocess.run(
            [*compose, "exec", "-T", "litellm-deepseek-staging", "python", "/app/owner_oneshot_proxy_control.py"],
            input=json.dumps({
                "operation": "block", "token": key, "request_id": request_id,
                "attempt_id": attempt_id, "research_budget_identity": research_budget_identity,
                "attempt_started_at_utc": attempt_started_at,
            }), capture_output=True, text=True,
            env=env, cwd=runtime, timeout=60,
        )
        blocked_record = json.loads(blocked.stdout.strip().splitlines()[-1]) if blocked.stdout.strip() else {}
        if blocked.returncode != 0 or blocked_record.get("blocked") is not True:
            raise DockerDispatchAmbiguous("Native one-shot key blocking was not verified")
        key_blocked = True
        call_evidence = blocked_record.get("call_evidence")
        if not isinstance(call_evidence, dict):
            call_evidence = {
                "format_version": "P12_LITELLM_CALL_EVIDENCE_V1",
                "request_id": request_id, "attempt_id": attempt_id,
                "native_experiment_user_id": None, "scoped_key_identity": None,
                "litellm_proxy_version": "1.105.1", "calls": [], "call_count": None,
                "total_spend_usd": None, "provider_model_identity_kind": "UNAVAILABLE",
                "missing_fields": ["native_spend_logs_response_missing"], "evidence_status": "PARTIAL",
            }
        evidence_write_error = None
        try:
            evidence_text = json.dumps(call_evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
            _durable_output_write(output, "p12-litellm-call-evidence.json", evidence_text)
            evidence_bytes = (output / "p12-litellm-call-evidence.json").read_bytes()
            call_evidence_digest = hashlib.sha256(evidence_bytes).hexdigest()
        except Exception as exc:
            evidence_write_error = type(exc).__name__
            call_evidence_digest = None
        native_evidence_write_error = None
        native_evidence_digest = None
        try:
            native_evidence = build_native_research_evidence(
                request_id=request_id, attempt_id=attempt_id, run_namespace=run_namespace,
                output=output, observed_worker=observed, qlib_evidence=research_evidence,
                artifact_volume=artifact_volume, llm_evidence_sha256=call_evidence_digest,
                llm_evidence=call_evidence,
            )
            native_evidence["process_status"] = (
                "PROCESS_EXIT_SUCCESS" if launched.returncode == 0 else "PROCESS_EXIT_FAILED"
            )
            native_evidence["llm_evidence_status_observed"] = call_evidence.get("evidence_status", "PARTIAL")
            native_text = json.dumps(
                native_evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ) + "\n"
            _durable_output_write(output, "p12-native-research-evidence.json", native_text)
            native_evidence_digest, _ = _hash_regular_file(
                output / "p12-native-research-evidence.json", output
            )
        except Exception as exc:
            native_evidence_write_error = type(exc).__name__
        remove = subprocess.run(["docker", "container", "rm", worker_name], capture_output=True, text=True, env=_owner_safe_environment(), timeout=30)
        if remove.returncode != 0:
            raise DockerDispatchAmbiguous("Owner worker cleanup was not verified")
        worker_started = False
        if staging_started:
            stop = subprocess.run([*compose, "stop", "litellm-deepseek-staging"], capture_output=True, text=True, env=env, cwd=runtime, timeout=60)
            if stop.returncode != 0:
                raise DockerDispatchAmbiguous("Temporary staging Proxy could not be stopped")
            staging_started = False
        return {
            **observed,
            "target_return_code": launched.returncode,
            "process_exit_status": "PROCESS_EXIT_SUCCESS" if launched.returncode == 0 else "PROCESS_EXIT_FAILED",
            "research_evidence_status": research_evidence.get("classification"),
            "research_evidence": research_evidence,
            "key_blocked_after_attempt": True,
            "native_user_budget_usd": record["user_budget_usd"],
            "native_key_budget_usd": record["key_budget_usd"],
            "native_user_spend_usd": blocked_record.get("spend"),
            "llm_call_evidence_write_error_type": evidence_write_error,
            "llm_call_evidence_sha256_observed": call_evidence_digest,
            "llm_call_evidence_status_observed": call_evidence.get("evidence_status", "PARTIAL"),
            "native_research_evidence_status": (
                "PARTIAL"
            ),
            "native_research_evidence_path": (
                "p12-native-research-evidence.json" if native_evidence_digest else None
            ),
            "native_research_evidence_sha256_observed": native_evidence_digest,
            "native_research_evidence_write_error_type": native_evidence_write_error,
            "qlib_research_status": (
                "QLIB_RESEARCH_COMPLETE"
                if research_evidence.get("classification") == "RESEARCH_EVIDENCE_COMPLETE"
                else "QLIB_RESEARCH_INCOMPLETE"
            ),
            "rdagent_provenance_status": "PARTIAL",
            "llm_provenance_status": call_evidence.get("evidence_status", "PARTIAL"),
            "effective_config_identity_status": (
                native_evidence.get("effective_config_identity", {}).get("status", "UNAVAILABLE")
                if native_evidence_write_error is None else "UNAVAILABLE"
            ),
            "output_directory": str(output),
            "mlflow_artifact_volume": artifact_volume,
            "chat_max_tokens": 8192,
        }
    except subprocess.TimeoutExpired as exc:
        if worker_started:
            subprocess.run(["docker", "container", "stop", "--time", "30", worker_name], capture_output=True, text=True, env=_owner_safe_environment(), timeout=45)
        raise DockerDispatchAmbiguous("Owner one-shot worker timed out; dispatch state is ambiguous") from exc
    finally:
        if key and not key_blocked:
            try:
                blocked = subprocess.run(
                    [*compose, "exec", "-T", "litellm-deepseek-staging", "python", "/app/owner_oneshot_proxy_control.py"],
                    input=json.dumps({"operation": "block", "token": key}), capture_output=True, text=True,
                    env=env, cwd=runtime, timeout=60,
                )
                block_record = json.loads(blocked.stdout.strip().splitlines()[-1]) if blocked.stdout.strip() else {}
                key_blocked = blocked.returncode == 0 and block_record.get("blocked") is True
            except Exception:
                key_blocked = False
        if staging_started:
            subprocess.run([*compose, "stop", "litellm-deepseek-staging"], capture_output=True, text=True, env=env, cwd=runtime, timeout=60)
        if key and not key_blocked:
            raise DockerDispatchAmbiguous("Native one-shot key block could not be verified")
