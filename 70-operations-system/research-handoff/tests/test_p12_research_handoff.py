from __future__ import annotations

import json
import os
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
        for record_kind in ("claim", "dispatching", "terminal"):
            self.assertEqual(json.loads(self._record_path(record_kind).read_text())["standing_policy_id"], policy_id)

        replay = self._process()
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertEqual(json.loads(replay.stdout)["classification"], "REPLAY_TERMINAL_NO_DISPATCH")
        self.assertEqual(len(self._dispatch_lines()), 1)

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
