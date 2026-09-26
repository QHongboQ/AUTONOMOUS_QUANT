# P6 News V1 whole-upstream owner selection 001

## Decision

This architecture-selection audit compared exactly four candidate whole paths.
It made no provider-data request, opened no WebSocket, created no account,
purchased no data, and added no production code.

The institutional reference owner is RavenPack Company News Factors plus News
Analytics. It is the smallest documented upstream that already owns company
identity, point-in-time news, sentiment, relevance, novelty, event taxonomy,
news-volume factors, historical archives, and real-time delivery. LSEG Machine
Readable News plus News Analytics is a second technically valid whole owner.
Neither is deployable by AQ now: both require commercial contact/entitlement,
public prices are absent, and the applicable license has not been established
for this personal-capital research project.

The two QuantConnect paths are technically coherent but cannot satisfy the
required Qlib handoff under the public download terms. QuantConnect states that
downloaded datasets are for the licensed organization's internal LEAN use and
must not be converted to another format. AQ therefore cannot treat a Parquet,
Arrow, CSV, or DuckDB export into Qlib as authorized without a different
contract. No license inference or workaround is permitted.

```text
ACTIVE_PHASE = P6_NEWS_MACRO_SKILLS
P6_MACRO_V1 = CLOSED_NO_MEASURABLE_INCREMENTAL_VALUE
P6_COMPANY_NEWS_PATCHWORK_APPROACH = RETIRED
CURRENT_P6_OBJECTIVE = COMPANY_NEWS_V1_CLOSEOUT_DECISION

INSTITUTIONAL_REFERENCE_OWNER = RAVENPACK_COMPANY_NEWS_FACTORS_AND_NEWS_ANALYTICS
DEPLOYABLE_COMPANY_NEWS_OWNER = NONE
SELECTED_COMPANY_NEWS_WHOLE_OWNER = NONE
GDELT_COMPANY_NEWS_GLUE_ROLE = RETIRED
ALPACA_DIRECT_ROLE = REALTIME_DIAGNOSTIC_OR_P9_FALLBACK
FINBERT_ROLE_AFTER_SELECTION = CHALLENGER_ONLY_NO_SELECTED_HISTORICAL_OWNER

CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_COMPANY_NEWS_ACCESS_OR_CLOSEOUT_DECISION_001
FINAL_CLASSIFICATION = PASS_P6_NEWS_V1_WHOLE_UPSTREAM_OWNER_SELECTION
```

## Hard-gate comparison

| Candidate | Classification | Historical / live | Security identity | PIT authority | Native analytics | Access and Qlib handoff |
|---|---|---|---|---|---|---|
| RavenPack Company News Factors + News Analytics | `VALID_WHOLE_OWNER_BUT_ACCESS_BLOCKED` | Factors since 2001; 20+ year analytics archive; real-time | RavenPack reference data / knowledge graph, point-in-time tickers and security identifiers, dead and survivor companies | `NATIVE_WITH_DOCUMENTED_LIMITATION`; public material proves point-in-time millisecond records but not the complete revision/deletion contract | Sentiment, relevance, novelty, event taxonomy, and news-volume factors are native | Trial/sales or institutional access; no public price or project license. CSV/API/Snowflake is technically simple, but legal permission is unproven. |
| LSEG Machine Readable News + News Analytics | `VALID_WHOLE_OWNER_BUT_ACCESS_BLOCKED` | News archive since 1996; analytics since 2003; real-time | RIC, PermID, and standard symbology | `NATIVE`; normalized, enriched, point-in-time news with millisecond timestamps | Sentiment, relevance, novelty, significance, volume, and classification are native | Sales contact and entitlement required; no public price or project license. JSON/tabular/API/SFTP handoff is technically simple, but legal permission is unproven. |
| QuantConnect LEAN + Benzinga News | `REJECTED_LICENSE_OR_EXPORT_INCOMPATIBLE` | Official page conflicts between January 2016 and September 2017; conservatively use September 2017, so the 2015-04-01 window is left-truncated; live stream exists | QuantConnect US Equity Security Master | `NATIVE_WITH_DOCUMENTED_LIMITATION`; `BenzingaNews.EndTime` is `UpdatedAt`, while the public history-start statement conflicts | Categories/tags are native; sentiment, relevance, and novelty are not | Cloud is listed at USD 120/month; on-premise at 10 QCC/file plus Security Master. Official download terms prohibit format conversion, blocking the Qlib handoff. |
| QuantConnect LEAN + Tiingo News | `REJECTED_LICENSE_OR_EXPORT_INCOMPATIBLE` | January 2014; historical `History()` and live stream | QuantConnect US Equity Security Master | `NATIVE`; `CrawlDate` is Tiingo's own database-ingestion time and LEAN uses the mapped data path | Company/topic/asset tags are native; sentiment, relevance, and novelty are not | Cloud is listed free; on-premise at 25 QCC/file plus Security Master. Official download terms prohibit format conversion, blocking the Qlib handoff. |

