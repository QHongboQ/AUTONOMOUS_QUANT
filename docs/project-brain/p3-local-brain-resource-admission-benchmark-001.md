# P3 Local Brain Resource Admission Benchmark 001

Benchmark date: 2026-09-15

## Scope and baseline

This was a bounded local admission benchmark. It did not run `fin_quant`, an
RD-Agent research loop, DVC reproduction, Qlib training, prediction,
backtesting, sealed-OOS access, cloud inference, or broker activity.

```text
BASE_HEAD = c3f2374d29ba9e691a8cf4fb4eb00283d4416b3d
OLLAMA_VERSION = 0.34.0
LITELLM_VERSION = 1.100.1
RD_AGENT_BACKEND = rdagent.oai.backend.LiteLLMAPIBackend
BASELINE_MODEL = qwen3:4b
BASELINE_DIGEST = 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7
EMBEDDING_MODEL = qwen3-embedding:0.6b
EMBEDDING_CHANGED = NO
```

The final workload used the existing P3 settings: temperature `0.2`, maximum
output `4096`, token limit `32768`, streaming enabled, thinking-tag removal
enabled, and one outer retry. Structured output used RD-Agent's native
`json_mode` fallback and JSON parser because LiteLLM reports that the Ollama
models do not expose a native response schema through this provider. Code used
RD-Agent's existing Python code-block extraction/continuation path. No AQ
benchmark engine was retained.

## Current official model discovery

