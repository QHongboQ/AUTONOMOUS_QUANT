# P3 Local Factor Coder Candidate Model Benchmark 003

Benchmark date: 2026-09-17

## Scope

This task completed the final first-tier comparison of the three
context-eligible local Factor Coder candidates under the frozen 32768-token
Ollama contract. It reused the benchmark-002 ground-truth self-test and used
the official Microsoft RD-Agent `rdagent.app.benchmark.factor.eval`,
`FactorCoSTEER`, and `FactorImplementEval` path without prompt, evaluator,
retry, context, temperature, or output-budget changes.

```text
BASE_HEAD = 3ce1059e5305be0ead25475adb0ecc851525e5ce
OLLAMA_VERSION = 0.34.0
OLLAMA_CONTEXT_LENGTH = 32768
OLLAMA_NUM_PARALLEL = 1
RDAGENT_SAFE_INPUT = 28672
RDAGENT_MAX_OUTPUT = 4096
FACTOR_COSTEER_MAX_LOOP = 10
FACTOR_RUNTIME = /home/zhou/miniforge3/envs/rdagent4qlib/bin/python
EMBEDDING = qwen3-embedding:0.6b
BENCHMARK_PATH_AUTHORITY = PASS_REUSED_FROM_BENCHMARK_002
BENCHMARK_PATH_SELF_TEST_SHA256 = bb88893aef8650cc70d1b844efccfe92ed746c20ee9c7ad65577fd19c08d8d17
```

No cloud fallback, DeepSeek test, DVC reproduction, `fin_quant`, autonomous
research attempt, model training, research prediction, backtest, Candidate V2
creation, or sealed-OOS access occurred.

## Candidate results

All three candidates passed the exact alias/digest, 32768-context, tiny local
request, structured `json_object`, native typed-schema, and RD-Agent parse
runtime gates.

### qwen3.5:4b

```text
DIGEST = 2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd
SCREEN = PASS
SCREEN_COSTEER_LOOPS = 7
SCREEN_LLM_CALLS = 25
SCREEN_MAX_PROMPT_TOKENS = 4064
SCREEN_MAX_COMPLETION_TOKENS = 1104
SCREEN_FINISH_REASONS = stop:24; length:1
SCREEN_CONTINUATIONS = 1
SCREEN_4096_CEILING_HITS = 0
SCREEN_SINGLE_COLUMN = TRUE
SCREEN_ROW_COUNT = 1.0
SCREEN_INDEX = 1.0
SCREEN_EQUAL_VALUE_RATIO = 0.0
SCREEN_CORRELATION = 1.0
SCREEN_RANK_CORRELATION = 0.999980
THINKING_CONTENT_PRODUCED = YES
REASONING_THINK_RM = TRUE
THINKING_CONSUMES_PRODUCTION_OUTPUT_BUDGET = YES
```

The screen pass authorized the six-case AQ admission. The same generated
implementation was evaluated twice for each required factor. Every run had no
factor execution error, one output column, row ratio 1.0, and index ratio 1.0,
but every equal-value ratio was 0.0 and every correlation was far below the
required greater-than-0.99 threshold.

```text
alpha053.ROUND_1.CORRELATION = 0.428381
alpha053.ROUND_2.CORRELATION = 0.428381
alpha053_15.ROUND_1.CORRELATION = 0.410446
alpha053_15.ROUND_2.CORRELATION = 0.410446
alpha053_5.ROUND_1.CORRELATION = 0.435539
alpha053_5.ROUND_2.CORRELATION = 0.435539
FULL_ADMISSION = FAIL
FULL_ADMISSION_PASS_COUNT = 0/6
FULL_ADMISSION_LLM_CALLS = 29
FULL_ADMISSION_MAX_PROMPT_TOKENS = 4677
FULL_ADMISSION_MAX_COMPLETION_TOKENS = 797
FULL_ADMISSION_4096_CEILING_HITS = 0
FAILURE_TAXONOMY = VALUE; CORRELATION
```

### granite-code:8b-instruct

