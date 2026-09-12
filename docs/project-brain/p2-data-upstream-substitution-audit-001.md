# P2 Data Upstream Substitution Audit 001

## Status and scope

```text
TASK = AUTONOMOUS-QUANT-P2-DATA-UPSTREAM-SUBSTITUTION-AUDIT-001
AUDIT_DATE = 2026-09-11
BASE_MAIN = 77b6a3b2bbfa32e58c72cdcbbd10c7f336f02c6c
P2_DATA_UPSTREAM_SUBSTITUTION_AUDIT = COMPLETE
FINAL_CLASSIFICATION = PASS_WITH_DEFERRED_DECISIONS
```

This was a source and architecture audit only. It made no provider request,
downloaded no market data, installed no dependency, and added no production
runtime. Its question was: which mature upstream owns each generic part of the
P2 certification-data path, and what is the smallest AQ-specific remainder?

## Mandatory ownership preamble

```text
CAPABILITY = P2 certification-data acquisition, evidence, composition,
             validation, versioning, and Qlib handoff
UPSTREAM_OWNER = MIXED; resolved by the matrix below
OWNERSHIP_MODE = MIXED
UPSTREAM_ALREADY_DEPLOYED = PARTIAL
AQ_IMPLEMENTATION_ALLOWED = ONLY THIN ADAPTER / CONTRACT / POLICY /
                            ORCHESTRATION / DOMAIN FACTS
AQ_ALLOWED_SCOPE = adapter, contract, policy, orchestration, domain-facts,
                   provenance
CUSTOM_ENGINE_REQUIRED = NO
CUSTOM_ENGINE_REJECTION_EVIDENCE = NONE
```

The controlling rules are:

```text
NO AQ ENGINE WITHOUT UPSTREAM REJECTION EVIDENCE
TREE != SELF-WRITTEN IMPLEMENTATION MAP
TREE = RESPONSIBILITY AND MAINTENANCE MAP
```

## Pinned upstream evidence

The following source revisions were inspected rather than relying on product
marketing:

| Candidate | Pinned evidence | License / maturity evidence | Finding |
|---|---|---|---|
| OpenBB | `OpenBB-finance/OpenBB@3e071fcc2cd9f891cac6040ae60296dba76dab46` | Root license AGPL-3.0; active provider/standard-model architecture | Adopt as provider gateway, not as data authority |
| yfinance | `ranaroussi/yfinance@3d9d2f0cacb662bff689874cd6113bae3a30a885` | Apache-2.0; active, broadly adopted | Adopt Yahoo acquisition behind OpenBB |
| Qlib Yahoo collector | `microsoft/qlib@2fb9380b342556ddb50a4b24e4fe8655d548b2b8` | Existing pinned Qlib authority | Research-only bulk collector |
| edgartools | `dgunning/edgartools@abe44344c56cf4bfb5443e0debca7e39342f6e7a`, release `5.58.0` | MIT; active releases | Adopt SEC access and parsing leaf |
| DuckDB | `duckdb/duckdb@10de9573794001c649621013bdd93553b54e00c9` | MIT; mature and active | Adopt local relational composition leaf |
| riazarbi/sp500-scraper | `194ca2acc92499c290288609cf0c6fa8aa711c60` | No license found; automated snapshots and heuristic pre-2022 reconstruction | Reference/cross-check only |
| michaelk95/market_data | `081a37b81dfd9bda7e9c6460cf5bba549c9897cb` | AGPL-3.0; very low adoption; application-specific collector/orchestrator | Reference only; do not vendor |
| LIVE15_QUANT_V2 | `c312e4c4dfbb94375578e9b346564c6cf59522cc` | User repository; no repository license found | Architecture pattern only |
| LIVE15_QUANT | `470388e471b784bb58bf77a7189f9899188ba245` | User repository; no repository license found | Recorder runtime not applicable |

Primary implementation evidence:

