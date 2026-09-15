"""Thin local Ollama metadata binding for the pinned RD-Agent LiteLLM backend."""

from __future__ import annotations

import os
from typing import Any

from litellm import get_model_info, register_model
from rdagent.oai.backend import LiteLLMAPIBackend
from rdagent.oai.backend.litellm import LITELLM_SETTINGS


_CHAT_MODEL = "ollama/aq-brain-local"
_EMBEDDING_MODEL = "ollama/aq-embedding-local"
_OLLAMA_API_BASE = "http://127.0.0.1:11434"
_CONTEXT_WINDOW = 32768
_SAFE_INPUT_BUDGET = 28672
_MAX_OUTPUT_TOKENS = 4096


def _required_positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RuntimeError(f"{name} must be a positive integer")
    return value


class USLocalOllamaLiteLLMAPIBackend(LiteLLMAPIBackend):
    """Register correct local-model metadata, then delegate entirely upstream."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if LITELLM_SETTINGS.chat_model != _CHAT_MODEL:
            raise RuntimeError("P3 chat backend must use the approved local Ollama logical slot")
        if LITELLM_SETTINGS.embedding_model != _EMBEDDING_MODEL:
            raise RuntimeError("P3 embedding backend must use the approved local Ollama logical slot")
        if os.environ.get("OLLAMA_API_BASE", "").rstrip("/") != _OLLAMA_API_BASE:
            raise RuntimeError("P3 Ollama endpoint must be the approved localhost endpoint")

        input_budget = _required_positive_int(
            "LITELLM_CHAT_TOKEN_LIMIT", LITELLM_SETTINGS.chat_token_limit
        )
        output_budget = _required_positive_int(
            "LITELLM_CHAT_MAX_TOKENS", LITELLM_SETTINGS.chat_max_tokens
        )
        if input_budget != _SAFE_INPUT_BUDGET or output_budget != _MAX_OUTPUT_TOKENS:
            raise RuntimeError("P3 local chat token budgets do not match the approved values")
        if input_budget + output_budget != _CONTEXT_WINDOW:
            raise RuntimeError("P3 local chat token budgets do not match the accepted context window")

        register_model(
            {
                _CHAT_MODEL: {
                    "litellm_provider": "ollama",
                    "mode": "chat",
                    "max_tokens": _CONTEXT_WINDOW,
                    "max_input_tokens": _CONTEXT_WINDOW,
                    "max_output_tokens": output_budget,
                    "input_cost_per_token": 0.0,
                    "output_cost_per_token": 0.0,
                }
            }
        )
        info = get_model_info(_CHAT_MODEL)
        if (
            info.get("litellm_provider") != "ollama"
            or info.get("mode") != "chat"
            or info.get("max_input_tokens") != _CONTEXT_WINDOW
            or info.get("max_output_tokens") != output_budget
        ):
            raise RuntimeError("LiteLLM rejected the approved local Ollama metadata")

        super().__init__(*args, **kwargs)
        if self.chat_token_limit != input_budget:
            raise RuntimeError("RD-Agent effective chat input limit does not match the approved budget")
