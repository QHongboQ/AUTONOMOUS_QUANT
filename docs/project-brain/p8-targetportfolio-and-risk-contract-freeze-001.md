# P8 TargetPortfolio and Risk Contract Freeze 001

**Task:** `AUTONOMOUS-QUANT-P8-TARGETPORTFOLIO-AND-RISK-CONTRACT-FREEZE-001`
**Base:** `e81bffcdd5d8e59f44ad3cf08d978f84d83f07f6`
**Classification:** contract design only; real portfolio and risk execution remain deferred.

## Authority and reuse

The authorized entry point is
[`p8-portfolio-risk-entry-audit-001.md`](p8-portfolio-risk-entry-audit-001.md):
P8 may freeze a broker-neutral TargetPortfolio and human-owned risk boundary
without waiting for P7 exit. P7 remains at one family with its exit condition
unsatisfied. This does not authorize a portfolio tournament or create an
ensemble.

P0 POC-C already proved a synthetic `skfolio.optimization.MeanRisk` output
mapped to a broker-neutral TargetPortfolio. P0 POC-D proved deterministic
identity and the separate synthetic TargetPortfolio-to-ExecutionPlan
boundary. The P0 artifacts remain integration evidence only. No tracked P8
TargetPortfolio or risk-envelope schema existed at this base. The frozen
contracts are in [`50-portfolio-system/contracts/README.md`](../../50-portfolio-system/contracts/README.md)
and its two JSON Schemas.

Ownership remains: Qlib owns research portfolio computation and backtesting;
skfolio owns optimization; P9+ execution owns accounts, orders, quantities,
fills, and reconciliation. AQ owns only these domain contract boundaries and
human risk policy references. No upstream portfolio or optimization
functionality is duplicated.

## Frozen contract boundary

`AQ_TARGET_PORTFOLIO_V1` contains deterministic identity, timezone-qualified
effective time, producer and output provenance, P2 certification references
(and a P4 decision reference for any Champion input), provider/episode asset
weights, explicit cash target weight, and a human risk-envelope reference.
Identity is RFC 8785/JCS SHA-256 over the complete object with the identity
field omitted. The schema carries no broker, account, order, quantity,
notional, fill, or reconciliation state.

`AQ_HUMAN_RISK_ENVELOPE_REFERENCE_V1` is either `UNSET` or points to a
human-authorized immutable risk-limit set and authority record over a bounded
effective interval. It sets no numeric limits, assets, brokers, capital, or
trading permissions. Missing, `UNSET`, expired, or unverifiable authority is
ineligible. Even a verified risk-envelope reference does not itself authorize
capital allocation, paper trading, or live trading.

P2-certified candidate inputs must be verified against an actual P2-issued
`CERTIFIED` decision. P4 Champion inputs additionally require an actual P4
decision. A Candidate record or schema-valid fixture cannot substitute for
either decision. The current authority has zero real P2-certified strategy
inputs and zero real Champions; therefore no real TargetPortfolio is eligible
for use. P7's current incompleteness does not block this contract design but
continues to block any multi-family portfolio claim.

## Validation and non-actions

Bounded synthetic JSON-schema fixtures validated: a structurally valid
non-authorized target is accepted; broker fields, a Champion without P4
decision, and an approved risk reference without its authority/limit-set
references are rejected. A fully referenced synthetic approved-risk envelope
validates structurally; the fixture carries no numeric limits or permissions
and proves no real human authority.

```text
P2_V2_SEALED_OOS_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
FACTOR_RESEARCH_COUNT = 0
REAL_PORTFOLIO_OPTIMIZATION_COUNT = 0
REAL_CAPITAL_ALLOCATION_COUNT = 0
BROKER_ACTION_COUNT = 0
PAPER_OR_LIVE_ORDERS = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P8_REAL_CERTIFIED_INPUT_COUNT = 0
P8_REAL_CHAMPION_INPUT_COUNT = 0
```
