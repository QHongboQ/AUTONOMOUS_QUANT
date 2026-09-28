from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

import rfc8785
from jsonschema import Draft202012Validator
from referencing import Registry, Resource


CONTRACT_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
BASE = "https://qhongboq.github.io/AUTONOMOUS_QUANT/"


def load(name: str) -> dict[str, object]:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class CandidateContractV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {
            name: load(name)
            for name in (
                "candidate-contract-v1.schema.json",
                "candidate-contract-v2.schema.json",
                "candidate-contract-v3.schema.json",
                "candidate-contract-v4.schema.json",
            )
        }
        registry = Registry().with_resources(
            (BASE + name, Resource.from_contents(schema))
            for name, schema in cls.schemas.items()
        )
        cls.v4 = cls.schemas["candidate-contract-v4.schema.json"]
        Draft202012Validator.check_schema(cls.v4)
        cls.validator = Draft202012Validator(cls.v4, registry=registry)
        cls.llm_validator = cls.validator.evolve(
            schema={"$ref": "#/$defs/llmExecutionIdentityV4"}
        )

    def llm_identity(self) -> dict[str, object]:
        return {
            "litellm_version": "1.100.1",
            "llm_configuration_sha256": digest("configuration"),
            "native_trace_artifact_sha256": digest("trace"),
            "chat_route_mode": "DEEPSEEK_ONLY",
            "chat_resolution": {
                "provider": "deepseek",
                "requested_model": "deepseek/deepseek-flash",
                "resolved_model": "deepseek-flash",
                "provider_model_identity_kind": "RESPONSE_MODEL_ONLY",
                "provider_model_identity": "deepseek-flash",
                "reasoning_mode": "THINKING_ENABLED",
                "reasoning_effort": "high",
                "max_output_tokens": 65536,
                "call_count": 3,
            },
            "fallback_occurred": False,
            "fallback_reason_counts": [],
            "embedding_logical_slot": "aq-embedding-local",
            "embedding_resolution": {
                "provider": "ollama",
                "requested_model": "ollama/aq-embedding-local",
                "resolved_model": "qwen3-embedding:0.6b",
                "provider_model_identity_kind": "LOCAL_DIGEST",
                "provider_model_identity": (
                    "ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d"
                ),
                "dimensions": 1024,
            },
            "embedding_epoch_sha256": (
                "e63389904f57782a645d2f9d79ec5f028b8a7ef99aa051a2cdb0ca2e55dbf6db"
            ),
        }

    def assert_llm_rejected(self, value: dict[str, object]) -> None:
        self.assertFalse(self.llm_validator.is_valid(value))

    def test_exact_eight_field_architecture_is_preserved(self) -> None:
        self.assertEqual(8, len(self.v4["required"]))
        self.assertFalse(self.v4["additionalProperties"])
        self.assertEqual(
            "P3_CANDIDATE_TO_P2_CONTRACT_V4",
            self.v4["properties"]["candidate_contract_version"]["const"],
        )

    def test_formulaic_branch_reuses_v3_authority(self) -> None:
        runtime_refs = self.v4["$defs"]["runtimeIdentityBundle"]["oneOf"]
        self.assertEqual(
            "candidate-contract-v3.schema.json#/$defs/formulaicRuntimeIdentityBundle",
            runtime_refs[1]["$ref"],
        )
        self.assertEqual(
            "candidate-contract-v3.schema.json#/$defs/p2TargetAndEligibilityBoundary",
            self.v4["properties"]["p2_target_and_eligibility_boundary"]["$ref"],
        )

    def test_deepseek_cloud_identity_passes(self) -> None:
        self.llm_validator.validate(self.llm_identity())

    def test_local_chat_or_legacy_budget_is_rejected(self) -> None:
        for field, value in (
            ("provider", "ollama"),
            ("requested_model", "ollama_chat/aq-brain-local"),
            ("max_output_tokens", 4096),
            ("reasoning_effort", "low"),
        ):
            modified = copy.deepcopy(self.llm_identity())
            modified["chat_resolution"][field] = value
            with self.subTest(field=field):
                self.assert_llm_rejected(modified)

    def test_automatic_fallback_is_rejected(self) -> None:
        modified = self.llm_identity()
        modified["fallback_occurred"] = True
        modified["fallback_reason_counts"] = [
            {"reason_class": "MODEL_UNAVAILABLE", "count": 1}
        ]
        self.assert_llm_rejected(modified)

    def test_secret_and_performance_fields_are_rejected(self) -> None:
        for field in ("api_key", "secret_path", "rank_ic"):
            modified = self.llm_identity()
            modified[field] = "forbidden"
            with self.subTest(field=field):
                self.assert_llm_rejected(modified)

    def test_call_count_and_response_model_are_required(self) -> None:
        for field in ("call_count", "resolved_model", "provider_model_identity"):
            modified = self.llm_identity()
            del modified["chat_resolution"][field]
            with self.subTest(field=field):
                self.assert_llm_rejected(modified)

    def test_rfc8785_candidate_identity_is_order_independent(self) -> None:
        projection = {
            "candidate_contract_version": "P3_CANDIDATE_TO_P2_CONTRACT_V4",
            "research_producer_identity": {"producer_kind": "RD_AGENT"},
            "qlib_recorder_identity": {"status": "FINISHED"},
            "artifact_identity_bundle": {"producer_kind": "RD_AGENT"},
            "dataset_identity_bundle": {"authority": "PIT"},
            "runtime_identity_bundle": {"producer_kind": "RD_AGENT"},
            "p2_target_and_eligibility_boundary": {"eligible": False},
        }
        reversed_projection = dict(reversed(list(projection.items())))
        self.assertEqual(rfc8785.dumps(projection), rfc8785.dumps(reversed_projection))
        self.assertEqual(
            hashlib.sha256(rfc8785.dumps(projection)).hexdigest(),
            hashlib.sha256(rfc8785.dumps(reversed_projection)).hexdigest(),
        )

    def test_active_dvc_route_is_upstream_deepseek_only(self) -> None:
        dvc_text = (REPOSITORY_ROOT / "dvc.yaml").read_text(encoding="utf-8")
        command = dvc_text.split("  p3_rdagent_us_quant_research:\n", 1)[1].split(
            "\n  p3_formulaic_alpha_reproducibility_seal:", 1
        )[0]
        self.assertIn("BACKEND=rdagent.oai.backend.LiteLLMAPIBackend", command)
        self.assertIn("LITELLM_CHAT_MODEL=deepseek/deepseek-flash", command)
        self.assertIn("LITELLM_CHAT_MAX_TOKENS=65536", command)
        self.assertIn("LITELLM_REASONING_EFFORT=high", command)
        self.assertNotIn("OLLAMA_API_BASE", command)
        self.assertNotIn("LITELLM_CHAT_TOKEN_LIMIT", command)
        self.assertNotIn("LITELLM_CHAT_TEMPERATURE", command)
        self.assertNotIn("ollama_chat/aq-brain-local", command)
        self.assertIn(
            "30-research-system/rd-agent/config/p3-deepseek-cloud-chat-local-embedding-v1.json",
            command,
        )
        self.assertNotIn("p3-local-logical-llm-slots-v1.json", command)


if __name__ == "__main__":
    unittest.main()
