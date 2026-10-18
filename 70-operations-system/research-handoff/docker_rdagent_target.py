"""One TEST_ONLY Docker target for the official RD-Agent proxy/mock smoke."""

from __future__ import annotations

import hashlib
import json
import os
import re
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


PINNED_FINQUANT_IMAGE = "aq/p3-rdagent-qlib:rdagent-1.0.0-qlib-0.9.8.dev26-v1"
PINNED_FINQUANT_IMAGE_ID = "sha256:f0caceba9e06a618dda72bd999de78c13e34e0773831c8796936c80793e4eea2"
FINQUANT_DATA_MOUNTS = {
    "/data/factor-source": "/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source",
    "/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data": "/mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data",
    "/mnt/d/AQ_DATA/P2/certification-historical-rehearsal-001/qlib-calendar-runtime": "/mnt/d/AQ_DATA/P2/certification-historical-rehearsal-001/qlib-calendar-runtime",
}


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
    """Run the pinned RD-Agent CLI for one TEST_ONLY native proposal step."""
    source_directory = Path(__file__).with_name("docker-rdagent-smoke")
    runtime_directory = runtime_directory.resolve()
    runtime_directory.mkdir(parents=True, exist_ok=True)
    project = "aq-p12-finquant-" + hashlib.sha256(
        f"{request_id}:{attempt_id}".encode("utf-8")
    ).hexdigest()[:12]
    run_directory = runtime_directory / project
    run_directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in _FILES:
        shutil.copyfile(source_directory / name, run_directory / name)

    master_key = "sk-" + secrets.token_urlsafe(32)
    database_password = secrets.token_urlsafe(32)
    env = _compose_env(master_key, database_password, "sk-test-key-not-yet-provisioned")
    env["P12_RUN_NAMESPACE"] = project
    compose_file = str(run_directory / "compose.yaml")
    compose = ["docker", "compose", "--project-name", project, "--file", compose_file]
    worker_name = project + "-finquant"
    try:
        image = _run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", PINNED_FINQUANT_IMAGE],
            env=env,
            timeout=30,
            cwd=run_directory,
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

        compose_check = _run([*compose, "config", "--quiet"], env=env, timeout=30, cwd=run_directory)
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
            [*compose, "up", "--detach", "--wait", "--wait-timeout", "180", "litellm"],
            env=env,
            timeout=240,
            cwd=run_directory,
        )
        if started.returncode != 0:
            raise DockerDispatchAmbiguous("Compose Proxy/Mock dependencies did not become healthy")

        provision = _run(
            [*compose, "exec", "--no-TTY", "litellm", "python", "/app/provision_test_key.py"],
            env=env,
            timeout=30,
            cwd=run_directory,
        )
        key_record = _json_line(provision.stdout, "TEST_PROXY_KEY_CREATED")
        if provision.returncode != 0 or not key_record or not isinstance(key_record.get("token"), str):
            raise DockerDispatchAmbiguous("Proxy failed to provision its scoped TEST_ONLY key")
        env["P3_TEST_PROXY_KEY"] = key_record["token"]

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
            cwd=run_directory,
        )

        inspect = _run(
            [
                "docker",
                "container",
                "inspect",
                "--format",
                "{{.Image}}|{{.State.Status}}|{{.State.ExitCode}}|{{.Config.Image}}|{{json .Config.Entrypoint}}|{{json .Config.Cmd}}",
                worker_name,
            ],
            env=env,
            timeout=30,
            cwd=run_directory,
        )
        if inspect.returncode != 0:
            raise DockerDispatchAmbiguous("Native fin_quant container terminal state could not be inspected")
        try:
            image_id, state, inspect_return_code, configured_image, entrypoint, command = inspect.stdout.strip().split("|", 5)
            inspect_return_code = int(inspect_return_code)
            entrypoint_value = json.loads(entrypoint)
            command_value = json.loads(command)
        except (TypeError, ValueError, json.JSONDecodeError):
            raise DockerDispatchAmbiguous("Native fin_quant container identity was corrupt") from None

        mounts_result = _run(
            ["docker", "container", "inspect", "--format", "{{json .Mounts}}", worker_name],
            env=env,
            timeout=30,
            cwd=run_directory,
        )
        env_result = _run(
            ["docker", "container", "inspect", "--format", "{{json .Config.Env}}", worker_name],
            env=env,
            timeout=30,
            cwd=run_directory,
        )
        networks_result = _run(
            ["docker", "container", "inspect", "--format", "{{json .NetworkSettings.Networks}}", worker_name],
            env=env,
            timeout=30,
            cwd=run_directory,
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
        mounts_valid = len(mounted) == 3 and all(
            target in mounted
            and mounted[target].get("Source") == source
            and mounted[target].get("RW") is False
            and mounted[target].get("Type") == "bind"
            for target, source in FINQUANT_DATA_MOUNTS.items()
        )
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
            "WORKSPACE_PATH": f"/workspace/runs/{project}/workspaces",
            "PICKLE_CACHE_FOLDER_PATH_STR": f"/workspace/runs/{project}/pickle-cache",
            "LOG_TRACE_PATH": f"/workspace/runs/{project}/trace",
            "QLIB_MLFLOW_URI": f"sqlite:////workspace/runs/{project}/mlflow.db",
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
        )
        internal_network = _run(
            [
                "docker",
                "network",
                "inspect",
                "--format",
                "{{.Internal}}",
                f"{project}_worker_proxy",
            ],
            env=env,
            timeout=30,
            cwd=run_directory,
        )
        if internal_network.returncode != 0:
            raise DockerDispatchAmbiguous("Worker-only Proxy network could not be verified")
        worker_network_valid = internal_network.stdout.strip() == "true" and len(networks) == 1 and all(
            name.endswith("_worker_proxy") for name in networks
        )

        counts = _compose_json_counts(compose, env, run_directory)
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
            "run_namespace": project,
            "proposal_phase_reached": proposal_phase_reached,
            "proposal_phase_marker": "Start Loop 0, Step 0: direct_exp_gen" if proposal_phase_reached else None,
            "proxy_mock_request_observed": counts["chat"] > 0 or counts["embedding"] > 0,
            "proxy_mock_chat_count": counts["chat"],
            "proxy_mock_embedding_count": counts["embedding"],
            "worker_return_code": worker.returncode,
            "container_return_code": inspect_return_code,
            "paid_provider_calls": 0,
            "training_runs": 0,
            "certification_runs": 0,
            "candidate_count": 0,
            "broker_actions": 0,
            "sealed_oos_accessed": False,
        }
        if not (
            process_identity_valid
            and env_valid
            and mounts_valid
            and worker_network_valid
            and scenario_initialized
            and proposal_phase_reached
            and evidence["proxy_mock_request_observed"]
            and worker.returncode == 0
        ):
            raise DockerDispatchFailed(worker.returncode or 1, evidence)
        return evidence
    finally:
        remove = _run(
            [*compose, "rm", "--force", "rdagent-finquant-worker"],
            env=env,
            timeout=120,
            cwd=run_directory,
        )
        if remove.returncode != 0:
            raise DockerDispatchAmbiguous("one-off fin_quant worker cleanup could not be verified")
        down = _run(
            [*compose, "down", "--volumes", "--remove-orphans"],
            env=env,
            timeout=120,
            cwd=run_directory,
        )
        if down.returncode != 0:
            raise DockerDispatchAmbiguous("temporary Compose Proxy/Mock teardown failed")
        _ensure_cleaned(project, env, run_directory)
