from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "project_rdagent_candidate_v3", ROOT / "project_rdagent_candidate_v3.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def digest(character: str) -> str:
    return character * 64


def content(role: str, character: str) -> dict[str, str]:
    return {"logical_role": role, "sha256": digest(character)}


def dvc(value: str = "fixture") -> dict[str, str]:
    return {"algorithm": "sha256", "value": value}


def candidate_source() -> dict[str, object]:
    artifact = lambda role, character: {  # noqa: E731
        **content(role, character),
        "dvc_output_identity": dvc(role),
    }
    return {
        "candidate_contract_version": "P3_CANDIDATE_TO_P2_CONTRACT_V3",
        "research_producer_identity": {
            "producer_kind": "RD_AGENT",
            "rdagent_research_identity": {
                "research_mode": "fin_quant",
                "scenario_family": "P3_US_RAGGED_QLIB",
                "hypothesis_content_sha256": digest("1"),
                "task_content_identities": [content("research_task", "2")],
                "experiment_structure_sha256": digest("3"),
                "generated_research_code_identities": [content("factor_code", "4")],
                "parent_lineage_content_identities": [],
            },
        },
        "qlib_recorder_identity": {
            "experiment_id": "fixture-experiment",
            "run_id": "fixture-run",
            "status": "FINISHED",
        },
        "artifact_identity_bundle": {
            "producer_kind": "RD_AGENT",
            "rdagent_artifact_identity": {
                "dvc_stage_name": "p3_rdagent_us_quant_research",
                "dvc_lock_file_sha256": digest("5"),
                "dvc_stage_lock_entry_sha256": digest("6"),
                "dvc_run_root_output_identity": dvc("run-root"),
                "selected_static_templates": [
                    {
                        "relative_name": "factor_template/conf_baseline.yaml",
                        "sha256": "ddfb7dd65875636db4cc0acb2471ae1c48d07a30b88b60380ef2a355fdf3d73c",
                    }
                ],
                "rendered_qlib_execution_config_sha256": digest("7"),
                "generated_research_code_artifacts": [artifact("factor_code", "4")],
                "serialized_model_artifact": artifact("qlib_params.pkl", "8"),
                "prediction_artifact": artifact("qlib_pred.pkl", "9"),
            },
        },
        "dataset_identity_bundle": {
            "provider_build_report_sha256": "eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142",
            "calendar_sha256": "d4c0c100af851245f6f894e275e5d494d7e1cbd07f82d342c034cbdf7b7bfa4d",
            "all_instruments_sha256": "24d3a9010b725f8121ae1a999916bd0b6e76923eb9fad85be7e57d8653cc2cbc",
            "p2_pit_instruments_sha256": "e771f73b91664b26584e66c42eb007c4276c492071172e7d6594bc900f01f875",
            "date_bounds": {"start": "2015-01-02", "end": "2024-12-31"},
            "security_identity_count": 730,
            "membership_range_count": 745,
            "member_session_row_count": 1267963,
            "p3_dvc_dependency_identities": [
                {"logical_role": "provider_build_report", "dvc_identity": dvc("provider")},
                {"logical_role": "qlib_provider", "dvc_identity": dvc("qlib")},
            ],
        },
        "runtime_identity_bundle": {
            "producer_kind": "RD_AGENT",
            "rdagent_runtime_identity": {
                "rdagent_source_git_sha": MODULE.RDAGENT_SOURCE_SHA,
                "rdagent_installed_wheel_sha256": "6d4b78037016951d21879249152fee21df90e5dca0a752e233026a41afe64395",
                "rdagent_environment_freeze_sha256": "1d60835745fad44b917eff46918719f8c1c392fb05747f06fb4dde8cb8c1f67e",
                "qlib_source_git_sha": "2fb9380b342556ddb50a4b24e4fe8655d548b2b8",
                "llm_execution_identity": {
                    "litellm_version": "1.100.1",
                    "llm_configuration_sha256": digest("a"),
                    "native_trace_artifact_sha256": digest("b"),
                    "chat_logical_slot": "aq-brain-local",
                    "chat_route_mode": "LOCAL_ONLY",
                    "chat_resolutions": [
                        {
                            "provider": "ollama",
                            "requested_model": "aq-brain-local",
                            "resolved_model": "qwen2.5-coder:7b",
                            "provider_model_identity_kind": "LOCAL_DIGEST",
                            "provider_model_identity": digest("c"),
                            "call_count": 1,
                        }
                    ],
                    "fallback_occurred": False,
                    "fallback_reason_counts": [],
                    "embedding_logical_slot": "aq-embedding-local",
                    "embedding_resolution": {
                        "provider": "ollama",
                        "requested_model": "aq-embedding-local",
                        "resolved_model": "qwen3-embedding:0.6b",
                        "provider_model_identity_kind": "LOCAL_DIGEST",
                        "provider_model_identity": digest("d"),
                        "dimensions": 1024,
                    },
                    "embedding_epoch_sha256": digest("e"),
                },
            },
        },
        "p2_target_and_eligibility_boundary": {
            "target_protocol_version": "P2_CERTIFICATION_PROTOCOL_V1",
            "protocol_sha256": "0fc22f259b27499f6d2d344767b179a5fa2c4c55daf15bb593ba0c9001e2289d",
            "protocol_activation_sha256": "d1ac67558f59d917eb71d666e48967f8f20bafc48bfc1ff616b7c85e262eef54",
            "protocol_freeze_merge_sha": "8cd703b4108d2e377d146de8384b63c0355e93a6",
            "protocol_freeze_authority": "P2_CERTIFICATION",
            "candidate_eligibility_status": "INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION",
            "eligibility_authority": "P2_CERTIFICATION",
            "historical_research_test_accessed": True,
            "historical_research_test_status": "CONSUMED_AS_RESEARCH_EVIDENCE",
            "sealed_oos_start": "2026-09-14",
            "sealed_oos_accessed_by_p3": False,
            "p3_can_issue_certified": False,
            "p3_can_edit_protocol": False,
            "p3_can_promote_to_production": False,
        },
    }


class RDagentCandidateProjectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.artifacts = Path(self.temp.name)
        for name in ("task", "params.pkl", "dataset", "pred.pkl"):
            (self.artifacts / name).write_bytes(f"fixture-{name}".encode())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def project(self, source: dict[str, object] | None = None) -> dict[str, object]:
        return MODULE.project_rdagent_candidate(source or candidate_source(), self.artifacts, ROOT)

    def test_complete_fixture_projects_and_validates(self) -> None:
        candidate = self.project()
        self.assertEqual(MODULE.candidate_id(candidate), candidate["candidate_id"])
        artifacts = candidate["artifact_identity_bundle"]["rdagent_artifact_identity"]
        self.assertEqual(MODULE._sha256(self.artifacts / "params.pkl"), artifacts["serialized_model_artifact"]["sha256"])
        self.assertEqual(MODULE._sha256(self.artifacts / "pred.pkl"), artifacts["prediction_artifact"]["sha256"])

    def test_unfinished_recorder_is_rejected(self) -> None:
        source = candidate_source()
        source["qlib_recorder_identity"]["status"] = "RUNNING"
        with self.assertRaisesRegex(ValueError, "not FINISHED"):
            self.project(source)

    def test_required_recorder_artifacts_are_rejected_when_missing(self) -> None:
        for name in ("params.pkl", "dataset", "pred.pkl"):
            with self.subTest(name=name):
                path = self.artifacts / name
                original = path.read_bytes()
                path.unlink()
                with self.assertRaisesRegex(ValueError, name.replace(".", r"\.")):
                    self.project()
                path.write_bytes(original)

    def test_wrong_rdagent_source_identity_is_rejected(self) -> None:
        source = candidate_source()
        source["runtime_identity_bundle"]["rdagent_runtime_identity"]["rdagent_source_git_sha"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source identity mismatch"):
            self.project(source)

    def test_wrong_producer_branch_is_rejected(self) -> None:
        source = candidate_source()
        source["artifact_identity_bundle"]["producer_kind"] = "FORMULAIC_ALPHA"
        with self.assertRaisesRegex(ValueError, "not the RD_AGENT producer branch"):
            self.project(source)

    def test_supplied_and_post_projection_candidate_id_mismatch_are_rejected(self) -> None:
        source = candidate_source()
        source["candidate_id"] = "sha256:" + digest("f")
        with self.assertRaisesRegex(ValueError, "supplied Candidate V3 identity mismatch"):
            self.project(source)
        candidate = self.project()
        candidate["candidate_id"] = "sha256:" + digest("f")
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            MODULE.validate_candidate(candidate, ROOT)


if __name__ == "__main__":
    unittest.main()
