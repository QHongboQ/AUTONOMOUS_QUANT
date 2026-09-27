# P7 Post-Inconclusive Successor Research Admissibility Audit 001

Date: 2026-09-27

Status: `PASS_P7_SUCCESSOR_RESEARCH_SCIENTIFICALLY_PERMISSIBLE_WITH_POST_FAILURE_DISCLOSURE`

This independent scientific review determines whether a wholly new historical
static-ensemble study may be designed after P7 V1 terminated inconclusive. It
uses only the sealed structural closeout facts and pinned Qlib source
semantics. It did not reopen V1, inspect Candidate or OLS prediction values,
inspect label magnitudes, create a successor protocol, or execute research.

## Baseline and immutable V1 authority

PR #126 merged as main commit
`e782f861688fe1f70366962d3bd7c8aabaca918c`. V1 remains permanently
terminal and visible as its own study history.

```text
V1_EXECUTION_STATUS = TERMINAL_INCONCLUSIVE
V1_RERUN_ALLOWED = NO
V1_REPAIR_ALLOWED = NO
V1_RESULT = STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
V1_IS_SUPERSEDED = NO
```

## Exposed information and selection-bias review

The only post-access facts were label key presence, NaN status, affected
sessions/instruments, and structural missingness causes. No label magnitude,
prediction relationship, model statistic, portfolio return, component rank,
or other performance result was observed.

The only scientifically admissible candidate row rule for a successor is:

```text
PROPOSED_SUCCESSOR_ROW_RULE = PREDICTION_CONTROL_POPULATION_VALID AND LABEL_KEY_PRESENT AND LABEL_FINITE
```

This is a deterministic observability gate. It does not depend on label sign
or magnitude, Candidate/OLS score, RankIC, return, or any performance
statistic. It must be frozen and hashed before a successor protocol is frozen
and before any performance access.

```text
PERFORMANCE_INFORMATION_EXPOSED = NO
PREDICTION_PERFORMANCE_RELATIONSHIP_EXPOSED = NO
LABEL_MAGNITUDE_INFORMATION_EXPOSED = NO
ROW_RULE_PERFORMANCE_INDEPENDENT = YES
ROW_RULE_LABEL_MAGNITUDE_INDEPENDENT = YES
ROW_RULE_STRUCTURAL_OBSERVABILITY_BASED = YES
```

## Missingness and estimand

The sealed closeout accounts for all 114 nonfinite labels among 374,591 V1
rows: 72 membership episodes end before the complete label horizon and 42
rows have known provider gaps. These causes are structural, but they are not
proven missing completely at random.

Membership-horizon rows may be excluded from a new label-observable
evaluation population because the target is unavailable without crossing the
authoritative episode boundary. Provider-gap rows may also be excluded from a
complete-case evaluation because no observed target exists and imputation is
prohibited. The latter exclusion requires explicit non-MCAR limitation and
coverage disclosure; the successor cannot claim results for the excluded
rows.

```text
MEMBERSHIP_FAILURE_EXCLUSION_JUSTIFICATION = DEFENSIBLE_FAIL_CLOSED_TARGET_UNOBSERVABLE_WITHIN_AUTHORIZED_MEMBERSHIP_HORIZON
PROVIDER_GAP_EXCLUSION_JUSTIFICATION = DEFENSIBLE_COMPLETE_CASE_EXCLUSION_WITH_NON_MCAR_DISCLOSURE_AND_NO_IMPUTATION
MISSINGNESS_ASSUMPTION = NOT_MCAR
STRUCTURAL_MISSINGNESS_DISCLOSURE_REQUIRED = YES
ESTIMAND_CHANGED_FROM_V1 = YES
SUCCESSOR_ESTIMAND = CONDITIONAL_ON_PREREGISTERED_LABEL_OBSERVABILITY
```

The required disclosure must include the membership-horizon and provider-gap
counts plus the affected session and instrument counts. It must not include a
performance split by missingness cause.

## Qlib-native compatibility

