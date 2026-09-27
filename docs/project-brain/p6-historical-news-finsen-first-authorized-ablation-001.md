# P6 Historical News FinSen First Authorized Ablation 001

Date: 2026-09-26

## Outcome

The exact frozen comparison reached a terminal `INCONCLUSIVE` result. This is
a protocol/runtime validity result, not a weak-evidence interpretation and not
a positive or negative FinSen finding.

```text
BASE_MAIN = cde0bce76a1c4e7712da5570968a003735f33d8d
PR109_MERGED = YES
PR109_MERGE_SHA = cde0bce76a1c4e7712da5570968a003735f33d8d
PROTOCOL_SHA256 = 63c69d4eb80a7d98ad4b846484ca14a0bc47e83b2fc5659a261098e7852d79b9
PROTOCOL_HASH_VERIFIED = YES
```

## Preflight

All frozen pre-fit gates passed before either model was fitted.

```text
CONTROL_FEATURE_MANIFEST_SHA256 = 7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463
CONTROL_DATASET_IDENTITY = P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135
FINSEN_FACTOR_SHA256 = 93bc6a62550accc0a4484e86d6f3af8242c69a6211a51ef40bb34d0c9bc60f48
M0_FEATURE_COUNT = 157
M1_FEATURE_COUNT = 158
M0_ROW_COUNT = 1011952
M1_ROW_COUNT = 1011952
M0_M1_ROW_IDENTITY_EQUAL = YES
M0_M1_LABEL_IDENTITY_EQUAL = YES
M0_M1_MEMBERSHIP_IDENTITY_EQUAL = YES
SUPPORTED_INTERVAL_NULL_SESSION_COUNT = 84
ZERO_FILL_USED = NO
FORWARD_FILL_USED = NO
BACKFILL_USED = NO
ROW_DROP_DUE_TO_FINSEN_NULL = NO
INSTRUMENT_DEPENDENT_FINSEN_VALUE_COUNT = 0
MANUFACTURED_INSTRUMENT_SESSION_ROW_COUNT = 0
```

The runtime identities were Qlib `0.9.8.dev26`, source
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`, LightGBM `4.7.0`, skfolio
`1.0.6`, and arch `8.0.0`. The model configuration hash remained
`f75355629e7ad6b85f100627dbc055712d7f72d1e1e31783736f1ce4cc10a61a`.

## Exact execution and failure boundary

Exactly one M0 fit and one M1 fit completed through Microsoft Qlib. The finite
Rank IC evidence is retained but cannot determine the preregistered
classification without the required statistical gates.

```text
M0_TEST_RANK_IC = 0.004271356026045012
M1_TEST_RANK_IC = 0.005851775987652466
RANK_IC_DELTA = 0.0015804199616074538
MODEL_TRAINING_COUNT = 2
PREDICTION_COUNT = 2
BACKTEST_COUNT = 2
ABLATION_COUNT = 1
```

The shared P2 backtest reference initially inherited its module-level end date
of 2024-12-31. That output is retained as invalid diagnostic evidence. The
exact recovery changed no scientific authority: it rebound the shared Qlib
backtest to the frozen FinSen interval `2022-01-03..2023-07-17`, reused the
same predictions, and performed zero model refits. The authoritative daily
return evidence contains 385 sessions.

The next frozen step failed before emitting any temporal or multiple-testing
gate:

```text
WALKFORWARD_TRAIN_SIZE = 504
WALKFORWARD_PURGED_SIZE = 2
MINIMUM_REQUIRED_OBSERVATIONS = 506
ACTUAL_TEST_OBSERVATIONS = 385
WALKFORWARD_FORWARD_GATE = NOT_AVAILABLE
WALKFORWARD_REVERSE_GATE = NOT_AVAILABLE
CPCV_FORWARD_GATE = NOT_AVAILABLE
CPCV_REVERSE_GATE = NOT_AVAILABLE
SPA_FORWARD_CONSISTENT_PVALUE = NOT_AVAILABLE
REALITY_CHECK_FORWARD_CONSISTENT_PVALUE = NOT_AVAILABLE
SPA_REVERSE_CONSISTENT_PVALUE = NOT_AVAILABLE
REALITY_CHECK_REVERSE_CONSISTENT_PVALUE = NOT_AVAILABLE
```

Changing the test end, WalkForward train size, purge, or any classification
threshold after seeing Rank IC would violate the protocol. No such change or
second FinSen experiment was performed.

## Safety and routing

```text
AQ_OUTCOME_DATA_ACCESSED = YES
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
PR106_STATE = OPEN
PR106_MERGED = NO
PR106_MODIFIED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/historical-news-finsen-first-authorized-ablation-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 728cd2ac31eb9e40f1f9682fe6663ac46a68ac17af71f446ee32c31892d2a5d0
CURRENT_DEVELOPMENT_NEXT = P6_HISTORICAL_NEWS_FINSEN_INCONCLUSIVE_CLOSEOUT_OR_EXACT_RECOVERY_001
FINAL_CLASSIFICATION = INCONCLUSIVE_P6_HISTORICAL_NEWS_FINSEN_FROZEN_WALKFORWARD_INSUFFICIENT_OBSERVATIONS
```
