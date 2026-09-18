# P4 Frouros Thin Evidence Adapter 001

## Decision

```text
P4_FROUROS_THIN_EVIDENCE_ADAPTER = PASS
P4_FROUROS_SUPPORTED_METRIC = RANK_IC_ONLY
P4_FROUROS_TRANSLATION = PLUS_1_CONSTANT_OFFSET
P4_FROUROS_DETECTOR_EVIDENCE = MATERIALIZED
P4_FROUROS_STATE_AUTHORITY = REPLAY_FROM_IMMUTABLE_OBSERVATIONS
P4_FINANCIAL_DECAY_POLICY = NOT_IMPLEMENTED
P4_LIFECYCLE_POLICY = NOT_IMPLEMENTED
CURRENT_NEXT = P4_QLIB_MLFLOW_DVC_IDENTITY_PROJECTION_INTEGRATION_001
```

This task adds only the bounded evidence seam selected by the prior P4 audit.
It neither calculates RankIC nor implements drift mathematics, financial decay
meaning, lifecycle decisions, scheduling, a workflow engine, or a state
database.

## Ownership

```text
QLIB_SIGANA_METRIC_COMPUTATION = UPSTREAM_WHOLE
FROUROS_ADWIN_CHANGE_DETECTION = UPSTREAM_LEAF
AQ_ROLE = BOUNDED_EVIDENCE_VALIDATION_AND_TRANSLATION_ONLY
AQ_METRIC_ENGINE = NO
AQ_DRIFT_ENGINE = NO
AQ_POLICY_ENGINE = NO
AQ_WORKFLOW_ENGINE = NO
AQ_STATE_DATABASE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

Pinned Qlib `SigAnaRecord` calls upstream `calc_ic`, then stores the resulting
per-session pandas Series as `sig_analysis/ric.pkl`. The Qlib-side exporter
loads only an explicitly supplied artifact with that filename. It requires a
non-empty numeric Series on a unique, strictly increasing `DatetimeIndex`, and
rejects non-finite or out-of-domain observations. It does not discover a
Recorder or reconstruct RankIC from predictions and labels.

## Closed contracts

The Qlib runtime emits `MetricObservationStreamV1` with exactly one supported
metric, `RANK_IC`, the source pickle SHA-256, the fixed source-format identity,
and ordered time/value observations. Pydantic validates the exporter model and
the tracked JSON Schema closes the cross-runtime contract.

The Frouros runtime verifies the exact observation-file byte hash and the
closed contract before replay. It applies only:

```text
translation_kind = CONSTANT_ADDITIVE_OFFSET
translation_constant = 1.0
original_domain = [-1.0, 1.0]
translated_domain = [0.0, 2.0]
```

It then constructs public `ADWINConfig` and `ADWIN` from Frouros `0.9.0` with:

```text
clock = 32
delta = 0.002
m = 5
min_window_size = 5
min_num_instances = 10
```

`DetectorEvidenceV1` records the source stream identity, observation extent,
translation provenance, detector/version/module/runtime identities, complete
configuration, and statistical change indices. It does not emit HEALTHY,
DEGRADED, Champion, retirement, promotion, or Research Request semantics.

Both JSON artifacts use deterministic sorted compact JSON plus one terminal
newline and are hashed as exact bytes. This is deliberately not represented as
RFC 8785 semantic-canonical identity. Both writers are write-once. Detector
state authority is the complete ordered immutable stream plus pinned runtime,
configuration, and translation; pickle is not durable authority.

## Environment boundary

```text
QLIB_SIDE = /home/zhou/miniforge3/envs/rdagent4qlib/bin/python
FROUROS_SIDE = /home/zhou/AQ_ENVS/p4-frouros-adwin/bin/python
FROUROS_ENV_PACKAGE_MUTATION = NO
QLIB_ENV_PACKAGE_MUTATION = NO
FROUROS_RUNTIME_FREEZE_SHA256 = 8c66ad3fde0f116d89aa31c0454a093eba00b16fe6d5946ac973bd5850dfb5d5
INSTALLED_ADWIN_MODULE_SHA256 = f3b2c06acf88b6938eac907909ca16b8daa382133eb1247e297a12f299ebd8fd
```

No Frouros package entered the Qlib environment and no pandas/Qlib package
entered the Frouros environment. The seam is an immutable JSON file, not a
generic subprocess, RPC, or service framework.

## Validation

Synthetic fixtures used the exact frozen seed and five prior POC shapes,
serialized as genuine pandas Series pickles. Full-path results were:

| Case | First change index |
| --- | ---: |
| stable positive to near zero | `1247` |
| stable positive to sign reversal | `1119` |
| stable noisy no-change | none |
| gradual deterioration | `1823` |
| temporary shock/recovery | none |

```text
QLIB_EXPORTER_TESTS = 11/11 PASS
FROUROS_RUNNER_TESTS = 8/8 PASS
FULL_CROSS_RUNTIME_PARITY_TEST = 1/1 PASS
FULL_ADAPTER_POC_PARITY = PASS
DETERMINISTIC_REPLAY = PASS
FRESH_ADWIN_INSTANCES_PER_CASE = 2
FAIL_CLOSED_NEGATIVE_TESTS = PASS
```

Negative coverage includes wrong objects, empty artifacts, NaN and infinities,
RankIC outside `[-1, 1]`, duplicate or unordered timestamps, non-numeric data,
unsupported metrics and translations, tampered stream hashes, and wrong
Frouros version, runtime-freeze, or module identities.

```text
QLIB_MODEL_TRAINING = NO
QLIB_PREDICTION = NO
REAL_QLIB_METRIC_RECOMPUTATION = NO
HISTORICAL_TEST_ACCESSED = NO
SEALED_OOS_ACCESSED = NO
FINANCIAL_DECAY_DECISION = NOT_IMPLEMENTED
LIFECYCLE_STATE_POLICY = NOT_IMPLEMENTED
CHAMPION_PROMOTION = NOT_IMPLEMENTED
RESEARCH_REQUEST = NOT_IMPLEMENTED
```

## Private evidence

The required ten reports and the replay fixtures are stored privately under:

```text
PRIVATE_REPORT = D:/AQ_DATA/P4/frouros-thin-evidence-adapter-001/adapter_summary.json
PRIVATE_REPORT_SHA256 = 3d7d34141e7c5b2ffa9afab3e0e15b03d057ac4aaa457d432ba2287894774592
```

## Next

```text
FULL_UPSTREAM_IDENTITY_PROJECTION = DEFERRED_TO_NEXT_TASK
CURRENT_NEXT = P4_QLIB_MLFLOW_DVC_IDENTITY_PROJECTION_INTEGRATION_001
```

The next task may bind the two new exact-byte evidence identities to real Qlib
Recorder, MLflow experiment/run/artifact, and DVC reproducibility identities.
It may not alter detector behavior or introduce financial/lifecycle policy.
