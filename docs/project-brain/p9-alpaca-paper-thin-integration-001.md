# P9 Alpaca Paper Thin Integration 001

**Task:** `AUTONOMOUS-QUANT-P9-ALPACA-PAPER-THIN-INTEGRATION-001`
**Base:** `d68178d5ab65d8c8e37b731e74c8adda69fc3a7e`
**Scope:** protected-credential read-only connectivity and synthetic, non-executable contract preview. No orders or deployment.

## Authority and phase decision

PR #149's statement that Alpaca was inactive remains an accurate historical
record of that decision. This task makes a newer, explicitly scoped decision:
Alpaca is selected as a **P9 Paper account/API candidate only**. This does not
replace Qlib's P9 historical research role, change the P9/P10 roadmap exit
conditions, activate the previously retired Alpaca plugin, or make Alpaca the
P10 live broker. Robinhood Trading MCP remains the P10 preferred live-broker
candidate. Paper trading, orders, and production remain separately gated.

```text
PR149_ALPACA_INACTIVE_RECORD = HISTORICAL_AND_PRESERVED
P9_ALPACA_PAPER_ACCOUNT_CANDIDATE = SELECTED_FOR_BOUNDED_FUTURE_EVALUATION
P9_Qlib_HISTORICAL_DAILY_SIMULATION = PASS_EXISTING_EVIDENCE_REUSED
P9_REALTIME_MARKET_DATA_PERMISSION = UNKNOWN_NOT_QUERIED
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
P2_SEALED_OOS_ACCESSED = NO
```

## Upstream ownership and protected read-only path

