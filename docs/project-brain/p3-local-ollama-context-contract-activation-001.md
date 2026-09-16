# P3 Local Ollama Context Contract Activation 001

Activation date: 2026-09-16

## Scope and authority

This task activated the already-certified Ollama 32K provider runtime contract.
It did not benchmark model capability, run `FactorCoSTEER`, execute DVC or
`fin_quant`, create `p3-fin-quant-004`, train a model, produce predictions, or
run a backtest.

```text
BASE_BRANCH = agent/p3-upstream-research-stack-integration-001
BASE_HEAD = 1877b8ceb54f25aa2f20ef5fd92e95b3e03539c0
CERTIFICATION_REPORT = D:\AQ_DATA\P3\ollama-context-certification-001\context_certification_report.json
CERTIFICATION_REPORT_SHA256 = 914b87f29a8bedc2c78fd80273c8a53f660bdde736d2e09f038a1a95d7b0a6e7
CERTIFIED_OLLAMA_CONTEXT = 32768
PRODUCTION_OLLAMA_CONTEXT = 32768
OLLAMA_NUM_PARALLEL = 1
SAFE_INPUT_BUDGET = 28672
MAX_OUTPUT_TOKENS = 4096
CONTRACT_SUM = 32768
CONTEXT_MISMATCH = CLOSED
```

## Authoritative Ollama runtime

The authoritative endpoint is owned by the `zhou` user in the
`Ubuntu-24.04` WSL2 distribution. The executable is the existing official
user-local Ollama binary:

```text
OLLAMA_VERSION = 0.34.0
OLLAMA_SERVER_HOST_OS = UBUNTU_24_04_WSL2
OLLAMA_SERVER_EXECUTABLE = /home/zhou/.local/ollama-v0.34.0/bin/ollama
PRIOR_STARTUP_OWNERSHIP = WSL_USER_SHELL_NOHUP
SYSTEMD_OLLAMA_UNIT = NONE
PERSISTENT_CONTEXT_MECHANISM = WSL_LOGIN_PROFILE_OFFICIAL_OLLAMA_ENVIRONMENT
OLLAMA_CONTEXT_LENGTH = 32768
OLLAMA_NUM_PARALLEL = 1
OLLAMA_ENDPOINT = http://127.0.0.1:11434
OLLAMA_LOCALHOST_ONLY = YES
```

The WSL login profile now exports the two official Ollama environment
variables. The controlled user-session restart also supplied the same exact
values explicitly, so the server did not rely on implicit defaults. No second
Ollama installation, proxy, request rewriter, custom server, or AQ runtime
manager was created.

After restart the API remained reachable and the existing model store
contained nine entries. A tiny local-only request loaded
`qwen2.5-coder:7b`; the official `/api/ps` response and runner log proved:

```text
CURRENT_CHAT_MODEL = qwen2.5-coder:7b
CURRENT_CHAT_DIGEST = dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
ACTUAL_LOADED_RUNNER_CONTEXT = 32768
RUNNER_ARGUMENTS = -c 32768 -np 1
RUNTIME_CONTEXT_VERIFIED = YES
MODEL_UNLOADED_AFTER_PROOF = YES
```

## Repository configuration identity

The logical-slot configuration now records the provider runtime facts. The
chat route, resolved chat model and digest, embedding model and digest, and
embedding epoch are unchanged. The backend already enforced the matching
32K/28672/4096 contract and required no implementation change.

```text
OLD_LLM_CONFIGURATION_SHA256 = 625aa6834f8466535e12e49c643e69d7edf40bbc066e1ba5a56869ac82ba46c1
NEW_LLM_CONFIGURATION_SHA256 = 770f25c549a83b709535e376cca519d7c7fb1c988eb4f68cb76d8df0fbfaddf9
EMBEDDING_CHANGED = NO
EMBEDDING_EPOCH_CHANGED = NO
CANDIDATE_V2_SCHEMA_CHANGED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

The focused repository regression remains:

```text
BINDING_TESTS = 15/15_PASS
MATERIALIZER_TESTS = 5/5_PASS
LLM_BACKEND_TESTS = 8/8_PASS
REPOSITORY_TESTS = 28/28_PASS
```

## Benchmark authority and next state

The historical qwen2.5 admission remains a valid failure because every
historical admission prompt plus completion fit inside the then-active 4096
runner context. Candidate benchmark 001 remains preserved but cannot select a
model because its candidates did not share the certified provider context.

```text
QWEN2_5_HISTORICAL_ADMISSION = VALID_FAIL
CANDIDATE_BENCHMARK_001 = PROVISIONAL_NOT_VALID_FOR_SELECTION
BENCHMARK_RESTART_AUTHORIZED = YES
AUTONOMOUS_ATTEMPT_004_AUTHORIZED = NO
P3_FIN_QUANT_004_CREATED = NO
DVC_REPRO_EXECUTED = NO
FIN_QUANT_EXECUTED = NO
CURRENT_NEXT = P3_LOCAL_FACTOR_CODER_CANDIDATE_MODEL_BENCHMARK_002
FINAL_CLASSIFICATION = PASS_CERTIFIED_OLLAMA_32K_CONTEXT_ACTIVATED
```

Untracked helper, cache, and log paths remain outside Git and are not Project
Brain authority. No cleanup, move, quarantine, or deletion was performed by
the resumed task.
