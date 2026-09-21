# P5 post-build readiness and evaluation authority freeze 001

## Scope and current state

This authority audit starts from main
`8d9d73e6f585639c6d3c91675472c258adbb2637` while the independent P5
historical fundamentals build remains active. It performs no build closeout,
SEC request, model fit, prediction, backtest, performance inspection, package
change, P6 deployment, or P2 V2 sealed-OOS access.

```text
CURRENT_PHASE = P5_FUNDAMENTAL_INTELLIGENCE
P5_COMPLETE = NO
P6_ACTIVE = NO
P6_PHASE_ENTRY_AUTHORIZED = NO
HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
HISTORICAL_BUILD_INTERFERENCE = NO
```

Microsoft Qlib remains the whole evaluation/model capability owner. AQ owns
only the vehicle-selection authority, immutable configuration identity,
two-trial binding, and interpretation policy.

## Existing evaluation-authority audit

The audit used only already-present project authorities and did not inspect
their historical performance to select a model.

| Existing authority | Technical fit | Decision |
|---|---|---|
| P1 LightGBM Alpha158 exploratory reference | Exercised and Qlib-native, but introduces a more complex nonlinear model and many fixed hyperparameters into a feature-value ablation. | Rejected for this role on ex-ante confounding/minimality grounds, not performance. |
| P1 Linear OLS Alpha158 recipe | Exercised, Qlib-native, deterministic, dependency-complete, and already identity-sealed. | Strongest vehicle candidate, subject to processor semantics. |
| P2 Formulaic Alpha statistical control | Reuses the same `LinearModel(estimator=ols)` and canonical configuration identity as a frozen control. | Corroborates model-class/config reuse. |
| P3 AlphaGen candidate evaluation vehicle | Reuses the same OLS class, TRAIN-only fit policy, processors, and Qlib Recorder path. | Corroborates operational reuse, but its dense/single-candidate features do not resolve sparse P5 event semantics. |

```text
MODEL_AUTHORITIES_AUDITED = 4
P5_MODEL_SELECTION_REASON = DETERMINISTIC_UPSTREAM_QLIB_NATIVE_PREVIOUSLY_EXERCISED_MINIMUM_CONFOUNDING_NO_MODEL_SEARCH
```

The preferred model class itself passes the engineering criteria. The exact
existing model-plus-handler composition does not pass the required sparse
feature semantics gate, so this task does not activate a P5 evaluation model.

## Runtime and configuration identity

The pinned Qlib source worktree is clean at the required identity. Runtime
inspection imported Qlib only; it did not initialize data, fit a model, or
create a Recorder.

```text
UPSTREAM_OWNER = MICROSOFT_QLIB
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_RUNTIME_PYTHON = 3.10.21
UPSTREAM_CONFIG_PATH = examples/benchmarks/Linear/workflow_config_linear_Alpha158.yaml
UPSTREAM_SOURCE_CONFIG_SHA256 = 68e12ae7aa88ee9749b181f4e76a27786d64fc36805370a8da6c21a0dd015b36
ADAPTED_CONFIG_PATH = 30-research-system/qlib/model-comparison/workflow_config_linear_Alpha158_US.yaml
UPSTREAM_CONFIG_SHA256 = b9a92537a9737ce909284e77e583ad20c0a3d2b18f795271d85db6c5ba5eafc1
CONFIG_HASH_SEMANTICS = EXISTING_PROJECT_AUTHORITY_CANONICAL_LF_SHA256
```

The expected `b9a925...` identity is the existing project's canonical-LF hash
of the US-adapted full Linear workflow configuration. The pinned upstream file
itself has the separately recorded `68e12a...` byte identity. These identities
must not be conflated.

## Exact audited model composition

```text
MODEL_CLASS = qlib.contrib.model.linear.LinearModel
MODEL_KWARGS = estimator=ols; alpha=0.0; fit_intercept=false; include_valid=false
AUDITED_RECIPE_DATA_HANDLER_CLASS = qlib.contrib.data.handler.Alpha158
P5_FUTURE_HANDOFF_CLASSES = qlib.data.dataset.loader.StaticDataLoader -> qlib.data.dataset.handler.DataHandlerLP -> qlib.data.dataset.DatasetH
LABEL_EXPRESSION = Ref($close, -2)/Ref($close, -1) - 1
INFER_PROCESSORS = RobustZScoreNorm(fields_group=feature,clip_outlier=true) -> Fillna(fields_group=feature,fill_value=0)
LEARN_PROCESSORS = DropnaLabel(fields_group=label) -> CSRankNorm(fields_group=label)
DATAHANDLER_PROCESS_TYPE = append
FIT_POLICY = TRAIN_ONLY
RANDOM_SEED_POLICY = NOT_APPLICABLE_DETERMINISTIC_OLS; INPUT_ORDER_AND_CONFIG_MUST_BE_FROZEN
RECORDER_OWNER = MICROSOFT_QLIB_RECORDER_PLUS_MLFLOW
```

