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
