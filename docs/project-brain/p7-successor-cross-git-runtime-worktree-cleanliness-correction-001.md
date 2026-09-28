# P7 Successor Cross-Git Runtime Worktree Cleanliness Correction 001

Date: 2026-09-27

Status: `PASS_CROSS_GIT_RUNTIME_WORKTREE_CLEANLINESS_CORRECTED`

## Pre-outcome history

Both successor invocations rejected before outcome access and consumed no
scientific attempt:

```text
EXECUTION_001_REJECTION = WORKTREE_SCRIPT_HEAD_MISMATCH
EXECUTION_002_REJECTION = DIRTY_WORKTREE_FORBIDDEN
EXECUTION_001_CLASS = PRE_OUTCOME_AUTHORITY_REJECTION
EXECUTION_002_CLASS = PRE_OUTCOME_AUTHORITY_REJECTION
PRIOR_REAL_OUTCOME_ACCESS_STARTED = NO
PRIOR_SCIENTIFIC_ATTEMPT_COUNT = 0
PRIOR_OUTPUT_ROOT_CREATED = NO
```

Execution 002 passed the deterministic script/seal blob checks and actual
runtime path binding. It failed because `runtime.worktree_clean` still used
ambient WSL `git status`, which treated the Windows CRLF checkout as 385
modifications. The same status command under the already-frozen clean-side Git
configuration returned zero entries.

## Thin deterministic correction

The runner now defines one shared native-Git configuration:

```text
DETERMINISTIC_TEXT_GIT_CONFIG =
  -c core.autocrlf=input
  -c core.safecrlf=false
```

It is used by both worktree blob hashing and:

```text
git status --porcelain=v1 -z --untracked-files=all
```

No repository, local, or global Git configuration is mutated. Ambient status
is diagnostic only and cannot authorize or reject execution.

## Regression evidence

A realistic temporary repository committed canonical LF text with
`core.autocrlf=true`, produced CRLF worktree text, and then removed that local
setting to simulate WSL. Ambient status reported false modifications, while the
deterministic status was empty and the complete runtime authority validation
passed.

Separate fixtures proved true dirtiness remains fail-closed:

```text
CROSS_GIT_AMBIENT_STATUS_FALSE_DIRTY_REGRESSION = PASS
DETERMINISTIC_STATUS_LINE_ENDING_ONLY_CLEAN = PASS
DETERMINISTIC_STATUS_REAL_CONTENT_MUTATION_DIRTY = PASS
DETERMINISTIC_STATUS_STAGED_CHANGE_DIRTY = PASS
DETERMINISTIC_STATUS_UNTRACKED_FILE_DIRTY = PASS
SCRIPT_CROSS_GIT_CONFIG_MISMATCH_REGRESSION = PASS
SEAL_CROSS_GIT_CONFIG_MISMATCH_REGRESSION = PASS
RUNTIME_SCRIPT_PATH_MISMATCH_REJECTION = PASS
SUCCESSOR_RUNNER_TESTS = 36/36 PASS
ROUTER_AND_BOUNDARY_TESTS = 24/24 PASS
TEMPORAL_SPLIT_TESTS = 4/4 PASS
RUFF = PASS
```

## Preserved authority

The real seal remains byte-identical to main at Git blob
`bfa8d0d510c09b4636820b5724cc0861eb9b6a32`. The canonical raw Git-blob text
identity, actual runtime script path gate, execution ancestry, dependency,
Qlib, scientific, and raw-byte data-artifact authorities are unchanged.

```text
ACTUAL_RUNTIME_SCRIPT_PATH_BOUND = YES
REAL_SEAL_MODIFIED = NO
RAW_WORKTREE_SHA_USED_FOR_AUTHORIZATION = NO
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
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
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_RESEAL_002
FINAL_CLASSIFICATION = PASS_CROSS_GIT_RUNTIME_WORKTREE_CLEANLINESS_CORRECTED
```
