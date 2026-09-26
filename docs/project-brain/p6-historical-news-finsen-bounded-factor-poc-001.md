# P6 Historical News FinSen Bounded Factor POC 001

## Decision

The research-only FinSen path successfully materialized one deterministic,
global-market sentiment factor. This is not a production data-source admission,
does not establish strict point-in-time availability, and contains no outcome
or performance evidence.

```text
P6_STATUS = REOPENED_BOUNDED_HISTORICAL_NEWS_RESEARCH
P6_CLOSEOUT_CANDIDATE = PR_106_HELD_UNMERGED
FINSEN_RESEARCH_FACTOR_STATUS = MATERIALIZED_RESEARCH_CHALLENGER
STRICT_PRODUCTION_PIT_READY = NO
PRODUCTION_ADMISSION_AUTHORIZED = NO
CURRENT_DEVELOPMENT_NEXT = P6_HISTORICAL_NEWS_FINSEN_ABLATION_PROTOCOL_FREEZE_001
```

## Frozen upstream identities

```text
FINSEN_SOURCE_SHA = 8dc90aa6f1c5c12352bab6a17108f991114e386f
FINSEN_DATA_FILE = data.pptx/FinSen_US_Categorized_Timestamp.csv
FINSEN_DATA_BLOB_SHA = 594280f4d838313bd4ef37cfa33171979a22cda2
FINSEN_DATA_FILE_BYTES = 8970903
FINSEN_DATA_FILE_SHA256 = b802d281423a5655bc4d3ca2eacf72293591bb45a36e18d41ee2403b95b459b5
FINSEN_USE_CLASS = RESEARCH_CHALLENGER_ONLY
FINSEN_PIT_STATUS = DATE_ONLY_RESEARCH_CHALLENGER_NOT_STRICT_PIT
FINBERT_TRANSFORMERS_VERSION = 5.17.0
FINBERT_TORCH_VERSION = 2.14.0+cu130
FINBERT_MODEL_ID = ProsusAI/finbert
FINBERT_MODEL_REVISION = 4556d13015211d73dccd3fdd39d39232506f3e43
FINBERT_MODEL_WEIGHTS_SHA256 = e15a7b5738df7f17553399b6d94c6e2ff69c89245d066e8e5d183f5803a554e3
```

The repository license is MIT, while the README limits the supplied US data to
research-purpose use. The source was therefore used only as a private research
challenger. The raw CSV, paper PDF, news text, and row-level inference output
were deleted after the aggregate signal was sealed.

## Published method and narrow reproduction

The paper and repository identify `Content` as the news-text surface and
`ProsusAI/finbert` as the sentiment owner. FinBERT probabilities were resolved
by their native labels rather than positional assumptions. For news item `i`,
the reproduced score is:

```text
S_i = (-1 * P_negative) + (0 * P_neutral) + (1 * P_positive)
    = P_positive - P_negative

SAgg_d = arithmetic mean of S_i for every FinSen item on calendar date d
```

No title variant, alternative weighting, threshold, count feature, rolling
feature, or second sentiment candidate was evaluated.

```text
FINSEN_PUBLISHED_SENTIMENT_METHOD = CONTENT_TO_PROSUSAI_FINBERT_THREE_CLASS_PROBABILITIES_SCORE_P_POSITIVE_MINUS_P_NEGATIVE
FINSEN_PUBLISHED_DAILY_AGGREGATION_METHOD = ARITHMETIC_MEAN_OF_PER_NEWS_P_POSITIVE_MINUS_P_NEGATIVE
FINSEN_METHOD_REPRODUCTION_STATUS = PASS_EXACT_PAPER_FORMULA_CONTENT_INPUT_REPOSITORY_CORROBORATED
RESEARCH_FACTOR_COUNT = 1
RESEARCH_FACTOR_NAME = finsen_finbert_market_sentiment
CANONICAL_GRAIN = SESSION_GLOBAL
```

## Determinism and conservative session projection

A fixed 64-row sample was inferred twice on the same CUDA runtime. The two
row-level outputs were byte-identical with SHA-256
`18e5871f66be4e83872cc73d227e9ad22fe655c3d42109e102ab3fd0694c339c`.
The complete 14,240-row eligible inference produced SHA-256
`960d5a52e791c56f2338076f39acc09e0539fb8ff2e68a388b02f7b88825cef4`.

Each FinSen calendar date becomes visible on the first XNYS session strictly
after that date through the existing `aq_xnys_calendar` leaf. When multiple
calendar-date aggregates become visible on the same session, the latest source
calendar date is the one session state; this is a fixed temporal projection,
not an aggregation variant. No state is carried into a later session without
new upstream evidence. Sessions without evidence remain NULL.

```text
STRICT_NEXT_XNYS_PROJECTION = PASS
STRICT_NEXT_SESSION_FAILURE_COUNT = 0
EFFECTIVE_SESSION_COLLISION_POLICY = LATEST_SOURCE_CALENDAR_DATE_PER_EFFECTIVE_SESSION
EFFECTIVE_SESSION_COLLISION_COUNT = 100
SUPERSEDED_DAILY_SIGNAL_COUNT = 106
FORWARD_FILL = NO
BACKFILL = NO
ZERO_FILL = NO
```

## Bounded output and quality

```text
SOURCE_ROW_COUNT = 15534
UNIQUE_TITLE_COUNT = 12980
SOURCE_DATE_MIN = 2007-06-04
SOURCE_DATE_MAX = 2023-07-16
ELIGIBLE_2015_2023_ROW_COUNT = 14240
DATE_PARSE_FAILURE_COUNT = 0
CONTENT_EMPTY_COUNT = 0
FINBERT_INFERENCE_FAILURE_COUNT = 0
DAILY_SIGNAL_ROW_COUNT = 2109
XNYS_SESSION_COUNT = 2087
SESSION_MIN = 2015-04-01
SESSION_MAX = 2023-07-17
SESSION_WITH_SIGNAL_COUNT = 2003
SESSION_WITHOUT_SIGNAL_COUNT = 84
SESSION_SIGNAL_COVERAGE_RATE = 0.9597508385241974
RESEARCH_SIGNAL_SHA256 = 93bc6a62550accc0a4484e86d6f3af8242c69a6211a51ef40bb34d0c9bc60f48
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/historical-news-finsen-bounded-factor-poc-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 6e56cfd78213eef31b256a4362f70352cfc37afb5e6ba9517b7b4bf73ae5c2f5
RAW_NEWS_RETENTION = NONE_AFTER_SIGNAL_SEAL
```

The private session table passed Pandera schema/value-range/uniqueness checks,
exact XNYS-session checks, strict-next visibility checks, and a repeat-build
hash comparison. It is research-factor evidence only; it has not been joined
to BASE_157, broadcast to securities, or passed to any model.

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
FINAL_CLASSIFICATION = PASS_P6_HISTORICAL_NEWS_FINSEN_BOUNDED_FACTOR_POC
```
