# P5 evaluation reproducibility and control-surface authority closeout 001

## Scope and outcome

This closeout starts from main
`8d9d73e6f585639c6d3c91675472c258adbb2637` and branch head
`d009b6d827f259e8bca7efc4ad47af5ee5e1851e`. It closes only the
reproducibility, CONTROL-surface, and P5 phase-exit coverage authorities for
the already-selected Qlib LightGBM evaluation vehicle. It uses pinned source,
repository authority, and two bounded synthetic fits. It does not inspect
performance, read project data, run a project fit or prediction, backtest,
access P2 V2 sealed OOS, contact SEC, or interfere with the independent
historical build.

```text
EVALUATION_MODEL_AUTHORITY = qlib.contrib.model.gbdt.LGBModel
PROCESSOR_SEMANTICS_GATE = PASS
REPRODUCIBILITY_GATE = PASS
CONTROL_SURFACE_GATE = PASS
P5_EXIT_COVERAGE_GATE = PASS_AUTHORITY_FROZEN_EXECUTION_PENDING
LINEAR_OLS_NULL_PRESERVING_COMPATIBLE = NO
```

The Linear OLS rejection remains unchanged.

## LightGBM 4.7.0 reproducibility authority

Official LightGBM 4.7.0 parameter authority states that `deterministic=true`
is a CPU-only reproducibility control and recommends forcing either column-
wise or row-wise histogram construction to avoid numerical instability. It
also establishes that `seed` has lower priority than explicitly supplied
component seeds and that `feature_fraction_seed` owns feature-fraction
sampling. The existing Qlib recipe and model hyperparameters are preserved;
only hidden reproducibility controls become explicit.

```text
device_type = cpu
deterministic = true
force_col_wise = true
force_row_wise = false
num_threads = 8

seed = 20260913
data_random_seed = 1
feature_fraction_seed = 2
bagging_seed = 3
drop_seed = 4
objective_seed = 5
extra_seed = 6

INPUT_ROW_ORDER = datetime ASC, episode_id ASC
INPUT_COLUMN_ORDER = FROZEN_BY_SURFACE_MANIFEST
RUNTIME_IDENTITY = QLIB_0.9.8.dev26_SOURCE_2fb9380..._LIGHTGBM_4.7.0_CPU
```

All other recipe values remain frozen, including:

```text
loss = mse
colsample_bytree = 0.8879
learning_rate = 0.2
subsample = 0.8789
lambda_l1 = 205.6999
lambda_l2 = 580.9768
max_depth = 8
num_leaves = 210
early_stopping_rounds = 50
num_boost_round = 1000
use_missing = true
zero_as_missing = false
bagging_freq = 0
```

### Synthetic repeatability proof

The proof used an in-memory fixture only: 12,000 deterministically ordered
rows, 162 ordered numeric columns, 7% deterministic NaN placement, 9,000
training rows, and 3,000 validation rows. The 162-column width represents the
frozen 157-column CONTROL width plus the largest authorized five-column
filing-feature increment. The same arrays and exact parameter object were
passed to native LightGBM 4.7.0 twice in the same pinned Python 3.10.21
runtime.

```text
SYNTHETIC_FIT_COUNT = 2
PROJECT_MODEL_TRAINING_COUNT = 0
PROJECT_PREDICTION_COUNT = 0
PROJECT_BACKTEST_COUNT = 0

RUN_1_MODEL_STRUCTURE_SHA256 = 2922239ec93cffe7c47d8a9e85cdab4c42647b71abc44b59a2af99e9a1bec18c
RUN_2_MODEL_STRUCTURE_SHA256 = 2922239ec93cffe7c47d8a9e85cdab4c42647b71abc44b59a2af99e9a1bec18c
REPEATED_MODEL_STRUCTURE_HASH_MATCH = YES

RUN_1_PREDICTION_SHA256 = d86ab87280c351cb82d8ea73f4f0647b4238ff09b4a9046f92ba2cee5b98a8ed
RUN_2_PREDICTION_SHA256 = d86ab87280c351cb82d8ea73f4f0647b4238ff09b4a9046f92ba2cee5b98a8ed
REPEATED_PREDICTION_BYTES_MATCH = YES
SYNTHETIC_REPRODUCIBILITY_POC = PASS
```

