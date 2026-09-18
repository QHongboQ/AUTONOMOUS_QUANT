# P3 Attempt-003 Blocker Resolution Implementation 001

Implementation date: 2026-09-16

## Scope

This task implemented the two bounded, upstream-first resolutions selected by
the attempt-003 audit. It did not modify or rerun `p3-fin-quant-003`, execute
the project DVC stage, invoke `fin_quant`, create `p3-fin-quant-004`, train a
Qlib model, generate predictions, backtest, access sealed OOS, or create a
Candidate V2 instance.

## Factor Scenario boundary

The thin AQ Factor and Quant Scenario subclasses now append the exact strategy
already owned and rendered by Microsoft RD-Agent at
`rdagent.scenarios.qlib.experiment.prompts:qlib_factor_strategy`. The AQ source
does not copy, rewrite, or replace the upstream prompt. Factor descriptions
receive it once; model-only and simple-background descriptions do not.

```text
FACTOR_STRATEGY_EXPOSURE = PASS
UPSTREAM_PROMPT_COPIED_TO_AQ = NO
AQ_DATA_SCHEMA_CHANGE_REQUIRED = NO
RUNNER_OVERRIDE_REQUIRED = NO
CODER_OVERRIDE_REQUIRED = NO
RD_LOOP_OVERRIDE_REQUIRED = NO
```

## Official factor-coder admission

The admission fixture was derived deterministically from the pinned Microsoft
RD-Agent RD2Bench JSON. The first three eligible, successfully ground-truth-
validated cases by difficulty and name were:

```text
alpha053 = Easy
alpha053_15 = Easy
alpha053_5 = Easy
```

The approved local-only coder was then exercised through the official pinned
`rdagent.app.benchmark.factor.eval` and `FactorImplementEval` path, configured
for two rounds. The upstream strategy text was visible in the live coding
prompt. The model returned Markdown-fenced JSON repeatedly for one task;
RD-Agent exhausted its ten built-in parse retries and raised
`RuntimeError: Failed to create chat completion after 10 retries.` before the
official evaluator could score any of the six required implementations.

This is an admission failure. Parse retries are not counted as CoSTEER
self-correction because evaluator feedback was never reached. No cloud or paid
inference route was used, no model was switched, and no retry outside the one
official benchmark invocation was attempted.

Private evidence is retained under
`D:\AQ_DATA\P3\factor-coder-admission-001`.

```text
RD2BENCH_SOURCE_SHA256 = dc293fe6b6ea4ce2df67226569cbf2c04e7d14fcfc13451b0cd293b085747f99
ADMISSION_FIXTURE_SHA256 = cf4c71c3e1758664082bbd45e06cfb78ca71e625fbf5f45d7a5acbf2587b2b49
GROUND_TRUTH_VALIDATION_SHA256 = 674a9a05dfbe0648ffb8db47b8a7623fff9c968a1e3bbe1f4bc2af1909b5d5f5
ADMISSION_REPORT_SHA256 = 3623fbb52b1d7b25f7c3889784302787176e6cc976a322233778caafbbf774be
FACTOR_CODER_ADMISSION_CASES = alpha053; alpha053_15; alpha053_5
FACTOR_CODER_ADMISSION_ROUNDS = 2
FACTOR_CODER_ADMISSION_TOTAL_REQUIRED = 6
FACTOR_CODER_ADMISSION_COMPLETED = 0
FACTOR_CODER_ADMISSION_PASSES = 0
FACTOR_CODER_ADMISSION_FAILURES = 6
FACTOR_CODER_SELF_CORRECTION_OBSERVED = NO
FACTOR_CODER_ADMISSION = FAIL
LOCAL_LLM_COMPLETION_CALLS = 18
CLOUD_INFERENCE_REQUESTS = 0
PAID_LLM_REQUESTS = 0
```

## WSL DVC alignment

An isolated WSL environment at `/home/zhou/AQ_ENVS/dvc-p3` owns DVC `3.67.1`
on Python `3.12.3`. Its 98 installed packages pass `uv pip check`. A disposable
WSL-on-`/mnt/d` regression proved that this DVC runtime can add and hash a
directory containing a Linux symlink; the scratch repository was then removed.

Only the P3 stage in `dvc.yaml` changed. It now uses native WSL execution,
portable repository-relative external dependencies/output, and the next
namespace `p3-fin-quant-004`. P0/P1/P2 stage bodies and `dvc.lock` remain
unchanged. Native WSL `dvc stage list`, `dvc dag`, and stage status parsing pass.

```text
WSL_DVC_ENV = /home/zhou/AQ_ENVS/dvc-p3
WSL_DVC_VERSION = 3.67.1
WSL_DVC_PYTHON = 3.12.3
WSL_DVC_FREEZE_SHA256 = 4d40f9b8475d5a9cf06bc30e73159f44eb9b4e57a59e6663f9ab3d95cc6614ec
WSL_DVC_PIP_CHECK = PASS
WSL_DVC_WSL_SYMLINK_TEST = PASS
P3_DVC_EXECUTION_OS = WSL_LINUX
WINDOWS_DVC_P3_EXECUTION = NOT_AUTHORIZED
P3_PORTABLE_EXTERNAL_PATHS = PASS
P3_RUN_NAMESPACE = p3-fin-quant-004
P3_RUN_004_ROOT_CREATED = NO
WSL_DVC_STAGE_LIST = PASS
WSL_DVC_DAG = PASS
P3_STAGE_PARSE = PASS
DVC_REPRO_EXECUTED = NO
DVC_LOCK_CHANGED = NO
CANDIDATE_V2_IMPACT = NO_CONTRACT_CHANGE
```

## Validation and decision

```text
BINDING_TESTS = 15/15_PASS
MATERIALIZER_TESTS = 5/5_PASS
LLM_BACKEND_TESTS = 7/7_PASS
DVC_CONFIG_TESTS = 1/1_PASS_INCLUDED_IN_BINDING
TOTAL_RELEVANT_TESTS = 27/27_PASS
RESOURCE_RECOVERY = PASS
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

The DVC blocker is resolved, and the upstream strategy-exposure fix is valid.
The official local factor-coder admission is not. Consequently this task does
not authorize autonomous attempt-004.

```text
P3_ATTEMPT_003_DVC_BLOCKER_RESOLVED = YES
P3_ATTEMPT_003_FACTOR_STRATEGY_GAP_RESOLVED = YES
P3_ATTEMPT_003_FACTOR_CODER_ADMISSION = FAIL
P3_ATTEMPT_003_BLOCKERS_RESOLVED = NO
CURRENT_NEXT = P3_LOCAL_FACTOR_CODER_MODEL_REEVALUATION_001
```
