# P2 Certification Protocol Preregistration 001

Date: 2026-09-13

Status: **COMPLETE — POLICY AND CONFIGURATION FROZEN BEFORE EXECUTION**

Classification: **PREREGISTRATION ONLY — NO PERFORMANCE WORKLOAD EXECUTED**

## Authority and immutable protocol

```text
TASK = AUTONOMOUS-QUANT-P2-CERTIFICATION-PROTOCOL-PREREGISTRATION-001
BASE_MAIN = 9c166de6758b1387f6cfef526ce06b7d19f4afc9
PROTOCOL_VERSION = P2_CERTIFICATION_PROTOCOL_V1
PROTOCOL_FILE = 40-certification-system/protocol/p2-certification-protocol-v1.json
PROTOCOL_SHA256 = a9aed881c229f9eb7f85fa23b866168a55dc9c00be3c3b178d91a4af20451dfb
CANONICAL_SERIALIZATION = UTF8_LF_SORTED_KEYS_INDENT_2_TERMINAL_NEWLINE
P2_CERTIFICATION_PROTOCOL = FROZEN
```

The JSON protocol is the machine-readable authority. It freezes policy,
thresholds, candidate and trial inventory, dataset dependencies, sealed-OOS
semantics, and the decision ceiling before any new performance-producing
certification workload. A material candidate-set or policy change requires a
new protocol version; it cannot silently mutate V1.

## Upstream ownership

Microsoft Qlib owns `DatasetH`, RaggedAlpha158/Alpha158 operators, models,
predictions, `TopkDropoutStrategy`, `Exchange`, transaction-cost behavior,
backtest, Recorder/MLflow, and portfolio analysis. skfolio `1.0.6` owns
`WalkForward`, `CombinatorialPurgedCV`, purge, and embargo mechanics. arch
`8.0.0` owns SPA, RealityCheck, StepM, MCS, and bootstrap procedures.
`exchange_calendars` owns XNYS sessions, Pandera owns generic tabular
validation, and DVC owns dependency/evidence reproducibility.

AQ owns only the preregistered policy, thresholds, trial inventory,
sealed-OOS authority, and `CertificationDecision` semantics.

```text
AQ_CUSTOM_CERTIFICATION_ENGINE = NO
AQ_CUSTOM_CV_ENGINE = NO
AQ_CUSTOM_STATISTICS_ENGINE = NO
AQ_CUSTOM_BACKTESTER = NO
AQ_CUSTOM_BOOTSTRAP_ENGINE = NO
AQ_CUSTOM_CALENDAR_ENGINE = NO
AQ_CUSTOM_SCHEMA_ENGINE = NO
AQ_CUSTOM_DATA_ENGINE = NO
AQ_CUSTOM_EXPERIMENT_DATABASE = NO
AQ_CUSTOM_ENGINE_COUNT = 0
```

The new `seal_protocol.py` is a bounded DVC dependency-hash verifier. It does
not construct splits, statistics, predictions, portfolios, or certification
decisions and is not a generic AQ engine.

## Frozen dataset identity

```text
HISTORY_START = 2015-01-02
HISTORY_END = 2024-12-31
SECURITY_IDENTITIES = 730
MEMBERSHIP_RANGES = 745
MEMBER_SESSION_ROWS = 1267963
OBSERVED_SAFE_ROWS = 1224788
MASKED_ROWS = 43175
MASKED_ROW_PERCENT = 3.405068
QLIB_PROVIDER = D:/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data
PROVIDER_BUILD_REPORT_SHA256 = eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142
AUTHORITY_FACT_COUNT = 12
AUTHORITY_FACT_SHA256 = 3cd9b13a1424609120a4e069ac2cf9f9b9aa61e2df919aa48cf51eeac616bc69
CODE_BASE_SHA = 9c166de6758b1387f6cfef526ce06b7d19f4afc9
```

The protocol also pins the existing upstream-stack Qlib, skfolio, arch,
validation, blocker-ledger, and DVC seal identities, plus canonical-LF hashes
for each relevant tracked candidate configuration. No dataset was rebuilt,
mutated, or reinterpreted.

