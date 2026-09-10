# P0 functional POC design 001

**Task:** `AUTONOMOUS-QUANT-P0-FUNCTIONAL-POC-DESIGN-001`
**Scope:** executable POC design and source/runtime inspection only. This document authorizes no installation, data access, LLM call, account access, order action, or P1 work.

## 1. Objective

Prove the selected P0 topology with four intentionally small, disposable POCs. P0 proves integration boundaries and replaceability, not profitability, production readiness, paper trading, or an autonomous research loop.

## 2. Final runtime topology

```text
Windows: OpenBB -> normalized Parquet -> D:\AQ_DATA\poc\...
                                               |
                                               | file/artifact handoff only
                                               v
WSL: /mnt/d/AQ_DATA/poc/... -> Linux Qlib + RD-Agent workspace
                                               |
                                               v
Windows Certification -> skfolio -> TargetPortfolio -> ExecutionPlan (local only)
```

Windows Qlib is not a consumer in the final topology. There is no RPC, shared Python process, or custom Windows-Qlib/WSL-RD-Agent bridge.

## 3. POC-B — Linux Qlib and RD-Agent runtime

### Selected environment and evidence

**Selected path: `QlibCondaEnv` (A).** The checked-out RD-Agent source at `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` defaults `ModelCoSTEERSettings.env_type` to `conda`. Its `QlibFBWorkspace` selects `QlibCondaEnv` for that value and executes `qrun conf.yaml`, then `python read_exp_res.py`.

`QlibCondaEnv` specifies environment name `rdagent4qlib`, Python 3.10, Qlib commit `2fb9380b342556ddb50a4b24e4fe8655d548b2b8`, and Qlib runtime dependencies including CatBoost, XGBoost, Tables, and Torch. It is the selected upstream-supported path even though Conda is not presently installed.

`QTDockerEnv` is rejected for this initial POC: its current `prepare()` method pulls an image and automatically downloads Qlib China daily data when absent. That is incompatible with the intentionally tiny, no-dataset POC boundary and adds Docker/WSL maintenance overhead.

### Exact layout and configuration

