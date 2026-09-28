# P7 Successor One-Shot Execution Provenance Seal 001

Date: 2026-09-27

Status: `PASS_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_SEAL_FROZEN_PRE_MERGE`

## Authority

PR #132 merged the Git-canonical tracked-text correction as
`e7f3a64fb4b0178bd7f21a886b591ef20d2d48db`. The execution script's raw Git
blob identity at that commit is:

```text
EXECUTION_CODE_COMMIT_SHA = e7f3a64fb4b0178bd7f21a886b591ef20d2d48db
EXECUTION_SCRIPT_GIT_BLOB_SHA256 = 0f11cba636d2db5849d7caf327c73f1063d0c053dcb35884406287344d714f3a
TRACKED_TEXT_CANONICAL_IDENTITY = SHA256_OF_RAW_GIT_BLOB_BYTES
RAW_WORKTREE_SCRIPT_SHA_IN_SEAL = NO
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
```

The seal is located at
`30-research-system/qlib/p7-native-ensemble/successor-one-shot-execution-provenance-seal.json`.
It contains exactly the authority fields expected by the merged runner and no
self-referential commit identity.

## Frozen identities

```text
SUCCESSOR_PROTOCOL_SHA256 = cb61628ed49ca0f9d9798f92567adedbeb533f6854da098ec3c945b38bdbd76a
SUCCESSOR_INPUT_CONTRACT_SHA256 = b9e0c447794c318d7ddc00803e0f2ea5468abc4c77a43752ead2910804b8a7b5
SIGNAL_CONSTRUCTION_POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
EVALUATION_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
LABEL_VALIDITY_MASK_SHA256 = 2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
EXPECTED_DEPENDENCY_VERSIONS = {qlib: 0.9.8.dev26, arch: 8.0.0, skfolio: 1.0.6}
```

## Artifact verification

Hash-only verification matched all 17 frozen Candidate source prediction
artifacts, the OLS control, Qlib label, construction population, and evaluation
population. Candidate, control, and label objects were not deserialized.

```text
CANDIDATE_ARTIFACT_COUNT = 17
CANDIDATE_ARTIFACT_HASH_VERIFIED_COUNT = 17
OLS_ARTIFACT_SHA256 = 26c3433faa58a64914393fe13eac169d9ce86dbbe86f16dfb2b24fbd64139dab
LABEL_ARTIFACT_SHA256 = c14c7c3f1e698126663b85dfcf436cf3258dc4609e8217e95ed188d9be7db35e
SIGNAL_CONSTRUCTION_POPULATION_ARTIFACT_SHA256 = c2677441b7ce4d4b001f5cb9f51c032fbb85d7a2163e0d80feaaf65e8e160dc6
EVALUATION_POPULATION_ARTIFACT_SHA256 = 5f240cb9d88a318047d597c2ed11c1356eebc60fe0b59ae982d347089dcf4c38
SIGNAL_CONSTRUCTION_POPULATION_ROW_COUNT = 374591
EVALUATION_POPULATION_ROW_COUNT = 374477
POPULATION_ORDERED_INDEX_VERIFICATION = PASS_KEYS_ONLY
QLIB_PROVIDER_PATH_EXISTS = YES
RUNNER_STATIC_HASH_ONLY_VALIDATION = PASS
```

## Pre-merge execution state

The real seal is tracked by this branch but cannot authorize execution until
this PR itself is merged. Runtime requires both `HEAD == origin/main` and seal
last-change commit equal to `HEAD`.

After this seal PR is merged, **no other commit may land on main before the
one-shot execution**. Any later main commit makes this seal runtime-ineligible
and requires a new seal authority commit.

```text
REAL_EXECUTION_READY = NO_PENDING_SEAL_PR_MERGE
REAL_EXECUTE_INVOKED = NO
REAL_OUTCOME_ACCESS_STARTED = NO
CANDIDATE_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
OLS_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
LABEL_MAGNITUDES_ACCESSED = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_ONE_SHOT_EXECUTION_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_SEAL_FROZEN_PRE_MERGE
```
