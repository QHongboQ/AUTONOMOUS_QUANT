# P2 Existing Free-Data Blocker Closure 001

**Task:** `AUTONOMOUS-QUANT-P2-EXISTING-FREE-DATA-BLOCKER-CLOSURE-001`
**Base:** `56fd8f1ed1eaf3d72019a7d1309361896f22f4cd`
**Result:** `PASS_WITH_REMAINING_BLOCKERS`

## Scope and ownership

This task stopped provider stacking and re-audited only the existing
Quantiacs and SimFin paths. Yahoo and Tiingo remain prior evidence and were
not called. No provider, account, credential, package, framework, runtime, or
production Python was added.

```text
CAPABILITY = EXISTING_FREE_DATA_BLOCKER_CLOSURE
UPSTREAM_OWNER = QUANTIACS_AND_SIMFIN
OWNERSHIP_MODE = UPSTREAM_WHOLE_WITH_AQ_THIN_IDENTITY_AND_CERTIFICATION_POLICY
AQ_IMPLEMENTATION_ALLOWED = POLICY_CONTRACT_EVIDENCE_DOCUMENTATION_ONLY
CUSTOM_ENGINE_REQUIRED = NO
NEW_PROVIDER = NONE
NEW_ACCOUNT = NONE
NEW_API_KEY = NONE
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

## Security identity and ticker episode are distinct

AQ now distinguishes two concepts:

- `SecurityIdentity` identifies the underlying listed security using stable,
  authoritative security evidence.
- `TickerEpisode` identifies the ticker valid for that security during a
  bounded date interval.

A security may have more than one ticker episode. A provider observation may
be bound to `SecurityIdentity` first and then to the date-valid
`TickerEpisode` only when stable evidence proves that the listed security is
the same. Company-name similarity, issuer continuity alone, price continuity,
and a current ticker alone are insufficient.

This policy does not restore the retired direct relabel rule. Raw provider
symbols remain untouched:

```text
FB_META_CROSS_EPISODE_DIRECT_RELABEL = 0
```

## FB / META continuity

Meta's issuer announcement filed with the SEC states that the same Class A
common stock changed from `FB` to `META` before market open on 2022-06-09,
continued its Nasdaq listing, retained the same CUSIP, and required no
shareholder action. Meta's 2022 Form 10-K independently records that its Class
A common stock began trading as `META` on that date, replacing `FB`.

- [Meta issuer announcement filed with the SEC](https://www.sec.gov/Archives/edgar/data/1326801/000132680122000070/may312022-exhibit991.htm)
- [Meta 2022 Form 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000132680123000013/meta-20221231.htm)

```text
FB_META_SECURITY_CONTINUITY = PROVEN
SECURITY_CLASS = META_PLATFORMS_CLASS_A_COMMON_STOCK
TICKER_EPISODE_FB_END = 2022-06-08
TICKER_EPISODE_META_START = 2022-06-09
```

Existing Quantiacs metadata exposes provider asset IDs, ticker, exchange,
name, and sometimes issuer CIK. Its field named `FIGI` contains Quantiacs
`tts-*` identifiers; it was not accepted as an independently verified FIGI or
permanent-security identifier. The old FB and current META records have
different provider asset IDs, and the old FB record has no CIK. Quantiacs
metadata therefore does not independently prove permanent identity.

The existing Quantiacs META series nevertheless identifies Meta Platforms,
Nasdaq `META`, CIK `1326801`, and contains observations on both sides of the
ticker boundary. Those observations may be interpreted only through the
external same-Class-A/same-CUSIP authority above:

```text
provider observation
  -> META_PLATFORMS_CLASS_A SecurityIdentity
  -> FB TickerEpisode through 2022-06-08
  -> META TickerEpisode from 2022-06-09
