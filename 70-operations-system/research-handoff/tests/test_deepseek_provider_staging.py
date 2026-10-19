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
        self.assertIn("networks: [core, worker_proxy, provider_egress]", compose)
        self.assertNotIn("ports:", compose)
        self.assertIn("deepseek_api_key", compose)
        self.assertIn("P12_OLLAMA_API_BASE:?", compose)
        worker = compose.split("  rdagent-owner-oneshot-worker:", 1)[1].split("secrets:", 1)[0]
        self.assertIn("profiles: [p12-owner-oneshot]", worker)
        self.assertIn("networks: [worker_proxy]", worker)
        self.assertNotIn("provider_egress", worker)
        self.assertIn('command: ["fin_quant", "--loop-n", "1"]', worker)
        self.assertIn('LITELLM_CHAT_MAX_TOKENS: "8192"', worker)
        config = (ROOT / "docker-rdagent-smoke" / "config.deepseek-staging.yaml").read_text()
        self.assertIn('db: "1"', config)
        self.assertNotIn("redis_db:", config)

    def test_staging_profile_sets_native_key_issuance_bounds_without_global_budget(self) -> None:
        config = (ROOT / "docker-rdagent-smoke" / "config.deepseek-staging.yaml").read_text()
        self.assertNotRegex(config, r"(?m)^  max_budget:")
        self.assertIn("default_key_generate_params:", config)
        self.assertIn("upperbound_key_generate_params:", config)
        settings = config.split("litellm_settings:", 1)[1].split("router_settings:", 1)[0]
        defaults = settings.split("default_key_generate_params:", 1)[1].split(
            "upperbound_key_generate_params:", 1
        )[0]
        upperbounds = settings.split("upperbound_key_generate_params:", 1)[1]
        self.assertIn("    max_budget: 5.0", defaults)
        self.assertIn("    budget_duration: null", defaults)
        self.assertIn("    duration: 24h", defaults)
        self.assertIn("    max_parallel_requests: 1", defaults)
        self.assertIn("      - deepseek/deepseek-flash", defaults)
        self.assertIn("      - ollama/qwen3-embedding:0.6b", defaults)
        self.assertIn("    max_budget: 5.0", upperbounds)
        self.assertIn("    duration: 24h", upperbounds)
        self.assertIn("    max_parallel_requests: 1", upperbounds)
        self.assertNotIn("budget_duration:", upperbounds)
        self.assertIn("fail_closed_budget_enforcement: true", config)
        self.assertIn("fail_closed_rate_limit_enforcement: true", config)
        router_settings = config.split("router_settings:", 1)[1]
        self.assertIn("default_max_parallel_requests: 1", router_settings)
        self.assertNotIn("default_max_parallel_requests:", config.split("router_settings:", 1)[0])
        self.assertIn("block_requests_for_models_without_pricing: true", config)
        self.assertEqual(config.count("model_name:"), 2)
        self.assertIn("model_name: deepseek/deepseek-flash", config)
        self.assertIn("model_name: ollama/qwen3-embedding:0.6b", config)
        self.assertNotIn("fallbacks:", config)

    def test_experiment_aggregate_requires_native_persistent_user_budget(self) -> None:
        readme = (ROOT / "README.md").read_text()
        self.assertIn("native persistent LiteLLM", readme)
        self.assertIn("same `user_id`", readme)
        self.assertIn("Per-key caps alone do not enforce this aggregate", readme)
        self.assertIn("No owner approval file, native user, paid key", readme)

    def test_pinned_source_contains_native_user_and_key_budget_controls(self) -> None:
        # Pin the upstream interface contract checked in the v1.105.1 runtime.
        compose = (ROOT / "docker-rdagent-smoke" / "compose.deepseek-staging.yaml").read_text()
        self.assertIn("ghcr.io/berriai/litellm@sha256:b7b9e2c306343721802253d0dd9436b9634a2eb4e14da7c7cf06c5c7b7530802", compose)
        # User/key creation belongs to a future approved control workflow, not startup.
        self.assertNotIn("/user/new", compose)
        self.assertNotIn("/key/generate", compose)

    def test_real_worker_is_owner_one_shot_only_and_startup_does_not_issue_a_key(self) -> None:
        config = (ROOT / "docker-rdagent-smoke" / "config.deepseek-staging.yaml").read_text()
        compose = (ROOT / "docker-rdagent-smoke" / "compose.deepseek-staging.yaml").read_text()
        self.assertIn("profiles: [deepseek-staging]", compose)
        worker = compose.split("  rdagent-owner-oneshot-worker:", 1)[1].split("secrets:", 1)[0]
        self.assertIn("profiles: [p12-owner-oneshot]", worker)
        self.assertIn("P12_OWNER_SCOPED_PROXY_KEY:?", compose)
        self.assertIn("owner_oneshot_proxy_control.py", compose)
        self.assertNotIn("/key/generate", config)
        control = (ROOT / "docker-rdagent-smoke" / "owner_oneshot_proxy_control.py").read_text()
        self.assertIn('"prepare"', control)
        self.assertIn('"block"', control)
        entrypoint = (ROOT / "owner_oneshot_research.py").read_text()
        self.assertIn("sys.stdin.isatty()", entrypoint)
        self.assertIn("RUN $5 ONCE", entrypoint)
        self.assertIn("sk-preflight-placeholder-only", entrypoint)
        handoff = (ROOT / "p12_research_handoff.py").read_text()
        self.assertIn('"BLOCKED_REAL_DISPATCH_DENIED"', handoff)


if __name__ == "__main__":
    unittest.main()
