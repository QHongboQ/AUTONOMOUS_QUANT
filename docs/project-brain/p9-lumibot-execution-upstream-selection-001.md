# P9 Lumibot Execution-Upstream Selection and PR #150 Supersession 001

**Task:** `AUTONOMOUS-QUANT-P9-LUMIBOT-UPSTREAM-ADOPTION-AND-PR150-SUPERSESSION-001`
**Date:** 2026-10-13
**Base origin/main:** `d68178d5ab65d8c8e37b731e74c8adda69fc3a7e`
**Scope:** upstream selection and offline native verification; no broker connection, order submission, deployment, or production authorization.

## Decision and authority

The owner selects official Lumiwealth Lumibot **v4.6.18**, source SHA
`730d5608f3ee625f0a30dc15e8cc512205dd2a2b`, as the sole P9 stock-execution
integration candidate. Reuse the already-installed isolated Python 3.11
environment and immutable pinned upstream source; no package or source changes
were made in this task.

This supersedes the *technical preference* in the earlier P9 Qlib-first
direction record without rewriting that historical record or PR #149. Qlib
continues to own research, predictions and historical simulation. Lumibot is
selected to own generic rebalance and order mechanics when an integration is
later authorized and its prerequisites are proven. Alpaca Paper remains the
intended broker, but this task did not contact it. P10's Robinhood Trading MCP
candidate is unchanged.

```text
P9_RESEARCH_OWNER = QLIB
P9_EXECUTION_UPSTREAM = LUMIBOT_4.6.18
P9_EXECUTION_UPSTREAM_STATUS = SELECTED_FOR_INTEGRATION_NOT_RUNTIME_READY
P9_PAPER_BROKER = ALPACA_PAPER
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
BROKER_MUTATION_ACTIONS = 0
```

## P8 and fail-closed integration boundary

P8 TargetPortfolio V1, its RFC 8785/JCS identity semantics, P2SEC identity
rules, P2 certification and P4 Champion requirements, and human-owned risk
envelope remain unchanged. P8 still has no real P2 Certified strategy inputs,
no real P4 Champions, and no approved human risk-limit set. P8 schema-valid or
synthetic inputs are not trade authorization.

No P2SEC-to-Alpaca/Lumibot broker-instrument mapping has been proven here.
There is also no approved, verified risk envelope, authorized strategy, or
runtime market-data policy. Accordingly, this PR adds **no order-capable
adapter or execution preview**. Any later integration must fail closed before
Lumibot receives an actionable target unless the exact asset mapping, actual
P2/P4 decision references, current human risk authorization, effective time,
and paper-only broker configuration are independently verified. Generic
weight-to-order conversion, holdings, cash/buying-power calculations, order
state, fills, cancellation, recovery and reconciliation belong to Lumibot and
the official broker integration, not a duplicate AQ engine.

## Pinned upstream evidence and supplemental checks

The completed full official installation and initial 95 unique passing
upstream offline test cases are recorded at
`E:\AQ\RESEARCH\P9\lumibot-v4.6.18-full-install-003\verification.md`, with
install and test logs alongside it. That record confirms version 4.6.18,
dependency closure (`uv pip check`), core imports and CLI smoke. No
installation was repeated here.

This task reran the following pinned-source official tests using the isolated
environment (`LUMIBOT_DISABLE_DOTENV=1`):

- existing-position/quote-asset target calculation;
- existing official full-sale order generation with limit and fractional
  limit orders;
- shorting-disabled order behavior;
- official backtesting order-lifecycle tests.

Result: **16 passed**, one upstream deprecation warning. A direct offline
probe through official `DriftCalculationLogic` supplied an existing AAPL
position and a 100% USD target. The result retained the cash target, assigned
the omitted AAPL position a zero target, and emitted a full-sale drift. It
submitted no order. This confirms native calculation semantics, not a complete
BacktestingBroker liquidation/fill from a cash-only target.

