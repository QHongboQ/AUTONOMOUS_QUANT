# P3 Candidate Qlib Recorder Upstream Persistence Audit 001

Date: 2026-09-27

## Decision

The 17 immutable Formulaic Candidate V3 Recorders lack `task`, `params.pkl`
and `dataset` because their P3 producer bypassed Qlib's standard
`TrainerR` / `task_train` path. The producer opened a Recorder directly,
called `LinearModel.fit`, then generated `SignalRecord` and `SigAnaRecord`.
Those three runtime artifacts were never created; there is no evidence that
they were created and later removed.

```text
CURRENT_17_MISSING_ARTIFACT_ROOT_CAUSE = STANDARD_QLIB_TRAINERR_PATH_NOT_USED
FINAL_CLASSIFICATION = PASS_STANDARD_QLIB_PERSISTENCE_PATH_WAS_BYPASSED
```

This is a P3 Candidate-production ownership issue. P7 remains a downstream
consumer and must not repair historical Candidate persistence.

## Pinned Qlib contract

Source inspection at pinned Qlib commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` and runtime version
`0.9.8.dev26` proves:

- `_log_task_info` saves the original task as Recorder artifact `task`;
- `_exe_task` fits the model, saves it as `params.pkl`, reconfigures the
  dataset for inference and saves it as `dataset`;
- `task_train` executes both operations inside one Recorder;
- `begin_task_train` and `end_task_train` provide the split form of the same
  supported lifecycle;
- `TrainerR` uses the Recorder-based task-training path;
- `RMDLoader.get_dataset` loads `dataset` and `RMDLoader.get_model` loads
  `params.pkl`;
- `PredUpdater` obtains the persisted model from `RMDLoader` and predicts on
  the reconstructed dataset.

The standard Qlib CLI is consistent with this contract: `qrun` imports and
calls `task_train`, then stores the rendered config in the same Recorder.

```text
QLIB_PERSISTS_TASK = YES
QLIB_PERSISTS_PARAMS_PKL = YES
QLIB_PERSISTS_DATASET = YES
PREDUPDATER_REQUIRES_PARAMS_PKL = YES
PREDUPDATER_REQUIRES_DATASET = YES
```

A prior bounded private upstream smoke test independently exercised
`TrainerR(task_train)` with a synthetic, non-Candidate fixture. Its finished
Recorder contained `task`, `params.pkl`, `dataset`, `pred.pkl` and
`label.pkl`; `PredUpdater` extended the bounded interval deterministically
without changing the historical prefix. This is corroboration only and is not
real Candidate training or prediction.

## Actual Formulaic 17 producer path

The authoritative producer script is the frozen private
`run_qlib_evaluation.py` under the P3 AlphaGen Qlib evaluation evidence root.
Its actual call path is:

```text
frozen AlphaGen expression and materialized factor values
    -> make_dataset(candidate_id) -> Qlib DatasetH / StaticDataLoader
    -> LinearModel(estimator="ols", include_valid=False)
    -> R.start(experiment_name, recorder_name=candidate_id)
    -> Recorder.log_params(...)
    -> model.fit(dataset)                         # manual
    -> SignalRecord(model, dataset, recorder)   # manual prediction
    -> SigAnaRecord(recorder)                    # manual analysis
    -> FINISHED Recorder
```

It does not call `TrainerR`, `task_train`, `begin_task_train`,
`end_task_train` or `R.save_objects` for task/model/dataset state. The 17
durable Recorder artifact trees contain exactly 17 each of `pred.pkl`,
`label.pkl`, `sig_analysis/ic.pkl` and `sig_analysis/ric.pkl`, but zero
`task`, zero `params.pkl` and zero `dataset` artifacts.

```text
FORMULAIC_17_ACTUAL_TRAINING_PATH = AQ_PRIVATE_EVALUATION_SCRIPT_R_START_THEN_MANUAL_LINEAR_MODEL_FIT_THEN_SIGNALRECORD_AND_SIGANARECORD
TRAINERR_USED_FOR_FORMULAIC_17 = NO
TASK_TRAIN_USED_FOR_FORMULAIC_17 = NO
ARTIFACTS_CREATED_THEN_REMOVED = NO_EVIDENCE
UPSTREAM_QLIB_DEFECT = NO
```

## AlphaGen and RD-Agent boundary

AlphaGen commit `259687e8f316994426416c530a94842a2fe6405e` owns expression
discovery. Its audited path does not provide a Qlib Candidate Recorder
training handoff. The P3 evaluation stage supplied that boundary manually.

RD-Agent commit `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` already routes Qlib
workspaces through `qrun <config>`. Pinned Qlib `qrun` delegates to
`task_train`, so this is the supported upstream handoff for future RD-Agent
Candidates. AQ does not need a training orchestrator, Recorder builder or
serializer.

```text
ALPHAGEN_QLIB_HANDOFF_STATUS = EXPRESSION_DISCOVERY_ONLY_NO_NATIVE_CANDIDATE_RECORDER_TRAINING_HANDOFF
RD_AGENT_QLIB_HANDOFF_STATUS = PASS_NATIVE_QRUN_DELEGATES_TO_QLIB_TASK_TRAIN
```

## Candidate contract and ownership

Candidate V3 already defines a closed `serialized_model_artifact` union. A
future Candidate can use `PERSISTED` with a real content identity; the
historical 17 correctly use `NOT_PERSISTED_BY_UPSTREAM`. No V4 or successor
contract is required.

The existing Qlib Recorder backed by MLflow supplies run and artifact lineage.
`PredUpdater` consumes Recorder artifacts directly, so MLflow Model Registry
is not required for this path. DVC remains the reproducibility owner; it does
not replace Recorder runtime state.

```text
CANDIDATE_MODEL_TRAINING_OWNER = QLIB / P3 PRODUCER PATH
RUNTIME_MODEL_STATE_OWNER = QLIB_RECORDER
RUN_LINEAGE_OWNER = QLIB_MLFLOW
REPRODUCIBILITY_OWNER = DVC
P7_ROLE = DOWNSTREAM_CONSUMER_ONLY
CANDIDATE_V3_SUPPORTS_PERSISTED_MODEL_BINDING = YES
CANDIDATE_SUCCESSOR_CONTRACT_REQUIRED = NO
MLFLOW_MODEL_REGISTRY_ROLE = NOT_REQUIRED
AQ_MODEL_STORE_REQUIRED = NO
AQ_MODEL_SERIALIZER_REQUIRED = NO
AQ_RECORDER_BUILDER_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

The corrected future path is architectural authority only:

```text
RD-Agent / AlphaGen proposal
    -> Qlib task
    -> TrainerR / task_train
    -> Recorder: task + params.pkl + dataset + pred.pkl
    -> Candidate V3 persisted-model identity binding
    -> P2 -> P4 -> P7
```

The existing 17 remain immutable historical-prediction-only Candidates. They
must not receive retrospective artifacts or inherited identity. Any future
reconstruction/refit creates a new model identity, Recorder identity and
Candidate identity.

## Safety and routing

```text
CURRENT_17_MODEL_STATE = HISTORICAL_PREDICTION_ONLY
CURRENT_17_PROSPECTIVE_INFERENCE_READY = NO
CURRENT_17_REFIT_COUNT = 0
REAL_MODEL_TRAINING_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_ENSEMBLE_EXECUTION_COUNT = 0
BACKTEST_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
NEW_P3_PRODUCTION_LOC = 0
NEW_P7_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P3_FUTURE_CANDIDATE_QLIB_TRAINERR_PATH_ALIGNMENT_001
```