No candidate was rescued with a multi-provider patchwork. RavenPack and LSEG
remain valid commercial whole owners, but `TECHNICALLY_VALID` is not treated as
`ACCESSIBLE_TO_THIS_PROJECT`. QuantConnect's internal-LEAN license boundary is
not reinterpreted as permission to create a Qlib feature table.

## Official evidence

RavenPack documents Company News Factors with six daily snapshots, history
since 2001, more than 100,000 listed companies, and native document/event
factors built from relevance, novelty, sentiment, event categories, and volume
([Company News Factors](https://marketing-prod.ravenpack.com/products/edge/factors/company-news)).
Its machine-readable News Analytics documentation records native entity/event
detection, entity mapping, real-time analysis, and millisecond-timestamped
history ([Machine-Readable News](https://www.ravenpack.com/blog/machine-readable-news/)).
RavenPack research explicitly describes point-in-time ticker/security
identifiers and inclusion of dead and survivor companies
([event-trading study](https://www.ravenpack.com/research/event-trading-using-market-response/)).
Delivery is available through historical queries, real-time API, and Snowflake
([Edge delivery](https://www.ravenpack.com/products/edge/delivery)). Public
access is a request/trial flow; product-license terms and price are not public.

LSEG describes Machine Readable News as normalized, enriched, point-in-time
news over 45,000+ companies, with millisecond timestamps and RIC/PermID tags
([MRN fact sheet](https://www.lseg.com/content/dam/data-analytics/en_us/documents/fact-sheets/lseg-machine-readable-news.pdf)).
The current product page states that the News Archive reaches 1996 and News
Analytics reaches 2003, with real-time and delayed point-in-time JSON delivered
through streaming, request-response, or bulk files
([Machine Readable News](https://www.lseg.com/en/data-analytics/financial-news-services/machine-readable-news)).
The developer product page confirms native sentiment, relevance, novelty,
volume, classification, real-time JSON, archive JSON/tabular, API, and SFTP
([News Analytics](https://developers.lseg.com/en/product/news/news_analytics)).
Access is explicitly a sales-contact flow; price and the applicable AQ license
are not public.

QuantConnect documents the Security Master as covering splits, dividends,
delistings, mergers, and ticker changes since January 1998
([auxiliary data](https://www.quantconnect.com/docs/v2/cloud-platform/datasets/quantconnect/auxiliary-data)).
The Benzinga and Tiingo feeds both depend on it and support native historical
`History()` plus live delivery
([Benzinga](https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/benzinga/benzinga-news-feed),
[Tiingo](https://www.quantconnect.com/docs/v2/writing-algorithms/datasets/tiingo/tiingo-news-feed)).
The official implementations additionally prove updated-time emission for
Benzinga and Tiingo-native crawl time for Tiingo at source identities
`cf363d2cc3357a932cd7f57b5666c1c001088f1d` and
`7acf0b37a3659ff687bfc66fb50867d62c386fd1`.
The decisive boundary is the public licensing rule: a download is for internal
LEAN use and may not be converted to another format
([QuantConnect licensing](https://www.quantconnect.com/docs/v2/cloud-platform/datasets/licensing)).

## Ownership and non-actions

Because no owner passes both access/license and Qlib-export gates, the selected
production ownership fields remain `NONE`. RavenPack is a reference, not a
deployed dependency. FinBERT is not forced into the architecture and remains a
challenger only. Direct Alpaca remains bounded to prior real-time diagnostic
evidence or a future P9 fallback. GDELT remains eligible only for a separately
authorized global/market/geopolitical news lane.

```text
SELECTED_HISTORICAL_REALTIME_SAME_OWNER = NO
SELECTED_SECURITY_MASTER_OWNER = NONE
SELECTED_PIT_TIME_AUTHORITY = NONE
SELECTED_SENTIMENT_OWNER = NONE
SELECTED_RELEVANCE_OWNER = NONE
SELECTED_NOVELTY_OWNER = NONE
SELECTED_EVENT_TAXONOMY_OWNER = NONE

AQ_NEWS_ENGINE_CREATED = NO
AQ_ENTITY_RESOLUTION_ENGINE_CREATED = NO
AQ_TIMESTAMP_ENGINE_CREATED = NO
AQ_SECURITY_MASTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
NEWS_ARTICLE_DOWNLOAD_COUNT = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
REALTIME_WEBSOCKET_SESSION_COUNT = 0
ORDER_COUNT = 0
BROKER_ACTION_COUNT = 0
CAPITAL_AT_RISK = 0
P2_V2_SEALED_OOS_ACCESSED = NO
```

Private evidence is retained at
`D:/AQ_DATA/P6/news-v1-whole-upstream-owner-selection-001`; its deterministic
evidence-set SHA-256 is
`f273ed8b89512e9f88ba62d57881de59fa80f59cd1fc0737c21ba2e45b60006c`.

The next task is an explicit access-or-closeout decision. It may decide whether
to pursue a RavenPack/LSEG commercial license that expressly permits the Qlib
handoff, or close Company News V1 for this phase. It must not restart the
Alpaca/GDELT patchwork or silently reinterpret QuantConnect's license.