At eight threads, two validation reductions differed by at most
`1.7763568394002505e-15`; their callback-observed best-iteration counters were
174 and 175. This did not change the serialized model structure or one byte of
the predictions. A diagnostic one-thread run also made the metric trace and
best-iteration counter exact, but changing the frozen recipe to one thread is
not justified by either required repeatability output. The paired evaluation
therefore retains the existing fixed eight-thread resource policy and treats
the serialized model and prediction bytes as the repeatability outputs.

## Feature-subsampling compatibility

`colsample_bytree=0.8879` is preserved. Both sides of each directional
hypothesis use the same recipe, ordered feature manifest, and explicit
`feature_fraction_seed=2`. Adding columns is the preregistered treatment: the
native model's response to the larger feature universe is part of the effect
being tested. Forcing `colsample_bytree=1.0` would instead create a P5-specific
recipe change solely to neutralize intended treatment mechanics.

```text
FEATURE_SUBSAMPLING_ABLATION_COMPATIBILITY = PASS
COLSAMPLE_BYTREE_CHANGED = NO
P5_SPECIFIC_LIGHTGBM_RECIPE_CREATED = NO
```

## Exact CONTROL feature surface

The old P1 native-baseline YAML is not the P5 CONTROL identity. Its static
`market: sp500` authority and its 158-column Alpha158 surface include `VWAP0`,
which cannot be requested from the authoritative P2 ragged OHLCV provider.
The current P2-native `RaggedAlpha158` class is the already-approved,
episode-compatible surface. It invokes upstream `Alpha158DL` with K-bar,
`OPEN0`, `HIGH0`, `LOW0`, and rolling OHLCV families while omitting only
`VWAP0`.

```text
CONTROL_FEATURE_FAMILY = P2_RAGGED_ALPHA158_OHLCV_157
CONTROL_FEATURE_COLUMN_COUNT = 157
CONTROL_FEATURE_CONFIG = 30-research-system/qlib/dataset-adapter/aq_qlib_handoff/qlib_config.py
CONTROL_FEATURE_CONFIG_SHA256 = bbec91c3eb8b79e6e01c202310d52a1f1bc5fe5b1e0af13fb9f7dc7fba315b92
OLD_STATIC_ALPHA158_CONTROL_REUSED = NO
OLD_ONLY_FEATURE = VWAP0:$vwap/$close
```

The exact ordered column list is:

```text
KMID,KLEN,KMID2,KUP,KUP2,KLOW,KLOW2,KSFT,KSFT2,OPEN0,HIGH0,LOW0,
ROC5,ROC10,ROC20,ROC30,ROC60,MA5,MA10,MA20,MA30,MA60,
STD5,STD10,STD20,STD30,STD60,BETA5,BETA10,BETA20,BETA30,BETA60,
RSQR5,RSQR10,RSQR20,RSQR30,RSQR60,RESI5,RESI10,RESI20,RESI30,RESI60,
MAX5,MAX10,MAX20,MAX30,MAX60,MIN5,MIN10,MIN20,MIN30,MIN60,
QTLU5,QTLU10,QTLU20,QTLU30,QTLU60,QTLD5,QTLD10,QTLD20,QTLD30,QTLD60,
RANK5,RANK10,RANK20,RANK30,RANK60,RSV5,RSV10,RSV20,RSV30,RSV60,
IMAX5,IMAX10,IMAX20,IMAX30,IMAX60,IMIN5,IMIN10,IMIN20,IMIN30,IMIN60,
IMXD5,IMXD10,IMXD20,IMXD30,IMXD60,CORR5,CORR10,CORR20,CORR30,CORR60,
CORD5,CORD10,CORD20,CORD30,CORD60,CNTP5,CNTP10,CNTP20,CNTP30,CNTP60,
CNTN5,CNTN10,CNTN20,CNTN30,CNTN60,CNTD5,CNTD10,CNTD20,CNTD30,CNTD60,
SUMP5,SUMP10,SUMP20,SUMP30,SUMP60,SUMN5,SUMN10,SUMN20,SUMN30,SUMN60,
SUMD5,SUMD10,SUMD20,SUMD30,SUMD60,VMA5,VMA10,VMA20,VMA30,VMA60,
VSTD5,VSTD10,VSTD20,VSTD30,VSTD60,WVMA5,WVMA10,WVMA20,WVMA30,WVMA60,
VSUMP5,VSUMP10,VSUMP20,VSUMP30,VSUMP60,VSUMN5,VSUMN10,VSUMN20,VSUMN30,VSUMN60,
VSUMD5,VSUMD10,VSUMD20,VSUMD30,VSUMD60
```