```

No raw Quantiacs ticker or row was changed in this task.

## SimFin official bulk daily share-price evidence

The existing SimFin credential was used once with the official bulk-download
interface corresponding to
`load_shareprices(market="us", variant="daily")`. No package installation was
needed. The official implementation defines the bulk endpoint and the daily
share-price variant:

- [SimFin official download implementation](https://github.com/SimFin/simfin/blob/master/simfin/download.py)
- [SimFin official loader](https://github.com/SimFin/simfin/blob/master/simfin/load.py)

The response was streamed to private storage, filtered only for `FB`, `META`,
`DISCK`, and `WBD`, and validated against the exact eleven-column schema. The
100,033,767-byte full download was deleted after the target-only artifact and
manifest were hash-validated. No market-data row entered Git.

```text
REQUEST = dataset=shareprices; variant=daily; market=us
UPSTREAM_SOURCE_COMMIT = 1f117a0b84072d2c0fdf61df88b737396eee514a
FULL_RESPONSE_SHA256 = 81cc200282e4de6c069c14b43ab025972a75b8f265dabd6f6c07523893cc0e5e
PRIVATE_FILTERED_ARTIFACT = D:\AQ_DATA\P2\p2-existing-free-data-blocker-closure-001\simfin-target-shareprices.csv
PRIVATE_FILTERED_ARTIFACT_BYTES = 187941
PRIVATE_FILTERED_ARTIFACT_SHA256 = 3a7c21afefc044a9c28f5a1f1069840fe092d7f44b937c7d9b489bcc5c9fd2a9
PRIVATE_MANIFEST_SHA256 = b7ea798bc7ef563477baa7e846a4198c54f429901cc05e321019d846b0928d7a
PRIVATE_EVIDENCE_ACL = CURRENT_USER_AND_SYSTEM_ONLY_INHERITANCE_DISABLED
SCHEMA_VALIDATION = PASS_EXACT_HEADER
```

Observed target records:

| Bulk ticker | SimFinId | Rows | First date | Last date | Required observation |
|---|---:|---:|---|---|---|
| `FB` | none | 0 | none | none | 2022-06-08 absent |
| `META` | `121021` | 1,237 | 2020-10-14 | 2025-09-17 | 2022-06-08 OHLC, adjusted close, and volume present |
| `DISCK` | none | 0 | none | none | 2022-04-08 absent |
| `WBD` | `120376` | 1,235 | 2020-10-14 | 2025-09-17 | 2022-04-08 OHLC, adjusted close, and volume present but not accepted as DISCK |

The current SimFin company record binds SimFinId `121021` to Meta Platforms,
ticker `META`, and ISIN `US30303M1027`. That security identifier, combined
with the issuer-filed unchanged-CUSIP evidence, supports the same Class A
security across the FB/META ticker boundary. SimFin's bulk file backfills the
current ticker instead of preserving the historical ticker, so its result is
security-level evidence, not an exact historical ticker record.

```text
FB_SIMFIN_BULK_EPISODE = SECURITY_LEVEL_ONLY
FB_PRICE_AUTHORITY = CLOSED
```

The binding is `SimFinId -> current ISIN -> authoritative unchanged CUSIP ->
date-valid TickerEpisode`; it is not `META rows -> FB rows`.

## DISCK security and terminal action

Nasdaq Equity Corporate Actions Alert ECA2022-63 identifies `DISCK` as
Discovery Series C Common Stock, CUSIP `25470F302`, with last trading date
2022-04-08 and suspension effective 2022-04-11. It specifies one WBD Series A
share for each DISCK share and identifies WBD CUSIP `934423104`, with regular-
way WBD trading beginning 2022-04-11.

- [Nasdaq ECA2022-63](https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2022-63)
- [SEC-filed Form 4 recording the one-for-one conversion](https://www.sec.gov/Archives/edgar/data/937797/000143710722000093/xslF345X03/wf-form4_164979993298213.xml)
- [WBD 2022 Form 10-K](https://www.sec.gov/Archives/edgar/data/1437107/000143710723000019/disca-20221231.htm)

```text
DISCK_SECURITY_IDENTITY = CLOSED_BY_NASDAQ_SEC
DISCK_TERMINAL_CORPORATE_ACTION = CLOSED_1_TO_1_WBD
```

Security identity and terminal consideration do not manufacture OHLCV.
SimFin's current `WBD` company record uses SimFinId `120376` and ISIN
`US9344231041`; the bulk file backfills `WBD` before 2022-04-11. That is not
the exact DISCK Series C security with CUSIP `25470F302`, and the contract
forbids substituting WBD, DISCA, or DISCB.

```text
DISCK_SIMFIN_2022_04_08 = ABSENT
DISCK_PRICE_AUTHORITY = UNRESOLVED
```

## Daily-price revision and reproducibility contract

AQ no longer requires a vendor revision ID for every daily market-price
snapshot. Exactly two authority modes are permitted:

```text
MODE_A = VENDOR_VERSIONED_SNAPSHOT
MODE_B = SEALED_LOCAL_OBSERVATION_SNAPSHOT
```

Mode B is acceptable only when provider rights authorize local retention and
the sealed evidence records provider, upstream interface/version, request
parameters, retrieval UTC, security identity, ticker episode, session,
source response/content hash, schema-validation result, and immutable artifact
hash. A sealed snapshot is never mutated in place. A later upstream correction
creates a new snapshot/version and requires re-certification before promotion.

This exception applies only to daily market prices. Fundamental revisions,
macro vintages, filing first-availability timestamps, and news publication
timestamps retain their stricter PIT/vintage requirements.

```text
DAILY_PRICE_VENDOR_REVISION_ID_REQUIRED = NO_IF_SEALED_LOCAL_SNAPSHOT_AUTHORIZED
DAILY_PRICE_REPRODUCIBILITY = CLOSED
```

## Quantiacs private-retention authority

Quantiacs officially supports local strategy development and grants compliant
users a limited, non-transferable right to use its Services for personal
purposes. Its terms prohibit transferring or providing accessible market data
to third parties, commercial copying, and public distribution.

- [Quantiacs local-development documentation](https://quantiacs.com/documentation/en/user_guide/local_development.html)
- [Quantiacs User Agreement](https://quantiacs.com/termsofuse)

The reviewed official text does not explicitly say whether an individual may
retain a private, local, noncommercial, nonredistributed immutable market-data
snapshot for personal research reproduction and audit. Local development and
the absence of public redistribution do not by themselves establish durable
retention authority. No legal permission is inferred.

```text
QUANTIACS_PRIVATE_LOCAL_RETENTION = NEEDS_WRITTEN_PROVIDER_CONFIRMATION
```

The one narrowly scoped confirmation question is:

> May an individual user privately retain a local, non-public,
> non-redistributed historical market-data snapshot solely to reproduce and
> audit their own personal quantitative research while complying with the
> Quantiacs Terms?

The question was not sent.

## Qwest 2011 and current model lineage

The accepted P1 Qlib-native lineage has a pre-existing provider boundary of
2015-01-02 and training begins on 2015-04-01. Those dates were recorded before
this task and were not selected from performance or changed to avoid Qwest.
The current model lineage has never consumed a 2011 price.

PIT identity regression coverage and current model-lineage price scope are
separate. Qwest remains a frozen identity regression, but its 2011 price is
outside the current lineage's established source-data domain.

```text
CURRENT_MODEL_LINEAGE_HISTORY_FLOOR = 2015-01-02
QWEST_2011_IDENTITY_REGRESSION = RETAIN
QWEST_2011_CURRENT_MODEL_PRICE_BLOCKER = NO
P2_CERTIFICATION_WINDOW_STATUS = NOT_YET_PREREGISTERED
```

This finding does not select or narrow the future sealed OOS certification
window.

## Composition decision and remaining blockers

No third price provider was added. Yahoo and Tiingo Starter are retired from
the certification price route; their historical audit evidence remains.

The proposed two-provider composition is not yet certification-acceptable:

```text
PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
PRIMARY = QUANTIACS
BOUNDED_GAP_FILL = SIMFIN
YAHOO_CERTIFICATION_ROUTE = RETIRED
TIINGO_STARTER_CERTIFICATION_ROUTE = RETIRED
NO_ADDITIONAL_FREE_PROVIDER_REQUIRED = NO
EXISTING_FREE_DATA_BLOCKER_EXHAUSTION_REQUIRED = YES
NEW_MARKET_DATA_PROVIDER_PROHIBITED_UNTIL_EXISTING_BLOCKERS_EXHAUSTED = YES
REMAINING_BLOCKERS = DISCK_2022_04_08_EXACT_PRICE_AUTHORITY; QUANTIACS_PRIVATE_LOCAL_RETENTION_WRITTEN_CONFIRMATION
PROVIDER_EXPANSION_GATE = CLOSED_UNTIL_BOTH_EXISTING_BLOCKERS_HAVE_BEEN_EXHAUSTED_OR_FORMALLY_ADJUDICATED_UNSOLVABLE
```

The exact minimal remaining blockers are:

1. `DISCK_2022_04_08_EXACT_PRICE_AUTHORITY` — neither Quantiacs nor SimFin
   supplies an exact DISCK row; terminal-action evidence cannot replace price.
2. `QUANTIACS_PRIVATE_LOCAL_RETENTION_WRITTEN_CONFIRMATION` — official text
   reviewed here is not explicit enough to authorize durable private
   certification snapshots.

No other API was added to compensate for either blocker.

Before any additional market-data price provider, API, account, API key, or
price source may be introduced, the project must first exhaust both remaining
existing-route blockers. Exhaustion requires all reasonable closure work with
the already selected providers and official issuer, exchange, and SEC
authority; obtaining or failing to obtain the required written provider
confirmation; and documenting why each blocker is solved or genuinely
unsolvable. Only then may a separate, explicitly authorized decision consider
another provider.

This gate applies to market-data price providers. SEC, Nasdaq, issuer, and
exchange evidence used to adjudicate identity or corporate actions is not an
additional price provider.

## Final state and non-actions

```text
P2_EXISTING_FREE_DATA_BLOCKER_CLOSURE = COMPLETE_WITH_REMAINING_BLOCKERS
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
MARKET_DATA_IN_GIT = NO
CREDENTIAL_IN_GIT = NO
PUSHED = NO
PR_CREATED = NO
MERGED = NO
CURRENT_NEXT = P2_FREE_DATA_ROUTE_BLOCKER_DECISION
```
