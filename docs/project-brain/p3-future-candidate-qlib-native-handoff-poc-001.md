# P3 Future Candidate Qlib Native Handoff POC 001

Date: 2026-09-27

## Decision

Future P3 Candidate production can use Qlib's native task path without an AQ
training engine. RD-Agent already supplies a complete `qrun -> task_train`
handoff. AlphaGen supplies expression identity and materialized factor data;
the remaining handoff is only a Qlib task configuration that references the
existing factor Parquet through Qlib's native `StaticDataLoader`.

```text
RD_AGENT_FUTURE_CANDIDATE_HANDOFF = UPSTREAM_WHOLE
ALPHAGEN_TO_QLIB_RESIDUAL = TASK_CONFIGURATION_ONLY
ALPHAGEN_THIN_ADAPTER_REQUIRED = NO
NEW_PRODUCTION_LOC = 0
FINAL_CLASSIFICATION = PASS_RD_AGENT_NATIVE_AND_ALPHAGEN_CONFIG_ONLY_HANDOFF
```

No historical Candidate was opened, refit, mutated or reidentified.

## Upstream handoff audit

Pinned Qlib source commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` owns task execution and
Recorder persistence. Its `qrun` entry calls `task_train`; `task_train`
instantiates the model and dataset, executes `model.fit`, persists `task`,
`params.pkl` and `dataset`, then produces configured records such as
`pred.pkl`.

RD-Agent commit `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` executes its Qlib
workspace with `qrun <config>`. No AQ wrapper or second orchestration layer is
needed.

AlphaGen commit `259687e8f316994426416c530a94842a2fe6405e` owns expression
discovery, not Candidate model training. Existing P3 outputs already provide
the exact expression identity and materialized factor Parquet. Pinned Qlib
`StaticDataLoader` accepts a Parquet path, and the existing P3 US ragged
RD-Agent templates already express `combined_factors_df.parquet` as a native
Qlib loader configuration. The future AlphaGen handoff is therefore data and
configuration, not executable AQ training code.

```text
ALPHAGEN_OUTPUT_TYPE = EXPRESSION_IDENTITY_PLUS_MATERIALIZED_FACTOR_PARQUET
ALPHAGEN_TO_QLIB_HANDOFF = QLIB_TASK_CONFIG_WITH_STATICDATALOADER_PARQUET
ALPHAGEN_TO_QLIB_RESIDUAL = TASK_CONFIGURATION_ONLY
CUSTOM_TRAINING_RUNTIME = NO
```

## Synthetic native-path proof

One bounded private fixture used the pre-existing P1 non-Candidate AAPL/MSFT
provider and called `qlib.model.trainer.task_train` directly. Qlib created a
finished MLflow-backed Recorder and natively wrote all required artifacts.
The POC did not call `R.save_objects` manually.

```text
FIXTURE_CLASSIFICATION = TEST_FIXTURE_NOT_REAL_CANDIDATE
QLIB_NATIVE_ENTRY_USED = qlib.model.trainer.task_train
QLIB_VERSION = 0.9.8.dev26
MLFLOW_VERSION = 3.16.0
SYNTHETIC_RECORDER_ID = 49c5419261db4e0989943a13e2a61d3f
SYNTHETIC_RECORDER_STATUS = FINISHED
SYNTHETIC_RECORDER_TASK_PRESENT = YES
SYNTHETIC_RECORDER_PARAMS_PRESENT = YES
SYNTHETIC_RECORDER_DATASET_PRESENT = YES
SYNTHETIC_RECORDER_PRED_PRESENT = YES
MANUAL_R_SAVE_OBJECTS_COUNT = 0
SYNTHETIC_MODEL_TRAINING_COUNT = 1
```

Artifact identities are:

| Artifact | SHA-256 |
| --- | --- |
| `task` | `9dad4842c858c4f41824e88fda915628c832a46243c6c44e3ad8a085f4bdc3a5` |
| `params.pkl` | `0ffb9976b713f739157a44205d4e24de095413ba7eb007570d16157f757b913d` |
| `dataset` | `225a10acf88f7c98d95419830b463969a715c7676c8a49ed829b96660a7bf8a1` |
| `pred.pkl` | `ac26815d6419fb769697abae0b87930c264171ad8cca330cca3c45783aa01dec` |

The first process completed the upstream Recorder and then encountered a
private post-run JSON Schema subtree-reference error. The corrected
post-validator reused that same Recorder; it did not retrain. All private
MLflow artifacts were moved out of the Git worktree into the authorized
evidence root and their private SQLite artifact URIs were corrected and
reloaded successfully.

## Bounded PredUpdater proof

`RMDLoader` reloaded `LinearModel` from `params.pkl` and `DatasetH` from
`dataset`. Two `PredUpdater(write=False)` replays used explicit
`to_date=2024-01-19`; both produced the same eight-row combined result, with
four new rows after the initial `2024-01-17` boundary. The original four-row
historical prefix was byte-semantically unchanged.

```text
PERSISTED_MODEL_RELOAD = PASS
PERSISTED_DATASET_RELOAD = PASS
BOUNDED_PREDUPDATER = PASS
HISTORICAL_PREFIX_UNCHANGED = PASS
PREDUPDATER_REPLAY_DETERMINISTIC = YES
INITIAL_PREDICTION_SHA256 = c4d78272fdc0c091f98e641fd9ac320b5d8aaf964cc31a37f5dc5618c69845f7
REPLAY_PREDICTION_SHA256 = e57c169d2dd7d999f4d29fb26fdb4266c4ae0007d91b834cf85285aa4f800828
```

## Candidate V3 binding

Candidate V3 requires a real `contentIdentity` when
`serialized_model_artifact.status = PERSISTED`. The synthetic binding
projection validated the existing union using the actual `params.pkl`
SHA-256. The separate existing `qlib_recorder_identity` binds experiment/run
identity and finished status. Together these are sufficient: no second model
identity system is needed.

The persisted Qlib `dataset` object remains Recorder runtime state. Candidate
V3's existing dataset bundle binds authoritative provider, calendar,
instrument, date-range, row-count and DVC dependency identities. It does not
need to copy dataset internals or own a dataset store.

```text
CANDIDATE_V3_PERSISTED_BINDING = PASS_PARAMS_PKL_CONTENT_SHA_PLUS_RECORDER_IDENTITY
CANDIDATE_V3_SCHEMA_CHANGE_REQUIRED = NO
CANDIDATE_OWNED_DATASET_STORE = NO
```

## Responsibility classification

| Capability | Owner classification | Authority |
| --- | --- | --- |
| Candidate expression identity | `IRREDUCIBLE_THIN_AQ_BINDING` | P3 producer evidence projected into Candidate V3 |
| Qlib task configuration | `IRREDUCIBLE_THIN_AQ_BINDING` | AQ supplies project-specific immutable inputs to Qlib's native task schema |
| Model training | `UPSTREAM_WHOLE` | Qlib `task_train` / `TrainerR` |
| Recorder lifecycle | `UPSTREAM_WHOLE` | Qlib Recorder |
| Model persistence | `UPSTREAM_WHOLE` | Qlib Recorder `params.pkl` |
| Dataset persistence | `UPSTREAM_WHOLE` | Qlib Recorder `dataset` |
| Prediction generation | `UPSTREAM_WHOLE` | configured Qlib records and `PredUpdater` |
| Run lineage | `UPSTREAM_LEAF` | Qlib Recorder backed by MLflow |
| Reproducibility | `UPSTREAM_LEAF` | DVC |
| Candidate binding | `IRREDUCIBLE_THIN_AQ_BINDING` | exact upstream identities projected into Candidate V3 |

```text
RUNTIME_MODEL_STATE_OWNER = QLIB_RECORDER
RUN_LINEAGE_OWNER = QLIB_MLFLOW
REPRODUCIBILITY_OWNER = DVC
MLFLOW_MODEL_REGISTRY = NOT_REQUIRED
AQ_TRAINING_ENGINE = NO
AQ_MODEL_STORE = NO
AQ_RECORDER_BUILDER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Future flow

