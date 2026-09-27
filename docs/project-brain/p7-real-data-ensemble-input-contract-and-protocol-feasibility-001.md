# P7 Real-data Ensemble Input Contract and Protocol Feasibility 001

## Result

This task performed bounded real-prediction input qualification only. It did
not call Qlib's ensemble on real inputs, train or refit a model, create a new
prediction, run a backtest, compute a performance metric, or access P2 V2
sealed OOS.

```text
BASE_MAIN = 6e513fcb196e8775945448ab69d2db2c3551b8bf
PR114_MERGED = YES
PR114_MERGE_SHA = 6e513fcb196e8775945448ab69d2db2c3551b8bf
FROZEN_CANDIDATE_ID_COUNT = 17
REAL_PREDICTION_VALUES_ACCESSED = YES_INPUT_QUALIFICATION_ONLY
INPUT_CONTRACT_STATUS = PARTIAL
P7_STATISTICAL_PROTOCOL_FROZEN = NO
P7_EXIT_CONDITION_SATISFIED = NO
FINAL_CLASSIFICATION = BLOCKED_P7_STRICT_REAL_INPUT_CONTRACT_AND_CONTROL_MATERIALIZATION_REQUIRED
```

## Frozen read scope

Before deserialization, the task froze exact paths, recorded SHA-256 values,
identities, declared intervals, permitted inspections and prohibited
operations. The selected-control scope contains the 17 native Candidate V3
prediction artifacts plus one pre-existing P2 historical-rehearsal OLS
control. A previously inspected P1 OLS potential control remains in the audit
trail and was rejected after its row-key intersection with the candidate
reference proved to be zero.

```text
SELECTED_READ_ALLOWLIST_ENTRY_COUNT = 18
SELECTED_READ_ALLOWLIST_SHA256 = bb23250cbd0edb803761c6f3660df2dbdaeb4694c684311a21ca71f57b4b6a68
CONTROL_SELECTION_METADATA_SHA256 = 02fb274e65fe9b3f69d65037080969f800bb10cfb792963f11b3b77c7279dda7
SELECTED_CONTRACT_PREDICTION_ARTIFACT_HASH_VERIFIED_COUNT = 18
TOTAL_UNIQUE_PREDICTION_ARTIFACTS_ACCESSED = 19
REJECTED_POTENTIAL_CONTROL_ARTIFACT_COUNT = 1
ORIGINAL_ARTIFACT_HASH_CHANGED_COUNT = 0
LABEL_OR_RETURN_ARTIFACTS_OPENED = 0
PERFORMANCE_ARTIFACTS_OPENED = 0
```

The 19 unique accesses comprise 17 candidates, the rejected P1 potential
control, and the selected P2 control; only the latter 18-entry candidate/P2
scope is the selected contract scope. Permitted inspection was limited to
`score` object/schema, ordered index
identity, key types, counts, missingness/non-finite checks, cross-sectional
readiness and byte-hash revalidation. No score value was exported. The real
`combine_complete_predictions()` boundary was not called.

## Candidate qualification

All 17 artifacts are single-column `score` DataFrames with a sorted
`(datetime, instrument)` MultiIndex. Each has 377,938 rows, 751 sessions,
559 distinct instruments, no duplicate or missing keys, no missing or
non-finite score, and 503 to 505 instruments per session. Their exact ordered
row identity is common:

```text
COMMON_ORDERED_ROW_IDENTITY_STATUS = PASS_CANDIDATES_17_OF_17
COMMON_ORDERED_INDEX_SHA256 = 44fe1aea7c3f51f9ed4711998b7612254cb8abf70a54ec6687ff9819c66fdd48
COMMON_CALENDAR_INTERVAL = 2022-01-03..2024-12-27
CANDIDATE_INTERSECTION_ROW_COUNT = 377938
CANDIDATE_UNION_ROW_COUNT = 377938
ROW_MISMATCH_COUNT = 0
DUPLICATE_KEY_COUNT = 0
MISSING_SCORE_COUNT = 0
NONFINITE_SCORE_COUNT = 0
```

The strict #114 boundary also requires every component to be nonconstant in
every session. Nine candidates pass that rule. Eight fail only that explicit
rule, with 385 candidate-session failures in total. No component was removed,
rescaled, sign-flipped, filled or silently subset.

