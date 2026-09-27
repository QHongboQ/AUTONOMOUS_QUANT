# P7 Historical Static Ensemble Research Execution 001

Date: 2026-09-27

Status: `STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE`

The exact frozen historical static-ensemble protocol was attempted once. All
Phase A identity and synthetic-method gates passed before any real prediction
or label value was deserialized. The immutable attempt root records the exact
17 Candidate identities and derived/source prediction hashes, OLS identity,
eligible-grid identity, Qlib source identity, and pinned Qlib/skfolio/arch
runtime checks.

## One-shot outcome

Phase B began at `2026-09-27T19:07:36.585773Z` and set the attempt count to
one before deserialization. The 17 Candidate views, OLS view, and frozen label
artifact were opened. The attempt then stopped at the label integrity gate:
after projecting the frozen label artifact onto the exact 374,591-row
population, at least one label was missing or non-finite. The fail-closed
boundary raised:

```text
RuntimeError: label is missing or non-finite on frozen population
```

This occurred before Qlib ensemble combination, RankIC calculation, arch
SPA/MCS, skfolio WalkForward/CPCV, or the secondary portfolio projection.
Consequently no endpoint or performance result exists and no scientific
direction can be inferred.

The frozen one-shot rule forbids changing the label policy or execution code
and retrying after outcome access. The failed attempt is therefore sealed as
`STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE`; it is not repaired or rerun under this
protocol.

## Sealed authority

```text
BASE_MAIN = 3cfa76f9d7541d00ce672da2cfcaf0827dfeb015
PROTOCOL_SHA256 = b60078bdba4190fbda2c6f3d3580f0e40a9801c87867095bfaa12885a0fb3ff4
INPUT_CONTRACT_SHA256 = 92de81d0b8b7b7a29891bf523ae8519af44456f52fea3410ebf0ebd210d0f81f
POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
REAL_OUTCOME_ACCESS_STARTED = YES
REAL_OUTCOME_EXECUTION_ATTEMPT_COUNT = 1
RESULT_CLASSIFICATION = STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PORTFOLIO_BACKTEST_COUNT = 0
MODEL_TRAINING_COUNT = 0
MODEL_REFIT_COUNT = 0
PREDICTION_GENERATION_COUNT = 0
PRISTINE_OOS = NO
P2_CERTIFICATION_EVIDENCE = NO
P7_DYNAMIC_ROSTER_EVIDENCE = NO
P7_EXIT_CONDITION_EVIDENCE = NO
PRODUCTION_AUTHORIZATION = NO
INDEPENDENT_ALPHA_FAMILY_COUNT = 1
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

Private evidence is sealed at
`D:/AQ_DATA/P7/historical-static-ensemble-research-execution-001`. The tracked
result reference binds the private attempt, failure, final result, and checksum
manifest without placing private artifacts in Git.

```text
ATTEMPT_MANIFEST_SHA256 = 07f974108cd9778558bcbdbf68122d117cdb815e559bba86b25b0fe92803f0fc
FAILURE_SHA256 = 76bec2f79b75eafa0ba28c0a55d85850a65de4d19d9a103b52d6d5c19fa048ae
FINAL_RESULT_SHA256 = d9e9bec3c8b11d9027aafb3f64afeb7f099a7ba7039440019fcd28f31c98d396
CHECKSUMS_MANIFEST_SHA256 = 728c6b9dac2235fdd93a96ee7b856476d939206ee6494fa9251f3c5842f9b5f4
```

The next task may close out the inconclusive result and audit the frozen label
population mismatch without reopening this attempt. It must not interpret the
failure as evidence for or against the ensemble.

```text
CURRENT_DEVELOPMENT_NEXT = P7_HISTORICAL_STATIC_ENSEMBLE_INCONCLUSIVE_RESULT_CLOSEOUT_001
FINAL_CLASSIFICATION = STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
```
