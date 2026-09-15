# P3 Qlib / MLflow / DVC Artifact-Boundary Resolution

Task:
`AUTONOMOUS-QUANT-P3-QLIB-MLFLOW-DVC-ARTIFACT-BOUNDARY-RESOLUTION-001`

Status:
`COMPLETE — NATIVE SQLITE ALIGNMENT / AUTONOMOUS RUN NOT STARTED`

## 1. Upstream behavior proof

Pinned RD-Agent `QlibFBWorkspace.execute()` passes its native workspace path
as `local_path` for `qrun`; the selected local/Conda environment resolves that
path and supplies it as the subprocess `cwd`. RD-Agent creates each workspace
under its configured workspace root.

MLflow 3.16.0 selects `SqlAlchemyStore` for a SQLite tracking URI. When no
artifact root is supplied, the store uses `./mlruns` and resolves that relative
path against the current working directory. Pinned Qlib
`MLflowExpManager.create_exp()` creates the MLflow experiment without an
explicit artifact location.

```text
RDAGENT_QRUN_WORKSPACE_CWD_PROOF = PASS
MLFLOW_SQLITE_DEFAULT_ARTIFACT_ROOT_PROOF = PASS
MLFLOW_FILE_STORE_SELECTED = NO
MLFLOW_ALLOW_FILE_STORE_USED = NO
FILESYSTEM_TRACKING_BACKEND_USED = NO
FILESYSTEM_ARTIFACT_STORAGE_ALLOWED = YES
FILESYSTEM_ARTIFACT_STORAGE_USED = YES
```

## 2. Disposable native proof

A disposable Qlib experiment used MLflow 3.16.0 with an absolute SQLite URI,
without an explicit artifact location or FileStore compatibility switch. The
SQLite database was created at the temporary run root. The experiment and
recorder artifact locations were descendants of the temporary qrun-equivalent
workspace's `mlruns` directory, and a tiny text artifact was present there.
The complete temporary root was then removed.

```text
NATIVE_SQLITE_TRACKING_PROOF = PASS
NATIVE_SQLITE_ARTIFACT_PROOF = PASS
DISPOSABLE_PROOF_RETIRED = YES
NETWORK_REQUESTS = 0
```

## 3. Run-scoped boundary

All five approved P3 runtime templates now select:

```text
MLFLOW_TRACKING_MODE = RUN_SCOPED_NATIVE_SQLITE
RUN_SCOPED_SQLITE_URI = sqlite:////mnt/d/AQ_DATA/P3/rdagent-us-ragged/dvc-runs/p3-fin-quant-001/mlflow.db
```

The future run-scoped database is a direct child of the existing DVC output.
Native RD-Agent workspaces remain beneath that same output, so MLflow's native
filesystem artifact locations resolve beneath
`workspaces/<native-id>/mlruns`. If later Qlib runs reuse an experiment whose
artifact location was established by an earlier workspace, that location is
still beneath the same DVC output root.

```text
REAL_RUN_ARTIFACT_PATH_UNDER_DVC_OUTPUT = YES
RUN_SCOPED_MLFLOW_DB_IS_DVC_OUTPUT = YES
OLD_SHARED_MLFLOW_DB_IS_DVC_OUTPUT = NO
MLFLOW_ARTIFACTS_UNDER_DVC_OUTPUT = YES
OLD_SHARED_SQLITE_RUNTIME_SELECTED = NO
```

The prior shared path was not deleted, moved, copied, migrated, or merged. It
was absent during this task and therefore remained unmodified.

## 4. Template hash authority

Only the SQLite URI changed in each template. The binding's canonical-text
hash authority was updated to the following finite set:

```text
factor_template/conf_baseline.yaml = ddfb7dd65875636db4cc0acb2471ae1c48d07a30b88b60380ef2a355fdf3d73c
factor_template/conf_combined_factors.yaml = 2758f1f764bc38a1193f3e78320a65eaecdf3360aada2c300881dee5c54f2426
factor_template/conf_combined_factors_sota_model.yaml = 8f5fac7c7f6592f282556c51f5b34c078460db46f9ee3a54c3bcc31385e6d119
model_template/conf_baseline_factors_model.yaml = 6f4aeab4e422e0e4b266c42f132ffd8a8a1b27cfbec74513a92745e60d7cb260
model_template/conf_sota_factors_model.yaml = 4a08250b0e0906f10a4856992aec1bb85f144076d1d4cf1ba34c90fa544b5d69
```

```text
TEMPLATE_HASH_AUTHORITY_UPDATED = YES
BINDING_RUNTIME_LOGIC_CHANGED = NO
ACTIVE_CHINA_EXECUTION_DEFAULTS = 0
```

## 5. Ownership and non-actions

Qlib Recorder and MLflow retain experiment/run identity and native artifact
ownership. DVC retains the enclosing run-root content/dependency identity. No
AQ MLflow manager, artifact engine, experiment database, runner, workflow, or
generic engine was introduced. Candidate identity has not been materialized.

```text
DVC_MODEL_ARTIFACT_IDENTITY_BOUNDARY = READY
DVC_PREDICTION_ARTIFACT_IDENTITY_BOUNDARY = READY
QLIB_RECORDER_NATIVE_IDENTITY_BOUNDARY = READY
DVC_YAML_CHANGED = NO
DVC_LOCK_CHANGED = NO
DVC_REPRO_EXECUTED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
AQ_CUSTOM_MLFLOW_MANAGER_COUNT = 0
AQ_CUSTOM_ARTIFACT_ENGINE_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
LEVEL1_BINDING_TESTS = 12/12 PASS
MATERIALIZER_TESTS = 5/5 PASS
```

## 6. Current state

```text
P3_MLFLOW_DVC_ARTIFACT_ALIGNMENT = PASS
DVC_REQUIRED_IDENTITY_COVERAGE = READY_FOR_FIRST_AUTHORIZED_RUN
P3_DVC_STAGE = ACTIVATED_DEFINITION_ONLY
P3_DVC_LOCK_ENTRY = PENDING_FIRST_AUTHORIZED_AUTONOMOUS_RUN
CURRENT_NEXT = P3_CANDIDATE_TO_P2_IDENTITY_CONTRACT_MATERIALIZATION_001
```
