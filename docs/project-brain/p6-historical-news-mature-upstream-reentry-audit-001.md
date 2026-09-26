# P6 Historical News Mature-Upstream Reentry Audit 001

## Decision

This bounded audit reopens P6 only for one research-challenger path. It does
not establish a certified production-PIT historical news owner and it does not
authorize a news crawler, entity resolver, signal engine, model run, or
ablation.

```text
P6_CLOSEOUT_CANDIDATE = PR_106_HELD_PENDING_FINAL_HISTORICAL_NEWS_REENTRY
P6_STATUS = REOPENED_BOUNDED_HISTORICAL_NEWS_RESEARCH
STRICT_PRODUCTION_PIT_READY = NO
BOUNDED_RESEARCH_POC_READY = YES
CURRENT_DEVELOPMENT_NEXT = P6_HISTORICAL_NEWS_SELECTED_UPSTREAM_BOUNDED_FACTOR_POC_001
```

## Frozen candidate census

| Candidate | Frozen source SHA | Classification | Decisive boundary |
| --- | --- | --- | --- |
| FNSPID | `4054842ec476953b30ee874d4b7e8eea786a21fa` | `BLOCKED_LICENSE_AMBIGUITY` | Repository statements conflict; the dataset card and LICENSE are CC BY-NC 4.0. Publication timestamps and ticker attachment do not prove strict PIT identity. |
| FinRL-DeepSeek | `5c21a923214bca6370800efd45f8c6c1ef776ae7` | `VALID_REFERENCE_ONLY` | Signal construction is separable, but it depends on FNSPID plus a hosted DeepInfra DeepSeek-V3 endpoint whose model revision is not frozen. |
| FinSen | `8dc90aa6f1c5c12352bab6a17108f991114e386f` | `SELECTED_BOUNDED_RESEARCH_CANDIDATE` | The public US research benchmark has 15,534 global-market news rows, date-only timing, and a documented FinBERT daily aggregation method. It is suitable only for a bounded research challenger. |
| TradeTheEvent | `51befedf01a7d5425790f45e2f2931706b2f8e1d` | `VALID_REFERENCE_ONLY` | The paper supplies a useful 11-event taxonomy, but the repository has no license and its current Yahoo ticker-string matching is not historical identity authority. |
| FinGPT forecasting | `fdb04c9a273d1ccc3764b09b8e3ed1e708e57566` | `VALID_REFERENCE_ONLY` | The released DOW30 forecaster is a natural-language challenger, not a factor/data owner; sampling and basic-financial availability are not PIT-frozen. |

## Selected bounded composition

```text
SELECTED_HISTORICAL_NEWS_DATA_OWNER = FINSEN_US_RESEARCH_ONLY_BENCHMARK
SELECTED_NEWS_SIGNAL_METHOD_OWNER = PROSUSAI_FINBERT_VIA_FINSEN_DAILY_AGGREGATION_METHOD
SELECTED_NEWS_PREDICTION_RESEARCH_PATH = FINSEN_GLOBAL_MARKET_DAILY_SENTIMENT_TO_QLIB_INCREMENTAL_ABLATION
PREFERRED_CANDIDATE_FACTOR_SURFACE = news_sentiment
```

FinSen is a global-market candidate rather than a company-news owner. The
next POC may test one daily market sentiment series and a thin session/Qlib
handoff. It must retain date-only timing as a research limitation and may not
promote the result to certified production PIT. No entity resolution is needed
for this bounded market-level path.

## Evidence boundaries

FNSPID documents 15,698,563 news records, approximately 29.7 million price
records, 4,775 companies, and 1999–2023 coverage. Its bounded Hugging Face
preview exposed publication-date, title, symbol, URL, publisher, author, and
summary fields but no `first_available_at`, `scraped_at`, or `ingested_at`.

FinRL-DeepSeek exposes `llm_sentiment` and `llm_risk` construction separately
from PPO/CPPO, but uses `deepseek-ai/DeepSeek-V3` through DeepInfra without a
frozen provider snapshot. TradeTheEvent documents 9,721 token-annotated items
and 303,893 minute-timestamped trading-benchmark items. FinGPT's released
forecaster covers DOW30 from 2022-12-30 through 2023-09-01; its final model
input removes the future-return label, while its upstream sampling and basic
financial availability remain insufficiently frozen for AQ PIT authority.

The audit used at most 500 transient rows per inspected dataset. No standalone
full corpus was acquired. The shallow FinSen source checkout included its
bundled 15,534-row US research CSV; it was inspected read-only and removed with
all temporary source checkouts. No raw news row is retained.

```text
MAX_NEWS_ROWS = 500
MAX_RETAINED_RAW_NEWS_ROWS = 0
NEWS_FULL_DATASET_DOWNLOAD_COUNT = 0
AQ_OUTCOME_DATA_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEWS_CRAWLER_REQUIRED = NO
AQ_ENTITY_RESOLUTION_ENGINE_REQUIRED = NO
AQ_NEWS_SIGNAL_ENGINE_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/historical-news-mature-upstream-reentry-audit-001
```

PR #106 remains open and unmodified as the frozen closeout candidate. The
reentry POC must not merge or close it.