`CONTROL_FEATURE_MANIFEST` is the compact, UTF-8, lexicographically
key-sorted JSON object with keys `feature_family` and `columns`. Each column
object contains its one-based `position`, exact `name`, and exact upstream
Qlib `expression` returned by the frozen `RaggedAlpha158.get_feature_config()`.

```text
CONTROL_FEATURE_MANIFEST_SHA256 = 7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463
```

## Exact CONTROL dataset identity

CONTROL is a date-valid left projection onto the complete P1/P5
episode-session grid. `episode_id` is the logical instrument key; rows are
ordered by `(datetime ASC, episode_id ASC)`. The 111 frozen identity
exclusions remain in the denominator with structurally missing P5
fundamentals. No current-ticker, static-universe, successor-price, or
pre-observation forward-fill shortcut is permitted.

The canonical `P5_CONTROL_DATASET_IDENTITY_V1` bundle fixes:

| Component | Frozen identity |
|---|---|
| P1 universe | 832 episodes; DVC snapshot `177a98ec2e94e460e4dff3166b991fac.dir`; accepted-facts SHA-256 `c1745a22c17c3a8a35bf56f504c1d96398c787492dce54a60ac85801799a9f62` |
| P5 identity | 721 bound, 111 exclusions; evidence checksum SHA-256 `32cba10a8f50c2a2a7dc1c9480547272b6f9ef501c49ef4c2a644c711f53dcd5`; replay SHA-256 `faab5726a5792b3d15cb1150f409845614a1b9bf8e2664e668ab46a5b2fbfb65` |
| P2 price surface | `D:/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data`; DVC dependency `fcd742578d6d89a5673bc1a618fc676b.dir`; build-report SHA-256 `eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142` |
| Provider authority | 12-fact SHA-256 `3cd9b13a1424609120a4e069ac2cf9f9b9aa61e2df919aa48cf51eeac616bc69`; Quantiacs primary plus bounded SimFin secondary |
| P2 counts | 730 security instruments; 745 membership ranges; 1,267,963 member-session rows |
| Feature surface | 157 columns; manifest SHA-256 `7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463` |

The canonical bundle uses compact sorted-key JSON and hashes to:

```text
CONTROL_DATASET_IDENTITY = P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135
```

Future materialization must additionally seal the produced dataset bytes in
DVC before H1 may execute. This authority freezes the exact
inputs and projection semantics; it does not claim that the not-yet-built P5
evaluation surface already has a final artifact hash.

## Final P5 V1 scope and phase-exit coverage

The prior eleven-feature and mandatory filing-ablation authority is
`SUPERSEDED_PRE_EVALUATION`. No project model training, prediction, backtest,
H1/H2 execution, or performance inspection occurred before this contraction.

The exact ordered P5 V1 fundamental increment is:

```text
Revenue
NetIncome
Assets
Liabilities
CommonEquity
NetCashFromOperatingActivities
CashAndCashEquivalents
CurrentAssetsTotal
CurrentLiabilitiesTotal
LongTermDebt
```

```text
P5_V1_REQUIRED_FUNDAMENTAL_FEATURE_COUNT = 10
P5_V1_REQUIRED_FILING_DERIVED_FEATURE_COUNT = 0
STRUCTURED_FUNDAMENTALS_INCLUDED_IN_CONTROL = NO
P5_FILING_INTERFACE_CAPABILITY = PROVEN_UPSTREAM_AVAILABLE
SCIENTIFIC_SCOPE_CHANGE = PRE_EVALUATION_SCOPE_CONTRACTION
```

The final P5 V1 evaluation has exactly two surfaces and one required
directional hypothesis:

```text
P5_V1_EVALUATION_SURFACE_COUNT = 2
P5_EVALUATION_SURFACE_S0 = BASE_157
P5_EVALUATION_SURFACE_S1 = BASE_157_PLUS_EXACT_10_FUNDAMENTALS
S0_COLUMN_COUNT = 157
S1_COLUMN_COUNT = 167

P5_V1_REQUIRED_HYPOTHESIS_COUNT = 1
P5_H1 = S0_VS_S1
MULTIPLE_TESTING_FAMILY_SIZE = 1
```

`S2` and `H2` are `DEFERRED_OPTIONAL_EXTENSION`. The five filing-derived
features remain valid historical research ideas/contracts, but their mass
historical materialization and ablation are not P5 V1 completion blockers.
The historical S2/H2 preregistration remains traceable evidence and is not
silently executed.

