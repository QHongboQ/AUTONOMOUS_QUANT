# P2 Free Data Secondary Gap-Fill Decision 001

**Task:** `AUTONOMOUS-QUANT-P2-FREE-DATA-SECONDARY-GAP-FILL-DECISION-001`
**Base:** `bf0d7fcbac3bcf4fdf75fc147b6530b31e74d6c9`
**Result:** `PASS_WITH_UNRESOLVED_AUTHORITY`

## Scope and ownership

This was a documentation-only upstream decision audit. It did not create an
account or API key, call a provider API, download data, install software, or
implement a provider client. Official provider material was reviewed only for
SimFin, Stooq, Alpha Vantage, EODHD, and Nasdaq Data Link US EOD.

```text
CAPABILITY = FREE_SECONDARY_CERTIFICATION_DATA_CANDIDATE_SELECTION
UPSTREAM_OWNER = SELECTED_PROVIDER_OFFICIAL_INTERFACE
OWNERSHIP_MODE = UPSTREAM_WHOLE
AQ_IMPLEMENTATION_ALLOWED = BOUNDED_EVIDENCE_INTERPRETATION_AND_POLICY_ONLY
NO_AQ_ENGINE_WITHOUT_UPSTREAM_REJECTION_EVIDENCE = ENFORCED
TREE = RESPONSIBILITY_AND_MAINTENANCE_MAP
NEW_PROVIDER_FRAMEWORK_CREATED = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
CUSTOM_ENGINE_REQUIRED = NO
```

The previously observed hard gaps remain unchanged:

- Facebook/Meta historical `FB` episode through 2022-06-08;
- `DISCK` on 2022-04-08;
- Qwest Communications International Inc. (CIK `0001037949`), historical
  NYSE ticker `Q`, whose listing ceased after the 2011-04-01 merger close.

Quantiacs, Yahoo, and Tiingo were not re-tested. No certification window was
selected or changed.

## Decision gates

A provider could be selected for one later bounded technical authority audit
only if official material established a credible path for free access, useful
2022 history, locally retained personal research while authorized, identity
stronger than an unqualified ticker, and a mature upstream interface. Revision
addressability could remain unresolved only if explicitly carried into that
next audit. Selection is not acceptance as certification authority.

## SimFin

### Official entitlement and interface

