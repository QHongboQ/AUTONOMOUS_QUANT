# P3 RD-Agent DVC Stage Activation

Task:
`AUTONOMOUS-QUANT-P3-DVC-STAGE-ACTIVATION-001`

Status:
`COMPLETE — DEFINITION ONLY / FIRST AUTONOMOUS RUN NOT STARTED`

## 1. Scope and ownership

The minimum legitimate DVC boundary is activated around the official
Microsoft RD-Agent `fin_quant` entrypoint. DVC owns the stage dependency,
command, output-directory, and future lock identity. RD-Agent continues to own
the autonomous loop, Qlib continues to own dataset/model/prediction/backtest
execution, and Qlib Recorder plus MLflow continue to own experiment and run
identity.

No AQ runner, wrapper, copier, packager, artifact registry, experiment
database, workflow engine, or seal script was added.

```text
DVC_VERSION = 3.67.1
DVC_STAGE_MODE = UPSTREAM_EXECUTION_STAGE
P3_DVC_STAGE_NAME = p3_rdagent_us_quant_research
P3_DVC_STAGE = ACTIVATED_DEFINITION_ONLY
P3_DVC_LOCK_ENTRY = PENDING_FIRST_AUTHORIZED_AUTONOMOUS_RUN
```

## 2. Native deterministic run root

Pinned RD-Agent exposes all required run-root surfaces through native
settings:

```text
WORKSPACE_PATH = /mnt/d/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-001/workspaces
PICKLE_CACHE_FOLDER_PATH_STR = /mnt/d/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-001/pickle-cache
LOG_TRACE_PATH = /mnt/d/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-001/trace
SESSION_CHECKPOINT_ROOT = <LOG_TRACE_PATH>/__session__
```

Individual upstream workspaces retain RD-Agent's native UUID names, but all
of them are descendants of one deterministic run-scoped parent. The output is
declared as one external, non-cached DVC directory:

```text
D:/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-001
```

Using `cache: false` preserves DVC output hashing and future lock identity
without copying private generated artifacts into the repository or DVC cache.

```text
NATIVE_RUN_ROOT = DETERMINISTIC_CONFIGURABLE
AQ_CUSTOM_ARTIFACT_ENGINE = NONE
AQ_CUSTOM_REPRO_ENGINE = NONE
```

## 3. Official execution command

The stage directly invokes:

```text
wsl.exe -d Ubuntu-24.04 ... /home/zhou/AQ_ENVS/rdagent/bin/rdagent fin_quant --loop-n 1
```

Process-local settings provide the six proven AQ class seams, approved factor
source folders, approved 2015-2024 factor/model/quant dates, binding-module
`PYTHONPATH`, and a `PATH` that exposes
`/home/zhou/miniforge3/bin/conda`. A settings-only validation resolved all six
classes, the approved dates, official runner/coder classes, and the intended
Conda executable. No shell profile or operating-system environment was
changed.

## 4. Dependencies and tracking separation

The stage dependencies are finite:

```text
30-research-system/rd-agent/binding/aq_rdagent_us_binding/
30-research-system/rd-agent/templates/p3-us-ragged/
docs/project-brain/p3-rdagent-runtime-provenance-alignment-001.md
docs/project-brain/p3-rdagent-runtime-dependency-alignment-001.md
docs/project-brain/p3-rdagent-conda-discovery-path-configuration-resolution-001.md
D:/AQ_DATA/P3/rdagent-us-ragged/factor-source
D:/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data
```

The Qlib templates retain the native SQLite MLflow manager. A bounded
follow-up aligned their tracking URI to the run-scoped SQLite database beneath
the existing DVC output. Because RD-Agent executes `qrun` from each native
workspace, MLflow's default filesystem artifact root also remains beneath that
same DVC output. A later candidate handoff will bind DVC artifact identity to
the Qlib/MLflow recorder identity; no parallel registry was created.

```text
RUN_SCOPED_MLFLOW_DB_IS_DVC_OUTPUT = YES
OLD_SHARED_MLFLOW_DB_IS_DVC_OUTPUT = NO
MLFLOW_ARTIFACTS_UNDER_DVC_OUTPUT = YES
P3_MLFLOW_DVC_ARTIFACT_ALIGNMENT = PASS
P2_PROVIDER_MUTATED = NO
```

## 5. Static validation

Native DVC 3.67.1 parsed the YAML and listed the new stage. `dvc dag` included
all five stages, and `dvc status` recognized the new stage's seven available
dependencies and absent, expected-first-run output. The four pre-existing
stage-definition hashes were identical before and after the edit. The entire
`dvc.lock` byte hash also remained unchanged:

```text
DVC_LOCK_SHA256 = f8efc1433db7a0e42ce281d45fb973386e22c9f66340a3d561aad3e72d8521ed
EXISTING_DVC_STAGE_DEFINITIONS_CHANGED = NO
EXISTING_DVC_LOCK_ENTRIES_CHANGED = NO
```

The existing lock file reports pre-existing changed dependencies/outputs for
some older stages. Those entries were not regenerated or altered because this
task is definition-only. The new P3 lock entry will be created only by the
first separately authorized autonomous run.

## 6. Isolation and non-actions

The stage passes no date later than 2024-12-31. The binding's immutable factor
source guard independently enforces the same maximum. No sealed-OOS path or
date is a dependency or command input.

```text
P3_CAN_ACCESS_SEALED_OOS = NO
SEALED_OOS_ISOLATION = PASS
DVC_REPRO_EXECUTED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
MARKET_DATA_NETWORK_CALLS = 0
DATASET_DOWNLOADS = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## 7. Current state

```text
P3_DVC_STAGE_ACTIVATION = PASS
P3_DVC_STAGE = ACTIVATED_DEFINITION_ONLY
P3_DVC_LOCK_ENTRY = PENDING_FIRST_AUTHORIZED_AUTONOMOUS_RUN
CURRENT_NEXT = P3_CANDIDATE_TO_P2_IDENTITY_CONTRACT_MATERIALIZATION_001
```