```text
P5_H2_STATUS = DEFERRED_OPTIONAL_EXTENSION
```

The existing model and processor authority remains unchanged:

```text
EVALUATION_MODEL = qlib.contrib.model.gbdt.LGBModel
FEATURE_SHARED_PROCESSORS = []
FEATURE_INFER_PROCESSORS = []
FEATURE_LEARN_PROCESSORS = LABEL_ONLY
PRIMARY_PREDICTION_METRIC = QLIB_RANK_IC
H1_DIRECTION = S1_MINUS_S0
```

The historical research split remains:

```text
TRAIN = 2015-04-01 through 2019-12-31
VALIDATION = 2020-01-01 through 2021-12-31
P5_HISTORICAL_RESEARCH_TEST = 2022-01-03 through 2024-12-31
```

Qlib owns DatasetH, model fit, prediction, Recorder, signal analysis, and its
native research/backtest surfaces. skfolio and arch retain their previously
frozen temporal-robustness and confirmatory-statistics roles. AQ does not own
a training, evaluation, or multiple-testing engine, and no extra challenger
is added merely to make multiple testing nontrivial.

P5 V1 exits after one valid, leakage-free, reproducible H1 comparison using
the frozen Qlib vehicle and historical split. A complete admissible result is
classified as `INCREMENTAL_VALUE_SUPPORTED`,
`NO_MEASURABLE_INCREMENTAL_VALUE`, or `DEGRADED`; all three allow phase
completion. `INCONCLUSIVE` allows completion only for an explicitly accepted
upstream/data limitation that cannot reasonably be repaired under current
governance; otherwise it remains an execution blocker.

`P5_COMPLETE` means the preregistered question was answered with admissible
evidence, not that fundamentals outperformed. A negative result does not
authorize ratios, restored `ShortTermDebt`, restored filing features,
quarterly variants, model/hyperparameter changes, or another P5 dataset.

The structured-fundamental H1 evidence must report zero for:

```text
ACCEPTANCE_TIME_LEAKAGE_COUNT
REPORT_PERIOD_LEAKAGE_COUNT
AMENDMENT_BACKWARD_LEAKAGE_COUNT
CROSS_CIK_CONTAMINATION_COUNT
EPISODE_MEMBERSHIP_LEAKAGE_COUNT
CURRENT_TICKER_LEAKAGE_COUNT
SOURCE_UNAVAILABLE_SUBSTITUTION_COUNT
FUTURE_FILING_VISIBILITY_COUNT
```

Filing-feature-only gates are `NOT_APPLICABLE_TO_P5_V1_H1`; checks are not
manufactured for absent features.

The stopped filing-feature materialization remains diagnostic evidence only:

```text
ALL_FORM_POPULATION_CENSUS = DIAGNOSTIC_SUPERSEDED_PRE_EVALUATION
ALL_FORM_POPULATION_CENSUS_STATUS = DIAGNOSTIC_SUPERSEDED_PRE_EVALUATION
TOTAL_ADMITTED_FILING_ACCESSIONS = 826859
EVENT_FORM_ACCESSION_COUNT = 62371
PARTIAL_COMPLETED_ACCESSION_COUNT = 20000
PARTIAL_COMPLETED_OBSERVATION_COUNT = 100000
PARTIAL_OUTPUT_CLASSIFICATION = PARTIAL_ABORTED_SUPERSEDED_SCOPE
P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION = DEFERRED_OPTIONAL_P5_EXTENSION
FILING_FEATURE_HISTORICAL_MATERIALIZATION_STATUS = DEFERRED_OPTIONAL_P5_EXTENSION
```

It is not resumed, promoted, deleted, or added to P5 V1 DVC authority by this
scope freeze.

```text
PID403_ROLE = HISTORICAL_REFERENCE_ONLY
PID403_FAILURE_COUNT = 392
PID403_FAILURES_REQUIRE_REPAIR = NO

P5_V1_UNVERIFIABLE_ACCESSION_COUNT = 5
P5_V1_UNVERIFIABLE_ACCESSION_POLICY = EXCLUDED
REPAIR_REQUIRED = NO
HEURISTIC_SUBSTITUTION = NO

ShortTermDebt = RETIRED_FROM_P5_V1
SHORTTERMDEBT_RETIREMENT_REASON = UPSTREAM_SEMANTIC_AMBIGUITY
AQ_PATCH_REQUIRED = NO
UPSTREAM_PATCH_ALLOWED = NO
```

