from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unittest


TEST_FILE = Path(__file__).resolve()
BINDING_ROOT = TEST_FILE.parents[1]
RDAGENT_ROOT = TEST_FILE.parents[2]
sys.path.insert(0, str(BINDING_ROOT))

os.environ.setdefault("OLLAMA_API_BASE", "http://127.0.0.1:11434")
os.environ.setdefault("LITELLM_CHAT_MODEL", "ollama_chat/aq-brain-local")
os.environ.setdefault("LITELLM_EMBEDDING_MODEL", "ollama/aq-embedding-local")
os.environ.setdefault("LITELLM_CHAT_TOKEN_LIMIT", "28672")
os.environ.setdefault("LITELLM_CHAT_MAX_TOKENS", "4096")

from rdagent.oai.backend import LiteLLMAPIBackend
from rdagent.oai.backend.litellm import LITELLM_SETTINGS
from litellm import get_supported_openai_params, supports_response_schema

from aq_rdagent_us_binding.llm_backend import USLocalOllamaLiteLLMAPIBackend


class LocalOllamaBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = (
            LITELLM_SETTINGS.chat_model,
            LITELLM_SETTINGS.embedding_model,
            LITELLM_SETTINGS.chat_token_limit,
            LITELLM_SETTINGS.chat_max_tokens,
            os.environ.get("OLLAMA_API_BASE"),
        )
        LITELLM_SETTINGS.chat_model = "ollama_chat/aq-brain-local"
        LITELLM_SETTINGS.embedding_model = "ollama/aq-embedding-local"
        LITELLM_SETTINGS.chat_token_limit = 28672
        LITELLM_SETTINGS.chat_max_tokens = 4096
        os.environ["OLLAMA_API_BASE"] = "http://127.0.0.1:11434"

    def tearDown(self) -> None:
        (
            LITELLM_SETTINGS.chat_model,
            LITELLM_SETTINGS.embedding_model,
            LITELLM_SETTINGS.chat_token_limit,
            LITELLM_SETTINGS.chat_max_tokens,
            api_base,
        ) = self.original
        if api_base is None:
            os.environ.pop("OLLAMA_API_BASE", None)
        else:
            os.environ["OLLAMA_API_BASE"] = api_base

    def test_public_metadata_registration_produces_safe_effective_limit(self) -> None:
        backend = USLocalOllamaLiteLLMAPIBackend()
        self.assertEqual(backend.chat_token_limit, 28672)

    def test_nonpositive_input_budget_fails_closed(self) -> None:
        for value in (0, -1):
            with self.subTest(value=value):
                LITELLM_SETTINGS.chat_token_limit = value
                with self.assertRaisesRegex(RuntimeError, "positive integer"):
                    USLocalOllamaLiteLLMAPIBackend()

    def test_missing_output_budget_fails_closed(self) -> None:
        LITELLM_SETTINGS.chat_max_tokens = None
        with self.assertRaisesRegex(RuntimeError, "positive integer"):
            USLocalOllamaLiteLLMAPIBackend()

    def test_context_budget_mismatch_or_overflow_fails_closed(self) -> None:
        for value in (28000, 28673):
            with self.subTest(value=value):
                LITELLM_SETTINGS.chat_token_limit = value
                with self.assertRaisesRegex(RuntimeError, "approved values"):
                    USLocalOllamaLiteLLMAPIBackend()

    def test_completion_and_embedding_implementations_are_inherited(self) -> None:
        self.assertIs(
            USLocalOllamaLiteLLMAPIBackend._create_chat_completion_inner_function,
            LiteLLMAPIBackend._create_chat_completion_inner_function,
        )
        self.assertIs(
            USLocalOllamaLiteLLMAPIBackend._create_embedding_inner_function,
            LiteLLMAPIBackend._create_embedding_inner_function,
        )

    def test_official_ollama_chat_route_exposes_structured_output(self) -> None:
        USLocalOllamaLiteLLMAPIBackend()
        self.assertIn(
            "response_format",
            get_supported_openai_params(model="ollama_chat/aq-brain-local"),
        )
        self.assertTrue(supports_response_schema(model="ollama_chat/aq-brain-local"))

    def test_nonlocal_or_cloud_routes_fail_closed(self) -> None:
        LITELLM_SETTINGS.chat_model = "openai/gpt-4o"
        with self.assertRaisesRegex(RuntimeError, "local Ollama"):
            USLocalOllamaLiteLLMAPIBackend()
        LITELLM_SETTINGS.chat_model = "ollama_chat/aq-brain-local"
        os.environ["OLLAMA_API_BASE"] = "https://example.invalid"
        with self.assertRaisesRegex(RuntimeError, "localhost"):
            USLocalOllamaLiteLLMAPIBackend()

    def test_selected_logical_slot_identities_remain_authoritative(self) -> None:
        config = json.loads(
            (RDAGENT_ROOT / "config" / "p3-local-logical-llm-slots-v1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(config["route_mode"], "LOCAL_ONLY")
        self.assertEqual(config["ollama_runtime"]["context_length"], 32768)
        self.assertEqual(config["ollama_runtime"]["num_parallel"], 1)
        self.assertEqual(config["chat"]["litellm_model"], "ollama_chat/aq-brain-local")
        self.assertEqual(config["chat"]["provider"], "ollama_chat")
        self.assertEqual(config["chat"]["resolved_model"], "qwen2.5-coder:7b")
        self.assertEqual(
            config["chat"]["resolved_digest"],
            "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364",
        )
        self.assertEqual(config["embedding"]["litellm_model"], "ollama/aq-embedding-local")


if __name__ == "__main__":
    unittest.main()
