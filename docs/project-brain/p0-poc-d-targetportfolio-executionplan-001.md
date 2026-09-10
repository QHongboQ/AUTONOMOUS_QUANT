# P0 POC-D TargetPortfolio to ExecutionPlan 001

**Task:** `AUTONOMOUS-QUANT-P0-POC-D-TARGETPORTFOLIO-EXECUTIONPLAN-001`  
**Result:** `POC_D = PASS` — deterministic local planning and static schema compatibility validation only.

## Scope and lineage boundary

POC-D proves the final P0 boundary: a broker-neutral synthetic `TargetPortfolio` becomes a deterministic local `ExecutionPlan`; its simulated payloads validate against the already-recorded Robinhood equity-order schema. It is not a recommendation, production certification, broker connection, paper trade, or live-trading action.

POC-C's `target-portfolio.json` was inspected read only. Its SHA-256 is `f8edd57b55d43bd033ca893f586f6db08ec8c3b751a0a5a4ff557876c88995b0`; it remains broker-neutral and has none of the prohibited execution/broker fields. POC-D deliberately does **not** turn POC-C's tiny-POC MeanRisk weights into orders.

## Synthetic fixture and planner result

The literal account identifier is `RH_ACCOUNT_PLACEHOLDER`; no real account number was accessed or stored. The local fixture uses account equity `$1,000`, confirmed buying power `$750`, reserve `$100`, USD reference prices AAPL `$100`, MSFT `$200`, SPY `$500` (synthetic age four minutes), and positions AAPL `1`, MSFT `0`, SPY `1`. Its broker-neutral targets are AAPL `0.40`, MSFT `0.30`, SPY `0.20`, CASH `0.10`.

The planner reproduced the expected deltas exactly: AAPL `+$300`, MSFT `+$300`, SPY `-$300`.

| Symbol | Simulated intent | Mutually exclusive executable amount |
|---|---|---:|
| AAPL | buy / market | `dollar_amount=300` |
| MSFT | buy / market | `dollar_amount=300` |
| SPY | sell / market | `quantity=0.6` |

The policy is explicitly `REGULAR_HOURS_ONLY`. No optional `market_hours` enum was guessed.

## Fail-closed invariants

Spendable buying power is `$750 - $100 = $650`; planned buys total `$600`. Planned SPY sale proceeds are **not** counted as spending authority. The one negative invariant fixture used buying power `$650`, reserve `$100`, spendable `$550`, unchanged `$600` buys and `$300` planned sale; it returned `REJECT` for insufficient confirmed buying power and was not written as an executable plan.

The planner rejects a delta below `$5`, price older than five minutes, missing/non-positive/non-USD price, unsupported side/type/session, insufficient confirmed buying power, and a sell above current position. Sell quantities are rounded down to six decimals and cannot create a short.

## Canonical snapshot, idempotency, and mutation

Uppercase assets, sorted inputs, normalized numeric representation, target, positions, prices, buying power, reserve, and policies form the canonical snapshot. The base snapshot SHA-256 is:

`0c23a30b6b732f3991c66bd58c7b165473fcfaa70c1534e0cf57c98b0d20da02`

The local execution identity is UUIDv5 `1186edac-f2dd-56ca-985c-5534ae293f3d`, derived with `uuid.NAMESPACE_URL`. Each deterministic UUIDv5 `ref_id` derives from snapshot hash, symbol, side, type, and canonical executable fields:

| Symbol | `ref_id` |
|---|---|
| AAPL | `797df6e5-1de8-504e-9d96-0d1389ff804d` |
| MSFT | `80661223-839d-5760-8f00-feaa9394cbd6` |
| SPY | `a850c5f5-e6c1-5f2a-86c9-8c948d7fcad5` |

The identical fixture was planned twice: snapshot hash, execution ID, ordered payload set, and all `ref_id` values were identical, and the second classification is `DUPLICATE_NO_NEW_PLAN`. A non-authoritative AAPL target mutation `0.40 -> 0.41` produced new snapshot `edea60ec470c8c1f6e617fbab76f734c74cefc2785119e0a5daed62e9a02f65d`, a new execution identity, and changed the affected AAPL ref ID to `9039e18c-91c7-561a-813f-de17aa52547f`. That mutation was not promoted or written as the authoritative plan.

## Schema and reconciliation boundary

`schema-validation.json` validates each simulated payload against the previously observed Robinhood metadata: plan-level `account_number`, symbol, valid side/type, exactly one of `quantity`/`dollar_amount`, market-only dollar amount, buy-notional/sell-quantity policy, non-short fractional sell, UUIDv5 `ref_id`, and replace capability `NONE`. All payloads pass. No Robinhood tool was rediscovered or invoked.

Future separately authorized reconciliation authority would be `order.id`, `state`, `cumulative_quantity`, `executions`, and timestamps. Cancellation would require `account_number` and `order_id` and is asynchronous. As replace is unavailable, a material plan change while a prior order state is unknown must fail closed. No remote state was accessed.

## Evidence and state

`D:\AQ_DATA\poc\poc-d-targetportfolio-executionplan\` contains `synthetic-target-portfolio.json`, `execution-plan.json`, `schema-validation.json`, `idempotency-validation.json`, and `evidence-manifest.json` (7,026 bytes, within the 1 MiB cap). No package changed.

```text
OPENBB_CALLED = NO
QLIB_EXECUTED = NO
RDAGENT_EXECUTED = NO
SKFOLIO_EXECUTED = NO
LLM_CALLS = NONE
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
POC_B = PASS
POC_A = PASS
POC_C = PASS
POC_D = PASS
P0_POC_B_LINUX_QLIB_RDAGENT_RUNTIME = PASS
P0_POC_A_OPENBB_LINUX_QLIB_HANDOFF = PASS
P0_POC_C_QLIB_CERTIFICATION_SKFOLIO = PASS
P0_POC_D_TARGETPORTFOLIO_EXECUTIONPLAN = PASS
P0_FUNCTIONAL_POC = COMPLETE
P0 = COMPLETE
CURRENT_NEXT = P1_MINIMAL_QUANT
P1 = NOT_STARTED
```
