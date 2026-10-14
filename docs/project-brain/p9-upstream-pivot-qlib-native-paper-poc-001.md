# P9 Upstream Pivot and Qlib Native Paper POC 001

**Task:** `AUTONOMOUS-QUANT-P9-UPSTREAM-PIVOT-QLIB-NATIVE-PAPER-POC-001`
**Date:** 2026-10-13
**Base origin/main:** `0056ccab14d3e9c55a37393006922b5caafe8b9a`
**Scope:** owner-authorized upstream direction reset and one bounded native
historical simulation; no production activation.

## Direction decision

The owner changed the preferred P9 technical direction to the existing
official Microsoft Qlib runtime first. NautilusTrader Sandbox is an alternate
candidate only if a required capability is unavailable in Qlib. LEAN remains
an alternate/reference engine, not a mandatory production dependency. The
Alpaca plugin exploration is retired from the active P9 path. Robinhood Trading
MCP remains the preferred P10 live brokerage interface; no LEAN-to-Robinhood
connector is asserted.

```text
P9_PRIMARY_CANDIDATE = QLIB_NATIVE_DAILY_SIMULATION
P9_REALTIME_SANDBOX_ALTERNATE_CANDIDATE = NAUTILUSTRADER
P9_LEAN_ROLE = ALTERNATE_REFERENCE
P9_ALPACA_PLUGIN_ACTIVE = NO
P9_REAL_MARKET_DATA_ROUTE = UNRESOLVED
P9_CONTINUOUS_PAPER_TRADING = NOT_READY
P10_PREFERRED_LIVE_BROKER = ROBINHOOD_TRADING_MCP
```

This supersedes the prior technical preference for LEAN; it does not rewrite
the P9/P10 roadmap exit condition or claim P9 is complete.

## Pinned Qlib authority

| Item | Verified authority |
|---|---|
| Official source | Microsoft Qlib |
| Runtime version | `0.9.8.dev26` |
| Source SHA | `2fb9380b342556ddb50a4b24e4fe8655d548b2b8` |
| Source checkout | `/home/zhou/AQ_WORKSPACES/p0-poc-b-qlib-src` (clean) |
| Runtime | `/home/zhou/miniforge3/envs/rdagent4qlib/bin/python` |
| Installed package | Qlib under the `rdagent4qlib` environment |
| Data authority | P1 non-sealed US Qlib provider at `/home/zhou/AQ_DATA/P1/qlib-native-baseline-001/qlib_data` |

