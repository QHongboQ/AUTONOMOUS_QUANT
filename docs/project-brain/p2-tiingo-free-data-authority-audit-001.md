# P2 Tiingo Free Data Authority Audit 001

**Task:** `AUTONOMOUS-QUANT-P2-TIINGO-FREE-DATA-AUTHORITY-AUDIT-001`
**Base:** `09dda5afe54dae4700169ec8da1183ab51d50b87`
**Result:** `PASS`

## Scope and ownership

The owner selected `P2_CERTIFICATION_DATA_ROUTE_POLICY = FREE_ONLY`. This
bounded audit tested Tiingo Starter only against the three gaps already left
by Quantiacs and Yahoo. Tiingo's official API owns acquisition
(`UPSTREAM_WHOLE`); AQ performed only bounded requests, identity adjudication,
and certification policy. No AQ Tiingo client, downloader, provider registry,
retry layer, cache, warehouse, security master, normalization framework, or
other data engine was created.

```text
CAPABILITY = TIINGO_FREE_CERTIFICATION_DATA_CANDIDATE_AUDIT
UPSTREAM_OWNER = TIINGO_OFFICIAL_API
OWNERSHIP_MODE = UPSTREAM_WHOLE
AQ_IMPLEMENTATION_ALLOWED = BOUNDED_REQUESTS_EVIDENCE_INTERPRETATION_POLICY_ONLY
CUSTOM_ENGINE_REQUIRED = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

## Credential migration

The plaintext token was found at `D:\API.txt`, read into process memory, and
stripped only of surrounding CR/LF. It was packaged using the established
AUTONOMOUS_QUANT Windows convention: CurrentUser DPAPI represented by
`ConvertFrom-SecureString`, stored at
`%LOCALAPPDATA%\AUTONOMOUS_QUANT\secrets\tiingo-api-key.dpapi`.

The existing secrets directory already had inheritance disabled and allowed
FullControl only to the current user and SYSTEM. An initial attempt to replace
the directory owner/ACL was rejected before any token read or write because
the process intentionally lacked `SeSecurityPrivilege`; no elevation or
administrator access was attempted. The existing directory ACL was therefore
preserved, and the new file was written atomically, set to the same two
principals, decrypted in memory, and compared byte-for-byte with the source.
Only after this roundtrip passed was exactly `D:\API.txt` deleted.

An exact-value scan then covered `D:\AUTONOMOUS_QUANT`, `D:\AQ_DATA\P2`, and
the secrets directory. It completed without errors and found zero plaintext
copies. The token, its hash, and all substrings remain absent from this
document and Git.

```text
PLAINTEXT_API_SOURCE_FOUND = YES
TIINGO_DPAPI_SECRET_CREATED = YES
DPAPI_SCOPE = CurrentUser
DPAPI_ROUNDTRIP_MATCH = YES
DPAPI_ACL_RESTRICTED = YES
PLAINTEXT_API_SOURCE_DELETED = YES
CREDENTIAL_HYGIENE = PASS
```

## Access path

The existing OpenBB environment contains OpenBB `4.7.2` and
`openbb-tiingo 1.6.1`; no package installation was required. Inspection of
the installed provider source showed that this version builds Tiingo request
URLs containing `token=<credential>`. That conflicts with this task's
mandatory header-only credential policy, so it was not invoked.

The audit instead used the contract-authorized Tiingo official REST endpoints
with `Authorization: Token <in-memory-token>`. The token was decrypted only
inside the request process and was not placed in a URL, command line,
environment variable, configuration file, log, or evidence artifact. HTTP
redirect following was disabled. There were seven authenticated REST calls
and one unauthenticated download of Tiingo's official supported-tickers list,
for exactly eight provider calls and no retry.

```text
TIINGO_ACCESS = PASS
ACCESS_PATH = TIINGO_OFFICIAL_REST
OPENBB_TIINGO_INVOKED = NO
PROVIDER_CALLS = 8
```

## Starter retention boundary

Tiingo's current Terms of Use, last updated 2026-08-05, expressly prohibit a
Starter or Trial user from writing, saving, archiving, backing up, or otherwise
retaining Tiingo Data in persistent storage. Transient volatile processing is
allowed only for the current operation, after which the data must be removed.
[Tiingo Terms of Use](https://api.tiingo.com/tos/)

Accordingly, this audit created no private evidence directory and retained no
raw provider payload, price value, response byte collection, table, Parquet,
cache, or DVC artifact. Only non-reconstructive audit conclusions, bounded
counts/session boundaries, field-presence results, and SHA-256 response hashes
are recorded. Direct metadata fields were inspected transiently as required
but are not reproduced as a retained provider record. This is a stricter
outcome than the task's optional private-evidence allowance.

Tiingo's pricing page labels Starter as `$0/month`, lists 30+ years of price
history, 500 unique symbols/month, 50 requests/hour, 1,000 requests/day, and
an internal-use-only license. It does not override the Starter no-retention
rule in the Terms. [Tiingo pricing](https://www.tiingo.com/about/pricing)

## Bounded provider observations

All response bodies were processed transiently in memory. No price value is
printed or retained.

### FB and META

| Item | Tiingo observation |
|---|---|
| FB metadata | requested ticker is reused by a later unrelated ETF; reported coverage begins after the accepted FB episode; no permaTicker field |
| FB EOD, 2022-03-15 through 2022-06-08 | HTTP 200 with 0 rows; 2022-06-08 absent |
| META metadata | exact Meta Class A issuer/ticker match; reported coverage includes the requested successor interval; no permaTicker field |
| META EOD, 2022-06-09 through 2022-06-17 | 7 rows, first 2022-06-09 and last 2022-06-17 |
| META fields | raw and adjusted OHLCV complete; `divCash` and `splitFactor` present |

Current Tiingo `FB` is a later, unrelated ETF, not the accepted Meta/Facebook
episode through 2022-06-08. The empty historical response cannot cure that
identity failure. META remains a distinct successor episode and none of its
rows was assigned to FB.

```text
FB_TIINGO_IDENTITY = WRONG_SECURITY
FB_TIINGO_PRICE = NOT_TESTABLE_IDENTITY
META_TIINGO_IDENTITY = EXACT
META_TIINGO_PRICE = PRESENT
FB_META_CROSS_EPISODE_MAPPING = 0
```

### DISCK

Tiingo metadata matched the requested DISCK Series C episode and reported
coverage that includes the required interval, but its reported end boundary
extends beyond the issuer's actual trading boundary. The bounded EOD response
contained only 2022-04-07 and 2022-04-08; it did not return DISCA, WBD, or any
post-boundary row.

The 2022-04-08 row had complete raw OHLCV and complete adjusted OHLCV, plus
`divCash` and `splitFactor`. Raw values were kept distinct from adjusted
values in memory and neither was persisted. SEC evidence remains the event
boundary authority: the Discovery classes were suspended before trading on
2022-04-11, when WBD began trading.
[WBD Form 8-K](https://www.sec.gov/Archives/edgar/data/1437107/000119312522103051/d328161d8k.htm)

```text
DISCK_TIINGO_IDENTITY = EXACT
DISCK_2022_04_08_TIINGO = PRESENT
DISCK_RAW_OHLCV = PRESENT
DISCK_ADJUSTED_OHLCV = PRESENT
DISCK_DIVCASH = PRESENT
DISCK_SPLITFACTOR = PRESENT
SYNTHETIC_PRICE_ROWS = 0
```

### Historical Qwest NYSE Q

The bare-Q metadata request resolved to a later, unrelated NYSE issuer whose
reported coverage begins years after the Qwest episode. This is not Qwest
Communications International Inc. (CIK `0001037949`), whose Q common stock
ceased NYSE listing after the 2011-04-01 merger.
[Qwest Form 8-K](https://www.sec.gov/Archives/edgar/data/1037949/000110465911018718/a11-9685_18k.htm)

The official supported-tickers archive contained two bare-Q records but no
issuer-name or permaTicker column and no Qwest name record. Tiingo's official
symbology documentation says delisted data is supported only where tickers
have not been recycled and describes broader permaTicker/delisted support as
still being expanded. Its changelog says EOD permaTicker queries are for
accounts with permaTicker enabled; the Starter interfaces inspected here did
not expose one. No alternate syntax was invented and, because exact historical
identity was unavailable, no Q price request was made.
[Tiingo symbology](https://www.tiingo.com/documentation/appendix/symbology)
[Tiingo EOD documentation](https://www.tiingo.com/documentation/end-of-day)

```text
BARE_Q_TIINGO_IDENTITY = WRONG_SECURITY
QWEST_TIINGO_IDENTITY = UNAVAILABLE
QWEST_TIINGO_PRICE_COVERAGE = NOT_TESTABLE_DUE_IDENTITY
```

## Response hashes

These hashes identify multi-field response bodies or the official
supported-tickers archive without retaining the underlying Tiingo Data:

```text
FB_METADATA_RESPONSE_SHA256 = ea8915f304db398d194394692848475bd583837ecf526ccd4ef599b08f43da6f
META_METADATA_RESPONSE_SHA256 = 8fff4dfe2a28db45d2ab6e89c15ffd9d74c00b64282fe7284b668a06efe6e4bb
FB_EOD_RESPONSE_SHA256 = NOT_RETAINED_EMPTY_RESPONSE
META_EOD_RESPONSE_SHA256 = 29cc7278a0076dd2d37653b41e8702866e782bbe98fe0bc739b13774f8a68f49
DISCK_METADATA_RESPONSE_SHA256 = b58ce4e1b03b8edcd7c28b96b19adbb74e0fee3151565bcf500d13beae572ca1
DISCK_EOD_RESPONSE_SHA256 = 556a5b03728c58d6887e550f1dc5934c7d5f0cf367f3de71cbbfade658ffec5b
Q_METADATA_RESPONSE_SHA256 = 0438d012aed320ddfd08f5e3a7c27b907b562fef73ca3ea7ca4a7b99b9515ad7
SUPPORTED_TICKERS_ARCHIVE_SHA256 = ef70f83fd943890f73c4eff923f8cc14cd87f200b7fcd85ee49d64ced531d704
```

## Authority audit

| Dimension | Evidence-backed classification |
|---|---|
| Free-plan access | `PASS`: bounded metadata/EOD calls succeeded; Starter is advertised at $0/month |
| Historical depth | `PARTIAL`: official 30+ year claim; observed historical META and DISCK, but no recycled historical FB or Qwest identity |
| Delisted-security support | `PARTIAL`: official docs limit ordinary delisted support to tickers not yet recycled |
| Ticker-reuse handling | `FAIL_FOR_STARTER_GAPS`: bare FB and Q resolve to later securities; no usable permanent identifier was exposed |
| Identity precision | `PARTIAL`: ticker/name/exchange/date metadata identifies current records but supplies no stable identifier in these EOD responses |
| Raw OHLCV | `PASS_WHEN_ROW_PRESENT` |
| Adjusted OHLCV | `PASS_WHEN_ROW_PRESENT`; Tiingo documents CRSP-style split/dividend adjustment |
| Dividend visibility | `PASS_WHEN_ROW_PRESENT`: `divCash` field returned |
| Split visibility | `PASS_WHEN_ROW_PRESENT`: `splitFactor` field returned |
| Revision addressability | `FAIL`: no revision, vintage, as-of, or immutable observation identifier is exposed; Tiingo documents that it updates corrections in place |
| Dataset versioning | `FAIL`: response hashes capture observations but the upstream dataset has no addressable release/version |
| Reproducibility | `FAIL_FOR_CERTIFICATION`: mutable responses cannot be frozen under Starter's no-retention rule |
| Retention rights | `FAIL`: current Starter terms explicitly prohibit persistent/durable storage of Tiingo Data |
| Redistribution rights | `FAIL`: Starter is internal-use only and redistribution requires separate permission |

```text
TIINGO_REVISION_ADDRESSABILITY = FAIL
TIINGO_RETENTION_RIGHTS = FAIL
TIINGO_REDISTRIBUTION_RIGHTS = FAIL
```

Tiingo's EOD documentation defines raw and adjusted OHLCV, `divCash`, and
`splitFactor`, and states that exchange corrections update prices throughout
the evening rather than exposing an immutable revision.
[Tiingo EOD documentation](https://www.tiingo.com/documentation/end-of-day)

## Decision matrix

| AQ episode | Quantiacs status | Yahoo status | Tiingo identity status | Tiingo price status | Tiingo action status | Revision status | Retention status | Certification gap-fill decision | Reason |
|---|---|---|---|---|---|---|---|---|---|
| FB through 2022-06-08 | absent | absent | wrong security | not testable | unavailable | fail | fail | `REJECT` | Tiingo FB is a later ETF; free EOD exposes no old-Facebook permanent identifier |
| DISCK, 2022-04-08 | absent | absent | exact | present | raw/adjusted OHLCV, dividend and split fields present | fail | fail | `REJECT` | technically fills the row, but Starter forbids durable retention and exposes no addressable revision |
| Qwest Communications International Inc., historical NYSE Q | absent | wrong security | unavailable after bare-Q rejection | not testable due identity | unavailable | fail | fail | `REJECT` | current Q is a later unrelated issuer and no free official historical-Qwest identifier is exposed |

Tiingo therefore covers one of the three technical gaps but supplies zero
certification-acceptable gap-fill rows under current Starter authority:

```text
TIINGO_TECHNICAL_GAP_COVERAGE = PARTIAL_DISCK_ONLY
TIINGO_CERTIFICATION_AUTHORITY_ACCEPTANCE = REJECTED_STARTER_RETENTION_AND_REVISION
FB_GAP_FILL_DECISION = REJECT
DISCK_GAP_FILL_DECISION = REJECT
QWEST_GAP_FILL_DECISION = REJECT
FREE_ROUTE_DECISION = B — TIINGO_PARTIAL_ANOTHER_FREE_SOURCE_REQUIRED
```

This finding is bounded to the currently tested Quantiacs, Yahoo, and Tiingo
Starter paths. It does not claim that every free provider in existence is
impossible, and it does not authorize another provider audit automatically.

## Final state and non-actions

```text
P2_CERTIFICATION_DATA_ROUTE_POLICY = FREE_ONLY
TIINGO_FREE_DATA_AUTHORITY_AUDIT = COMPLETE
CURRENT_NEXT = P2_FREE_DATA_SECONDARY_GAP_FILL_DECISION
MARKET_DATA_RETAINED = NO
PRIVATE_EVIDENCE_CREATED = NO
MARKET_DATA_IN_GIT = NO
CREDENTIAL_IN_GIT = NO
PACKAGES_CHANGED = NO
MODEL_TRAINING = NO
BACKTEST = NO
SKFOLIO_EXECUTED = NO
ARCH_TESTS_EXECUTED = NO
RDAGENT_EXECUTED = NO
MLFLOW_EXPERIMENT = NO
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
PUSHED = NO
PR_CREATED = NO
MERGED = NO
```
