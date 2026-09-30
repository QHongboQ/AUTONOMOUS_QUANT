from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "project_rdagent_candidate_v4", ROOT / "project_rdagent_candidate_v4.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


V1_TO_V3_HASHES = {
    "candidate-contract-v1.md": "0085963ad80b3e8ca526e8749be1eda6a157e7e15908462c8af5633277b8a364",
    "candidate-contract-v2.md": "a5ca1f92684cc2eec3bed9024e4c9f221cc23b4c4992029d4d41963ac088837a",
    "candidate-contract-v3.md": "49974251f0094c0a3d173369ba806e5a44715a3b4433e6c6241e10db54fc16e2",
    "candidate-contract-v1.schema.json": "a30630d41596d5d89da1b4291b07489585e0ca23fbc78ddd822404eb0e3cb795",
    "candidate-contract-v2.schema.json": "a7f1c175c68188e641eacc61da2ba2683a9b1b6d6021cf1faa25f5543818266b",
    "candidate-contract-v3.schema.json": "fb0775c4b8c9a947eb2023d66d3b2c17fda3b3215edcf31a36f3d30ef87fc8f2",
}


def digest(character: str) -> str:
    return character * 64


def content(role: str, character: str) -> dict[str, str]:
    return {"logical_role": role, "sha256": digest(character)}


def dvc(value: str = "fixture") -> dict[str, str]:
    return {"algorithm": "sha256", "value": value}