SimFin's current pricing page identifies a `$0` FREE account with no billing,
5 years of chart history, Data API and bulk download, daily stock prices,
trading volume, and a 5-year delayed bulk-download history. The same page
assigns longer price-history entitlements to paid tiers, so generic SimFin
claims of 20+ years are not used as the FREE entitlement.
[SimFin pricing and feature matrix](https://www.simfin.com/en/prices/)

SimFin's official Python package documents a free API key obtained by account
registration, daily share-price bulk data, local on-disk caching, and a mature
Python download interface. Its official field definitions describe `Open`,
`High`, `Low`, and `Close` as split-adjusted but not dividend-adjusted,
`Adj. Close` as split- and dividend-adjusted total return, and volume as part
of the daily share-price dataset.
[SimFin official Python package](https://github.com/SimFin/simfin)
[SimFin official field definitions](https://github.com/SimFin/simfin/blob/master/simfin/names.py)

### Identity

The official field definitions call `SimFinId` a unique company identifier
that is useful when multiple companies have the same ticker at different
points in time or when a company has no ticker. This is materially stronger
than bare-ticker resolution and creates a credible path for the FB and Qwest
reuse cases. The bounded official review did not establish how the current
FREE share-price entitlement exposes every historical delisted episode, so
delisted coverage remains unresolved until a technical audit.

```text
SIMFIN_STABLE_IDENTITY = PASS
SIMFIN_DELISTED_SECURITY_SUPPORT = UNRESOLVED
SIMFIN_TICKER_REUSE_HANDLING = CREDIBLE_SIMFIN_ID_PATH_NOT_YET_TESTED
```

### Retention and use boundary

SimFin's current Data License Agreement grants FREE/BASIC licensees a
non-exclusive right to use data for personal, non-commercial research. Its
general terms permit copies solely for use under the granted rights. The
pricing FAQ and official download page state that downloaded data and backups
must be deleted when the subscription ends. Redistribution is restricted and
is not needed for AQ's private local audit.
[SimFin Data License Agreement](https://www.simfin.com/en/commercial-license/)
[SimFin download and cancellation FAQ](https://www.simfin.com/en/fundamental-data-download/)

Accordingly, local persistence for private personal research passes only while
the account/subscription and its license remain active. This is not a perpetual
retention grant: termination requires deletion. A later audit must fail closed
unless it can preserve the intended certification snapshot throughout its
authorized lifecycle and enforce the deletion boundary. Nothing in this
decision authorizes redistribution or persistence after termination.

```text
SIMFIN_PERSONAL_NONCOMMERCIAL_USE_RIGHTS = PASS_WHILE_SUBSCRIPTION_ACTIVE
SIMFIN_PERSONAL_RETENTION_SCOPE = ACTIVE_SUBSCRIPTION_ONLY
SIMFIN_POST_TERMINATION_RETENTION = FAIL_DELETE_REQUIRED
SIMFIN_REDISTRIBUTION = RESTRICTED
```

### Revision and reproducibility boundary

SimFin publishes an API/bulk-download technical update history and documents
that locally cached files are refreshed, but the reviewed official material
does not expose an immutable dataset release, vintage, correction identifier,
or reproducible as-of query for daily prices. A content hash could identify a
locally authorized response, but would not make the upstream revision
addressable. These gates remain unresolved for the technical audit.
[SimFin API and bulk-download updates](https://www.simfin.com/en/technical-updates-to-api-v3-and-bulk-download/)

### SimFin gate matrix

| Gate | Decision | Official evidence boundary |
|---|---|---|
| Free plan available | `PASS` | `$0`, no billing |
| Free price-history depth | `5_YEARS` | FREE chart history and delayed bulk history |
| US equity daily OHLCV | `PASS_DOCUMENTED` | daily share-price interface and fields |
| Delisted security support | `UNRESOLVED` | not established for every FREE historical episode |
| Ticker reuse handling | `PASS_DESIGN` | `SimFinId` explicitly covers repeated tickers |
| Stable security/company identifier | `PASS` | unique `SimFinId` |
| Corporate-action visibility | `PARTIAL` | split/dividend effects documented; standalone event completeness not established |
| Raw price visibility | `PARTIAL` | OHLC are split-adjusted, not unadjusted raw |
| Adjusted price visibility | `PASS_DOCUMENTED` | adjusted close includes split and dividend effects |
| API or bulk download | `PASS` | both documented for FREE |
| Persistent personal retention | `PASS_WHILE_SUBSCRIPTION_ACTIVE` | copies allowed under active license; deletion required after termination |
| Revision addressability | `UNRESOLVED` | no immutable price revision located |
| Dataset versioning | `UNRESOLVED` | no addressable price release located |
| Reproducibility | `UNRESOLVED` | technical snapshot/hash path requires audit; upstream vintage absent |
| Account required | `YES` | free registration required |
| API key required | `YES` | free key documented |
| Upstream maturity | `PASS` | maintained official package, bulk, and web API paths |

Five years from the current 2026 decision date creates a credible entitlement
window for the known 2022 gaps, subject to exact episode and row verification.
It cannot cover the 2011 Qwest episode under the FREE history entitlement.

```text
SIMFIN_FREE_PLAN = PASS
SIMFIN_FREE_HISTORY_DEPTH = 5_YEARS
SIMFIN_PERSONAL_RETENTION = PASS
SIMFIN_PERSONAL_RETENTION_SCOPE = ACTIVE_SUBSCRIPTION_ONLY
SIMFIN_STABLE_IDENTITY = PASS
SIMFIN_REVISION_ADDRESSABILITY = UNRESOLVED
SIMFIN_2022_GAP_POTENTIAL = YES
SIMFIN_QWEST_2011_POTENTIAL = NO
```

## Stooq

Stooq's official instrument pages expose historical-data navigation, OHLCV
display, exchange-qualified symbols such as `NVDA.US`, and corporate-operation
annotations. Its official historical database/download surface is publicly
visible. These observations establish a technically visible historical data
surface, not a certification authority.
[Stooq official US equity page](https://stooq.com/q/?s=nvda.us)
[Stooq official historical database](https://stooq.com/db/h/)

Within this bounded official-source review, no stable documented contract was
located that establishes all of: a free plan entitlement, persistent local-use
rights, a permanent security or issuer identifier, delisted/recycled-ticker
semantics, raw-versus-adjusted methodology, immutable revisions, or dataset
versions. The public page footer links to terms, but no accessible official
text found in this audit proved the required market-data retention right.
Absence of located documentation is recorded as unresolved, not as proof that
Stooq forbids those uses.

```text
STOOQ_FREE_PLAN = UNRESOLVED
STOOQ_PERSONAL_RETENTION = UNRESOLVED
STOOQ_PERSONAL_NONCOMMERCIAL_USE_RIGHTS = UNRESOLVED
STOOQ_STABLE_IDENTITY = UNRESOLVED
STOOQ_DELISTED_SECURITY_SUPPORT = UNRESOLVED
STOOQ_TICKER_REUSE_HANDLING = UNRESOLVED
STOOQ_RAW_ADJUSTED_SEMANTICS = UNRESOLVED
STOOQ_CORPORATE_ACTION_COMPLETENESS = UNRESOLVED
STOOQ_REVISION_ADDRESSABILITY = UNRESOLVED
STOOQ_DATASET_VERSIONING = UNRESOLVED
STOOQ_REPRODUCIBILITY = UNRESOLVED
STOOQ_DOCUMENTED_STABLE_INTERFACE = UNRESOLVED
STOOQ_ACCOUNT_REQUIRED = UNRESOLVED
STOOQ_API_KEY_REQUIRED = UNRESOLVED
STOOQ_2022_GAP_POTENTIAL = UNKNOWN
STOOQ_QWEST_2011_POTENTIAL = UNKNOWN
```

Visible CSV/history is insufficient to pass the selection gates. Stooq is not
selected, and no account, key, or download was attempted.

## Previously screened candidates

Only current official entitlement documentation was checked.

- Alpha Vantage documents that `TIME_SERIES_DAILY` FREE access is the latest
  100 data points (`compact`), while the full 25+ year series requires a
  premium key. It cannot reach the 2022 or 2011 gaps from the current date.
  `ALPHA_VANTAGE_FREE_DECISION = REJECT_HISTORY_DEPTH`.
  [Alpha Vantage API documentation](https://www.alphavantage.co/documentation/)
- EODHD documents a `$0` personal plan with 20 calls/day and only the past
  year of historical EOD data. It cannot reach the known gaps.
  `EODHD_FREE_DECISION = REJECT_HISTORY_DEPTH`.
  [EODHD official pricing](https://eodhd.com/pricing)
- Nasdaq Data Link identifies QuoteMedia End of Day US Prices (`EOD`) as a
  premium Tables product, not a free US EOD equity dataset.
  `NASDAQ_DATALINK_FREE_EOD_DECISION = REJECT_NOT_FREE`.
  [Nasdaq Data Link data organization](https://docs.data.nasdaq.com/docs/data-organization)

## Selection

SimFin is the sole next candidate. It passes the decision-stage access,
2022-depth, active-license retention, stable-identity, and mature-interface
gates. This is authorization only for a separately approved bounded technical
authority audit; it is not provider acceptance, data certification, account
creation, or an API call. The audit must test exact FB/DISCK identity and
coverage, licensed snapshot retention, adjustment/event fields, and revision
behavior. It must preserve the Qwest gap rather than narrowing the window.

```text
NEXT_FREE_PROVIDER_CANDIDATE = SIMFIN
P2_CERTIFICATION_DATA_ROUTE_POLICY = FREE_ONLY
P2_CERTIFICATION_WINDOW_STATUS = NOT_YET_PREREGISTERED
CURRENT_NEXT = P2_SIMFIN_FREE_DATA_AUTHORITY_AUDIT
```

## Non-actions

```text
ACCOUNT_CREATED = NO
API_KEY_CREATED = NO
PROVIDER_API_CALLS = 0
MARKET_DATA_DOWNLOADED = NO
PROVIDER_PAYLOAD_RETAINED = NO
PACKAGES_CHANGED = NO
NEW_PROVIDER_FRAMEWORK_CREATED = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
MODEL_TRAINING = NO
BACKTEST = NO
QLIB_EXECUTED = NO
SKFOLIO_EXECUTED = NO
ARCH_EXECUTED = NO
RDAGENT_EXECUTED = NO
MLFLOW_EXPERIMENT = NO
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
PUSHED = NO
PR_CREATED = NO
MERGED = NO
```
