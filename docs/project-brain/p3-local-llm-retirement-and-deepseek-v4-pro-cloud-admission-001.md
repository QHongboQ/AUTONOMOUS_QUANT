# P3 Local-LLM Retirement and DeepSeek V4 Pro Cloud Admission 001

Date: 2026-09-27

Status: `BLOCKED_DEEPSEEK_API_KEY_REQUIRED`

## Baseline and preserved architecture

The branch starts from exact main
`29b8fe4302c89dc87da48829eaf9127b3adb9ef4`, the squash merge of PR #140.
The active P7 runtime remains 352 physical LOC and
`project_rdagent_candidate_v3.py` remains the unchanged 99-line Candidate V3
projection. P7, P2 sealed-OOS authority, historical Candidate contracts,
RD-Agent, Qlib, and DVC production stages were not modified.

The intended architecture remains:

```text
RD-Agent -> LiteLLM -> Qlib -> Recorder -> Candidate V3 -> P2 -> P4 -> P7
```

Only the proposed generative-LLM provider changes. Embeddings remain on the
existing local epoch.

## Local benchmark stop and evidence preservation

The local candidate process had already been stopped at the user's explicit
cloud-pivot boundary before this task began. No benchmark process, official
FactorCoSTEER evaluator, or Ollama runner remained active. The exact boundary
is:

```text
LOCAL_MODEL_SEARCH_TERMINATION_REASON = USER_AUTHORIZED_CLOUD_PIVOT
LOCAL_BENCHMARK_STOP_BOUNDARY = AFTER_FOUR_COMPLETE_PHI_FULL_ADMISSION_RECOVERY_CYCLES_DURING_FIFTH_GENERATION_BEFORE_ATOMIC_RESULT
```

The incomplete Phi evidence is not reclassified as a pass or terminal
scientific failure. Gemma was never started. The private evidence root
`D:/AQ_DATA/P3/local-factor-coder-secondary-candidate-model-benchmark-001/`
still contains 643 files totaling 18,705,608 bytes. Nothing in it was deleted
or rewritten.

Recorded identities before exact removal:

| Model | Digest | Recorded size | Evidence status |
|---|---|---:|---|
| `granite4.1:3b` | `6fd349357287c7ffc9e38189a93b48ea175d24fc566b38f09cfc564fb7f303eb` | 2.1 GB | screen failed after the frozen ten-loop limit |
| `phi4-mini:3.8b` | `78fad5d182a7c33065e153a5f8ba210754207ba9d91973f57dffa7f487363753` | 2.5 GB | screen passed; full admission incomplete at the stop boundary |
| `gemma3:4b` | `a2af6cc3eb7fa8be8504abaf9b04e88f17a119ec3f04a3addf55f92841195f5a` | 3.3 GB | downloaded, never benchmarked |

All three were removed using native WSL Ollama by exact name. No wildcard or
blob-store cleanup was used. The retained rollback identities are:

| Role | Name | Digest |
|---|---|---|
| chat model and `aq-brain-local` alias | `qwen2.5-coder:7b` | `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` |
| embedding model and `aq-embedding-local` alias | `qwen3-embedding:0.6b` | `ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d` |

The only Ollama runtime is Ubuntu-24.04 WSL2 at
`/home/zhou/.local/ollama-v0.34.0/bin/ollama`. The Windows portable runtime
`D:/AQ_TOOLS/ollama-0.34.4` and temporary store `D:/AQ_MODELS/ollama` are
absent; no Windows Ollama process exists.

## Official DeepSeek evidence

Official live documentation was checked on 2026-09-27:

- [model-list API](https://api-docs.deepseek.com/api/list-models/) lists
  `deepseek-v4-pro`, a 1,048,576-token context window, 393,216 maximum output
  tokens, text input/output, and `low`, `high`, `max` effort levels;
- [Chat Completions](https://api-docs.deepseek.com/api/create-chat-completion/)
  lists `deepseek-v4-pro`, thinking control, and the same effort levels;
- [JSON Output](https://api-docs.deepseek.com/guides/json_mode/) documents
  native `response_format={"type":"json_object"}`; and
- [thinking mode](https://api-docs.deepseek.com/guides/thinking_mode/)
  documents provider effort mapping.

The required API base remains `https://api.deepseek.com`. The public official
catalog establishes that the model is offered, but authenticated live
`GET /models` was not executed because no key is configured. Accordingly
`DEEPSEEK_MODEL_DISCOVERY_PASS` is not claimed.

```text
DEEPSEEK_MODEL_ID = deepseek-v4-pro
DEEPSEEK_CONTEXT_WINDOW = 1048576
DEEPSEEK_MAX_OUTPUT_TOKENS = 393216
DEEPSEEK_EFFORT_LEVELS = low,high,max
OFFICIAL_PUBLIC_CATALOG_MODEL_PRESENT = YES
DEEPSEEK_MODEL_DISCOVERY_PASS = NOT_RUN_BLOCKED_API_KEY
```

## Pinned LiteLLM audit and credential blocker

The authorized RD-Agent Python environment contains exact LiteLLM 1.100.1.
Its native spelling is `deepseek/deepseek-v4-pro`; provider resolution returns
`deepseek`, model metadata is present, and the provider exposes
`response_format`, `thinking`, and `reasoning_effort`. The existing interface
accepts an explicit API base, so no AQ wrapper/client is needed.

The pinned transformation currently maps `low`, `high`, and `max` alike to
`thinking={"type":"enabled"}`. It does not forward the selected effort label.
Thus `max` cannot be asserted through this pinned Chat Completions path; the
strongest native effective setting available without patching or upgrading is
the provider's documented default `high`. This limitation does not prevent the
pinned version from addressing the model, so no dependency upgrade is
authorized by this task.

No `DEEPSEEK_API_KEY` was found in process, user, machine, WSL environment, or
the existing approved local secret inventory. Secret bytes were never read,
printed, hashed, logged, written to Git, or sent to GitHub. Per the task's
fail-closed rule, no unauthenticated substitute, custom client, live chat,
JSON smoke, RD-Agent parse, screen, or full admission was attempted.

```text
PINNED_LITELLM_DEEPSEEK_V4_PRO_SUPPORT = YES_STATIC_NATIVE_MAPPING_LIVE_UNVERIFIED
NATIVE_LITELLM_MODEL = deepseek/deepseek-v4-pro
LITELLM_UPGRADE_REQUIRED = NO
EFFECTIVE_REASONING_MODE = NOT_EXECUTED_PLANNED_PROVIDER_DEFAULT_HIGH
DEEPSEEK_AUTH = NOT_RUN_BLOCKED_API_KEY
DEEPSEEK_CHAT = NOT_RUN_BLOCKED_API_KEY
DEEPSEEK_JSON_OUTPUT = NOT_RUN_BLOCKED_API_KEY
RDAGENT_NATIVE_PARSE = NOT_RUN_BLOCKED_API_KEY
DEEPSEEK_SCREEN_RESULT = NOT_RUN_BLOCKED_API_KEY
FULL_ADMISSION_EXECUTED = NO
```

## Identity, embedding, and safety boundaries

DeepSeek must not be mislabeled as `provider=openai`. No historical Candidate
schema was changed and no Candidate was created. A forward-only truthful
provider identity extension remains mandatory before any real `fin_quant`
activation. The existing qwen3 embedding epoch is unchanged and no reindexing
occurred.

```text
PRIMARY_GENERATIVE_LLM = PROPOSED_DEEPSEEK_V4_PRO_NOT_ADMITTED
EMBEDDING_OWNER = EXISTING_LOCAL_QWEN3_EMBEDDING
EMBEDDING_EPOCH_CHANGED = NO
FUTURE_DEEPSEEK_CANDIDATE_IDENTITY_EXTENSION_REQUIRED = YES
AQ_CUSTOM_CLOUD_LLM_ENGINE = NO
AQ_CUSTOM_PROVIDER_CLIENT = NO
AQ_CUSTOM_RETRY_ENGINE = NO
AQ_CUSTOM_JSON_PARSER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
FIN_QUANT_EXECUTED = NO
P3_FIN_QUANT_004_CREATED = NO
REAL_CANDIDATE_CREATED = 0
REAL_MODEL_TRAINING_COUNT = 0
NEW_RESEARCH_PREDICTIONS = NO
BACKTEST_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
NEXT_TASK = BLOCKED_DEEPSEEK_API_KEY_REQUIRED
FINAL_CLASSIFICATION = BLOCKED_DEEPSEEK_API_KEY_REQUIRED
```