The kwargs above resolve hidden class defaults from the pinned source, not
only the single `estimator` value written in YAML. `include_valid=false`
establishes TRAIN-only fitting.

## Processor-semantics gate

The gate fails closed. In Qlib source `2fb9380...`:

1. `DataHandlerLP` defaults to append processing, so inference processors are
   applied before learning processors and therefore affect both inference and
   learning data.
2. `RobustZScoreNorm(fields_group=feature)` selects every column in the
   `feature` group, which would include the five externally supplied P5
   columns unless a new field-group policy were designed.
3. `Fillna(fields_group=feature)` defaults to `fill_value=0` and executes
   `df[feature] = df[feature].fillna(0)`.
4. The frozen P5 design requires non-event, exclusion, and unavailable cells
   to remain null and keeps legitimate numeric zero distinct from missingness.
5. Removing `Fillna` without another frozen policy is not sufficient:
   `LinearModel.fit()` calls `df_train.dropna()`, which would cause the sparse
   challenger to drop rows that the control retains.

Consequently the existing recipe would either erase point-event missingness
by converting null to zero or produce a different effective row population.
Either outcome breaks the byte/config-identical two-trial comparison. This
task is not authorized to introduce a new processor, mask, imputer, handler,
or alternative model.

```text
PROCESSOR_SEMANTICS_GATE = BLOCKED
EVALUATION_MODEL_AUTHORITY = BLOCKED_PROCESSOR_SEMANTICS
P5_EVALUATION_MODEL = UNFROZEN_BLOCKED
P5_EVALUATION_MODEL_CANDIDATE = qlib.contrib.model.linear.LinearModel(estimator=ols)
P5_EVALUATION_MODEL_ROLE = FIXED_FEATURE_ABLATION_VEHICLE_CANDIDATE_NOT_ACTIVATED
DATA_HANDLER_CLASS = UNFROZEN; AUDITED_RECIPE=qlib.contrib.data.handler.Alpha158; P5_HANDOFF=qlib.data.dataset.handler.DataHandlerLP
```

This is a blocker in the evaluation authority, not a failure of Qlib or the
historical fundamentals build.

## Frozen two-trial boundary

The already-preregistered inventory remains exactly two trials even though
execution authority is blocked:

```text
TRIAL_COUNT = 2
CONTROL = EXISTING_APPROVED_BASELINE_FEATURE_SURFACE
CHALLENGER = SAME_EXACT_BASELINE_PLUS_EXACTLY_FIVE_P5_FILING_FEATURE_COLUMNS
```

The five challenger additions, in frozen order, are:

1. `p5_filing_lag_days_v1`
2. `p5_accepted_after_market_close_v1`
3. `p5_is_amendment_v1`
4. `p5_press_release_exhibit_present_v1`
5. `p5_authorized_exhibit_count_v1`

Model, label, processors, segments, seed policy, strategy, costs, runtime, row
population, and prediction semantics must be identical between trials. There
is no leave-one-out run, model comparison, feature subset search, or
hyperparameter search.

The frozen historical research windows remain:

```text
TRAIN = 2015-04-01 through 2019-12-31
VALIDATION = 2020-01-01 through 2021-12-31
P5_HISTORICAL_RESEARCH_TEST = 2022-01-03 through 2024-12-31
P2_V2_SEALED_OOS_ACCESSED = NO
```

## Historical-build terminal-closeout checklist

This checklist is authority for a later terminal-closeout task. None of its
checks is executed here. The accounting base is:

```text
SELECTIVE_DISCOVERED_ACCESSION_COUNT = 36206
SOURCE_VERIFIABLE_REQUIRED_ACCESSION_COUNT = 36204
SOURCE_UNAVAILABLE_ACCESSION_COUNT = 2
GLOBAL_ACCESSION_TARGET = 36206
SOURCE_VERIFIABLE_TARGET = 36204
SOURCE_UNAVAILABLE_TARGET = 2
GLOBAL_ACCESSION_RECONCILIATION = 36204 + 2 = 36206
```

The two source-unavailable accessions remain a separate explicit ledger. They
must never be turned into fake evidence or silently included in the
source-verifiable terminal denominator.

The later closeout has exactly 26 gates:

### Global and terminal accounting — gates 1 through 5

1. `36204 + 2 = 36206` reconciles exactly.
2. Every one of the 36,204 source-verifiable accessions appears in exactly one
   of: `COMPLETE_WITH_EVIDENCE`, `COMPLETE_NO_AUTHORIZED_FACTS`,
   `COMPLETE_NO_STRUCTURED_FINANCIALS`,
   `SKIPPED_OUTSIDE_AUTHORIZED_HISTORY`, `FAILED_TRANSIENT`,
   `FAILED_DETERMINISTIC`, or `FAILED_REQUIRED_ACCESSION`.
