# P3 RD-Agent / LiteLLM Effective Context Headroom Resolution 001

## Scope

This task resolves only the local Ollama context-metadata mismatch that blocked
the first authorized P3 autonomous smoke. It does not execute `dvc repro`, an
RD-Agent research loop, Qlib training, prediction, backtest, or Candidate
materialization.

## Root cause and upstream state

Pinned RD-Agent `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd`
computes `chat_token_limit` as LiteLLM `max_input_tokens -
max_output_tokens`. LiteLLM 1.100.1 dynamically maps the Ollama model's one
`context_length` value to all three of `max_tokens`, `max_input_tokens`, and
`max_output_tokens`. For `aq-brain-local`, the observed values were therefore
`32768 / 32768 / 32768`, producing the invalid effective limit `0`.

The current official [RD-Agent backend](https://github.com/microsoft/RD-Agent/blob/main/rdagent/oai/backend/litellm.py)
still uses the subtraction algorithm, and the current official [LiteLLM Ollama
model-info implementation](https://github.com/BerriAI/litellm/blob/main/litellm/llms/ollama/common_utils.py)
still maps the same runtime context length to input and output. No released
upstream fix for this exact interaction was identified, and no package was
upgraded.

```text
ROOT_CAUSE = RDAGENT_LITELLM_OLLAMA_METADATA_SEMANTIC_MISMATCH
PINNED_RDAGENT_TOKEN_LIMIT_ALGORITHM = MAX_INPUT_MINUS_MAX_OUTPUT
PINNED_LITELLM_OLLAMA_METADATA = 32768_32768_32768
UPSTREAM_CURRENT_FIX_AVAILABLE = NO
```

## Thin upstream-first resolution

LiteLLM 1.100.1 public `register_model()` was proven in a disposable process
to override the alias metadata to input `32768` and output `4096`. The original
RD-Agent `LiteLLMAPIBackend` then returned the required `28672` effective input
budget.

`USLocalOllamaLiteLLMAPIBackend` is one thin subclass. It validates the exact
local logical slots, localhost Ollama endpoint, and approved budgets; registers
the metadata through LiteLLM's public API; and delegates to `super().__init__()`.
It does not override completion, embedding, retry, response parsing, streaming,
token counting, or routing.

The P3 DVC stage selects this class through RD-Agent's native `BACKEND` setting
and changes only its input budget from `32768` to `28672`. Output remains
`4096`; their sum is the verified Ollama context `32768`.

```text
RESOLUTION_MODE = LITELLM_PUBLIC_REGISTER_MODEL
BACKEND_CLASS = aq_rdagent_us_binding.llm_backend.USLocalOllamaLiteLLMAPIBackend
CONTEXT_WINDOW = 32768
EFFECTIVE_CHAT_INPUT_LIMIT = 28672
CHAT_MAX_OUTPUT_TOKENS = 4096
CONTEXT_HEADROOM_GATE = PASS
CUSTOM_COMPLETION_LOGIC = 0
CUSTOM_EMBEDDING_LOGIC = 0
CUSTOM_ROUTER_LOGIC = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Verification

The exact DVC process environment resolved `APIBackend()` to the thin class and
reported `28672`. One bounded local chat request returned `OK`; one local
embedding request returned 1,024 finite values. Both calls used inherited
RD-Agent/LiteLLM implementations and localhost Ollama only. Native Ollama stop
controls were used after the checks.

Focused adapter tests passed `7/7`, existing binding tests passed `12/12`, and
materializer tests passed `5/5`. Candidate V2 schema was not changed; only its
descriptive current-model example was made logical-slot-driven.

```text
LITELLM_REGISTER_MODEL_METADATA_PROOF = PASS
LOCAL_CHAT_HEALTH = PASS
LOCAL_EMBEDDING_HEALTH = PASS
BINDING_TESTS = 19/19_PASS
MATERIALIZER_TESTS = 5/5_PASS
CANDIDATE_V2_SCHEMA_CHANGED = NO
DVC_LOCK_CHANGED = NO
DVC_REPRO_EXECUTED = NO
AUTONOMOUS_ATTEMPT_COUNT = 0
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
RD_AGENT_SOURCE_CHANGED = NO
LITELLM_SITE_PACKAGES_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
```

## Current state

```text
P3_RDAGENT_LITELLM_EFFECTIVE_CONTEXT_HEADROOM_RESOLUTION = PASS
CURRENT_NEXT = P3_FIRST_AUTHORIZED_AUTONOMOUS_SMOKE_AND_CANDIDATE_V2_INSTANCE_001
```

## Runtime namespace regression check

After attempt-001 exposed the missing process-local Conda selection, the exact
future attempt-002 stage environment was reconstructed without inference. The
same accepted backend class still resolves input 28672 plus output 4096 to the
32768 context window. Runtime namespace selection moved to one DVC variable
and Qlib's native `QLIB_MLFLOW_URI`; no backend implementation changed.

```text
BACKEND_CLASS = aq_rdagent_us_binding.llm_backend.USLocalOllamaLiteLLMAPIBackend
EFFECTIVE_CHAT_INPUT_LIMIT = 28672
CHAT_MAX_OUTPUT_TOKENS = 4096
CONTEXT_WINDOW = 32768
CONTEXT_HEADROOM_GATE = PASS
BACKEND_IMPLEMENTATION_CHANGED = NO
LLM_INFERENCE_EXECUTED = NO
DVC_REPRO_EXECUTED = NO
CURRENT_NEXT = P3_FIRST_AUTHORIZED_AUTONOMOUS_SMOKE_AND_CANDIDATE_V2_INSTANCE_003
```
