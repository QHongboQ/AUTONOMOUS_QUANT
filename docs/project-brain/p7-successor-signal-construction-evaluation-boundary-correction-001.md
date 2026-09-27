# P7 Successor Signal-Construction / Evaluation Boundary Correction 001

Date: 2026-09-27

Status: `PASS_SUCCESSOR_SIGNAL_CONSTRUCTION_EVALUATION_BOUNDARY_CORRECTED_PRE_OUTCOME`

## Pre-outcome correction authority

PR #129 is merged at baseline
`e98256f17b2391943e4c3f38414d34db98da04b1`. PR #130 remains open and is
not modified by this task. No successor outcome has been accessed.

Pinned Qlib source `2fb9380b342556ddb50a4b24e4fe8655d548b2b8`
implements `AverageEnsemble` by concatenating component predictions, grouping
by `datetime`, performing cross-sectional mean/std standardization, and only
then averaging. Consequently, applying a future-label-observability mask
before `AverageEnsemble` would change the constructed signal and is
scientifically invalid.

The prior successor input contract and protocol are therefore superseded
before outcome access:

```text
PRIOR_SUCCESSOR_INPUT_CONTRACT_SHA256 = b693f43b8dfab0fa04cb12a876fc32928bc5020592a2e137f1c0cbfdde0639ee
CORRECTED_SUCCESSOR_INPUT_CONTRACT_SHA256 = b9e0c447794c318d7ddc00803e0f2ea5468abc4c77a43752ead2910804b8a7b5
PRIOR_SUCCESSOR_PROTOCOL_SHA256 = a4ca307c3e3a245bb211978d36f03d8a2552c81df28049ddb6b667231689a894
CORRECTED_SUCCESSOR_PROTOCOL_SHA256 = cb61628ed49ca0f9d9798f92567adedbeb533f6854da098ec3c945b38bdbd76a
PRIOR_SUCCESSOR_AUTHORITY_STATUS = SUPERSEDED_PRE_OUTCOME_BY_SIGNAL_EVALUATION_BOUNDARY_CORRECTION
OLD_PR130_SCRIPT_AUTHORIZABLE = NO
```

This does not supersede or reopen V1. V1 remains permanently
`STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE` with rerun prohibited.

## Distinct frozen populations

Signal construction uses the outcome-independent V1 prediction/control
population. The 17 immutable Candidate predictions are projected to that exact
ordered population, the session-local constant-component policy is applied,
and Qlib `AverageEnsemble` constructs the full signal. Only afterward is the
already-frozen label-observable evaluation population applied for primary
RankIC and statistical evaluation.

```text
SIGNAL_CONSTRUCTION_POPULATION = V1_PREDICTION_CONTROL_POPULATION
SIGNAL_CONSTRUCTION_ROW_COUNT = 374591
SIGNAL_CONSTRUCTION_POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
EVALUATION_POPULATION = SUCCESSOR_LABEL_OBSERVABLE_POPULATION
EVALUATION_ROW_COUNT = 374477
EVALUATION_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
LABEL_VALIDITY_MASK_SHA256 = 2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf
LABEL_OBSERVABILITY_USED_IN_SIGNAL_CONSTRUCTION = NO
LABEL_VALIDITY_MASK_APPLIED_BEFORE_AVERAGEENSEMBLE = PROHIBITED
PORTFOLIO_SIGNAL_POPULATION = V1_PREDICTION_CONTROL_POPULATION
LABEL_OBSERVABILITY_USED_FOR_PORTFOLIO_SIGNAL_SELECTION = NO
```

## Primary and secondary failure semantics

The six primary gates are unchanged. `INCONCLUSIVE` applies only when a
required input or method integrity failure prevents complete valid primary and
robustness evidence: ensemble RankIC, OLS RankIC, their mean delta, SPA,
WalkForward, CPCV, and exact frozen identities/integrity.

Individual component RankIC is secondary. Exact-constant Candidate/session
pairs remain unavailable/NaN without imputation; component summaries use only
finite component sessions and disclose their valid-session counts. MCS remains
descriptive. If its exact 18-column loss matrix is incomplete, its explicit
status is `NOT_AVAILABLE_SECONDARY_INCOMPLETE_LOSS_MATRIX`; no complete-case
filter is invented. Portfolio projection and run-lineage status are also
separate secondary evidence. Their failure after complete primary and
robustness evidence cannot change the primary classification.

```text
COMPONENT_CONSTANT_SESSION_RANKIC_POLICY = UNAVAILABLE_NAN_NOT_IMPUTED_NOT_ZERO
MCS_NON_GATING_FAILURE_POLICY = NOT_AVAILABLE_SECONDARY_INCOMPLETE_LOSS_MATRIX_NO_PRIMARY_CLASSIFICATION_EFFECT
PORTFOLIO_NON_GATING_FAILURE_POLICY = RECORD_FAILURE_NO_PRIMARY_CLASSIFICATION_EFFECT
RUN_LINEAGE_FAILURE_POLICY = RECORD_STATUS_NO_SIX_GATE_CHANGE_AFTER_COMPLETE_PRIMARY_ROBUSTNESS_EVIDENCE
PRIMARY_INCONCLUSIVE_RULE = REQUIRED_INPUT_OR_METHOD_INTEGRITY_FAILURE_PREVENTS_COMPLETE_VALID_PRIMARY_AND_ROBUSTNESS_EVIDENCE
```

## Safety and routing

No execution code, provenance seal, real output root, prediction value, label
magnitude, ensemble, RankIC, statistical procedure, or portfolio backtest was
created or executed.

```text
CANDIDATE_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
OLS_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
LABEL_MAGNITUDES_ACCESSED = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
SPA_MCS_EXECUTION_COUNT = 0
PORTFOLIO_BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_CODE_REBASE_AFTER_BOUNDARY_CORRECTION_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_SIGNAL_CONSTRUCTION_EVALUATION_BOUNDARY_CORRECTED_PRE_OUTCOME
```
