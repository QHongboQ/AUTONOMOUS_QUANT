# P7 Successor One-Shot Execution Code Precommit and Preflight Freeze 001

Date: 2026-09-27

Status: `PASS_SUCCESSOR_ONE_SHOT_EXECUTION_CODE_PRECOMMITTED_AND_SYNTHETICALLY_VALIDATED`

## Authority

PR #129 is merged at exact baseline
`e98256f17b2391943e4c3f38414d34db98da04b1`. This task adds the bounded
successor-specific research orchestration and synthetic tests without changing
either frozen successor authority:

```text
SUCCESSOR_PROTOCOL_SHA256 = a4ca307c3e3a245bb211978d36f03d8a2552c81df28049ddb6b667231689a894
SUCCESSOR_INPUT_CONTRACT_SHA256 = b693f43b8dfab0fa04cb12a876fc32928bc5020592a2e137f1c0cbfdde0639ee
SUCCESSOR_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
LABEL_VALIDITY_MASK_SHA256 = 2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf
```

The execution script loads these authorities, verifies their RFC8785
identities first, and derives Candidate, control, population, label, ensemble,
statistics, temporal-partition, portfolio and classification semantics from
them. It consumes the frozen population rather than reconstructing it.
Existing `session_local_router.py` and `average_ensemble_boundary.py` remain
the thin AQ boundary around Qlib `AverageEnsemble`.

## Hard execution firewall

Real execution requires the separately tracked
`successor-one-shot-execution-provenance-seal.json`. That file does not exist.
The real entry therefore fails as `EXECUTION_PROVENANCE_SEAL_MISSING` before
creating an output root or deserializing any prediction or label value.

The future seal must bind the merged execution-code commit, external script
SHA, protocol/input/population/mask identities, Qlib source, dependency
versions, exact Candidate/control/label/population artifacts, and a separate
authority commit. The script also requires a clean worktree, exact authorized
HEAD, and both commits in `origin/main` ancestry.

The one-shot state machine writes its attempt manifest and
`OUTCOME_ACCESS_STARTED` marker before real value deserialization. An existing
marker rejects all retries. A post-marker exception seals
`STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE` and still rejects retry. No recursive
self-hash is embedded in the script; the later external seal owns its content
identity.

```text
EXECUTION_SCRIPT_PATH = 30-research-system/qlib/p7-native-ensemble/execute_successor_historical_static_research.py
EXECUTION_SCRIPT_SHA256 = 12ec3ad8df9b6b053356ccf7997d41f21b1d98863a33cbe80ae9a3bb76aecf95
REAL_EXECUTION_PROVENANCE_SEAL_PRESENT = NO
REAL_EXECUTION_READY = NO_PENDING_POST_MERGE_PROVENANCE_SEAL
```

## Synthetic validation

All validation used synthetic inputs or metadata identities only. The exact
frozen upstream APIs passed:

```text
SYNTHETIC_QLIB_ENSEMBLE = PASS
SYNTHETIC_QLIB_RANKIC = PASS
SYNTHETIC_QLIB_PORTFOLIO_PATH = PASS
SYNTHETIC_SPA_STATUS = PASS_LOWER_CONSISTENT_UPPER
SYNTHETIC_MCS_STATUS = PASS_18_COLUMNS
SYNTHETIC_WALKFORWARD_FOLD_COUNT = 3
SYNTHETIC_CPCV_SPLIT_COUNT = 45
MISSING_SEAL_REJECTION = PASS
PROTOCOL_MISMATCH_REJECTION = PASS
INPUT_CONTRACT_MISMATCH_REJECTION = PASS
SCRIPT_HASH_MISMATCH_REJECTION = PASS
DIRTY_WORKTREE_REJECTION = PASS
HEAD_AUTHORITY_REJECTION = PASS
SECOND_ATTEMPT_REJECTION = PASS
POST_MARKER_FAILURE_SEAL_STATUS = PASS_FAILED_SEALED_INCONCLUSIVE
```

Focused successor/firewall, Qlib boundary/router, and temporal-split tests all
passed. Ruff and `git diff --check` passed. The execution entry has 847 physical
lines and the focused test module has 190 physical lines. Both are research
scope; production LOC remains zero. No generic engine was created.

## Safety and routing

```text
REAL_OUTCOME_ACCESS_STARTED = NO
CANDIDATE_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
OLS_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
LABEL_MAGNITUDES_ACCESSED = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_RESEARCH_EXECUTION_LOC = 847
NEW_TEST_LOC = 190
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_SEAL_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_ONE_SHOT_EXECUTION_CODE_PRECOMMITTED_AND_SYNTHETICALLY_VALIDATED
```