```text
AlphaGen expression + materialized factor Parquet
    -> native Qlib task configuration

or

RD-Agent Qlib workspace
    -> qrun

then

task_train / TrainerR
    -> Recorder: task + params.pkl + dataset + pred.pkl
    -> Candidate V3 persisted-model binding
    -> P2 -> P4 -> P7
```

## Evidence and safety

Private evidence is under
`D:/AQ_DATA/P3/future-candidate-qlib-native-handoff-poc-001/`.

```text
PRIVATE_CHECKSUMS_SHA256 = c90cb3de05d2c6c547804eeede7f91ad0d551aaa6397759ab964dcbd62be4562
CURRENT_17_REFIT_COUNT = 0
CURRENT_17_RECORDER_MUTATION_COUNT = 0
CURRENT_17_CANDIDATE_IDENTITY_CHANGE_COUNT = 0
REAL_CANDIDATE_CREATED = 0
REAL_MODEL_TRAINING_COUNT = 0
REAL_CANDIDATE_PREDICTION_GENERATION_COUNT = 0
REAL_P2_CERTIFICATION_COUNT = 0
REAL_P4_LIFECYCLE_TRANSITION_COUNT = 0
REAL_P7_ENSEMBLE_EXECUTION_COUNT = 0
BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P3_FUTURE_CANDIDATE_UPSTREAM_PATH_FREEZE_001
```
