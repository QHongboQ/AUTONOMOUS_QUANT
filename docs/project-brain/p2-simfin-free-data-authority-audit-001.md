# P2 SimFin Free Data Authority Audit 001

**Task:** `AUTONOMOUS-QUANT-P2-SIMFIN-FREE-DATA-AUTHORITY-AUDIT-001`
**Base:** `ee0ba8a6b193bd0b66321bf63a11159242f601c5`
**Result:** `PASS_WITH_UNRESOLVED_AUTHORITY`

## Scope and ownership

This bounded technical and authority audit tested only whether SimFin FREE
could identify the historical Facebook `FB` episode through 2022-06-08 and
the exact Discovery Series C `DISCK` security on 2022-04-08. Qwest 2011 was
not queried. No model, backtest, downstream data composition, or trading
operation ran.

```text
CAPABILITY = SIMFIN_FREE_BOUNDED_CERTIFICATION_DATA_AUTHORITY_AUDIT
UPSTREAM_OWNER = SIMFIN_OFFICIAL_INTERFACE
OWNERSHIP_MODE = UPSTREAM_WHOLE
AQ_IMPLEMENTATION_ALLOWED = BOUNDED_REQUEST_PARAMETERS_IDENTITY_ADJUDICATION_EVIDENCE_VALIDATION_AUTHORITY_CLASSIFICATION_DOCUMENTATION_ONLY
CUSTOM_ENGINE_REQUIRED = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

No AQ SimFin client, provider registry, downloader, HTTP/retry/cache engine,
generic store, security master, ticker resolver, corporate-action engine,
normalizer, provenance framework, DuckDB pipeline, or DVC promotion pipeline
was created.

## Credential migration

The plaintext source `D:\API.txt` was found and read directly into process
memory. Only surrounding CR/LF characters were removed. The nonempty value was
protected with the established Windows CurrentUser DPAPI convention and
written atomically to
`%LOCALAPPDATA%\AUTONOMOUS_QUANT\secrets\simfin-api-key.dpapi`.

The existing secrets directory already had inheritance disabled and explicit
FullControl entries only for the current user and `SYSTEM`. The new file was
assigned the same two-principal, inheritance-protected ACL. It was decrypted
in memory and compared byte-for-byte with the source. Only after the match
passed was exactly `D:\API.txt` deleted.

An exact-value scan covered `D:\AUTONOMOUS_QUANT`, `D:\AQ_DATA\P2`, and the
secrets directory without printing the value, its hash, or any substring. It
found zero plaintext copies.

```text
PLAINTEXT_API_SOURCE_FOUND = YES
SIMFIN_DPAPI_SECRET_CREATED = YES
DPAPI_SCOPE = CurrentUser
DPAPI_ROUNDTRIP_MATCH = YES
DPAPI_ACL_RESTRICTED = YES
PLAINTEXT_API_SOURCE_DELETED = YES
CREDENTIAL_HYGIENE = PASS
```

## Official access path

The current official SimFin Python package documents an `Authorization`
header in the form `api-key <credential>` for upstream downloads. The current
official API v3 reference exposes company-list, company-general, and bounded
price endpoints and likewise specifies the `Authorization` header. Direct
official REST was selected because it required no package or environment
change and allowed exact bounded parameters. The credential was decrypted
only within each request process and was never placed in a URL, command line,
environment variable, profile, `.env`, log, or evidence document.

- [SimFin official Python download implementation](https://github.com/SimFin/simfin/blob/master/simfin/download.py)
- [SimFin API v3 authentication](https://simfin.readme.io/reference/getting-started-1)
- [SimFin API v3 company information](https://simfin.readme.io/reference/general-verbose-1)
- [SimFin API v3 company list](https://simfin.readme.io/reference/list-1)
- [SimFin API v3 price data](https://simfin.readme.io/reference/prices-verbose-1)

```text
SIMFIN_ACCESS = PASS
ACCESS_PATH = SIMFIN_OFFICIAL_REST
PACKAGES_CHANGED = NO
```

## Request ledger

The provider received five calls. No automatic retry or open-ended search was
performed.

| Call | Endpoint and bounded parameters | Status | Evidence result |
|---:|---|---:|---|
| 1 | `companies/general/verbose`, tickers `FB,META,DISCK` | 500 | FREE rejected the multi-company request as exceeding the allowed company count |
| 2 | `companies/general/verbose`, ticker `FB` | 200 | empty JSON array |
| 3 | `companies/general/verbose`, ticker `META` | 429 | rate-limited; not used as identity evidence |
| 4 | `companies/general/verbose`, ticker `DISCK` | 200 | empty JSON array |
| 5 | `companies/list` | 200 | official endpoint has no filter parameter; 6,697 records were filtered in memory to relevant names/tickers |

The full company directory was not retained. Only the four filtered records,
request metadata, and the full-response hash were stored privately. The
official list contained current `META` with SimFinId `121021` and ISIN
`US30303M1027`, and current `WBD` with SimFinId `120376` and ISIN
`US9344231041`. It contained no `FB` or `DISCK` ticker record. Two unrelated
company names containing “Discovery” were excluded by issuer/ticker identity.

Private evidence is restricted to:
`D:\AQ_DATA\P2\simfin-free-data-authority-audit-001`.
The directory ACL allows only the current user and `SYSTEM`.

| Evidence | UTC retrieval | Status | Bytes | SHA-256 |
|---|---|---:|---:|---|
| Multi-company general response | 2026-09-12T20:42:35Z | 500 | 156 | `3ebf79299a46c1a6eab3bf6f59cfde8d8c152e6efb2d19dde208054fb8b65418` |
| FB general response | 2026-09-12T20:43:23Z | 200 | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| META general response | 2026-09-12T20:43:24Z | 429 | 166 | `c6341e068a0838955b22bb5dceb6bd5c9d88530feae46d09012e703b13eac3b7` |
| DISCK general response | 2026-09-12T20:43:25Z | 200 | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |
| Company list full response, hash only | 2026-09-12T20:44:48Z | 200 | 1,100,352 | `5dac3a3ed23b5ce0f16723763b700f80d5aa235191476edb54c557a323ea1105` |

These hashes prove only what AQ observed. They do not make SimFin revisions or
dataset releases addressable.

## FB historical episode

The current company directory establishes an exact current Meta Platforms
company record under ticker `META`. It does not associate that SimFinId with
the historical `FB` ticker episode. The exact `ticker=FB` company request
returned an empty array. No historical ticker field, prior-ticker record,
rename event, or effective ticker dates were exposed in the bounded official
interfaces.

Company continuity cannot manufacture historical episode identity. Because
the identity gate failed before price observation, no FB price request was
made. No current META row was queried or relabeled as FB.

```text
FB_SIMFIN_COMPANY_IDENTITY = UNAVAILABLE
FB_HISTORICAL_TICKER_EPISODE = UNAVAILABLE
FB_2022_06_08 = NOT_TESTABLE_IDENTITY
FB_META_CROSS_EPISODE_MAPPING = 0
```

This does not contradict the accepted external FB/META boundary. It means the
bounded SimFin FREE interfaces did not independently expose enough provider
identity to bind price observations to that historical episode.

## DISCK Series C security

The current company directory establishes a current Warner Bros. Discovery
`WBD` company record. It does not expose a historical `DISCK` record, a Series
C security identifier, or effective ticker/class dates. The exact
`ticker=DISCK` company request returned an empty array. A company-level
SimFinId for current WBD would not by itself identify Discovery Series C.

The audit therefore did not substitute DISCA, DISCB, or WBD and stopped before
any DISCK price request.

```text
DISCK_COMPANY_IDENTITY = UNAVAILABLE
DISCK_SECURITY_CLASS_IDENTITY = UNAVAILABLE
DISCK_2022_04_07 = NOT_TESTABLE_IDENTITY
DISCK_2022_04_08 = NOT_TESTABLE_IDENTITY
```

## Price semantics

No price response was requested or retained because neither historical
episode passed identity. The official SimFin field definitions nevertheless
define `Open`, `High`, `Low`, and `Close` as split-adjusted but not
dividend-adjusted, and `Adj. Close` as adjusted for both stock splits and
dividends, described as total return. The evidence therefore does not call
SimFin OHLC raw.

[SimFin official field definitions](https://github.com/SimFin/simfin/blob/master/simfin/names.py)

```text
SIMFIN_OHLC_SEMANTICS = SPLIT_ADJUSTED_NOT_DIVIDEND_ADJUSTED
SIMFIN_ADJ_CLOSE_SEMANTICS = SPLIT_AND_DIVIDEND_ADJUSTED_TOTAL_RETURN
OPEN = NOT_OBSERVED_IDENTITY_GATE
HIGH = NOT_OBSERVED_IDENTITY_GATE
LOW = NOT_OBSERVED_IDENTITY_GATE
CLOSE = NOT_OBSERVED_IDENTITY_GATE
VOLUME = NOT_OBSERVED_IDENTITY_GATE
ADJUSTED_CLOSE = NOT_OBSERVED_IDENTITY_GATE
DIVIDEND = NOT_OBSERVED_IDENTITY_GATE
SPLIT = NOT_OBSERVED_IDENTITY_GATE
CORPORATE_ACTION = NOT_OBSERVED_IDENTITY_GATE
SYNTHETIC_PRICE_ROWS = 0
```

## Revision, versioning, and reproducibility

The official API reference provides a current mutable company list, company
information, prices, a changed-companies endpoint, and a paginated database
change log. The reviewed endpoints and actual bounded responses exposed no
immutable observation revision, vintage, as-of dataset snapshot, or dataset
release identifier. The unrestricted change log has no company filter and was
not crawled to invent historical ticker authority.

Because no historical price response passed the identity gate, no price
snapshot can be classified reproducible. The request parameters, HTTP status,
retrieval time, selected identity fields, response sizes, and response hashes
are preserved privately; the upstream state remains non-version-addressable
in this audit.

```text
SIMFIN_REVISION_ADDRESSABILITY = UNRESOLVED
SIMFIN_DATASET_VERSIONING = UNRESOLVED
SIMFIN_REPRODUCIBILITY = PARTIAL_IDENTITY_EVIDENCE_ONLY
```

## Retention boundary

SimFin's FREE/BASIC license grants personal non-commercial research use and
permits copies only while used under the active license. SimFin's official
terms and pricing FAQ require downloaded data and backups to be deleted after
subscription termination. No perpetual retention or redistribution right is
claimed.

- [SimFin Data License Agreement](https://www.simfin.com/en/commercial-license/)
- [SimFin pricing and termination FAQ](https://www.simfin.com/en/prices/)

```text
SIMFIN_PERSONAL_NONCOMMERCIAL_USE = PASS_WHILE_ACCOUNT_ACTIVE
SIMFIN_RETENTION = PASS_WHILE_ACCOUNT_ACTIVE
LICENSE_RETENTION_SCOPE = ACTIVE_SUBSCRIPTION_ONLY
SIMFIN_POST_TERMINATION_RETENTION = FAIL_DELETE_REQUIRED
POST_TERMINATION_DELETE_REQUIRED = YES
REDISTRIBUTION = NOT_AUTHORIZED
```

## Qwest 2011

No Qwest or ticker-Q SimFin request was made. The FREE five-year entitlement
does not reach 2011. This does not remove the Qwest requirement and does not
authorize changing the certification start date.

```text
SIMFIN_QWEST_2011_POTENTIAL = NO
QWEST_2011_GAP = UNRESOLVED
P2_CERTIFICATION_WINDOW_STATUS = NOT_YET_PREREGISTERED
```

## Decision matrix

| AQ episode | Quantiacs status | Yahoo status | Tiingo status | SimFin company identity | SimFin security identity | SimFin episode identity | SimFin price status | Revision status | Retention status | Certification gap-fill decision | Reason |
|---|---|---|---|---|---|---|---|---|---|---|---|
| FB through 2022-06-08 | absent | absent | wrong security | unavailable | unavailable | unavailable | not testable | unresolved | pass while account active | `NEEDS_FURTHER_AUTHORITY_EVIDENCE` | current META SimFinId does not prove the historical FB ticker episode |
| DISCK on 2022-04-08 | absent | absent | technically present but rejected for authority | unavailable | unavailable | unavailable | not testable | unresolved | pass while account active | `NEEDS_FURTHER_AUTHORITY_EVIDENCE` | current WBD company identity does not prove the DISCK Series C security |
| Qwest historical NYSE Q | absent | wrong security | unavailable | not tested | not tested | not tested | outside FREE depth | unresolved | pass while account active | `REJECT_NOT_IN_FREE_HISTORY_SCOPE` | FREE history does not reach 2011; the AQ gap remains unresolved |

```text
FB_GAP_FILL_DECISION = NEEDS_FURTHER_AUTHORITY_EVIDENCE
DISCK_GAP_FILL_DECISION = NEEDS_FURTHER_AUTHORITY_EVIDENCE
QWEST_GAP_FILL_DECISION = REJECT_NOT_IN_FREE_HISTORY_SCOPE
```

## Route outcome

SimFin FREE access works, but its bounded official identity interfaces did not
bind either historical ticker episode to an exact certification-usable
security. The audit cannot state whether the needed price rows are present or
absent because the mandatory identity order stopped first.

```text
FREE_ROUTE_DECISION = D — SIMFIN_2022_IDENTITY_NOT_CERTIFICATION_USABLE
P2_CERTIFICATION_DATA_ROUTE_POLICY = FREE_ONLY
P2_CERTIFICATION_WINDOW_STATUS = NOT_YET_PREREGISTERED
CURRENT_NEXT = P2_FREE_DATA_ROUTE_BLOCKER_DECISION
```

## Non-actions

```text
PROVIDER_CALLS = 5
PRICE_PROVIDER_CALLS = 0
MARKET_DATA_DOWNLOADED = NO
MARKET_DATA_IN_GIT = NO
CREDENTIAL_IN_GIT = NO
PRIVATE_EVIDENCE_IN_GIT = NO
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