| Role | Location / value |
|---|---|
| RD-Agent source | `/home/zhou/AQ_UPSTREAM/rd-agent` |
| Existing RD-Agent control environment | `/home/zhou/AQ_ENVS/rdagent` (Python 3.11.16; remains separate) |
| Selected Qlib execution environment | Conda environment name `rdagent4qlib`, Python 3.10; its resolved Conda prefix must be recorded in the manifest at execution time |
| Disposable workspace | `/home/zhou/AQ_WORKSPACES/p0-poc-b-qlib-rdagent` |
| Windows evidence handoff | `D:\AQ_DATA\poc\poc-b-qlib-rdagent\` / `/mnt/d/AQ_DATA/poc/poc-b-qlib-rdagent/` |
| RD-Agent selection | scoped run configuration whose evaluated `MODEL_COSTEER_SETTINGS.env_type` is `conda`; no global PATH or `.env` change |

The existing RD-Agent environment runs the control code only. `QlibCondaEnv` owns Qlib execution; it is not replaced by, and does not mutate, `/home/zhou/AQ_ENVS/rdagent`.

### Minimum future execution

After separate authorization to install Conda and provision only this environment, create a disposable 3-symbol, 20-session synthetic OHLCV fixture in the workspace. Use the RD-Agent `QlibCondaEnv` path directly (not an RD-Agent loop) to run one tiny Qlib `qrun` workflow with a fixed native factor/model configuration. It must produce `pred.pkl`, `label.pkl`, recorder metadata, and a short result summary. No LLM, hypothesis generation, search, training sweep, or downloaded Qlib dataset is allowed.

Expected lineage is `conf.yaml`, fixture hash, Qlib/RD-Agent versions, command log, recorder reference, `pred.pkl`, `label.pkl`, `qlib_res.csv` and, if the upstream workspace template emits it, `ret.parquet`. `factor.py` and `model.py` are included only if the fixed fixture workflow needs them; they are never agent-generated in this POC. The `ResearchArtifactManifest` also records the resolved Conda prefix and a complete package snapshot/freeze, including the exact resolved versions of upstream-unpinned CatBoost, XGBoost, Tables, and Torch.

`QlibCondaEnv.prepare()` catches installation exceptions without re-raising, so its return is not provisioning evidence. **PASS** requires all of the following independent, fail-closed checks after `prepare()`:

1. `conda env list` contains exactly the intended `rdagent4qlib` environment and the resolved prefix is recorded.
2. `conda run -n rdagent4qlib python --version` reports Python 3.10.
3. `conda run -n rdagent4qlib python -c "import qlib"` succeeds.
4. Installed Qlib provenance resolves to RD-Agent's pinned commit `2fb9380b342556ddb50a4b24e4fe8655d548b2b8`.
5. `conda run -n rdagent4qlib qrun --help` and `conda run -n rdagent4qlib pip check` both succeed.
6. The fixed `qrun` completes; expected artifacts, package snapshot, and manifest are present; RD-Agent and Qlib remain co-located.

**FAIL:** any independent verification fails, provenance cannot be resolved to the pinned commit, the configuration requires a downloaded provider dataset, `qrun` fails, expected artifacts are missing, or any unapproved network/LLM action is attempted.
**Rollback:** stop the foreground command, preserve logs/manifest, remove only the named disposable workspace and the named `rdagent4qlib` environment after recording its resolved prefix. Do not touch `/home/zhou/AQ_ENVS/rdagent` or upstream source.

## 4. POC-A — Windows OpenBB to Linux Qlib

### Data route

The installed Windows environment contains OpenBB `4.7.2` and `openbb-yfinance 1.6.3`. Its registered yfinance provider has `EquityHistorical` support, daily `1d` interval, `include_actions`, and declared `splits_only` / `splits_and_dividends` adjustment modes. It is the credential-free candidate for the future POC; no provider request was made in this task.

The future POC obtains only AAPL, MSFT, and SPY daily bars for 20 completed US sessions with explicit yfinance request parameters `adjustment="splits_only"` and `include_actions=true`. It calls `OBBject.to_df()`, normalizes once on Windows, and writes one Parquet artifact plus sidecar metadata to `D:\AQ_DATA\poc\poc-a-openbb-qlib\market_data.parquet`. Linux reads exactly `/mnt/d/AQ_DATA/poc/poc-a-openbb-qlib/market_data.parquet`.

OpenBB must run with an explicitly pre-existing isolated settings/cache home under `D:\AQ_CACHE\openbb-home`; the standard user-profile default is not an approved artifact location.

### Normalization contract

| Field | Rule |
|---|---|
| `symbol` | uppercase canonical ticker: `AAPL`, `MSFT`, `SPY` |
| `datetime` | timezone-aware source timestamp converted to `America/New_York`, then stored as the completed exchange **session date** with no intraday rows |
| OHLCV | numeric `open`, `high`, `low`, `close`, non-negative `volume`; reject duplicate `(datetime, symbol)` |
| adjusted close | request and require `adjustment="splits_only"`; preserve provider `close` as delivered and do not silently substitute an adjusted series |
| actions | request and require `include_actions=true`; retain split/dividend columns when returned |
| currency | `USD`, otherwise fail |
| provenance | provider `yfinance`, OpenBB/version, exact request `adjustment="splits_only"` and `include_actions=true`, demonstrated response semantics/metadata, UTC retrieval timestamp, artifact SHA-256 |

The artifact uses a sorted pandas MultiIndex `(datetime, instrument)` where `datetime` is a naive session-date timestamp after the timezone/session conversion and `instrument` is the canonical symbol. Columns use Qlib-compatible field groups, at minimum `feature` (`$open`, `$high`, `$low`, `$close`, `$volume`) plus a separately declared label only when a later POC computes one.

**Selected Qlib ingress: `StaticDataLoader` from normalized pandas/Parquet.** Qlib `0.9.7` accepts a pandas `DataFrame` or Parquet path directly. Native provider/storage conversion is deferred because it would build a warehouse rather than prove the final file handoff.

**PASS:** one bounded, credential-free response normalizes to the stated schema; the hash/sidecar records the exact adjustment/action request and demonstrated response semantics; Linux reads the same bytes; `StaticDataLoader` loads and filters all three instruments.

**FAIL:** unavailable provider, credentials required, missing/invalid fields, duplicate dates, non-USD data, unreadable Linux path, or adjustment/action semantics that cannot be demonstrated from request/result metadata.
**Rollback:** delete only `D:\AQ_DATA\poc\poc-a-openbb-qlib\` after preserving the failure metadata; no provider cache is promoted.

## 5. POC-C — Qlib to Certification to skfolio

```text
Linux Qlib recorder artifacts + ResearchArtifactManifest
    -> Windows Certification
    -> approved pandas return/prediction panel
    -> skfolio MeanRisk
    -> asset-aligned weights
    -> broker-neutral TargetPortfolio
