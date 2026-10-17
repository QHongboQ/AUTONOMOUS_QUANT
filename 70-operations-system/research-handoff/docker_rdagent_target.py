"""One TEST_ONLY Docker target for the official RD-Agent proxy/mock smoke."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import subprocess
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