Pinned Qlib source
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` defines the Alpha158 label as
`Ref($close, -2)/Ref($close, -1) - 1`. `SignalRecord.generate_label` requests
the raw label (`DataHandlerLP.DK_R`) and saves it without applying the learning
processor. `DropnaLabel` delegates to `dropna` for the label group and declares
itself unsafe for inference.

Qlib therefore natively represents missing raw labels and drops them in its
learning path. A separately preregistered evaluation-population finiteness
gate is compatible with these semantics, provided AQ does not replace Qlib's
label formula or implement a label engine.

```text
QLIB_SUPPORTS_MISSING_LABEL_STATE = YES
QLIB_NATIVE_LEARNING_DROPS_MISSING_LABELS = YES
FUTURE_ROW_LEVEL_LABEL_GATE_COMPATIBLE_WITH_QLIB = YES
FUTURE_LABEL_GENERATION_OWNER = QLIB
FUTURE_LABEL_SEMANTICS_OWNER = QLIB
FUTURE_LABEL_INTEGRITY_GATE_OWNER = AQ_THIN_FAIL_CLOSED_CONTRACT
```

## Contamination and successor identity

Knowing which rows are structurally unobservable is post-failure information,
so the contamination is not `NONE`. It is limited to structural observability:
no values, signs, prediction relationships, or performance statistics were
exposed. The gate is not permitted to evolve after any successor outcome
access.

```text
POST_FAILURE_INFORMATION_CONTAMINATION = LIMITED_STRUCTURAL_ONLY
NEW_STUDY_IDENTITY_REQUIRED = YES
NEW_PROTOCOL_IDENTITY_REQUIRED = YES
NEW_INPUT_CONTRACT_IDENTITY_REQUIRED = YES
NEW_POPULATION_INDEX_IDENTITY_REQUIRED = YES
NEW_LABEL_VALIDITY_MASK_IDENTITY_REQUIRED = YES
NEW_EXECUTION_ATTEMPT_IDENTITY_REQUIRED = YES
```

Before protocol freeze, the new input contract must bind the exact 17
Candidate identities and prediction hashes, OLS prediction hash, Qlib label
artifact and formula/runtime identities, label key-presence and finite masks,
final evaluation population and SHA, provider-gap evidence, and complete old
to new population accounting. It may inspect label observability only, not
label values or prediction performance.

Any later one-shot execution must be committed before outcome access. Its
pre-outcome manifest must bind the exact execution commit and script SHA-256,
and reject a dirty worktree, HEAD mismatch, or protocol/input mismatch.

## Immutable scientific boundary

The Candidate roster, OLS control, ensemble weighting, component selection,
signs, weights, and primary comparator may not change merely because V1
failed structurally. Changing any of those elements defines a different
research question requiring separate justification.

```text
FILL_LABEL_WITH_ZERO = PROHIBITED
FORWARD_FILL_LABEL = PROHIBITED
BACKFILL_LABEL = PROHIBITED
SYNTHETIC_RETURN_IMPUTATION = PROHIBITED
CUSTOM_AQ_LABEL_GENERATION = PROHIBITED
SUCCESSOR_RESEARCH_ADMISSIBILITY = SCIENTIFICALLY_PERMISSIBLE_WITH_POST_FAILURE_DISCLOSURE
```

This is scientific permission to freeze a new input contract only. It is not
permission to create a protocol or execute the study in this task.

```text
CANDIDATE_PREDICTION_VALUES_ACCESSED = 0
OLS_PREDICTION_VALUES_ACCESSED = 0
LABEL_MAGNITUDES_ACCESSED = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
SPA_MCS_EXECUTION_COUNT = 0
PORTFOLIO_BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
AQ_LABEL_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_STATIC_ENSEMBLE_LABEL_OBSERVABLE_INPUT_CONTRACT_FREEZE_001
FINAL_CLASSIFICATION = PASS_P7_SUCCESSOR_RESEARCH_SCIENTIFICALLY_PERMISSIBLE_WITH_POST_FAILURE_DISCLOSURE
```