```

Certification reads native Qlib `pred.pkl`, `label.pkl`, recorder/workflow metadata, configuration hash, and relevant result/backtest evidence from the file handoff. It owns temporal integrity, leakage checks, sealed OOS partitioning, multiple-testing ledger, and the acceptance/rejection decision. skfolio never owns promotion authority.

The minimum Certification output is two pandas objects:

- a score/prediction panel indexed by `(datetime, instrument)` with one numeric score column; and
- an approved return matrix indexed by strictly increasing, unique `DatetimeIndex` session dates with columns exactly `[AAPL, MSFT, SPY]` in recorded order.

Certification calculates returns from the approved close convention and records the formula; it does not let skfolio infer returns from predictions. It rejects duplicate dates/assets, look-ahead alignment, non-finite values, insufficient observations, or a column-order mismatch. The initial NaN policy is fail-closed: reject rather than fill, except an explicitly documented first-return row may be dropped before the sealed split.

For the first tiny POC, run no optimizer in this task. The future execution may use `WalkForward` only when the small panel has enough observations for a declared train/test split; `CombinatorialPurgedCV` is deferred unless the date count supports a meaningful purge/embargo configuration. `MeanRisk` is the single initial optimizer. Its `weights_` ndarray is mapped by `feature_names_in_` / the recorded return-matrix column order, never by positional assumption alone.

The resulting `TargetPortfolio` is a sorted asset-to-target-weight set whose approved risky weights satisfy the explicit budget and whose source points to the `CertificationDecision`. It contains no broker fields.

**PASS:** Qlib artifacts load on Windows; Certification emits the approved panels and decision; skfolio consumes the `(observations, assets)` return matrix and yields finite, asset-mapped weights; the TargetPortfolio can be reproduced from evidence.

**FAIL:** artifact/provenance gap, temporal or NaN failure, panel/weight-order mismatch, optimizer failure, or a certification rejection.
**Rollback:** remove only POC-C copied artifacts and generated local reports; retain failure metadata and do not alter the Qlib recorder source artifacts.

## 6. POC-D — TargetPortfolio to ExecutionPlan

This is deterministic local planning and schema validation only. It does not invoke any Robinhood MCP tool.

### Synthetic fixture

| Item | Value |
|---|---|
| Account identifier | `RH_ACCOUNT_PLACEHOLDER` only |
| Account equity | $1,000 |
| Buying power | $750 |
| Cash reserve | 10% ($100) |
| Reference prices | AAPL $100; MSFT $200; SPY $500 |
| Current positions | AAPL 1; MSFT 0; SPY 1 |
| TargetPortfolio | AAPL 40%; MSFT 30%; SPY 20%; cash 10% |

Target dollars are $400, $300, and $200; current dollars are $100, $0, and $500; deltas are +$300 AAPL, +$300 MSFT, and -$300 SPY. The policy uses market/regular-hours `dollar_amount` for permitted buys and `quantity` for a sell; the synthetic SPY sell is `0.6` shares and cannot create a short position.

### Deterministic planner rules

- Use `target_dollars = account_equity * target_weight`; current dollars use the synthetic reference price; delta determines side.
- Reject a plan below a $5 absolute delta, a price older than five minutes, non-positive/unknown price, non-USD instrument, unsupported side/type/session, or insufficient buying power after reserve. Planned sell proceeds must not be counted as available buying power; only a later confirmed broker/account-state snapshot may increase spendable buying power.
- Buy notional is allowed only for market/regular-hours orders. Fractional quantities are allowed only where the verified schema permits them; sell quantity is rounded down to six decimals and never exceeds the current position.
- Canonicalize and sort the TargetPortfolio before hashing. A duplicate canonical target/state snapshot produces no new plan.
- Generate `ref_id` as a deterministic UUIDv5 from the plan snapshot, symbol, side, and canonical order fields. Reuse that same UUID only for retrying that exact logical order; any material state/target change creates a new logical order and UUID.
- `ExecutionPlan` is local output only. Its schema check requires `account_number`, `symbol`, `side`, `type`, and exactly one of `quantity`/`dollar_amount`; it validates price, time-in-force, session, and tax-lot rules without calling the broker.
- Future reconciliation treats `order.id`, `state`, cumulative quantity, executions, and timestamps as the authority after a separately authorized order-status capability. A cancellation is only a future, separately authorized request using account number and order ID. There is no replace capability: a changed plan fails closed until prior-order state is known.

**PASS:** the synthetic fixture produces a deterministic, schema-valid local plan; no account or MCP call occurs; TargetPortfolio remains broker-neutral.

**FAIL:** a required field or invariant fails, duplicate handling is non-deterministic, a trade violates cash/price/fractional rules, or a broker field appears in TargetPortfolio.
**Rollback:** delete only synthetic plan files; no remote state exists.

## 7. Final glue contracts

Exactly five custom contracts remain. Native pandas and Qlib recorder objects stay native within one runtime.

| Classification | Name | Owner / producer -> consumer | Minimum fields | Serialization | Why native object is insufficient |
|---|---|---|---|---|---|
| KEEP | `MarketDataPanel` | Data normalization: OpenBB -> Linux Qlib | artifact ref/hash, symbols, session range, field map, currency, adjustment policy, provider, retrieved_at | Parquet + JSON sidecar | OBBject/provider metadata is neither cross-runtime nor Qlib-native. |
| KEEP | `ResearchArtifactManifest` | Research: Linux Qlib/RD-Agent -> Certification | run_id, scenario, source/version hashes, Qlib env prefix, config/fixture/data hashes, artifact refs, created_at | JSON | Raw files do not establish provenance or a runtime crossing. |
| KEEP | `CertificationDecision` | Certification -> Portfolio | run_id, status, approved assets, panel refs/hashes, evidence refs, policy version, as_of | JSON | A DataFrame cannot express independent acceptance or promotion authority. |
| KEEP | `TargetPortfolio` | Portfolio -> execution planner | asset, target_weight, as_of, source_run_id, decision_ref | JSON | `weights_` has positional semantics and lacks portfolio provenance. |
| KEEP | `ExecutionPlan` | Execution planner -> Robinhood adapter | execution_id, account placeholder/ref, ref_id, symbol, side, one quantity/notional, type, prices, session, TIF, source_run_id | JSON | Broker fields and idempotency must not cross into TargetPortfolio. |

## 8. Ownership boundaries

OpenBB owns provider access; Qlib/RD-Agent own research execution and native artifacts; Certification owns validity and promotion decisions; skfolio supplies splitters/optimization only; the portfolio layer owns target weights; the execution planner owns broker mapping and fails closed. Robinhood remains uncalled until a separate authorization explicitly permits a broker-functional POC.

## 9. Resource budgets

| Future POC | Time | Disk | Network | LLM calls | Symbols / date range | Artifact cap |
|---|---:|---:|---:|---:|---|---:|
| B | 30 min | 6 GiB | 4 GiB dependency provision only; 0 market data | 0 | 3 / 20 synthetic sessions | 20 |
| A | 10 min | 25 MiB | 50 MiB | 0 | AAPL, MSFT, SPY / 20 completed sessions | 4 |
| C | 10 min | 50 MiB | 0 | 0 | 3 / same approved sessions | 12 |
| D | 5 min | 1 MiB | 0 | 0 | 3 / one synthetic as-of snapshot | 3 |

Exceeding any cap stops that POC and records a failure; it does not authorize expansion.

## 10. Execution order

1. `P0_POC_B_LINUX_QLIB_RDAGENT_RUNTIME_EXECUTION`
2. `P0_POC_A_OPENBB_LINUX_QLIB_HANDOFF`
3. `P0_POC_C_QLIB_CERTIFICATION_SKFOLIO`
4. `P0_POC_D_TARGETPORTFOLIO_EXECUTIONPLAN`

This order is required because POC-A's final consumer is Linux Qlib, which must be staged by POC-B first. POC-C consumes real POC-A/B artifacts. POC-D is deliberately last because it receives only an approved, broker-neutral TargetPortfolio.

## 11. P0 exit criteria

P0 may be marked complete only when evidence shows that all four POCs passed within their caps: the selected Linux runtime executed, tiny real market data crossed the stated file boundary, Qlib artifacts reached independent Certification, skfolio produced asset-mapped weights, a broker-neutral TargetPortfolio and deterministic local ExecutionPlan were produced, and every component remained replaceable. P0 does not require alpha quality, a full universe, long history, LEAN/FinRL-X work, paper/live trading, or any Robinhood tool call.

## 12. Rollback strategy

Every execution POC uses a uniquely named disposable workspace or `D:\AQ_DATA\poc\poc-<letter>-...` artifact directory. On failure, stop foreground work, hash and retain only the manifest/log required for evidence, then delete only that named workspace/environment/artifact directory after the exact path is verified. No upstream checkout, existing RD-Agent environment, OpenBB settings cache, global PATH, service, scheduled task, or account state is modified.

## 13. First executable task

`P0_POC_B_LINUX_QLIB_RDAGENT_RUNTIME_EXECUTION` is the first task. It requires a new, explicit authorization for Conda installation and isolated `rdagent4qlib` provisioning. Until then the design is complete but execution is blocked by the intentionally uninstalled upstream runtime prerequisite.

### Historical status at POC design completion

```text
P0 = IN_PROGRESS
P0_INTERFACE_AUDIT = COMPLETE
P0_FUNCTIONAL_POC_DESIGN = COMPLETE
CURRENT_NEXT = P0_POC_B_LINUX_QLIB_RDAGENT_RUNTIME_EXECUTION
P1 = NOT_STARTED
```
