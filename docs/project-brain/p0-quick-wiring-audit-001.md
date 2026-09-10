# P0 quick wiring audit 001

**Scope:** eight retained-upstream boundaries only. This is a static/public-runtime interface audit, not a functional POC. No package was installed or upgraded; no upstream source, data, model weight, account, broker, Docker, Conda, or LLM/API call was used.

## Boundary decisions

| BOUNDARY | DIRECT | NATIVE INPUT | NATIVE OUTPUT | GLUE REQUIRED | DECISION |
|---|---|---|---|---|---|
| OpenBB -> Qlib | NO | OpenBB historical-price command returns `OBBject`; `to_df()` returns pandas | Qlib `StaticDataLoader` accepts pandas `DataFrame`; provider-backed Qlib workflows use Qlib storage | THIN_ADAPTER | Convert `OBBject` to pandas; normalize timestamps, instruments, OHLCV/adjustment semantics, then use `StaticDataLoader` or a Qlib provider-format dump. |
| Qlib -> RD-Agent | YES within selected research runtime | Co-located Linux Qlib runtime | RD-Agent Qlib scenarios call `qlib.init()`/`qrun` in their own workspace | NONE | `RUNTIME_COLOCATION` is required: `QlibFBWorkspace` selects `QTDockerEnv` or `QlibCondaEnv`. The existing Windows Qlib runtime is not used by RD-Agent. |
| RD-Agent -> Qlib | NO across runtimes | Qlib factor/model/quant hypothesis and workspace | `factor.py`, `model.py`, Qlib YAML, `combined_factors_df.parquet`, `ret.parquet`, `qlib_res.csv`, logs/workspaces | THIN_ARTIFACT_ADAPTER | These are upstream-native Qlib experiment artifacts when Qlib is co-located; a cross-runtime consumer needs a manifest and file handoff, not Python-object sharing. |
| Qlib -> Certification | YES | Qlib recorder artifacts | pandas `pred.pkl`/`label.pkl`; backtest reports, positions, indicator/risk-analysis DataFrames and recorder metrics | NONE for native artifacts | Certification should receive native Qlib pandas artifacts plus their recorder/provenance reference. |
| Certification -> skfolio | NO | Certified Qlib score/backtest/position evidence | skfolio accepts an `(observations, assets)` pandas/array return matrix; time-aware WalkForward needs `DatetimeIndex` | THIN_ADAPTER | Certification derives an approved, date-indexed return panel with stable asset columns; no wrapper is needed once that native pandas matrix exists. |
| skfolio -> TargetPortfolio | NO | Asset-aligned return matrix | `MeanRisk.weights_`: ndarray shaped `(n_assets,)` (or multi-optimization matrix) | THIN_ADAPTER | Preserve `feature_names_in_`/input-column order when materializing asset-to-weight targets. |
| TargetPortfolio -> Robinhood | NO | `{asset, target_weight}` | `place_equity_order` requires an executable order intent | EXECUTION_PLANNER | `account_number`, `symbol`, `side`, `type`, and exactly one of `quantity`/`dollar_amount`; optional price, session, TIF, tax lots, and idempotency `ref_id`. |
| TargetPortfolio -> LEAN | NO | `{asset, target_weight}` | LEAN `PortfolioTarget.Percent` / `SetHoldings` and resulting `OrderTicket`s | THIN_EXECUTION_ADAPTER | LEAN maps target percentages after resolving its `Symbol`, security price, buying-power model, lot size, and existing holdings into quantities/orders. |

## RDAGENT_QLIB_RUNTIME_DECISION

**B — co-locate Qlib and RD-Agent inside WSL/Linux for autonomous research.**

This follows upstream behavior, not a platform preference. RD-Agent's Qlib scenario selects Docker or Conda execution, runs `qrun` and `qlib.init()` from a Qlib workspace, and exchanges files such as `combined_factors_df.parquet`, `ret.parquet`, and `qlib_res.csv`. A Windows-Qlib/WSL-RD-Agent bridge would add file, environment, and reproducibility glue around every experiment. Windows should consume only selected research/certification artifacts. No Qlib move, WSL Qlib install, Docker install, or Conda install is authorized by this audit.

## Robinhood MCP schema discovery

OAuth-authenticated MCP metadata discovery completed without invoking a business tool, reading account data, or supplying any business-tool argument values.

