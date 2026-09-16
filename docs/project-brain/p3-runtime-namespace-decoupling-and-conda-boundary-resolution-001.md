# P3 Runtime Namespace Decoupling and Conda Boundary Resolution 001

## Scope

This task resolves the configuration blocker observed during the first real
P3 autonomous attempt. It does not execute `dvc repro`, `rdagent fin_quant`, an
LLM research call, Qlib training, prediction, backtest, MLflow run creation,
or Candidate materialization.

## Failed attempt 001

The failed run root remains byte-for-byte in place at
`D:/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-001`. A deterministic
manifest was calculated in memory from sorted UTF-8 records of
`relative_path<TAB>size<TAB>sha256<LF>`; no manifest or other file was written
into the failed root.

```text
FAILED_ATTEMPT_001_STATE = PRESERVED_IMMUTABLE_PRE_RESEARCH_FAILURE
FAILED_ATTEMPT_001_FILE_COUNT = 16
FAILED_ATTEMPT_001_TOTAL_BYTES = 39673
FAILED_ATTEMPT_001_MANIFEST_SHA256 = 1f671a5ee8a0a854731750a03ad50683a9d938ea0c473ef075ae678ed18e48b2
FAILED_ATTEMPT_001_MUTATED = NO
```

The pinned RD-Agent factor CoSTEER implementation constructs
`CondaConf(conda_env_name=os.environ.get("CONDA_DEFAULT_ENV"))`, while
`CondaConf.conda_env_name` is a required string. Attempt 001 omitted that
process-local variable and failed before autonomous LLM inference or Qlib
execution.

```text
ROOT_CAUSE = MISSING_PROCESS_LOCAL_CONDA_DEFAULT_ENV
CUSTOM_RDAGENT_FIX_REQUIRED = NO
CONDA_DEFAULT_ENV = rdagent4qlib
CONDA_ENV_PREFIX = /home/zhou/miniforge3/envs/rdagent4qlib
QLIB_VERSION = 0.9.8.dev26
LIGHTGBM_VERSION = 4.7.0
FACTOR_COSTEER_ENV_CONSTRUCTION = PASS
```

## Native runtime namespace

DVC 3.67.1 owns one variable, `P3_RUN_NAMESPACE`, whose current value is
`p3-fin-quant-002`. The P3 stage interpolates that value into the workspace,
pickle cache, trace, Qlib MLflow SQLite URI, and DVC output root. It also binds
`CONDA_DEFAULT_ENV=rdagent4qlib` process-locally. No shell profile, global
environment, Conda environment, RD-Agent source, or Qlib source changed.

Pinned Qlib was proven in a disposable process to consume
`QLIB_MLFLOW_URI` natively: both `QSETTINGS.mlflow.uri` and the default
`C["exp_manager"]["kwargs"]["uri"]` resolved to the attempt-002 SQLite URI.
The native default experiment name remained `Experiment`. No MLflow run was
created.

```text
QLIB_PROCESS_LOCAL_MLFLOW_URI_PROOF = PASS
NEXT_RUN_NAMESPACE = p3-fin-quant-002
WORKSPACE_ROOT = /mnt/d/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-002/workspaces
PICKLE_CACHE_ROOT = /mnt/d/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-002/pickle-cache
TRACE_ROOT = /mnt/d/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-002/trace
MLFLOW_DB = sqlite:////mnt/d/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-002/mlflow.db
DVC_OUTPUT_ROOT = D:/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-002
RUN_NAMESPACE_COHERENCE = PASS
ACTIVE_RUNTIME_001_REFERENCE_COUNT = 0
```

## Immutable template normalization

The five approved Qlib templates no longer embed an `exp_manager` block or an
attempt-specific MLflow URI. Qlib's native process-local configuration now
owns that runtime selection. Only the five normalized template hash constants
were refreshed; binding logic did not change.

```text
ATTEMPT_ID_PRESENT_IN_TEMPLATE_COUNT = 0
TEMPLATE_HASH_CONSTANTS_CHANGED = 5
BINDING_RUNTIME_LOGIC_CHANGED = NO
FACTOR_TEMPLATE_CONF_BASELINE_SHA256 = ddc6713ca9b07b44f210c0dc61d15fa3359fdd9a3e0e2dfd832331b58674bb40
FACTOR_TEMPLATE_CONF_COMBINED_SHA256 = 9641b4eaca343ce3d690c4389a47e147e9de130b893af8db900f24365578f03c
FACTOR_TEMPLATE_CONF_COMBINED_SOTA_SHA256 = 4ab822372277af50d3a6ccc7fb1558b6c90a3148536fe9e0b920ef092a481029
MODEL_TEMPLATE_CONF_BASELINE_SHA256 = 9ccbda614474cec2834543baa39e9cb0500091911718bf9df9f49dd5cc195cb7
MODEL_TEMPLATE_CONF_SOTA_SHA256 = 5470f63512477a0f232db3eca00db23c9cfe04227f991769513349dcff61813b
TEMPLATE_HASH_GUARD = PASS
FUTURE_ATTEMPT_REQUIRES_TEMPLATE_CHANGE = NO
FUTURE_ATTEMPT_REQUIRES_HASH_REFRESH = NO
```

## Execution boundary

The exact stage environment successfully constructed the pinned
`CondaConf`, resolved the `rdagent4qlib` bin path, constructed the factor
CoSTEER environment, and instantiated
`USLocalOllamaLiteLLMAPIBackend` with input 28672 and output 4096. These were
configuration-only checks; no inference occurred.

DVC's non-executing `stage list` and `dag` commands parsed the native variable
and resolved the P3 output to `p3-fin-quant-002`. The existing binding, local
LLM backend, and materializer suites passed 24/24 tests.

```text
CONTEXT_HEADROOM_GATE = PASS
BINDING_AND_MATERIALIZER_TESTS = 24/24_PASS
DVC_REPRO_EXECUTED = NO
AUTONOMOUS_ATTEMPT_COUNT_THIS_TASK = 0
MLFLOW_RUN_CREATED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
CANDIDATE_CREATED = NO
P3_DVC_LOCK_ENTRY = ABSENT
CURRENT_NEXT = P3_FIRST_AUTHORIZED_AUTONOMOUS_SMOKE_AND_CANDIDATE_V2_INSTANCE_003
```