| Boundary | Evidence/status |
|---|---|
| Existing position excluded from target | Official calculation test and supplemental cash-target probe; target becomes zero. |
| Full-sale order generation | Official `DriftOrderLogic` tests pass. |
| End-to-end all-cash simulated liquidation/fill | **Not verified**; no combined native scenario was run. |
| Sell before buy | Ordering exists in pinned upstream logic; source-confirmed, not separately fault-injected in this task. |
| Pending order on next rebalance | The official example calls `cancel_open_orders()`; cancellation completion/race and partial-fill interaction are not established. |
| Partial fill / broker rejection during rebalance | **Not verified** by the selected offline tests. |
| Restart/reconciliation | Pinned `StrategyExecutor` startup source calls broker position sync and open-order retrieval; **source-only**, no restart test. |
| No shorting / cash-limited buy sizing | `DriftRebalancerLogic` defaults `shorting=False`; official test confirms short-disabled behavior. Its source limits buys to cash, but account-specific margin semantics are not tested here. |
| Alpaca Paper execution | Prior source/config evidence only. No credentials, broker client, API, or order endpoint were used here. |

The official runtime's ability to calculate target drift does not itself prove
that a requested portfolio is investable, identity-safe, funded, or authorized.
There is no human-approved numeric leverage/capital policy in P8 to configure.

## PR #150 supersession scope

PR #150 remains **OPEN, unchanged, and unmerged** at the verified head
`29fe4d15a137a7fedebb9970d446b5587ff331d1`. This PR does not import its source
or rewrite it. After owner review of this selection record, the intended
successor disposition is:

- Retire `60-execution-system/execution-adapter/alpaca_target_preview.py` and
  its tests for AQ-computed target deltas, share quantities, buying-power or
  margin calculations, liquidation and process-local duplicate-intent logic.
- Retain the P8 contract, identity/certification/risk-authority requirements;
  they are not broker execution functionality.
- Consider retaining the read-only probes
  `alpaca_paper_readonly_probe.ps1` and
  `alpaca_paper_readonly_probe.py` only if a later approved operations design
  still needs them. They are not part of this PR and no credentials were read.
- Do not translate the frozen P2SEC identifiers directly into broker symbols.
  No production or paper submission route exists until an authoritative
  historical provider-to-broker identity mapping and authorization boundary
  are separately established.

This is a retirement recommendation, not deletion of PR #150. PR #150 must
remain untouched until the successor PR is reviewed; no PR was merged or
closed by this task.

## Repository and non-actions

This change is documentation-only because there is no currently safe
P8-to-Lumibot actionable target boundary to implement. It does not alter P8
contracts, add an AQ order planner, adapter, risk calculator, runner, or
configuration, or create an AQ execution engine.

```text
LUMIBOT_UPSTREAM_SELECTED = YES
LUMIBOT_RUNTIME_ADMISSION = BLOCKED
NATIVE_CASH_ONLY_LIQUIDATION = NOT_VERIFIED_END_TO_END
NATIVE_PARTIAL_FILL_AND_CANCEL_HANDLING = NOT_VERIFIED
NATIVE_RESTART_RECONCILIATION = SOURCE_ONLY_NOT_VERIFIED
P8_CONTRACT_PRESERVED = YES
AQ_GENERIC_EXECUTION_ENGINE_CREATED = NO
PR150_MERGED = NO
NEW_GENERIC_AQ_ENGINE_COUNT = 0
BROKER_MUTATION_ACTIONS = 0
LIVE_ENDPOINT_CONTACTED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
```

## Next single action

Complete the remaining offline acceptance using only Lumibot's official
native components and tests: an end-to-end 100%-cash liquidation, pending and
partially filled order/cancellation handling during rebalance, and restart
position/order recovery. Do not connect to Alpaca or submit orders. Keep PR
#150's close/retire decision separate; this task does not close it.