- **Market data:** `get_equity_quotes`, `get_equity_price_book`, `get_equity_historicals`, `get_equity_fundamentals`, `get_equity_tradability`.
- **Account/positions/order-status capabilities (discovered, not invoked):** `get_accounts`, `get_equity_positions`, `get_equity_orders`.
- **Equity order/cancel capabilities (discovered, not invoked):** `place_equity_order`, `cancel_equity_order`. No equity replace-order tool is exposed.
- **Equity order input schema:** required `account_number`, `symbol`, `side` (`buy`/`sell`), and `type` (`market`, `limit`, `stop_market`, `stop_limit`); exactly one of `quantity` or market-only USD `dollar_amount`; `limit_price` for limit/stop-limit, `stop_price` for stop variants, optional `market_hours`, `time_in_force` (`gfd`/`gtc`), sell-only `tax_lots`, and UUID `ref_id`.
- **Fractional/notional behavior:** decimal fractional `quantity` is supported only for eligible-account market orders during regular hours (up to six decimals; no fractional short sales). `dollar_amount` is supported only for market orders. Both are regular-hours-only.
- **Idempotency:** `ref_id` is a client-supplied UUID. The same `ref_id` must be reused for a retry of the same logical order; the upstream deduplicates it. The exposed order-result schema does not echo `ref_id`.
- **Equity order result schema:** `order.id`, `symbol`, `side`, `state`, `quantity`, `dollar_based_amount`, `cumulative_quantity`, `average_price`, `price`, `stop_price`, `time_in_force`, `market_hours`, `created_at`, `last_transaction_at`, `executions[]`, `fees`, and optional `reject_reason`. States include `new`, `queued`, `unconfirmed`, `partially_filled`, `filled`, `cancelled`, `rejected`, `failed`, `voided`, `pending_cancelled`, and `partially_filled_rest_cancelled`.
- **Cancel schema:** `cancel_equity_order` requires `account_number` and `order_id`, returning `accepted`; cancellation is asynchronous. **Replace:** no exposed equity replace capability.

```text
TARGET_WEIGHT_ACCEPTED_DIRECTLY = NO
EXECUTION_PLANNER_REQUIRED = YES
IDEMPOTENCY_SUPPORTED = YES (ref_id)
FRACTIONAL_SUPPORTED_BY_SCHEMA = YES (market + regular_hours constraints)
NOTIONAL_SUPPORTED_BY_SCHEMA = YES (market-only dollar_amount)
ORDER_STATUS_ID_AVAILABLE = YES (order.id + state)
CANCEL_AVAILABLE = YES
REPLACE_AVAILABLE = NO
```

## MINIMUM_GLUE_CONTRACTS

1. **MarketDataPanel** — producer: OpenBB normalization; consumer: Qlib. Needed because OpenBB's `OBBject`/provider schemas are not a Qlib provider. Fields: `dataframe_ref`, `datetime_index`, `asset_id`, `fields`, `currency`, `adjustment_policy`, `timezone`, `provider`, `retrieved_at`.
2. **ResearchArtifactManifest** — producer: co-located RD-Agent/Qlib workspace; consumer: Certification/Windows artifact consumer. Needed for the Linux-to-Windows runtime crossing. Fields: `run_id`, `scenario`, `qlib_version`, `rdagent_version`, `code_hashes`, `config_refs`, `data_snapshot_id`, `artifact_refs`, `created_at`.
3. **CertificationDecision** — producer: Certification; consumer: optimizer/portfolio construction. Needed as the security/promotion boundary. Fields: `run_id`, `status`, `approved_assets`, `return_panel_ref`, `evidence_refs`, `policy_version`, `as_of`.
4. **TargetPortfolio** — producer: skfolio mapping; consumer: LEAN adapter or execution planner. Needed to preserve target semantics independent of venue. Fields: `asset`, `target_weight`, `as_of`, `source_run_id`.
5. **ExecutionPlan** — producer: execution planner; consumer: Robinhood MCP only after a separately authorized functional POC. Needed because target weights are not executable orders. Fields: `execution_id`, `account_number`, `ref_id`, `asset`, `side`, `quantity_or_notional`, `order_type`, `limit_price`, `stop_price`, `market_hours`, `time_in_force`, `target_weight`, `source_run_id`.

No custom wrapper is recommended for native pandas objects within a single runtime: Qlib recorder artifacts and the Certification-to-skfolio return matrix should remain pandas.

## CRITICAL_BLOCKERS

No remaining **interface-schema** blocker. RD-Agent's Qlib runtime remains a separately authorized functional-POC staging prerequisite: its upstream execution path requires Linux Qlib through Docker or Conda, neither of which this audit installed or configured.

## NEXT_ACTION

`P0_FUNCTIONAL_POC_DESIGN`: design separately authorized, bounded POCs for the co-located Linux Qlib/RD-Agent runtime and the execution planner. No Robinhood account-data or order-tool call is authorized by this schema audit.

### Historical status at quick-wiring-audit completion

```text
P0 = IN_PROGRESS
P0_INTERFACE_AUDIT = COMPLETE
CURRENT_NEXT = P0_FUNCTIONAL_POC_DESIGN
P1 = NOT_STARTED
```
