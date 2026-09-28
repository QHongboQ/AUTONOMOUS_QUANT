# P7 Successor One-Shot Execution Provenance Reseal 001

Date: 2026-09-27

Status: `PASS_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_RESEALED_PRE_MERGE`

## Execution authority

PR #134 merged the deterministic cross-Git text-equivalence correction as
`3c46824c2865a8b8f938e0ff75e840b6de03fa14`. Independent raw Git-blob hashing
of the merged runner produced the required identity:

```text
PRIOR_SEAL_EXECUTION_CODE_COMMIT_SHA = e7f3a64fb4b0178bd7f21a886b591ef20d2d48db
NEW_SEAL_EXECUTION_CODE_COMMIT_SHA = 3c46824c2865a8b8f938e0ff75e840b6de03fa14
PRIOR_SEAL_EXECUTION_SCRIPT_SHA256 = 0f11cba636d2db5849d7caf327c73f1063d0c053dcb35884406287344d714f3a
NEW_SEAL_EXECUTION_SCRIPT_SHA256 = 3349177fbff145111312819082ea2359a6b867e8419006abe6c0dfee2644bb70
TRACKED_TEXT_CANONICAL_IDENTITY = SHA256_OF_RAW_GIT_BLOB_BYTES
DETERMINISTIC_CLEAN_FILTER_MODE = GIT_CORE_AUTOCRLF_INPUT_SAFECRLF_FALSE
ACTUAL_RUNTIME_SCRIPT_PATH_BOUND = YES
```

The existing tracked seal was updated in place. It still contains no
self-referential authority commit. Runtime derives the seal authority from Git
history and requires HEAD to equal origin/main, the seal's last-change commit
to equal HEAD, deterministically cleaned worktree text to match HEAD blobs, and
the sealed execution-code commit to be an ancestor of HEAD.

## Preserved scientific and artifact authority

Every field other than the two execution identities remains unchanged.
Hash-only verification matched all 17 Candidate artifacts plus the OLS
control, Qlib label, construction population, and evaluation population.
Candidate/control prediction values and label magnitudes were not opened.

```text
SUCCESSOR_PROTOCOL_SHA256 = cb61628ed49ca0f9d9798f92567adedbeb533f6854da098ec3c945b38bdbd76a
SUCCESSOR_INPUT_CONTRACT_SHA256 = b9e0c447794c318d7ddc00803e0f2ea5468abc4c77a43752ead2910804b8a7b5
SIGNAL_CONSTRUCTION_POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
EVALUATION_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
LABEL_VALIDITY_MASK_SHA256 = 2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
CANDIDATE_ARTIFACT_COUNT = 17
CANDIDATE_ARTIFACT_BINDINGS_UNCHANGED = YES
OLS_ARTIFACT_SHA256 = 26c3433faa58a64914393fe13eac169d9ce86dbbe86f16dfb2b24fbd64139dab
LABEL_ARTIFACT_SHA256 = c14c7c3f1e698126663b85dfcf436cf3258dc4609e8217e95ed188d9be7db35e
SIGNAL_CONSTRUCTION_POPULATION_ARTIFACT_SHA256 = c2677441b7ce4d4b001f5cb9f51c032fbb85d7a2163e0d80feaaf65e8e160dc6
EVALUATION_POPULATION_ARTIFACT_SHA256 = 5f240cb9d88a318047d597c2ed11c1356eebc60fe0b59ae982d347089dcf4c38
```

## Pre-merge execution state

This reseal is not execution-authoritative while its PR remains open. The
prior invocation was a pre-outcome authority rejection and consumed no
scientific attempt.

```text
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
RAW_WORKTREE_SHA_USED_FOR_AUTHORIZATION = NO
REAL_EXECUTION_READY = NO_PENDING_RESEAL_PR_MERGE
REAL_EXECUTE_INVOKED = NO
REAL_OUTCOME_ACCESS_STARTED = NO
CANDIDATE_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
OLS_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
LABEL_MAGNITUDES_ACCESSED = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
PRIOR_EXECUTION_REJECTION = WORKTREE_SCRIPT_HEAD_MISMATCH
PRIOR_OUTCOME_ATTEMPT_CONSUMED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_ONE_SHOT_EXECUTION_002
FINAL_CLASSIFICATION = PASS_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_RESEALED_PRE_MERGE
```

After this reseal merges, no other main commit may land before execution. A
later main commit invalidates the seal and requires another reseal.