3. `UNACCOUNTED_GLOBAL_ACCESSION_COUNT = 0`.
4. `FAILED_REQUIRED_ACCESSION_COUNT = 0`.
5. `DUPLICATE_GLOBAL_ACCOUNTING_COUNT = 0`.

### Evidence integrity — gates 6 through 12

6. `DUPLICATE_EVIDENCE_ID_COUNT = 0`.
7. `EARLY_VISIBILITY_COUNT = 0`.
8. `CROSS_CIK_CONTAMINATION_COUNT = 0`.
9. `PERIOD_CLASS_MIXING_FAILURE_COUNT = 0`.
10. `SOURCE_HASH_MISMATCH_COUNT = 0`.
11. `FAKE_SOURCE_HASH_COUNT = 0`.
12. `SOURCE_UNAVAILABLE_FAKE_EVIDENCE_COUNT = 0`.

### Checkpoint replay and resume — gates 13 through 16

13. `REUSABLE_ACCESSION_COUNT` equals every eligible completed accession.
14. `REPROCESSED_ACCESSION_COUNT = 0`.
15. `REPLAY_NETWORK_BYTES = 0`.
16. `OFFLINE_DERIVED_EVIDENCE_REPLAY = PASS`.

### Storage and cache — gates 17 through 20

17. `CACHE_CEILING_BREACH_COUNT = 0`.
18. Ordinary transient source assets are evicted after valid seal.
19. Persistent outputs remain within the frozen storage budget.
20. No full SEC submission mirror or accidental full-corpus cache is retained.

### DVC and artifact seal — gates 21 through 25

21. `DVC_SEAL = PASS`.
22. `OUTPUT_HASH_MATCH = YES`.
23. `BUILD_SPEC_IDENTITY_MATCH = YES`.
24. `EXECUTION_INVENTORY_IDENTITY_MATCH = YES`.
25. `SOURCE_UNAVAILABLE_LEDGER_IDENTITY_MATCH = YES`.

### Qlib handoff — gate 26

26. The complete historical Parquet/DataFrame passes
    `StaticDataLoader -> DataHandlerLP -> DatasetH` with
    `QLIB_FULL_HISTORICAL_HANDOFF = PASS`, without training or prediction.

```text
TERMINAL_CLOSEOUT_GATE_COUNT = 26
QLIB_FULL_HISTORICAL_HANDOFF_REQUIRED = YES
```

Only all 26 passing may authorize a later closeout to set:

```text
P5_HISTORICAL_DATASET_BUILT = YES
P5_EDGARTOOLS_NATIVE_HISTORICAL_INGESTION_MODE = ONE_TIME_HISTORICAL_BACKFILL_PLUS_IMMUTABLE_POINT_IN_TIME_VINTAGES
```

Any failure remains fail-closed and cannot be repaired by inventing a new
engine during closeout.

## Post-build hygiene review queue

The existing build-specific candidates remain untouched:

1. `_NetworkMeter` / `httpx.Client.send` monkey patch;
2. `_install_transient_native_cache` / attachment content override.

After terminal closeout, each must be classified exactly once as
`KEEP_BUILD_SPECIFIC_AUDIT_GLUE`, `REPLACE_WITH_EDGARTOOLS_NATIVE`, or
`RETIRE_AFTER_BUILD`.

```text
POST_BUILD_HYGIENE_CANDIDATE_COUNT = 2
AQ_GENERIC_CACHE_ENGINE = NO
AQ_GENERIC_NETWORK_ENGINE = NO
```

## Next authority task

The historical build and its later terminal closeout remain independent. The
new evaluation blocker can be resolved without reading or mutating that build,
but no replacement policy is designed here.

```text
CURRENT_DEVELOPMENT_NEXT = P5_FILING_FEATURE_PROCESSOR_SEMANTICS_AUTHORITY_RESOLUTION_001
P5_HISTORICAL_DATA_PATH_NEXT = P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_001
P5_HISTORICAL_DATA_PATH_GATE = WAITING_FOR_P5_HISTORICAL_FUNDAMENTALS_BUILD_TERMINAL_CLOSEOUT
```

## Non-actions and validation

```text
NEW_PRODUCTION_LOC = 0
AQ_MODEL_ENGINE = NO
AQ_TRAINING_ENGINE = NO
AQ_BACKTEST_ENGINE = NO
AQ_TERMINAL_CLOSEOUT_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
SEC_DATA_REQUEST_COUNT = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
P6_ACTIVE = NO
TEST_RESULT = PASS
DIFF_CHECK = PASS
FINAL_CLASSIFICATION = PASS_CLOSEOUT_READINESS_FROZEN_EVALUATION_AUTHORITY_BLOCKED_PROCESSOR_SEMANTICS
```
