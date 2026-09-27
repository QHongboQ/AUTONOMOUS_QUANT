# P7 Historical Static Ensemble Inconclusive Result Closeout 001

Date: 2026-09-27

Status: `PASS_P7_STATIC_ENSEMBLE_V1_TERMINAL_INCONCLUSIVE_CLOSEOUT`

This task permanently closes the frozen P7 V1 historical static-ensemble
execution as `STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE`. It performed a
structural label-integrity audit only. It did not reopen Candidate or OLS
prediction values, execute an ensemble, calculate RankIC, run SPA/MCS,
partition outcomes with WalkForward/CPCV, backtest a portfolio, or compute a
performance metric.

## Terminal V1 authority

PR #125 was merged at `2026-09-27T19:58:37Z` as main commit
`f23d0f6c4af8c9b1078f4e9e66a4c15c34e45aba`. The V1 protocol, result
reference, and original private evidence hashes remain unchanged.

```text
V1_EXECUTION_STATUS = TERMINAL_INCONCLUSIVE
V1_RERUN_ALLOWED = NO
V1_REPAIR_AND_CONTINUE_ALLOWED = NO
V1_PROTOCOL_MUTATION_ALLOWED = NO
V1_POPULATION_MUTATION_ALLOWED = NO
V1_LABEL_POLICY_MUTATION_ALLOWED = NO
PROTOCOL_SHA256 = b60078bdba4190fbda2c6f3d3580f0e40a9801c87867095bfaa12885a0fb3ff4
REAL_OUTCOME_EXECUTION_ATTEMPT_COUNT = 1
RESULT_CLASSIFICATION = STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
```

## Structural label census

The audit bound label artifact
`c14c7c3f1e698126663b85dfcf436cf3258dc4609e8217e95ed188d9be7db35e`
and the exact 374,591-row population identity
`2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e`.
Every population key exists in the label artifact. Exactly 114 present rows
contain NaN; there are no absent keys and no positive or negative infinities.
No label magnitude, sign, rank, distribution, or prediction relationship was
computed or retained.

```text
LABEL_POPULATION_ROW_COUNT = 374591
LABEL_PRESENT_ROW_COUNT = 374591
LABEL_MISSING_ROW_COUNT = 114
LABEL_NAN_ROW_COUNT = 114
LABEL_POSINF_ROW_COUNT = 0
LABEL_NEGINF_ROW_COUNT = 0
LABEL_NONFINITE_ROW_COUNT = 114
LABEL_AFFECTED_SESSION_COUNT = 74
LABEL_AFFECTED_INSTRUMENT_COUNT = 57
FIRST_AFFECTED_SESSION = 2022-02-09
LAST_AFFECTED_SESSION = 2024-12-20
LABEL_KEY_ABSENT_COUNT = 0
LABEL_PRESENT_NAN_COUNT = 114
LABEL_PRESENT_INF_COUNT = 0
```

`LABEL_MISSING_ROW_COUNT` records Qlib missing-value rows, while
`LABEL_KEY_ABSENT_COUNT` separately records absent keys.

## Proven structural causes

