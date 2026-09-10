# P0 POC-C Qlib Certification/skfolio 001

**Task:** `AUTONOMOUS-QUANT-P0-POC-C-QLIB-CERTIFICATION-SKFOLIO-001`
**Result:** `POC_C = PASS` (P0 integration-only interface and ownership proof)

## Scope and lineage boundary

This POC proves two strictly separate tracks. POC-B synthetic Qlib artifacts prove Windows Certification can independently read, hash, validate, and materialize a research-artifact handoff. POC-A real OpenBB/yfinance market data alone produces the return matrix consumed by skfolio. No POC-B prediction was joined to a POC-A return, no IC or predictive metric was calculated, no alpha was derived, and no profitability or production-fitness claim is made.

## Certification runtime and package evidence

| Item | Observed value |
|---|---|
| Runtime | `D:\AQ_ENVS\skfolio`, Python `3.12.14` |
| pandas / numpy / skfolio | `3.0.5` / `2.5.3` / `1.0.6` |
| MeanRisk import/API | `skfolio.optimization.MeanRisk`; supports `min_weights`, `max_weights`, and `budget` |
| WalkForward / CPCV | available; `NOT_EXECUTED_SMALL_SAMPLE` |
| pyarrow before | absent |
| Authorized change | `uv pip install --python D:\AQ_ENVS\skfolio\Scripts\python.exe pyarrow==25.0.1` |
| pyarrow after | `25.0.1` |
| Dependency validation | `uv pip check` PASS, 21 packages compatible |
| Other package changes | none; uv resolved and installed one package |

The pre-install snapshot SHA-256 is `eb1fb58ad8c3c4ceb84b5746bae92a3d785558761a45b05d95502245fb11fc29`. The pyarrow installation was the sole package change authorized for this task.

## Track 1 — synthetic POC-B research artifacts

| Item | Result |
|---|---|
| Qlib / source authority | `0.9.8.dev26` / `2fb9380b342556ddb50a4b24e4fe8655d548b2b8` |
| RD-Agent source SHA | `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` |
| `pred.pkl` SHA-256 | `68f844eccd5693f8062b48a8ea0b4c8b244c18e2067c9f5d0eb1e10ddf8812b8` |
| `label.pkl` SHA-256 | `54097ef288d930dfe0ec832c39d7910cf7950f1bf4efe564151432478a79a809` |
| Windows readability | pandas DataFrames, each `24x1` |
| Prediction / label schema | `score` / `LABEL0`; identical `(datetime, instrument)` indexes |
| Index / numeric validation | sorted, unique, compatible, finite values |

`research-artifact-manifest.json` materializes source `POC-B`, `data_kind=synthetic`, source/config/original-manifest hashes, object types/shapes/index dtypes, and the explicit no-cross-dataset lineage boundary. `approved-predictions.parquet` preserves the emitted semantic index and contains only the deterministic certified-for-readability prediction panel.

## Track 2 — real POC-A return matrix and Certification decision

The POC-A market artifact hash was verified as `49090594039da38d39d38156d5921539f6b609fe3a090c5621dcf4f2aeee8d23`. Certification used only its approved `$close` field and computed:

```text
return[t] = close[t] / close[t-1] - 1
pandas pct_change(fill_method=None)
```

The matrix is a strictly increasing, unique `DatetimeIndex × [AAPL, MSFT, SPY]`. Each instrument had exactly one initial NaN from `pct_change`; Certification verified this and dropped only the initial all-NaN row. The resulting `approved-returns.parquet` is `19x3`, has no later NaNs or infinities, and has SHA-256 `40aa707c5bc77ec9361fdade3c0db607c0fa5fb3f4d71e0575013b79edcf31a3`.

Certification owns the deterministic temporal boundary: TRAIN is 14 rows from `2026-08-13` through `2026-09-01`; SEALED_POC_OOS is 5 rows from `2026-09-02` through `2026-09-09`. The sealed rows were not used for fitting and no sealed-row performance was evaluated.

`certification-decision.json` has `status=POC_ACCEPTED`, `scope=P0_INTEGRATION_ONLY`, and `policy_version=P0_POC_C_001`. `production_authorized=false`, `promotion_authorized=false`, and `live_trading_authorized=false`. It is neither `CERTIFIED` nor a production approval.

## skfolio and broker-neutral TargetPortfolio

One and only one MeanRisk fit used the 14x3 TRAIN return matrix, with explicit long-only full-investment settings `min_weights=0.0`, `max_weights=1.0`, and `budget=1.0`. The mapping authority was `feature_names_in_`, which exactly recorded `[AAPL, MSFT, SPY]`; no unlabeled positional mapping was used. The output weights sum to `1.0` within tolerance `1e-8`:

| Asset | Target weight |
|---|---:|
| AAPL | 0.13129883879306606 |
| MSFT | 0.00000013873790244405662 |
| SPY | 0.8687010224690316 |

`target-portfolio.json` is broker-neutral, canonically ordered, and references the Certification decision and approved-return hash. It contains no account, broker, Robinhood, order, quantity, notional, idempotency, or execution field. It is not a trade instruction.

## Evidence and non-actions

`D:\AQ_DATA\poc\poc-c-qlib-certification-skfolio\` contains `research-artifact-manifest.json`, `certification-decision.json`, `approved-predictions.parquet`, `approved-returns.parquet`, `target-portfolio.json`, `evidence-manifest.json`, and pre/post package snapshots. Total output is `12,811` bytes, below the 50 MiB cap.

### Historical state at POC-C completion

```text
QLIB_EXECUTED = NO
RDAGENT_EXECUTED = NO
OPENBB_CALLED = NO
LLM_CALLS = NONE
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
POC_C = PASS
P0_POC_C_QLIB_CERTIFICATION_SKFOLIO = PASS
P0_FUNCTIONAL_POC = IN_PROGRESS
CURRENT_NEXT = P0_POC_D_TARGETPORTFOLIO_EXECUTIONPLAN
P0 = IN_PROGRESS
P1 = NOT_STARTED
```
