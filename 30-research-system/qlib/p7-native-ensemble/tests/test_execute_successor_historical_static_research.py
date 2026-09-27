from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[1] / "execute_successor_historical_static_research.py"
)
sys.path.insert(0, str(MODULE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("p7_successor_execution", MODULE_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)

REPO = Path(__file__).parents[4]


class SuccessorOneShotExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.authorities = runner.load_authorities(REPO)

    def base_seal(self) -> dict[str, object]:
        contract = self.authorities.input_contract
        return {
            "successor_protocol_sha256": runner.PROTOCOL_SHA256,
            "successor_input_contract_sha256": runner.INPUT_CONTRACT_SHA256,
            "successor_population_index_sha256": runner.POPULATION_SHA256,
            "label_validity_mask_sha256": runner.LABEL_MASK_SHA256,
            "execution_code_commit_sha": "code-commit",
            "authority_commit_sha": "authority-commit",
            "execution_script_sha256": "script-sha",
            "qlib_source_sha": runner.QLIB_SOURCE_SHA,
            "expected_dependency_versions": dict(runner.EXPECTED_DEPENDENCIES),
            "artifacts": {
                "candidates": [
                    {
                        "slot": item["slot"],
                        "candidate_id": item["candidate_id"],
                        "path": f"/synthetic/{item['slot']}.pkl",
                        "sha256": item["source_prediction_sha256"],
                    }
                    for item in contract["candidate_snapshot"]["bindings"]
                ],
                "control": {
                    "path": "/synthetic/control.pkl",
                    "sha256": contract["control"]["source_prediction_sha256"],
                },
                "label": {
                    "path": "/synthetic/label.pkl",
                    "sha256": contract["label_authority"]["label_artifact_sha256"],
                },
                "population": {
                    "path": "/synthetic/population.parquet",
                    "sha256": contract["successor_population"]["artifact_byte_sha256"],
                },
            },
        }

    @staticmethod
    def runtime(**overrides: object) -> runner.RuntimeAuthority:
        values: dict[str, object] = {
            "current_head": "authority-commit",
            "worktree_clean": True,
            "execution_commit_on_origin_main": True,
            "authority_commit_on_origin_main": True,
            "script_sha256": "script-sha",
            "dependency_versions": dict(runner.EXPECTED_DEPENDENCIES),
        }
        values.update(overrides)
        return runner.RuntimeAuthority(**values)

    def assert_rejected(
        self,
        code: str,
        seal: dict[str, object],
        runtime: runner.RuntimeAuthority | None = None,
    ) -> None:
        with self.assertRaises(runner.GateError) as raised:
            runner.validate_provenance_seal(
                self.authorities, seal, runtime or self.runtime()
            )
        self.assertEqual(raised.exception.code, code)

    def test_frozen_authorities_are_bound_without_outcome_access(self) -> None:
        self.assertEqual(
            self.authorities.protocol["input_contract"]["row_count"], 374477
        )
        self.assertEqual(
            self.authorities.input_contract["candidate_snapshot"]["candidate_count"],
            17,
        )

    def test_missing_provenance_seal_rejects_real_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(runner.GateError) as raised:
                runner.load_provenance_seal(Path(directory))
        self.assertEqual(raised.exception.code, "EXECUTION_PROVENANCE_SEAL_MISSING")

    def test_protocol_mismatch_rejected(self) -> None:
        seal = self.base_seal()
        seal["successor_protocol_sha256"] = "wrong"
        self.assert_rejected("PROTOCOL_MISMATCH", seal)

    def test_input_contract_mismatch_rejected(self) -> None:
        seal = self.base_seal()
        seal["successor_input_contract_sha256"] = "wrong"
        self.assert_rejected("INPUT_CONTRACT_MISMATCH", seal)

    def test_script_hash_mismatch_rejected(self) -> None:
        seal = self.base_seal()
        seal["execution_script_sha256"] = "wrong"
        self.assert_rejected("SCRIPT_HASH_MISMATCH", seal)

    def test_dirty_worktree_rejected(self) -> None:
        self.assert_rejected(
            "DIRTY_WORKTREE_FORBIDDEN",
            self.base_seal(),
            self.runtime(worktree_clean=False),
        )

    def test_head_authority_mismatch_rejected(self) -> None:
        self.assert_rejected(
            "HEAD_AUTHORITY_MISMATCH",
            self.base_seal(),
            self.runtime(current_head="other-head"),
        )

    def test_authorized_but_unbound_artifacts_reject(self) -> None:
        seal = self.base_seal()
        seal["artifacts"]["candidates"][0]["sha256"] = "wrong"  # type: ignore[index]
        self.assert_rejected("CANDIDATE_ARTIFACT_BINDING_MISMATCH", seal)

    def test_second_attempt_is_rejected_after_marker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "one-shot"
            runner.begin_one_shot(output, {"state": "PRE_OUTCOME_PREFLIGHT"})
            with self.assertRaises(runner.GateError) as raised:
                runner.begin_one_shot(output, {"state": "PRE_OUTCOME_PREFLIGHT"})
            self.assertEqual(raised.exception.code, "SECOND_REAL_EXECUTION_FORBIDDEN")

    def test_post_marker_failure_is_sealed_and_retry_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "one-shot"

            def fail_after_marker() -> dict[str, object]:
                raise RuntimeError("synthetic post-marker failure")

            with self.assertRaisesRegex(RuntimeError, "synthetic post-marker"):
                runner.run_one_shot(
                    output,
                    {"state": "PRE_OUTCOME_PREFLIGHT"},
                    fail_after_marker,
                )
            result = json.loads((output / "final-result.json").read_text())
            self.assertEqual(result["state"], "FAILED_SEALED_INCONCLUSIVE")
            self.assertEqual(
                result["result_classification"],
                "STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE",
            )
            with self.assertRaises(runner.GateError) as raised:
                runner.begin_one_shot(output, {"state": "PRE_OUTCOME_PREFLIGHT"})
            self.assertEqual(raised.exception.code, "SECOND_REAL_EXECUTION_FORBIDDEN")

    def test_classification_uses_exact_six_frozen_gates(self) -> None:
        stats = {
            "spa": {"consistent": 0.05},
            "walkforward": {"positive_fraction": 0.6, "median_mean_delta": 0.01},
            "cpcv": {"positive_fraction": 0.6, "median_mean_delta": 0.01},
        }
        classification, gates = runner.classify(
            self.authorities.protocol, 0.01, stats
        )
        self.assertEqual(classification, "STATIC_ENSEMBLE_RESEARCH_SUPPORTIVE")
        self.assertEqual(len(gates), 6)
        stats["cpcv"]["median_mean_delta"] = 0.0
        classification, _ = runner.classify(self.authorities.protocol, 0.01, stats)
        self.assertEqual(
            classification, "STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE"
        )


if __name__ == "__main__":
    unittest.main()
