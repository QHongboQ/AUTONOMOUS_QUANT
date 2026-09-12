# P2 remaining data blockers resolution 001

**Task:** `AUTONOMOUS-QUANT-P2-REMAINING-DATA-BLOCKERS-RESOLUTION-001`
**Base:** `4194c2b683ba37ed7347ad4bbbef1c7b928eb95e`
**Result:** `PASS`

## Scope and ownership

This task adjudicated the two remaining data hard blockers for the current
personal-capital certification profile. It did not add a provider, account,
API key, data framework, market-data row, or production Python code.

```text
CAPABILITY = P2_REMAINING_DATA_BLOCKERS_RESOLUTION
UPSTREAM_OWNER = QUANTIACS_PLUS_SIMFIN_WITH_QLIB_EXECUTION_SEMANTICS
OWNERSHIP_MODE = UPSTREAM_WHOLE_WITH_AQ_THIN_CERTIFICATION_POLICY
AQ_IMPLEMENTATION_ALLOWED = EVIDENCE_ADJUDICATION_AND_DOCUMENTATION_ONLY
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
NEW_PROVIDER = NONE
NEW_ACCOUNT = NONE
NEW_API_KEY = NONE
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

Nasdaq, SEC, and issuer evidence remain identity and corporate-action
authority rather than price providers. Public historical websites used below
are corroboration only. They are not members of the active provider set and
their observations are not inserted into a dataset.

## DISCK authority retained from the prior closure

The prior accepted evidence remains unchanged:

```text
DISCK_SECURITY_IDENTITY = CLOSED_BY_NASDAQ_SEC
DISCK_LAST_TRADING_DATE = 2022-04-08
DISCK_TERMINAL_ACTION = CLOSED_1_TO_1_WBD
QUANTIACS_DISCK_2022_04_08 = ABSENT
SIMFIN_DISCK_2022_04_08 = ABSENT
```

The corporate-action conclusion does not supply a missing price and does not
authorize substituting WBD, DISCA, or DISCB for DISCK.

## Independent public corroboration

Two independent public historical pages were inspected for the exact DISCK
session. Both report the same OHLC values. ChartExchange reports exact volume;
Investing.com displays volume rounded to 9.22 million.

| Source | Date | Open | High | Low | Close | Volume | Evidence role |
|---|---:|---:|---:|---:|---:|---:|---|
| [ChartExchange — DISCK Historical Data](https://chartexchange.com/symbol/nasdaq-disck/historical/) | 2022-04-08 | 23.15 | 24.50 | 22.78 | 24.42 | 9,215,459 | corroboration only |
| [Investing.com — Discovery Communications C Historical Data](https://www.investing.com/equities/discovery-communications-(c)-historical-data) | 2022-04-08 | 23.15 | 24.50 | 22.78 | 24.42 | 9.22M | corroboration only |

The observations materially agree and establish that the session occurred.
They do not create exact primary-provider OHLCV authority. No value from
either page was copied into Quantiacs data, SimFin data, or any AQ dataset.

## Narrow terminal-session policy

`KNOWN_TERMINAL_SESSION_PROVIDER_GAP` is permitted only when every condition
below is satisfied:

1. Exact security identity is independently closed.
2. Exact final trading date is independently closed.
3. Terminal corporate action and successor treatment are independently closed.
4. Every active primary provider has an explicit missing row.
5. No replacement or successor security row is substituted.
6. No synthetic or forward-filled OHLCV row is created.
7. Independent public sources establish that the session occurred and
   materially agree on the observation.
8. The primary certification dataset explicitly marks the session unavailable.

This policy preserves the missing observation as missing. The affected
security is not tradable on that session, and no order may use a fabricated,
forward-filled, or successor-security price. The independently confirmed
terminal corporate action remains effective.

All eight conditions hold for DISCK on 2022-04-08:

```text
DISCK_2022_04_08_CLASSIFICATION = KNOWN_TERMINAL_SESSION_PROVIDER_GAP
DISCK_2022_04_08_EXTERNAL_CORROBORATION = PASS
DISCK_2022_04_08_PRIMARY_ROW = ABSENT
DISCK_SYNTHETIC_ROW = NO
DISCK_FORWARD_FILL = NO
DISCK_SESSION_TRADABLE = NO
DISCK_TERMINAL_ACTION = CLOSED_1_TO_1_WBD
DISCK_PRICE_GAP = KNOWN_EXPLICIT_NONBLOCKING_TERMINAL_PROVIDER_GAP
DISCK_EXACT_PRICE_AUTHORITY_HARD_BLOCKER = NO
```

This is not `DISCK_PRICE_AUTHORITY = CLOSED`. Exact primary-provider OHLCV
remains absent and explicitly unavailable.

## Qlib missing-close behavior

The pinned Qlib source at commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` was inspected without execution or
modification. In `qlib/backtest/exchange.py`, a missing/NaN `$close` marks the
instrument suspended; `is_stock_tradable` then rejects it, and order generation
skips non-tradable instruments.

```text
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_MISSING_CLOSE_BEHAVIOR = SUSPENDED_NOT_TRADABLE
QLIB_MODIFIED = NO
QLIB_EXECUTED = NO
```

