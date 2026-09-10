# P1 US equity data provider decision 001

**Task:** `AUTONOMOUS-QUANT-P1-SHARADAR-UPSTREAM-FIT-POC-001`
**Status:** `PASS_WITH_CREDENTIAL_REQUIRED`
**Decision date:** `2026-09-10`
**Scope:** upstream fit and bounded metadata POC only; no permanent dataset, prices, model, performance, or trading.

## Decision

`SHARADAR` is recommended as `PRIMARY_US_EQUITY_REFERENCE_DATA` for the first P1 dataset acquisition. It supplies the four upstream datasets the project needs as one coherent product family: historical S&P 500 membership, a securities master, active and delisted daily prices, and corporate actions. AQ must not rebuild these datasets. AQ owns only a thin normalization adapter, deterministic snapshot/hash mechanics, validation gates, and Qlib materialization.

The recommendation is conditional on acquiring user-provided Sharadar access. No credential was found in the process, user, or machine environment under the common Sharadar/Nasdaq Data Link variable names. No secret was printed or persisted, no account was created, and no subscription was purchased. The official `test-api-key` returned a bounded TICKERS sample, while SP500 and ACTIONS returned `Exceeds free tier`; therefore a full data POC was not executed.

Official sources used:

- [Sharadar S&P500 constituents](https://sharadar.com/docs/sp500)
- [Sharadar tickers and metadata](https://sharadar.com/docs/tickers)
- [Sharadar stock prices](https://sharadar.com/docs/stocks)
- [Sharadar corporate actions](https://sharadar.com/docs/actions)
- [Sharadar bulk downloads](https://sharadar.com/docs/bulk)
- [Nasdaq Data Link table API](https://docs.data.nasdaq.com/docs/tables-1)
- [Norgate data content](https://norgatedata.com/data-content-tables.php)
- [Norgate subscription tiers](https://norgatedata.com/prices.php)
- [Norgate Python package](https://pypi.org/project/norgatedata/)

## Official table contracts

### SP500

Official history begins January 1998 and includes current constituents, additions, removals, their effective dates, and historical quarterly snapshots. Required fields are `date`, `action`, `ticker`, `name`, `contraticker`, `contraname`, and `note`; the primary key is `date,ticker,action`. This directly covers 2010-2024.

Deterministic AQ semantics: preserve the raw upstream file; sort normalized events by `(date, action, ticker, contraticker)`; resolve the event ticker to upstream identity valid for that event; open an interval on an `added` effective date and close it on a `removed` effective date; emit half-open `[membership_start, membership_end)` intervals. `current` rows and quarterly snapshots are independent terminal/intermediate validation anchors, not substitutes for event history.

### TICKERS

The official securities master covers active and delisted records from June 1990. Required fields are `table`, `permaticker`, `ticker`, `name`, `exchange`, `isdelisted`, `category`, `cusips`, `figi`, `relatedtickers`, `currency`, `firstadded`, `firstpricedate`, `lastpricedate`, `lastupdated`, and `secfilings`.

Sharadar defines `permaticker` as a unique, unchanging **issuer** identifier. AQ must preserve that upstream fact and must not relabel it as an infallible security-level identifier. Security/series disambiguation remains upstream-derived from the TICKERS row (`table`, `permaticker`, `ticker`, price-date bounds, category, FIGI/CUSIPs) plus ACTIONS relationships. This is sufficient for a thin deterministic join, including reused tickers, without inventing an AQ corporate lineage database.

### STOCKS / SEP

Official stock-price history begins December 1997 and covers active and delisted US public stocks. Required fields are `ticker`, `date`, split-adjusted `open`, `high`, `low`, `close`, split-adjusted `volume`, `closeadj`, `closeunadj`, and `lastupdated`.

The three distinct price meanings are:

- `closeunadj`: unadjusted close as traded;
- `open/high/low/close/volume`: split-adjusted OHLCV;
- `closeadj`: adjusted for splits, cash dividends, and spinoffs (total-return style).

No final P1 price policy is selected by this fit POC. Candidate use is split-adjusted OHLCV for Qlib price/volume features, an explicitly certified label field for future returns, and unadjusted close plus ACTIONS for corporate-action validation. Before `closeadj` can feed labels, tests must prove point-in-time adjustment-factor availability, split-event reconciliation, dividend/spinoff as-of behavior, no future-action leakage, revision stability, and reproducibility from a frozen raw snapshot. Total-return adjustment must never silently enter feature history.

### ACTIONS

Official history begins January 1998 and covers active and delisted tickers. Required fields are `date`, `action`, `ticker`, `name`, `value`, `contraticker`, and `contraname`; the primary key uses date, ticker/name, action, and contra fields. Official coverage includes ticker changes, splits, dividends, spinoffs, ADR ratio changes, listings, delistings/reasons, acquisition counterparties, and relations among securities of one issuer.

Stable linkage policy is upstream-first: same-issuer ticker changes use `permaticker` and `relatedtickers`; mergers, spinoffs, acquisitions, listings, and delistings use ACTIONS/contra relationships and distinct TICKERS rows; ticker reuse is separated by different upstream records, identities, metadata, and date bounds. AQ records the upstream result and does not hard-code lineage corrections.

## Bounded identity POC

The official public `test-api-key` returned only TICKERS metadata. It did not authorize ACTIONS/SP500 rows, so action-level confirmation remains `NOT_TESTABLE_WITH_CURRENT_ACCESS`. The following observations are direct sample results, not hand-built corrections:

| Case | Identity result | Action result | Price linkage |
|---|---|---|---|
| FB / META | `UPSTREAM_IDENTITY_RESOLVED`: META has permaticker `194817`, related `FB`; the reused current FB ETF is separately permaticker `644713` | not testable | META row supplies 2012-05-18 onward price bounds |
| CDAY / DAY | `UPSTREAM_IDENTITY_RESOLVED`: DAY permaticker `119466`, related `CDAY`, delisted flag and complete price bounds | not testable | linkable by upstream row/bounds |
| RE / EG | `UPSTREAM_IDENTITY_RESOLVED`: EG permaticker `196236`, related `RE` | not testable | linkable from 1995-10-03 |
| KORS / CPRI | `UPSTREAM_IDENTITY_RESOLVED`: CPRI permaticker `192178`, related `KORS` | not testable | linkable from 2011-12-15 |
| WLTW / WTW | `UPSTREAM_IDENTITY_RESOLVED`: WTW permaticker `195815`, related `WLTW WSH` | not testable | linkable from 2001-06-12 |
| DLPH / APTV | `UPSTREAM_IDENTITY_RESOLVED`: APTV permaticker `192339`, related old DLPH; new Delphi Technologies/DLPH is separately permaticker `121395`, delisted 2020-10-01 | not testable | both upstream series have distinct price bounds |
| DISCK / WBD | `UPSTREAM_IDENTITY_RESOLVED`: WBD permaticker `193488`; DISCK secondary class separately permaticker `119313`, last price 2022-04-08; rows are related | not testable | distinct predecessor/successor series are linkable |

The sample establishes upstream identity and price-series linkability for all seven cases. A paid-access acquisition preflight must still query ACTIONS and SP500 for the exact transitions before creating a permanent snapshot.

## Survivorship and bulk feasibility

STOCKS explicitly includes active and delisted securities, and TICKERS exposes `isdelisted`, first/last price dates, and the full delisted universe. Historical members remain queryable by their upstream ticker/security record and date bounds; this avoids a current-tickers-only universe.

All four tables support filtered API calls and compressed full/5/10-year bulk files. Current official status examples report approximately: STOCKS `950.9 MB`, ACTIONS `9.39 MB`, TICKERS `3.74 MB`, and SP500 `246.6 KB` compressed. The required raw bundle is therefore about `1 GB compressed`; a conservative local working/snapshot allowance is several GB after extraction, normalization, manifests, and Qlib materialization. This fits the 256 GB policy but must be measured before acquisition.

Future deterministic root: `D:\AQ_DATA\P1\sharadar\`. Expected order is `raw/{tickers,actions,sp500,stocks}` then immutable download metadata/checksums, normalized identity/membership/market panels, DatasetSnapshot manifest, and finally Qlib materialization. Absolute paths are excluded from logical snapshot identity. This POC downloaded none of these files.

## Thin Qlib adapter

Design target: `10-data-system/asset-adapters/sharadar/`.

One adapter package should: validate raw schemas; preserve upstream identity fields; resolve date-effective source/price series using TICKERS and ACTIONS; convert SP500 events to logical membership intervals; normalize STOCKS into `MarketDataPanel`; build content-addressed `DatasetSnapshot`; and expose a separate Qlib instrument symbol for each materialized series. It must not copy Sharadar's security master, corporate-action logic, or constituent database into AQ. Complexity classification: `THIN_BOUNDED_ADAPTER`.

## Norgate fallback

Norgate provides a daily Boolean historical-index-constituent series with S&P 500 history, delisted US securities, and stable `assetid` access. Historical constituents and delisted coverage require US Stocks Platinum or Diamond. Its Python client requires Microsoft Windows, an active subscription, and the Windows-only Norgate Data Updater running. This makes it a strong fallback/independent validator but a poorer fit for the project's Linux-friendly ingestion path. It is not installed or purchased, and it must not be mixed into the initial Sharadar snapshot.

```text
NORGATE_ROLE = FALLBACK_OR_INDEPENDENT_VALIDATION
```

## Experimental branch policy and state

```text
agent/p1-minimal-quant-data-protocol-001
HEAD = 702116b2b0b99a3a6e4ea21161f73d2f414d0742
ROLE = PIT_DIAGNOSTIC_REFERENCE_ONLY
POLICY = DO_NOT_MERGE / DO_NOT_EXTEND

P0 = COMPLETE
P1 = NOT_STARTED
CURRENT_NEXT = P1_SHARADAR_DATASET_ACQUISITION
```

Useful diagnostics from that branch may later cross-check vendor data, but it is not the primary path and was neither modified nor deleted by this task.

## Acquisition prerequisites

The remaining blocker is commercial/access validation, not a demonstrated technical capability gap. Before a permanent DatasetSnapshot: the owner supplies a credential with SP500, TICKERS, STOCKS, and ACTIONS entitlements; AQ runs bounded schema/action/price checks for the seven cases; verifies exact licensed export/snapshot rights; records bulk status sizes/timestamps; and freezes adjustment-correctness test expectations. Only then may the separate dataset-acquisition task download 2010-2024.
