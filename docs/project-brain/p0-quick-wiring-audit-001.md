# P0 quick wiring audit 001

**Scope:** eight retained-upstream boundaries only. This is a static/public-runtime interface audit, not a functional POC. No package was installed or upgraded; no upstream source, data, model weight, account, broker, Docker, Conda, or LLM/API call was used.

## Boundary decisions

| BOUNDARY | DIRECT | NATIVE INPUT | NATIVE OUTPUT | GLUE REQUIRED | DECISION |
|---|---|---|---|---|---|
| OpenBB -> Qlib | NO | OpenBB historical-price command returns `OBBject`; `to_df()` returns pandas | Qlib `StaticDataLoader` accepts pandas `DataFrame`; provider-backed Qlib workflows use Qlib storage | THIN_ADAPTER | Convert `OBBject` to pandas; normalize timestamps, instruments, OHLCV/adjustment semantics, then use `StaticDataLoader` or a Qlib provider-format dump. |
| Qlib -> RD-Agent | NO | Windows `pyqlib 0.9.7` runtime | RD-Agent Qlib scenarios call `qlib.init()`/`qrun` in their own workspace | RUNTIME_BRIDGE | RD-Agent assumes Qlib execution beside it: `QlibFBWorkspace` selects `QTDockerEnv` or `QlibCondaEnv`. Existing Windows Qlib is not a directly usable runtime. |
| RD-Agent -> Qlib | NO across runtimes | Qlib factor/model/quant hypothesis and workspace | `factor.py`, `model.py`, Qlib YAML, `combined_factors_df.parquet`, `ret.parquet`, `qlib_res.csv`, logs/workspaces | THIN_ARTIFACT_ADAPTER | These are upstream-native Qlib experiment artifacts when Qlib is co-located; a cross-runtime consumer needs a manifest and file handoff, not Python-object sharing. |
| Qlib -> Certification | YES | Qlib recorder artifacts | pandas `pred.pkl`/`label.pkl`; backtest reports, positions, indicator/risk-analysis DataFrames and recorder metrics | NONE for native artifacts | Certification should receive native Qlib pandas artifacts plus their recorder/provenance reference. |
| Certification -> skfolio | NO | Certified Qlib score/backtest/position evidence | skfolio accepts an `(observations, assets)` pandas/array return matrix; time-aware WalkForward needs `DatetimeIndex` | THIN_ADAPTER | Certification derives an approved, date-indexed return panel with stable asset columns; no wrapper is needed once that native pandas matrix exists. |
| skfolio -> TargetPortfolio | NO | Asset-aligned return matrix | `MeanRisk.weights_`: ndarray shaped `(n_assets,)` (or multi-optimization matrix) | THIN_ADAPTER | Preserve `feature_names_in_`/input-column order when materializing asset-to-weight targets. |
| TargetPortfolio -> Robinhood | NO | `{asset, target_weight}` | No Robinhood MCP schema was exposed to this task | EXECUTION_PLANNER | A broker normally requires executable orders rather than allocation weights. Schema support for client order id/idempotency, fractional or notional orders, and order-status identifiers is **UNVERIFIED**; no authentication or tool call was attempted. |
| TargetPortfolio -> LEAN | NO | `{asset, target_weight}` | LEAN `PortfolioTarget.Percent` / `SetHoldings` and resulting `OrderTicket`s | THIN_EXECUTION_ADAPTER | LEAN maps target percentages after resolving its `Symbol`, security price, buying-power model, lot size, and existing holdings into quantities/orders. |

## RDAGENT_QLIB_RUNTIME_DECISION

**B — co-locate Qlib and RD-Agent inside WSL/Linux for autonomous research.**

This follows upstream behavior, not a platform preference. RD-Agent's Qlib scenario selects Docker or Conda execution, runs `qrun` and `qlib.init()` from a Qlib workspace, and exchanges files such as `combined_factors_df.parquet`, `ret.parquet`, and `qlib_res.csv`. A Windows-Qlib/WSL-RD-Agent bridge would add file, environment, and reproducibility glue around every experiment. Windows should consume only selected research/certification artifacts. No Qlib move, WSL Qlib install, Docker install, or Conda install is authorized by this audit.

## MINIMUM_GLUE_CONTRACTS

1. **MarketDataPanel** — producer: OpenBB normalization; consumer: Qlib. Needed because OpenBB's `OBBject`/provider schemas are not a Qlib provider. Fields: `dataframe_ref`, `datetime_index`, `asset_id`, `fields`, `currency`, `adjustment_policy`, `timezone`, `provider`, `retrieved_at`.
2. **ResearchArtifactManifest** — producer: co-located RD-Agent/Qlib workspace; consumer: Certification/Windows artifact consumer. Needed for the Linux-to-Windows runtime crossing. Fields: `run_id`, `scenario`, `qlib_version`, `rdagent_version`, `code_hashes`, `config_refs`, `data_snapshot_id`, `artifact_refs`, `created_at`.
3. **CertificationDecision** — producer: Certification; consumer: optimizer/portfolio construction. Needed as the security/promotion boundary. Fields: `run_id`, `status`, `approved_assets`, `return_panel_ref`, `evidence_refs`, `policy_version`, `as_of`.
4. **TargetPortfolio** — producer: skfolio mapping; consumer: LEAN adapter or execution planner. Needed to preserve target semantics independent of venue. Fields: `asset`, `target_weight`, `as_of`, `source_run_id`.
5. **ExecutionPlan** — producer: execution planner; consumer: Robinhood MCP only after a separately authorized interface/auth POC. Needed because target weights are not executable orders. Fields: `execution_id`, `client_order_id`, `asset`, `side`, `quantity_or_notional`, `order_type`, `limit_price`, `time_in_force`, `target_weight`, `source_run_id`.

No custom wrapper is recommended for native pandas objects within a single runtime: Qlib recorder artifacts and the Certification-to-skfolio return matrix should remain pandas.

## CRITICAL_BLOCKERS

- **Robinhood MCP schema is not exposed in this task context.** Its order request/response fields, idempotency support, fractional/notional support, and status identifier remain unverified. `AUTH_BOUNDARY = NOT_TESTED`; no account authentication, data access, or tool invocation occurred.
- **RD-Agent's Qlib runtime is not yet provisioned.** Its upstream execution path requires Linux Qlib through Docker or Conda; this audit neither installed nor configured either. This is a functional-POC staging prerequisite, not a reason to retain a Windows/WSL direct runtime bridge.

## NEXT_ACTION

`P0_INTERFACE_BLOCKER_RESOLUTION`: expose the Robinhood MCP tool schema without account access, then record the permitted order-planning mapping. A later separately authorized functional POC can stage Qlib beside RD-Agent in WSL/Linux using the upstream-supported execution environment.

```text
P0 = IN_PROGRESS
P0_INTERFACE_AUDIT = COMPLETE_WITH_BLOCKERS
CURRENT_NEXT = P0_INTERFACE_BLOCKER_RESOLUTION
P1 = NOT_STARTED
```
