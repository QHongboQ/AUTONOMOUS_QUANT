# P6 Historical News FinSen Ablation Protocol Freeze 001

## Authority

PR #108 was squash-merged before this protocol was created. The exact sealed
FinSen factor is now subject to one preregistered comparison and no alternative
FinSen hypothesis.

```text
PR108_MERGE_SHA = 8599916dfe472175598e2bd24bd3164ed90916f0
BASE_MAIN = 8599916dfe472175598e2bd24bd3164ed90916f0
PROTOCOL_ARTIFACT = 30-research-system/qlib/p6-historical-news-finsen-ablation/finsen-ablation-protocol.json
PROTOCOL_SHA256 = 63c69d4eb80a7d98ad4b846484ca14a0bc47e83b2fc5659a261098e7852d79b9
PROTOCOL_STATUS = FROZEN_PRE_EXECUTION
HYPOTHESIS_COUNT = 1
PRIMARY_SURFACE_COMPARISON_COUNT = 1
PROTOCOL_CHANGING_RERUN_AUTHORIZED = NO
```

PR #106 remains open, unmerged, unmodified stale closeout evidence. It must not
be rebased, conflict-resolved, merged, or closed by this protocol task.

## Exact surfaces and common support

The control authority is reused without regeneration. `M0` and `M1` must have
identical datetime rows, instruments, membership episodes, labels, splits, and
row counts. A FinSen NULL may not remove a row.

```text
CONTROL_SURFACE = BASE_157
CONTROL_FEATURE_COUNT = 157
CONTROL_FEATURE_MANIFEST_SHA256 = 7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463
CONTROL_DATASET_IDENTITY = P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135
M0 = BASE_157
M0_FEATURE_COUNT = 157
M1 = BASE_157_PLUS_EXACT_FINSEN_SENTIMENT_1
M1_FEATURE_COUNT = 158
FINSEN_FACTOR_NAME = finsen_finbert_market_sentiment
FINSEN_FACTOR_SHA256 = 93bc6a62550accc0a4484e86d6f3af8242c69a6211a51ef40bb34d0c9bc60f48
TRAIN_RANGE = 2015-04-01..2019-12-31
VALIDATION_RANGE = 2020-01-01..2021-12-31
HISTORICAL_RESEARCH_TEST_RANGE = 2022-01-03..2023-07-17
```

The right tail after 2023-07-17 is excluded. The 84 NULL sessions inside the
supported interval remain rows in both surfaces and retain NULL on `M1`; they
are not interpreted as neutral or no-news observations.

## Semantic ownership

FinSen and the pinned ProsusAI/FinBERT upstream own the text-to-daily-sentiment
semantics. AQ owns only the conservative research-session projection and its
already-sealed collision choice.

```text
FINSEN_SENTIMENT_METHOD_OWNER = FINSEN_PROSUSAI_FINBERT
UPSTREAM_FINSEN_OWNED_SEMANTICS = Content -> ProsusAI/FinBERT -> P_positive - P_negative -> arithmetic daily mean
FINSEN_SESSION_PROJECTION_OWNER = AQ_RESEARCH_POLICY
SESSION_PROJECTION_POLICY = FIRST_XNYS_SESSION_STRICTLY_AFTER_SOURCE_CALENDAR_DATE
COLLISION_POLICY = LATEST_SOURCE_CALENDAR_DATE_PER_EFFECTIVE_SESSION
COLLISION_COUNT = 100
SUPERSEDED_DAILY_SIGNAL_COUNT = 106
NO_ZERO_FILL = YES
NO_FORWARD_FILL = YES
NO_BACKFILL = YES
NO_ROW_DROP_DUE_TO_FINSEN_NULL = YES
INSTRUMENT_DEPENDENT_FINSEN_VALUE_COUNT_REQUIRED = 0
MANUFACTURED_ROW_COUNT_REQUIRED = 0
```

Future evaluation may use only a mechanical DuckDB session join to broadcast
the same global value to existing eligible security rows. No per-instrument
FinSen artifact, entity mapping, ticker mapping, or company-news claim is
authorized.

## Frozen research vehicle

The protocol reuses the P5/Macro V1 vehicle exactly. No model, label,
processor, portfolio, cross-validation, bootstrap, or hyperparameter authority
was changed.

```text
MODEL_OWNER = MICROSOFT_QLIB
MODEL_CLASS = qlib.contrib.model.gbdt.LGBModel
MODEL_CONFIG_SHA256 = f75355629e7ad6b85f100627dbc055712d7f72d1e1e31783736f1ce4cc10a61a
PRIMARY_METRIC = QLIB_RANK_IC
PRIMARY_DIRECTION = M1_MINUS_M0
WALKFORWARD_OWNER = skfolio
CPCV_OWNER = skfolio
SPA_REALITY_CHECK_OWNER = arch
CLASSIFICATION_SET = INCREMENTAL_VALUE_SUPPORTED,DEGRADED,NO_MEASURABLE_INCREMENTAL_VALUE,INCONCLUSIVE
```

`INCREMENTAL_VALUE_SUPPORTED` requires a positive Rank IC delta plus all
forward WalkForward, CPCV, SPA, and RealityCheck gates. `DEGRADED` requires the
corresponding complete reverse-direction evidence. Valid evidence satisfying
neither complete direction is `NO_MEASURABLE_INCREMENTAL_VALUE`.
`INCONCLUSIVE` is reserved for invalid or incomplete science/runtime evidence,
not weak performance.

Even a positive result would mean only `RESEARCH_EVIDENCE_SUPPORTED`. FinSen
remains date-only and research-use constrained:

```text
STRICT_PRODUCTION_PIT_READY = NO
PRODUCTION_ADMISSION_AUTHORIZED = NO
```

## Anti-p-hacking and no-execution close

No alternate lag, window, weekend aggregation, FinBERT model, text field,
count feature, threshold, normalization, clipping, imputation, split, model,
or hyperparameter search is permitted after this freeze. A negative result
closes this exact FinSen question.

```text
AQ_OUTCOME_DATA_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEWS_CRAWLER_CREATED = NO
AQ_ENTITY_RESOLUTION_ENGINE_CREATED = NO
AQ_SENTIMENT_ENGINE_CREATED = NO
AQ_NEWS_DATABASE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P6_HISTORICAL_NEWS_FINSEN_FIRST_AUTHORIZED_ABLATION_001
FINAL_CLASSIFICATION = PASS_P6_HISTORICAL_NEWS_FINSEN_ABLATION_PROTOCOL_FROZEN
```