## H1 authority correction and attempt-002 boundary

Attempt-001 did not match the processor contract frozen before execution. It
used `DropnaLabel` but omitted `CSZScoreNorm(fields_group=label)`. Its outputs
remain immutable diagnostic evidence, but its undefined Rank IC and identical
return paths are ineligible for scientific classification.

```text
ATTEMPT_001_CLASSIFICATION = INVALID_IMPLEMENTATION_DEVIATION
ATTEMPT_001_PROCESSOR_AUTHORITY_MATCH = NO
ATTEMPT_001_MISSING_FROZEN_PROCESSOR = CSZScoreNorm(fields_group=label)
RERUN_REASON = RESTORE_PREEXISTING_FROZEN_PROCESSOR_AUTHORITY
RERUN_IS_PROTOCOL_CHANGE = NO
```

The corrected implementation uses `StaticDataLoader` and `DataHandlerLP` with
empty shared/infer processors and the exact label-only chain
`DropnaLabel -> CSZScoreNorm(label)`. Before either fit, Qlib public `DK_L` and
`DK_R` surfaces proved identical transformed labels, non-degenerate train and
validation labels, unchanged feature-NaN locations, and preserved valid zero
values for both S0 and S1.

```text
DVC_H1_STAGE = p5_h1_incremental_fundamental_evaluation
DVC_H1_REPRO_STATUS = FAIL_RESOURCE_OOM
S0_ROW_COUNT = 1196594
S1_ROW_COUNT = 1196594
S0_S1_ROW_IDENTITY_MATCH = YES
S0_COLUMN_COUNT = 157
S1_COLUMN_COUNT = 167
S0_LEARN_PROCESSOR_IDENTITY = DropnaLabel->CSZScoreNorm(label)
S1_LEARN_PROCESSOR_IDENTITY = DropnaLabel->CSZScoreNorm(label)
TRAIN_TRANSFORMED_LABEL_NON_NULL_COUNT = 572819
TRAIN_TRANSFORMED_LABEL_UNIQUE_COUNT = 567440
VALID_TRANSFORMED_LABEL_NON_NULL_COUNT = 247795
VALID_TRANSFORMED_LABEL_UNIQUE_COUNT = 246739
FEATURE_NAN_POSITIONS_PRESERVED = YES
VALID_FEATURE_ZERO_PRESERVED = YES
```

Attempt-002 ran from a clean separate output child. S0 fit exactly once and
completed with finite Rank IC. The S1 recorder then started and S1 fit was
invoked, but before completion the WSL kernel killed the Python process for global OOM
(`anon-rss=7,543,644 KiB`, `total-vm=16,287,820 KiB`). DVC surfaced exit code
15. No traceback, S1 prediction, S1 Rank IC, backtest, WalkForward, CPCV, SPA,
or RealityCheck output exists. Per the frozen no-retry rule, S0 is not reused
and no checkpoint/resume framework is introduced.

```text
ATTEMPT_002_CLASSIFICATION = INCONCLUSIVE_RESOURCE_OOM
S0_MODEL_FIT_COUNT = 1
S1_MODEL_FIT_COUNT = 1_INCOMPLETE_RESOURCE_OOM
S0_TEST_RANK_IC = 0.0021911029598144574
S1_TEST_RANK_IC = NOT_AVAILABLE_RESOURCE_OOM_BEFORE_FIT_COMPLETION
H1_TEST_RANK_IC_DELTA = NOT_AVAILABLE
WALKFORWARD_STATUS = NOT_RUN_PRIMARY_METRIC_PAIR_INCOMPLETE
CPCV_STATUS = NOT_RUN_PRIMARY_METRIC_PAIR_INCOMPLETE
SPA_STATUS = NOT_RUN_PRIMARY_METRIC_PAIR_INCOMPLETE
SPA_PVALUE = NOT_AVAILABLE
REALITYCHECK_STATUS = NOT_RUN_PRIMARY_METRIC_PAIR_INCOMPLETE
REALITYCHECK_PVALUE = NOT_AVAILABLE
H1_RESULT_CLASSIFICATION = INCONCLUSIVE
```

## Attempt-003 process-isolated boundary

