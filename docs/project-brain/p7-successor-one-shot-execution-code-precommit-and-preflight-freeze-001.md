# P7 Successor One-Shot Execution Code Rebase After Boundary Correction 001

Date: 2026-09-27

Status: `PASS_SUCCESSOR_EXECUTION_CODE_REBASED_AFTER_BOUNDARY_CORRECTION`

## Corrected authority

The open PR #130 execution code is rebased onto the PR #131 authority merged at
`fea869c3138033266258de76bffd8bd7bf60574d`. It now binds the corrected RFC8785
identities:

```text
SUCCESSOR_PROTOCOL_SHA256 = cb61628ed49ca0f9d9798f92567adedbeb533f6854da098ec3c945b38bdbd76a
SUCCESSOR_INPUT_CONTRACT_SHA256 = b9e0c447794c318d7ddc00803e0f2ea5468abc4c77a43752ead2910804b8a7b5
SIGNAL_CONSTRUCTION_POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
SIGNAL_CONSTRUCTION_ROW_COUNT = 374591
EVALUATION_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
EVALUATION_ROW_COUNT = 374477
LABEL_VALIDITY_MASK_SHA256 = 2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf
```

The prior script identity
`12ec3ad8df9b6b053356ccf7997d41f21b1d98863a33cbe80ae9a3bb76aecf95`
is retired and cannot be used by a future provenance seal. The corrected
script identity is
`996a9fe439651ef377337405fac85449bd8abd1d82851b9fc79e69536a03267b`.

## Scientific boundary

Candidate predictions are first projected to the complete 374,591-row signal
construction population. The session-local constant/numeric policy and Qlib
`AverageEnsemble` run there. Only the resulting full-population ensemble signal
is projected to the 374,477-row label-observable evaluation population.
Candidate evaluation signals, the OLS control, and the Qlib label are then
projected directly to that evaluation population.

The label mask is never used to choose rows before `AverageEnsemble` and never
selects portfolio signals. Portfolio projection consumes the complete
construction-population ensemble signal.

## Primary and secondary evidence

Primary ensemble and OLS daily RankIC remain strict across all 751 sessions.
Mean delta, SPA, WalkForward, and CPCV mechanically determine the six-gate
primary classification. Once that evidence is complete, the primary
classification is locked.

Individual component RankIC may be unavailable for exact-constant
Candidate/session pairs. Summaries use finite component sessions only and do
not impute zero. If any entry in the exact ensemble-plus-17-component MCS loss
matrix is unavailable, MCS is not run and reports
`NOT_AVAILABLE_SECONDARY_INCOMPLETE_LOSS_MATRIX`. Component-summary, MCS,
portfolio, and post-primary MLflow lineage failures are secondary and cannot
change a locked primary result. Input identity, signal construction, primary
RankIC/statistics, and required result-integrity failures remain fail-closed
and seal the one-shot attempt as inconclusive.

## One-shot firewall and synthetic validation

The future seal model separately binds byte identities for
`artifacts.signal_construction_population` and
`artifacts.evaluation_population`, plus the 17 Candidate, OLS, and label
artifacts. Runtime verifies both semantic ordered-index identities. Missing
seal, tracked-seal, protocol/contract/population/mask/script hashes, clean
worktree, commit ancestry, HEAD authority, artifact byte hashes, pre-value
marker, and second-attempt rejection remain enforced.

Synthetic-only validation proved:

```text
SYNTHETIC_CONSTRUCTION_EVALUATION_BOUNDARY_TEST = PASS
SYNTHETIC_CONSTANT_COMPONENT_TEST = PASS
SYNTHETIC_MCS_INCOMPLETE_TEST = PASS
SYNTHETIC_PORTFOLIO_FAILURE_TEST = PASS
SYNTHETIC_LINEAGE_FAILURE_TEST = PASS
SYNTHETIC_REQUIRED_FAILURE_INCONCLUSIVE_TEST = PASS
SYNTHETIC_QLIB_ENSEMBLE = PASS
SYNTHETIC_QLIB_RANKIC = PASS
SYNTHETIC_QLIB_PORTFOLIO_PATH = PASS
SYNTHETIC_SPA_STATUS = PASS_LOWER_CONSISTENT_UPPER
SYNTHETIC_MCS_STATUS = PASS_18_COLUMNS
SYNTHETIC_WALKFORWARD_FOLD_COUNT = 3
SYNTHETIC_CPCV_SPLIT_COUNT = 45
```

No real Candidate predictions, OLS predictions, label magnitudes, ensemble,
RankIC, portfolio result, or performance metric were opened or computed.

## Safety and routing

```text
REAL_EXECUTION_PROVENANCE_SEAL_PRESENT = NO
REAL_EXECUTION_READY = NO_PENDING_POST_MERGE_PROVENANCE_SEAL
EXECUTION_SCRIPT_SHA256 = 996a9fe439651ef377337405fac85449bd8abd1d82851b9fc79e69536a03267b
REAL_OUTCOME_ACCESS_STARTED = NO
CANDIDATE_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
OLS_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
LABEL_MAGNITUDES_ACCESSED = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_RESEARCH_EXECUTION_LOC = 1134
NEW_TEST_LOC = 339
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_SEAL_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_EXECUTION_CODE_REBASED_AFTER_BOUNDARY_CORRECTION
```
