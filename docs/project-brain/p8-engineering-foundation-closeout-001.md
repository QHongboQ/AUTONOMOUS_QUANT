# P8 Engineering Foundation Closeout 001

**Date:** 2026-10-13
**Base main:** `487cd5c6d3299e37b6df008cd8bde6f9fec8bc73`
**Scope:** documentation-only phase closeout; no tests or experiments rerun.

## Decision

The original P8 engineering exit condition—stable broker-neutral
`TargetPortfolio` contract—is met. PR #147 was merged into `main` as commit
`487cd5c6d3299e37b6df008cd8bde6f9fec8bc73`.

```text
P8_CONTRACT_V1 = FROZEN_AND_MERGED
P8_SKFOLIO_NATIVE_CAPABILITIES = VERIFIED
P8_QLIB_NATIVE_PORTFOLIO_CAPABILITY = VERIFIED
P8_GENERIC_OPTIMIZER_OWNER = SKFOLIO
P8_RESEARCH_PORTFOLIO_OWNER = QLIB
AQ_CUSTOM_PORTFOLIO_ENGINE_REQUIRED = NO
AQ_CUSTOM_RISK_ENGINE_REQUIRED = NO
P8_ENGINEERING_FOUNDATION = CLOSED
P8_REAL_PORTFOLIO_TOURNAMENT = DEFERRED
P8_HUMAN_RISK_LIMIT_SET = NOT_YET_APPROVED
P8_PRODUCTION_RISK_ACTIVATION = NOT_AUTHORIZED
```

## Frozen contract and ownership

The merged V1 contracts are defined in
[`50-portfolio-system/contracts/README.md`](../../50-portfolio-system/contracts/README.md),
[`target_portfolio_v1.schema.json`](../../50-portfolio-system/contracts/target_portfolio_v1.schema.json),
and
[`human_risk_envelope_reference_v1.schema.json`](../../50-portfolio-system/contracts/human_risk_envelope_reference_v1.schema.json).
They retain a deterministic, provenance-bearing, time-qualified,
broker-neutral target; P2 equity instrument identities; explicit cash weight;
and a reference to human-owned risk authority. They do not define numeric
limits or encode broker, account, order, quantity, fill, or reconciliation
state. The historical freeze record is
[`p8-targetportfolio-and-risk-contract-freeze-001.md`](p8-targetportfolio-and-risk-contract-freeze-001.md).

Qlib owns research portfolio and backtest mechanics. skfolio owns generic
optimization and risk calculations. The retained native verification at
`E:\AQ\RESEARCH\P8\upstream-native-portfolio-capability-001\verification.md`
records one bounded synthetic skfolio capability check, the installed Qlib
native `WeightStrategyBase` surface, and reuse of prior P0-C/P0-D evidence.
No synthetic output is a certified strategy or an approved risk policy.
Because these upstream owners cover their generic capabilities, no AQ
optimizer, portfolio engine, or risk-calculation engine is required.

The human risk-envelope contract records authority by reference; it supplies
no risk numbers, capital permission, permitted assets, broker permission, or
activation permission. `UNSET`, missing, expired, or unverifiable authority
fails closed.

## Re-entry boundary

Real portfolio work remains deferred. A future consumer may proceed only
after verifying each input against an actual P2-issued `CERTIFIED` decision;
each input represented as a P4 Champion must additionally resolve to its P4
decision. A current human-approved risk-envelope reference must be applicable
to the target's effective time and independently verifiable. The current
authority records zero real P2-certified strategy inputs and zero real P4
Champions. P2 sealed OOS remains inaccessible. Contract validity alone grants
no investment, allocation, paper-trading, live-trading, or production-risk
authority.

The P8 entry boundary and upstream decision are retained in
[`p8-portfolio-risk-entry-audit-001.md`](p8-portfolio-risk-entry-audit-001.md),
[`p0-poc-c-qlib-certification-skfolio-001.md`](p0-poc-c-qlib-certification-skfolio-001.md),
[`p0-poc-d-targetportfolio-executionplan-001.md`](p0-poc-d-targetportfolio-executionplan-001.md),
and [`upstream-ownership-model.md`](upstream-ownership-model.md).

P7 remains deferred; this closeout neither creates a second alpha family nor
asserts that a multi-family portfolio exists.

## Future phase boundary

P9 may use official LEAN for isolated simulation or paper-capability work
under its own authorization; this closeout does not activate paper production.
Robinhood Trading MCP remains the original P0 primary live-broker candidate
for P10. The project does not assert that an official LEAN-to-Robinhood
brokerage connector exists. Robinhood authentication, account or brokerage
data access, order submission, and any production activation require
separate owner approval.

## Evidence and non-actions

- PR #147's merged commit is the frozen contract authority on `main`.
- The Qlib/skfolio native verification is reused; no tests or experiments were
  rerun for this closeout.
- No production source, JSON Schema, test, upstream runtime, P2, P3, or P8
  contract was modified by this documentation closeout.
- No P2 sealed OOS access, brokerage access, or broker action occurred.

```text
P2_V2_SEALED_OOS_ACCESSED = NO
P3_MODIFIED = NO
BROKER_ACTION_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```
