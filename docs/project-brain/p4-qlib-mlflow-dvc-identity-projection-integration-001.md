# P4 Qlib / MLflow / DVC Identity Projection Integration 001

## Decision

```text
P4_QLIB_MLFLOW_DVC_IDENTITY_PROJECTION_INTEGRATION = PASS
P4_REAL_QLIB_RECORDER_MECHANISM = PASS_SYNTHETIC_FIXTURE
P4_REAL_MLFLOW_RUN_MECHANISM = PASS_SYNTHETIC_FIXTURE
P4_DVC_IDENTITY_PROJECTION = PASS
P4_UPSTREAM_IDENTITY_PROJECTION_V1 = MATERIALIZED
P4_FINANCIAL_DECAY_POLICY = NOT_IMPLEMENTED
P4_LIFECYCLE_POLICY = NOT_IMPLEMENTED
CURRENT_NEXT = P4_UPSTREAM_COMPONENTS_INTEGRATION_AND_OWNERSHIP_REAUDIT_001
```

This task proves only immutable identity linkage across the upstream owners. It
does not create lifecycle or financial-decay meaning and it is not Candidate,
Shadow, Champion, or certification evidence.

## Ownership

```text
QLIB_RECORDER = UPSTREAM_WHOLE
MLFLOW = UPSTREAM_LEAF_FOR_EXPERIMENT_RUN_ARTIFACT_IDENTITY
DVC = UPSTREAM_LEAF_FOR_REPRODUCIBILITY
FROUROS_ADWIN = UPSTREAM_LEAF_FOR_CHANGE_DETECTION
AQ_ROLE = THIN_IDENTITY_PROJECTION_AND_CROSS_UPSTREAM_CONSISTENCY_CHECK_ONLY
AQ_EXPERIMENT_REGISTRY = NO
AQ_MODEL_REGISTRY = NO
AQ_ARTIFACT_STORE = NO
AQ_STATE_DATABASE = NO
AQ_IDENTITY_DATABASE = NO
AQ_GENERIC_IDENTITY_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

`UpstreamIdentityProjectionV1` is one closed, immutable evidence document. It
binds the Qlib Recorder and backing MLflow run/artifact identities, exact
MetricObservationStreamV1 and DetectorEvidenceV1 bytes, and the frozen Frouros
runtime identities. It is not a registry or database record.

## Real upstream fixture run

The mechanism proof used public Qlib Recorder and MLflow APIs with private
tracking state under
`D:/AQ_DATA/P4/qlib-mlflow-dvc-identity-projection-integration-001/`.
The input was the already-frozen deterministic synthetic RankIC case; no model
was trained, no prediction was generated, and RankIC was not recalculated from
predictions or labels.

```text
FIXTURE_CLASSIFICATION = TEST_FIXTURE_NOT_REAL_RESEARCH
QLIB_VERSION = 0.9.8.dev26
MLFLOW_VERSION = 3.16.0
QLIB_EXPERIMENT_ID = 1
QLIB_RECORDER_ID = 5cc4123dd93f454383652330544eba26
QLIB_RECORDER_STATUS = FINISHED
MLFLOW_EXPERIMENT_ID = 1
MLFLOW_RUN_ID = 5cc4123dd93f454383652330544eba26
MLFLOW_RUN_STATUS = FINISHED
QLIB_MLFLOW_IDENTITY_MATCH = PASS
QLIB_ARTIFACT_LOGICAL_PATH = sig_analysis/ric.pkl
QLIB_RIC_ARTIFACT_SHA256 = badf9786036f7426f09aa65ba48de925c2e8cd76065e4bb7b2dcf3acf96ee299
QLIB_RIC_ARTIFACT_CONTENT_MATCH = PASS
```

The unchanged thin adapter produced:

```text
METRIC_OBSERVATION_STREAM_SHA256 = 7e306e6bb68f4a325c4ae1d5c695f9d5417d7073502e31a20671a9fea617882a
DETECTOR_EVIDENCE_SHA256 = 6a7d146093e2412914e9db2957024b334b30b361eca9f179389465d8026bb062
FIRST_CHANGE_INDEX = 1247
FROUROS_VERSION = 0.9.0
FROUROS_IDENTITY_BINDING = PASS
UPSTREAM_IDENTITY_PROJECTION_SHA256 = 8b7fdf79d5b5d5805cefdc94488bb0ba4b408331daa0578f86676b22585e5725
```

## DVC reproducibility identity

One bounded upstream DVC stage validates the frozen identity chain and emits
one small seal. The first reproduction succeeded and the immediate second run
reported unchanged data and pipelines. Existing DVC stage definitions and
lock-entry semantics remain unchanged; DVC 3.67.1 reserialized the lock file
while adding the new entry.

```text
DVC_VERSION = 3.67.1
DVC_STAGE_NAME = p4_frouros_identity_projection
DVC_REPRO_1 = PASS
DVC_REPRO_2 = UNCHANGED_DATA_AND_PIPELINES_UP_TO_DATE
DVC_YAML_SHA256 = f15c791b1c868fcb6368673fbcb8dc1ed97a03a7db4abd5ea9dcb152e4bbf74f
DVC_LOCK_SHA256 = e0ea749bf921e2bdc0ac9c16cf20baa0ad5f63ee3708f78f13960135e139eae5
DVC_STAGE_LOCK_ENTRY_IDENTITY = sha256:9c8fd01b2cd3000c92fb04043ad16c70cb70d4acc3bb285a9614d4038fbcdfe9
DVC_SEAL_OUTPUT_SHA256 = 3397523b2d1e2fcd1e7d2ddde999855ef7252d1b6cac15fea8ebf45230c4c7ab
DVC_SEAL_OUTPUT_HASH = md5:174e2c65d907d69e8cdc072c0eaccdf9
DVC_IDENTITY_BINDING = PASS
CIRCULAR_HASH_DEPENDENCY = NO
```

The layering is deliberately acyclic: upstream run/artifact and Frouros
evidence form the projection; the DVC stage then validates that projection and
emits a seal that references its SHA-256.

## Validation and safety

```text
IDENTITY_PROJECTION_TESTS = 14/14 PASS
QLIB_EXPORTER_TESTS = 11/11 PASS
FROUROS_RUNNER_TESTS = 8/8 PASS
FULL_CROSS_RUNTIME_TESTS = 1/1 PASS
NEGATIVE_TESTS = PASS
DVC_STAGE_PARSE = PASS
DVC_DAG = PASS
DVC_STATUS = DATA_AND_PIPELINES_UP_TO_DATE
QLIB_ENV_PACKAGE_MUTATION = NO
FROUROS_ENV_PACKAGE_MUTATION = NO
DVC_ENV_PACKAGE_MUTATION = NO
REAL_ALPHAGEN_CANDIDATE_ARTIFACTS_ACCESSED = NO
HISTORICAL_TEST_ACCESSED = NO
SEALED_OOS_ACCESSED = NO
MODEL_TRAINING = NO
PREDICTION = NO
BACKTEST = NO
```

Fail-closed tests cover non-FINISHED runs, Qlib/MLflow run and experiment ID
mismatches, wrong artifact bytes or path, broken observation/detector hashes,
wrong Frouros identities, tampered projection/dependency bytes, and unsupported
metrics.

## Private evidence

```text
PRIVATE_REPORT = D:/AQ_DATA/P4/qlib-mlflow-dvc-identity-projection-integration-001/integration_summary.json
PRIVATE_REPORT_SHA256 = 4e6468a8466783b9cacf6e5f383e7a85cecf510876dd1e5e8acc86287d2ac5dd
```

## Next

```text
CURRENT_NEXT = P4_UPSTREAM_COMPONENTS_INTEGRATION_AND_OWNERSHIP_REAUDIT_001
```

The next task must audit the completed Qlib, MLflow, DVC, Frouros, thin-adapter,
and identity-projection ownership stack before any residual lifecycle or decay
policy is implemented.