The terminal-gap policy therefore agrees with the accepted upstream execution
semantics and requires no Qlib patch.

## Quantiacs personal local operational retention

The current public evidence supports a deliberately narrow project policy:

- The [Quantiacs User Agreement](https://quantiacs.com/termsofuse) grants
  compliant users personal-purpose use and prohibits third-party transfer,
  commercial copying, and public distribution of market data.
- The official [local-development guide](https://quantiacs.com/documentation/en/user_guide/local_development.html)
  and [Quantiacs Toolbox](https://github.com/quantiacs/toolbox) support local
  development and execution.
- The official [development-environment documentation](https://quantiacs.com/documentation/en/user_guide/code.html)
  describes a local `data-cache` for loaded data.
- A Quantiacs [community support response](https://quantiacs.com/community/topic/281/local-development-with-notifications)
  documents ordinary local-tooling settings including `CACHE_DIR=data-cache`
  and `CACHE_RETENTION=7`.

These sources support personal use and local operational caching. They do not
establish perpetual archival rights, and none are interpreted as doing so.

```text
P2_DATA_USAGE_PROFILE = PERSONAL_PRIVATE_NONCOMMERCIAL_NONREDISTRIBUTED
QUANTIACS_PERSONAL_USE = PASS
QUANTIACS_LOCAL_OPERATIONAL_CACHE = SUPPORTED_BY_OFFICIAL_TOOLING
QUANTIACS_THIRD_PARTY_TRANSFER = PROHIBITED
QUANTIACS_PUBLIC_REDISTRIBUTION = PROHIBITED
QUANTIACS_COMMERCIAL_COPYING = PROHIBITED
QUANTIACS_INDEFINITE_ARCHIVAL_RIGHT = NOT_ESTABLISHED_NOT_REQUIRED
QUANTIACS_PRIVATE_LOCAL_RETENTION_WRITTEN_CONFIRMATION_REQUIRED = NO_FOR_CURRENT_PERSONAL_PROFILE
QUANTIACS_PERSONAL_LOCAL_OPERATIONAL_RETENTION = ACCEPTED
```

This is a project certification-policy decision, not a legal opinion. It is
limited to personal, private, noncommercial, nonredistributed local operational
retention during the active research/certification lifecycle. Quantiacs-derived
data must remain private, local, outside Git, noncommercial, and
nonredistributed.

Permitted reproducibility metadata includes provider, retrieval UTC,
request/config, upstream/toolbox version, schema, dataset/content hash,
transformed-artifact hash, model-artifact hash, code SHA, and certification
manifest. A changed source dataset must produce a new dataset hash and
certification version; certification history must never be silently
overwritten. A material terms change or explicit prohibition of local use
causes a prospective fail-closed route review.

## Certification profile boundary

```text
PROFILE_A = PERSONAL_CAPITAL_CERTIFICATION
PROFILE_B = INSTITUTIONAL_FORENSIC_DATA_CERTIFICATION
CURRENT_PROFILE = PROFILE_A
```

Profile A requires correct PIT identity, ticker-reuse protection,
corporate-action correctness, no lookahead, no silent synthetic fill, explicit
missing-data handling, reproducible code/config/hash manifests, private
nonredistributed data handling, separated train/validation/sealed-OOS windows,
multiple-testing control, and realistic cost/slippage/stress testing.

Profile A does not require every vendor to expose an immutable revision ID,
perpetual archival language for every free source, zero missing rows for every
delisted security, or written vendor correspondence for ordinary supported
local-cache behavior. Profile B may require stronger forensic and licensing
evidence, but it is not the current project profile.

Nothing in this adjudication weakens survivorship-bias controls, identity
rules, leakage controls, OOS sealing, multiple-testing protection, or
production risk controls.

## Final blocker adjudication

```text
DISCK_2022_04_08_EXACT_PRICE_AUTHORITY = NO_LONGER_HARD_BLOCKER
QUANTIACS_PRIVATE_LOCAL_RETENTION_WRITTEN_CONFIRMATION = NO_LONGER_HARD_BLOCKER
REMAINING_CERTIFICATION_DATA_HARD_BLOCKERS = NONE
NO_ADDITIONAL_PRICE_PROVIDER_REQUIRED = YES
PROVIDER_EXPANSION_GATE = CLOSED
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
YAHOO_CERTIFICATION_ROUTE = RETIRED
TIINGO_STARTER_CERTIFICATION_ROUTE = RETIRED
```

The provider-expansion gate remains closed. No new price provider, account, or
key is required or authorized by this result.

## Repository and non-actions

```text
MARKET_DATA_IN_GIT = NO
PROVIDER_RESPONSE_BODY_IN_GIT = NO
CREDENTIAL_IN_GIT = NO
PRIVATE_LICENSED_ARTIFACT_IN_GIT = NO
MODEL_TRAINING = NO
BACKTEST = NO
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
PUSHED = NO
PR_CREATED = NO
MERGED = NO
CURRENT_NEXT = P2_FROZEN_CERTIFICATION_DATASET_CONTRACT
```

The frozen certification dataset contract is not started in this task.
