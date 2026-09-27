from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal


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
        cls.router = runner.load_module(
            REPO
            / "30-research-system/qlib/p7-native-ensemble/session_local_router.py",
            "p7_successor_execution_test_router",
        )

    @staticmethod
    def synthetic_index(
        sessions: list[str], instruments: list[str]
    ) -> pd.MultiIndex:
        return pd.MultiIndex.from_product(
            [pd.to_datetime(sessions), instruments],
            names=["datetime", "instrument"],
        )

    def base_seal(self) -> dict[str, object]:
        contract = self.authorities.input_contract
        return {
            "successor_protocol_sha256": runner.PROTOCOL_SHA256,
            "successor_input_contract_sha256": runner.INPUT_CONTRACT_SHA256,
            "signal_construction_population_index_sha256": (
                runner.SIGNAL_CONSTRUCTION_POPULATION_SHA256
            ),
            "evaluation_population_index_sha256": (
                runner.EVALUATION_POPULATION_SHA256
            ),
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
                "signal_construction_population": {
                    "path": "/synthetic/construction-population.parquet",
                    "sha256": "a" * 64,
                },
                "evaluation_population": {
                    "path": "/synthetic/evaluation-population.parquet",
                    "sha256": contract["evaluation_population"][
                        "artifact_byte_sha256"
                    ],
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
            self.authorities.protocol["input_contract"][
                "signal_construction_row_count"
            ],
            374591,
        )
        self.assertEqual(
            self.authorities.protocol["input_contract"]["evaluation_row_count"],
            374477,
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

    def test_both_population_semantic_identities_are_required(self) -> None:
        seal = self.base_seal()
        seal["signal_construction_population_index_sha256"] = "wrong"
        self.assert_rejected("SIGNAL_CONSTRUCTION_POPULATION_MISMATCH", seal)
        seal = self.base_seal()
        seal["evaluation_population_index_sha256"] = "wrong"
        self.assert_rejected("EVALUATION_POPULATION_MISMATCH", seal)

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

    def test_signal_is_constructed_before_evaluation_projection(self) -> None:
        construction = self.synthetic_index(["2024-01-02"], ["A", "B", "C", "D"])
        evaluation = construction[:-1]
        raw = {
            "one": pd.DataFrame({"score": [1.0, 2.0, 3.0, 100.0]}, index=construction),
            "two": pd.DataFrame({"score": [4.0, 1.0, 3.0, 2.0]}, index=construction),
        }
        full, corrected, projected, _ = runner.construct_then_project_ensemble(
            raw, construction, evaluation, self.router
        )
        prohibited, _ = self.router.combine_session_local_nonconstant(projected)
        assert_frame_equal(corrected, full.loc[evaluation])
        self.assertFalse(np.allclose(corrected["score"], prohibited["score"]))

    def test_constant_component_rankic_is_secondary_nan_without_imputation(self) -> None:
        index = self.synthetic_index(
            ["2024-01-02", "2024-01-03"], ["A", "B", "C"]
        )
        raw = {
            "constant_then_active": pd.DataFrame(
                {"score": [7.0, 7.0, 7.0, 1.0, 2.0, 3.0]}, index=index
            ),
            "alpha": pd.DataFrame(
                {"score": [1.0, 2.0, 3.0, 1.0, 3.0, 2.0]}, index=index
            ),
            "beta": pd.DataFrame(
                {"score": [3.0, 1.0, 2.0, 2.0, 1.0, 3.0]}, index=index
            ),
        }
        _, ensemble, projected, _ = runner.construct_then_project_ensemble(
            raw, index, index, self.router
        )
        label = pd.Series([1.0, 2.0, 3.0, 2.0, 1.0, 3.0], index=index)
        component = runner.rank_ic(
            projected["constant_then_active"]["score"], label, required=False
        )
        primary = runner.rank_ic(ensemble["score"], label, required=False)
        summary = runner.summarize_component_rank_ic(component)
        self.assertTrue(np.isnan(component.iloc[0]))
        self.assertEqual(summary["finite_valid_session_count"], 1)
        self.assertTrue(np.isfinite(primary).all())
        stats = {
            "spa": {"consistent": 0.05},
            "walkforward": {"positive_fraction": 0.6, "median_mean_delta": 0.01},
            "cpcv": {"positive_fraction": 0.6, "median_mean_delta": 0.01},
        }
        classification, _ = runner.classify(self.authorities.protocol, 0.01, stats)
        self.assertEqual(classification, "STATIC_ENSEMBLE_RESEARCH_SUPPORTIVE")

    def test_structural_nan_makes_mcs_unavailable_without_filtering(self) -> None:
        index = pd.to_datetime(["2024-01-02", "2024-01-03"])
        components = pd.DataFrame(
            {"candidate": [np.nan, 0.1]}, index=index
        )
        ensemble = pd.Series([0.2, 0.3], index=index)
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(runner.subprocess, "check_output") as invoked:
                result = runner.mcs_result(
                    components, ensemble, self.authorities.protocol, Path(directory)
                )
        invoked.assert_not_called()
        self.assertEqual(
            result["status"], "NOT_AVAILABLE_SECONDARY_INCOMPLETE_LOSS_MATRIX"
        )
        self.assertEqual(result["primary_classification_effect"], "NONE")

    def test_mcs_runtime_failure_is_secondary(self) -> None:
        with mock.patch.object(
            runner, "mcs_result", side_effect=RuntimeError("synthetic mcs failure")
        ):
            result = runner.run_mcs_secondary(
                pd.DataFrame({"candidate": [0.1]}),
                pd.Series([0.2]),
                self.authorities.protocol,
                Path("synthetic"),
            )
        self.assertEqual(result["status"], "FAILED_SECONDARY")
        self.assertEqual(result["primary_classification_effect"], "NONE")

    def test_portfolio_failure_is_secondary_after_primary_lock(self) -> None:
        classification = "STATIC_ENSEMBLE_RESEARCH_SUPPORTIVE"
        with mock.patch.object(
            runner, "run_portfolio", side_effect=RuntimeError("synthetic portfolio")
        ):
            result = runner.run_portfolio_secondary(
                pd.Series(dtype=float), {}, {}, Path("synthetic")
            )
        self.assertEqual(result["status"], "FAILED_SECONDARY")
        self.assertEqual(result["primary_classification_effect"], "NONE")
        self.assertEqual(classification, "STATIC_ENSEMBLE_RESEARCH_SUPPORTIVE")

    def test_lineage_failure_is_secondary_after_primary_lock(self) -> None:
        classification = "STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE"
        with mock.patch.object(
            runner, "record_lineage", side_effect=RuntimeError("synthetic lineage")
        ):
            result = runner.record_lineage_secondary(
                Path("synthetic"), classification, 0.0, self.authorities
            )
        self.assertEqual(result["status"], "FAILED_SECONDARY")
        self.assertIsNone(result["run_id"])
        self.assertEqual(result["primary_classification_effect"], "NONE")
        self.assertEqual(classification, "STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE")


if __name__ == "__main__":
    unittest.main()
