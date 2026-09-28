# P7 Successor Cross-Git Runtime Text Equivalence Correction 001

Date: 2026-09-27

Status: `PASS_CROSS_GIT_RUNTIME_TEXT_EQUIVALENCE_CORRECTED`

## Prior pre-outcome rejection

The authorized main and seal authority were both
`16977fbf8ba62aa3b689cb94a0b56483c4c64739`. The sole invocation rejected
before the outcome marker with `WORKTREE_SCRIPT_HEAD_MISMATCH`.

```text
PRIOR_REAL_OUTCOME_ACCESS_STARTED = NO
PRIOR_OUTCOME_ATTEMPT_CONSUMED = NO
PRIOR_ATTEMPT_CLASS = PRE_OUTCOME_AUTHORITY_REJECTION
OUTPUT_ROOT_CREATED = NO
SCIENTIFIC_RESULT_CREATED = NO
```

The mismatch was configuration-dependent: Windows Git had
`core.autocrlf=true`; WSL Git had `core.autocrlf` unset. The canonical HEAD
script blob OID was `d5472605f4ae950adf5294e39ca9594d4bc80152`, while
ambient WSL worktree hashing produced
`e6b15cb15335a26fdf1a87e648ac2c54be9b6b67`.

## Thin correction

The worktree identity helper now invokes native Git with explicit clean-side
configuration:

```text
git -c core.autocrlf=input -c core.safecrlf=false hash-object --path=<repo-relative-path> <worktree-path>
```

This removes the ambient Windows/WSL configuration dependency without changing
repository configuration or redefining authority. Canonical tracked-text
authority remains SHA-256 of raw Git blob bytes. Raw worktree SHA remains
diagnostic only. Binary/data artifacts retain raw-file-byte SHA-256 authority.

The same deterministic rule applies to the execution script and provenance
seal. The runner additionally binds its actual runtime path: resolved
`Path(__file__)` must equal the resolved authorized repository script path.

## Regression evidence

A temporary Git fixture committed canonical LF text under
`core.autocrlf=true`, produced CRLF worktree copies, removed the repository
setting, and reproduced the ambient mismatch. The deterministic helper matched
the HEAD blob for both the runner and seal. LF worktrees also matched.

```text
SCRIPT_CROSS_GIT_CONFIG_MISMATCH_REGRESSION = PASS
SEAL_CROSS_GIT_CONFIG_MISMATCH_REGRESSION = PASS
LF_RUNTIME_REGRESSION = PASS
SCRIPT_LINE_ENDING_ONLY_DIFFERENCE_ACCEPTED = YES
SEAL_LINE_ENDING_ONLY_DIFFERENCE_ACCEPTED = YES
SCRIPT_REAL_CONTENT_MUTATION_REJECTION = PASS
SEAL_REAL_CONTENT_MUTATION_REJECTION = PASS
ACTUAL_RUNTIME_SCRIPT_PATH_BOUND = YES
RUNTIME_SCRIPT_PATH_MISMATCH_REJECTION = PASS
SUCCESSOR_RUNNER_TESTS = 32/32 PASS
ROUTER_AND_BOUNDARY_TESTS = 24/24 PASS
TEMPORAL_SPLIT_TESTS = 4/4 PASS
RUFF = PASS
```

## Preserved authority and next gate

The current real seal was not modified. The correction merge will make that
seal ineligible because its last-change commit will no longer equal HEAD. A
separate reseal must bind the correction merge commit and the new execution
script Git-blob SHA before any later real invocation.

```text
RAW_WORKTREE_SHA_USED_FOR_AUTHORIZATION = NO
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
REAL_SEAL_MODIFIED = NO
REAL_EXECUTE_INVOKED = NO
REAL_OUTCOME_ACCESS_STARTED = NO
CANDIDATE_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
OLS_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
LABEL_MAGNITUDES_ACCESSED = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_RESEAL_001
FINAL_CLASSIFICATION = PASS_CROSS_GIT_RUNTIME_TEXT_EQUIVALENCE_CORRECTED
```
