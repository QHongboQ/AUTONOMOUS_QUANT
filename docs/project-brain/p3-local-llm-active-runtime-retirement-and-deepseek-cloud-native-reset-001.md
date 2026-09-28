# P3 Local LLM Active-Runtime Retirement and DeepSeek Cloud-Native Reset 001

Task date: 2026-09-28

## Decision and scope

This task retires the local Ollama generative path from active P3 production
routing and moves the single generative route to the upstream-native chain:

```text
DeepSeek Flash
  -> LiteLLM 1.100.1
  -> RD-Agent
  -> Qlib
  -> future Candidate V4
```

This is not a Candidate admission, `fin_quant` run, scientific factor result,
or P2 certification event. Historical local-model reports remain unchanged.
PR #141 was closed as superseded; none of its draft work was merged.

## Active runtime contraction

The active DVC stage now binds:

```text
BACKEND = rdagent.oai.backend.LiteLLMAPIBackend
LITELLM_CHAT_MODEL = deepseek/deepseek-flash
LITELLM_CHAT_MAX_TOKENS = 65536
LITELLM_REASONING_EFFORT = high
CHAT_ROUTE_MODE = DEEPSEEK_ONLY
```

It no longer binds an Ollama chat base URL, local chat alias/digest, 28,672
input budget, 4,096 output budget, or local temperature override. DeepSeek
credentials are supplied only through the process environment and no secret,
secret hash, secret path, or key fragment is tracked.

The project-owned `USLocalOllamaLiteLLMAPIBackend` had no non-local
responsibility. Its 76 production LOC and 126 dedicated test LOC were deleted
without replacement. Upstream RD-Agent and LiteLLM own the cloud connection,
retry, parsing, reasoning, and provider mapping.

