# P7 Successor Git-Canonical Text-Byte Identity Correction 001

Date: 2026-09-27

Status: `PASS_GIT_CANONICAL_TEXT_BYTE_IDENTITY_CORRECTED`

## Baseline finding

PR #130 merged as `62c9a6d7c94598d46198af26118e29ed69346205`.
The tracked execution script at that commit has two different physical
representations under the repository's Windows checkout configuration:

```text
GIT_CANONICAL_BLOB_BYTES = 47464
GIT_CANONICAL_BLOB_SHA256 = 5f4f43b8cf1096e1def491722cd776abf5cd3e4e8d20cde5eeb2c59a0ec3eaf9
RAW_WINDOWS_WORKTREE_BYTES = 48122
RAW_WINDOWS_WORKTREE_SHA256 = a1a666cba8b8d7162f52cf24c24b9ec58f0463750ea424eaa716c931158d875f
CORE_AUTOCRLF = true
```

The difference is checkout line-ending transformation, not tracked content.
The former runtime incorrectly required both raw byte identities to be equal.

## Corrected authority

For the tracked execution script and tracked provenance seal:

```text
TRACKED_TEXT_CANONICAL_IDENTITY = SHA256_OF_RAW_GIT_BLOB_BYTES
RAW_WORKTREE_SHA_USED_FOR_AUTHORIZATION = NO
```

The future `execution_script_sha256` means the SHA-256 of raw bytes returned by
`git show <execution-code-commit>:<execution-script-path>`. Runtime verifies
that identity independently at the sealed execution commit and current
`HEAD`. It does not compare the seal to raw checkout bytes.

Working-tree equivalence uses Git's native path filters:

```text
git hash-object --path=<repo-relative-path> <worktree-path>
==
git rev-parse HEAD:<repo-relative-path>
```

The same rule applies to the tracked seal. Raw worktree script SHA-256 remains
available only as descriptive pre-outcome diagnostics. Binary/data artifact
hashes remain raw file-byte SHA-256 and are unchanged.

## Preserved gates

The correction retains:

- `HEAD == origin/main`;
- clean worktree;
- tracked seal and `seal last-change commit == HEAD`;
- no self-referential `authority_commit_sha`;
- execution-code commit ancestry to `HEAD` and `origin/main`;
- sealed dependencies and runtime version equality;
- Qlib source identity;
- protocol, input-contract, construction/evaluation population, and label-mask identities.

Because the runner changes in this branch, the later seal must bind the future
merge commit and the execution-script Git-blob SHA calculated from that merge.
Neither value is frozen before merge.

## Regression evidence

A temporary Git repository with `core.autocrlf=true` proved:

```text
AUTOCRLF_SCRIPT_REGRESSION = PASS
AUTOCRLF_SEAL_REGRESSION = PASS
RAW_WORKTREE_SHA_DIFFERS_FROM_GIT_BLOB_SHA = YES
WORKTREE_SCRIPT_GIT_EQUIVALENT_TO_HEAD = YES
WORKTREE_SEAL_GIT_EQUIVALENT_TO_HEAD = YES
SCRIPT_REAL_CONTENT_MUTATION_REJECTION = PASS
SEAL_REAL_CONTENT_MUTATION_REJECTION = PASS
LATER_UNRELATED_COMMIT_REJECTION = PASS
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
```

The successor runner/router/boundary suite passed 53 tests. The temporal split
suite passed 4 tests. No dependency or environment was changed.

## Safety and next task

```text
REAL_PROVENANCE_SEAL_CREATED = NO
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
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_SEAL_001
FINAL_CLASSIFICATION = PASS_GIT_CANONICAL_TEXT_BYTE_IDENTITY_CORRECTED
```