Pinned Qlib source
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` defines negative `Ref` offsets
as future data. The frozen expression therefore requires finite t+1 and t+2
closes for each row. Both future closes are unavailable for all 114 affected
rows. Existing episode, identity, provider-asset, and availability evidence
supports two mutually exclusive causes:

```text
MEMBERSHIP_EPISODE_ENDED_BEFORE_LABEL_HORIZON = 72
KNOWN_PROVIDER_GAP = 42
UNRESOLVED_LABEL_FAILURE_ROW_COUNT = 0
T_PLUS_1_CLOSE_UNAVAILABLE_COUNT = 114
T_PLUS_2_CLOSE_UNAVAILABLE_COUNT = 114
T_PLUS_1_MEMBERSHIP_INVALID_COUNT = 34
T_PLUS_2_MEMBERSHIP_INVALID_COUNT = 72
FUTURE_PROVIDER_ASSET_FILE_MISSING_COUNT = 0
SECURITY_IDENTITY_REFERENCE_MISSING_COUNT = 0
```

For the 72 membership cases, at least one required future session falls beyond
the exact episode boundary. The remaining 42 rows retain the complete
membership horizon but have explicit existing provider-gap evidence. No cause
was inferred from label NaN alone.

## Input-contract gap

The prior input-qualification report explicitly records
`LABEL_OR_RETURN_ARTIFACTS_OPENED = 0`. Its two-session safety check bounded
the common calendar globally at 2024-12-27 while the provider continued
through 2024-12-31. It verified current close row-by-row, but did not open the
label artifact or verify that both future dependencies were finite for every
population row.

```text
CALENDAR_LEVEL_LABEL_HORIZON_CHECK = YES
ROW_LEVEL_LABEL_FINITE_CHECK = NO
INPUT_CONTRACT_GAP_CLASSIFICATION = INPUT_CONTRACT_OMITTED_ROW_LEVEL_LABEL_ELIGIBILITY
```

This is not a Qlib label defect: Qlib preserved its native future-reference
semantics and returned missing labels where the required future source values
were unavailable. Provider and membership gaps explain the individual rows;
the research-contract defect was omission of their row-level label-validity
gate before protocol freeze.

Any future contract must bind the exact Qlib label artifact, exact
population-to-label keys, the preregistered row-level finiteness mask, and
that mask's identity before outcome access. It may not mutate the population
after result access.

```text
FUTURE_LABEL_GENERATION_OWNER = QLIB
FUTURE_LABEL_SEMANTICS_OWNER = QLIB
FUTURE_LABEL_INTEGRITY_GATE_OWNER = AQ_THIN_FAIL_CLOSED_CONTRACT
AQ_LABEL_ENGINE = NO
```

## Execution-code provenance limitation

The V1 attempt manifest bound `BASE_MAIN`, protocol, inputs, label hash,
source prediction hashes, and upstream versions. It did not bind a content
SHA for the execution script, and `BASE_MAIN` did not contain that uncommitted
script before Phase B. No pre-outcome script hash or execution commit may be
fabricated retroactively.

```text
PRE_OUTCOME_EXECUTION_SCRIPT_CONTENT_SHA_BOUND = NO
PRE_OUTCOME_EXECUTION_COMMIT_BOUND = NO
FUTURE_ONE_SHOT_EXECUTION_CODE_MUST_BE_COMMITTED_BEFORE_OUTCOME_ACCESS = YES
FUTURE_ATTEMPT_MANIFEST_MUST_BIND_EXECUTION_CODE_SHA256 = YES
PROVENANCE_GAP_CHANGES_RESULT_CLASSIFICATION = NO
```

The limitation prevents overclaiming exact execution-code reproducibility,
but it does not change the current classification: no ensemble, metric,
statistical test, or portfolio result was produced.

## Scientific authority and successor boundary

```text
V1_PROVIDES_EVIDENCE_FOR_ENSEMBLE_PERFORMANCE = NO
V1_PROVIDES_EVIDENCE_AGAINST_ENSEMBLE_PERFORMANCE = NO
V1_P2_CERTIFICATION_EVIDENCE = NO
V1_P7_DYNAMIC_ROSTER_EVIDENCE = NO
V1_P7_EXIT_EVIDENCE = NO
V1_PRODUCTION_AUTHORIZATION = NO
SUCCESSOR_RESEARCH_ADMISSIBILITY = REQUIRES_INDEPENDENT_REVIEW
```

Only label integrity/missingness was observed; no performance was computed.
That makes a separately preregistered successor scientifically reviewable,
but this closeout does not authorize one, create a V2 protocol, change the
population, or route directly to execution.

The original V1 root was not mutated. New closeout evidence is sealed at
`D:/AQ_DATA/P7/historical-static-ensemble-inconclusive-closeout-001`; its
checksum manifest SHA-256 is
`07eb215536ef54eb2765e11499f2ce92805f2c8b52b2dd6b00876bd8981ab77d`.

```text
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P7_POST_INCONCLUSIVE_SUCCESSOR_RESEARCH_ADMISSIBILITY_AUDIT_001
FINAL_CLASSIFICATION = PASS_P7_STATIC_ENSEMBLE_V1_TERMINAL_INCONCLUSIVE_CLOSEOUT
```
