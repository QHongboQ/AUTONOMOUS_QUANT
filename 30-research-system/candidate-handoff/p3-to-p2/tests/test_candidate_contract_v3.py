from __future__ import annotations

import copy
import hashlib
import json
import os
import unittest
from pathlib import Path

import rfc8785
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


CONTRACT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRIVATE_ROOT = (
    Path("/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001")
    if Path("/mnt/d/AQ_DATA").exists()
    else Path("D:/AQ_DATA/P3/candidate-v3-materialization-001")
)
PRIVATE_ROOT = Path(os.environ.get("AQ_CANDIDATE_V3_ROOT", str(DEFAULT_PRIVATE_ROOT)))


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_id(candidate: dict[str, object]) -> str:
    projection = {key: value for key, value in candidate.items() if key != "candidate_id"}
    if len(projection) != 7:
        raise AssertionError("Candidate ID projection must contain exactly seven fields")
    return "sha256:" + hashlib.sha256(rfc8785.dumps(projection)).hexdigest()


def nested_keys(value: object) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            result.add(key.lower())
            result.update(nested_keys(child))
    elif isinstance(value, list):
        for child in value:
            result.update(nested_keys(child))
    return result


class CandidateContractV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        base = "https://qhongboq.github.io/AUTONOMOUS_QUANT/"
        cls.v1 = load_json(CONTRACT_ROOT / "candidate-contract-v1.schema.json")
        cls.v2 = load_json(CONTRACT_ROOT / "candidate-contract-v2.schema.json")
        cls.v3 = load_json(CONTRACT_ROOT / "candidate-contract-v3.schema.json")
        registry = Registry().with_resources(
            [
                (base + "candidate-contract-v1.schema.json", Resource.from_contents(cls.v1)),
                (base + "candidate-contract-v2.schema.json", Resource.from_contents(cls.v2)),
                (base + "candidate-contract-v3.schema.json", Resource.from_contents(cls.v3)),
            ]
        )
        Draft202012Validator.check_schema(cls.v3)
        cls.validator = Draft202012Validator(cls.v3, registry=registry)
        paths = sorted((PRIVATE_ROOT / "candidates").glob("candidate-*.json"))
        if len(paths) != 17:
            raise AssertionError(f"expected 17 private Candidate files, found {len(paths)}")
        cls.candidates = [load_json(path) for path in paths]

    def assert_rejected(self, candidate: dict[str, object]) -> None:
        schema_valid = self.validator.is_valid(candidate)
        id_valid = candidate_id(candidate) == candidate.get("candidate_id")
        self.assertFalse(schema_valid and id_valid)

    def test_exact_top_level_contract(self) -> None:
        required = {
            "candidate_contract_version",
            "candidate_id",
            "research_producer_identity",
            "qlib_recorder_identity",
            "artifact_identity_bundle",
            "dataset_identity_bundle",
            "runtime_identity_bundle",
            "p2_target_and_eligibility_boundary",
        }
        self.assertEqual(8, len(self.v3["required"]))
        self.assertEqual(required, set(self.v3["required"]))
        self.assertFalse(self.v3["additionalProperties"])

    def test_all_17_real_candidates_validate_and_recompute(self) -> None:
        identities = set()
        for candidate in self.candidates:
            with self.subTest(source=candidate["research_producer_identity"]):
                self.validator.validate(candidate)
                self.assertEqual(candidate["candidate_id"], candidate_id(candidate))
                identities.add(candidate["candidate_id"])
                self.assertEqual(
                    "FORMULAIC_ALPHA",
                    candidate["research_producer_identity"]["producer_kind"],
                )
                self.assertEqual("FINISHED", candidate["qlib_recorder_identity"]["status"])
                self.assertEqual(
                    "NOT_PERSISTED_BY_UPSTREAM",
                    candidate["artifact_identity_bundle"]["formulaic_alpha_artifact_identity"][
                        "serialized_model_artifact"
                    ]["status"],
                )
        self.assertEqual(17, len(identities))

    def test_formulaic_collections_are_deterministically_sorted(self) -> None:
        for candidate in self.candidates:
            research = candidate["research_producer_identity"][
                "formulaic_alpha_research_identity"
            ]
            self.assertEqual(sorted(research["origin_seeds"]), research["origin_seeds"])
            self.assertEqual(
                sorted(
                    research["origin_locations"],
                    key=lambda item: (item["origin_seed"], item["pool_index"]),
                ),
                research["origin_locations"],
            )
            artifacts = candidate["artifact_identity_bundle"][
                "formulaic_alpha_artifact_identity"
            ]["evaluation_artifact_identities"]
            self.assertEqual(
                sorted(artifacts, key=lambda item: (item["logical_role"], item["sha256"])),
                artifacts,
            )

    def test_performance_metrics_are_excluded(self) -> None:
        prohibited = {
            "ic",
            "rankic",
            "rank_ic",
            "sharpe",
            "return",
            "returns",
            "pnl",
            "test_performance",
            "runtime_seconds",
            "gpu_metrics",
            "cpu_metrics",
        }
        for candidate in self.candidates:
            self.assertFalse(nested_keys(candidate).intersection(prohibited))

    def test_rdagent_branch_reuses_immutable_v1_v2_definitions(self) -> None:
        definitions = self.v3["$defs"]
        self.assertEqual(
            "candidate-contract-v1.schema.json#/$defs/rdagentResearchIdentity",
            definitions["researchProducerIdentity"]["oneOf"][0]["properties"][
                "rdagent_research_identity"
            ]["$ref"],
        )
        self.assertEqual(
            "candidate-contract-v1.schema.json#/$defs/artifactIdentityBundle",
            definitions["rdAgentArtifactIdentityBundle"]["properties"][
                "rdagent_artifact_identity"
            ]["$ref"],
        )
        self.assertEqual(
            "candidate-contract-v2.schema.json#/$defs/runtimeIdentityBundleV2",
            definitions["rdAgentRuntimeIdentityBundle"]["properties"][
                "rdagent_runtime_identity"
            ]["$ref"],
        )

    def test_required_negative_cases_fail_closed(self) -> None:
        candidate = self.candidates[0]
        cases: dict[str, dict[str, object]] = {}

        modified = copy.deepcopy(candidate)
        modified["runtime_identity_bundle"]["formulaic_alpha_runtime_identity"][
            "rdagent_source_git_sha"
        ] = "0" * 40
        cases["formulaic_fake_rdagent_identity"] = modified

        modified = copy.deepcopy(candidate)
        modified["runtime_identity_bundle"]["formulaic_alpha_runtime_identity"][
            "llm_execution_identity"
        ] = {}
        cases["formulaic_llm_identity"] = modified

        modified = copy.deepcopy(candidate)
        del modified["research_producer_identity"]["formulaic_alpha_research_identity"][
            "engine_git_sha"
        ]
        cases["missing_alphagen_source_sha"] = modified

        modified = copy.deepcopy(candidate)
        del modified["research_producer_identity"]["formulaic_alpha_research_identity"][
            "expression"
        ]
        cases["missing_expression_identity"] = modified

        modified = copy.deepcopy(candidate)
        del modified["artifact_identity_bundle"]["formulaic_alpha_artifact_identity"][
            "seal_output_sha256"
        ]
        cases["missing_dvc_seal_identity"] = modified

        modified = copy.deepcopy(candidate)
        modified["qlib_recorder_identity"]["status"] = "RUNNING"
        cases["non_finished_recorder"] = modified

        modified = copy.deepcopy(candidate)
        del modified["artifact_identity_bundle"]["formulaic_alpha_artifact_identity"][
            "prediction_artifact_identity"
        ]
        cases["missing_prediction_identity"] = modified

        modified = copy.deepcopy(candidate)
        modified["artifact_identity_bundle"]["formulaic_alpha_artifact_identity"][
            "serialized_model_artifact"
        ]["identity"] = {"logical_role": "fake_model", "sha256": "0" * 64}
        cases["fake_model_hash_when_not_persisted"] = modified

        modified = copy.deepcopy(candidate)
        modified["p2_target_and_eligibility_boundary"][
            "historical_research_test_status"
        ] = "PRISTINE_OOS"
        cases["historical_test_marked_pristine"] = modified

        modified = copy.deepcopy(candidate)
        modified["p2_target_and_eligibility_boundary"]["sealed_oos_accessed_by_p3"] = True
        cases["sealed_oos_access_claim"] = modified

        modified = copy.deepcopy(candidate)
        modified["candidate_id"] = "sha256:" + "f" * 64
        cases["candidate_id_mismatch"] = modified

        modified = copy.deepcopy(candidate)
        modified["runtime_identity_bundle"] = {
            "producer_kind": "RD_AGENT",
            "rdagent_runtime_identity": {},
        }
        cases["producer_runtime_branch_mismatch"] = modified

        modified = copy.deepcopy(candidate)
        modified["artifact_identity_bundle"] = {
            "producer_kind": "RD_AGENT",
            "rdagent_artifact_identity": {},
        }
        cases["producer_artifact_branch_mismatch"] = modified

        self.assertEqual(13, len(cases))
        for name, value in cases.items():
            with self.subTest(case=name):
                self.assert_rejected(value)


if __name__ == "__main__":
    unittest.main()
