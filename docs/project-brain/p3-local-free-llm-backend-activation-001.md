# P3 Local Free LLM Backend Activation 001

Activation date: 2026-09-15

## Scope and baseline

This task activated a completely local chat and embedding backend for the
pinned Microsoft RD-Agent runtime. It did not execute the DVC research stage,
RD-Agent `fin_quant`, Qlib training, prediction, or backtesting.

```text
BASE_BRANCH = agent/p3-upstream-research-stack-integration-001
BASE_HEAD = 356cd6779d3e256dc4e1776f87c5503ff6b49289
RDAGENT_VERSION = 0.8.1.dev37
RDAGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
PYTHON_VERSION = 3.11.16
LITELLM_VERSION = 1.100.1
RDAGENT_ENV_PRECHECK = PASS
PINNED_RDAGENT_LITELLM_NATIVE_SUPPORT = PASS
```

The pinned backend is
`rdagent.oai.backend.LiteLLMAPIBackend`; its public settings use the
`LITELLM_` prefix and its implementation calls `litellm.completion()` and
`litellm.embedding()` directly. No RD-Agent or LiteLLM source was patched.

## Hardware admission and model selection

```text
CPU = Intel Core i7-10870H / 16 LOGICAL CPUS
SYSTEM_RAM = 7.6 GiB
AVAILABLE_RAM_AT_ADMISSION = 7.0 GiB
SWAP = 2.0 GiB
GPU_MODEL = NVIDIA GeForce RTX 3060 Laptop GPU
GPU_VRAM_TOTAL = 6144 MiB
GPU_VRAM_FREE_AT_ADMISSION = 5994 MiB
CUDA_VISIBLE_FROM_WSL = YES
LOCAL_INFERENCE_CLASS = GPU_SMALL_MODEL_ONLY
```

The bounded fallback `qwen3:4b` was selected because the 5.2 GB 8B model plus
the required context/runtime overhead is not a stable fit for 6 GiB VRAM and
7.6 GiB system RAM. The 8B model was not downloaded.

```text
SELECTED_CHAT_MODEL = ollama/qwen3:4b
SELECTED_CHAT_MODEL_DIGEST = 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7
SELECTED_CHAT_MODEL_SIZE = 2497293931
SELECTED_CHAT_MODEL_QUANTIZATION = Q4_K_M
SELECTED_EMBEDDING_MODEL = ollama/qwen3-embedding:0.6b
SELECTED_EMBEDDING_MODEL_DIGEST = ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d
SELECTED_EMBEDDING_MODEL_SIZE = 639150858
SELECTED_EMBEDDING_MODEL_QUANTIZATION = Q8_0
SELECTED_EMBEDDING_DIMENSIONS = 1024
```

## Ollama runtime

The official Ollama v0.34.0 Linux amd64 release was installed in the WSL
user directory because the WSL account has no non-interactive sudo authority.
The downloaded official release archive was independently checked before
extraction.

```text
OLLAMA_VERSION = 0.34.0
OLLAMA_INSTALL_ROOT = /home/zhou/.local/ollama-v0.34.0
OLLAMA_RELEASE_ARCHIVE_SHA256 = cf95886728959aa09910bb34de5cca1cc5a8f68003b5597197d3f2c2d57c0804
OLLAMA_ENDPOINT = http://127.0.0.1:11434
OLLAMA_LOCALHOST_ONLY = YES
OLLAMA_REMOTE_CLOUD_USED = NO
LOCAL_CHAT_MODEL_PRESENT = YES
LOCAL_EMBEDDING_MODEL_PRESENT = YES
MODEL_DOWNLOAD_NETWORK_USED = YES_OFFICIAL_OLLAMA_ONLY
```

The service was started process-locally with `OLLAMA_HOST` fixed to
`127.0.0.1:11434`. No listener was exposed on `0.0.0.0`, LAN, or a public
interface. No Ollama account or sign-in was used.

## Native, LiteLLM, and RD-Agent health evidence

Exactly one bounded native chat request and one bounded native embedding
request were issued. The chat response was successful, non-empty, and bound
to `qwen3:4b`. The embedding response contained 1024 finite values.

The installed LiteLLM provider recognizes `OLLAMA_API_BASE`; direct calls from
the exact RD-Agent Python environment succeeded for both selected models. The
pinned RD-Agent backend then passed a Pydantic structured-response proof, a
chat proof, and a public embedding proof. LiteLLM reported that native response
schema is unavailable for this provider and used the pinned RD-Agent fallback;
the returned JSON still validated as `{"status":"ok"}` without parser changes.

```text
OLLAMA_CHAT_NATIVE_HEALTH = PASS
OLLAMA_EMBEDDING_NATIVE_HEALTH = PASS
LITELLM_DIRECT_CHAT_HEALTH = PASS
LITELLM_DIRECT_EMBEDDING_HEALTH = PASS
RDAGENT_RESPONSE_SCHEMA_COMPATIBILITY = PASS_FALLBACK_JSON_VALIDATED
RDAGENT_LITELLM_CHAT_HEALTH = PASS
RDAGENT_LITELLM_EMBEDDING_HEALTH = PASS
PAID_LLM_REQUESTS = 0
PAID_EMBEDDING_REQUESTS = 0
CLOUD_INFERENCE_REQUESTS = 0
```

## Process-local settings contract

The successful proof used only process-local settings. They were not written
to `.bashrc`, `.profile`, Windows environment storage, the repository, or a
secret file. The next authorized run must reapply these settings in its own
process boundary.

```text
OLLAMA_API_BASE = http://127.0.0.1:11434
LITELLM_CHAT_MODEL = ollama/qwen3:4b
LITELLM_EMBEDDING_MODEL = ollama/qwen3-embedding:0.6b
LITELLM_CHAT_TOKEN_LIMIT = 32768
LITELLM_CHAT_MAX_TOKENS = 4096
LITELLM_CHAT_TEMPERATURE = 0.2
LITELLM_REASONING_THINK_RM = true
```

The Ollama service is a user-session runtime, not a persisted system service;
after a WSL shutdown or host restart it must be started again with the same
localhost-only binding before the next health gate.

## Non-actions and state

```text
AUTONOMOUS_ATTEMPT_COUNT = 0
DVC_REPRO_EXECUTED = NO
RD_AGENT_RESEARCH_LOOP_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
MARKET_DATA_NETWORK_CALLS = 0
BROKER_CALLS = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P3_LOCAL_FREE_LLM_BACKEND = ACTIVE
LOCAL_CHAT_BACKEND = OLLAMA
LOCAL_EMBEDDING_BACKEND = OLLAMA
CURRENT_NEXT = P3_FIRST_AUTHORIZED_AUTONOMOUS_SMOKE_AND_CANDIDATE_INSTANCE_001
```
