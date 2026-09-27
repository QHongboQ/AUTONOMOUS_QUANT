# P8 Portfolio / Risk Entry Audit 001

## Decision

P8 may begin bounded contract and upstream-ownership work, but it may not run a
real portfolio tournament or production risk overlay yet.

The Roadmap exit condition is a stable `TargetPortfolio` contract. P0 already
proved the broker-neutral TargetPortfolio boundary and a synthetic
TargetPortfolio-to-ExecutionPlan handoff. Qlib and skfolio are already selected
upstream owners for portfolio/backtest/optimization mechanics. Those facts are
sufficient to authorize P8 interface and ownership design.

They are not sufficient to authorize real capital allocation, Champion
selection, or a portfolio tournament over certified production strategies.

```text
BASE_MAIN = e90d18b0511b6d0981b16111ddf4a75424d86562
P8_ENTRY_AUDIT = COMPLETE
P8_ENTRY_ALLOWED_FOR_CONTRACT_AND_UPSTREAM_DESIGN = YES
P8_REAL_PORTFOLIO_TOURNAMENT_AUTHORIZED = NO
P8_REAL_RISK_OVERLAY_EXECUTION_AUTHORIZED = NO
P8_EXIT_CONDITION_SATISFIED = NO
```

## Existing upstream and interface evidence

### Qlib and skfolio

Current architecture already assigns generic portfolio construction,
optimization, WalkForward, CombinatorialPurgedCV, MeanRisk, and compatible
financial tooling to Qlib + skfolio. AQ owns only project portfolio policy and
human risk limits.

P0 POC-C exercised `skfolio.optimization.MeanRisk` with explicit long-only,
full-investment constraints and produced a broker-neutral TargetPortfolio. The
POC was integration-only and not certification or production evidence.

```text
P8_GENERIC_PORTFOLIO_OPTIMIZER_OWNER = SKFOLIO
P8_RESEARCH_BACKTEST_PORTFOLIO_OWNER = QLIB
AQ_GENERIC_PORTFOLIO_OPTIMIZER = NO
```

### TargetPortfolio boundary

P0 POC-D proved a deterministic broker-neutral TargetPortfolio to synthetic
ExecutionPlan boundary. The TargetPortfolio contained no broker, account,
order, quantity, notional, or execution state. POC-D also proved that execution
mechanics remain downstream of the portfolio contract.

```text
P0_TARGETPORTFOLIO_POC = PASS_SYNTHETIC_INTEGRATION_ONLY
P0_TARGETPORTFOLIO_TO_EXECUTIONPLAN_POC = PASS_SYNTHETIC_INTEGRATION_ONLY
P8_TARGETPORTFOLIO_CONTRACT_DESIGN_REUSE_ALLOWED = YES
```

P8 must not copy POC-D's execution planner into the portfolio layer. Execution
remains owned by P9+.

## Current blockers to real P8 execution

### P7 ensemble unavailable

P7 entry audit found only one current candidate alpha family,
`P3_FORMULAIC_ALPHA`, and therefore deferred multi-family ensemble execution.

```text
P7_STATUS = DEFERRED_INSUFFICIENT_INDEPENDENT_ALPHA_FAMILIES
P7_EXIT_CONDITION_SATISFIED = NO
P7_ENSEMBLE_ARTIFACT_AVAILABLE = NO
```

P8 contract work may not manufacture an ensemble merely to obtain a portfolio
input.

### No real Certified / Champion artifact

P2 Formulaic Alpha V2 remains in sealed-OOS accumulation. P4 has no real
P2-issued Certified artifact, Shadow, or Champion.

```text
P4_REAL_CERTIFIED_ARTIFACT_COUNT = 0
P4_REAL_CHAMPION_COUNT = 0
P8_REAL_CERTIFIED_STRATEGY_INPUT_COUNT = 0
```

Therefore any real portfolio tournament, capital allocation decision, or
production risk policy execution would be premature.

## Authorized P8 scope now

P8 may now perform only:

1. upstream ownership revalidation for Qlib/skfolio portfolio capabilities;
2. a minimal broker-neutral `TargetPortfolio` domain contract;
3. deterministic identity/version/provenance rules for that contract;
4. human-owned risk-envelope contract design;
5. portfolio-method inventory and future tournament protocol design;
6. fail-closed handoff rules from future Certified/Champion inputs.

P8 must not:

- optimize real candidate capital weights;
- use P2 sealed-OOS results;
- create a real Champion portfolio;
- place paper/live orders;
- duplicate skfolio optimizers;
- duplicate Qlib portfolio/backtest engines;
- implement broker order state;
- turn synthetic P0 fixtures into production evidence.

```text
P8_MODEL_TRAINING_COUNT = 0
P8_BACKTEST_COUNT = 0
P8_REAL_PORTFOLIO_OPTIMIZATION_COUNT = 0
P8_BROKER_ACTION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
```

## Empty portfolio tree is not a blocker

The logical directories under `50-portfolio-system` currently contain no
implementation. That is acceptable: the tree is a responsibility map, not a
requirement to self-write engines. P8 must populate only bounded AQ-specific
contracts/policies after upstream ownership is proven.

```text
P8_PORTFOLIO_TREE_IMPLEMENTATION_STATUS = EMPTY_BY_DESIGN_PRE_ENTRY
P8_EMPTY_TREE_REQUIRES_GENERIC_ENGINE_BUILD = NO
```

## Next

The next task should freeze ownership and the minimal TargetPortfolio/risk
contract before any portfolio tournament implementation.

```text
NEXT_TASK = P8_PORTFOLIO_UPSTREAM_OWNERSHIP_AND_TARGETPORTFOLIO_CONTRACT_FREEZE_001
FINAL_CLASSIFICATION = PASS_P8_ENTRY_AUDIT_CONTRACT_DESIGN_ALLOWED_REAL_PORTFOLIO_EXECUTION_DEFERRED
```