```text
DIGEST = 36c3c3b9683b411ee20ba5c6c6858df83a1d7bf3b65f9fd76a073791e98a18dd
SCREEN = FAIL
SCREEN_COSTEER_LOOPS = 2
SCREEN_LLM_CALLS = 13
SCREEN_MAX_PROMPT_TOKENS = 2937
SCREEN_MAX_COMPLETION_TOKENS = 392
SCREEN_FINISH_REASONS = stop:13
SCREEN_CONTINUATIONS = 0
SCREEN_4096_CEILING_HITS = 0
RAW_RESPONSE_CLASSIFICATION = MODEL_RAW_RESPONSE_INVALID
FAILURE_TAXONOMY = TYPED_SCHEMA
FULL_ADMISSION = NOT_RUN_SCREEN_FAIL
FULL_ADMISSION_PASS_COUNT = 0
```

The model's raw response supplied invalid field types to the requested schema.
The pinned parser exhausted its native retries and failed closed. The evidence
does not show AQ, LiteLLM, or RD-Agent transformation corruption.

### llama3.1:8b

```text
DIGEST = 46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e
SCREEN = FAIL
SCREEN_COSTEER_LOOPS = 10
SCREEN_LLM_CALLS = 38
SCREEN_MAX_PROMPT_TOKENS = 23750
SCREEN_MAX_COMPLETION_TOKENS = 4114
SCREEN_CONTINUATIONS = 6
SCREEN_4096_CEILING_HITS = 6
FAILURE_TAXONOMY = OUTPUT_LENGTH; SOURCE_SCHEMA; VALUE; FACTOR_EXECUTION; COSTEER_RECOVERY
FULL_ADMISSION = NOT_RUN_SCREEN_FAIL
FULL_ADMISSION_PASS_COUNT = 0
```

The model completed all ten upstream recovery loops naturally. Its generated
implementations repeatedly used source-column names that did not exist, then
produced later implementations with incorrect factor semantics or output
behavior. The final screen remained fail-closed. This was a model/production
compatibility result, not a context-infrastructure failure.

## Selection and recovery

No candidate satisfied the mandatory 6/6 admission gate, so no least-bad
candidate was selected. The logical alias was restored to the historical
`qwen2.5-coder:7b` digest and unloaded. This recovery does not change that
model's historical valid admission failure.

```text
SELECTED_MODEL = NONE
SELECTED_DIGEST = NONE
SELECTION_REASON = NO_CANDIDATE_REACHED_6_OF_6
ALIAS_RESTORED_MODEL = qwen2.5-coder:7b
ALIAS_RESTORED_DIGEST = dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
MODELS_LOADED_AFTER_RECOVERY = 0
OLD_LLM_CONFIGURATION_SHA256 = 770f25c549a83b709535e376cca519d7c7fb1c988eb4f68cb76d8df0fbfaddf9
NEW_LLM_CONFIGURATION_SHA256 = 770f25c549a83b709535e376cca519d7c7fb1c988eb4f68cb76d8df0fbfaddf9
EMBEDDING_CHANGED = NO
EMBEDDING_EPOCH_CHANGED = NO
```

## Evidence and next authority

```text
PRIVATE_REPORT = D:\AQ_DATA\P3\factor-coder-candidate-benchmark-003\benchmark_summary.json
PRIVATE_REPORT_SHA256 = b16cf0d9e839d9f6638816270cf8e3f82ae7ed4d3fcf3088dd2b9fe68d9f4397
REPOSITORY_TESTS = 28/28_PASS
P3_FIN_QUANT_004_CREATED = NO
DVC_REPRO_EXECUTED = NO
FIN_QUANT_EXECUTED = NO
SEALED_OOS_ACCESSED = NO
NEXT_AUTONOMOUS_ATTEMPT_AUTHORIZED = NO
CURRENT_NEXT = P3_LOCAL_FACTOR_CODER_SECONDARY_CANDIDATE_MODEL_BENCHMARK_001
FINAL_CLASSIFICATION = PASS_NO_FIRST_TIER_CANDIDATE_ADMITTED
```