| Candidate | prediction SHA-256 | rows | sessions | minimum members | constant sessions | strict boundary |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| candidate-001 | `6f94bbd7aa14e5b8abfd810b27cf0f10521d9d1a7f615470776ba5a13bfdd3ce` | 377938 | 751 | 503 | 0 | PASS |
| candidate-002 | `6cf5f69b5fb3358ec3725219806a55e44ae39cded37e98b45cc409225222e558` | 377938 | 751 | 503 | 0 | PASS |
| candidate-003 | `a5f8a0bf419a3cc10be5a2b2135703793649e4f698886a4c02dacdcbb7045bce` | 377938 | 751 | 503 | 0 | PASS |
| candidate-004 | `6d95d4910386802ec8bc0cd0495e6a4bb89b4703571c16f7c154152a8c24b092` | 377938 | 751 | 503 | 2 | FAIL_CONSTANT_CROSS_SECTION |
| candidate-005 | `51952a9d5ea12aae48df6121a6522f42e55ee53af767a1af40eed30e945676a9` | 377938 | 751 | 503 | 3 | FAIL_CONSTANT_CROSS_SECTION |
| candidate-006 | `891327baf5c52a6ee8f5c9da043070ac7c54d48bdd6aa62c628909de1395a2b7` | 377938 | 751 | 503 | 0 | PASS |
| candidate-007 | `dd732208e18da7c1ae26cb27872e9befef6eb5abf395230dc1a9c5ab5b2d5012` | 377938 | 751 | 503 | 0 | PASS |
| candidate-008 | `86be2394545bb84a092e64153b1ad335969d4776860422b47a65b49f9ab89f76` | 377938 | 751 | 503 | 0 | PASS |
| candidate-009 | `2c7bdae6db795d1fc2b1736e7bba09af7dfafc9bba1e51e92b37bda72548b017` | 377938 | 751 | 503 | 0 | PASS |
| candidate-010 | `c5c735400f843049a49dc04095f417f0ac25991bf1bf51137140d0beee77039f` | 377938 | 751 | 503 | 2 | FAIL_CONSTANT_CROSS_SECTION |
| candidate-011 | `d5a5a506fec62ef76c76757cf574e3c89eb15434b0f77741bc57458067f5f6a4` | 377938 | 751 | 503 | 0 | PASS |
| candidate-012 | `056d2d66cc84e674789939fc4f4f601a85f15ddf9eab82251ac98fc320c57865` | 377938 | 751 | 503 | 113 | FAIL_CONSTANT_CROSS_SECTION |
| candidate-013 | `f86a5906821697852e347fa7f60cd393b2c043d717f8861fc4516d896cc1f41a` | 377938 | 751 | 503 | 0 | PASS |
| candidate-014 | `fe9cbbdfa2c70fd1a497051ee1089e54db61718f6efaea782cb8de362ef6ffd3` | 377938 | 751 | 503 | 86 | FAIL_CONSTANT_CROSS_SECTION |
| candidate-015 | `bc3b23a4e44bfacc2686142690303f8a7a4efb15b38fcb054465000dae02b679` | 377938 | 751 | 503 | 1 | FAIL_CONSTANT_CROSS_SECTION |
| candidate-016 | `570320e758cd3ea278613189bd89f2a5d28fdf33d697160f446f7aa9cb1fc01c` | 377938 | 751 | 503 | 113 | FAIL_CONSTANT_CROSS_SECTION |
| candidate-017 | `46e12a561f33f4ada8b15069263823e1cc436c65e02bacea7f4748d738793d88` | 377938 | 751 | 503 | 65 | FAIL_CONSTANT_CROSS_SECTION |

```text
STRICT_PR114_BOUNDARY_PASS_COUNT = 9
STRICT_PR114_BOUNDARY_FAIL_COUNT = 8
CONSTANT_COMPONENT_SESSION_COUNT = 385
```

## Explicit control binding

The selected control is the pre-existing P2 historical-rehearsal OLS artifact,
not P5 LightGBM and not the methodologically incompatible P1 broad-market
artifact. The selection used only configuration and lineage facts:

```text
CONTROL_RECIPE_IDENTIFIED = YES
CONTROL_MODEL_IDENTITY = qlib.contrib.model.linear.LinearModel(estimator=ols)
CONTROL_MODEL_CONFIG_IDENTITY = sha256:b9a92537a9737ce909284e77e583ad20c0a3d2b18f795271d85db6c5ba5eafc1
CONTROL_FIT_POLICY = TRAIN_ONLY
CONTROL_LABEL = Ref($close, -2)/Ref($close, -1) - 1
CONTROL_LABEL_LOOKAHEAD_SESSIONS = 2
CONTROL_DATASET_UNIVERSE = P2_FROZEN_RAGGED_PANEL / p2_pit
CONTROL_RECORDER_ID = d6035e318a0640da876e52d587137e7c
CONTROL_PREDICTION_ARTIFACT_BOUND = YES
CONTROL_PREDICTION_SHA256 = 26c3433faa58a64914393fe13eac169d9ce86dbbe86f16dfb2b24fbd64139dab
PERFORMANCE_USED_FOR_CONTROL_SELECTION = NO
```

