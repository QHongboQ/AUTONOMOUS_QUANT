# P1 Certification Upstream Gap Audit 001

**Task:** `AUTONOMOUS-QUANT-P1-CERTIFICATION-UPSTREAM-GAP-AUDIT-001`
**Scope:** bounded upstream audit only, performed 2026-09-10. This is a P1 entry prerequisite and makes no implementation, installation, model-training, data-provider, Qlib, RD-Agent, broker, account, or trading authorization.

## Decision boundary

P0 is complete. P1 Minimal Quant remains **not started** and `CURRENT_NEXT` remains `P1_MINIMAL_QUANT`. This audit does not create P2 Certification and does not transfer any authority to an upstream package.

Project-owned authority remains non-delegable: sealed-OOS access and ledger, trial-ledger semantics, pre-registration and policy hashes, CertificationDecision, promotion, and Champion/Challenger lifecycle. Every selected upstream below is only a deterministic evidence producer operating on versioned inputs and returning evidence artifacts.

## Existing skfolio ownership — retain, do not duplicate

The installed isolated runtime is skfolio `1.0.6`; a read-only import confirmed `WalkForward` and `CombinatorialPurgedCV` are available. skfolio owns WalkForward, CombinatorialPurgedCV, purging/embargo mechanics, cross-validation helpers, and portfolio/risk tooling. It is the project’s temporal-split owner, but does not own sealed-OOS authority, trial accounting, or promotion.

No candidate below replaces skfolio’s CV/purging role. In particular, MLFinLab/mlfinpy-style PurgedKFold functionality would duplicate the retained skfolio leaf.

## Candidate findings

