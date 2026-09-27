# P7 Historical Static Ensemble Research Protocol Freeze 001

Date: 2026-09-27

Status: `PASS_P7_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_PROTOCOL_FROZEN`

This task preregistered one historical, research-only static ensemble study
before any ensemble result was opened. It did not deserialize Candidate
prediction values for analysis, combine real signals, compute RankIC, run a
portfolio backtest, train/refit a model, or access P2 V2 sealed OOS.

## Study boundary

```text
STUDY_TYPE = RESEARCH_ONLY_HISTORICAL_STATIC_ENSEMBLE
HISTORICAL_TEST_STATUS = CONSUMED_AS_RESEARCH_EVIDENCE
PRISTINE_OOS = NO
P2_CERTIFICATION_EVIDENCE = NO
P7_DYNAMIC_ROSTER_EVIDENCE = NO
P7_EXIT_CONDITION_EVIDENCE = NO
PRODUCTION_AUTHORIZATION = NO
```

The study asks only whether the fixed all-17 Formulaic Alpha static Qlib
ensemble improves historical predictive signal quality relative to the
preregistered OLS Alpha158 historical control on the exact frozen P7
population. A supportive result would remain research evidence, not
certification, lifecycle eligibility, dynamic-roster evidence, or production
authorization.

## Frozen input and control

The complete P7 input contract is reused byte-for-byte. All 17 derived
Candidate views and the losslessly adapted OLS control must cover this exact
ordered population. No union, recomputed intersection, or result-conditioned
row removal is permitted.

```text
ROW_COUNT = 374591
SESSION_COUNT = 751
INSTRUMENT_COUNT = 547
START = 2022-01-03
END = 2024-12-27
POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
INPUT_CONTRACT_SHA256 = 92de81d0b8b7b7a29891bf523ae8519af44456f52fea3410ebf0ebd210d0f81f
```

The master roster is exactly the 17 Candidate V3 identities in the frozen P2
Formulaic cohort manifest. They are distinct Candidate identities but one
Formulaic Alpha research family.

```text
MASTER_CANDIDATE_COUNT = 17
FORMULAIC_CANDIDATE_COUNT = 17
INDEPENDENT_ALPHA_FAMILY_COUNT = 1
COHORT_MANIFEST_SHA256 = 53920302856592fb43bbffb011423731893ac0a995a04194541c39d69ecfde70
```

The preregistered control remains:

```text
CONTROL_MODEL = qlib.contrib.model.linear.LinearModel(estimator=ols)
CONTROL_CONFIG_IDENTITY = sha256:b9a92537a9737ce909284e77e583ad20c0a3d2b18f795271d85db6c5ba5eafc1
CONTROL_FIT_POLICY = TRAIN_ONLY
CONTROL_PREDICTION_SHA256 = 26c3433faa58a64914393fe13eac169d9ce86dbbe86f16dfb2b24fbd64139dab
CONTROL_RECORDER_ID = d6035e318a0640da876e52d587137e7c
```

No component is added, removed, reweighted, sign-flipped, or selected using
historical performance.

## Ensemble and endpoint

