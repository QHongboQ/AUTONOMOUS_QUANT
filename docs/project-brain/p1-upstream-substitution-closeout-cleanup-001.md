# P1 Upstream Substitution Closeout Cleanup 001

## Result

The accepted upstream-substitution stack is sealed as
`COMPLETE_PENDING_REVIEW`. This task added no functionality and did not start
market data.

The former compiler/contracts/overlays/validation/source/ingestion reference
implementation was moved from the production `aq_pit` namespace to
`tests/reference_oracle`. The 13 frozen behavioral regressions remain active,
while the production package exposes one PIT path only:
`aq_pit.build_research_ready_universe`.

`accepted_reconciliation_facts.json` is now the sole active P1 reconciliation
authority. Loading fails closed on its frozen content SHA-256
`c1745a22c17c3a8a35bf56f504c1d96398c787492dce54a60ac85801799a9f62`,
the 37 canonical finding IDs, 20 identity events, 9 overlay cases, schema,
structure, classifications, evidence references, and uniqueness constraints.
The historical unresolved-findings ledger remains archive/reference evidence
only; active runtime and DVC no longer read it.

## Test and host boundaries

Pure DatasetSnapshot export and Qlib handoff tests now use deterministic
temporary fixtures and always run on a clean checkout. Real 832-row checks, DVC
CLI behavior, pinned terminal evidence, and the WSL Qlib public-API probe are
explicit integration tests. The Qlib probe derives the checkout path
dynamically and contains no fixed repository root or Linux username.

The DVC external dependency `D:/AQ_DATA/P1/pit` remains an explicit
`HOST_LOCAL_BINDING` on the authoritative machine so DVC can natively hash the
pinned FJA input. No custom data-location framework was added.

## Behavior freeze and state

The closeout preserves 37 accepted facts, 20 identity events, 9 overlay cases,
3,236 overlay rows, 630 reconciled membership events, 832 instrument episodes,
832 DatasetSnapshot rows, and 832 Qlib ranges. The DatasetSnapshot content hash
is unchanged.

The final suite contains 137 always-run unit/contract/regression tests and 26
explicit integration tests. All 163 tests pass in the authoritative local
environment, all 13 frozen regressions pass, and compileall passes. No
integration test is reported as executed unless its required local boundary was
available and the test actually ran.

```text
P0 = COMPLETE
P1 = STARTED
P1_MINIMAL_QUANT = IN_PROGRESS
UPSTREAM_SUBSTITUTION_STACK = COMPLETE_PENDING_REVIEW
PIT_UNIVERSE_RESEARCH_READY = YES
PIT_UNIVERSE_CERTIFIED = NO
DATASET_SNAPSHOT_READY = YES
QLIB_HANDOFF_READY = YES
REAL_MARKET_DATA_READY = NO
CURRENT_NEXT = P1_UPSTREAM_SUBSTITUTION_FINAL_INDEPENDENT_REVIEW
PRODUCTION_TRADING = NOT_AUTHORIZED
```
