# P6 News V1 real-time upstream streaming stack POC 001

## Outcome

PR #98 was squash-merged at
`fec1fab07e0be1bf7c446a8bb58d7c861e6bd70b`. The bounded private POC proves
the minimum upstream-owned shape for real-time company news and separate
official-event feeds. It does not create a news engine, entity resolver,
crawler, WebSocket framework, feed framework, sentiment model, feature family,
or trading rule.

```text
FINAL_CLASSIFICATION = PASS_WITH_ALPACA_LIVE_CREDENTIAL_BLOCKER
P6_NEWS_COMPANY_ENTITY_RESOLUTION_LANE = CLOSED_NOT_REQUIRED_FOR_REALTIME_COMPANY_NEWS
REALTIME_NEWS_PUSH_ARCHITECTURE = UPSTREAM_OWNED
NEW_PRODUCTION_LOC = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Alpaca upstream interface and credential gate

The isolated runtime is `D:/AQ_ENVS/p6-news-realtime-poc`, CPython `3.11.16`,
with `alpaca-py 0.44.0`. The installed public
`alpaca.data.live.news.NewsDataStream` constructor and
`subscribe_news(handler, *symbols)` signatures were inspected and the `"*"`
subscription was registered without opening a socket. Installed upstream
source owns its reconnect/backoff and stale-socket mechanics; AQ added none.
The package is the [official Alpaca Python SDK](https://github.com/alpacahq/alpaca-py).

No authorized Alpaca credential pair was present in the checked Windows
process/user/machine environments, WSL process environment, or existing P6
private credential-file inventory. Only boolean presence was recorded; no
secret value, hash, prefix, or suffix was read into evidence. Therefore no
WebSocket connection or authentication was attempted and no message was
fabricated. The wildcard live interface is proven, while the live session
remains credential-blocked.

```text
ALPACA_PY_VERSION = 0.44.0
ALPACA_NEWS_STREAM_CLASS = alpaca.data.live.news.NewsDataStream
ALPACA_CREDENTIAL_AVAILABLE = NO
ALPACA_STREAM_CONNECTION_STATUS = NOT_ATTEMPTED_CREDENTIAL_REQUIRED
ALPACA_STREAM_AUTH_STATUS = NOT_ATTEMPTED_CREDENTIAL_REQUIRED
ALPACA_STREAM_SUBSCRIPTION_STATUS = STATIC_INTERFACE_PROVEN_LIVE_BLOCKED_CREDENTIAL_REQUIRED
ALPACA_SUBSCRIPTION = *
LIVE_OBSERVATION_MINUTES = 0
LIVE_MESSAGES_TOTAL = 0
LIVE_MESSAGES_WITH_SYMBOLS = 0
LIVE_MESSAGES_MATCHING_DEV_UNIVERSE = 0
DUPLICATE_PROVIDER_ARTICLE_ID_COUNT = 0
FABRICATED_RECEIVE_TIMESTAMP_COUNT = 0
COMPANY_NEWS_SECURITY_ASSOCIATION_OWNER = ALPACA_BENZINGA_PROVIDER_NATIVE_SYMBOLS
CUSTOM_WEBSOCKET_RECONNECT_CODE = NO
REALTIME_COMPANY_NEWS_OWNER = BLOCKED_CREDENTIAL_REQUIRED
```

The existing pre-2025 P1 `InstrumentEpisodeV1` authority was read only to
freeze a future provider-symbol routing set: source SHA-256
`5d2732f8a6187bdab342ff09ff3ecdcc7e66d9e755bc364a8f3f822923d877e1`
and 819 unique symbols. No P2 V2 sealed-OOS surface was read. Provider-native
`symbols[]`, rather than headline or organization-name inference, remains the
only candidate company-news security association.

## FinBERT authority reuse

The previously deployed Transformers runtime and pinned
`ProsusAI/finbert` revision were verified in place. The model file, config, and
tokenizer identities were hashed without reinstalling or invoking the obsolete
FinBERT repository runtime. With no live Alpaca message, inference count is
zero and latency medians are not applicable; no synthetic headline was used to
manufacture an operational result.

```text
FINBERT_VERSION = TRANSFORMERS_5.17.0
FINBERT_MODEL_REVISION = 4556d13015211d73dccd3fdd39d39232506f3e43
FINBERT_ANALYZED_MESSAGE_COUNT = 0
FINBERT_POSITIVE_COUNT = 0
FINBERT_NEUTRAL_COUNT = 0
FINBERT_NEGATIVE_COUNT = 0
MEDIAN_FINBERT_INFERENCE_MS = NOT_APPLICABLE_NO_LIVE_MESSAGES
MEDIAN_RECEIVED_TO_ANALYSIS_COMPLETE_MS = NOT_APPLICABLE_NO_LIVE_MESSAGES
LANGEXTRACT_INFERENCE_COUNT = 0
LLM_CALL_COUNT = 0
FINANCIAL_SENTIMENT_OWNER = TRANSFORMERS_PLUS_PINNED_PROSUSAI_FINBERT
```

## Official-event lanes

The POC used `feedparser 6.0.12`, not an AQ XML parser. One bounded retrieval
of the Federal Reserve all-press-release feed returned 20 entries. One bounded
retrieval of the BLS latest-numbers feed returned one entry. Both retained only
hashed provider identity plus native RSS `published`/`updated` fields and the
separate actual AQ retrieval instant; no feed body was retained. The sources
are the [Federal Reserve official feeds](https://www.federalreserve.gov/feeds/feeds.htm)
and [BLS official feeds](https://www.bls.gov/feed/).

```text
FED_FEED_ACCESS = PASS
FED_LATEST_ITEM_COUNT = 20
FED_NATIVE_TIMESTAMP_SEMANTICS = RSS_PUBLISHED_AND_UPDATED_FIELDS_AS_SUPPLIED
BLS_FEED_ACCESS = PASS
BLS_LATEST_ITEM_COUNT = 1
BLS_NATIVE_TIMESTAMP_SEMANTICS = RSS_PUBLISHED_AND_UPDATED_FIELDS_AS_SUPPLIED
RSS_ATOM_PARSER_OWNER = FEEDPARSER
RSS_ATOM_PARSER_VERSION = 6.0.12
OFFICIAL_MACRO_EVENT_OWNER = FED_BLS_NATIVE_FEEDS
```

The existing EdgarTools `5.58.0` runtime exposes the native
`get_current_filings(form='', owner='include', page_size=40)` interface, matching
the upstream [current-filings guide](https://dgunning.github.io/edgartools/guides/current-filings/).
Its private SEC identity is not currently configured. The POC therefore issued
zero SEC requests and records the identity blocker rather than inventing a user
agent or writing an SEC poller/parser.

```text
SEC_CURRENT_FILINGS_OWNER = EDGARTOOLS_NATIVE_CURRENT_FILINGS
SEC_CURRENT_FILINGS_POC_STATUS = BLOCKED_PRIVATE_EDGAR_IDENTITY_REQUIRED
SEC_CURRENT_FILINGS_RECORD_COUNT = 0
SEC_CURRENT_FILINGS_NETWORK_REQUEST_COUNT = 0
```

## Evidence and safety

Private evidence is retained at
`D:/AQ_DATA/P6/news-v1-realtime-upstream-streaming-stack-poc-001`. It contains
runtime and credential-presence reports, empty typed Parquet relations for the
blocked live lane, official-feed metadata, EdgarTools interface evidence,
FinBERT runtime identities, the routing authority, and deterministic checksums.
No secret, article corpus, full article body, or private record enters Git.

```text
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 72e95f0b6ed4442340a369804bf8d5460fb70e13a47bdbe392214ddd4b81571f
AQ_RECEIVED_AT_TIMEZONE = UTC
AQ_RECEIVED_AT_PRECISION = RUNTIME_INSTANT
POC_BACKGROUND_PROCESS_COUNT_AFTER_CLOSE = 0
GDELT_REALTIME_PRIMARY_OWNER = NO
GDELT_COMPANY_ENTITY_RESOLUTION_USED = NO
AQ_NEWS_CRAWLER_REQUIRED = NO
AQ_WEBSOCKET_ENGINE_REQUIRED = NO
AQ_ENTITY_RESOLUTION_ENGINE_REQUIRED = NO
AQ_SENTIMENT_MODEL_REQUIRED = NO
AQ_RSS_PARSER_REQUIRED = NO
NEWS_FEATURE_FAMILY_SELECTED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
ORDER_COUNT = 0
BROKER_ACTION_COUNT = 0
CAPITAL_AT_RISK = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
```

Because the upstream push interface and official-feed lane pass but live Alpaca
authentication could not be exercised, the smallest next task is an access and
machine-readable-signal decision, not a production news platform:

```text
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_ALPACA_ACCESS_AND_MACHINE_READABLE_SIGNAL_DECISION_001
```
