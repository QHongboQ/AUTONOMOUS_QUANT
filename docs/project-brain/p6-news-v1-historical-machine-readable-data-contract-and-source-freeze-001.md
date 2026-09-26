# P6 News V1 historical machine-readable data contract and source freeze 001

## Decision

The bounded historical source contract is blocked, without weakening PIT
semantics. Official Alpaca/Benzinga historical News is a viable machine-readable
content and security-association source, but this POC found no exact URL overlap
with bounded GDELT GKG evidence. Because Alpaca `created_at` and `updated_at`
are not admitted as historical first-availability authority, no returned article
may enter News V1.

```text
FINAL_CLASSIFICATION = BLOCKED_HISTORICAL_SAFE_AVAILABILITY_CORROBORATION
NEWS_EVIDENCE_V1_CONTRACT_FROZEN = NO
NEWS_FEATURE_FAMILY_SELECTED = NO
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_HISTORICAL_SOURCE_CLOSEOUT_DECISION_001
```

## Phase correction

Real-time infrastructure exploration is sufficient for P6. Its productionization
and paper execution are deferred to P9. Macro V1 is closed with no measurable
incremental value. P6 now remains focused on historical PIT news and the future
frozen comparison against `BASE_157`; this task performed no feature design,
training, prediction, backtest, or ablation.

```text
ACTIVE_PHASE = P6_NEWS_MACRO_SKILLS
ACTIVE_DEVELOPMENT = P6_NEWS_INFORMATION_INTELLIGENCE
P6_MACRO_V1 = CLOSED_NO_MEASURABLE_INCREMENTAL_VALUE
REALTIME_NEWS_INFRASTRUCTURE_EXPLORATION = SUFFICIENT_FOR_P6
REALTIME_NEWS_PRODUCTIONIZATION = DEFERRED_TO_P9
PAPER_TRADING_EXECUTION = DEFERRED_TO_P9
CURRENT_P6_OBJECTIVE = NEWS_V1_HISTORICAL_PIT_DATA_AND_FACTOR_ABLATION
```

## Deterministic P1 population

Selection occurred before querying news. Within each frozen stratum, eligible
episodes were ordered by immutable `episode_id`; every chosen episode had at
least 121 XNYS sessions in the authorized 2015-04-01 through 2024-12-31 range.
The early anchor was session 60 after the eligible start and the late anchor was
session 60 before the eligible end. Each query covered exactly 14 calendar days
inside the episode.

| Stratum | Episodes | PIT-admissible episodes |
|---|---:|---:|
| ordinary continuous | 5 | 0 |
| ticker/name change | 3 | 0 |
| inactive/acquired/delisted | 2 | 0 |
| multi-share-class/shared-CIK | 2 | 0 |

```text
EPISODE_SAMPLE_COUNT = 12
EPISODE_WINDOW_COUNT = 24
CURRENT_TICKER_BACKFILL_COUNT = 0
```

## Alpaca/Benzinga historical result

The existing current-user DPAPI credential was decrypted only in process
memory and injected only into the child process. Official `alpaca-py 0.44.0`
`NewsClient`/`NewsRequest` executed 24 historical queries with
`include_content=False`. All succeeded; the 174 returned rows represent 173
unique provider articles. All rows carried native `symbols[]`, and every row
contained its requested historical ticker. No current-ticker fallback, company
name matching, CIK inference, article fetch, or body retention occurred.

