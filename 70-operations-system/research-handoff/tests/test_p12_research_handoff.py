from __future__ import annotations

import inspect
import json
import os
import pickle
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

HANDOFF_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HANDOFF_DIR))
import p12_research_handoff as handoff  # noqa: E402
import standing_policy as policy_gate  # noqa: E402
import docker_rdagent_target  # noqa: E402

TEST_ROOT = Path(
    os.environ.get(
        "AQ_P12_HANDOFF_TEST_ROOT",
        "/mnt/d/AQ/OPERATIONS/P12/research-handoff-synthetic-poc-001/acceptance-runs",
    )
)
PYTHON = sys.executable
SCRIPT = HANDOFF_DIR / "p12_research_handoff.py"


class DurableSyntheticHandoffTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_dir = TEST_ROOT / f"{self._testMethodName}-{uuid.uuid4().hex}"
        self.run_dir.mkdir(parents=True, exist_ok=False)
        self.request_file = self.run_dir / "request.json"
        self.policy_file = self.run_dir / "test-policy.json"
        self.state_dir = self.run_dir / "state"
        self.assertTrue(str(self.run_dir).startswith(str(TEST_ROOT)))

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = ":".join(
            [
                "/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001/upstream-libs",
                environment.get("PYTHONPATH", ""),
            ]
        ).rstrip(":")
        return subprocess.run(
            [PYTHON, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )

    def _make_request(self) -> dict[str, object]:
        result = self._run("create-synthetic-request", "--output", str(self.request_file))
        self.assertEqual(result.returncode, 0, result.stderr)
        policy = self._run(
            "create-synthetic-test-policy",
            "--request",
            str(self.request_file),
            "--output",
            str(self.policy_file),
        )
        self.assertEqual(policy.returncode, 0, policy.stderr)
        return json.loads(self.request_file.read_text(encoding="utf-8"))

    def _process_at(self, state_dir: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return self._run(
            "process",
            "--request",
            str(self.request_file),
            "--policy",
            str(self.policy_file),
            "--state-dir",
            str(state_dir),
            "--synthetic-only",
            *extra,
        )

    def _process(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self._process_at(self.state_dir, *extra)

    def test_missing_policy_is_denied_before_durable_claim(self) -> None:
        self._run("create-synthetic-request", "--output", str(self.request_file))
        result = self._run(
            "process",
            "--request",
            str(self.request_file),
            "--state-dir",
            str(self.state_dir),
            "--synthetic-only",
        )
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["classification"], "DENIED_POLICY_MISSING")
        self.assertFalse(self.state_dir.exists())

    def _dispatch_lines(self) -> list[dict[str, object]]:
        files = list(self.state_dir.glob("*.dispatch.jsonl")) if self.state_dir.exists() else []
        return [json.loads(line) for path in files for line in path.read_text().splitlines()]

    def _record_path(self, kind: str, state_dir: Path | None = None) -> Path:
        request_id = json.loads(self.request_file.read_text(encoding="utf-8"))[
            "research_request"]["request_id"]
        return (state_dir or self.state_dir) / f"{request_id.removeprefix('sha256:')}.{kind}.json"

    def test_p4_factory_creates_bootstrap_request_without_champion(self) -> None:
        envelope = handoff.create_synthetic_request()
        decision = envelope["p4_decision"]
        request = envelope["research_request"]
        self.assertEqual(decision["evidence_classification"], "TEST_FIXTURE_NOT_REAL_EVIDENCE")
        self.assertEqual(decision["decision_kind"], "CHALLENGER_NEEDED")
        self.assertIsNone(decision["current_state"])
        self.assertEqual(request["reason"], "NO_CHAMPION")
        self.assertEqual(request["request_provenance"], handoff._identity("p12-synthetic-fixture-provenance-v1"))
        parsed = handoff.p4.ResearchRequestV1.model_validate(request)
        self.assertEqual(parsed.request_id, request["request_id"])

    def test_valid_synthetic_handoff_and_terminal_replay(self) -> None:
        envelope = self._make_request()
        first = self._process()
        self.assertEqual(first.returncode, 0, first.stderr)
        result = json.loads(first.stdout)
        self.assertEqual(result["classification"], "SUCCEEDED_SYNTHETIC")
        self.assertEqual(result["external_authorization"], "UNVERIFIED_DENIED")
        self.assertEqual(result["spending_permission"], "NOT_PROVEN_DENIED")
        self.assertEqual(result["real_dispatch_permission"], "DENIED")
        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["status"]["request_id"], envelope["research_request"]["request_id"])
        policy_id = json.loads(self.policy_file.read_text(encoding="utf-8"))["policy_id"]
        self.assertEqual(result["status"]["standing_policy_id"], policy_id)
        research_budget_identity = envelope["research_request"]["research_budget_identity"]
        experiment_user_id = handoff.experiment_user_id(research_budget_identity)
        for record_kind in ("claim", "dispatching", "terminal"):
            marker = json.loads(self._record_path(record_kind).read_text())
            self.assertEqual(marker["standing_policy_id"], policy_id)
            self.assertEqual(marker["research_budget_identity"], research_budget_identity)
            self.assertEqual(marker["native_experiment_user_id"], experiment_user_id)

        replay = self._process()
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["classification"], "REPLAY_TERMINAL_NO_DISPATCH")
        self.assertEqual(len(self._dispatch_lines()), 1)

    def test_p4_origin_is_persisted_and_checked_across_all_terminal_records(self) -> None:
        self._make_request()
        for kind in ("claim", "dispatching", "terminal"):
            with self.subTest(record=kind):
                state = self.run_dir / f"origin-{kind}"
                processed = self._process_at(state)
                self.assertEqual(processed.returncode, 0, processed.stderr)
                path = self._record_path(kind, state)
                record = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(record["request_origin"], "P4_LIFECYCLE")
                record["request_origin"] = "OWNER_INITIAL_BOOTSTRAP"
                path.write_text(json.dumps(record), encoding="utf-8")
                replay = self._process_at(state)
                self.assertNotEqual(replay.returncode, 0)
                self.assertIn("COLLISION", json.loads(replay.stdout)["classification"])

    def test_legacy_synthetic_success_and_failure_replay_without_redispatch(self) -> None:
        self._make_request()
        for mode, expected_code, expected_classification in (
            ("success", 0, "REPLAY_TERMINAL_NO_DISPATCH"),
            ("failure", 4, "REPLAY_TERMINAL_FAILED_NO_DISPATCH"),
        ):
            with self.subTest(mode=mode):
                state = self.run_dir / f"legacy-{mode}"
                first = self._process_at(state, "--target-mode", mode)
                self.assertEqual(first.returncode, expected_code)
                for kind in ("claim", "dispatching", "terminal"):
                    path = self._record_path(kind, state)
                    record = json.loads(path.read_text(encoding="utf-8"))
                    record.pop("request_origin")
                    path.write_text(json.dumps(record), encoding="utf-8")
                replay = self._process_at(state)
                self.assertEqual(replay.returncode, expected_code, replay.stderr)
                self.assertEqual(json.loads(replay.stdout)["classification"], expected_classification)
                self.assertEqual(len(list(state.glob("*.dispatch.jsonl"))), 1)

    def test_mixed_legacy_and_origin_markers_are_rejected(self) -> None:
        self._make_request()
        state = self.run_dir / "mixed-origin"
        self.assertEqual(self._process_at(state).returncode, 0)
        path = self._record_path("claim", state)
        claim = json.loads(path.read_text(encoding="utf-8"))
        claim.pop("request_origin")
        path.write_text(json.dumps(claim), encoding="utf-8")
        replay = self._process_at(state)
        self.assertEqual(replay.returncode, 3, replay.stderr)
        self.assertEqual(
            json.loads(replay.stdout)["classification"],
            "BLOCKED_REQUEST_ID_COLLISION_OR_CONTENT_CHANGE",
        )
        self.assertEqual(len(list(state.glob("*.dispatch.jsonl"))), 1)

    def test_native_experiment_identity_tampering_blocks_replay(self) -> None:
        self._make_request()
        for marker_kind in ("claim", "dispatching", "terminal"):
            state_dir = self.run_dir / f"native-user-{marker_kind}"
            first = self._process_at(state_dir)
            self.assertEqual(first.returncode, 0, first.stderr)
            marker_path = self._record_path(marker_kind, state_dir)
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
            marker["native_experiment_user_id"] = "aq-p12-exp-tampered"
            marker_path.write_text(json.dumps(marker), encoding="utf-8")

            replay = self._process_at(state_dir)
            self.assertEqual(replay.returncode, 3, replay.stderr)
            self.assertEqual(
                json.loads(replay.stdout)["classification"],
                "BLOCKED_REQUEST_ID_COLLISION_OR_CONTENT_CHANGE",
            )
            self.assertEqual(len(list(state_dir.glob("*.dispatch.jsonl"))), 1)

    def test_docker_target_identity_is_durable_and_success_replays_without_redispatch(self) -> None:
        self._make_request()
        evidence = {
            "classification": "DOCKER_RDAGENT_PROXY_MOCK_SMOKE",
            "mock_chat_count": 1,
            "mock_embedding_count": 1,
            "paid_provider_calls": 0,
            "training_runs": 0,
            "broker_actions": 0,
            "sealed_oos_accessed": False,
        }
        with patch.object(docker_rdagent_target, "run_docker_rdagent_proxy_mock_smoke", return_value=evidence) as run:
            first, code = handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity=handoff.TARGET_DOCKER_RDAGENT,
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(code, 0)
        self.assertEqual(first["classification"], "SUCCEEDED_SYNTHETIC")
        self.assertEqual(run.call_count, 1)
        for kind in ("claim", "dispatching", "terminal"):
            record = json.loads(self._record_path(kind).read_text(encoding="utf-8"))
            self.assertEqual(record["target_identity"], handoff.TARGET_DOCKER_RDAGENT)
            self.assertEqual(record["synthetic_dispatch_target"], handoff.TARGET_DOCKER_RDAGENT)

        with patch.object(docker_rdagent_target, "run_docker_rdagent_proxy_mock_smoke", side_effect=AssertionError("redispatch")) as replay_runner:
            replay, replay_code = handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity=handoff.TARGET_DOCKER_RDAGENT,
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(replay_code, 0)
        self.assertEqual(replay["classification"], "REPLAY_TERMINAL_NO_DISPATCH")
        replay_runner.assert_not_called()

    def test_finquant_test_only_target_is_durable_and_replay_does_not_redispatch(self) -> None:
        self._make_request()
        evidence = {
            "classification": "P12_NATIVE_FINQUANT_TEST_ONLY",
            "official_finquant_process_started": True,
            "scenario_initialized": True,
            "us_pit_binding_selected": True,
            "proposal_phase_reached": True,
            "proxy_mock_request_observed": True,
            "worker_return_code": 0,
            "paid_provider_calls": 0,
            "training_runs": 0,
            "candidate_count": 0,
            "broker_actions": 0,
            "sealed_oos_accessed": False,
        }
        with patch.object(docker_rdagent_target, "run_docker_rdagent_finquant", return_value=evidence) as run:
            first, code = handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity=handoff.TARGET_DOCKER_FINQUANT,
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(code, 0)
        self.assertEqual(first["classification"], "SUCCEEDED_SYNTHETIC")
        self.assertEqual(first["status"]["target_stdout"], json.dumps(evidence, sort_keys=True))
        self.assertEqual(run.call_count, 1)
        self.assertEqual(
            json.loads(self._record_path("claim").read_text(encoding="utf-8"))["target_identity"],
            handoff.TARGET_DOCKER_FINQUANT,
        )

        with patch.object(
            docker_rdagent_target,
            "run_docker_rdagent_finquant",
            side_effect=AssertionError("fin_quant redispatched on replay"),
        ) as replay_runner:
            replay, replay_code = handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity=handoff.TARGET_DOCKER_FINQUANT,
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(replay_code, 0)
        self.assertEqual(replay["classification"], "REPLAY_TERMINAL_NO_DISPATCH")
        replay_runner.assert_not_called()

    def test_finquant_failed_proposal_is_terminal_and_replays_without_redispatch(self) -> None:
        self._make_request()
        evidence = {
            "classification": "P12_NATIVE_FINQUANT_TEST_ONLY",
            "official_finquant_process_started": True,
            "scenario_initialized": True,
            "us_pit_binding_selected": True,
            "proposal_phase_reached": True,
            "proxy_mock_request_observed": True,
            "worker_return_code": 1,
            "research_step_outcome": "FAILED_MALFORMED_MOCK_RESPONSE",
            "paid_provider_calls": 0,
            "training_runs": 0,
            "candidate_count": 0,
            "broker_actions": 0,
            "sealed_oos_accessed": False,
        }
        with patch.object(
            docker_rdagent_target,
            "run_docker_rdagent_finquant",
            side_effect=docker_rdagent_target.DockerDispatchFailed(1, evidence),
        ) as run:
            first, code = handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity=handoff.TARGET_DOCKER_FINQUANT,
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(code, 4)
        self.assertEqual(first["classification"], "FAILED_SYNTHETIC")
        self.assertEqual(first["status"]["target_return_code"], 1)
        replay, replay_code = handoff.process_synthetic_request(
            self.request_file,
            self.state_dir,
            self.policy_file,
            target_identity=handoff.TARGET_DOCKER_FINQUANT,
            docker_runtime_dir=self.run_dir / "docker-runtime",
        )
        self.assertEqual(replay_code, 4)
        self.assertEqual(replay["classification"], "REPLAY_TERMINAL_FAILED_NO_DISPATCH")
        run.assert_called_once()

    def test_finquant_proxy_unavailable_blocks_replay_without_redispatch(self) -> None:
        self._make_request()
        with patch.object(
            docker_rdagent_target,
            "run_docker_rdagent_finquant",
            side_effect=docker_rdagent_target.DockerDispatchAmbiguous("test Proxy unavailable"),
        ) as run:
            first, code = handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity=handoff.TARGET_DOCKER_FINQUANT,
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(code, 3)
        self.assertEqual(first["classification"], "BLOCKED_UNKNOWN_POST_DISPATCH_STATE")
        self.assertFalse(self._record_path("terminal").exists())
        replay, replay_code = handoff.process_synthetic_request(
            self.request_file,
            self.state_dir,
            self.policy_file,
            target_identity=handoff.TARGET_DOCKER_FINQUANT,
            docker_runtime_dir=self.run_dir / "docker-runtime",
        )
        self.assertEqual(replay_code, 3)
        self.assertEqual(replay["classification"], "BLOCKED_UNKNOWN_POST_DISPATCH_STATE")
        run.assert_called_once()

    def test_finquant_image_mismatch_fails_closed_without_compose_launch(self) -> None:
        def inspect_wrong_image(command, **kwargs):
            stdout = "sha256:wrong-image\n" if command[:3] == ["docker", "image", "inspect"] else ""
            return subprocess.CompletedProcess(command, 0, stdout, "")

        with patch.object(docker_rdagent_target, "FINQUANT_OUTPUT_ROOT", self.run_dir / "durable-output"), patch.object(
            docker_rdagent_target, "_run", side_effect=inspect_wrong_image
        ) as run:
            with self.assertRaises(docker_rdagent_target.DockerDispatchFailed) as raised:
                docker_rdagent_target.run_docker_rdagent_finquant(
                    request_id="sha256:" + "a" * 64,
                    attempt_id=str(uuid.uuid4()),
                    runtime_directory=self.run_dir / "docker-runtime",
                )
        self.assertEqual(raised.exception.evidence["classification"], "PINNED_FINQUANT_IMAGE_MISMATCH")
        self.assertFalse(raised.exception.evidence["worker_launched"])
        self.assertEqual(run.call_args_list[0].args[0][:3], ["docker", "image", "inspect"])
        commands = [call.args[0] for call in run.call_args_list]
        self.assertFalse(any(command[:2] == ["docker", "compose"] and "up" in command for command in commands))
        self.assertFalse(any(command[:2] == ["docker", "compose"] and "run" in command for command in commands))

    def test_finquant_durable_output_is_request_and_attempt_scoped_and_immutable(self) -> None:
        root = self.run_dir / "durable-output"
        request_id = "sha256:" + "b" * 64
        attempt_id = str(uuid.uuid4())
        output = docker_rdagent_target._finquant_output_directory(request_id, attempt_id, root)
        self.assertEqual(output, root / ("b" * 64) / attempt_id)
        self.assertTrue(output.is_dir())
        docker_rdagent_target._durable_output_write(output, "diagnostic.txt", "preserved\n")
        with self.assertRaises(FileExistsError):
            docker_rdagent_target._durable_output_write(output, "diagnostic.txt", "overwrite\n")
        self.assertEqual((output / "diagnostic.txt").read_text(encoding="utf-8"), "preserved\n")
        second_attempt = docker_rdagent_target._finquant_output_directory(
            request_id, str(uuid.uuid4()), root
        )
        self.assertNotEqual(output, second_attempt)

    def test_finquant_durable_output_rejects_noncanonical_request_or_attempt_identity(self) -> None:
        root = self.run_dir / "durable-output"
        with self.assertRaises(ValueError):
            docker_rdagent_target._finquant_output_directory("request", str(uuid.uuid4()), root)
        with self.assertRaises(ValueError):
            docker_rdagent_target._finquant_output_directory("sha256:" + "c" * 64, "../attempt", root)
        self.assertFalse(root.exists())

    def test_finquant_diagnostics_redact_test_and_provider_tokens(self) -> None:
        sanitized = docker_rdagent_target._redact_diagnostics(
            "key=sk-specific-secret-value Bearer abcdefghijklmnop", ("sk-specific-secret-value",)
        )
        self.assertNotIn("specific-secret", sanitized)
        self.assertNotIn("abcdefghijklmnop", sanitized)
        self.assertIn("[REDACTED_TEST_SECRET]", sanitized)
        self.assertIn("[REDACTED_BEARER_TOKEN]", sanitized)

    def test_finquant_redacts_plain_log_without_mutating_signed_native_pickle(self) -> None:
        output = self.run_dir / "native-output"
        settings_directory = output / "LITELLM_SETTINGS"
        settings_directory.mkdir(parents=True)
        source = {"api_key": "sk-" + "a" * 32, "authorization": "Bearer " + "b" * 24}
        artifact = settings_directory / "trace.pkl"
        artifact.write_bytes(pickle.dumps(source, protocol=4))
        original = artifact.read_bytes()
        (output / "selector.log").write_text(source["api_key"] + "\n", encoding="utf-8")
        self.assertEqual(docker_rdagent_target._redact_persisted_selector_logs(output), 1)
        restored = pickle.loads(artifact.read_bytes())
        self.assertEqual(artifact.read_bytes(), original)
        self.assertEqual(restored, source)
        self.assertNotIn(source["api_key"], (output / "selector.log").read_text(encoding="utf-8"))

    def test_finquant_compose_uses_existing_image_and_official_step_limit(self) -> None:
        compose = (HANDOFF_DIR / "docker-rdagent-smoke/compose.yaml").read_text(encoding="utf-8")
        self.assertIn("rdagent-finquant-worker:", compose)
        worker_section = compose.split("  rdagent-finquant-worker:", 1)[1].split("\nnetworks:", 1)[0]
        self.assertIn("image: aq/p3-rdagent-qlib:rdagent-1.0.0-qlib-0.9.8.dev26-v1", worker_section)
        self.assertIn("pull_policy: never", worker_section)
        self.assertNotIn("build:", worker_section)
        self.assertIn('entrypoint: ["rdagent"]', worker_section)
        self.assertIn('command: ["fin_quant", "--step-n", "1", "--loop-n", "1"]', worker_section)
        self.assertIn("read_only: true", worker_section)
        self.assertIn("source: ${P12_FINQUANT_OUTPUT_DIR:?unique durable per-attempt output directory required}", worker_section)
        self.assertIn("target: /workspace", worker_section)
        self.assertIn("create_host_path: false", worker_section)
        self.assertNotIn("/workspace:rw", worker_section)
        for name, value in (
            ("QLIB_QUANT_TRAIN_START", "2015-01-02"),
            ("QLIB_QUANT_TEST_END", "2024-12-31"),
            ("QLIB_FACTOR_TRAIN_START", "2015-01-02"),
            ("QLIB_FACTOR_TEST_END", "2024-12-31"),
            ("QLIB_MODEL_TRAIN_START", "2015-01-02"),
            ("QLIB_MODEL_TEST_END", "2024-12-31"),
        ):
            self.assertIn(f'{name}: "{value}"', worker_section)

    def test_persistent_proxy_worker_isolated_and_uses_native_scoped_key(self) -> None:
        compose = (HANDOFF_DIR / "docker-rdagent-smoke/compose.persistent-test.yaml").read_text(encoding="utf-8")
        proxy_section = compose.split("  litellm:", 1)[1].split("  rdagent-finquant-worker:", 1)[0]
        worker_section = compose.split("  rdagent-finquant-worker:", 1)[1].split("\nnetworks:", 1)[0]
        self.assertIn("networks: [core, worker_proxy]", proxy_section)
        self.assertIn("name: aq-p12-litellm-worker-proxy", compose)
        self.assertIn("internal: true", compose)
        self.assertIn("networks: [worker_proxy]", worker_section)
        self.assertIn("P3_TEST_PROXY_KEY: ${P3_TEST_PROXY_KEY:-}", worker_section)
        self.assertIn("OPENAI_API_KEY: ${P3_TEST_PROXY_KEY:-}", worker_section)
        self.assertIn("TEST_ONLY scoped Proxy key required", worker_section)
        self.assertIn("durable per-attempt output path required", worker_section)
        self.assertIn("test -f /workspace/p12-attempt.json", worker_section)
        for forbidden in ("LITELLM_MASTER_KEY", "POSTGRES_PASSWORD", "DEEPSEEK_API_KEY", "ports:", "/var/run/docker.sock"):
            self.assertNotIn(forbidden, worker_section)
        self.assertIn("provision_test_key.py", proxy_section)
        provisioner = (HANDOFF_DIR / "docker-rdagent-smoke/provision_test_key.py").read_text(encoding="utf-8")
        for native_limit in ("max_budget", "budget_duration", "duration", "max_parallel_requests"):
            self.assertIn(native_limit, provisioner)
        self.assertIn("/key/generate", provisioner)
        self.assertIn("/key/info", provisioner)
        self.assertIn("/key/update", provisioner)
        self.assertIn("/key/block", provisioner)

        target_source = inspect.getsource(docker_rdagent_target.run_docker_rdagent_finquant)
        self.assertIn("PERSISTENT_LITELLM_PROJECT", target_source)
        self.assertIn("PERSISTENT_LITELLM_ENV_FILE", target_source)
        self.assertIn('"create"', target_source)
        self.assertIn('"verify-exhaustion"', target_source)
        self.assertIn('"block"', target_source)
        self.assertNotIn('"down", "--volumes"', target_source)

    def test_inert_success_cannot_be_replayed_as_docker_target(self) -> None:
        self._make_request()
        first = self._process()
        self.assertEqual(first.returncode, 0, first.stderr)
        with patch.object(docker_rdagent_target, "run_docker_rdagent_proxy_mock_smoke", side_effect=AssertionError("redispatch")) as runner:
            replay = self._process(
                "--target", handoff.TARGET_DOCKER_RDAGENT,
                "--docker-runtime-dir", str(self.run_dir / "docker-runtime"),
            )
        self.assertEqual(replay.returncode, 3, replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["classification"], "BLOCKED_REQUEST_ID_COLLISION_OR_CONTENT_CHANGE")
        runner.assert_not_called()

    def test_docker_proxy_unavailable_is_ambiguous_and_not_retried(self) -> None:
        self._make_request()
        with patch.object(
            docker_rdagent_target,
            "run_docker_rdagent_proxy_mock_smoke",
            side_effect=docker_rdagent_target.DockerDispatchAmbiguous("proxy unavailable"),
        ) as runner:
            result, code = handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity=handoff.TARGET_DOCKER_RDAGENT,
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(code, 3)
        self.assertEqual(result["classification"], "BLOCKED_UNKNOWN_POST_DISPATCH_STATE")
        self.assertFalse(self._record_path("terminal").exists())
        replay, replay_code = handoff.process_synthetic_request(
            self.request_file,
            self.state_dir,
            self.policy_file,
            target_identity=handoff.TARGET_DOCKER_RDAGENT,
            docker_runtime_dir=self.run_dir / "docker-runtime",
        )
        self.assertEqual(replay_code, 3)
        self.assertEqual(replay["classification"], "BLOCKED_UNKNOWN_POST_DISPATCH_STATE")
        runner.assert_called_once()

    def test_failed_docker_worker_is_terminal_and_not_replayed(self) -> None:
        self._make_request()
        evidence = {"classification": "DOCKER_RDAGENT_SMOKE_FAILED", "worker": {"classification": "EXPECTED_DENIAL"}}
        with patch.object(
            docker_rdagent_target,
            "run_docker_rdagent_proxy_mock_smoke",
            side_effect=docker_rdagent_target.DockerDispatchFailed(17, evidence),
        ) as runner:
            failed, code = handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity=handoff.TARGET_DOCKER_RDAGENT,
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(code, 4)
        self.assertEqual(failed["classification"], "FAILED_SYNTHETIC")
        replay, replay_code = handoff.process_synthetic_request(
            self.request_file,
            self.state_dir,
            self.policy_file,
            target_identity=handoff.TARGET_DOCKER_RDAGENT,
            docker_runtime_dir=self.run_dir / "docker-runtime",
        )
        self.assertEqual(replay_code, 4)
        self.assertEqual(replay["classification"], "REPLAY_TERMINAL_FAILED_NO_DISPATCH")
        runner.assert_called_once()

    def test_invalid_test_proxy_key_denial_cannot_be_terminal_success(self) -> None:
        self._make_request()
        evidence = {"classification": "DOCKER_RDAGENT_SMOKE_FAILED_INVALID_KEY_DENIAL"}
        with patch.object(
            docker_rdagent_target,
            "run_docker_rdagent_proxy_mock_smoke",
            side_effect=docker_rdagent_target.DockerDispatchFailed(1, evidence),
        ):
            result, code = handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity=handoff.TARGET_DOCKER_RDAGENT,
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(code, 4)
        self.assertEqual(result["classification"], "FAILED_SYNTHETIC")
        self.assertEqual(result["status"]["target_return_code"], 1)
        self.assertEqual(result["status"]["target_identity"], handoff.TARGET_DOCKER_RDAGENT)

    def test_interrupted_docker_dispatch_is_ambiguous_without_redispatch(self) -> None:
        self._make_request()
        interrupted = self._process(
            "--target", handoff.TARGET_DOCKER_RDAGENT,
            "--docker-runtime-dir", str(self.run_dir / "docker-runtime"),
            "--test-interrupt-after", "dispatch-start",
        )
        self.assertEqual(interrupted.returncode, 86)
        replay = self._process(
            "--target", handoff.TARGET_DOCKER_RDAGENT,
            "--docker-runtime-dir", str(self.run_dir / "docker-runtime"),
        )
        self.assertEqual(replay.returncode, 3)
        self.assertEqual(json.loads(replay.stdout)["classification"], "BLOCKED_UNKNOWN_POST_DISPATCH_STATE")

    def test_different_valid_policy_for_same_request_blocks_replay(self) -> None:
        self._make_request()
        first = self._process()
        self.assertEqual(first.returncode, 0, first.stderr)
        alternate_policy = json.loads(self.policy_file.read_text(encoding="utf-8"))
        alternate_policy.pop("policy_id")
        alternate_policy["maximum_run_spend_usd"] = "0.24"
        alternate_policy["policy_id"] = policy_gate.policy_identity(alternate_policy)
        self.policy_file.write_text(json.dumps(alternate_policy), encoding="utf-8")

        replay = self._process()
        self.assertEqual(replay.returncode, 3, replay.stderr)
        self.assertEqual(
            json.loads(replay.stdout)["classification"],
            "BLOCKED_REQUEST_ID_COLLISION_OR_CONTENT_CHANGE",
        )
        self.assertEqual(len(self._dispatch_lines()), 1)

    def test_policy_identity_tampering_in_any_persisted_marker_blocks_replay(self) -> None:
        self._make_request()
        for marker_kind in ("claim", "dispatching", "terminal"):
            state_dir = self.run_dir / f"state-{marker_kind}"
            first = self._process_at(state_dir)
            self.assertEqual(first.returncode, 0, first.stderr)
            marker_path = self._record_path(marker_kind, state_dir)
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
            marker["standing_policy_id"] = "sha256:" + "f" * 64
            marker_path.write_text(json.dumps(marker), encoding="utf-8")

            replay = self._process_at(state_dir)
            self.assertEqual(replay.returncode, 3, replay.stderr)
            self.assertEqual(
                json.loads(replay.stdout)["classification"],
                "BLOCKED_REQUEST_ID_COLLISION_OR_CONTENT_CHANGE",
            )
            self.assertEqual(
                len(list(state_dir.glob("*.dispatch.jsonl"))),
                1,
                f"marker={marker_kind}",
            )

    def test_real_dispatch_defaults_to_denied(self) -> None:
        self._make_request()
        result = self._run(
            "process", "--request", str(self.request_file), "--state-dir", str(self.state_dir)
        )
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["real_dispatch_permission"], "DENIED")
        self.assertEqual(len(self._dispatch_lines()), 0)

    def test_real_finquant_target_is_not_registered_or_dispatchable(self) -> None:
        self._make_request()
        with self.assertRaisesRegex(ValueError, "unsupported TEST_ONLY target"):
            handoff.process_synthetic_request(
                self.request_file,
                self.state_dir,
                self.policy_file,
                target_identity="DOCKER_RDAGENT_FINQUANT_REAL",
                docker_runtime_dir=self.run_dir / "docker-runtime",
            )
        self.assertEqual(len(self._dispatch_lines()), 0)
        self.assertFalse(self._record_path("claim").exists())

    def test_same_request_concurrent_claims_dispatch_once(self) -> None:
        self._make_request()
        command = [
            PYTHON,
            str(SCRIPT),
            "process",
            "--request",
            str(self.request_file),
            "--policy",
            str(self.policy_file),
            "--state-dir",
            str(self.state_dir),
            "--synthetic-only",
            "--test-before-claim-delay-ms",
            "250",
        ]
        environment = os.environ.copy()
        environment["PYTHONPATH"] = "/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001/upstream-libs"
        processes = [
            subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=environment)
            for _ in range(2)
        ]
        outputs = [process.communicate(timeout=30) + (process.returncode,) for process in processes]
        self.assertEqual(sum(1 for _, _, code in outputs if code == 0), 1, outputs)
        self.assertEqual(sum(1 for _, _, code in outputs if code == 3), 1, outputs)
        classes = [json.loads(stdout)["classification"] for stdout, _, _ in outputs]
        self.assertEqual(classes.count("SUCCEEDED_SYNTHETIC"), 1, classes)
        blocked = {
            "BLOCKED_CLAIM_WITHOUT_TERMINAL_STATUS",
            "BLOCKED_CORRUPT_OR_INCOMPLETE_CLAIM",
            "BLOCKED_UNKNOWN_POST_DISPATCH_STATE",
        }
        self.assertEqual(sum(classification in blocked for classification in classes), 1, classes)
        self.assertEqual(len(self._dispatch_lines()), 1)

    def test_crash_after_claim_is_not_retried_on_process_restart(self) -> None:
        self._make_request()
        interrupted = self._process("--test-interrupt-after", "claim")
        self.assertEqual(interrupted.returncode, 86)
        restarted = self._process()
        self.assertEqual(restarted.returncode, 3, restarted.stderr)
        result = json.loads(restarted.stdout)
        self.assertEqual(result["classification"], "BLOCKED_CLAIM_WITHOUT_TERMINAL_STATUS")
        self.assertEqual(len(self._dispatch_lines()), 0)

    def test_ambiguous_post_dispatch_state_is_not_retried(self) -> None:
        self._make_request()
        interrupted = self._process("--test-interrupt-after", "dispatch-start")
        self.assertEqual(interrupted.returncode, 86)
        restarted = self._process()
        self.assertEqual(restarted.returncode, 3, restarted.stderr)
        result = json.loads(restarted.stdout)
        self.assertEqual(result["classification"], "BLOCKED_UNKNOWN_POST_DISPATCH_STATE")
        self.assertEqual(result["state"], "DISPATCHING_SYNTHETIC")
        self.assertEqual(len(self._dispatch_lines()), 0)

    def test_failed_synthetic_execution_is_terminal_and_not_replayed(self) -> None:
        self._make_request()
        failed = self._process("--target-mode", "failure")
        self.assertEqual(failed.returncode, 4)
        status = json.loads(failed.stdout)["status"]
        self.assertEqual(status["state"], "FAILED_SYNTHETIC")
        replay = self._process()
        self.assertEqual(replay.returncode, 4, replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["state"], "FAILED_SYNTHETIC")
        self.assertEqual(len(self._dispatch_lines()), 1)

    def test_success_state_with_nonzero_return_code_is_blocked(self) -> None:
        self._make_request()
        self.assertEqual(self._process().returncode, 0)
        status_path = self._record_path("terminal")
        status = json.loads(status_path.read_text(encoding="utf-8"))
        status["target_return_code"] = 17
        status_path.write_text(json.dumps(status), encoding="utf-8")

        replay = self._process()
        self.assertEqual(replay.returncode, 3, replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["classification"], "BLOCKED_UNKNOWN_POST_DISPATCH_STATE")
        self.assertEqual(len(self._dispatch_lines()), 1)

    def test_mismatched_attempt_identity_is_blocked(self) -> None:
        self._make_request()
        for kind in ("claim", "dispatching", "terminal"):
            with self.subTest(record=kind):
                state_dir = self.run_dir / kind
                self.assertEqual(self._process_at(state_dir).returncode, 0)
                request_id = json.loads(self.request_file.read_text(encoding="utf-8"))[
                    "research_request"]["request_id"]
                record_path = state_dir / f"{request_id.removeprefix('sha256:')}.{kind}.json"
                record = json.loads(record_path.read_text(encoding="utf-8"))
                record["attempt_id"] = str(uuid.uuid4())
                record_path.write_text(json.dumps(record), encoding="utf-8")

                replay = self._process_at(state_dir)
                self.assertEqual(replay.returncode, 3, replay.stderr)
                self.assertEqual(
                    json.loads(replay.stdout)["classification"],
                    "BLOCKED_REQUEST_ID_COLLISION_OR_CONTENT_CHANGE",
                )

    def test_tampered_request_identity_fails_before_claim(self) -> None:
        envelope = self._make_request()
        envelope["research_request"]["allowed_research_families"] = ["OTHER"]
        self.request_file.write_text(json.dumps(envelope), encoding="utf-8")
        result = self._process()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(self.state_dir.glob("*.claim.json")) if self.state_dir.exists() else [], [])
        self.assertEqual(len(self._dispatch_lines()), 0)

    def test_nonterminal_or_unreadable_claim_fails_closed(self) -> None:
        envelope = self._make_request()
        request_id = envelope["research_request"]["request_id"].removeprefix("sha256:")
        self.state_dir.mkdir()
        (self.state_dir / f"{request_id}.claim.json").write_text("{", encoding="utf-8")
        replay = self._process()
        self.assertEqual(replay.returncode, 3, replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["classification"], "BLOCKED_CORRUPT_OR_INCOMPLETE_CLAIM")
        self.assertEqual(len(self._dispatch_lines()), 0)

    def test_corrupt_dispatch_and_terminal_records_exit_nonzero(self) -> None:
        self._make_request()
        self.assertEqual(self._process().returncode, 0)
        terminal_path = self._record_path("terminal")
        terminal_record = terminal_path.read_bytes()
        terminal_path.write_text("{", encoding="utf-8")
        corrupt_terminal_replay = self._process()
        self.assertEqual(corrupt_terminal_replay.returncode, 3)
        self.assertEqual(
            json.loads(corrupt_terminal_replay.stdout)["classification"],
            "BLOCKED_UNKNOWN_POST_DISPATCH_STATE",
        )

        terminal_path.write_bytes(terminal_record)
        dispatch_path = self._record_path("dispatching")
        dispatch_path.write_text("{", encoding="utf-8")
        corrupt_dispatch_replay = self._process()
        self.assertEqual(corrupt_dispatch_replay.returncode, 3)
        self.assertEqual(
            json.loads(corrupt_dispatch_replay.stdout)["classification"],
            "BLOCKED_UNKNOWN_POST_DISPATCH_STATE",
        )
        self.assertEqual(len(self._dispatch_lines()), 1)

    def test_actual_host_filesystem_exclusive_claim_and_immutable_status_marker(self) -> None:
        probe_dir = self.run_dir / "filesystem-proof"
        probe_dir.mkdir()
        claim_path = probe_dir / "single.claim"
        child_code = (
            "import os,sys; fd=os.open(sys.argv[1],os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600); "
            "os.write(fd,b'claim'); os.fsync(fd); os.close(fd)"
        )
        processes = [
            subprocess.Popen([PYTHON, "-c", child_code, str(claim_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for _ in range(24)
        ]
        outcomes = [process.communicate(timeout=30) + (process.returncode,) for process in processes]
        self.assertEqual(sum(1 for _, _, code in outcomes if code == 0), 1, outcomes)
        self.assertEqual(claim_path.read_bytes(), b"claim")

        status_path = probe_dir / "terminal.json"
        handoff._durable_json_create(status_path, {"state": "SUCCEEDED_SYNTHETIC"})
        self.assertEqual(json.loads(status_path.read_text())["state"], "SUCCEEDED_SYNTHETIC")
        with self.assertRaises(FileExistsError):
            handoff._durable_json_create(status_path, {"state": "FAILED_SYNTHETIC"})

if __name__ == "__main__":
    unittest.main()