## Historical and sealed-OOS boundary

The entire 2015-01-02 through 2024-12-31 dataset is frozen as:

```text
DATA_HISTORY_CLASSIFICATION = HISTORICAL_DEVELOPMENT_AND_CERTIFICATION_REHEARSAL_ONLY
HISTORICAL_DATA_IS_PRISTINE_OOS = NO
HISTORICAL_DATA_CAN_ISSUE_CERTIFIED_STATUS = NO
P1_OBSERVED_TEST_INTERVAL_REMAINS_NON_PRISTINE = YES
```

No historical partition may later be relabeled as pristine sealed OOS. A V1
historical execution may return only `REJECTED` or
`NOT_ELIGIBLE_NO_PRISTINE_OOS`; it may not return `CERTIFIED`.

```text
SEALED_OOS_START_RULE = THE_FIRST_XNYS_SESSION_STRICTLY_AFTER_THE_CERTIFICATIONPROTOCOLV1_FREEZE_COMMIT_BECOMES_PART_OF_ORIGIN_MAIN
SEALED_OOS_START_SESSION_RESOLVED = NO
MINIMUM_SEALED_OOS_SESSIONS = 126
EARLY_SEALED_RESULT_ACCESS = PROHIBITED
INTERMEDIATE_PEEK = PROHIBITED
ONE_SHOT_RELEASE = YES
SEALED_OOS_REUSE_FOR_RETUNING = PROHIBITED
SEALED_OOS_AVAILABLE = NO
```

After one-shot release, that window becomes historical evidence for later
protocol versions and cannot be reused as pristine OOS.

## Candidate, control, and historical trial inventory

```text
PRIMARY_CANDIDATE_ID = QLIB_LGBMODEL_RAGGEDALPHA158_TOPK30_NDROP3_V1
PRIMARY_MODEL = QLIB_LGBMODEL_CONFIG_SHA256_c6e6c4882adeb053d58e91b27d7d796fd9886dc1946d1d0540d5d9637f42ccaf
PRIMARY_FACTOR_FAMILY = CURRENT_P2_RAGGEDALPHA158_ALPHA158_COMPATIBLE
PRIMARY_STRATEGY = TOPK_30_NDROP_3
PRIMARY_STATISTICAL_CONTROL = QLIB_LINEARMODEL_OLS_TOPK50_NDROP5
KNOWN_EXECUTED_TRIAL_COUNT = 4
CATBOOST_EXECUTED = NO
```

The four retained historical trials are LightGBM 50/5, LightGBM 30/3,
LightGBM 100/10, and Linear OLS 50/5. No unsuccessful historical trial was
removed. The P1 winner selection is explicitly already-observed historical
evidence and does not certify the primary candidate.

SPY remains a P1 historical reference only. The accepted P2 provider has no
valid certification-authority SPY instrument, so V1 records
`MARKET_BENCHMARK_CERTIFICATION_EVIDENCE = NOT_AVAILABLE` and prohibits any
claim that the candidate is certified to beat SPY.

## Label and temporal CV policy

Read-only inspection of pinned Qlib source commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` confirmed that
`RaggedAlpha158` inherits `Alpha158.get_label_config()` unchanged:

```text
LABEL_EXPRESSION = Ref($close, -2)/Ref($close, -1) - 1
LABEL_LOOKAHEAD_SESSIONS = 2
LABEL_VERIFICATION = PASS
```

The frozen skfolio policies are:

```text
WALKFORWARD = WalkForward(test_size=63, train_size=504, purged_size=2, expand_train=False, reduce_test=False)
WALKFORWARD_STEP = 63_SESSIONS_VIA_SKFOLIO_INTEGER_WINDOW_TEST_SIZE_ADVANCEMENT
WF_MIN_POSITIVE_ACTIVE_RETURN_FRACTION = 0.60
WF_MEDIAN_ACTIVE_RETURN_REQUIRED = GREATER_THAN_ZERO