```text
LOCAL_LLM_ACTIVE_PRODUCTION_LOC_BEFORE = 76
LOCAL_LLM_ACTIVE_PRODUCTION_LOC_AFTER = 0
LOCAL_ONLY_TEST_LOC_BEFORE = 126
LOCAL_ONLY_TEST_LOC_AFTER = 0
NEW_CLOUD_PROVIDER_PRODUCTION_LOC = 0
AQ_CUSTOM_LLM_BACKEND_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

Active local-chat references were removed. Remaining local-chat strings are
either immutable Candidate V2/V3 or historical configuration/evidence, plus a
V4 negative-validation test proving that the retired route is rejected.

## Cloud-native preflight

The official model list returned `deepseek-flash`. LiteLLM mapped
`reasoning_effort=high` to `thinking={"type":"enabled"}` and RD-Agent's native
backend executed and parsed a JSON response with the 65,536-token ceiling.

```text
DEEPSEEK_AUTH = PASS
DEEPSEEK_MODEL_DISCOVERY = PASS
LITELLM_CHAT_COMPLETION = PASS
DEEPSEEK_REASONING_HIGH = PASS
DEEPSEEK_JSON_OUTPUT = PASS
RDAGENT_NATIVE_PARSE = PASS
EFFECTIVE_MODEL = deepseek/deepseek-flash
EFFECTIVE_PROVIDER_MODEL = deepseek-flash
EFFECTIVE_REASONING_EFFORT = high
EFFECTIVE_THINKING = enabled
EFFECTIVE_MAX_TOKENS = 65536
```

The earlier screen that inherited `LITELLM_CHAT_MAX_TOKENS=4096` stopped before
the next recovery loop and is classified only as:

```text
DEEPSEEK_4096_SCREEN = INVALID_LEGACY_LOCAL_RUNTIME_CONFIGURATION_DIAGNOSTIC
MODEL_FAIL = NO_FOR_4096_DIAGNOSTIC
SCIENTIFIC_FACTOR_FAIL = NO_FOR_4096_DIAGNOSTIC
```

## First valid admission screen

One fresh alpha053 screen used the frozen fixture, official RD-Agent
`FactorCoSTEER`, `FactorImplementEval`, prompt, evaluator, feedback path, and
10-loop ceiling. It used the DeepSeek-native configuration above. The generated
implementation executed and passed the single-column, row-count, and index
checks, but it grouped the delta by instrument while the frozen ground truth
did not. The resulting value checks failed:

```text
VALID_ALPHA053_SCREEN = FAIL_FACTOR_CORRECTNESS
FACTOR_COSTEER_RECOVERY_LOOPS_USED = 1
NATIVE_LLM_CALL_COUNT = 4
SINGLE_COLUMN = TRUE
ROW_COUNT_RATIO = 1.0
INDEX_RATIO = 1.0
EQUAL_VALUE_RATIO = 0.0
CORRELATION = 0.40474220115578846
RANK_CORRELATION = 0.423337
ROUND_1 = NOT_RUN_SCREEN_FAIL
ROUND_2 = NOT_RUN_SCREEN_FAIL
FINAL_ADMISSION_PASS_COUNT = 0/6
DEEPSEEK_GENERATIVE_RUNTIME = NOT_ADMITTED
FAILURE_CLASS = MODEL_CAPABILITY_FACTOR_CORRECTNESS
INFRASTRUCTURE_FAILURE = NO
```

This valid screen failure is not confused with the prior 4,096-token
diagnostic. It terminates admission exactly at the frozen screen gate. No
alternate prompt, evaluator, fixture, factor source, fallback model, or retry
system was introduced.

## Local capability inventory

After the cloud smoke passed, the chat-only `aq-brain-local:latest` and
`qwen2.5-coder:7b` tags (shared digest prefix `dae161e27b0e`) were removed from
the existing WSL Ollama store. The separately owned embedding model remains:

```text
OLLAMA_RUNTIME = /home/zhou/.local/ollama-v0.34.0/bin/ollama
LOCAL_GENERATIVE_LLM_ACTIVE = NO
LOCAL_CHAT_MODEL_COUNT_AFTER = 0
LOCAL_EMBEDDING_ACTIVE = YES
EMBEDDING_ALIAS = aq-embedding-local:latest
EMBEDDING_MODEL = qwen3-embedding:0.6b
EMBEDDING_DIGEST = ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d
LOADED_OLLAMA_MODEL_COUNT_AFTER = 0
```

## Candidate V4 boundary

`P3_CANDIDATE_TO_P2_CONTRACT_V4` is a forward-only design. It preserves the
eight top-level fields, reuses the immutable V3 Formulaic Alpha branch, and
changes only the future RD-Agent runtime identity so it can truthfully bind
DeepSeek provider/model resolution, high reasoning, native trace identity,
call count, and the 65,536-token ceiling. Candidate V1/V2/V3 are unchanged.
No V4 Candidate was materialized because admission did not pass.

```text
CANDIDATE_V4_SCHEMA_SHA256 = fbb9d22a3d18aa0f559d156efbae48eb237a09e79e4e0a8fe28897198a2aacbc
DEEPSEEK_CONFIGURATION_SHA256 = bfc352734eb75183a6de0f47228918806fce5e6ee0298ea08102959b3b276f8c
CANDIDATE_TOP_LEVEL_FIELD_COUNT = 8
RFC8785 = 0.1.4_UPSTREAM
CANDIDATE_V4_INSTANCE_CREATED = NO
```

## Validation and safety

```text
RD_AGENT_BINDING_TESTS = 20/20_PASS
CANDIDATE_V4_TESTS = 9/9_PASS
CHANGED_PYTHON_RUFF = PASS
COMPILEALL = PASS
DIFF_CHECK = PASS
FIN_QUANT_EXECUTED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P1_MODIFIED = NO
P2_MODIFIED = NO
P4_MODIFIED = NO
P7_MODIFIED = NO
```

Private runtime evidence is retained under:

```text
D:\AQ_DATA\P3\local-llm-active-runtime-retirement-and-deepseek-cloud-native-reset-001
```

## Current authority

```text
PRIMARY_GENERATIVE_AI_PROVIDER = DEEPSEEK
PRIMARY_GENERATIVE_AI_MODEL = deepseek-flash
MODEL_VERSION_FAMILY = DeepSeek-V4.1-Flash
PRODUCTION_CHAT_ROUTE = DEEPSEEK_ONLY_NOT_ADMITTED_FOR_AUTONOMOUS_FACTOR_RUNS
CURRENT_DEVELOPMENT_NEXT = BLOCKED_DEEPSEEK_FLASH_ALPHA053_SCREEN_CORRECTNESS
FIN_QUANT_NEXT_TASK_AUTHORIZED = NO
FINAL_CLASSIFICATION = PASS_ARCHITECTURE_RESET_DEEPSEEK_ADMISSION_BLOCKED_MODEL_CAPABILITY
```