- OpenBB's provider registry loads provider extensions, its standard
  `EquityHistorical` model supplies a common contract, and its yfinance and
  Alpha Vantage fetchers implement provider-specific query transformation,
  extraction, and normalization. See the pinned
  [OpenBB provider source](https://github.com/OpenBB-finance/OpenBB/tree/3e071fcc2cd9f891cac6040ae60296dba76dab46/openbb_platform).
- The pinned [yfinance source](https://github.com/ranaroussi/yfinance/tree/3d9d2f0cacb662bff689874cd6113bae3a30a885)
  owns Yahoo session/transport and exposes adjustment, actions, timeout, and
  repair controls. Its `repair` path can reconstruct detected price anomalies;
  that is useful research behavior, not raw certification evidence.
- The pinned [Qlib Yahoo collector](https://github.com/microsoft/qlib/tree/2fb9380b342556ddb50a4b24e4fe8655d548b2b8/scripts/data_collector/yahoo)
  retries collection, handles unavailable symbols, normalizes/deduplicates,
  calendar-reindexes, adjusts values, and contains anomaly correction logic.
  Those transformations make it appropriate for research bulk collection but
  not the authority for preserved raw certification observations.
- [edgartools](https://github.com/dgunning/edgartools/tree/abe44344c56cf4bfb5443e0debca7e39342f6e7a)
  provides SEC company/CIK lookup, filing retrieval (including 8-K), XBRL and
  Company Facts parsing, and throttled/cached HTTP machinery. CUSIP support is
  present in bounded filing/reference contexts, not as a universal PIT
  security master.
- DuckDB natively reads and writes Parquet with projection/filter pushdown and
  multi-file provenance support, and SQL supplies union, anti-join, grouping,
  and conflict queries. See the official
  [Parquet overview](https://duckdb.org/docs/stable/data/parquet/overview) and
  [FROM/JOIN syntax](https://duckdb.org/docs/stable/sql/query_syntax/from).
- OpenFIGI maps third-party identifiers to permanent FIGIs and related
  metadata. It is an identifier lookup/evidence source; its API does not own
  AQ's date-bounded accepted S&P membership episodes. See the official
  [OpenFIGI API documentation](https://www.openfigi.com/api/documentation) and
  [FIGI overview](https://www.openfigi.com/about/overview).

No Alpha Vantage account, key, or request was used. Its OpenBB extension is
technically suitable as the initial integration candidate, but provider rights,
free-tier coverage, timing semantics, and actual gap coverage require a later
bounded authority audit before adoption.

## Capability ownership matrix

`CUSTOM_ENGINE_REQUIRED` is `NO` for every row. No upstream was rejected in a
way that justifies a generic AQ engine.

| ID | Capability | Upstream candidate / owner | Mode | Decision | Reason | AQ remaining scope | Rejection evidence |
|---|---|---|---|---|---|---|---|
| A | Market-data provider access | Quantiacs directly; OpenBB for compatible providers | `UPSTREAM_WHOLE` | ADOPT | Existing SDK/gateway paths own provider access | Select provider and enforce certification policy | None |
| B | Yahoo acquisition | OpenBB yfinance provider / yfinance | `UPSTREAM_WHOLE` | ADOPT | Mature upstream owns Yahoo transport and mapping | Explicit request policy and evidence boundary only | None |
| C | Alternate/free acquisition | Alpha Vantage through OpenBB | `UPSTREAM_WHOLE` | DEFER | Integration exists; rights/coverage not yet qualified | Later bounded authority decision | None |
| D | SEC filing and issuer-event retrieval | edgartools | `UPSTREAM_LEAF` | ADOPT | Owns SEC retrieval, parsing, throttling, and filing models | Decide whether fact validates an episode | None |
| E | Ticker/CIK/FIGI/identity evidence | edgartools, OpenFIGI, provider IDs | `UPSTREAM_LEAF` + `AQ_OWNED` | ADOPT | Upstreams own lookup; none owns accepted AQ PIT semantics | Thin episode facts and evidence acceptance | None |
| F | HTTP transport | Provider SDK, OpenBB, edgartools | upstream-native | KEEP | Each selected upstream already owns transport | Configuration only | None |
| G | Authentication | Provider SDK / OpenBB credentials | upstream-native | KEEP | Authentication is provider-specific | Secret references and permission policy only | None |
| H | Retries/backoff | Provider SDK / OpenBB / edgartools | upstream-native | KEEP | No demonstrated adapter gap | None now; later narrow config if evidenced | None |
| I | Pagination | Provider SDK / edgartools | upstream-native | KEEP | Provider semantics belong with provider | Completion policy only | None |
| J | Response caching | Provider SDK / edgartools; DVC after acceptance | upstream-native | DEFER | No separate generic cache requirement exists | Retention/rights policy | None |
| K | Provider normalization | OpenBB provider fetchers; direct provider SDK where applicable | `UPSTREAM_WHOLE` | ADOPT | Standard models and provider transforms already exist | Thin translation to AQ domain row contract | None |
| L | Source provenance | Provider metadata + AQ thin contract + DVC | `AQ_OWNED` contract | KEEP | Meaning of accepted evidence is project-specific | Provider/version/request/time/rights/hash fields | None |
| M | Cross-provider composition | DuckDB | `UPSTREAM_LEAF` | ADOPT | SQL owns deterministic relational execution | Source-precedence policy and query parameters | None |
| N | Duplicate/conflict detection | DuckDB + Pandera domain checks | `UPSTREAM_LEAF` | ADOPT | SQL grouping/anti-joins plus schema mechanics suffice | Blocking domain thresholds/invariants | None |
| O | Trading-session authority | exchange_calendars XNYS | `UPSTREAM_LEAF` | KEEP | Existing accepted session authority | Select calendar/version | None |
| P | Schema validation | Pandera | `UPSTREAM_LEAF` | KEEP | Existing accepted validation mechanics | Domain-specific invariants | None |
| Q | Dataset snapshot/reproducibility | DVC | `UPSTREAM_LEAF` | KEEP | Owns dependency/content versioning | Thin DatasetSnapshot domain metadata | None |
| R | Local joins/gap detection | DuckDB | `UPSTREAM_LEAF` | ADOPT | Relational engine supplies joins and coverage queries | Gap definition and precedence policy | None |
| S | Qlib downstream ingestion | Qlib | `UPSTREAM_WHOLE` | KEEP | Existing validated dataset/research runtime | Validated frozen handoff configuration | None |
| T | Certification acceptance/fail-closed policy | AQ | `AQ_OWNED` | KEEP | Project authority cannot be delegated to a data tool | Acceptance rules and blocking findings | None |
| U | Terminal-event policy | AQ, using upstream evidence retrieval | `AQ_OWNED` | KEEP | Provider/filing facts do not decide AQ terminal acceptance | Evidence-backed terminal decision | None |
| V | PIT membership/ticker reuse/episode ownership | AQ `InstrumentEpisodeV1` | `AQ_OWNED` thin domain | KEEP | No candidate owns accepted project-specific PIT semantics | Date-bounded facts only; no generic security master | None |

## Provider-specific decisions

### OpenBB and Yahoo

```text
OPENBB = ADOPT
OPENBB_ROLE = DATA_PROVIDER_GATEWAY
OPENBB_IS_CERTIFICATION_AUTHORITY = NO
YFINANCE = ADOPT_BEHIND_OPENBB
YAHOO_PROVIDER_ACCESS_OWNER = OPENBB_YFINANCE_PROVIDER
QLIB_YAHOO_COLLECTOR = RESEARCH_ONLY
```

For any later Yahoo certification pilot, adjustment and repair settings must be
explicit, provider actions/metadata must be retained where permitted, and the
pilot must separately qualify authority, revision, missing-symbol, and
retention behavior. The gateway does not make Yahoo certification-grade.

Quantiacs remains a direct primary candidate because OpenBB does not own its
native access path and wrapping it would not remove a generic AQ capability.

### Alpha Vantage

```text
ALPHA_VANTAGE_VIA_OPENBB = DEFER
DIRECT_AQ_CLIENT_REQUIRED = NO
```

A later audit may exercise only OpenBB's provider integration. It must not
start by creating `AQ AlphaVantageClient`.

### SEC and identity

```text
EDGARTOOLS = ADOPT
EDGARTOOLS_ROLE = SEC_EDGAR_ACCESS_AND_PARSING
OPENFIGI_ROLE = IDENTIFIER_LOOKUP_AND_SUPPORTING_EVIDENCE
POINT_IN_TIME_EPISODE_AUTHORITY = AQ_INSTRUMENT_EPISODE_V1
AQ_GENERIC_SECURITY_MASTER = PROHIBITED
```

SEC/CIK/CUSIP/FIGI evidence can support a decision. It cannot silently create,
merge, or extend an index-membership episode.

### Local composition

```text
DUCKDB = ADOPT
DUCKDB_ROLE = LOCAL_DETERMINISTIC_RELATIONAL_COMPOSITION
SOURCE_PRECEDENCE_POLICY_OWNER = AQ
GENERIC_COMPOSITION_ENGINE_OWNER = DUCKDB
```

For example, AQ may declare `QUANTIACS` followed by one explicitly accepted
gap-fill source. DuckDB executes union, anti-join, duplicate/conflict, coverage,
and provenance queries; AQ must not write a generic DataFrame merge engine.

## Existing project and reference audits

### LIVE15

LIVE15_QUANT_V2's ingress documents correctly separate provider-owned
transport, typed narrow ports, parent composition, and immediate project-domain
translation. That boundary is reusable as a design pattern only. The examined
implementation is Kalshi-specific and the repository exposes no license that
would support copying it here.

LIVE15_QUANT V1's WebSocket recorder, archive/chunk, lease, replay, retention,
SQLite, manifest, gap, and sequence machinery solve a different streaming
problem. They are not applicable to daily equity certification and must not be
ported.

```text
LIVE15_V2_REUSE = PATTERN_ONLY
LIVE15_V1_RECORDER_REUSE = NO
```

### Historical S&P projects

The existing FJA-derived history remains the reconciled AQ PIT evidence base;
pitindex shares that ancestry and is diagnostic, not an independent vote.
Other historical projects, including `riazarbi/sp500-scraper`, may locate or
cross-check evidence but do not replace accepted facts. The absence of a usable
license and heuristic reconstruction are additional reasons not to copy its
data/code into authority. Older/unlicensed constituent projects likewise remain
reference-only.

### Third-party market-data pipelines

`michaelk95/market_data` is a custom yfinance/FRED collector, stateful
orchestrator, Parquet merger, and survivorship-mitigation application. It is
AGPL-3.0, has minimal adoption, and duplicates capabilities already assigned to
OpenBB/yfinance, DuckDB, DVC, and AQ policy. It is `REFERENCE_ONLY`; no code is
vendored or copied.

## HTTP, retry, and cache decision

```text
TENACITY = DEFER
REQUESTS_CACHE = DEFER
REASON = CURRENT_SELECTED_UPSTREAMS_OWN_TRANSPORT
```

Adding libraries merely because they exist would add dependencies without
removing project code. If a future thin adapter proves one missing behavior,
that task may audit a narrow upstream leaf. It still may not create AQ retry,
HTTP, or cache engines.

## Target ownership topology

```text
Quantiacs direct primary candidate          -> provider-owned acquisition
OpenBB                                      -> compatible-provider gateway
  yfinance                                  -> Yahoo acquisition
  Alpha Vantage provider (deferred)         -> alternate acquisition
edgartools                                  -> SEC retrieval/parsing
OpenFIGI (supporting only)                  -> identifier lookup evidence
DuckDB                                      -> local relational composition
Pandera                                     -> schema-validation mechanics
exchange_calendars                          -> XNYS session authority
DVC                                         -> snapshot/dependency versioning
Qlib                                        -> downstream dataset/research runtime

AQ InstrumentEpisodeV1                     -> thin PIT identity/membership facts
AQ source-precedence policy                 -> accepted source order
AQ provenance contract                      -> evidence meaning and traceability
AQ certification fail-closed policy         -> acceptance/rejection authority
AQ terminal acceptance policy               -> evidence-backed terminal decision
AQ orchestration/configuration              -> compose upstream leaves
```

## Prohibited AQ engines

Unless a later task first records explicit upstream rejection evidence, the
following are prohibited:

- AQ generic downloader or provider registry;
- AQ HTTP framework, retry engine, or cache engine;
- AQ SEC downloader, scraper, or parser;
- AQ trading-calendar or schema engine;
- AQ generic security master;
- AQ generic DataFrame merge/composition engine;
- AQ artifact cache, manifest, or dataset-version engine;
- AQ training-data, binary-storage, model-data-loader, or research engine.

The existing thin `DatasetSnapshot` metadata contract does not become a
generic manifest engine; DVC owns snapshot mechanics. Quantiacs durable raw
retention remains blocked until provider rights are confirmed.

## Implementation footprint

No generic engine remains for AQ to implement. A later runtime may contain only
the following bounded components:

| Component | Classification | Limit |
|---|---|---|
| Provider selection and version configuration | `CONFIG_ONLY` | No provider registry engine |
| Direct-provider/OpenBB result-to-domain mapping | `THIN_ADAPTER` | One accepted boundary per source |
| `InstrumentEpisodeV1` and thin provenance/DatasetSnapshot fields | `DOMAIN_CONTRACT` | Project facts, not generic masters/manifests |
| Source precedence, terminal acceptance, and fail-closed certification | `POLICY` | No relational/validation engine |
| Calls to DuckDB, Pandera, calendars, DVC, and Qlib | `ORCHESTRATION` | Declarative/bounded composition |

```text
CUSTOM_ENGINE_REQUIRED = NO
CUSTOM_ENGINE_REJECTION_EVIDENCE = NONE
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
ARCHITECTURE_DRIFT = NO
```

## Non-actions and authoritative next state

No Quantiacs, Yahoo, Alpha Vantage, OpenBB provider, SEC, OpenFIGI, Robinhood,
or account-data call was made. No market data was downloaded. No model,
backtest, or trading action ran.

```text
P2_CERTIFICATION = STARTED / IN_PROGRESS
P2_CERTIFIED_DATA_FOUNDATION = IN_PROGRESS
QUANTIACS_FREE_DATA_PILOT_CORRECTION = COMPLETE
QUANTIACS_PILOT_RESULT = PASS_TECHNICAL_PILOT_FREE_GAP_FILL_REQUIRED
P2_DATA_UPSTREAM_SUBSTITUTION_AUDIT = COMPLETE
DATA_GENERIC_ENGINE_POLICY = UPSTREAM_FIRST_NO_CUSTOM_ENGINE_WITHOUT_REJECTION_EVIDENCE
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PIT_UNIVERSE_CERTIFIED = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
LIVE_CAPITAL = NOT_AUTHORIZED
CURRENT_NEXT = P2_DATA_PILOT_LOCAL_HYGIENE_AUDIT
AFTER_LOCAL_HYGIENE = P2_FREE_DATA_GAP_FILL_AUTHORITY_AUDIT
```