The existing `alpaca-py 0.44.0` runtime is reused. Its installed
`TradingClient` constructor accepts `paper=True`; the pinned implementation
selects its Paper base URL unless a URL override is supplied. The read-only
probe supplies no override, checks the resolved base URL, rejects any endpoint
other than `https://paper-api.alpaca.markets`, and is bounded by a 45-second
parent-process timeout. Alpaca's SDK owns account, clock, position, and order
reads and all eventual broker order-state APIs; this AQ boundary has no submit,
replace, cancel, or close operation. See the [official Paper Trading guide](https://docs.alpaca.markets/us/docs/paper-trading)
and [official alpaca-py Trading API documentation](https://github.com/alpacahq/alpaca-py/blob/master/docs/trading.rst).

The repeatable local probe is
`60-execution-system/execution-adapter/alpaca_paper_readonly_probe.ps1`.
It accepts only the specifically named, current-user DPAPI credential file
created from the owner's replacement Paper key set; it has no fallback to the
older encrypted file or Desktop plaintext. The encrypted input is decrypted in
the PowerShell process and forwarded to a one-shot SDK child through redirected
stdin. No credential enters command arguments, environment variables, files,
stdout, or error text. The child performs only `get_account()`, `get_clock()`,
`get_all_positions()`, and `get_orders(GetOrdersRequest(status=ALL, limit=500))`.
The output omits account identifiers, symbols, balances, and credential
material; it reports only status and counts.

Observed read-only result:

```text
SDK_VERSION = 0.44.0
TRADING_CLIENT_PAPER = YES
PAPER_BASE_URL_GUARD = PASS
ACCOUNT_READ = PASS_ACTIVE
CLOCK_READ = PASS_MARKET_CLOSED_AT_CHECK
POSITIONS_READ = PASS_COUNT_0
ORDERS_READ = PASS_COUNT_0
ORDER_MUTATION_CALLS = 0
LIVE_ENDPOINT_CONTACTED = NO
```

This proves those four account API reads worked once with the current Paper
credential. It does not prove market-data entitlements, real-time feed health,
order submission, reconciliation, restart recovery, or continuous operation.

## P8 TargetPortfolio boundary

The frozen P8 `AQ_TARGET_PORTFOLIO_V1` remains unchanged. Its asset keys are
P2 `P2SEC` identities, never broker symbols. `alpaca_target_preview.py` is a
non-networked, non-submitting boundary: it requires external injected
authorities to verify actual P2 Certified/P4 Champion references and the
human-owned risk envelope, and an external identity resolver to return an
effective P2 episode-to-Alpaca-symbol mapping. No resolver, P2 Certified input,
P4 Champion, approved human risk envelope, or production market-data identity
mapping is supplied by this change. Missing authority fails closed.

The preview requires a Paper endpoint, an order-state-known assertion,
non-duplicate target identity, effective-time-valid P2 mapping, usable USD
quotes within the caller-resolved risk policy's age limit, account status,
available cash and broker buying-power checks, and explicit risk-policy
permissions for shorting or leverage. The TargetPortfolio ID is checked as
SHA-256 over RFC 8785/JCS bytes with only `target_portfolio_id` omitted, using
the existing upstream `rfc8785` package when available; there is deliberately
no local canonicalization fallback. The checked development runtimes did not
have `rfc8785` installed, so the public preview now fails closed with
`RFC8785_VALIDATOR_UNAVAILABLE`; complete P8 content-identity validation is
not yet available in this runtime.

Existing nonzero holdings omitted from `target_weights` are rejected because
this thin boundary cannot infer their P2SEC identity or create a complete
liquidation plan. A cash-only target with no positions remains a valid empty
preview; an explicit zero target for a mapped asset produces a sell preview.
Account margin capability (`multiplier`) is not treated as evidence that the
strategy uses leverage. Actual strategy leverage is identified from gross
target exposure or purchases that exceed current cash, and broker buying power
is checked separately. When leverage is not authorized, buying beyond cash is
rejected even if broker buying power is higher. The preview returns in-memory
lines with `executable=false`; it does not submit requests or maintain durable
intent/reconciliation state. A synthetic test constructs the installed SDK's
`MarketOrderRequest` only to validate static field compatibility; it never
calls an order method. The existing P0 POC-D ExecutionPlan evidence is reused
as prior synthetic planning evidence; its planner is not copied.

All successful authority/identity paths in downstream preview-mechanics tests
use fixture-only verifiers, mapping, prices, account state, and references;
those tests bypass the unavailable JCS package only to exercise unrelated
preview rules. A separate public-path regression verifies that missing
`rfc8785` fails closed. These tests prove neither successful P8 identity
verification nor authorization, identity truth, market-data permission, or an
investable portfolio.

## Market-data limits and remaining blockers

No market-data endpoint or stream was called. The account's actual feed
subscription is therefore unverified. Alpaca's current Paper-only account
documentation states IEX entitlement; its market-data plan comparison
distinguishes Basic real-time IEX from consolidated SIP coverage. This report
does not infer this user's actual entitlement from a successful Trading API
call. See [Paper Trading](https://docs.alpaca.markets/us/docs/paper-trading),
[market-data subscription plans](https://docs.alpaca.markets/us/docs/about-market-data-api),
and the [market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq).
No IEX feed test, SIP entitlement test, WebSocket, or persistent service was
started.

Real P9 forward-paper remains blocked on, at minimum: a real P2 Certified
TargetPortfolio and any required P4 Champion authority; a human-approved,
effective risk-envelope artifact; an authoritative historical P2SEC-to-Alpaca
tradable-symbol identity mapping; an approved live market-data source/price
freshness policy that does not use Qlib normalized research prices; and
durable idempotency, unknown-order-state, update-stream/reconciliation, and
restart evidence. The synthetic preview's `prior_intent_ids` input is
process-local test logic, not durable duplicate-order protection.

```text
P8_CONTRACT_MODIFIED = NO
REAL_CERTIFIED_INPUTS = 0
REAL_P4_CHAMPIONS = 0
HUMAN_RISK_ENVELOPE_APPROVED = NO
P8_TO_ALPACA_SYNTHETIC_OFFLINE_PREVIEW = PASS
P9_THIN_BOUNDARY = PASS_SYNTHETIC_ONLY
P9_REALTIME_DATA_READY = UNKNOWN
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
PAPER_ORDERS_SUBMITTED = 0
BROKER_MUTATION_ACTIONS = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_DEPENDENCIES = 0
```

The minimal future architecture is frozen as a boundary only:

```text
Qlib/skfolio target computation
    -> frozen P8 TargetPortfolio
    -> external P2/P4/risk/identity verification
    -> approved market-data + account snapshot
    -> offline execution preview / separate order authorization
    -> official alpaca-py Paper API
```

An isolated, explicitly authorized Paper Broker API engineering test may use
synthetic inputs without a real P2 Certified strategy, provided all fixtures
are labeled `ENGINEERING_TEST_ONLY` and are never represented as certification
or a real strategy. This classification does not waive separate owner
authorization for any order submission. Real strategy integration still
requires actual P2/P4 decisions, human risk authority, verified identity and
market-data inputs. No Paper order is submitted by this change. No production
P9 adapter is ready; forward and continuous operation remain separately
blocked by the real-input and operational blockers above.