The bound artifact is a named `score` Series, while #114 accepts exactly a
one-column `score` DataFrame. It has 375,597 rows over 753 sessions and is
individually finite, nonconstant and duplicate-free. It is nevertheless not
strictly compatible with the candidates:

```text
CONTROL_ACTUAL_OBJECT_TYPE = Series
CONTROL_STRICT_SHAPE_STATUS = FAIL_NOT_DATAFRAME
CONTROL_COMMON_CALENDAR_INTERVAL = 2022-01-03..2024-12-27
CONTROL_CANDIDATE_INTERSECTION_ROW_COUNT = 374591
CANDIDATE_ONLY_ROW_COUNT = 3347
CONTROL_ONLY_ROW_COUNT = 1006
CONTROL_EXACT_ORDERED_ROW_IDENTITY = NO
CONTROL_REAL_INPUT_COMPATIBILITY_VERIFIED = FAIL
REDUCED_COMMON_SUPPORT_MATERIALIZED = NO
```

This is a verified incompatibility, not a missing artifact. The task did not
silently convert the Series, intersect rows or generate replacement control
predictions.

## Synthetic statistical feasibility

Only the verified 751-session candidate calendar and synthetic zero arrays
entered skfolio 1.0.6. No prediction values, outcomes or returns entered the
splitters. The proposal uses purge 2 to match the frozen two-session label
horizon; it is feasibility evidence, not a frozen P7 protocol.

```text
WALKFORWARD_PROPOSAL = train_size=504,test_size=63,purged_size=2,expand_train=False,reduce_test=False
WALKFORWARD_USABLE_FOLD_COUNT = 3
WALKFORWARD_COMPLETE_TEST_FOLDS = YES
WALKFORWARD_UNUSED_TRAILING_SESSION_COUNT = 56
CPCV_PROPOSAL = n_folds=10,n_test_folds=2,purged_size=2,embargo_size=2
CPCV_USABLE_SPLIT_COUNT = 45
CPCV_TRAIN_COUNT_RANGE = 589..598
CPCV_TEST_COUNT_RANGE = 150..151
TRAIN_TEST_OVERLAP_COUNT = 0
SPLIT_FEASIBILITY_RESULT = PASS_SYNTHETIC_MECHANICS_ON_VERIFIED_751_SESSION_LENGTH
P7_STATISTICAL_PROTOCOL_FROZEN = NO
```

The WalkForward folds end on 2024-04-09, 2024-07-10 and 2024-10-08.
Temporal robustness partitions an existing return series; it is not rolling
model refitting and does not create prospective predictions.

## Readiness and immutable boundaries

```text
HISTORICAL_PREDICTION_REUSE_READINESS = PARTIAL
MODEL_PERSISTENCE_STATUS = CANDIDATES_NOT_PERSISTED_17_OF_17;CONTROL_MODEL_BYTES_NOT_BOUND
PROSPECTIVE_PREDICTION_READINESS = NO_REFIT_OR_NEW_PREDICTION_AUTHORIZED
SIGNAL_COMPLEMENTARITY = NOT_YET_EVALUATED
REAL_MODEL_TRAINING_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_ENSEMBLE_EXECUTION_COUNT = 0
BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
ENVIRONMENT_MUTATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_RESEARCH_RUNTIME_LOC = 0
NEW_TEST_LOC = 0
NEW_PRODUCTION_LOC = 0
```

Private evidence is under
`D:/AQ_DATA/P7/real-data-ensemble-input-contract-and-protocol-feasibility-001`.
The partial contract evidence SHA-256 is
`90fe25244461b628dacb83632af4e0330a927a5f43444f11770c08c0dec267c8`;
because the contract is not complete, no complete input-contract identity is
claimed. The private evidence manifest SHA-256 is
`57b59aab2e85a6e7b6f219aebb9d4ba381e958e6264a921d9d6d2e5f05bcc6eb`.

## Next

The smallest bounded next task must resolve the strict nonconstant-component
authority and define/materialize one exact candidate-compatible OLS control
shape and row identity before any protocol freeze. It must not execute an
ensemble or choose a subset using observed performance.

```text
CURRENT_DEVELOPMENT_NEXT = P7_REAL_DATA_ENSEMBLE_INPUT_AND_CONTROL_CONTRACT_CLOSEOUT_001
```
