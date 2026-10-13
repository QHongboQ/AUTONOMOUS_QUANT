# P8 TargetPortfolio and human risk-envelope contracts

**Status:** contract freeze only; no certified/Champion strategy or active risk
envelope is supplied by this change.

## Ownership and reuse

P8 is authorized for bounded contract design by
`docs/project-brain/p8-portfolio-risk-entry-audit-001.md`. P0 POC-C already
emitted a broker-neutral TargetPortfolio from a synthetic `skfolio.MeanRisk`
fixture. P0 POC-D proved deterministic identity and the downstream
TargetPortfolio-to-ExecutionPlan boundary. Those artifacts are integration
fixtures, not certification or production evidence. This contract reuses that
boundary; it does not copy the P0 planner.

Qlib owns research portfolio computation/backtesting. skfolio owns portfolio
optimization. Neither is reimplemented here. P9+ execution owns accounts,
orders, quantities, fills, fees, reconciliation, and broker state.

## TargetPortfolioV1

`target_portfolio_v1.schema.json` freezes a broker-neutral snapshot containing:

- `contract_version` and deterministic `target_portfolio_id`;
- timezone-qualified `effective_time`;
- producer/method and output-artifact provenance;
- exact P2-certified candidate references, optionally with a P4 Champion
  decision reference;
- an asset-keyed P2 equity instrument-weight map (which may be empty) and a
  separate explicit cash weight;
- a reference to the human-owned risk envelope.

The identity is `sha256:` plus SHA-256 of RFC 8785/JCS canonical UTF-8 JSON for
the complete object with only `target_portfolio_id` omitted. `target_weights`
is keyed only by the `qlib_instrument_id()` output from the accepted P2
security identity: `P2SEC` followed by 64 uppercase hexadecimal characters.
This matches the authoritative implementation in
`30-research-system/qlib/dataset-adapter/aq_qlib_handoff/ragged_panel.py` and
does not admit ticker aliases such as `AAPL`. An empty map is valid when the
explicit `cash_target_weight` is present. A future asset class or identity
scheme requires a separately versioned contract. JSON object keys are
canonicalized by JCS. This is an identity rule, not an AQ hashing
implementation.

The retained synthetic suite is `tests/Test-P8Contracts.ps1`; it uses the
installed PowerShell `Test-Json` validator and keeps all evidence references
under `fixture://`. A successful synthetic validation is never real
certification, human approval, or trading permission.

Weights are fractions of portfolio NAV. The schema deliberately does not
choose long-only, leverage, net/gross exposure, normalization, concentration,
turnover, or permitted-asset limits. Those are human-owned risk-envelope
terms. A target is not an order, allocation authorization, or permission to
trade. A consumer must fail closed unless every input resolves to a P2-issued
`CERTIFIED` decision, every claimed Champion also resolves to its P4 decision,
and a current human-approved envelope is verifiably applicable. Schema
validation alone proves none of those external facts.

## HumanRiskEnvelopeReferenceV1

`human_risk_envelope_reference_v1.schema.json` records either `UNSET` or a
reference to a human-owned, immutable limit set and its authority record. P8
defines no numeric limit, asset permission, broker permission, capital
authorization, or activation permission. The actual limit-set artifact must be
written and approved by the human owner before use; its reference and digest
must be verified at the consuming boundary. `UNSET`, missing, expired, or
unverifiable references fail closed.

The human authority must define the applicable capital, leverage, exposure,
concentration, turnover, drawdown/de-risk, and permitted-asset/broker
boundaries as relevant. This list defines ownership, not values or defaults.
Even a valid approved risk-envelope reference is not itself production or
live-trading authorization.

When materialized, `risk_envelope_id` is `sha256:` plus SHA-256 of RFC
8785/JCS canonical UTF-8 JSON for the complete envelope object with only
`risk_envelope_id` omitted. An approved reference has a bounded
`effective_from`/`effective_until` interval. A consumer checks the portfolio's
effective time against that interval and verifies both referenced artifacts;
this contract does not implement that policy engine.

## Eligibility and phase boundary

No current Certified or Champion input is asserted. P7 remains at one family
and its exit condition is unsatisfied; P8 contract design is independent of
that status, but no ensemble or portfolio may be manufactured to bypass it.
P2 sealed OOS remains inaccessible. Current P2 protocol/cohort eligibility
must be checked from the authoritative P2 decision, not inferred from a
Candidate record or this schema. A Candidate V4 that is not P2-eligible is not
an admissible portfolio input.

The P0 examples remain synthetic and outside this schema's evidence of real
eligibility. Contract acceptance creates no Certified, Champion, allocation,
paper-trading, or live-trading state.
