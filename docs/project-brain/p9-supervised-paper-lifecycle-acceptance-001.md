# P9 supervised Paper lifecycle acceptance 001

**Date:** 2026-10-16
**Classification:** bounded `ENGINEERING_TEST_ONLY` acceptance; not strategy certification or runtime authorization.

## Purpose and fixed upstream

This record closes the supervised, one-shot P9 Paper lifecycle test across read-only startup synchronization, one explicitly authorized test buy, a fresh-process recovery, and a separately authorized one-share cleanup. No Live endpoint was contacted. The original local evidence remains outside Git; only redacted outcomes and SHA-256 fingerprints are recorded here.

```text
BROKER = Alpaca Paper only
EXECUTION_UPSTREAM = Lumibot 4.6.18
LUMIBOT_UPSTREAM_SHA = 730d5608f3ee625f0a30dc15e8cc512205dd2a2b
TEST_CLASSIFICATION = ENGINEERING_TEST_ONLY
P9_SUPERVISED_PAPER_LIFECYCLE = PASS
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
P8_CONTRACT_MODIFIED = NO
P2_SEALED_OOS_ACCESSED = NO
LIVE_ENDPOINT_CONTACTED = NO
```

## Results

| Stage | Verified result |
|---|---|
| A — read-only cross-process sync | PASS. Separate process IDs 22560 and 16848; each reported zero broker-write calls. This proves read-only synchronization only, not restoration of an order created by a prior process. |
| B — real Paper order and new-process recovery | PASS. Lumibot submitted one limit BUY of 1 share of F at $12.62. The order filled 1 share. A (PID 15316) exited successfully; fresh B (PID 24440), with a new Broker and same explicitly named Strategy, recovered the same broker order identity and Strategy ownership, filled quantity 1, and F position 1. B made zero order-write calls. |
| C — authorized residual cleanup | PASS. After fresh Paper preflight, Lumibot submitted one limit SELL of 1 F share at $12.55; the order filled 1 at average $12.55. The post-trade read showed F position 0 and zero open orders. No additional write followed. |

The private order and client-order identifiers were cross-checked across the Stage B report, Stage C report, and sell intent. They are deliberately omitted from this public record. Stage C's final account state is an observation at the cleanup completion time, not a claim about later account state.

### Order-status adjudication

The raw Stage B report preserved a literal-string comparison of `false`: Alpaca returned `filled`, while Lumibot exposed its canonical status `fill`. This did not indicate conflicting broker state. In the pinned Lumibot 4.6.18 source, `lumibot/entities/order.py` maps `filled` to `fill` in `STATUS_ALIAS_MAP` (lines 132–137), and the status setter applies that alias (lines 1116–1122). The separate local `status-adjudication.md` records this interpretation. The raw report and its original comparison result remain unchanged. On that pinned semantic mapping, order status, order identity, filled quantity, Strategy ownership, and position recovery all agree.

### Local evidence fingerprints

The source files named below remain in the owner's local research directory and are not included in this repository. SHA-256 values are fingerprints of the exact private evidence files used for this closeout; no account identifiers or raw broker responses are published.

| Evidence file | SHA-256 |
|---|---|
| `readonly-stage-a-results-utc-preserved.json` | `39f081f7a75ea47a17ccaebdf1932a609b5266ef1d66c8c25881821382bdfd7c` |
| `stage-b-001/stage-b-final-report-02.json` | `06a9afaad63b8ddddd99c4ae05b0412e6e8d840cfcc93e91ae2baafb892bebce` |
| `stage-b-001/status-adjudication.md` | `676af676d5bb2fd294249a70a5c0cf3e765a9cb37b6173e7e32db3aa60c47129` |
| `one-share-cleanup-001/cleanup-report.json` | `ac5eb48840641841203ddfb5de1e39d0511286e2c9f0c14fff58d3a4c3859a48` |
| `one-share-cleanup-001/sell-intent.json` | `9a8c605aa5ad83e489b46ed9c66ccf2fe2d1d141df18658d22fb39a2aca9d8e7` |

Cross-checks confirmed that the Stage C intent client ID matches the cleanup report, its original buy references match the Stage B order identity, and the reported final position/open-order counts satisfy the cleanup acceptance criteria.

## What this acceptance does not establish

The following P9 gates remain open and must not be inferred from A/B/C:

1. Official Lumibot end-to-end execution of a 100% cash target, including simulated liquidation fills.
2. Safe full-strategy handling of partial fills, cancel races, and unresolved order states.
3. Safe bounds for Alpaca SDK writes: no finite HTTP timeout and default POST retry behavior leave uncertain submission outcomes as a risk.
4. Complete long-term order-history inventory/recovery beyond Lumibot's current 100-order synchronization limit.
5. Valid real P2/P4 strategy and certification authority.
6. Authoritative P2SEC-to-broker instrument identity mapping.
7. Human-approved numeric capital, leverage, and risk limits.
8. Continuous runtime, fault recovery, and unattended-trading acceptance.

Therefore this bounded engineering test does not make forward Paper, continuous Paper, or production trading ready. No AQ generic execution engine was created.

```text
STAGE_A_READONLY_SYNC = PASS
STAGE_B_ORDER_RECOVERY = PASS
STAGE_C_ONE_SHARE_CLEANUP = PASS
FINAL_POSITION_AT_CLOSEOUT = 0 F
FINAL_OPEN_ORDERS_AT_CLOSEOUT = 0
NEW_BROKER_ACTIONS_DURING_CLOSEOUT = 0
AQ_GENERIC_EXECUTION_ENGINE_CREATED = NO
P9_FORWARD_PAPER_READY = NO
P9_CONTINUOUS_PAPER_READY = NO
P9_PRODUCTION_AUTHORIZED = NO
```

## Next single technical action

Complete the remaining official Lumibot offline native execution acceptance, prioritizing end-to-end 100% cash liquidation and partial-fill/cancel safety. Do not start another Paper order test as part of that work.
