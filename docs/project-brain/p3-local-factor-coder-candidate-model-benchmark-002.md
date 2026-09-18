# P3 Local Factor Coder Candidate Model Benchmark 002

Benchmark date: 2026-09-16

## Scope

This task restarted the local Factor Coder candidate benchmark under the
certified production envelope. It certified the benchmark path without an LLM,
then applied the mandatory per-candidate runtime gate. The task stopped before
any `FactorCoSTEER` screen when one candidate failed the exact context gate.

```text
BASE_HEAD = d1fb50ee447778d9b19958b000c9dbcf5cc430b0
OLLAMA_CONTEXT_LENGTH = 32768
OLLAMA_NUM_PARALLEL = 1
RDAGENT_SAFE_INPUT = 28672
RDAGENT_MAX_OUTPUT = 4096
CHAT_ROUTE = ollama_chat/aq-brain-local
EMBEDDING_ROUTE = ollama/aq-embedding-local
```

No DVC reproduction, `fin_quant`, autonomous research attempt, Qlib training,
prediction generation, backtest, Candidate V2 creation, or sealed-OOS access
occurred.

## Benchmark-path certification

The three frozen cases were run with their benchmark `gt_code` through the
normal upstream `FactorFBWorkspace` and the official evaluator list used by
`FactorImplementEval`.

```text
GROUND_TRUTH_SELF_TEST = PASS
alpha053.RUN_FACTOR_ERROR = NONE
alpha053.SingleColumn = TRUE
alpha053.RowCount = 1.0
alpha053.Index = 1.0
alpha053.EqualValueRatio = 0.0
alpha053.Correlation = 1.0
alpha053_15.RUN_FACTOR_ERROR = NONE
alpha053_15.SingleColumn = TRUE
alpha053_15.RowCount = 1.0
alpha053_15.Index = 1.0
alpha053_15.EqualValueRatio = 0.0
alpha053_15.Correlation = 1.0
alpha053_5.RUN_FACTOR_ERROR = NONE
alpha053_5.SingleColumn = TRUE
alpha053_5.RowCount = 1.0
alpha053_5.Index = 1.0
alpha053_5.EqualValueRatio = 0.0
alpha053_5.Correlation = 1.0
```

The equal-value metric is zero because the pinned upstream evaluator counts
matching NaNs as unequal. The official correlation evaluator is exactly 1.0
for all three identical implementations, satisfying the authorized equivalent
ground-truth criterion.

## Candidate runtime gate

The first two candidates passed the 32K and structured-output gate. They were
not screened because the later global stop condition invalidated continuation
of the benchmark.

```text
qwen3.5:4b.DIGEST = 2a654d98e6fba55d452b7043684e9b57a947e393bbffa62485a7aac05ee4eefd
qwen3.5:4b.ACTUAL_CONTEXT = 32768
qwen3.5:4b.STRUCTURED_JSON_OBJECT = PASS
qwen3.5:4b.TYPED_SCHEMA = PASS
qwen3.5:4b.MARKDOWN_FENCE = NO
qwen3.5:4b.RDAGENT_NATIVE_PARSE = PASS
qwen3.5:4b.SCREEN = NOT_EXECUTED_GLOBAL_CONTEXT_GATE_STOP

granite-code:8b-instruct.DIGEST = 36c3c3b9683b411ee20ba5c6c6858df83a1d7bf3b65f9fd76a073791e98a18dd
granite-code:8b-instruct.ACTUAL_CONTEXT = 32768
granite-code:8b-instruct.STRUCTURED_JSON_OBJECT = PASS
granite-code:8b-instruct.TYPED_SCHEMA = PASS
granite-code:8b-instruct.MARKDOWN_FENCE = NO
granite-code:8b-instruct.RDAGENT_NATIVE_PARSE = PASS
granite-code:8b-instruct.SCREEN = NOT_EXECUTED_GLOBAL_CONTEXT_GATE_STOP
```

The third candidate's official tag advertises a 16384-token context. After
binding the logical alias and making the required tiny local request, the
authoritative `/api/ps` response also reported 16384, not the required 32768.

```text
deepseek-coder:6.7b-instruct.DIGEST = ce298d984115b93bb1b191b47fee6b39e4e9fbd5f18e651c02f9fa74e0edcd13
deepseek-coder:6.7b-instruct.ADVERTISED_CONTEXT = 16384
deepseek-coder:6.7b-instruct.ACTUAL_CONTEXT = 16384
deepseek-coder:6.7b-instruct.CONTEXT_GATE = FAIL
deepseek-coder:6.7b-instruct.FAILURE_TAXONOMY = INFRASTRUCTURE
deepseek-coder:6.7b-instruct.STRUCTURED_OUTPUT = NOT_RUN_CONTEXT_GATE
deepseek-coder:6.7b-instruct.SCREEN = NOT_EXECUTED_CONTEXT_GATE
```

The benchmark contract requires a global stop when any candidate reports an
actual context other than 32768. Consequently `llama3.1:8b` was not loaded or
tested and no candidate entered the screen or full 6/6 admission phase. This
result is not a model-capability failure for DeepSeek or Llama.

## Evidence and recovery

```text
PRIVATE_ROOT = D:\AQ_DATA\P3\factor-coder-candidate-benchmark-002
BENCHMARK_PATH_SELF_TEST_SHA256 = bb88893aef8650cc70d1b844efccfe92ed746c20ee9c7ad65577fd19c08d8d17
QWEN3_5_RUNTIME_PROOF_SHA256 = d5a0b7ddeba5b09e87909ba84cbfdae1eb9620095e72f32531730427314b4746
GRANITE_RUNTIME_PROOF_SHA256 = 27105ef116042895c857c4053913dfde424da19046e9353e055b8ba49827ee23
DEEPSEEK_RUNTIME_PROOF_SHA256 = 781e295af69bfaacb46a99aa32b0251d47e140507131fd7c7c0fd04a8719cb8d
BENCHMARK_REPORT_SHA256 = 0742fdb7e3d468e7cde2e008dceda607dcdfd4e7c268dc5e51180c032767bbe5
SELECTED_MODEL = NONE
SELECTED_DIGEST = NONE
ALIAS_RESTORED_MODEL = qwen2.5-coder:7b
ALIAS_RESTORED_DIGEST = dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
MODELS_LOADED_AFTER_RECOVERY = 0
EMBEDDING_CHANGED = NO
EMBEDDING_EPOCH_CHANGED = NO
```

## Authority state

```text
P3_FACTOR_CODER_CANDIDATE_BENCHMARK_002 = FAIL_INFRASTRUCTURE_CONTEXT_GATE_MISMATCH
P3_BENCHMARK_002_GROUND_TRUTH_SELF_TEST = PASS
P3_BENCHMARK_002_CANDIDATES_RUNTIME_TESTED = 3
P3_BENCHMARK_002_SCREENS_EXECUTED = 0
P3_BENCHMARK_002_FULL_ADMISSIONS_EXECUTED = 0
P3_BENCHMARK_002_SELECTED_MODEL = NONE
P3_NEXT_AUTONOMOUS_ATTEMPT_AUTHORIZED = NO
P3_FIN_QUANT_004_CREATED = NO
DVC_REPRO_EXECUTED = NO
FIN_QUANT_EXECUTED = NO
CURRENT_NEXT = P3_LOCAL_FACTOR_CODER_CANDIDATE_CONTEXT_GATE_AUDIT_001
FINAL_CLASSIFICATION = FAIL_INFRASTRUCTURE_CONTEXT_GATE_MISMATCH
```