After an owner-authorized WSL allocation increase, the resource gate passed
with approximately 10 GiB RAM and 4 GiB swap. Attempt-003 used independent
preflight, S0-fit, S1-fit, and composition processes under the one existing H1
DVC stage. Both fresh fits exited successfully, stayed below the new memory
boundary, and produced the complete finite primary metric pair. The two Qlib
backtests also completed.

The same single DVC execution then failed before the skfolio process began. The
WSL-to-Windows PowerShell invocation preserved escaped quote characters around
the virtual environment's base-interpreter path, so the Windows launcher
reported that the quoted Python path did not exist. This is a bounded runtime
entrypoint/orchestration failure, not a model, data, upstream semantics, or
resource failure. Per the frozen rule, no partial continuation or retry was
performed. The DVC command now uses the virtual-environment executables
directly through WSL interoperability; both direct entrypoints passed static
`--help` validation, but no further scientific execution is authorized here.

```text
RESOURCE_HEADROOM_STATUS = SUFFICIENT_FOR_PROCESS_ISOLATED_ATTEMPT
PROCESS_ISOLATION_IS_PROTOCOL_CHANGE = NO
ATTEMPT_003_AUTHORITY = PROCESS_ISOLATED_AUTHORITY_CORRECTED
ATTEMPT_003_EXECUTION_STATUS = FAIL_POST_PREDICTION_STATISTICS_ENTRYPOINT
ATTEMPT_003_S0_MAX_RSS_KIB = 6180492
ATTEMPT_003_S1_MAX_RSS_KIB = 7509472
ATTEMPT_003_S0_MODEL_FIT_COUNT = 1
ATTEMPT_003_S1_MODEL_FIT_COUNT = 1
ATTEMPT_003_S0_MODEL_FIT_COMPLETION_COUNT = 1
ATTEMPT_003_S1_MODEL_FIT_COMPLETION_COUNT = 1
ATTEMPT_003_S0_TEST_RANK_IC = 0.0021911029598144574
ATTEMPT_003_S1_TEST_RANK_IC = 0.004588185207288156
ATTEMPT_003_H1_TEST_RANK_IC_DELTA = 0.0023970822474736987
ATTEMPT_003_QLIB_BACKTEST_STATUS = PASS
WALKFORWARD_STATUS = NOT_RUN_POST_PREDICTION_ENTRYPOINT_FAILURE
CPCV_STATUS = NOT_RUN_POST_PREDICTION_ENTRYPOINT_FAILURE
SPA_STATUS = NOT_RUN_POST_PREDICTION_ENTRYPOINT_FAILURE
REALITYCHECK_STATUS = NOT_RUN_POST_PREDICTION_ENTRYPOINT_FAILURE
H1_RESULT_CLASSIFICATION = INCONCLUSIVE
DVC_H1_REPRO_STATUS = FAIL_POST_PREDICTION_STATISTICS_ENTRYPOINT
```

## Attempt-004 final clean boundary

Attempt-004 was the one owner-authorized final clean execution. It used a new
root and regenerated the preflight surface; no prediction, return, cross-
validation result, or statistical evidence from attempts 001-003 was used.
The approximately 10 GiB WSL RAM and 4 GiB swap resource gate passed. Both
fresh fits and both frozen Qlib backtests completed, with the two fit processes
exiting normally below the available memory boundary.

The pre-execution Windows-environment version/help probes passed outside the
real stage invocation, but did not reproduce its WSL interoperability boundary.
In the actual DVC stage, the skfolio virtual-environment launcher again received
a quoted base-interpreter path and exited before importing the H1 script.
Process 5 therefore failed and process 6 was not started. Under the explicit
fail-closed rule, the completed primary pair and backtests remain diagnostic
only: no partial continuation or retry occurred, and attempt-004 is not eligible
for scientific classification.