CPCV = CombinatorialPurgedCV(n_folds=10, n_test_folds=2, purged_size=2, embargo_size=2)
CPCV_MIN_POSITIVE_ACTIVE_RETURN_FRACTION = 0.60
CPCV_MEDIAN_ACTIVE_RETURN_REQUIRED = GREATER_THAN_ZERO
```

Active return means candidate net return minus the preregistered Linear OLS
control net return for the same evaluation window. No split was constructed in
this task.

## Multiple-testing, cost, robustness, and regime policy

```text
MULTIPLE_TESTING_OWNER = ARCH_8.0.0
SIGNIFICANCE_ALPHA = 0.05
BOOTSTRAP_REPLICATIONS = 5000
BOOTSTRAP_SEED = 20260913
BOOTSTRAP_METHOD = STATIONARY
BOOTSTRAP_BLOCK_SIZE = 10
LOSS = NEGATIVE_NET_DAILY_RETURN
PRIMARY_BENCHMARK_LOSS = NEGATIVE_NET_DAILY_RETURN_OF_PREREGISTERED_LINEAR_OLS_CONTROL
SPA_CONSISTENT_PVALUE = LESS_THAN_OR_EQUAL_TO_0.05
REALITYCHECK_PVALUE = LESS_THAN_OR_EQUAL_TO_0.05
PRIMARY_CANDIDATE_IN_STEPM_SUPERIOR_SET = YES
PRIMARY_CANDIDATE_IN_MCS_95_PERCENT_SET = YES
```

The cost policy retains close execution, 0.095 limit threshold, 0.0005 open
cost, 0.0015 close cost, and minimum cost 5. Base and 2x proportional-cost
scenarios require median active return greater than zero. The 3x scenario is
mandatory evidence only and is not a veto gate; minimum cost remains 5 in all
scenarios.

The strategy perturbations are frozen exactly as 30/3, 25/3, 35/3, 30/2,
and 30/4. At least three of four neighbors must preserve the primary positive
active-return sign, and the median active return across all five must exceed
zero. Calendar evidence blocks are 2015-2016, 2017-2018, 2019-2020,
2021-2022, and 2023-2024. Regime evidence is mandatory but not a hard veto;
unavailable blocks remain explicit and predictions may not be fabricated.

```text
DSR = DEFERRED_NO_SELECTED_UPSTREAM_OWNER
PBO = DEFERRED_NO_SELECTED_UPSTREAM_OWNER
DSR_PBO_BLOCK_P2_V1_SYSTEM_COMPLETION = NO
DSR_PBO_SELF_IMPLEMENTATION_AUTHORIZED = NO
```

## Reproducibility and non-actions

The `p2_certification_protocol_freeze` DVC stage binds the canonical protocol,
provider build report, upstream-stack evidence seal, 12-fact authority, and
the RaggedAlpha158, LightGBM, Linear OLS, and strategy configuration
identities. Its generated seal is private and ignored by Git. Initial
reproduction passed; an immediate second reproduction reported unchanged.

```text
DVC_REPRO = PASS
SECOND_DVC_REPRO = UNCHANGED
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
WALKFORWARD_EXECUTED = NO
CPCV_EXECUTED = NO
SPA_EXECUTED = NO
REALITYCHECK_EXECUTED = NO
STEPM_EXECUTED = NO
MCS_EXECUTED = NO
CERTIFICATION_DECISION_EXECUTED = NO
MARKET_DATA_NETWORK_CALLS = 0
BROKER_CALLS = 0
LLM_CALLS = 0
RD_AGENT_EXECUTED = NO
NEW_DATA_PROVIDER = NO
```

## Current state

```text
P2_CERTIFICATION = STARTED / IN_PROGRESS
P2_CERTIFICATION_PROTOCOL = FROZEN
P2_CERTIFICATION_PROTOCOL_VERSION = V1
P2_HISTORICAL_REHEARSAL_READY = YES
SEALED_OOS_AVAILABLE = NO
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
CURRENT_NEXT = P2_CERTIFICATION_HISTORICAL_REHEARSAL_001
```
