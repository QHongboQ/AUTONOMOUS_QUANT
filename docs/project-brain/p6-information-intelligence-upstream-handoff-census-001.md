# P6 information-intelligence upstream handoff census 001

## Scope and authority

PR #72 squash-merged the completed P5 filing-feature historical
materialization and ablation design into main at
`2e194950e70bc3860e9d5b41dd9c416a6cadd25b` on
`2026-09-21T03:52:06Z`. P5 upstream selection is therefore closed. EdgarTools
remains the primary filing, fundamentals, XBRL, document, and notes owner. The
historical build remains an independent running process and was not stopped,
restarted, queried, or given competing SEC work by this census.

This document is future-phase preaudit evidence: P6 is not the active project
phase. It is a source, documentation, and public-interface audit only. It does
not install an upstream, download a model, retrieve a news item or macro
observation, call an LLM, create a feature, train a model, or run a backtest.

```text
P5_UPSTREAM_HANDOFF_STATUS = COMPLETE_WITH_POST_BUILD_HYGIENE
P5_NEW_GENERIC_ENGINE_REQUIRED = NO
P5_UPSTREAM_HANDOFF_BLOCKER_COUNT = 0
P5_PRIMARY_FILING_OWNER = EDGARTOOLS
P5_PRIMARY_FUNDAMENTALS_OWNER = EDGARTOOLS
P5_XBRL_OWNER = EDGARTOOLS
P5_DOCUMENT_OWNER = EDGARTOOLS
P5_NOTES_OWNER = EDGARTOOLS
P6_DUPLICATE_SEC_STACK = NO
```

The active project phase remains P5 Fundamental Intelligence. Completing an
upstream census for a future phase does not satisfy the P5 exit condition or
authorize P6 deployment.

```text
CURRENT_PHASE = P5_FUNDAMENTAL_INTELLIGENCE
P5_COMPLETE = NO
P5_UPSTREAM_HANDOFF = COMPLETE_WITH_POST_BUILD_HYGIENE
P5_HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
P6_PREAUDIT_COMPLETE = YES
P6_ACTIVE = NO
P6_SELECTED_UPSTREAM_DEPLOYMENT_STARTED = NO
P5_EXIT_CONDITION_SATISFIED = NO
P6_PHASE_ENTRY_AUTHORIZED = NO
```

The historical-build `_NetworkMeter`/HTTPX instrumentation and transient
attachment override/cache remain post-build hygiene candidates only. Neither
was changed here.

## Audit method and current source identities

The census inspected upstream repositories, current package metadata, public
interfaces, provider schemas, and official documentation at fixed source
identities. It made zero data requests to SEC, FRED/ALFRED, news providers, or
GDELT.

| Upstream | Audited identity | Access class | Audited role |
|---|---|---|---|
| OpenBB | Platform `4.7.3`, `OpenBB-finance/OpenBB` commit `3e071fcc2cd9f891cac6040ae60296dba76dab46` | `FREE_NO_KEY` core; data access is provider-dependent (`FREE_NO_KEY`, `FREE_API_KEY`, `FREEMIUM`, or `PAID_REQUIRED`) | Provider-normalizing gateway for news and the FRED release calendar; not a universal data or PIT authority. |
| TradingAgents | `0.5.0`, `TauricResearch/TradingAgents` commit `2d17df8da1536c121e4d7395ac5a5dcec9e96d6f` | `FREE_NO_KEY` code; data and LLM costs are provider-dependent | Information-intelligence challenger with structured reports, PIT-aware date windows, checkpoints, and decision logs. Not selected as a trading, execution, SEC, news-data, or macro-data owner. |
| FinGPT | `1.0.0`, `AI4Finance-Foundation/FinGPT` commit `cefb3a26b84a3a4c57868f1ca48fb0d9723fd28e` | `FREE_NO_KEY` code; model/runtime costs vary | Broad research collection and challenger for future extraction benchmarks; not a cohesive production owner. |
| ProsusAI FinBERT repository | Unversioned repository commit `44995e0c5870c4ab37a189d756550654ae87cdf0` | `FREE_NO_KEY` | Old training/runtime implementation is rejected; it depends on the obsolete `pytorch_pretrained_bert` path. |
| FinBERT model + Transformers | `ProsusAI/finbert` model revision `4556d13015211d73dccd3fdd39d39232506f3e43`; Transformers `5.17.0`, commit `d67c72935fc5eae6539a6c2fde8326dc9332b5fa` | `FREE_NO_KEY` | Selected narrow inference leaf for financial text sentiment, subject to a future bounded model/runtime POC. No weights were downloaded. |
| FRED/ALFRED | Official API and real-time-period documentation; no semantic package version | `FREE_API_KEY` | Authoritative macro series, releases, revisions, and vintage semantics. |
| fredapi | `0.5.2`, `mortada/fredapi` commit `d0a0ba3001ebbbceafdcbdd3eb23828f0537cdff` | `FREE_API_KEY` | Selected thin Python access leaf for FRED/ALFRED PIT observations and revisions. |
| GDELT 2.x | Official GDELT data/API documentation; service has no semantic package version | `FREE_NO_KEY` | Supplementary news discovery, seen/event metadata, and event-volume evidence; not an article-content or complete historical PIT authority. |
| gdeltdoc | `1.12.0`, `alex9smith/gdelt-doc-api` commit `41220163fbab99982e4dca3a05d25a95b49896d7` | `FREE_NO_KEY` | Thin client for the bounded GDELT DOC API surface; supplementary only. |