| Upstream | Relevant capability and accepted input | Maintenance / license / compatibility | Overlap and state behavior | Decision / target phase |
|---|---|---|---|---|
| [skfolio/skfolio](https://github.com/skfolio/skfolio) | WalkForward, CombinatorialPurgedCV, purging/embargo, portfolio/risk tools; date-indexed returns and declared splits | Existing `1.0.6`; retained isolated Windows runtime | Owns temporal CV; does not own multiple-testing or promotion. Operates as an evidence producer when input/split hashes are recorded. | **KEEP** — P1/P2 temporal integrity |
| [bashtage/arch](https://github.com/bashtage/arch) / [bootstrap docs](https://bashtage.github.io/arch/8.0.0/multiple-comparison/multiple-comparison_examples.html) | `SPA` / `RealityCheck`, `StepM`, `MCS`, `IIDBootstrap`, `MovingBlockBootstrap`, `StationaryBootstrap`; benchmark loss vector plus model-loss matrix (`t × k`, lower loss better) | Active public repository; release `8.0.0` (2025-10-21), public activity 2026-08-10. Repository metadata reports non-SPDX `Other/NOASSERTION`, so exact license text must be pinned and legal-reviewed before installation. Modern CPython scientific package; Windows target compatibility must be confirmed against the selected release wheel. | Directly fills multiple-model comparison gap; no material skfolio/Qlib overlap. Objects have configurable bootstrap RNG state, so task code must seed and record state; results are otherwise pure evidence. | **ADD** — `40-certification-system/multiple-testing-control`, separately authorized installation only |
| [stefan-jansen/alphalens-reloaded](https://github.com/stefan-jansen/alphalens-reloaded) / [API](https://alphalens.ml4trading.io/api-reference.html) | IC / mean IC, quantile returns, forward-return construction, turnover, rank autocorrelation, horizon/decay analysis; requires factor panel plus raw price panel (and optional groups) | Apache-2.0; release `0.4.5` (2025-07-23), public activity 2025-12-15. Documented dependencies: NumPy, pandas, SciPy, statsmodels, matplotlib, seaborn; ordinary Windows Python is feasible but increases visualization/scientific dependency footprint. | Qlib already emits native score/prediction artifacts and basic IC-style research evidence; Alphalens adds standardized factor-panel diagnostics, not authority. Its utilities create derived frames but do not mutate source panels if copied/hashed at the boundary. | **DEFER** — add only if the first registered P1 factor family needs diagnostics Qlib evidence cannot provide; do not add for reports/plots alone |
| [deepcharles/ruptures](https://github.com/deepcharles/ruptures) / [docs](https://dev.ipol.im/~truong/ruptures-docs/build/html/index.html) | Offline change-point segmentation: `Pelt`, `Binseg`, `Dynp`, `BottomUp`, `Window`, kernel/cost models; accepts univariate or multivariate ordered market-state feature arrays | BSD-2-Clause; release `1.1.10` (2025-09-10), public activity 2026-07-06. NumPy/SciPy-oriented dependency cost; deterministic once input, model, penalty, and any seed are recorded; Windows-compatible Python package subject to selected-wheel verification. | No skfolio CV or Qlib recorder replacement. Adds interpretable segmentation evidence beyond manually declared stress windows, but does not itself select a regime or change trading behavior. | **DEFER** — optional `40-certification-system/regime-stress` evidence after P1 baseline |
| [online-ml/river](https://github.com/online-ml/river) / [drift APIs](https://riverml.xyz/latest/api/drift/) | Online statistics and drift detectors including ADWIN, Page-Hinkley, KSWIN and incremental monitoring; accepts ordered streaming residual/loss/feature observations | BSD-3-Clause; release `0.26.1` (2026-08-21), public activity 2026-09-03. Broader incremental-ML dependency and operational state; Windows support must be pinned/verified at adoption. | No overlap with skfolio’s offline CV. Detector state mutates per observation, so snapshots/reset/seed semantics would be mandatory; it must never become an autonomous trading switch. | **DEFER** — later Shadow / Production Operations, not P1/P2 |
| [Hudson & Thames MLFinLab](https://github.com/hudson-and-thames/mlfinlab) | Advertises backtest-overfitting tools, CV, and broader financial-ML toolbox | Public-facing issue tracker is explicitly all-rights-reserved/commercial; repository activity is stale (2023-10-02), and source availability is not a free upstream adoption path. | Broadly overlaps skfolio CV and would create commercial/vendor lock-in. | **REJECT** — no free upstream adoption |
| [esvhd/pypbo](https://github.com/esvhd/pypbo) | CSCV/PBO, PSR, MinTRL/MinBTL, DSR reference implementation | AGPL-3.0; small standalone reference project. It is useful for paper/reference vectors, but is not selected as a project dependency because of copyleft licensing, narrow maintenance assurance, and its own metric conventions. | No authority role; input is a return/performance matrix. | **REJECT AS DEPENDENCY** — reference only |
| [vectorbt DSR API](https://vectorbt.dev/api/returns/metrics/) | `deflated_sharpe_ratio(est_sharpe, var_sharpe, nb_trials, backtest_horizon, skew, kurtosis)` | Current documentation exposes a usable DSR formula, but VectorBT is Apache-2.0 with Commons Clause / fair-code terms and is a broad backtesting stack. | Adds DSR only while duplicating broader analytics/backtesting and introducing license/lock-in cost. | **REJECT AS DEPENDENCY** — formula/reference only |

`arch` documentation explicitly identifies SPA (also accessible as RealityCheck), StepM, and MCS as multiple-comparison procedures and specifies benchmark/model **loss** inputs. Therefore it can consume versioned model-loss or strategy-return-derived loss matrices without deciding what a model may promote. The project must supply the matrix, benchmark definition, bootstrap configuration, RNG state, and interpretation policy; `arch` supplies the statistical evidence only.

Alphalens-reloaded directly supports the requested factor diagnostics: forward-return construction, Spearman rank IC, mean return by quantile, quantile turnover, and factor-rank autocorrelation. That is genuine diagnostic value, but P1 starts with a small registered baseline and Qlib’s existing recorder/prediction evidence. The extra visualization/analysis stack is not justified until a documented gap appears.

Ruptures is explicitly an offline change-point package, suitable for a bounded post-hoc segmentation of predeclared market-state features. Its output is evidence only; regime labels cannot directly switch allocation, model selection, or execution. River is purpose-built for mutable online monitoring and belongs after the offline research/certification boundary is mature.

## DSR, PBO, Haircut Sharpe, and MinTRL conclusion

No mature, permissively licensed, narrowly scoped, maintained free upstream was established in this bounded audit for the **complete** DSR + CSCV/PBO + Haircut Sharpe set. MLFinLab is commercial; pypbo is a useful AGPL reference rather than an adoptable dependency; VectorBT implements DSR but is an unnecessarily broad, fair-code-licensed dependency. Newly published small repositories were not selected solely to avoid a small implementation.

**Decision: `THIN_VERIFIED_IMPLEMENTATION_REQUIRED`.** This is not P2 implementation authorization. When separately authorized, the only permissible self-build scope is:

1. A pure DSR evidence function based on the published Bailey/López de Prado formula and reference vectors, consuming recorded Sharpe, trial count/distribution variance, horizon, skew, and kurtosis.
2. A pure CSCV/PBO evidence function based on the published PBO procedure, consuming a versioned strategy/model performance matrix and declared contiguous slice construction.
3. MinTRL / PSR only if the policy needs them, using published formulas and reference vectors.
4. No Harvey–Liu haircut formula unless an exact policy requirement is approved; use `arch` SPA/RealityCheck/StepM/MCS as the mature multiple-testing evidence path. If an exact Haircut Sharpe later becomes mandatory, it requires a separately verified published-formula implementation and tests, not a weak package.

These functions may emit metrics and diagnostics only. They may not read/write sealed-OOS permissions, choose trials, grant CertificationDecision, promote a candidate, or replace the trial/OOS ledgers.

## Target ownership tree and minimum stack

```text
40-certification-system/
  temporal-integrity       <- skfolio (KEEP): WalkForward, CPCV, purge/embargo
  multiple-testing-control <- arch (ADD): SPA / RealityCheck / StepM / MCS
  factor-diagnostics       <- deferred Alphalens only on documented Qlib gap
  regime-stress            <- deferred ruptures, offline evidence only
  sealed-oos               <- OUR CODE: authority and access ledger
  independent-replication  <- OUR CODE: policy/orchestration
  benchmark-suite          <- OUR CODE + arch evidence
  promotion                <- OUR CODE: CertificationDecision lifecycle
```

**MINIMUM_RECOMMENDED_STACK:** `skfolio = KEEP`; `arch = ADD when separately authorized`; `DSR/PBO = THIN_VERIFIED_IMPLEMENTATION_REQUIRED`; `alphalens-reloaded = DEFER`; `ruptures = DEFER`; `river = DEFER`; `MLFinLab = REJECT`.

This is the smallest mature stack that avoids duplicating skfolio, accepts `arch` where a difficult tested procedure already exists, and refuses weak/locked-in DSR/PBO dependencies.

## Final classification table

| Upstream | Role | Overlap | Maturity | License | Dependency cost | Decision | Target phase |
|---|---|---|---|---|---|---|---|
| skfolio | temporal CV / portfolio risk | retained owner | established, installed | existing project-approved runtime | already present | KEEP | P1/P2 |
| arch | multiple-model bootstrap evidence | complementary | active release/docs/tests | review exact non-SPDX repo license before pin | moderate scientific package | ADD | P1 entry / P2 evidence |
| alphalens-reloaded | factor diagnostics | partial Qlib overlap | maintained fork | Apache-2.0 | medium + plots/stats | DEFER | after first factor gap |
| ruptures | offline regime segmentation | complementary optional evidence | active | BSD-2-Clause | low/moderate | DEFER | later P1/P2 |
| river | online drift monitoring | no offline-CV overlap | very active | BSD-3-Clause | medium/high operational state | DEFER | shadow/operations |
| MLFinLab | broad financial ML | duplicates CV and more | commercial/stale public façade | all rights reserved | high/vendor lock-in | REJECT | none |
| DSR/PBO/Haircut package | selection-bias metrics | arch covers only different multiple-testing tests | no qualifying free complete stack found | mixed/restrictive | avoid weak/broad dependency | THIN_VERIFIED_IMPLEMENTATION_REQUIRED | separately authorized P2 work |

```text
P0 = COMPLETE
P1 = NOT_STARTED
CURRENT_NEXT = P1_MINIMAL_QUANT
PACKAGES_INSTALLED = NONE
CODE_CHANGED = NO
QLIB_EXECUTED = NO
RDAGENT_EXECUTED = NO
OPENBB_CALLED = NO
ROBINHOOD_TOOLS_INVOKED = NONE
TRADING_ACTIONS = NONE
```