def candidate_source() -> dict[str, object]:
    return {
        "candidate_contract_version": "P3_CANDIDATE_TO_P2_CONTRACT_V4",
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
            "experiment_id": "1",
            "run_id": "fixture-run",
            "status": "FINISHED",
        },
        "artifact_identity_bundle": {
            "producer_kind": "RD_AGENT",
            "rdagent_artifact_identity": {
                "selected_static_templates": [
                    {
                        "relative_name": "factor_template/conf_baseline.yaml",
                        "sha256": "e3fa90de82f79d2d372cb6aab287cb117712a76c684bf3b8c415aef0f86273f2",
                    }
                ],
                "rendered_qlib_execution_config_sha256": digest("5"),
                "generated_research_code_artifacts": [content("factor_code", "4")],
                "serialized_model_artifact": content("qlib_params.pkl", "6"),
                "prediction_artifact": content("qlib_pred.pkl", "7"),
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
                "rdagent_version": "1.0.0",
                "rdagent_release_git_sha": "484776c211e4fbbeef03e0ec00d6bbee7362a4f4",
                "qlib_source_git_sha": "2fb9380b342556ddb50a4b24e4fe8655d548b2b8",
                "backend": "rdagent.oai.backend.LiteLLMAPIBackend",
                "llm_execution_identity": {
                    "litellm_version": "1.103.1",
                    "llm_configuration_sha256": digest("8"),
                    "native_trace_artifact_sha256": digest("9"),
                    "chat_route_mode": "CLOUD_ONLY",
                    "chat_execution": {
                        "provider": "deepseek",
                        "requested_model": "deepseek/deepseek-chat",
                        "resolved_model": "deepseek/deepseek-chat",
                        "provider_model_identity_kind": "RESPONSE_MODEL_ONLY",
                        "provider_model_identity": "deepseek/deepseek-chat",
                        "call_count": 1,
                        "fallback_occurred": False,
                        "fallback_reason_counts": [],
                    },
                    "configured_embedding": {
                        "provider": "ollama",
                        "requested_model": "ollama/qwen3-embedding:0.6b",
                        "resolved_model": "ollama/qwen3-embedding:0.6b",
                        "configuration_sha256": digest("a"),
                    },
                    "embedding_execution": {"executed": False},
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


class RDagentCandidateV4ProjectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.artifacts = Path(self.temp.name)
        for name in ("task", "params.pkl", "dataset", "pred.pkl"):
            (self.artifacts / name).write_bytes(f"fixture-{name}".encode())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def project(self, source: dict[str, object] | None = None) -> dict[str, object]:
        return MODULE.project_rdagent_candidate(source or candidate_source(), self.artifacts, ROOT)

    def test_native_deepseek_candidate_projects(self) -> None:
        candidate = self.project()
        self.assertEqual(MODULE.candidate_id(candidate), candidate["candidate_id"])
        execution = candidate["runtime_identity_bundle"]["rdagent_runtime_identity"]["llm_execution_identity"]
        self.assertEqual("deepseek", execution["chat_execution"]["provider"])

    def test_configured_embedding_can_be_unexecuted(self) -> None:
        candidate = self.project()
        execution = candidate["runtime_identity_bundle"]["rdagent_runtime_identity"]["llm_execution_identity"]
        self.assertEqual({"executed": False}, execution["embedding_execution"])

    def test_old_rdagent_sha_is_rejected(self) -> None:
        source = candidate_source()
        source["runtime_identity_bundle"]["rdagent_runtime_identity"]["rdagent_release_git_sha"] = (
            "32b3d395e73d9db5eee3fe9063d69aec0fdc83bd"
        )
        with self.assertRaisesRegex(ValueError, "rdagent_release_git_sha"):
            self.project(source)

    def test_old_v1_template_identity_is_rejected(self) -> None:
        source = candidate_source()
        source["artifact_identity_bundle"]["rdagent_artifact_identity"]["selected_static_templates"][0][
            "sha256"
        ] = "ddfb7dd65875636db4cc0acb2471ae1c48d07a30b88b60380ef2a355fdf3d73c"
        with self.assertRaisesRegex(ValueError, "schema rejection"):
            self.project(source)

    def test_deepseek_cannot_be_mislabeled_as_openai(self) -> None:
        source = candidate_source()
        source["runtime_identity_bundle"]["rdagent_runtime_identity"]["llm_execution_identity"]["chat_execution"]["provider"] = "openai"
        with self.assertRaisesRegex(ValueError, "schema rejection"):
            self.project(source)

    def test_unfinished_recorder_is_rejected(self) -> None:
        source = candidate_source()
        source["qlib_recorder_identity"]["status"] = "RUNNING"
        with self.assertRaisesRegex(ValueError, "not FINISHED"):
            self.project(source)

    def assert_missing_artifact_is_rejected(self, name: str) -> None:
        path = self.artifacts / name
        original = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(ValueError, name.replace(".", r"\.")):
            self.project()
        path.write_bytes(original)

    def test_missing_task_is_rejected(self) -> None:
        self.assert_missing_artifact_is_rejected("task")

    def test_missing_params_is_rejected(self) -> None:
        self.assert_missing_artifact_is_rejected("params.pkl")

    def test_missing_dataset_is_rejected(self) -> None:
        self.assert_missing_artifact_is_rejected("dataset")

    def test_missing_prediction_is_rejected(self) -> None:
        self.assert_missing_artifact_is_rejected("pred.pkl")

    def test_candidate_id_mismatch_is_rejected(self) -> None:
        source = candidate_source()
        source["candidate_id"] = "sha256:" + digest("f")
        with self.assertRaisesRegex(ValueError, "supplied Candidate V4 identity mismatch"):
            self.project(source)

    def test_producer_branch_mismatch_is_rejected(self) -> None:
        source = candidate_source()
        source["artifact_identity_bundle"]["producer_kind"] = "FORMULAIC_ALPHA"
        with self.assertRaisesRegex(ValueError, "not the RD_AGENT producer branch"):
            self.project(source)

    def test_v1_to_v3_bytes_and_formulaic_references_remain_unchanged(self) -> None:
        for name, expected in V1_TO_V3_HASHES.items():
            self.assertEqual(expected, hashlib.sha256((ROOT / name).read_bytes()).hexdigest())
        schema = json.loads((ROOT / "candidate-contract-v4.schema.json").read_text())
        self.assertEqual(8, len(schema["required"]))
        self.assertIn(
            "candidate-contract-v3.schema.json#/$defs/formulaicArtifactIdentityBundle",
            json.dumps(schema),
        )


if __name__ == "__main__":
    unittest.main()