Authoritative references include the [OpenBB repository](https://github.com/OpenBB-finance/OpenBB),
the [TradingAgents repository](https://github.com/TauricResearch/TradingAgents),
the [FinGPT repository](https://github.com/AI4Finance-Foundation/FinGPT), the
[ProsusAI FinBERT model](https://huggingface.co/ProsusAI/finbert), the
[FRED API documentation](https://fred.stlouisfed.org/docs/api/fred/), the
[fredapi repository](https://github.com/mortada/fredapi), and the
[GDELT DOC API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/).

```text
P6_UPSTREAM_PROJECT_COUNT_AUDITED = 9
```

## Native behavior and PIT findings

### OpenBB

OpenBB is a mature provider gateway and interface owner. Its current news
standard models normalize publication datetime, title, author, excerpt, body,
URL, images, and associated symbols. The current providers include free,
freemium, and paid sources, so the gateway does not by itself establish data
authority, completeness, historical retention, or first-availability time.
`date` is documented as publication time, not first retrieval time.

The only current OpenBB earnings-call transcript implementation is the FMP
provider. Its normalized result includes symbol, year, quarter, date, and
content, but the provider access plan and historical provenance must be proven
in a later bounded POC. It is not selected by this static census.

OpenBB's FRED provider is not the macro PIT owner. In the audited source, its
series transformation deliberately removes `realtime_start` and
`realtime_end`; that loses the exact ALFRED vintage identity needed for
historical research. Its economic calendar remains useful as a release
calendar gateway, but official FRED documentation warns that source release
dates do not necessarily equal the precise instant that data became available
on FRED/ALFRED.

```text
OPENBB_STATUS = UPSTREAM_WHOLE_GATEWAY_NOT_PIT_AUTHORITY
OPENBB_CAN_PROVE_WHAT_WAS_KNOWN_WHEN = PARTIAL
```

### TradingAgents

The current TradingAgents source has materially improved its audit surface:
PIT-aware date-window utilities, an official FRED adapter that pins the
real-time period to the analysis date, Pydantic structured outputs,
checkpoint/resume, graph signatures, and decision logs. These make it a
credible challenger for information synthesis.

It is not a production source owner. Its own sentiment analyst documents that
Yahoo news, StockTwits, and Reddit inputs are recent feeds and are not archived
as of a historical date, so historical runs are not guaranteed point-in-time.
Its broader analyst stack also contains SEC/fundamental dataflows that would
duplicate P5 if adopted whole. A current upstream issue also records that
reports do not yet persist all exact source windows and item counts needed for
full reproducibility. AQ must therefore evaluate only a bounded information-
synthesis path supplied with already-authoritative inputs.

```text
TRADINGAGENTS_STATUS = CHALLENGER_INFORMATION_SYNTHESIS_ONLY
TRADINGAGENTS_CAN_PROVE_WHAT_WAS_KNOWN_WHEN = PARTIAL
TRADINGAGENTS_TRADING_EXECUTION_OWNER = NO
```

### FinGPT and FinBERT

FinGPT is a broad research repository spanning benchmarks, sentiment,
forecasting, RAG, multi-agent examples, report analysis, scripts, and
notebooks. That breadth overlaps TradingAgents, general LLM tooling, and the
narrow FinBERT sentiment leaf. It is useful as a future challenger corpus and
benchmark reference, but adopting the whole repository would add overlapping
runtime ownership without establishing source PIT authority.

The original ProsusAI FinBERT repository is not the correct runtime owner in
2026. Its training/runtime code is old, while the published Hugging Face model
remains directly usable through current Transformers. The selected leaf is
therefore the pinned model revision plus current Transformers inference, not a
copy of the old repository runtime. It emits positive, negative, and neutral
financial-text classifications. The source document's authoritative
`first_available_at` remains the feature availability time; inference time can
never replace it.

```text
FINGPT_STATUS = DEFER_BROAD_DUPLICATIVE_RESEARCH_RUNTIME
FINBERT_STATUS = UPSTREAM_LEAF_VIA_TRANSFORMERS_AND_PINNED_MODEL
FINGPT_CAN_PROVE_WHAT_WAS_KNOWN_WHEN = NO
FINBERT_CAN_PROVE_WHAT_WAS_KNOWN_WHEN = NO_SOURCE_AUTHORITY
```

### FRED/ALFRED and fredapi

Official FRED/ALFRED real-time periods are the source authority for what a
macro observation looked like at a historical vintage. `fredapi` exposes the
required thin access methods: latest series, first release, all releases,
as-of-date values, and vintage dates. It preserves observation date,
`realtime_start`, and value on revision results. No AQ revision engine or
macro HTTP client is needed.

The official FRED/ALFRED service remains the data authority; `fredapi` is only
the selected Python access leaf. OpenBB's FRED release calendar can be used as
a supplementary calendar interface, but neither a calendar date nor a later
corrected value may be substituted for ALFRED vintage evidence.

```text
FRED_ALFRED_STATUS = AUTHORITATIVE_MACRO_PIT_SOURCE
FREDAPI_STATUS = SELECTED_MACRO_PIT_ACCESS_LEAF
FRED_ALFRED_CAN_PROVE_WHAT_WAS_KNOWN_WHEN = YES
FREDAPI_CAN_PROVE_WHAT_WAS_KNOWN_WHEN = YES_WHEN_ALFRED_METHODS_USED
```

### GDELT

GDELT 2.x is useful for broad news/event discovery, seen timestamps, event
volume, and source URLs. The GDELT DOC API returns ranked article metadata and
timeline modes, but article-list results are capped, query windows and ranking
rules constrain reproducibility, and GDELT does not own the full article body
or guarantee that URLs remain retrievable. `seendate`/`DATEADDED` can establish
when GDELT observed or added an item, not necessarily the publisher's original
first availability. GDELT is therefore supplementary metadata rather than the
primary historical-news content or universal PIT owner.

```text
GDELT_STATUS = SUPPLEMENTARY_HISTORICAL_NEWS_METADATA
GDELT_CAN_PROVE_WHAT_WAS_KNOWN_WHEN = PARTIAL
```

## Capability ownership matrix

Every required capability has exactly one classification. `Primary path` is
an ownership recommendation, not an authorization to deploy or query it.

| # | Capability | Classification | Primary path | PIT finding / boundary |
|---:|---|---|---|---|
| 1 | `NEWS_DISCOVERY` | `UPSTREAM_WHOLE` | OpenBB news provider gateway | Mature normalized discovery interface; provider authority and access remain provider-specific. |
| 2 | `HISTORICAL_NEWS_DISCOVERY` | `SUPPLEMENTARY` | GDELT 2.x through gdeltdoc | Broad metadata/event discovery, not complete deterministic article history. |
| 3 | `NEWS_PUBLISHED_AT` | `UPSTREAM_LEAF` | OpenBB normalized provider result | Provider-supplied publication datetime only; validate per provider. |
| 4 | `NEWS_FIRST_AVAILABLE_AT` | `TRUE_UPSTREAM_GAP` | None selected | Publication time and GDELT seen time do not universally prove first retrievable time. |
| 5 | `NEWS_CONTENT_ACCESS` | `UPSTREAM_LEAF` | OpenBB provider result | Body/excerpt where the selected provider supplies it; URL alone is not sealed content. |
| 6 | `NEWS_METADATA_HASHING_INPUT` | `UPSTREAM_LEAF` | OpenBB normalized metadata | Supplies stable candidate inputs; AQ may later canonicalize/hash evidence identity. |
| 7 | `NEWS_EVENT_VOLUME` | `UPSTREAM_LEAF` | GDELT timeline/event data | Useful event-volume leaf; query/ranking identity must be sealed. |
| 8 | `MACRO_SERIES_ACCESS` | `UPSTREAM_WHOLE` | Official FRED/ALFRED via fredapi | Official source plus mature thin client. |
| 9 | `MACRO_RELEASE_CALENDAR` | `UPSTREAM_LEAF` | OpenBB FRED provider over official FRED release pages | Calendar only; it is not exact availability authority. |
| 10 | `MACRO_FIRST_RELEASE` | `UPSTREAM_LEAF` | fredapi | Native `get_series_first_release`. |
| 11 | `MACRO_REVISION_HISTORY` | `UPSTREAM_LEAF` | fredapi + ALFRED | Native all-releases relation with real-time dates. |
| 12 | `MACRO_AS_OF_DATE_QUERY` | `UPSTREAM_LEAF` | fredapi + ALFRED | Native as-of-date query. |
| 13 | `MACRO_VINTAGE_IDENTITY` | `UPSTREAM_LEAF` | Official ALFRED fields via fredapi | Preserve observation date and real-time/vintage identity. |
| 14 | `FINANCIAL_SENTIMENT` | `UPSTREAM_LEAF` | Transformers + pinned ProsusAI/finbert | Narrow three-class inference leaf; future frozen inference POC required. |
| 15 | `NEWS_SENTIMENT` | `UPSTREAM_LEAF` | Same FinBERT leaf on authoritative news text | Source timestamp/provenance remains external and mandatory. |
| 16 | `FILING_SENTIMENT` | `UPSTREAM_LEAF` | Same FinBERT leaf consuming EdgarTools text | EdgarTools remains the only SEC source/document authority. |
| 17 | `TEXT_CLASSIFICATION` | `UPSTREAM_LEAF` | Transformers | Mature inference runtime; model/version identity must be frozen per feature. |
| 18 | `STRUCTURED_TEXT_EXTRACTION` | `CHALLENGER` | FinGPT or bounded general-LLM POC | No production model/provider or structured evidence contract selected. |
| 19 | `LLM_DOCUMENT_ANALYSIS` | `DEFER` | `DEFER_PENDING_POC` | Source, prompt, model, output schema, and evidence identity are not frozen. |
| 20 | `MULTI_AGENT_INFORMATION_SYNTHESIS` | `CHALLENGER` | TradingAgents | Bounded challenger only after authoritative inputs replace its duplicate/current-only feeds. |
| 21 | `EARNINGS_CALL_ACCESS` | `DEFER` | OpenBB FMP transcript interface | Native gateway exists; plan, historical depth, and source provenance need a bounded POC. |
| 22 | `EARNINGS_CALL_TEXT_INTELLIGENCE` | `DEFER` | `DEFER_PENDING_ACCESS_AND_MODEL_POC` | Depends on authoritative transcript access and frozen model/prompt identity. |
| 23 | `SOCIAL_SENTIMENT` | `TRUE_UPSTREAM_GAP` | None selected | Current TradingAgents feeds are not a historical PIT archive. |

```text
P6_CAPABILITY_COUNT_AUDITED = 23
TRUE_UPSTREAM_GAP_COUNT = 2
PAID_REQUIRED_SELECTED_OWNER_COUNT = 0
```

The two gaps are deliberately not converted into AQ engines. A later task may
re-audit a mature upstream, contract the claim to a live-only feature, or
reject the feature.

## PIT fitness matrix

| Data-producing path | `CAN_PROVE_WHAT_WAS_KNOWN_WHEN` | Admissible use |
|---|---|---|
| Official FRED/ALFRED + fredapi ALFRED methods | `YES` | Historical macro observation vintages and revisions. |
| OpenBB FRED series | `NO` for exact vintages | Gateway/current use only; audited transformation drops real-time fields. |
| OpenBB FRED release calendar | `PARTIAL` | Release calendar metadata, not exact data-availability timestamp. |
| OpenBB news gateway | `PARTIAL` | Provider publication time and content where returned; no universal first-available proof. |
| GDELT 2.x / gdeltdoc | `PARTIAL` | Seen/event metadata and volume; not authoritative article first-availability or content. |
| TradingAgents current news/social feeds | `NO` for historical research | Current/live challenger only unless supplied with an external sealed PIT input bundle. |
| FinBERT / Transformers | `NO_SOURCE_AUTHORITY` | Deterministic inference on separately admitted text; never supplies source timing. |
| FinGPT | `NO_SOURCE_AUTHORITY` | Challenger methods only; source evidence must come from another owner. |

## Access and cost matrix

| Path | Cost class | Key / credential | Selection effect |
|---|---|---|---|
| OpenBB core | `FREE_NO_KEY` | None | Selected as gateway interface only. |
| OpenBB news providers | Provider-dependent | Varies | No paid provider selected; later POC must pick and freeze one provider. |
| Official FRED/ALFRED | `FREE_API_KEY` | Free FRED key | Selected macro authority. |
| fredapi | `FREE_NO_KEY` library | Uses FRED key | Selected macro client leaf. |
| GDELT 2.x / gdeltdoc | `FREE_NO_KEY` | None | Selected supplementary metadata leaf. |
| Transformers + ProsusAI/finbert | `FREE_NO_KEY` | None | Selected sentiment inference leaf; weights not downloaded here. |
| TradingAgents | `FREE_NO_KEY` code | LLM/data providers vary | Challenger only; no provider spend authorized. |
| FinGPT | `FREE_NO_KEY` code | Models/providers vary | Deferred research challenger. |
| OpenBB/FMP transcripts | `FREEMIUM` / plan-dependent | FMP key | Deferred; no subscription selected or purchased. |

## Overlap and substitution decisions

| Overlap | Decision |
|---|---|
| TradingAgents vs FinGPT | TradingAgents is the multi-agent synthesis challenger. FinGPT is deferred as a benchmark/extraction research collection. Neither owns source data. |
| TradingAgents vs OpenBB | OpenBB owns provider gateway interfaces; TradingAgents may later consume sealed gateway outputs but must not duplicate the gateway or P5 SEC paths. |
| FinGPT vs FinBERT | The pinned FinBERT model plus Transformers owns narrow sentiment inference. FinGPT does not duplicate that production role. |
| OpenBB FRED vs fredapi | fredapi + official ALFRED owns PIT macro observations/revisions. OpenBB owns only the supplementary release-calendar gateway. |
| OpenBB news vs GDELT | OpenBB is the primary normalized discovery gateway pending provider POC. GDELT is supplementary historical/event metadata and volume. |

No upstream in this census may replace EdgarTools as the P5 SEC source,
document, XBRL, attachment, exhibit, press-release, or notes authority.

## Recommended minimum topology

```text
MACRO_PIT_OWNER = OFFICIAL_FRED_ALFRED_VIA_FREDAPI
MACRO_RELEASE_CALENDAR_OWNER = OPENBB_FRED_PROVIDER_SUPPLEMENTARY_CALENDAR
NEWS_DISCOVERY_OWNER = OPENBB_NEWS_PROVIDER_GATEWAY_PENDING_BOUNDED_PROVIDER_POC
HISTORICAL_NEWS_OWNER = GDELT_2X_SUPPLEMENTARY_ONLY
FINANCIAL_SENTIMENT_OWNER = HUGGINGFACE_TRANSFORMERS_PLUS_PINNED_PROSUSAI_FINBERT
LLM_TEXT_EXTRACTION_OWNER = DEFER_PENDING_POC
MULTI_AGENT_INFORMATION_OWNER = TRADINGAGENTS_CHALLENGER_PENDING_POC
```

The selected topology does not create duplicate production owners. The
OpenBB news provider itself, a complete historical-news authority, an LLM
extraction model/provider, earnings-call access, and TradingAgents admission
remain unselected until bounded POCs establish provenance, access, and PIT
fitness.

## Allowed AQ scope

Future AQ code may own only project-specific contracts and policy:

- evidence identity and immutable source/model/prompt version references;
- `first_available_at` admission and fail-closed missingness;
- source precedence and conflicts;
- factor eligibility and PIT session projection;
- certification and ablation policy.

The following are not authorized:

```text
AQ_NEWS_CRAWLER = NO
AQ_MACRO_CLIENT = NO
AQ_MACRO_REVISION_ENGINE = NO
AQ_SENTIMENT_ENGINE = NO
AQ_LLM_FRAMEWORK = NO
AQ_MULTI_AGENT_FRAMEWORK = NO
AQ_RAG_ENGINE = NO
AQ_VECTOR_DB = NO
AQ_PROVIDER_REGISTRY = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Future deployment order after P5 closeout

1. Deploy `fredapi` in an isolated P6 runtime and prove a small ALFRED vintage,
   first-release, all-releases, and as-of-date matrix without introducing an AQ
   client.
2. Deploy current Transformers plus the pinned ProsusAI/finbert revision and
   run a bounded deterministic inference/interface POC on non-OOS fixtures.
3. Deploy OpenBB as a gateway and run a bounded provider-selection POC for
   news publication/content/provenance and the FRED release calendar. Select no
   paid provider without separate owner authority.
4. Run a bounded GDELT/gdeltdoc metadata and event-volume POC; do not treat it
   as complete historical article content.
5. Evaluate TradingAgents only as a challenger supplied with authoritative,
   pre-sealed macro/news/P5 inputs. Disable or reject duplicate SEC,
   fundamentals, current-only social, and trading/execution paths.
6. Keep FinGPT, generic LLM analysis, earnings calls, and social sentiment
   deferred until a separate access/model/PIT contract is authorized.

This order is frozen preaudit guidance only. Before any item can start, P5
must complete all of the following active blockers:

1. historical fundamentals build terminal closeout;
2. historical filing-feature materialization;
3. Qlib handoff of the completed P5 dataset;
4. the frozen two-trial filing-feature ablation;
5. P5 incremental OOS evidence;
6. final P5 phase closeout.

The current development next therefore remains the P5 filing-feature
materialization, gated on the historical fundamentals build's terminal
closeout. The selected-leaf P6 deployment is only the future task after P5
closeout.

```text
CURRENT_DEVELOPMENT_NEXT = P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_001
CURRENT_DEVELOPMENT_NEXT_GATE = WAITING_FOR_P5_HISTORICAL_FUNDAMENTALS_BUILD_TERMINAL_CLOSEOUT
FUTURE_AFTER_P5_CLOSEOUT = P6_SELECTED_UPSTREAM_LEAVES_DEPLOYMENT_AND_BOUNDED_POC_001
```

## Validation and non-actions

The 23-row capability matrix was checked for exact inventory and one
classification per capability. Repository validation is documentation-only.

```text
NEW_PRODUCTION_LOC = 0
SEC_DATA_REQUEST_COUNT = 0
FRED_DATA_REQUEST_COUNT = 0
NEWS_DATA_REQUEST_COUNT = 0
LLM_CALL_COUNT = 0
MODEL_WEIGHTS_DOWNLOADED = NO
TEST_RESULT = PASS
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
FINAL_CLASSIFICATION = PASS_P6_PREAUDIT_COMPLETE_P5_REMAINS_ACTIVE
```

## Post-P5 deployment and substitution audit (2026-09-25)

This section records actual isolated-runtime evidence after P5 closeout. It
does not revise the historical preaudit above. All six viable audited upstream
groups were deployed without adding AQ production code:

| Deployment | Frozen runtime identity | Bounded native-interface result |
|---|---|---|
| Official FRED/ALFRED + fredapi | `/home/zhou/AQ_ENVS/p6-data-gateways`; Python 3.11.16; fredapi 0.5.2; freeze `d75b5380efc2b0dc4629565daf6cb11909d501b8629b8ccc137d345f56a6fcdf` | ALFRED first-release, all-releases, as-of-date, and vintage methods exist. No FRED key was available, so live retrieval is `DEFERRED_CREDENTIAL_REQUIRED`; no AQ HTTP client was created. |
| GDELT + gdeltdoc | Same isolated gateway runtime; gdeltdoc 1.12.0 | Bounded article search returned 5 rows. After one bounded rate-limit retry, timeline search returned 83 rows. GDELT remains supplementary metadata/event-volume authority, not complete article or first-availability authority. |
| OpenBB | `/home/zhou/AQ_ENVS/p6-openbb`; Python 3.11.16; OpenBB 4.7.3 from commit `3e071fcc2cd9f891cac6040ae60296dba76dab46`; freeze `cc70cf31802c8c86b95e8bedcdaac70fdb6c5d93421d26735344161c0f0347a3` | 17 providers registered. Five news providers were present; only yfinance was free/no-key and its bounded AAPL news call passed. The FRED calendar interface exists but the bounded live call timed out. FMP transcript access correctly failed for missing credentials. |
| Transformers + pinned ProsusAI/finbert | `/home/zhou/AQ_ENVS/p6-finbert`; Python 3.11.16; Transformers 5.17.0; model revision `4556d13015211d73dccd3fdd39d39232506f3e43`; freeze `6272d29eabada2446624ce9b400296299f99be4281b4ddbc2637af5d1680c278` | `BertTokenizer` + `BertForSequenceClassification` classified frozen positive/negative/neutral fixtures correctly. A second run produced byte-for-byte identical scores. The obsolete ProsusAI repository runtime was not deployed. |
| TradingAgents | `/home/zhou/AQ_ENVS/p6-tradingagents`; version 0.5.0; commit `2d17df8da1536c121e4d7395ac5a5dcec9e96d6f`; freeze `8251436ffc7a035e96a2dcac641332a84d052ccad92c05df466919f7b4925ee6` | Source/public-interface inspection passed, but its initial-state API does not accept externally pre-sealed macro/news/fundamental reports and its analyst graph binds duplicate retrieval tool paths. `DEFERRED_INTERFACE_MISMATCH`; no fork or unrestricted execution. |
| FinGPT | `/home/zhou/AQ_ENVS/p6-fingpt`; package metadata 0.0.1; commit `cefb3a26b84a3a4c57868f1ca48fb0d9723fd28e`; freeze `d2c2f09f65f61cf040b355be436d7a88ccc8c0823d85453f798554bbc93751dc` | Root and RAG imports passed. Benchmark/report/forecast capability is distributed across optional notebooks and subprojects rather than one stable public runtime API. One extraction capability remains useful as a challenger; five overlaps are deferred to existing owners. |

Every isolated runtime passed `uv pip check`. The FinBERT snapshot occupies
1,314,371,575 bytes and has content-tree SHA-256
`180d70d121ec254e60ab946d1d1d2efc64e0185177536d3945edbb9feffac334`.
The frozen synthetic fixture SHA-256 is
`377d6e07894de73651a384296208f528d72c9fcc33040155a5a1c98a000c1473`.
No credential value was recorded.

### Deployed provider and overlap decisions

OpenBB registered these 17 providers: benzinga, bls, cftc, congress_gov,
econdb, eia, federal_reserve, fmp, fred, government_us, imf, intrinio, oecd,
sec, tiingo, tradingeconomics, and yfinance. The deployed news surface exposed
benzinga (`FREEMIUM_OR_KEY_REQUIRED`), fmp (`FREEMIUM_OR_KEY_REQUIRED`),
intrinio (`PAID_REQUIRED`), tiingo (`FREE_API_KEY_OR_PAID_TIER`), and yfinance
(`FREE_NO_KEY`). No subscription was purchased.

FinGPT overlap is frozen as follows:

| FinGPT capability | Decision |
|---|---|
| financial sentiment | `USE_FINBERT` |
| structured text extraction | `FINGPT_UNIQUE_USEFUL_LEAF` as challenger only |
| report analysis | `FINGPT_DUPLICATIVE_DEFER` |
| RAG | `FINGPT_DUPLICATIVE_DEFER` |
| forecasting | `FINGPT_DUPLICATIVE_DEFER` |
| LLM finance research | `FINGPT_DUPLICATIVE_DEFER`; TradingAgents remains the synthesis challenger |

### Final 23-capability deployed coverage matrix

The following classifications are conservative runtime-admission results. A
client interface without the credential needed to exercise its authoritative
service is access-deferred rather than falsely called live-deployed.

| # | Capability | Final coverage class | Deployed owner / evidence |
|---:|---|---|---|
| 1 | `NEWS_DISCOVERY` | `UPSTREAM_WHOLE_DEPLOYED` | OpenBB news gateway; yfinance bounded POC passed. |
| 2 | `HISTORICAL_NEWS_DISCOVERY` | `UPSTREAM_LEAF_DEPLOYED` | GDELT 2.x via gdeltdoc, supplementary only. |
| 3 | `NEWS_PUBLISHED_AT` | `UPSTREAM_LEAF_DEPLOYED` | OpenBB provider publication timestamp. |
| 4 | `NEWS_FIRST_AVAILABLE_AT` | `DEFER_NO_MATURE_UPSTREAM` | No deployed path proves universal first availability. |
| 5 | `NEWS_CONTENT_ACCESS` | `UPSTREAM_LEAF_DEPLOYED` | OpenBB provider content where returned. |
| 6 | `NEWS_METADATA_HASHING_INPUT` | `UPSTREAM_LEAF_DEPLOYED` | OpenBB normalized source, URL, title, and date fields. |
| 7 | `NEWS_EVENT_VOLUME` | `UPSTREAM_LEAF_DEPLOYED` | GDELT timeline interface. |
| 8 | `MACRO_SERIES_ACCESS` | `DEFER_ACCESS_OR_CREDENTIAL` | Official FRED/ALFRED + deployed fredapi; live key absent. |
| 9 | `MACRO_RELEASE_CALENDAR` | `UPSTREAM_LEAF_DEPLOYED` | OpenBB FRED calendar interface, supplementary; bounded live call timed out. |
| 10 | `MACRO_FIRST_RELEASE` | `DEFER_ACCESS_OR_CREDENTIAL` | Official ALFRED method proven; live key absent. |
| 11 | `MACRO_REVISION_HISTORY` | `DEFER_ACCESS_OR_CREDENTIAL` | Official ALFRED method proven; live key absent. |
| 12 | `MACRO_AS_OF_DATE_QUERY` | `DEFER_ACCESS_OR_CREDENTIAL` | Official ALFRED method proven; live key absent. |
| 13 | `MACRO_VINTAGE_IDENTITY` | `DEFER_ACCESS_OR_CREDENTIAL` | Official ALFRED vintage method proven; live key absent. |
| 14 | `FINANCIAL_SENTIMENT` | `UPSTREAM_LEAF_DEPLOYED` | Transformers + pinned ProsusAI/finbert. |
| 15 | `NEWS_SENTIMENT` | `UPSTREAM_LEAF_DEPLOYED` | Same deterministic model leaf on admitted news text. |
| 16 | `FILING_SENTIMENT` | `UPSTREAM_LEAF_DEPLOYED` | Same model leaf on EdgarTools-authoritative text. |
| 17 | `TEXT_CLASSIFICATION` | `UPSTREAM_LEAF_DEPLOYED` | Transformers public inference runtime. |
| 18 | `STRUCTURED_TEXT_EXTRACTION` | `UPSTREAM_CHALLENGER_DEPLOYED` | FinGPT research collection; no production admission. |
| 19 | `LLM_DOCUMENT_ANALYSIS` | `DEFER_NO_MATURE_UPSTREAM` | Model, prompt, schema, and evidence contract remain unfrozen. |
| 20 | `MULTI_AGENT_INFORMATION_SYNTHESIS` | `UPSTREAM_CHALLENGER_DEPLOYED` | TradingAgents; interface mismatch prevents production ownership. |
| 21 | `EARNINGS_CALL_ACCESS` | `DEFER_ACCESS_OR_CREDENTIAL` | OpenBB FMP transcript interface; credential absent. |
| 22 | `EARNINGS_CALL_TEXT_INTELLIGENCE` | `DEFER_ACCESS_OR_CREDENTIAL` | Transcript access and model contract are both prerequisites. |
| 23 | `SOCIAL_SENTIMENT` | `DEFER_NO_MATURE_UPSTREAM` | No deployed historical PIT social archive. |

```text
P6_CAPABILITY_COUNT = 23
UPSTREAM_WHOLE_DEPLOYED_COUNT = 1
UPSTREAM_LEAF_DEPLOYED_COUNT = 10
UPSTREAM_CHALLENGER_DEPLOYED_COUNT = 2
DEFER_NO_MATURE_UPSTREAM_COUNT = 3
DEFER_ACCESS_OR_CREDENTIAL_COUNT = 7
GENUINE_AQ_SPECIFIC_THIN_LOGIC_COUNT = 0
```

### Residual-custom audit: no implementation authorization

These seven cross-cutting residuals are outside the 23 generic upstream
capabilities. They are retained only because they express AQ's existing PIT,
episode, evidence, and certification semantics. None requires a generic
engine, and none is implemented by this task.

| Residual | Class | Why deployed upstreams cannot own it | Why scope contraction cannot remove it | Why defer is not acceptable once consumed | Minimum eventual AQ behavior | Est. production LOC | Engine |
|---|---|---|---|---|---|---:|---|
| source/evidence identity | `PROJECT_POLICY_ONLY` | It binds project-selected source/model/config identities, not a provider operation. | Removing identity would make outputs non-reproducible. | A governed dataset cannot admit unidentified inputs. | Persist immutable upstream identities and hashes. | 25 | `NO` |
| first-available-at admission | `PROJECT_POLICY_ONLY` | Providers expose varying timestamps but cannot choose AQ's PIT admissibility claim. | Removing availability control would permit look-ahead. | Any time-sensitive feature needs an admission decision or fail-closed null. | Admit only proven timestamps and fail closed otherwise. | 20 | `NO` |
| source precedence/conflict | `PROJECT_POLICY_ONLY` | The one-owner decision and conflict consequence are repository governance. | Removing it would permit contradictory owners. | A conflict cannot be silently carried into an authoritative feature. | Apply frozen precedence and reject conflicts. | 25 | `NO` |
| upstream-to-AQ evidence shape | `THIN_SHAPE_ADAPTER_ONLY` | Upstreams do not emit AQ's bounded evidence contract. | Without projection, upstream records cannot enter the existing contract. | A selected upstream is unusable until its native fields are losslessly shaped. | Project selected fields without reinterpretation. | 35 | `NO` |
| episode/session/Qlib mapping | `THIN_SHAPE_ADAPTER_ONLY` | AQ's P1 membership episodes and Qlib dataset shape are project-specific. | Removing it breaks the existing research-universe and runtime boundary. | An admitted feature must be aligned before Qlib can consume it. | Map admitted evidence onto existing episodes/sessions and Qlib input. | 45 | `NO` |
| factor eligibility | `PROJECT_POLICY_ONLY` | Upstreams cannot define AQ research eligibility. | Removing it would admit sources outside the frozen scientific claim. | Evaluation cannot start without an exact eligible surface. | Apply source-availability and PIT eligibility. | 20 | `NO` |
| ablation/certification policy | `PROJECT_POLICY_ONLY` | It governs existing Qlib/MLflow/DVC/arch/skfolio owners rather than replacing them. | Removing it erases the project's preregistered decision rule. | Results cannot be promoted without a frozen acceptance rule. | Bind frozen comparisons and gates; build no evaluation engine. | 20 | `NO` |

Each item remains design evidence until a separately authorized P6 handoff
actually consumes it; “not acceptable to defer” is not implementation
authorization in this task.
The exact true upstream gaps remain `NEWS_FIRST_AVAILABLE_AT` and
`SOCIAL_SENTIMENT`; neither authorizes a crawler or archive. LLM document
analysis is deferred because its scientific contract is unfrozen, not because
AQ should build an LLM framework.

```text
DEPLOYED_UPSTREAM_COUNT = 6
RESIDUAL_CUSTOM_CAPABILITY_COUNT = 7
TRUE_UNSOLVED_UPSTREAM_GAP_COUNT = 2
TRUE_UNSOLVED_UPSTREAM_GAPS = NEWS_FIRST_AVAILABLE_AT,SOCIAL_SENTIMENT
CUSTOM_ENGINE_REQUIRED_COUNT = 0
OLD_FINBERT_REPOSITORY_RUNTIME = REJECTED_SUPERSEDED_BY_TRANSFORMERS_MODEL_LEAF
NEW_AQ_P6_PRODUCTION_CAPABILITY_IMPLEMENTATION = NO
NEW_PRODUCTION_LOC = 0
AQ_NEWS_CRAWLER_CREATED = NO
AQ_MACRO_CLIENT_CREATED = NO
AQ_MACRO_REVISION_ENGINE_CREATED = NO
AQ_SENTIMENT_ENGINE_CREATED = NO
AQ_LLM_FRAMEWORK_CREATED = NO
AQ_MULTI_AGENT_FRAMEWORK_CREATED = NO
AQ_RAG_ENGINE_CREATED = NO
AQ_VECTOR_DB_CREATED = NO
AQ_PROVIDER_REGISTRY_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
MODEL_TRAINING_COUNT = 0
BACKTEST_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P6_FRED_API_CREDENTIAL_ACTIVATION_AND_MACRO_PIT_POC_001
FINAL_CLASSIFICATION = PASS_P6_UPSTREAMS_DEPLOYED_RESIDUAL_CUSTOM_AUDIT_COMPLETE
```

## FRED credential activation gate (2026-09-25)

The selected macro ownership remains unchanged:

```text
MACRO_PIT_PRODUCTION_OWNER = OFFICIAL_FRED_ALFRED
MACRO_PIT_OWNERSHIP_MODE = UPSTREAM_WHOLE
MACRO_PIT_PYTHON_ACCESS_OWNER = FREDAPI
MACRO_PIT_PYTHON_ACCESS_MODE = UPSTREAM_LEAF
CUSTOM_ENGINE_REQUIRED = NO
```

The existing `/home/zhou/AQ_ENVS/p6-data-gateways` runtime was reused. It
contains Python 3.11.16 and fredapi 0.5.2, its 12-package freeze remains
`d75b5380efc2b0dc4629565daf6cb11909d501b8629b8ccc137d345f56a6fcdf`,
and `uv pip check` passes. The native `Fred` class exposes all five selected
methods: `get_series`, `get_series_first_release`,
`get_series_all_releases`, `get_series_as_of_date`, and
`get_series_vintage_dates`.

No authorized FRED API key was available in the Windows environment, WSL
environment, or fredapi private default file. No credential value was printed,
logged, stored, or committed. The task therefore stopped before any live
request, exactly as required. `GDP`, `CPIAUCSL`, and `UNRATE` were not queried,
and interface presence is not promoted to live PIT evidence.

```text
FRED_API_KEY_AVAILABLE = NO
SERIES_COUNT = 3
SERIES_IDS = GDP,CPIAUCSL,UNRATE
FRED_NETWORK_REQUEST_COUNT = 0
FRED_LATEST_SERIES_POC = BLOCKED_CREDENTIAL_NOT_RUN
FRED_FIRST_RELEASE_POC = BLOCKED_CREDENTIAL_NOT_RUN
FRED_ALL_RELEASES_POC = BLOCKED_CREDENTIAL_NOT_RUN
FRED_AS_OF_DATE_POC = BLOCKED_CREDENTIAL_NOT_RUN
FRED_VINTAGE_DATES_POC = BLOCKED_CREDENTIAL_NOT_RUN
GDP_PIT_STATUS = BLOCKED_CREDENTIAL_NOT_RUN
CPIAUCSL_PIT_STATUS = BLOCKED_CREDENTIAL_NOT_RUN
UNRATE_PIT_STATUS = BLOCKED_CREDENTIAL_NOT_RUN
FRED_ALFRED_CAN_PROVE_WHAT_WAS_KNOWN_WHEN = NOT_LIVE_VALIDATED_CREDENTIAL_REQUIRED
AQ_MACRO_HTTP_CLIENT_CREATED = NO
AQ_MACRO_REVISION_ENGINE_CREATED = NO
AQ_MACRO_VINTAGE_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
THIN_SHAPE_ADAPTER_REQUIRED = PENDING_AFTER_LIVE_POC
THIN_SHAPE_ADAPTER_IMPLEMENTED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
BACKTEST_COUNT = 0
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/fred-api-credential-activation-and-macro-pit-poc-001
CREDENTIAL_GATE_EVIDENCE_SHA256 = 6623a7c8e62ccc458b68becebbcb1e7dc9c0b7e280b3a50fa6d6dad3ee3b0c90
CURRENT_DEVELOPMENT_NEXT = P6_FRED_API_CREDENTIAL_PROVISIONING_001
FINAL_CLASSIFICATION = BLOCKED_FRED_API_CREDENTIAL_REQUIRED
```

### Live continuation on PR #84

The initial credential gate above remains historical evidence. After the owner
provisioned a credential in one local D-drive root file, that file was located
by an explicitly authorized non-recursive root search and read only inside the
bounded child process. The credential value, length, fingerprint, hash, and
contents were never printed or persisted. No `FRED_API_KEY` remained in the
Windows or WSL environment after the process exited.

The same fredapi 0.5.2 runtime then exercised, for exactly `GDP`, `CPIAUCSL`,
and `UNRATE`, each native public method selected by the authority:
`get_series`, `get_series_first_release`, `get_series_all_releases`,
`get_series_as_of_date`, and `get_series_vintage_dates`. This produced 15
instrumented native upstream requests. Bounded evidence retained observation
date, `realtime_start` vintage identity, and value; it did not substitute the
latest revised value for the historical observation.

Each series contained a bounded revision relation: the selected GDP target had
6 distinct values, CPIAUCSL had 3, and UNRATE had 2. The native as-of results
and vintage dates prove that official FRED/ALFRED through fredapi can answer
what value was known at a historical date. The returned pandas Series/DataFrame
shapes will require a future thin projection to the AQ/Qlib evidence shape, but
no such adapter was implemented here.

```text
INITIAL_FRED_CREDENTIAL_GATE = BLOCKED_CREDENTIAL_REQUIRED
FRED_KEY_FILE_EXISTS = YES
FRED_API_KEY_AVAILABLE = YES
FRED_CREDENTIAL_PROVISIONED = YES
FRED_LIVE_PIT_POC = PASS
FRED_NETWORK_REQUEST_COUNT = 15
SERIES_COUNT = 3
SERIES_IDS = GDP,CPIAUCSL,UNRATE
FRED_LATEST_SERIES_POC = PASS
FRED_FIRST_RELEASE_POC = PASS
FRED_ALL_RELEASES_POC = PASS
FRED_AS_OF_DATE_POC = PASS
FRED_VINTAGE_DATES_POC = PASS
GDP_PIT_STATUS = PASS
CPIAUCSL_PIT_STATUS = PASS
UNRATE_PIT_STATUS = PASS
FRED_ALFRED_CAN_PROVE_WHAT_WAS_KNOWN_WHEN = YES
AQ_MACRO_HTTP_CLIENT_CREATED = NO
AQ_MACRO_REVISION_ENGINE_CREATED = NO
AQ_MACRO_VINTAGE_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
THIN_SHAPE_ADAPTER_REQUIRED = YES
THIN_SHAPE_ADAPTER_IMPLEMENTED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
BACKTEST_COUNT = 0
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/fred-api-credential-activation-and-macro-pit-poc-001
LIVE_MACRO_PIT_EVIDENCE_SHA256 = 5335c17cd936ab53785f205d075ad7d5ed6eb22319030d6024984b927d412896
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_PIT_THIN_SHAPE_ADAPTER_001
FINAL_CLASSIFICATION = PASS_FRED_ALFRED_LIVE_MACRO_PIT_POC
```

## Macro PIT upstream substitution POC 002 (2026-09-25)

The planned AQ macro shape adapter was not implemented. Four specifically
authorized candidates were evaluated against the sealed PR #84 fredapi
evidence, and only bounded live calls for `GDP`, `CPIAUCSL`, and `UNRATE` were
made. Official FRED/ALFRED remains the source authority.

### Candidate decisions

| Candidate | Frozen identity | Runtime evidence | Owner class | Production decision |
|---|---|---|---|---|
| Vintage | `vintage-mcp==0.9.0`; source `c55b6d5bd801a21e5844600fc6110de4a3c8dd4b`; MIT; Python 3.11.16 runtime `/home/zhou/AQ_ENVS/p6-vintage`; freeze `20c3c069a3475c503f54d9cfb7fd11bec045c9ccc6dcdeb1769bbfbcca834a68` | Live three-series POC passed. Native rows retain `entity`, `field`, `observed_at`, `known_at`, and `value`. The bounded PR #84 revisions matched exactly and no future revision crossed the as-of cutoff. Missing upstream values are not filled. | `SELECTED_UPSTREAM_LEAF` | Own the upstream-to-AQ macro evidence relation. |
| pyfredapi | `pyfredapi==0.10.2`; source `6d924602bfa5e18af6630f4bb272fb5181268c0b`; MIT; Python 3.11.16 runtime `/home/zhou/AQ_ENVS/p6-pyfredapi`; freeze `dea654fd2d35299cfbf6da7a1543bb2ff89a4294ebb9b97c8bda0415fb273108` | Live JSON and pandas calls passed for all three series. Full releases, `realtime_start`, `realtime_end`, and vintage dates matched the official data already proven through fredapi 0.5.2. | `VALID_BUT_DUPLICATIVE` | `DUPLICATIVE_NOT_SELECTED`; it does not remove the remaining project session policy. |
| ferric-fred | source `46887a7a0ea1024c3c6001b2864f0883b901401a`; library/CLI 0.3.8; MCP 0.3.11; MIT OR Apache-2.0 | Source and public interfaces prove ALFRED real-time windows, vintage dates, typed observations, CLI JSON, and MCP schemas. The existing WSL runtime has no Cargo toolchain; installing Rust or adding a Python bridge was not a bounded, zero-burden deployment. | `VALID_BUT_RUNTIME_MISMATCH` | `VALID_UPSTREAM_BUT_NOT_SELECTED_RUNTIME_MISMATCH`. |
| QuantSmith FRED PIT leaf | current direct repository access returned HTTP 404; the last official search index describes spec 0045 and `fred_point_in_time.py` inside the broader agentic SDK | No current immutable source commit, license, stable import boundary, or independent leaf deployment could be verified. The indexed module is surrounded by QuantSmith orchestration, agents, gates, memory, backtest, and pipeline surfaces. | `VALID_BUT_FRAMEWORK_COUPLED` | `REJECTED_COUPLED_TO_BROADER_FRAMEWORK`; no algorithm was copied. |

Vintage's `as_of` behavior is intentionally recorded precisely: it removes
rows whose `known_at` is later than the cutoff and preserves every revision
that was already visible. For the GDP probe this means several visible rows
can remain for one `observed_at`; the convenience API does not silently select
one revised value. This is the correct lossless evidence relation, but it is
not by itself the final AQ/XNYS/Qlib session panel. The only remaining AQ
behavior is the already project-specific policy that maps `known_at` onto the
first tradable session and performs the as-of projection. It does not justify
a macro client, revision engine, normalization adapter, or generic panel
engine.

pyfredapi is a sound newer access library and exposes a broader typed endpoint
surface than fredapi, but selecting it would merely replace one working FRED
client with another. Ferric-fred is also sound upstream code, but using it in
the present Python/Qlib runtime would introduce a Rust process or bridge for no
semantic gain. QuantSmith was not vendored or partially copied.

`RezaSoleymanifar/ape-tape` is recorded only for the future role
`FORWARD_ONLY_SOCIAL_SENTIMENT_ARCHIVE`. It cannot manufacture historical
social point-in-time data and was not deployed in this task.

```text
VINTAGE_VERSION = 0.9.0
VINTAGE_POC_STATUS = PASS
VINTAGE_OBSERVED_AT_STATUS = PASS
VINTAGE_KNOWN_AT_STATUS = PASS
VINTAGE_AS_OF_STATUS = PASS_FILTERS_FUTURE_PRESERVES_VISIBLE_REVISION_RELATION
VINTAGE_REVISION_PARITY_STATUS = PASS_EXACT_BOUNDED_PR84_MATCH
VINTAGE_MISSINGNESS_PRESERVATION = PASS_NO_IMPUTATION
VINTAGE_PRODUCTION_FIT = SELECTED_UPSTREAM_LEAF_FOR_EVIDENCE_SHAPE
PYFREDAPI_VERSION = 0.10.2
PYFREDAPI_POC_STATUS = PASS
PYFREDAPI_PRODUCTION_FIT = DUPLICATIVE_NOT_SELECTED
FERRIC_FRED_POC_STATUS = SOURCE_AND_INTERFACE_AUDIT_PASS_BUILD_SKIPPED_NO_CARGO
FERRIC_FRED_PRODUCTION_FIT = VALID_UPSTREAM_BUT_NOT_SELECTED_RUNTIME_MISMATCH
QUANTSMITH_FRED_PIT_LEAF_STATUS = REJECTED_COUPLED_TO_BROADER_FRAMEWORK
QUANTSMITH_PRODUCTION_FIT = NOT_SELECTED
SELECTED_MACRO_PIT_NORMALIZATION_OWNER = VINTAGE_0_9_0
CAN_UPSTREAM_OWN_MACRO_EVIDENCE_SHAPE = YES
CAN_UPSTREAM_OWN_MACRO_PIT_PANEL = NO
AQ_MACRO_SHAPE_ADAPTER_REQUIRED = NO
AQ_MACRO_PIT_PANEL_CODE_REQUIRED = YES_PROJECT_SESSION_POLICY_ONLY
AQ_MACRO_SESSION_POLICY_ONLY_REMAINS = YES
CUSTOM_ENGINE_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
APE_TAPE_FUTURE_ROLE = FORWARD_ONLY_SOCIAL_SENTIMENT_ARCHIVE
P2_V2_SEALED_OOS_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/macro-pit-upstream-substitution-poc-002
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_PIT_SESSION_POLICY_ONLY_INTEGRATION_001
FINAL_CLASSIFICATION = PASS_VINTAGE_SELECTED_FOR_NATIVE_MACRO_EVIDENCE_SHAPE
```

## Macro session policy upstream-native composition POC (2026-09-25)

The historical PR #85 selection above remains intact: official FRED/ALFRED is
the source authority and Vintage 0.9.0 is the selected lossless macro evidence
leaf. The follow-on bounded POC proved that the remaining session-visibility
behavior does not require the previously anticipated AQ panel code.

The public `vintage.macro(...)` relation for exactly `GDP`, `CPIAUCSL`, and
`UNRATE` retained `entity`, `field`, `observed_at`, `known_at`, `value`, and
source provenance. Its 385 bounded rows exposed non-null date-only `known_at`
values. The existing `aq_xnys_calendar` leaf generated the XNYS session
relation, and the retained DuckDB 1.5.5 runtime applied the sole AQ-owned
predicate:

```sql
MIN(session) WHERE session > CAST(known_at AS DATE)
```

The strict comparison is authoritative. Date-only evidence published on a
trading day is not admitted to that day's session because no intraday release
time has been proven. Monday, Friday, Saturday, Sunday, and pre-holiday cases
all mapped to the first strictly later XNYS session; there were zero same-day
or earlier mappings. Repeated canonical execution was byte/order stable.

For three bounded target sessions, the session-visible relation
`effective_session <= T` exactly equaled the public Vintage relation obtained
with `as_of = T - 1 calendar day`. The cutoff is deliberately a calendar day,
not the previous XNYS session, so weekend evidence remains eligible on Monday.
All visible revisions stayed lossless, the deterministic DuckDB window query
selected the latest visible revision per `(entity, field, observed_at)`, no
future revision leaked, and no conflicting revision identity appeared.
Different `observed_at` periods were not collapsed and no missing value was
filled, interpolated, or backfilled.

Vintage's generic backtest panel was not selected for this relation. It pivots
primarily by `known_at` and entity with last-value aggregation, so it does not
preserve the required field/observed-at/revision identity. This is a semantic
mismatch for the macro revision relation, not a rejection of Vintage as its
evidence owner. The existing P5 fundamentals session and as-of functions were
also left fundamentals-specific; `aq_hybrid_fundamentals.effective_session`
is reference-only, while `project_events_asof` and `aq_p5_projection` are
semantic mismatches for macro evidence.

This POC stops at revision-to-first-safe-session visibility. It does not choose
which observed period becomes a model feature, define release age or lag,
derive growth, forward-fill, create Qlib columns, train, predict, or backtest.
That scientific policy is the next bounded authority task.

```text
MACRO_SOURCE_AUTHORITY = OFFICIAL_FRED_ALFRED
MACRO_EVIDENCE_OWNER = VINTAGE_0_9_0
VINTAGE_PUBLIC_API_USED = YES
VINTAGE_PRIVATE_INTERNAL_REQUIRED = NO
KNOWN_AT_PRECISION = DATE_ONLY
XNYS_OWNER = EXCHANGE_CALENDARS_VIA_AQ_XNYS_CALENDAR
EXISTING_XNYS_LEAF_REUSED = YES
RELATIONAL_COMPOSITION_OWNER = DUCKDB
DUCKDB_VERSION = 1.5.5
EFFECTIVE_SESSION_POLICY = FIRST_XNYS_SESSION_STRICTLY_AFTER_KNOWN_AT_DATE
SAME_DAY_DATE_ONLY_VISIBILITY = PROHIBITED
MONDAY_MAPPING_STATUS = PASS
FRIDAY_MAPPING_STATUS = PASS
WEEKEND_MAPPING_STATUS = PASS
HOLIDAY_MAPPING_STATUS = PASS
VINTAGE_AS_OF_EQUIVALENCE = PASS
AS_OF_SESSION_CUTOFF_RULE = TARGET_SESSION_MINUS_ONE_CALENDAR_DAY
REVISION_RELATION_PRESERVED = PASS
LATEST_VISIBLE_REVISION_POC = PASS
FUTURE_REVISION_LEAKAGE_COUNT = 0
REVISION_IDENTITY_CONFLICT_COUNT = 0
MISSINGNESS_PRESERVATION = PASS_NO_FILL_INTERPOLATION_OR_BACKFILL
CROSS_OBSERVED_AT_COLLAPSE_PERFORMED = NO
FINAL_MACRO_FEATURE_POLICY_SELECTED = NO
VINTAGE_GENERIC_BACKTEST_PANEL_FOR_MACRO_REVISION_RELATION = NOT_SELECTED_SEMANTIC_MISMATCH
AQ_HYBRID_FUNDAMENTALS_EFFECTIVE_SESSION = REFERENCE_ONLY
AQ_HYBRID_FUNDAMENTALS_PROJECT_EVENTS_ASOF = SEMANTIC_MISMATCH
AQ_P5_PROJECTION = SEMANTIC_MISMATCH
AQ_P5_PROJECTION_REFACTORED = NO
AQ_MACRO_SESSION_MAPPER_CREATED = NO
AQ_MACRO_REVISION_ENGINE_CREATED = NO
AQ_MACRO_PANEL_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
PRIVATE_POC_CODE_ONLY = YES
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/macro-session-policy-upstream-native-composition-poc-001
PRIVATE_EVIDENCE_CHECKSUM_MANIFEST_SHA256 = f19e05121a37d25ef8ed8d3231a96be8294062729a5624ac8e5e15a983db4b32
P2_V2_SEALED_OOS_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_FEATURE_OBSERVED_AT_POLICY_FREEZE_001
FINAL_CLASSIFICATION = PASS_UPSTREAM_NATIVE_MACRO_SESSION_COMPOSITION_POC
```

## Residual upstream and Skills substitution audit (2026-09-25)

This bounded audit ran after PR #86 was squash-merged at main
`1c6eba0cfa99cccfc27e6ac5042f4607892cee8b`. It did not add production code,
create features, train a model, predict, or backtest. Official FRED/ALFRED,
Vintage 0.9.0, `exchange_calendars`, and DuckDB retain their previously frozen
macro ownership; no candidate below displaced them.

### Candidate identity and runtime matrix

| Candidate | Source identity | Version or SHA | License / use boundary | Runtime fit and public interface | Skill available | Cost |
|---|---|---|---|---|---|---|
| FRED-MD / FRED-QD | Official St. Louis Fed 2026-08 CSVs | MD `412b5451...ac0a4`; QD `7471dd58...1b303` (SHA-256) | official public research dataset; citation required | `PASS`; versioned CSVs are directly usable by pandas/DuckDB | no | free |
| Google LangExtract | `google/langextract` release | `1.7.0`, `70cfb988cc25f15d8b04a1e57bd52a777207c0c6` | Apache-2.0 | `PASS` structural POC through public `lx.extract()` | official `langextract-usage` | library free; model/provider cost varies |
| Anthropic financial-services Skills | `anthropics/financial-services` | `574ed3624aebd0418c7e96cd101262f30210ab26` | Apache-2.0 | Markdown/JSON workflow assets; connector and model runtimes remain separate | yes | Skills free; named data connectors may cost |
| Alpha Vantage transcripts | official `EARNINGS_CALL_TRANSCRIPT` API | unversioned service interface audited 2026-09-25 | default terms permit personal non-commercial use; other use needs separate agreement | documented API; no authorized credential was found, so no live call was made | no | standard limit 25 calls/day; paid tier for scale |
| Media Cloud | `mediacloud/api-client` | `5.1.0`, `d36ca5d653aa94739e51dc7b52f08fe89b819550` | Apache-2.0 client; extracted article text is not downloadable for copyright reasons | Python Search API; token required; default client throttle is 2 requests/minute | no | account/API token required |
| Common Crawl | `commoncrawl/cc-index-table` | `595493ff3a87295f99ce2951133288dbc1e5ad11` | Apache-2.0 index code; corpus terms apply | CDXJ and Parquet Columnar Index; direct DuckDB compatibility | no | index is public; compute/egress may apply |
| Arctic Shift | `ArthurHeitmann/arctic_shift` release `2026_08` | `1565f3456488a99c212166e5779dc0b87f622ad3` | **no repository license or dataset-use grant identified**; Reddit terms remain unresolved | monthly RC/RS dumps plus bounded search API; no dump downloaded | no | service free; material storage burden |
| MLflow Dataset Tracking + DVC | installed MLflow public API plus existing DVC owner | MLflow `3.16.0` | Apache-2.0 | `PASS` SQLite POC using `mlflow.data.from_pandas()` and `mlflow.log_input()` | no | already installed |

### Candidate fit and production decisions

| Candidate | PIT fit | Provenance fit | Coverage | Duplicates an owner? | AQ implementation removable? | Production decision |
|---|---|---|---|---|---|---|
| FRED-MD / FRED-QD | historical reference vintages, not the selected PIT-normalization owner | file/vintage name plus content hash | broad monthly/quarterly macro inventories | partially overlaps FRED/ALFRED and Vintage without replacing either | benchmark inventory/transformation reference only; final scientific choice remains AQ policy | `SELECTED_UPSTREAM_LEAF` as `PRIMARY_MACRO_FEATURE_TRANSFORMATION_REFERENCE` |
| LangExtract | not a time authority | precise source-span alignment; ungrounded output remains explicitly ungrounded | structured extraction, schema shaping, chunking and multiple passes | supersedes FinGPT as the preferred mechanics challenger, not as model-quality authority | yes, for extraction mechanics if textual features are later authorized | `VALID_BUT_CHALLENGER`; `LANGEXTRACT_VALID_BUT_MODEL_DEPENDENT` |
| Financial Skills | no source/PIT authority | workflows require citations, source checks and human review | earnings, guidance, beat/miss, management Q&A, company/market research and synthesis | workflow-only; SEC/FRED/Vintage/OpenBB/GDELT remain data owners | yes, for workflow guidance only | `SELECTED_UPSTREAM_SKILL_WORKFLOW_ONLY` |
| Alpha Vantage | quarter-addressed history since 2010Q1; exact safe-availability fields not proven | turn-by-turn sentiment is documented, but immutable transcript identity/completeness was not live-validated | over 15 years documented | challenger to deferred OpenBB/FMP transcript access | no, pending credential, scale and terms validation | `BLOCKED_CREDENTIAL_OR_COST` |
| Media Cloud | `indexed_date` is capture/processing time and therefore a conservative upper bound, **not** exact first publication | normalized-URL hash ID, final URL and indexed timestamp | 200M+ stories; collection/source dependent | supplements provider publication fields and GDELT | yes when credentialed, for safe availability only; not a text archive | `BLOCKED_CREDENTIAL_OR_COST` |
| Common Crawl | capture timestamp is a conservative upper bound, not publication time | URL, response status, content digest and WARC filename/offset/length | archive since 2007; individual URL coverage is not guaranteed | supplementary archive fallback | yes, for capture/digest/WARC provenance; no AQ crawler | `SELECTED_UPSTREAM_LEAF` |
| Arctic Shift | strong `created_utc`, `retrieved_on`, second-retrieval and delay evidence | monthly SHA-256, edit/deletion fields and retrieval timestamps | current 2026 submissions/comments dumps; Reddit subset only | would fill the Reddit part of social sentiment | technically yes, but legally not authorized | `BLOCKED_LICENSE_OR_TERMS` |
| MLflow + DVC | mechanical lineage only, not domain availability semantics | dataset name, digest, source, schema, profile, context and run linkage | experiment input datasets | extends existing owners; no new registry | yes, for mechanical dataset registry/lineage | `SELECTED_UPSTREAM_LEAF` (existing owner) |

The current FRED-MD file assigns benchmark transformation code `6` to
`CPIAUCSL` and `2` to `UNRATE`. The current FRED-QD file assigns `5` to
`GDPC1`, `6` to `CPIAUCSL`, and `2` to `UNRATE`. Exact `GDP` is absent from
both current inventories, so `GDPC1` must not be silently substituted. These
codes materially reduce the macro transformation-policy search space, but the
FRED-QD research explicitly says benchmark choices may need reconsideration
and can change forecast accuracy. Applying any code, including choosing real
GDP `GDPC1` instead of nominal `GDP`, remains a preregistered AQ scientific
decision. Vintage 0.9.0 remains the PIT evidence-normalization owner.

The LangExtract POC used a fixed private test model, no network and no external
LLM. It round-tripped one verbatim extraction to character interval `[13,39)`,
retained an invented extraction with `char_interval = null`, and exercised
100-character chunking with two passes across 60 prompts. The upstream owns
source-span resolution, chunk scheduling, repeated extraction and structured
output mechanics, but it cannot certify the selected model's semantic quality.
OpenAI has structured-output support; Ollama has JSON-format support but does
not support a user-supplied `output_schema` in LangExtract 1.7.0. FinGPT is
therefore downgraded to reference/challenger status for structured extraction.

The official `langextract-usage` Skill is adopted as private usage guidance,
not as source or model authority. The financial-services `earnings-analysis`
and `earnings-reviewer` workflows are `ADOPT_WORKFLOW_ONLY` for earnings-call
reading, guidance, beat/miss, management commentary and Q&A themes. The
`market-researcher`, competitive-analysis and equity-research workflows are
also `ADOPT_WORKFLOW_ONLY` for company research, cross-source verification and
news/event synthesis. Their investment opinions, proprietary connector
assumptions and publishing decisions are not AQ authority; no external Skill
copy is committed.

Media Cloud documents `indexed_date` as the time content was captured and
processed. It is a safe non-optimistic admission bound but is never renamed
`first_available_at`; its heuristic `publish_date` is also not exact first
availability. Common Crawl supplies the free supplementary equivalent through
capture time plus digest and WARC identity. Consequently the former generic
`NEWS_FIRST_AVAILABLE_AT` gap is narrowed to a fail-closed project predicate:
use a provider timestamp only when its semantics are authoritative, otherwise
use an available archive capture upper bound, and emit no observation if
neither exists. Exact universal first publication remains unproved, but is not
required for conservative admission.

Arctic Shift is a serious technical Reddit candidate. The 2026-08 schemas
include `created_utc`, `retrieved_on`, `_meta.retrieved_2nd_on`, edit and
deletion status; documentation describes a second retrieval after roughly 36
hours, and monthly releases include SHA-256 hashes. However the source has no
recognized license file or repository license declaration, and neither the
archive's dataset-use grant nor compatibility with Reddit terms was proven.
Public access is not a use license. It is blocked and the true Reddit sentiment
gap remains.

The MLflow 3.16.0 POC recorded a synthetic pandas dataset through a native
SQLite tracking backend and recovered its name, digest, local source, schema,
profile and `audit` context from the run input. DVC continues to own artifact
content/dependency identity. AQ retains only domain facts such as safe
availability, conflict/admission meaning and source-specific evidence IDs; no
AQ evidence registry is justified.

### Residual reclassification

The seven prior residuals were mechanical source/evidence identity,
first-available-at admission, source precedence/conflict, upstream-to-AQ
evidence shape, episode/session/Qlib mapping, scientific feature eligibility,
and ablation/certification. MLflow+DVC now clearly own mechanical dataset
identity/lineage; LangExtract/Vintage own their applicable evidence-shaping
mechanics; and existing DuckDB/Pandera/`exchange_calendars`/Qlib composition
owns generic tabular/session/handoff mechanics. Four AQ-owned project decisions
remain:

1. PIT admission policy;
2. source precedence and conflict policy;
3. scientific feature eligibility;
4. certification and promotion policy.

```text
P6_RESIDUAL_UPSTREAM_SKILLS_SUBSTITUTION_AUDIT = PASS
FRED_MD_QD_STATUS = PRIMARY_MACRO_FEATURE_TRANSFORMATION_REFERENCE
MACRO_TRANSFORMATION_POLICY_UPSTREAM_REDUCTION = BENCHMARK_CODES_REUSED_AS_PRIMARY_REFERENCE_FINAL_SELECTION_REMAINS_AQ_SCIENTIFIC_POLICY
LANGEXTRACT_VERSION = 1.7.0
LANGEXTRACT_SOURCE_IDENTITY = 70cfb988cc25f15d8b04a1e57bd52a777207c0c6
LANGEXTRACT_STATUS = LANGEXTRACT_VALID_BUT_MODEL_DEPENDENT
LANGEXTRACT_AGENT_SKILL_STATUS = ADOPT_AS_IS_PRIVATE_USAGE_GUIDANCE
FINGPT_STRUCTURED_EXTRACTION_ROLE = REFERENCE_OR_CHALLENGER_ONLY
FINANCIAL_SKILLS_STATUS = PASS_OFFICIAL_WORKFLOWS_AUDITED
FINANCIAL_SKILLS_ADOPTION_MODE = SELECTED_UPSTREAM_SKILL_WORKFLOW_ONLY
ALPHA_VANTAGE_TRANSCRIPT_STATUS = BLOCKED_CREDENTIAL_COST_AND_TERMS_VALIDATION
MEDIA_CLOUD_SAFE_AVAILABILITY_STATUS = VALID_CONSERVATIVE_UPPER_BOUND_CREDENTIAL_REQUIRED
COMMON_CRAWL_CAPTURE_STATUS = SELECTED_SUPPLEMENTARY_CAPTURE_PROVENANCE_LEAF
ARCTIC_SHIFT_STATUS = SERIOUS_TECHNICAL_CANDIDATE_BLOCKED_LICENSE_OR_TERMS
ARCTIC_SHIFT_LICENSE_TERMS_STATUS = BLOCKED_NO_LICENSE_OR_DATA_USE_GRANT_PROVEN
SOCIAL_SENTIMENT_CLASSIFICATION_AFTER_AUDIT = TRUE_GAP_RETAINED_REDDIT_LICENSE_AND_TERMS
MLFLOW_DATASET_LINEAGE_STATUS = SELECTED_EXISTING_OWNER_WITH_DVC
OLD_P6_RESIDUAL_CUSTOM_CAPABILITY_COUNT = 7
NEW_P6_RESIDUAL_CUSTOM_CAPABILITY_COUNT = 4
TRUE_UNSOLVED_UPSTREAM_GAP_COUNT = 1
TRUE_UNSOLVED_UPSTREAM_GAPS = REDDIT_SENTIMENT_LICENSE_AND_REDDIT_TERMS_AUTHORITY
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/residual-upstream-skills-substitution-audit-001
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_FEATURE_OBSERVED_AT_POLICY_FREEZE_001
FINAL_CLASSIFICATION = PASS_P6_RESIDUAL_UPSTREAM_SKILLS_SUBSTITUTION_AUDIT
```

## Macro feature observed-at policy freeze (2026-09-25)

This authority decision was made before any P6 macro feature was built or any
model, prediction, ablation, or backtest was run. It consumes the already
proven session-visible revision relation and does not alter its upstream
owners: official FRED/ALFRED remains source authority, Vintage 0.9.0 remains
PIT evidence-normalization owner, `exchange_calendars` plus DuckDB remain the
session/relational composition owners, and FRED-MD/QD is only the primary
benchmark transformation reference.

### Series identity and transformation decision

`GDP` and `GDPC1` are different economic quantities. `GDP` is nominal gross
domestic product; `GDPC1` is real gross domestic product in chained dollars.
The current bounded FRED-MD/QD inventories do not assign an official benchmark
code to exact `GDP`. FRED-QD assigns code `5` to `GDPC1`, but selecting it would
be a feature-inventory change, not a transformation of `GDP`. Macro V1 therefore
defers `GDP`, rejects `GDPC1` for V1, and performs no silent substitution.

| SERIES_ID | ECONOMIC_MEANING | FREQUENCY | PIT_OWNER | BENCHMARK_REFERENCE | BENCHMARK_TRANSFORM_CODE | SELECTED_TRANSFORMATION | OBSERVED_AT_SELECTION_RULE | SESSION_STATE_RULE | MISSINGNESS_RULE | PROVENANCE_RULE | FINAL_V1_STATUS |
|---|---|---|---|---|---:|---|---|---|---|---|---|
| `GDP` | nominal gross domestic product, SAAR | quarterly | Vintage 0.9.0 | current FRED-MD/QD | none for exact series | none | not active | not projected | remain missing | preserve source evidence; do not substitute `GDPC1` | `DEFERRED` |
| `GDPC1` | real gross domestic product, chained dollars, SAAR | quarterly | Vintage 0.9.0 | FRED-QD | `5` | not adopted; benchmark means `ln(x_t)-ln(x_{t-1})` | not active | not projected | remain missing | retain distinct series identity | `REJECTED` |
| `CPIAUCSL` | seasonally adjusted consumer price index | monthly | Vintage 0.9.0 | FRED-MD/QD | `6` | `ln(x_t)-2ln(x_{t-1})+ln(x_{t-2})` | latest monthly `observed_at` whose three-period dependency window is visible and valid | carry the latest legitimate transformed state until a release or constituent revision changes it | emit no new state when any required period is absent or non-positive | retain all three source `observed_at`, selected revisions, `known_at`, effective sessions and evidence IDs | `SELECTED` |
| `UNRATE` | seasonally adjusted civilian unemployment rate | monthly | Vintage 0.9.0 | FRED-MD/QD | `2` | `x_t-x_{t-1}` in percentage points | latest monthly `observed_at` whose two-period dependency window is visible and valid | carry the latest legitimate transformed state until a release or constituent revision changes it | emit no new state when either required period is absent | retain both source `observed_at`, selected revisions, `known_at`, effective sessions and evidence IDs | `SELECTED` |

The official code definitions are used literally: code `2` is the first
difference in levels, code `5` is the first difference of logs, and code `6`
is the second difference of logs. They are selected ex ante for `UNRATE` and
`CPIAUCSL`; no model-performance evidence was inspected. FRED-QD's research
notes that benchmark transformations can be reconsidered, so these codes
constrain rather than eliminate AQ scientific responsibility.

### Revision, economic-period, and session-state policy

For each selected series and target XNYS session `T`:

1. retain only evidence with `effective_session <= T`;
2. independently select the latest visible revision within each exact
   `(entity, field, observed_at)` group;
3. select the latest frequency-valid `observed_at` whose complete frozen
   transformation dependency window is available;
4. compute only the frozen transformation from those visible revisions; and
5. carry that legitimate state across later XNYS sessions until a new release
   or a newly visible constituent revision creates a new state.

Revision selection and economic-period selection are therefore separate.
When any constituent period is revised, the recomputed transformed state is
available only from that revision's own effective session forward; it is never
projected backward. A transformed state's `known_at` and `effective_session`
are the maxima across its selected constituents, while its provenance retains
the full constituent revision vector.

State carry-forward is not missing-value imputation. It means that the last
legitimately known macro state remains the state known to the market between
releases. It never manufactures an absent upstream observation, interpolates
between observations, backfills a value before availability, or bridges a
missing transform dependency. Monthly and any later-authorized quarterly
series advance independently on their native observed-period grids and may be
carried independently onto the daily XNYS session grid. Macro V1 itself has no
active quarterly feature because both GDP-family candidates are not selected.

### Minimal future Qlib feature contract

| feature_id | source_series_id | transformation | source_frequency | value_semantics | availability_semantics | provenance requirements |
|---|---|---|---|---|---|---|
| `macro_v1_cpiaucsl_d2_log` | `CPIAUCSL` | FRED-MD/QD code `6` | monthly | change in continuously compounded monthly CPI growth | first XNYS session strictly after the maximum date-only `known_at` of the three selected visible revisions; then state carry-forward | series ID, all dependency `observed_at`/`known_at`/effective sessions, values, evidence IDs, transformation code and lineage identity |
| `macro_v1_unrate_d1` | `UNRATE` | FRED-MD/QD code `2` | monthly | monthly percentage-point change in unemployment rate | first XNYS session strictly after the maximum date-only `known_at` of the two selected visible revisions; then state carry-forward | series ID, both dependency `observed_at`/`known_at`/effective sessions, values, evidence IDs, transformation code and lineage identity |

This contract freezes names and semantics only. Its intended future proof path
is Vintage + DuckDB + `exchange_calendars` + Pandera + MLflow/DVC + Qlib
`StaticDataLoader`; it does not authorize a macro feature, transformation,
state, resampling, registry, panel, or feature-store engine.

```text
MACRO_FEATURE_OBSERVED_AT_POLICY_FREEZE = PASS
MACRO_SOURCE_AUTHORITY = OFFICIAL_FRED_ALFRED
MACRO_PIT_OWNER = VINTAGE_0_9_0
MACRO_SESSION_OWNER = EXCHANGE_CALENDARS_PLUS_DUCKDB_COMPOSITION
MACRO_TRANSFORMATION_REFERENCE = FRED_MD_QD
GDP_STATUS = DEFERRED
GDP_STATUS_REASON = NO_EXACT_CURRENT_BENCHMARK_TRANSFORMATION
GDPC1_STATUS = REJECTED
GDPC1_STATUS_REASON = DISTINCT_REAL_GDP_IDENTITY_NOT_SELECTED_FOR_V1
GDP_TO_GDPC1_SILENT_SUBSTITUTION = NO
CPIAUCSL_STATUS = SELECTED
CPIAUCSL_TRANSFORMATION = CODE_6_SECOND_LOG_DIFFERENCE
UNRATE_STATUS = SELECTED
UNRATE_TRANSFORMATION = CODE_2_FIRST_LEVEL_DIFFERENCE
MACRO_V1_SELECTED_SERIES_COUNT = 2
MACRO_V1_SELECTED_SERIES = CPIAUCSL,UNRATE
BENCHMARK_TRANSFORMATION_POLICY = ADOPT_EXACT_FRED_MD_QD_CODES_FOR_SELECTED_EXACT_SERIES_ONLY
LATEST_VISIBLE_REVISION_RULE = INDEPENDENT_PER_ENTITY_FIELD_OBSERVED_AT_AS_OF_TARGET_SESSION
OBSERVED_AT_SELECTION_RULE = LATEST_FREQUENCY_VALID_OBSERVED_AT_WITH_COMPLETE_VISIBLE_TRANSFORMATION_WINDOW
MACRO_SESSION_STATE_CARRY_FORWARD = YES
UPSTREAM_MISSING_OBSERVATION_IMPUTATION = NO
INTERPOLATION = NO
BACKFILL = NO
MONTHLY_QUARTERLY_INDEPENDENT_STATE = YES
MACRO_V1_QUARTERLY_SERIES_ACTIVE = NO
PROVENANCE_PRESERVED_THROUGH_SESSION_STATE = YES
QLIB_FEATURE_CONTRACT_FROZEN = YES
AQ_MACRO_FEATURE_ENGINE_CREATED = NO
AQ_MACRO_TRANSFORMATION_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_V1_UPSTREAM_NATIVE_COMPOSITION_POC_001
FINAL_CLASSIFICATION = PASS_P6_MACRO_FEATURE_OBSERVED_AT_POLICY_FROZEN
```

## Macro V1 upstream-native composition POC (2026-09-25)

This bounded private POC exercised the frozen two-feature path without adding
repository production code or evaluating scientific performance. It reused a
relation previously produced through the public `vintage.macro` API at Vintage
0.9.0/source `c55b6d5bd801a21e5844600fc6110de4a3c8dd4b`, the existing
`aq_xnys_calendar` leaf, DuckDB 1.5.5, Pandera 0.33.1, and pinned Qlib
0.9.8.dev26/source `2fb9380b342556ddb50a4b24e4fe8655d548b2b8`.

DuckDB independently selected the latest visible revision per exact
`observed_at`, enforced consecutive monthly dependency windows, calculated the
frozen transforms, selected the latest valid economic period, and persisted
the resulting state across XNYS sessions. Independent Python arithmetic matched
both SQL formulas with maximum absolute error `0.0`. Controlled cases proved:

- missing CPI or UNRATE dependencies emit no new state;
- a zero CPI dependency emits no code-6 state;
- a later revision to an already-used UNRATE dependency changes the transformed
  state only from the revision's own safe session forward;
- revision backward leakage is zero;
- 127 session rows demonstrate legitimate state carry-forward;
- early visibility, interpolation, upstream imputation, and backfill are zero;
- `GDP` and `GDPC1` are absent.

The private provenance sidecar retains source series, transform code, every
dependency's `observed_at`, selected `known_at`, effective session, raw value
and evidence identity, plus transformed-state and upstream runtime identities.
Pandera validated both this evidence boundary and the exact two-feature Qlib
surface.

### Global-state boundary and Qlib result

Pinned Qlib's public `StaticDataLoader` can hold a time-only frame, but the
current `DataHandlerLP`/`DatasetH` research path cannot consume it as a global
feature surface: the bounded time-only probe failed at instrument-oriented
slicing (`TypeError: unhashable type: 'slice'`). Therefore native global
time-only feature support is classified `NO` for this path.

The minimal fallback used no adapter: DuckDB left-joined the global state onto
an explicitly supplied bounded `(datetime, instrument)` grid. The grid had two
synthetic instruments with different eligibility rows, so the POC could prove
that no nonexistent instrument/session row was manufactured. Every instrument
on the same eligible session received the same global macro state; the
instrument-dependent value count and manufactured-row count were both zero.

The resulting 114-row surface contained exactly
`macro_v1_cpiaucsl_d2_log` and `macro_v1_unrate_d1`, including three null cells
that exercise missingness preservation. With all feature processors empty,
`StaticDataLoader -> DataHandlerLP -> DatasetH` preserved index, row count,
column identity, dtypes, values, and missingness exactly. Canonical input and
output SHA-256 were both
`f9134b7c9e08fd3a388fa11054f1a8a3d93b3a931aa73814dbb1dfc38e287f19`.
Two complete executions produced byte-identical result and Parquet hashes.

Private evidence is under
`D:/AQ_DATA/P6/macro-v1-upstream-native-composition-poc-001`; its checksum
manifest SHA-256 is
`29cf981db3501ac7894d29ff00749deb9f9bee9183d32054ee01e413a5246a3d`.

```text
MACRO_V1_UPSTREAM_NATIVE_COMPOSITION_POC = PASS
MACRO_V1_SERIES = CPIAUCSL,UNRATE
CPI_TRANSFORMATION = FRED_CODE_6_EXACT
UNRATE_TRANSFORMATION = FRED_CODE_2_EXACT
GDP_INCLUDED = NO
GDPC1_INCLUDED = NO
VINTAGE_PUBLIC_API_USED = YES
XNYS_EXISTING_LEAF_REUSED = YES
DUCKDB_COMPOSITION_OWNER = YES
PANDERA_BOUNDARY_VALIDATION = PASS
LATEST_VISIBLE_REVISION_STATUS = PASS
TRANSFORMATION_WINDOW_STATUS = PASS
LATER_OBSERVED_AT_SAFE_SESSION_STATUS = PASS
REVISION_TRIGGERED_RECOMPUTATION = PASS
REVISION_BACKWARD_LEAKAGE_COUNT = 0
SESSION_STATE_CARRY_FORWARD = PASS
MISSING_DEPENDENCY_STATUS = PASS
CPI_NONPOSITIVE_FAIL_CLOSED = PASS
UPSTREAM_MISSING_OBSERVATION_IMPUTATION = NO
INTERPOLATION = NO
BACKFILL = NO
GLOBAL_MACRO_NATIVE_QLIB_SUPPORT = NO
GLOBAL_TO_INSTRUMENT_MECHANISM = DUCKDB_MECHANICAL_BROADCAST
INSTRUMENT_DEPENDENT_MACRO_VALUE_COUNT = 0
MANUFACTURED_INSTRUMENT_SESSION_ROW_COUNT = 0
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_IDENTITY = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_STATIC_DATA_LOADER = PASS
QLIB_DATA_HANDLER_LP = PASS
QLIB_DATASET_H = PASS
QLIB_ROUNDTRIP_EQUALITY = PASS
FEATURE_COUNT = 2
FEATURE_IDS = macro_v1_cpiaucsl_d2_log,macro_v1_unrate_d1
PROVENANCE_RECOVERABILITY = PASS
DETERMINISM = PASS
AQ_MACRO_FEATURE_ENGINE_CREATED = NO
AQ_MACRO_TRANSFORMATION_ENGINE_CREATED = NO
AQ_MACRO_QLIB_ADAPTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/macro-v1-upstream-native-composition-poc-001
PRIVATE_EVIDENCE_CHECKSUMS_SHA256 = 29cf981db3501ac7894d29ff00749deb9f9bee9183d32054ee01e413a5246a3d
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_V1_MINIMAL_PRODUCTION_MATERIALIZATION_001
FINAL_CLASSIFICATION = PASS_P6_MACRO_V1_UPSTREAM_NATIVE_COMPOSITION_POC
```

## Macro V1 minimal production materialization (2026-09-25)

The production boundary is intentionally narrow: one Python entrypoint binds
the selected upstream leaves and delegates revision selection, dependency
windows, transformations, and carry-forward to one DuckDB SQL relation. The
canonical artifact remains global by XNYS session. A 30-row real-output canary
mechanically broadcast the surface onto an explicit non-sealed instrument grid
and passed the pinned Qlib public `StaticDataLoader -> DataHandlerLP -> DatasetH`
path with exact index, value, and missingness equality.

```text
MACRO_V1_MINIMAL_PRODUCTION_MATERIALIZATION = PASS
PRODUCTION_LOCATION = 20-intelligence-system/macro-factors/macro-v1
CANONICAL_OUTPUT_ROOT = D:/AQ_DATA/P6/macro-v1-001
CANONICAL_MACRO_STORAGE_GRAIN = SESSION_GLOBAL
PERMANENT_INSTRUMENT_BROADCAST_STORAGE = NO
MACRO_V1_SERIES = CPIAUCSL,UNRATE
SESSION_START = 2015-04-01
SESSION_END = 2024-12-31
SOURCE_OBSERVED_START = 2014-12-01
SOURCE_AS_OF = 2024-12-31
EVIDENCE_ROWS = 745
MACRO_STATE_ROWS = 2455
PROVENANCE_ROWS = 611
EVIDENCE_LOGICAL_SHA256 = 281ca7ff1a18700ad1453d62d4a2f239690cedb97c413ee4639acd4766899866
MACRO_STATE_LOGICAL_SHA256 = 3dbb88c1529d259b6447fc3f2e6e2d9124efa2bce8466b12b43f631a849d20fc
PROVENANCE_LOGICAL_SHA256 = 4974edca45e48e67e61446341ba1cf3fdb037e41b5878c95ea13e9321512e55a
MANIFEST_SHA256 = 23dee6c4430d68e26068305f3e929a3c2cba59d30dd38d5ba97fd1fe6e39e44c
DVC_STAGE = p6_macro_v1_materialization
DVC_STATUS = UP_TO_DATE
DVC_OUTPUT_CACHE = FALSE
PANDERA_VALIDATION = PASS
CANONICAL_OUTPUT_DETERMINISM = PASS_LOGICAL_AND_PHYSICAL
REVISION_BACKWARD_LEAKAGE_COUNT = 0
REAL_OUTPUT_BROADCAST_CANARY = PASS
INSTRUMENT_DEPENDENT_MACRO_VALUE_COUNT = 0
MANUFACTURED_INSTRUMENT_SESSION_ROW_COUNT = 0
QLIB_REAL_OUTPUT_CANARY = PASS
PRODUCTION_PYTHON_FILE_COUNT = 1
NEW_PRODUCTION_PYTHON_LOC = 153
AQ_NEW_GENERIC_ENGINE_COUNT = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_V1_ABLATION_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_P6_MACRO_V1_MINIMAL_PRODUCTION_MATERIALIZATION
```

## Macro V1 ablation protocol freeze (2026-09-25)

The protocol freezes one family-level hypothesis and two surfaces before any
Macro V1 performance evidence exists. `M0` is the exact 157-column P2 ragged
Alpha158 OHLCV control. `M1` adds only the two canonical Macro V1 columns.
P5 fundamentals, individual macro trials, alternative transformations, and
all other information families are excluded. The future executor must reuse
the accepted P5 Attempt-005 Qlib/skfolio/arch vehicle without creating a broad
evaluation framework.

```text
MACRO_V1_ABLATION_PROTOCOL = FROZEN_PRE_EXECUTION
PROTOCOL_ARTIFACT = 30-research-system/qlib/p6-macro-v1-ablation/macro-v1-ablation-protocol.json
PROTOCOL_SHA256 = 5aad8128f9473558689b602edc91850022b0667826ee0dd8eb126fab7c58b116
CONTROL_SURFACE = BASE_157
CONTROL_FEATURE_COUNT = 157
CONTROL_FEATURE_MANIFEST_SHA256 = 7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463
CONTROL_DATASET_IDENTITY = P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135
P5_FUNDAMENTALS_INCLUDED_IN_BASELINE = NO
SURFACE_M0 = BASE_157
SURFACE_M1 = BASE_157_PLUS_EXACT_MACRO_V1_2
MACRO_INCREMENT_FEATURES = macro_v1_cpiaucsl_d2_log,macro_v1_unrate_d1
SCIENTIFIC_HYPOTHESIS_COUNT = 1
PRIMARY_SURFACE_COMPARISON_COUNT = 1
MODEL_FIT_COUNT_PLANNED = 2
TRAIN = 2015-04-01..2019-12-31
VALIDATION = 2020-01-01..2021-12-31
HISTORICAL_RESEARCH_TEST = 2022-01-03..2024-12-31
MODEL = qlib.contrib.model.gbdt.LGBModel
MODEL_CONFIG_SHA256 = f75355629e7ad6b85f100627dbc055712d7f72d1e1e31783736f1ce4cc10a61a
PRIMARY_PREDICTION_METRIC = QLIB_RANK_IC
PRIMARY_DIRECTION = M1_MINUS_M0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_V1_FIRST_AUTHORIZED_ABLATION_EXECUTION_001
FINAL_CLASSIFICATION = PASS_P6_MACRO_V1_ABLATION_PROTOCOL_FROZEN
```

## Macro V1 first authorized ablation result (2026-09-25)

The exact preregistered `M0 = BASE_157` versus
`M1 = BASE_157 + macro_v1_cpiaucsl_d2_log + macro_v1_unrate_d1` comparison
completed without performance-based branching. Both Qlib surfaces used the
same 1,196,594-row index and labels; no P5 fundamental values entered either
surface. The control-plane 401 interruption occurred before any `model.fit`;
exact recovery reused the completed BASE extraction and did not increment the
scientific attempt.

`M1` Rank IC was lower by `0.00033915849184813144`. The forward gates failed.
The reverse WalkForward gate passed, but reverse CPCV and both reverse arch
gates did not, so the complete `DEGRADED` condition was not satisfied. The
preregistered result is `NO_MEASURABLE_INCREMENTAL_VALUE`, closing Macro V1 and
retaining its materialization as historical evidence only.

```text
M0_TEST_RANK_IC = 0.0021911029598144574
M1_TEST_RANK_IC = 0.001851944467966326
M1_MINUS_M0_RANK_IC_DELTA = -0.00033915849184813144
M1_MINUS_M0_WALKFORWARD_GATE = FALSE
M0_MINUS_M1_WALKFORWARD_GATE = TRUE
M1_MINUS_M0_CPCV_GATE = FALSE
M0_MINUS_M1_CPCV_GATE = FALSE
M1_MINUS_M0_SPA_CONSISTENT_PVALUE = 0.4356
M1_MINUS_M0_REALITY_CHECK_CONSISTENT_PVALUE = 0.4356
M0_MINUS_M1_SPA_CONSISTENT_PVALUE = 0.5644
M0_MINUS_M1_REALITY_CHECK_CONSISTENT_PVALUE = 0.5644
FINAL_SCIENTIFIC_CLASSIFICATION = NO_MEASURABLE_INCREMENTAL_VALUE
POST_RESULT_MACRO_V1_STATUS = HISTORICAL_EVIDENCE_ONLY_QUESTION_CLOSED
MODEL_FIT_ATTEMPT_COUNT = 2
MODEL_FIT_COMPLETED_COUNT = 2
PREDICTION_COUNT = 2
BACKTEST_SURFACE_COUNT = 2
ABLATION_COUNT = 1
CONTROL_PLANE_INTERRUPTION_COUNT = 1
CONTROL_PLANE_INTERRUPTION_CLASSIFICATION = CODEX_AUTH_401_PRE_SCIENTIFIC_EXECUTION
SCIENTIFIC_ATTEMPT_INCREMENTED_BY_401 = NO
RECOVERY_PROTOCOL_CHANGED = NO
RECOVERY_MODEL_CONFIG_CHANGED = NO
RECOVERY_DATA_CHANGED = NO
RECOVERY_FEATURE_INVENTORY_CHANGED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/macro-v1-ablation-001/attempt-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 05383ece11ddc5ecbe26fb025323e5ffc810f9c4347f4f0552e37911128b980d
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_V1_NEGATIVE_RESULT_CLOSEOUT_001
```

## Macro V1 terminal negative-result closeout (2026-09-25)

The frozen two-feature Macro V1 question is closed at
`NO_MEASURABLE_INCREMENTAL_VALUE`. The result is scoped to that exact family
and protocol, not to macro information generally. With no active DVC
downstream dependency or feature consumer, the materialization stage is
retired from the active DAG. Source and evaluator code plus both private
evidence roots remain immutable historical reproducibility references. No
rescue search is authorized; P6 remains active and proceeds to news policy.

```text
FINAL_SCIENTIFIC_CLASSIFICATION = NO_MEASURABLE_INCREMENTAL_VALUE
MACRO_V1_ACTIVE = NO
MACRO_V1_CANDIDATE_ELIGIBLE = NO
MACRO_V1_PROMOTION_ELIGIBLE = NO
MACRO_V1_RESEARCH_QUESTION_CLOSED = YES
MACRO_V1_MATERIALIZATION_ROLE = HISTORICAL_EVIDENCE_ONLY
MACRO_V1_ACTIVE_DVC_STAGE = NO
ACTIVE_DVC_DOWNSTREAM_DEPENDENCY_COUNT = 0
MACRO_V1_ACTIVE_FEATURE_CONSUMER_COUNT = 0
MACRO_V1_FURTHER_SEARCH_AUTHORIZED = NO
MACRO_V1_CPI_ONLY_RETEST_AUTHORIZED = NO
MACRO_V1_UNRATE_ONLY_RETEST_AUTHORIZED = NO
MACRO_V1_GDP_AUTHORIZED = NO
MACRO_V1_GDPC1_AUTHORIZED = NO
MACRO_V1_MORE_SERIES_AUTHORIZED = NO
MACRO_V1_ALTERNATE_TRANSFORM_AUTHORIZED = NO
MACRO_V1_LAG_TUNING_AUTHORIZED = NO
MACRO_V1_MODEL_TUNING_AUTHORIZED = NO
MACRO_V1_HYPERPARAMETER_SEARCH_AUTHORIZED = NO
MACRO_V1_HISTORICAL_ARTIFACT_RETAINED = YES
MACRO_V1_ABLATION_EVIDENCE_RETAINED = YES
MACRO_V1_PRIVATE_MATERIALIZATION_MANIFEST_SHA256 = 23dee6c4430d68e26068305f3e929a3c2cba59d30dd38d5ba97fd1fe6e39e44c
MACRO_V1_ABLATION_EVIDENCE_CHECKSUM_SHA256 = 05383ece11ddc5ecbe26fb025323e5ffc810f9c4347f4f0552e37911128b980d
POST_MACRO_CONTROL_SURFACE = BASE_157
POST_MACRO_CONTROL_FEATURE_COUNT = 157
P6_ACTIVE = YES
P6_MACRO_V1_LANE = CLOSED_NEGATIVE
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
AQ_TERMINAL_CLOSEOUT_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_EVIDENCE_AND_SAFE_AVAILABILITY_POLICY_FREEZE_001
FINAL_CLASSIFICATION = PASS_P6_MACRO_V1_NEGATIVE_RESULT_CLOSEOUT
```

## News V1 evidence and safe-availability policy freeze (2026-09-25)

### Authority question and decision

News V1 asks what upstream evidence proves that a document already existed and
was safely usable at a historical time. It does not require a universally exact
first-publication time because that property is not generally observable. A
publication timestamp, HTML date, RSS date, GDELT `V2.1DATE`, or generic OpenBB
`date` is metadata rather than historical admission authority by default.

An admissible evidence row must have immutable source identity, exact document
identity, qualified conservative availability evidence, frozen timestamp
semantics, a safe availability no later than the research cutoff, and no
future/reprocessed metadata projected backward. If safe availability cannot be
proved, the row is rejected; `published_at` is never substituted.

### Official GDELT GKG 2.1 finding

The [official GKG 2.1 codebook](https://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf)
defines one tab-delimited row per document and the following distinct fields:

- `GKGRECORDID`: globally unique string `YYYYMMDDHHMMSS-X` or
  `YYYYMMDDHHMMSS-TX`; the prefix is the full date/time of the 15-minute update
  batch in which the record was created.
- `V2.1DATE`: the source document's publication date, not the creation batch.
- `V2SOURCECOLLECTIONIDENTIFIER`: interpretation authority for the document
  identifier. Only `1 = WEB` is automatically eligible for News V1.
- `V2SOURCECOMMONNAME`: human-readable source, normally the top-level domain
  for web material.
- `V2DOCUMENTIDENTIFIER`: unique external document identifier; for `WEB` it is
  a fully qualified URL.

The codebook does not explicitly and normatively assign a timezone to the
`GKGRECORDID` batch prefix. Related GDELT products cannot supply that missing
contract by inference. The prefix is therefore retained as timezone-unproven
date/time metadata, and only its calendar date is used for conservative
historical admission. `V2.1DATE` remains publication metadata and is not a
fallback.

GDELT's [official data page](https://gdeltproject.org/data.html) describes GKG
2.x as updating every 15 minutes, while the official launch record states the
2.x files begin on 2015-02-19. Bounded master-file checks found the required
GKG files at the research-range boundaries and direct retrieval passed:

| Official file | Master-list bytes | Master-list MD5 | Retrieved SHA-256 | Bounded sample |
|---|---:|---|---|---|
| `20150401000000.gkg.csv.zip` | 9,671,813 | `6b3348c36995a54246736e014e0d7022` | `a4edc9c182f6e59db070e014438d4b37d2c1ccc486a9dd23196189b0c24208d2` | 200 rows, 27 columns, 200 `WEB` |
| `20241231120000.gkg.csv.zip` | 3,941,030 | `d836879425b178bcb2f3dc3b2c26184e` | `55523bb4fe1153ad372296b03b2dbe8d18807381b172acab11e30146ea29a0d5` | 200 rows, 27 columns, 200 `WEB` |

Both samples had all 200 record IDs, `V2.1DATE` values, source names, URLs,
tone values, and GCAM values. Organizations were populated in 156 and 152
rows; themes in 186 and 181 rows. Sparsity is permitted by the codebook and no
field is assumed populated. Temporary archives were retired after aggregation;
no article body, HTML, or copyrighted archive entered Git.

Coverage is therefore sufficient to advance to a bounded multi-year historical
POC. This conclusion establishes endpoint/file availability over the requested
range, not complete corpus recall or content quality.

### Other upstream roles

| Upstream | Frozen role | Safe-availability meaning and limit |
|---|---|---|
| GDELT DOC / `gdeltdoc` | `SUPPLEMENTARY_QUERY_INTERFACE` | Official ArticleList is ranked/windowed and capped; use it for bounded discovery, timelines, and metadata inspection, not as the 2015-2024 dataset authority. |
| OpenBB | `NEWS_PROVIDER_GATEWAY` | Normalizes provider-specific news surfaces. Its standard `date` is documented as publication time; it is not universal safe availability. A provider-specific crawl/first-seen field requires separate proof. |
| Media Cloud | `SUPPLEMENTARY_SAFE_AVAILABILITY_AUTHORITY` | Official `indexed_date` is the timezone-aware time content was captured and processed for archive insertion. This is a conservative capture/processing upper bound, not exact publication or first availability. Account/API-key access and quotas apply; absent access does not block the primary GDELT path. |
| Common Crawl | `SUPPLEMENTARY_CAPTURE_PROVENANCE_LEAF` | CDX/WARC capture timestamp, URL, status, digest, filename, offset, and length can corroborate a known exact URL. It is not news discovery, publication time, or authority to retain WARC content. |

For the exact same URL, multiple qualified observations yield the earliest
qualified proven capture/processing observation. Each observation retains its
precision and source semantics. A date-only GDELT observation is never compared
or represented as a fabricated intraday UTC instant. Cross-document joining
requires exact identity first; fuzzy title matching, approximate URL matching,
query-parameter stripping, AMP/mobile merging, and guessed canonicalization are
not authorized.

### Session visibility compatibility

The existing P5 daily timing authority already maps a timezone-aware instant to
the first XNYS session whose market open is strictly later. News V1 reuses that
rule without a new calendar engine. Thus legitimate pre-open evidence can enter
that session, while at-open or later evidence enters the next session. For
date-only or timezone-unproven evidence, including GDELT GKG under this freeze,
the stricter rule is the first XNYS session strictly after the evidence's
calendar date.

### Native structured intelligence and evidence shape

The GKG codebook and bounded samples prove native Organizations, Enhanced
Organizations, Themes, Tone, and GCAM surfaces. Organizations are useful
upstream metadata but are not AQ ticker/CIK identity; Themes and Tone are usable
as evidence metadata; GCAM remains a challenger because the upstream surface
contains thousands of dimensions and none is selected here. These surfaces let
News V1 postpone full-text, LangExtract, and FinBERT for evidence admission.
They do not authorize a news feature family.

The minimum future evidence shape is frozen semantically as:
`source_system`, `source_record_id`, `source_collection_id`, `source_name`,
`document_identifier`, nullable `published_at`, `published_at_semantics`,
`capture_or_batch_at`, `capture_semantics`, `safe_available_at`,
`safe_available_source`, `source_metadata_digest`, `archive_locator`,
`language_or_translation_status`, and native organization/theme/tone presence
flags. Only source identity, document identity, and qualified safe availability
are mandatory for admission. This is a contract freeze, not an implementation.

```text
NEWS_EXACT_FIRST_AVAILABLE_AT = NOT_REQUIRED_NOT_UNIVERSALLY_PROVABLE
GDELT_GKG_ROLE = PRIMARY_HISTORICAL_SAFE_AVAILABILITY_EVIDENCE_CANDIDATE
GDELT_GKG_RECORD_ID_SEMANTICS = UNIQUE_RECORD_ID_WITH_15_MINUTE_CREATION_BATCH_PREFIX_NOT_PUBLICATION_TIME
GDELT_GKG_BATCH_TIMEZONE = UNPROVEN
GDELT_GKG_SAFE_AVAILABILITY_STATUS = PASS_DATE_ONLY_CONSERVATIVE
GDELT_GKG_HISTORICAL_COVERAGE_FOR_P6 = PASS
GDELT_GKG_HISTORICAL_COVERAGE_STATUS = PASS_2015_04_01_THROUGH_2024_12_31_BOUNDARY_VERIFIED
GDELT_WEB_SOURCE_COLLECTION_ONLY = YES
GDELT_DOC_ROLE = SUPPLEMENTARY_QUERY_INTERFACE
OPENBB_NEWS_ROLE = NEWS_PROVIDER_GATEWAY
OPENBB_PUBLISHED_AT = PUBLICATION_METADATA_ONLY_BY_DEFAULT
OPENBB_PUBLISHED_AT_ADMISSION_AUTHORITY = NO
MEDIA_CLOUD_ROLE = SUPPLEMENTARY_SAFE_AVAILABILITY_AUTHORITY
MEDIA_CLOUD_INDEXED_DATE = CONSERVATIVE_CAPTURE_PROCESSING_UPPER_BOUND
MEDIA_CLOUD_INDEXED_DATE_SEMANTICS = CONSERVATIVE_CAPTURE_PROCESSING_UPPER_BOUND
MEDIA_CLOUD_CREDENTIAL_REQUIREMENT = REGISTERED_ACCOUNT_API_ACCESS
COMMON_CRAWL_ROLE = SUPPLEMENTARY_CAPTURE_PROVENANCE_LEAF
COMMON_CRAWL_CAPTURE_TIMESTAMP_SEMANTICS = ARCHIVE_CAPTURE_TIME_FOR_KNOWN_URL_NOT_PUBLICATION_OR_DISCOVERY
NEWS_SAFE_AVAILABLE_AT_POLICY = EARLIEST_QUALIFIED_PROVEN_CAPTURE_OR_PROCESSING_OBSERVATION_FOR_EXACT_SAME_URL_PRECISION_PRESERVED
NEWS_SESSION_VISIBILITY_POLICY = AWARE_INSTANT_FIRST_XNYS_OPEN_STRICTLY_AFTER_INSTANT_ELSE_FIRST_XNYS_SESSION_STRICTLY_AFTER_CALENDAR_DATE
NEWS_FULL_TEXT_REQUIRED_FOR_EVIDENCE = NO
GDELT_NATIVE_ORGANIZATION_METADATA = UPSTREAM_NATIVE_PARTIAL_NOT_SECURITY_IDENTITY
GDELT_NATIVE_THEME_METADATA = UPSTREAM_NATIVE_USABLE_AS_EVIDENCE_METADATA
GDELT_NATIVE_TONE_GCAM_METADATA = TONE_UPSTREAM_NATIVE_USABLE_GCAM_CHALLENGER_ONLY_NO_DIMENSION_SELECTED
LANGEXTRACT_REQUIRED_FOR_NEWS_V1_EVIDENCE = NO
FINBERT_REQUIRED_FOR_NEWS_V1_EVIDENCE = NO
NEWS_ENTITY_TO_AQ_SECURITY_BINDING = UNRESOLVED_SEPARATE_POLICY
NEWS_FEATURE_FAMILY_SELECTED = NO
AQ_NEWS_CRAWLER_CREATED = NO
AQ_NEWS_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_GDELT_GKG_HISTORICAL_SAFE_AVAILABILITY_POC_001
FINAL_CLASSIFICATION = PASS_P6_NEWS_V1_EVIDENCE_SAFE_AVAILABILITY_POLICY_FROZEN
```

## Raw GDELT GKG historical safe-availability POC (2026-09-25)

The policy freeze was exercised on real GDELT GKG 2.1 archives without using
GDELT DOC, publisher URLs, Media Cloud, Common Crawl, article content, NLP, or
entity binding. The official master list was streamed and filtered in memory;
it was never persisted. The deterministic selection rule produced:

| Role | Selected official archive | Advertised bytes |
|---|---|---:|
| Anchor 2015-04-01 | `20150401000000.gkg.csv.zip` | 9,671,813 |
| Anchor 2017-07-04 | `20170704001500.gkg.csv.zip` | 10,014,189 |
| Anchor 2020-03-14 | `20200314000000.gkg.csv.zip` | 9,094,197 |
| Anchor 2022-01-03 | `20220103000000.gkg.csv.zip` | 2,606,082 |
| Adjacent +1 | `20220103001500.gkg.csv.zip` | 2,930,590 |
| Adjacent +2 | `20220103003000.gkg.csv.zip` | 2,822,320 |
| Adjacent +3 | `20220103004500.gkg.csv.zip` | 3,239,163 |
| Anchor 2024-12-31 | `20241231000000.gkg.csv.zip` | 5,858,646 |

The total was 46,237,000 bytes, safely below the 128 MiB limit. Every archive
matched both official advertised bytes and MD5; local SHA-256 identities are
sealed in private evidence. ZIPs were deleted after two-pass analysis and only
the bounded evidence relation and aggregate reports remain.

### Schema, identity, and exact URL results

The parser used the official 27-field ordering. Of 11,750 source rows, 11,749
were strict UTF-8 and exactly 27 fields. One row in
`20220103000000.gkg.csv.zip` failed strict UTF-8 decoding. It was counted as a
malformed row and excluded without byte replacement, heuristic repair, or
column shifting. This isolated fail-closed exclusion is not material schema
drift.

All 11,749 valid rows were source collection `1` (`WEB`). Every valid record ID
matched `YYYYMMDDHHMMSS-X` or `YYYYMMDDHHMMSS-TX`, was unique in the selected
evidence, and matched its archive batch prefix. Every WEB row had a non-empty
document identifier. No Translingual `T` record appeared in this fixed sample.

The complete four-batch 2022-01-03 window contained 2,875 unique byte-exact
URLs and zero repeat groups. This is the truthful result of the frozen window:
no URL normalization or fuzzy join was introduced merely to manufacture
duplicates. The grouping operation remains exact-string-only and retains every
source record identity.

`V2.1DATE` was equal to the batch calendar date for all 11,749 valid rows; the
less-than, greater-than, and unknown/zero counts were each zero. These are
diagnostics only. A controlled negative assertion supplied a present
`published_at` with an invalid batch identity; the row remained unadmitted and
safe availability remained null.

Native metadata presence over admitted WEB rows was:

| Surface | Rows | Presence rate |
|---|---:|---:|
| Organizations / Enhanced Organizations | 8,917 | 75.895821% |
| Themes / Enhanced Themes | 10,385 | 88.390501% |
| Tone | 11,749 | 100.000000% |
| GCAM | 11,749 | 100.000000% |

These measurements remain descriptive evidence metadata; no news feature was
selected.

### Date-only XNYS admission and cutoff

No timezone was attached to any 14-digit GKG batch prefix. The existing
`aq_xnys_calendar` owner resolved the strict-after-date rule as follows:

| Safe available date | Effective XNYS session | Usable by 2024-12-31 |
|---|---|---|
| 2015-04-01 | 2015-04-02 | Yes |
| 2017-07-04 | 2017-07-05 | Yes |
| 2020-03-14 | 2020-03-16 | Yes |
| 2022-01-03 | 2022-01-04 | Yes |
| 2024-12-31 | 2025-01-02 | No |

Thus the holiday, weekend, ordinary-session, and end-boundary cases all obey
the conservative policy, including zero leakage from the 2024-12-31 anchor
into the frozen 2024 research surface. Re-running normalization over the same
verified ZIP bytes reproduced file identities, sample order, safe dates,
sessions, exact-URL grouping, metadata counts, and diagnostics exactly.

The private evidence root contains selected-file metadata, archive checksum
identities, schema diagnostics, a deterministic first-500-WEB-row sample for
each anchor, URL aggregation, XNYS mappings, the negative fallback assertion,
the final report, and a SHA-256 manifest. It contains no archive ZIP, article
body, HTML, WARC payload, credential, or full master list.

```text
HISTORICAL_NEWS_SAFE_AVAILABILITY_OWNER = GDELT_GKG_2_1_RAW_ARCHIVE
GDELT_GKG_OWNER_DECISION = SELECTED_PRIMARY_HISTORICAL_NEWS_EVIDENCE_LEAF
SELECTED_GKG_FILE_COUNT = 8
SELECTED_GKG_COMPRESSED_BYTES = 46237000
DOWNLOAD_BUDGET_STATUS = PASS
ANCHOR_2015_04_01 = 20150401000000.gkg.csv.zip
ANCHOR_2017_07_04 = 20170704001500.gkg.csv.zip
ANCHOR_2020_03_14 = 20200314000000.gkg.csv.zip
ANCHOR_2022_01_03 = 20220103000000.gkg.csv.zip
ANCHOR_2024_12_31 = 20241231000000.gkg.csv.zip
GDELT_SELECTED_FILE_INTEGRITY = PASS
EXPECTED_MAJOR_FIELD_COUNT = 27
TOTAL_ANALYZED_ROW_COUNT = 11750
VALID_27_FIELD_ROW_COUNT = 11749
MALFORMED_ROW_COUNT = 1
WEB_ROW_COUNT = 11749
NON_WEB_EXCLUDED_ROW_COUNT = 0
INVALID_GKGRECORDID_COUNT = 0
DUPLICATE_GKGRECORDID_COUNT = 0
BATCH_PREFIX_FILE_MATCH_COUNT = 11749
BATCH_PREFIX_FILE_MISMATCH_COUNT = 0
GDELT_BATCH_TIMEZONE = UNPROVEN
SAFE_AVAILABILITY_PRECISION = DATE
FABRICATED_GDELT_INTRADAY_TIMESTAMP_COUNT = 0
EMPTY_WEB_DOCUMENT_IDENTIFIER_COUNT = 0
ADJACENT_WINDOW_FILE_COUNT = 4
UNIQUE_EXACT_URL_COUNT = 2875
EXACT_URL_REPEAT_GROUP_COUNT = 0
EXACT_URL_REPEAT_RECORD_COUNT = 0
PUBLISHED_DATE_LT_BATCH_DATE = 0
PUBLISHED_DATE_EQ_BATCH_DATE = 11749
PUBLISHED_DATE_GT_BATCH_DATE = 0
PUBLISHED_DATE_UNKNOWN_OR_ZERO = 0
GDELT_TRANSLINGUAL_ROW_COUNT = 0
ORGANIZATION_METADATA_PRESENCE_RATE = 0.7589582092092944
THEME_METADATA_PRESENCE_RATE = 0.8839050131926122
TONE_METADATA_PRESENCE_RATE = 1.0
GCAM_METADATA_PRESENCE_RATE = 1.0
XNYS_DATE_ONLY_MAPPING_STATUS = PASS
END_BOUNDARY_FUTURE_SESSION_LEAKAGE_COUNT = 0
PUBLISHED_AT_FALLBACK_USED = NO
PUBLISHED_AT_FALLBACK_CONTROL_ASSERTION = PASS_NOT_ADMITTED
SOURCE_ARTICLE_REQUEST_COUNT = 0
GDELT_DOC_REQUEST_COUNT = 0
COMMON_CRAWL_CORROBORATION = NOT_REQUIRED
NORMALIZATION_DETERMINISM = PASS
NEWS_ENTITY_TO_AQ_SECURITY_BINDING = UNRESOLVED_SEPARATE_POLICY
NEWS_FEATURE_FAMILY_SELECTED = NO
LLM_CALL_COUNT = 0
FINBERT_INFERENCE_COUNT = 0
LANGEXTRACT_INFERENCE_COUNT = 0
AQ_NEWS_CRAWLER_CREATED = NO
AQ_NEWS_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-gdelt-gkg-historical-safe-availability-poc-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = dcca9cfa4e041b5f08c54ae95f7834ea3a3a761685e0790c48fb05f0e8a314f6
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_ENTITY_TO_SECURITY_UPSTREAM_SUBSTITUTION_AUDIT_001
FINAL_CLASSIFICATION = PASS_P6_NEWS_V1_GDELT_GKG_HISTORICAL_SAFE_AVAILABILITY_POC
```