```text
ATTEMPT_004_IS_PROTOCOL_CHANGE = NO
RESOURCE_GATE = PASS
SKFOLIO_ENTRYPOINT_GATE = FAIL_RUNTIME_EQUIVALENCE
ARCH_ENTRYPOINT_GATE = NOT_REACHED_AFTER_SKFOLIO_FAILURE
ATTEMPT_004_AUTHORITY = FINAL_CLEAN
ATTEMPT_004_EXECUTION_STATUS = FAIL_POST_PREDICTION_STATISTICS_ENTRYPOINT
ATTEMPT_004_FINAL_CLASSIFICATION_ELIGIBLE = NO
ATTEMPT_004_S0_MAX_RSS_KIB = 6168912
ATTEMPT_004_S1_MAX_RSS_KIB = 7514992
ATTEMPT_004_S0_MODEL_FIT_COUNT = 1
ATTEMPT_004_S1_MODEL_FIT_COUNT = 1
ATTEMPT_004_S0_MODEL_FIT_COMPLETION_COUNT = 1
ATTEMPT_004_S1_MODEL_FIT_COMPLETION_COUNT = 1
ATTEMPT_004_S0_TEST_RANK_IC = 0.0021911029598144574
ATTEMPT_004_S1_TEST_RANK_IC = 0.004588185207288156
ATTEMPT_004_H1_TEST_RANK_IC_DELTA = 0.0023970822474736987
ATTEMPT_004_QLIB_BACKTEST_STATUS = PASS
WALKFORWARD_STATUS = NOT_RUN_POST_PREDICTION_ENTRYPOINT_FAILURE
CPCV_STATUS = NOT_RUN_POST_PREDICTION_ENTRYPOINT_FAILURE
SPA_STATUS = NOT_RUN_POST_PREDICTION_ENTRYPOINT_FAILURE
REALITYCHECK_STATUS = NOT_RUN_POST_PREDICTION_ENTRYPOINT_FAILURE
H1_RESULT_CLASSIFICATION = INCONCLUSIVE
DVC_H1_REPRO_STATUS = FAIL_POST_PREDICTION_STATISTICS_ENTRYPOINT
```

The frozen projection authority, exact date-valid episode crosswalk, and
unchanged missingness policy establish the required leakage gates:

```text
ACCEPTANCE_TIME_LEAKAGE_COUNT = 0
REPORT_PERIOD_LEAKAGE_COUNT = 0
AMENDMENT_BACKWARD_LEAKAGE_COUNT = 0
CROSS_CIK_CONTAMINATION_COUNT = 0
EPISODE_MEMBERSHIP_LEAKAGE_COUNT = 0
CURRENT_TICKER_LEAKAGE_COUNT = 0
SOURCE_UNAVAILABLE_SUBSTITUTION_COUNT = 0
FUTURE_FILING_VISIBILITY_COUNT = 0
```

No bulk stage, SEC path, filing-feature materialization, H2/S2 path, PID403
path, or P2 V2 sealed OOS surface was accessed. None of attempts 001-004
completed the frozen evidence family, so the preregistered H1 question remains
inconclusive and P6 entry is not authorized.

The retained 603 physical lines remain above the approximate 405-line guide
because they contain H1-specific episode crosswalk validation, frozen input and
processor gates, exact S0/S1 surface composition, Qlib/MLflow evidence capture,
and result classification. Calendar construction, Qlib backtest mechanics, and
temporal split/reduction logic now call the already-proven historical-rehearsal
implementation; the former task-specific resume framework is gone. The only
remaining duplicated repository utility surface is 14 lines of local hashing
and immutable JSON output.

## Ownership and next authority

```text
P5_MINIMAL_UPSTREAM_DATA_LAYER = COMPLETE
P5_COMPLETE = NO

AQ_FEATURE_ENGINE = NO
AQ_MODEL_ENGINE = NO
AQ_ABLATION_ENGINE = NO
AQ_STATISTICS_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 603
LOC_DUPLICATING_EXISTING_REPO_CAPABILITY_BEFORE = 162
LOC_DUPLICATING_EXISTING_REPO_CAPABILITY_AFTER = 14
RESUME_FRAMEWORK_RETIRED = YES

PROJECT_MODEL_TRAINING_COUNT = 8
PROJECT_PREDICTION_COUNT = 7
PROJECT_BACKTEST_COUNT = 6
H1_EXECUTED = INCOMPLETE_ATTEMPT_004
H2_EXECUTED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P6_ACTIVE = NO

CURRENT_PHASE = P5_FUNDAMENTAL_INTELLIGENCE
CURRENT_DEVELOPMENT_NEXT = P5_H1_FINAL_ATTEMPT_RUNTIME_BOUNDARY_CLOSEOUT_001
CURRENT_DEVELOPMENT_NEXT_GATE = H1_INCONCLUSIVE_FINAL_ATTEMPT_FAILED_CLOSED
FINAL_CLASSIFICATION = INCONCLUSIVE_ATTEMPT_004_POST_PREDICTION_ENTRYPOINT_FAILURE
```
