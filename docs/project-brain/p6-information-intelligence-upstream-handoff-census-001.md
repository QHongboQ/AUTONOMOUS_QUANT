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
