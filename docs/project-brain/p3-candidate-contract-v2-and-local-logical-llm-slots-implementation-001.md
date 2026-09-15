# P3 Candidate Contract V2 and Local Logical LLM Slots Implementation 001

Implementation date: 2026-09-15

## Scope and baseline

This task materialized the minimum local-only LLM identity boundary required
before a first authorized P3 run. It did not execute RD-Agent research, DVC
reproduction, Qlib training, prediction, backtesting, cloud inference, or a
model download.

```text
BASE_HEAD = bf3298cc59b248433fb38ee713c7c68184461fa9
RDAGENT_VERSION = 0.8.1.dev37
LITELLM_VERSION = 1.100.1
OLLAMA_VERSION = 0.34.0
DEFAULT_CHAT_POLICY = LOCAL_ONLY
```

## Candidate Contract V2

Two new non-executable contract files were added:

```text
30-research-system/candidate-handoff/p3-to-p2/candidate-contract-v2.schema.json
30-research-system/candidate-handoff/p3-to-p2/candidate-contract-v2.md
```

V2 preserves the exact eight-field V1 top-level architecture and reuses the
immutable V1 bundle definitions. Only `runtime_identity_bundle` is extended,
with required `llm_execution_identity`. V1 bytes remain unchanged.

```text
CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V2
CANDIDATE_TOP_LEVEL_FIELD_COUNT = 8
CANDIDATE_ID_INPUT_FIELD_COUNT = 7
LLM_EXECUTION_IDENTITY_REQUIRED = YES
V1_SCHEMA_SHA256 = a30630d41596d5d89da1b4291b07489585e0ca23fbc78ddd822404eb0e3cb795
V1_SPEC_SHA256 = 0085963ad80b3e8ca526e8749be1eda6a157e7e15908462c8af5633277b8a364
V2_SCHEMA_SHA256 = a7f1c175c68188e641eacc61da2ba2683a9b1b6d6021cf1faa25f5543818266b
V2_SPEC_SHA256 = d052a429269995e12c572863c307f6a8eb9adcf70f97a460e1ea16274dc44c1c
```

Required identity now includes LiteLLM version; LLM configuration and native
trace hashes; logical chat slot and route mode; per-provider requested and
resolved model identity plus call counts; fallback evidence; embedding slot,
provider, model, digest and dimensions; and the embedding epoch identity.

## Validation

The installed `jsonschema 4.26.0` validated both Draft 2020-12 schemas. One
in-memory LOCAL_ONLY structural witness passed. The witness Candidate ID used
the unchanged seven-field canonical projection and was never persisted.

Fail-closed mutations produced:

```text
missing llm_execution_identity = REJECTED
missing local provider model identity/digest = REJECTED
missing embedding epoch = REJECTED
cloud placeholders required for LOCAL_ONLY = NO
LOCAL_ONLY_WITNESS = PASS
NEGATIVE_VALIDATION_CASES = 3/3 PASS
REAL_CANDIDATE_INSTANCE_CREATED = NO
FAKE_CANDIDATE_INSTANCE_CREATED = NO
```

## Local logical slots

Ollama's native `cp` command created aliases without downloading model bytes:

```text
aq-brain-local:latest
  -> qwen3:4b
  -> 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7

aq-embedding-local:latest
  -> qwen3-embedding:0.6b
  -> ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d
```

The non-secret configuration authority is:

```text
30-research-system/rd-agent/config/p3-local-logical-llm-slots-v1.json
CONFIGURATION_SHA256 = 786d489c34832a60b2035c7024fbd7e3c3b3eb23099c6bc58b80e1c96af5eaa7
```

The pinned RD-Agent settings resolver accepted the DVC process-local values:

```text
LITELLM_CHAT_MODEL = ollama/aq-brain-local
LITELLM_EMBEDDING_MODEL = ollama/aq-embedding-local
OLLAMA_API_BASE = http://127.0.0.1:11434
LITELLM_MAX_RETRY = 1
```

No AQ model router, provider registry, model loader, or alias engine exists.
Replacing a local model means updating the native Ollama alias and the frozen
resolved identity/configuration; it does not modify RD-Agent or Qlib source.

## Embedding epoch

The epoch is SHA-256 over the RFC 8785-compatible canonical JSON encoding of
the exact `epoch_identity_projection` in the configuration file:

```text
EMBEDDING_EPOCH_IDENTITY = e63389904f57782a645d2f9d79ec5f028b8a7ef99aa051a2cdb0ca2e55dbf6db
EMBEDDING_AUTO_CROSS_MODEL_FALLBACK = NO
EMBEDDING_EPOCH_REQUIRED_FOR_MODEL_SWITCH = YES
```

Changing the embedding provider, requested model, resolved model, digest,
dimensions, preprocessing, corpus, cache or index requires a new epoch and a
new empty upstream cache/index followed by full reindexing.

## DVC and native trace boundary

Only the P3 stage was changed. Its command now binds the local logical aliases
and the already-proven local LiteLLM settings. The non-secret slot
configuration is a DVC dependency. Existing `LOG_TRACE_PATH` remains under the
DVC run root, where RD-Agent's native settings, model-use and token/cost trace
objects can be content-hashed by a future real Candidate.

```text
DVC_VERSION = 3.67.1
P3_DVC_STAGE = ACTIVATED_DEFINITION_ONLY
P3_DVC_LOCK_ENTRY = PENDING_FIRST_AUTHORIZED_AUTONOMOUS_RUN
DVC_YAML_CHANGED = YES_P3_STAGE_ONLY
DVC_LOCK_CHANGED = NO
DVC_REPRO_EXECUTED = NO
DVC_STAGE_LIST = PASS
DVC_DAG = PASS
```

`dvc status` truthfully remains changed for the not-yet-executed P3 stage and
also reports pre-existing historical stage drift. No lock entry was fabricated
and no output was generated.

## Resource lifecycle

```text
MODEL_RESIDENCY_POLICY = ON_DEMAND
PERMANENT_LLM_GPU_RESIDENCY_REQUIRED = NO
MODEL_RESIDENCY_OWNER = OLLAMA
UPSTREAM_RESIDENCY_CONTROL = OLLAMA_KEEP_ALIVE
AQ_GPU_SCHEDULER = NONE
AQ_PROCESS_SUPERVISOR = NONE
```

The local Ollama service must use its native keep-alive lifecycle so chat and
embedding models can be released after use and need not remain resident during
Qlib training. This task records that operating policy; it does not add a
service manager or permanently mutate a shell profile.

## Reserved cloud interfaces and non-actions

```text
CLOUD_CHAT_INTERFACE = RESERVED_NOT_IMPLEMENTED
CLOUD_CHAT_LOGICAL_SLOT = aq-brain-cloud
CLOUD_EMBEDDING_INTERFACE = RESERVED_NOT_IMPLEMENTED
CLOUD_EMBEDDING_LOGICAL_SLOT = aq-embedding-cloud
LITELLM_GATEWAY_DEPLOYED = NO
AUTO_CLOUD_FALLBACK = NO
OPENAI_API_KEY_REQUIRED = NO
PAID_LLM_REQUESTS = 0
PAID_EMBEDDING_REQUESTS = 0
CLOUD_INFERENCE_REQUESTS = 0
MODEL_UPGRADE_PERFORMED = NO
OLLAMA_MODEL_DOWNLOAD = NO
AUTONOMOUS_ATTEMPT_COUNT = 0
RD_AGENT_RESEARCH_LOOP_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
CUSTOM_AQ_ROUTER_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_LOCAL_BRAIN_RESOURCE_ADMISSION_BENCHMARK_001
```
