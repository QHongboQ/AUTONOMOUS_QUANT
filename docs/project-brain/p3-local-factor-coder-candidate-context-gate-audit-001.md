# P3 Local Factor Coder Candidate Context Gate Audit 001

Audit date: 2026-09-16

## Scope

This bounded audit corrects only the candidate context-gate semantics used for
future Factor Coder benchmarks. It does not rerun or rewrite benchmark 002 and
does not modify Ollama, LiteLLM, RD-Agent, or the certified 32768-token
production context contract.

```text
BASE_HEAD = b0c0b494b1ff832337e28df36a3a55bb5d5cf8cb
BENCHMARK_002_PRESERVED_UNCHANGED = YES
BENCHMARK_002_GROUND_TRUTH_SELF_TEST = PASS
GLOBAL_OLLAMA_32K_CONTRACT = PASS
```

## Correct context-gate semantics

The 32768-token contract is a candidate admission requirement. A candidate
whose native maximum context is below 32768 is individually ineligible for P3;
that expected native limitation does not invalidate the global Ollama service
or stop evaluation of the remaining eligible candidates.

```text
qwen3.5:4b = CONTEXT_ELIGIBLE
granite-code:8b-instruct = CONTEXT_ELIGIBLE
deepseek-coder:6.7b-instruct = CONTEXT_INELIGIBLE_FOR_P3
deepseek-coder:6.7b-instruct.NATIVE_MAXIMUM_CONTEXT = 16384
deepseek-coder:6.7b-instruct.REQUIRED_CONTEXT = 32768
deepseek-coder:6.7b-instruct.REASON = NATIVE_MAXIMUM_CONTEXT_BELOW_REQUIRED_CONTEXT
llama3.1:8b = CONTEXT_ELIGIBLE
```

The DeepSeek result is therefore an expected candidate-native limit, not a
global infrastructure defect. Benchmark 002 remains immutable historical
evidence of its fail-closed execution; this audit supersedes only the earlier
interpretation that one ineligible candidate must stop the whole candidate
benchmark.

```text
DEEPSEEK_RESULT = EXPECTED_CANDIDATE_NATIVE_LIMIT
GLOBAL_INFRASTRUCTURE_DEFECT = NO
CANDIDATE_NATIVE_CONTEXT_BELOW_32768_ACTION = REJECT_CANDIDATE_INDIVIDUALLY
GLOBAL_BENCHMARK_STOP_REQUIRED = NO
```

## Non-actions and next authority

```text
MODEL_BENCHMARK_EXECUTED = NO
MODEL_LOADED = NO
OLLAMA_CHANGED = NO
LITELLM_CHANGED = NO
RDAGENT_CHANGED = NO
CONTEXT_CONTRACT_CHANGED = NO
DVC_REPRO_EXECUTED = NO
FIN_QUANT_EXECUTED = NO
AUTONOMOUS_ATTEMPT_004_AUTHORIZED = NO
BENCHMARK_003_AUTHORIZED = YES
CURRENT_NEXT = P3_LOCAL_FACTOR_CODER_CANDIDATE_MODEL_BENCHMARK_003
FINAL_CLASSIFICATION = PASS_CANDIDATE_CONTEXT_GATE_SEMANTICS_CORRECTED
```