Pinned Microsoft Qlib source
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` confirms that
`AverageEnsemble` standardizes each component cross-section by session and
then averages the standardized values. Qlib remains the only numerical
combination owner.

```text
ENSEMBLE_OWNER = QLIB_AVERAGEENSEMBLE
ENSEMBLE_WEIGHTING = SESSION_LOCAL_NONCONSTANT_COMPONENT_EQUAL_WEIGHT
CONSTANT_SESSION_POLICY = EXACT_CONSTANT_COMPONENT_INACTIVE_FOR_CURRENT_SESSION_ONLY_NOT_A_ROSTER_CHANGE
MINIMUM_ACTIVE_COMPONENT_COUNT = 2
MISSING_NONFINITE_MISALIGNED_POLICY = FAIL_CLOSED
```

The primary endpoint is frozen as:

```text
PRIMARY_METRIC = DAILY_CROSS_SECTIONAL_RANK_IC
PRIMARY_COMPARISON = STATIC_17_ENSEMBLE_MINUS_OLS_ALPHA158_CONTROL
PRIMARY_ENDPOINT = MEAN_DAILY_RANK_IC_DELTA_VS_OLS_CONTROL
PRIMARY_SESSION_COUNT = 751
```

Qlib `calc_ic` owns daily cross-sectional RankIC. The primary inference uses
arch 8.0.0 `SPA` with one preregistered alternative: OLS negative daily RankIC
is the benchmark loss and ensemble negative daily RankIC is the alternative
loss. Parameters are stationary bootstrap, block size 10, 5,000 replications,
studentization enabled, no nested bootstrap, and seed 20260913. The consistent
p-value gate is at most 0.05.

## Component family and temporal robustness

Read-only API inspection confirmed that arch `SPA`, `RealityCheck`, and
`StepM` consume a benchmark loss vector plus alternative-model losses, while
`MCS` consumes a symmetric model-loss matrix. MCS is therefore the exact
selected upstream procedure for the ensemble-plus-17-component family. It is
descriptive/exploratory only and cannot select a component or change the
primary classification.

```text
SECONDARY_COMPONENT_CONTROL_COUNT = 17
MULTIPLE_COMPARISON_PROCEDURE = ARCH_8_0_0_MCS_DESCRIPTIVE_18_SIGNAL_FAMILY
MCS_SIZE = 0.05
MCS_REPS = 5000
MCS_BLOCK_SIZE = 10
MCS_METHOD = R
MCS_BOOTSTRAP = STATIONARY
MCS_SEED = 20260913
```

skfolio 1.0.6 was rechecked with synthetic arrays of length 751. It produces
three complete WalkForward folds and 45 CPCV splits, with zero train/test
overlap. These are robustness partitions over frozen daily RankIC deltas; they
do not train/refit a model and do not restore pristine OOS status.

```text
WALKFORWARD_PROTOCOL = train_size=504,test_size=63,purged_size=2,expand_train=false,reduce_test=false
WALKFORWARD_USABLE_FOLD_COUNT = 3
WALKFORWARD_UNUSED_TAIL_SESSION_COUNT = 56
CPCV_PROTOCOL = n_folds=10,n_test_folds=2,purged_size=2,embargo_size=2
CPCV_USABLE_SPLIT_COUNT = 45
CPCV_TRAIN_COUNT_RANGE = 589..598
CPCV_TEST_COUNT_RANGE = 150..151
TEMPORAL_CV_ROLE = ROBUSTNESS_PARTITIONS_ONLY_NO_MODEL_TRAINING
TEMPORAL_CV_RESTORES_PRISTINE_OOS = NO
```

Both robustness gates require a positive median split/fold mean delta and a
positive fraction of at least 0.6. These reuse the already-frozen P2 temporal
robustness interpretation rather than choosing a threshold from P7 outcomes.

## Secondary portfolio projection

The exact frozen P2 V2 comparable strategy configuration exists and may be
reused as a secondary descriptive projection. It does not affect the primary
classification and cannot be tuned from P7 outcomes.

```text
PORTFOLIO_PROJECTION_STATUS = AUTHORIZED_SECONDARY_REUSE_FROZEN_P2_V2_CONFIGURATION
STRATEGY = qlib.contrib.strategy.signal_strategy.TopkDropoutStrategy
TOPK = 30
N_DROP = 3
ACCOUNT = 100000000
BENCHMARK = NONE
LIMIT_THRESHOLD = 0.095
DEAL_PRICE = close
OPEN_COST = 0.0005
CLOSE_COST = 0.0015
MIN_COST = 5
PORTFOLIO_CLASSIFICATION_ROLE = SECONDARY_DESCRIPTIVE_ONLY_NO_PRIMARY_GATE
```

## Frozen decision rule

`STATIC_ENSEMBLE_RESEARCH_SUPPORTIVE` requires all six preregistered gates:

1. full-period mean daily RankIC delta is greater than zero;
2. arch SPA consistent p-value is at most 0.05;
3. WalkForward positive-fold fraction is at least 0.6;
4. WalkForward median fold mean delta is greater than zero;
5. CPCV positive-split fraction is at least 0.6; and
6. CPCV median split mean delta is greater than zero.

For a complete, valid execution, failure of any required supportive gate is
`STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE`. An input/method integrity failure
that prevents complete valid primary and robustness evidence is
`STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE`. There is no economically invented
effect-size threshold and no outcome-selected alternative endpoint.

```text
RESULT_CLASSIFICATIONS = STATIC_ENSEMBLE_RESEARCH_SUPPORTIVE; STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE; STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
PROTOCOL_CHANGING_RERUN_AUTHORIZED = NO
```

## Protocol identity, ownership, and safety

The normative protocol is
`30-research-system/qlib/p7-native-ensemble/historical-static-ensemble-research-protocol.json`.
Its identity is SHA-256 over the `rfc8785==0.1.4` canonical bytes of the full
JSON object.

```text
PROTOCOL_SHA256 = b60078bdba4190fbda2c6f3d3580f0e40a9801c87867095bfaa12885a0fb3ff4
PROTOCOL_STATUS = FROZEN_PRE_EXECUTION
RANKIC_OWNER = QLIB
TEMPORAL_SPLIT_OWNER = SKFOLIO_IF_USED
MULTIPLE_TESTING_OWNER = ARCH_IF_USED
RUN_LINEAGE_OWNER = QLIB_MLFLOW
REPRODUCIBILITY_OWNER = DVC
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0

REAL_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PORTFOLIO_BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
MODEL_TRAINING_COUNT = 0
MODEL_REFIT_COUNT = 0
PREDICTION_GENERATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
```

The required next execution may run this exact protocol once. P2 Formulaic
Alpha sealed-OOS accumulation remains independently active and unchanged.

```text
CURRENT_DEVELOPMENT_NEXT = P7_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_EXECUTION_001
FINAL_CLASSIFICATION = PASS_P7_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_PROTOCOL_FROZEN
```