```text
ALPACA_HISTORICAL_NEWS_STATUS = PASS_REAL_2015_2024_BOUNDED_WINDOWS
ALPACA_HISTORICAL_START = 2015
ALPACA_UNDERLYING_NEWS_PROVIDER = BENZINGA
ALPACA_CREATED_AT_ROLE = ARTICLE_METADATA_TIME_NOT_PIT_AUTHORITY
ALPACA_UPDATED_AT_ROLE = ARTICLE_METADATA_TIME_NOT_PIT_AUTHORITY
ALPACA_SUCCESSFUL_WINDOW_COUNT = 24
ALPACA_FAILED_WINDOW_COUNT = 0
ALPACA_ARTICLE_COUNT = 174
ALPACA_UNIQUE_ARTICLE_COUNT = 173
ALPACA_ARTICLES_WITH_SYMBOLS = 174
ALPACA_REQUESTED_TICKER_PRESENT_COUNT = 174
ALPACA_REQUESTED_TICKER_ABSENT_COUNT = 0
ALPACA_ARTICLE_URL_PRESENT_COUNT = 174
```

## GDELT exact-URL boundary

The only admitted join was byte-for-byte equality between Alpaca `url` and
GKG `V2DOCUMENTIDENTIFIER`. Candidate 15-minute GKG batches were generated
solely from the returned article times, scored deterministically by how many
returned articles they could cover, and then processed within the frozen
compressed-byte cap. A standard-library CSV field-limit failure on the first
archive consumed 8,654,874 bytes; it was included in total accounting before a
bounded reader correction and replay. The final total was 267,567,105 bytes,
below 256 MiB by 868,351 bytes. Twenty-six replay archives parsed successfully.
No ZIP was persisted and no article URL was requested.

No exact URL matched. Therefore the measured exact-overlap rate is zero, every
Alpaca row remains `NOT_PIT_ADMISSIBLE_FOR_NEWS_V1`, and the conceptual
`NewsEvidenceV1` contract is not frozen. Provider timestamps cannot substitute
for GDELT safe availability.

```text
GDELT_URL_MATCH_SEMANTICS = EXACT_STRING_EQUALITY_ONLY
GDELT_ADDITIONAL_COMPRESSED_BYTES = 267567105
GDELT_MAX_ADDITIONAL_COMPRESSED_BYTES = 268435456
GDELT_BUDGET_BREACH_COUNT = 0
GDELT_SOURCE_ARTICLE_REQUEST_COUNT = 0
RAW_GKG_ZIP_RETAINED = NO
GDELT_EXACT_URL_MATCH_COUNT = 0
GDELT_EXACT_URL_MATCH_RATE = 0.0
PIT_ADMISSIBLE_ARTICLE_COUNT = 0
PIT_ADMISSIBLE_EPISODE_COUNT = 0
PIT_ADMISSIBLE_WINDOW_COUNT = 0
```

## Ownership and safety

Alpaca/Benzinga remains the bounded content and native security-tag source;
GDELT remains the required historical safe-availability owner. The zero overlap
means the composition is not admitted, not that AQ may introduce URL
normalization, an entity resolver, a crawler, or timestamp heuristics. The
existing P1 episodes remain security identity authority. The pinned FinBERT
stack remains a future sentiment leaf and was not executed.

```text
COMPANY_NEWS_CONTENT_AND_SECURITY_ASSOCIATION_OWNER = ALPACA_BENZINGA_HISTORICAL_NEWS
HISTORICAL_NEWS_SAFE_AVAILABILITY_OWNER = GDELT_GKG_EXACT_URL_CORROBORATION
HISTORICAL_SECURITY_IDENTITY_OWNER = P1_INSTRUMENT_EPISODE_V1
FINANCIAL_SENTIMENT_OWNER = TRANSFORMERS_PLUS_PINNED_PROSUSAI_FINBERT
P6_NEWS_ENTITY_RESOLUTION_LANE = NOT_REOPENED_SOURCE_CONTRACT_BLOCKED
GDELT_COMPANY_ENTITY_RESOLUTION_USED = NO
AQ_ENTITY_RESOLUTION_ENGINE_CREATED = NO
AQ_NEWS_CRAWLER_CREATED = NO
AQ_GENERIC_NEWS_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-historical-machine-readable-data-contract-and-source-freeze-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 49856e97c80db6150b1566c25ee72efa12ee30934d4c9b55eb0a97026908f807
TEST_RESULT = PASS
```
