# P3 Future Candidate Upstream Path Freeze 001

Date: 2026-09-27

Status: `PASS_FUTURE_CANDIDATE_UPSTREAM_PATH_FROZEN`

This authority closes P3 persistence/runtime architecture development for
future Candidates. It freezes the upstream-native path already demonstrated by
the Qlib Recorder persistence audit and the bounded future-Candidate handoff
POC. It does not execute training, create a Candidate, retrofit the historical
17 Candidates, or change any P2, P4, or P7 authority.

## Producer handoffs

```text
RD_AGENT_FUTURE_CANDIDATE_HANDOFF = UPSTREAM_WHOLE_QRUN_TO_QLIB_TASK_TRAIN
ALPHAGEN_FUTURE_CANDIDATE_HANDOFF = EXPRESSION_IDENTITY_PLUS_MATERIALIZED_FACTOR_PARQUET_TO_QLIB_TASK_CONFIG
ALPHAGEN_EXECUTABLE_ADAPTER_REQUIRED = NO
```

RD-Agent enters the native Qlib path through `qrun`; it receives no AQ
training wrapper. AlphaGen supplies an immutable expression identity and an
immutable materialized factor Parquet artifact to a native Qlib task
configuration. That project-specific configuration/data binding is the full
residual AQ responsibility; there is no executable AlphaGen adapter or task
generation framework.

A future AlphaGen Qlib task configuration must reference:

- the immutable AlphaGen expression identity;
- the immutable materialized factor artifact identity and path;
- a `StaticDataLoader`-compatible Parquet input;
- frozen train/validation/test or applicable prospective segments;
- the pinned model class and configuration;
- the pinned Dataset/handler configuration;
- configured `SignalRecord` and other required records; and
- the exact Qlib source/runtime identity.

## Upstream ownership

QLib owns native task execution, model and Dataset instantiation, `model.fit`,
Recorder lifecycle, task persistence, `params.pkl`, persisted inference
Dataset state, configured prediction generation, and `PredUpdater` inference.
MLflow is used through Qlib Recorder for run lineage; DVC remains the
reproducibility owner. MLflow Model Registry is not required for this path.

```text
MODEL_TRAINING_OWNER = QLIB
RUNTIME_MODEL_STATE_OWNER = QLIB_RECORDER
PREDICTION_RUNTIME_OWNER = QLIB
RUN_LINEAGE_OWNER = QLIB_MLFLOW
REPRODUCIBILITY_OWNER = DVC
MLFLOW_MODEL_REGISTRY_ROLE = NOT_REQUIRED_FOR_CURRENT_PATH
```

The supported default production route is `qrun` / `task_train` / `TrainerR`.
The historical direct `R.start -> model.fit -> SignalRecord -> SigAnaRecord`
pattern is not an authorized default for future real Candidates.

```text
MANUAL_MODEL_FIT_FOR_REAL_CANDIDATE = PROHIBITED_BY_DEFAULT
MANUAL_RECORDER_MODEL_PERSISTENCE = PROHIBITED_BY_DEFAULT
MANUAL_PARAMS_PKL_WRITE = PROHIBITED_BY_DEFAULT
```

## Candidate binding

Candidate V3 already supports the future persisted-model path. A future
Candidate with `serialized_model_artifact.status = PERSISTED` binds the actual
persisted `params.pkl` content SHA-256, while the existing
`qlib_recorder_identity` independently binds the Qlib experiment/run identity.
Candidate V3 continues to retain its existing dataset, source, and runtime
authorities. No second model identity system is permitted.

```text
CANDIDATE_V3_PERSISTED_BINDING = PARAMS_PKL_CONTENT_SHA256_PLUS_QLIB_RECORDER_IDENTITY
CANDIDATE_V3_SCHEMA_CHANGE_REQUIRED = NO
CANDIDATE_V4_REQUIRED = NO
```

## Historical 17 and authority boundaries

The original 17 Candidate V3 identities remain immutable historical-prediction
evidence. They are not prospectively inference-ready and must not be retrofitted
with `task`, `params.pkl`, or Dataset artifacts. Any later training creates a
new model identity, new Recorder identity, and new Candidate identity.

```text
CURRENT_17_MODEL_STATE = HISTORICAL_PREDICTION_ONLY
CURRENT_17_PROSPECTIVE_INFERENCE_READY = NO
CURRENT_17_REFIT_COUNT = 0
CURRENT_17_RECORDER_MUTATION_COUNT = 0
CURRENT_17_CANDIDATE_IDENTITY_CHANGE_COUNT = 0
```

The authority boundary remains:

```text
P3 = PRODUCE_IMMUTABLE_CANDIDATE_EVIDENCE
P2 = CERTIFICATION_AUTHORITY
P4 = LIFECYCLE_AUTHORITY
P7 = DOWNSTREAM_AUTHORIZED_ENSEMBLE_CONSUMER
```

Recorder existence, persisted model state, or Qlib online status does not imply
P2 certification, P4 lifecycle eligibility, or P7 roster authorization.

## Frozen future flow

```text
RD-Agent
  -> native Qlib qrun

OR

AlphaGen
  -> expression identity + materialized factor artifact
  -> native Qlib task configuration

THEN

Qlib task_train / TrainerR
  -> Recorder: task + params.pkl + dataset + pred.pkl
  -> Candidate V3 persisted-model binding
  -> P2
  -> P4
  -> P7
```

## Prohibited duplicate engines and safety

```text
AQ_TRAINING_ENGINE = NO
AQ_MODEL_STORE = NO
AQ_MODEL_SERIALIZER = NO
AQ_RECORDER_BUILDER = NO
AQ_MODEL_REGISTRY = NO
AQ_PREDICTION_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0

REAL_CANDIDATE_CREATED = 0
REAL_MODEL_TRAINING_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_P2_CERTIFICATION_COUNT = 0
REAL_P4_LIFECYCLE_TRANSITION_COUNT = 0
REAL_P7_ENSEMBLE_EXECUTION_COUNT = 0
BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
```

P3 future-Candidate production architecture is closed. Prospective dynamic P7
remains gated by real P2 eligibility. The independently executable historical
17-prediction static ensemble remains research-only and must not be represented
as dynamic-roster, certification, or production evidence.

```text
CURRENT_DEVELOPMENT_NEXT = P7_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_FUTURE_CANDIDATE_UPSTREAM_PATH_FROZEN
```
