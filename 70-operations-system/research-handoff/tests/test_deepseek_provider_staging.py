from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = ROOT.parents[1] / "30-research-system" / "candidate-handoff" / "p3-to-p2"


class DeepSeekProviderStagingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.v4 = json.loads((CONTRACT_ROOT / "candidate-contract-v4.schema.json").read_text())
        cls.v5 = json.loads((CONTRACT_ROOT / "candidate-contract-v5.schema.json").read_text())

    @staticmethod
    def chat_identity(schema: dict[str, object]) -> tuple[str, str, str]:
        chat = schema["$defs"]["chatExecution"]["properties"]
        runtime = schema["$defs"]["llmExecutionIdentity"]["properties"]["litellm_version"]
        return chat["requested_model"]["const"], chat["resolved_model"]["const"], runtime["const"]

    def test_v5_accepts_flash_with_current_pinned_runtime(self) -> None:
        self.assertEqual(
            ("deepseek/deepseek-flash", "deepseek/deepseek-flash", "1.103.1"),
            self.chat_identity(self.v5),
        )

    def test_v5_rejects_historical_chat_identity(self) -> None:
        self.assertNotIn("deepseek/deepseek-chat", self.chat_identity(self.v5))

    def test_v4_remains_historical_and_does_not_accept_flash(self) -> None:
        self.assertEqual(
            ("deepseek/deepseek-chat", "deepseek/deepseek-chat", "1.103.1"),
            self.chat_identity(self.v4),
        )
        self.assertNotIn("deepseek/deepseek-flash", self.chat_identity(self.v4))

    def test_test_only_proxy_configuration_is_not_retargeted(self) -> None:
        mock_config = (ROOT / "docker-rdagent-smoke" / "config.yaml").read_text()
        self.assertIn("model_name: deepseek-chat", mock_config)
        self.assertIn("model: openai/mock-chat", mock_config)
        self.assertNotIn("deepseek/deepseek-flash", mock_config)

    def test_real_route_has_no_worker_attachment_or_published_port(self) -> None:
        compose = (ROOT / "docker-rdagent-smoke" / "compose.deepseek-staging.yaml").read_text()
        self.assertIn("profiles: [deepseek-staging]", compose)
        self.assertIn("pull_policy: never", compose)
        self.assertIn("networks: [core, provider_egress]", compose)
        self.assertNotIn("worker_proxy", compose)
        self.assertNotIn("ports:", compose)
        self.assertIn("deepseek_api_key", compose)
        self.assertIn("P12_OLLAMA_API_BASE:?", compose)
        config = (ROOT / "docker-rdagent-smoke" / "config.deepseek-staging.yaml").read_text()
        self.assertIn('db: "1"', config)
        self.assertNotIn("redis_db:", config)

    def test_disabled_real_profile_has_native_lifetime_ceiling_and_no_reset(self) -> None:
        config = (ROOT / "docker-rdagent-smoke" / "config.deepseek-staging.yaml").read_text()
        self.assertIn("max_budget: 5.0", config)
        self.assertIn("fail_closed_budget_enforcement: true", config)
        self.assertIn("fail_closed_rate_limit_enforcement: true", config)
        self.assertIn("default_max_parallel_requests: 1", config)
        # A duration-based budget would renew; only key/approval expiry is 24h.
        self.assertFalse(
            any(line.lstrip().startswith("budget_duration:") for line in config.splitlines())
        )
        self.assertIn("block_requests_for_models_without_pricing: true", config)
        self.assertEqual(config.count("model_name:"), 2)
        self.assertIn("model_name: deepseek/deepseek-flash", config)
        self.assertIn("model_name: ollama/qwen3-embedding:0.6b", config)
        self.assertNotIn("fallbacks:", config)

    def test_native_budget_does_not_enable_real_dispatch_or_create_a_key(self) -> None:
        config = (ROOT / "docker-rdagent-smoke" / "config.deepseek-staging.yaml").read_text()
        compose = (ROOT / "docker-rdagent-smoke" / "compose.deepseek-staging.yaml").read_text()
        self.assertIn("profiles: [deepseek-staging]", compose)
        self.assertNotIn("rdagent-finquant-worker", compose)
        self.assertNotIn("/key/generate", config)
        handoff = (ROOT / "p12_research_handoff.py").read_text()
        self.assertIn('"BLOCKED_REAL_DISPATCH_DENIED"', handoff)


if __name__ == "__main__":
    unittest.main()