Pinned public APIs inspected were `qlib.backtest.backtest`,
`SimulatorExecutor`, `Exchange`, `Account`,
`qlib.contrib.strategy.signal_strategy.TopkDropoutStrategy`,
`qlib.workflow.online.manager.OnlineManager`,
`qlib.workflow.online.strategy.OnlineStrategy`, and the contrib online
Operator/manager source. The pinned official Online Serving documentation is
[`docs/component/online.rst`](https://github.com/microsoft/qlib/blob/2fb9380b342556ddb50a4b24e4fe8655d548b2b8/docs/component/online.rst).
It states that daily prediction for the next trading day is supported, while
generating next-day orders is not supported because of public-data
limitations.

## Capability assessment

| Requirement | Pinned Qlib evidence | Assessment |
|---|---|---|
| A. Daily trading decision | Native `TopkDropoutStrategy`; its decision path requests signal data at the preceding trade-calendar step. | Supported for historical simulation. |
| B. Virtual order simulation | `SimulatorExecutor` executes native strategy decisions against Qlib `Exchange`; the bounded run completed eight daily steps. | Supported for historical simulation. |
| C. Cash accounting | Native `Account`/`Position`; daily reports include cash. | Demonstrated. |
| D. Holdings | Native account positions track instrument amounts and values. | Demonstrated. |
| E. Transaction costs | Native `Exchange` accepts open/close/impact/minimum-cost parameters; nonzero open/close costs were set in the demonstration. | Mechanism demonstrated; exact aggregate cost was not retained in the captured output. Parameters were fixtures, not approved policy. |
| F. NAV/history | Native portfolio metrics include account value, return, cash, benchmark and position snapshots. | Demonstrated for the short simulation. |
| G. Save/restore | Native `Account.save_account`/`load_account` and `UserManager.save_user_data`/`load_user` APIs exist. | Source capability present; round-trip and day-to-day continuation were not tested. |
| H. No-hindsight daily timing | The strategy fetches the prior trade step's signal before the current session decision. The fixture ranked one-session close-to-close returns available by the previous close and executed at the current session open. | Demonstrated in the bounded historical path; not a forward/live feed guarantee. |
| I. US instrument identities | Qlib initialized with `region=us`; the P1 provider returned complete daily `$open`, `$close`, and `$volume` rows for AAPL, MSFT and SPY over the checked sample window. | Compatible with these existing Qlib instrument labels. This is not a general security master or identity adjudication. |
| J. Avoid China defaults | The top-level backtest API defaults to `SH000300`. In this pinned version, `benchmark=None` creates an empty config that falls through to that default and fails against the US provider. | Must explicitly supply an available US benchmark. The completed run used existing P1 SPY. No source patch or custom benchmark was used. |

`qlib.contrib.online.operator.Operator` is not an available end-to-end
paper-order flow in the installed pinned runtime: importing it fails because
the referenced `qlib.contrib.backtest` and `qlib.contrib.online.executor`
modules are absent. `OnlineManager`/`OnlineStrategy` are model/prediction
management surfaces and are not a brokerage. A module's existence or
successful import alone is not evidence of order routing.

## Bounded native historical daily simulation

One native Qlib daily simulation used the approved non-sealed P1 provider; no
source or configuration files were modified. The selection was a
plumbing-only fixture, not an alpha hypothesis:

- Instruments: `AAPL`, `MSFT`, `SPY`.
- Sessions: 2015-01-06 through 2015-01-15 (eight daily sessions).
- Strategy: official `TopkDropoutStrategy`, `topk=2`, `n_drop=1`,
  `risk_degree=0.8`.
- Score: preceding-session close-to-close return, computed solely from
  already observed close values; strategy timing used the prior session's
  score, and virtual execution used current-session `$open`.
- Execution: official `SimulatorExecutor(time_per_step="day")` and Qlib
  `Exchange`; account fixture `1,000,000`; open/close costs each `0.001`,
  minimum and impact cost `0`. These are synthetic demonstration settings,
  not human-approved policy.
- Benchmark: explicit existing US `SPY` series. The first preflight invocation
  with `benchmark=None` stopped before the simulation loop because the pinned
  Account report path defaulted to CSI300; it did not create orders or run a
  session. The one completed simulation then used SPY to avoid the Chinese
  default.

The completed native result had eight daily report rows and eight position
snapshots. Qlib's native trade indicator recorded nonzero deal amounts on six
sessions (with its `count` field equal to two on those sessions) and zero
deal amounts on two sessions. Daily account values, cash and holdings changed
through the native execution path. On the final row (2015-01-15), reported
account value was approximately `988,858.84` fixture units, cash
`117,218.95`, with AAPL and SPY in the position snapshot. The provider's
stored prices are normalized research values, not dollar-denominated
execution prices; these values are not economically interpretable returns,
profitability evidence, a strategy evaluation, or investment results. The
captured console summary did not retain per-order records or an exact summed
transaction-cost amount.

Qlib emitted `future=True; return current calendar` warnings because a future
daily calendar was unavailable in this provider configuration. The requested
simulation ended on 2015-01-15 and added no future observation. This warning
does not establish that the requested dates were at the provider's final
loaded observation. No later session, P2 sealed OOS data, real market feed,
account, or broker was accessed.

## Classification and limitations

```text
QLIB_NATIVE_DAILY_SIMULATION = PASS_NATIVE_DAILY_SIMULATION
QLIB_ORDER_SIMULATION = YES_HISTORICAL_VIRTUAL_EXECUTION
QLIB_CASH_ACCOUNTING = DEMONSTRATED
QLIB_POSITION_TRACKING = DEMONSTRATED
QLIB_PORTFOLIO_NAV = DEMONSTRATED
QLIB_TRANSACTION_COSTS = NATIVE_COST_PARAMETERS_APPLIED_AMOUNT_NOT_RETAINED
QLIB_STATE_PERSISTENCE = APIS_PRESENT_ROUNDTRIP_UNVERIFIED
QLIB_US_EQUITY_COMPATIBILITY = DEMONSTRATED_FOR_AAPL_MSFT_SPY_P1_LABELS
QLIB_NEXT_DAY_ORDER_LIMITATION = DOCUMENTED
P9_FORWARD_DAILY_PAPER_READY = NO
P9_CONTINUOUS_REALTIME_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
```

This proves only a short historical virtual simulation. It does not prove a
forward daily paper process, continuous real-time data acquisition, durable
restart/reconciliation, production-grade instrument identity, complete
per-order audit persistence, or a working brokerage. The real-market-data
route remains unresolved. If Qlib's documented online order limitation blocks
a required capability, NautilusTrader Sandbox may be evaluated as the next
official upstream candidate; it is not installed or selected here.

## Boundaries

No Qlib, LEAN, AQ production source, P2, P3, or P8 contract was modified. No
NautilusTrader deployment, Alpaca activation, credentials, accounts, external
orders, persistent services, P2 sealed OOS access, or production activation
occurred. This record is documentation and feasibility evidence only.