The current Ollama catalog was inspected on 2026-09-15. The official
[Qwen3.5 catalog](https://ollama.com/library/qwen3.5) positions the family for
reasoning, coding and agentic work; its 4B tag is a 3.4 GB Q4_K_M model with a
256K context. The official [Qwen2.5-Coder catalog](https://ollama.com/library/qwen2.5-coder)
positions that family for code generation, reasoning and repair; its 7B tag is
a 4.7 GB model with a 32K context.

```text
CANDIDATES_BENCHMARKED = qwen3:4b; qwen3.5:4b; qwen2.5-coder:7b
CHALLENGERS_DOWNLOADED = qwen3.5:4b; qwen2.5-coder:7b
QWEN3_5_9B = REJECTED_BEFORE_DOWNLOAD_6_6_GB_WEIGHTS_EXCEED_6_GIB_VRAM
QWEN3_CODER_30B = REJECTED_BEFORE_DOWNLOAD_19_GB
```

Exact downloaded metadata:

| Model | Digest | Bytes | Parameters | Quantization | Context |
|---|---|---:|---:|---|---:|
| `qwen3.5:4b` | `2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd` | 3,389,983,735 | 4.7B | Q4_K_M | 262,144 |
| `qwen2.5-coder:7b` | `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` | 4,683,087,561 | 7.6B | Q4_K_M | 32,768 |

## Measured resource envelope

```text
WINDOWS_PHYSICAL_RAM = 16935030784 bytes (15.77 GiB)
WSL_RAM_LIMIT = 8201596928 bytes (7.64 GiB)
WSL_AVAILABLE_RAM_PRE_BENCH = 7549534208 bytes (7.03 GiB)
WSL_SWAP_TOTAL = 2147483648 bytes (2.00 GiB)
CPU = Intel Core i7-10870H / 16 LOGICAL CPUS
GPU = NVIDIA GeForce RTX 3060 Laptop GPU
GPU_VRAM_TOTAL = 6144 MiB
GPU_VRAM_FREE_PRE_BENCH = 5994 MiB
CUDA_VISIBLE_FROM_WSL = YES
WINDOWS_WSL_CONFIG = ABSENT
```

## Fixed workload results

All candidates received the same four bounded prompts through Ollama,
LiteLLM 1.100.1 and the pinned RD-Agent backend. Native Ollama streaming was
used only to measure cold load, first token and generation throughput. Peak
resources cover the native probe and all four RD-Agent calls.

| Model | Structured | Python syntax/artifact | Research plan | Longer context | Cold load | TTFT | tokens/s | Peak VRAM | Peak WSL RAM | Swap delta | Recovery | Result |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| `qwen3:4b` | PASS | FAIL: empty response body after thinking consumed the 4096-token budget | PASS | PASS | 7.33 s | 7.49 s | 45.03 | 3,827 MiB | 2,706 MiB | 8.20 MiB | PASS | FAIL |
| `qwen3.5:4b` | PASS | FAIL: empty response body after thinking consumed the 4096-token budget | PASS | PASS | 9.35 s | 9.53 s | 45.54 | 3,993 MiB | 2,537 MiB | 120.53 MiB | PASS | FAIL |
| `qwen2.5-coder:7b` | PASS | PASS: valid Python and requested function present | PASS | PASS | 12.20 s | 12.54 s | 18.97 | 4,189 MiB | 1,355 MiB | 1.77 MiB | PASS | PASS |

The code gate is deliberately factual: it verifies syntactic validity and the
requested function artifact, not mathematical correctness or production
fitness of generated code. Generated code remains untrusted research output
and still requires normal review and tests.

The selected model's RD-Agent wall times were 10.96 seconds for structured
JSON, 10.35 seconds for code, 10.50 seconds for the four-step research plan,
and 5.55 seconds for the 1,799-input-token context case. There were no backend
exceptions or retries in those four admitted calls.

## Selection and lifecycle

`qwen2.5-coder:7b` was the only candidate that passed every hard gate at the
existing 4096-token P3 limit. Although its measured generation rate was lower
than the smaller Qwen3 models, it returned every requested artifact with
practical bounded wall times and stayed within the measured resource envelope.

```text
LOCAL_BRAIN_SELECTED_MODEL = qwen2.5-coder:7b
LOCAL_BRAIN_SELECTED_DIGEST = dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
LOCAL_BRAIN_LOGICAL_SLOT = aq-brain-local
LOGICAL_SLOT_CONFIGURATION_SHA256 = e087c4edb0d4516c0ea5bf0ade8f6129cf070be276566ab8162c5b65ac2db825
MODEL_RESIDENCY_POLICY = ON_DEMAND
MODEL_UNLOAD = PASS
UNLOAD_SECONDS = 3.30
POST_UNLOAD_VRAM_USED = 0 MiB
POST_UNLOAD_WSL_RAM_USED = 979 MiB
RESOURCE_RECOVERY = PASS
```

Ollama's native `cp` command moved `aq-brain-local` to the selected digest.
The losing downloaded challenger `qwen3.5:4b` was removed after evidence was
recorded. Existing `qwen3:4b` remains as the known fallback, while both the
embedding model and `aq-embedding-local` alias remain unchanged. No benchmark
chat model remained resident after validation.

## Qlib handoff readiness and repository impact

After unload, `nvidia-smi` reported zero MiB benchmark-model residency and
5,994 MiB free VRAM. The established `rdagent4qlib` environment imported Qlib
`0.9.8.dev26` and LightGBM `4.7.0`; no fit, prediction or backtest occurred.

Only the resolved chat model and digest changed in the existing logical-slot
configuration. Candidate V2 already records resolved model identity inside
`llm_execution_identity`, so its schema did not change. The slot configuration
is already a DVC dependency; neither `dvc.yaml` nor `dvc.lock` changed.

```text
POST_LLM_QLIB_RESOURCE_READINESS = PASS
CANDIDATE_V2_SCHEMA_CHANGE_REQUIRED = NO
DVC_YAML_CHANGED = NO
DVC_LOCK_CHANGED = NO
DVC_REPRO_EXECUTED = NO
CLOUD_INFERENCE_REQUESTS = 0
PAID_LLM_REQUESTS = 0
AUTONOMOUS_ATTEMPT_COUNT = 0
RD_AGENT_RESEARCH_LOOP_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
LOCAL_BRAIN_RESOURCE_ADMISSION = PASS
CURRENT_NEXT = P3_FIRST_AUTHORIZED_AUTONOMOUS_SMOKE_AND_CANDIDATE_V2_INSTANCE_001
```

## Effective context metadata follow-up

The selected model and its resource admission remain unchanged. A later
pre-run gate found that pinned RD-Agent subtracted LiteLLM's dynamically
reported Ollama output maximum (`32768`) from its input maximum (`32768`). A
thin backend now uses LiteLLM's public metadata registration interface to
declare the approved output budget `4096`, yielding the safe effective input
budget `28672`. One bounded inherited chat health call and one inherited
embedding health call passed; no autonomous attempt or Qlib execution occurred.

```text
LOCAL_BRAIN_SELECTED_MODEL = qwen2.5-coder:7b
LOCAL_BRAIN_SELECTED_DIGEST = dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
CONTEXT_WINDOW = 32768
EFFECTIVE_CHAT_INPUT_LIMIT = 28672
CHAT_MAX_OUTPUT_TOKENS = 4096
CONTEXT_HEADROOM_GATE = PASS
MODEL_SELECTION_CHANGED = NO
AUTONOMOUS_ATTEMPT_COUNT = 0
CURRENT_NEXT = P3_FIRST_AUTHORIZED_AUTONOMOUS_SMOKE_AND_CANDIDATE_V2_INSTANCE_001
```
