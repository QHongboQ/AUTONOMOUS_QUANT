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

---

## Closeout and superseding input policy

The original qualification above remains historical evidence. This closeout
supersedes only its partial input-contract conclusion. It did not call Qlib's
ensemble on real scores, train or refit a model, generate a prediction, compute
performance, run a backtest, change a P2 cohort, or access sealed OOS.

Before the additional reads, the task froze an expanded 753-path allowlist:
18 prediction artifacts, five historical membership/identity authorities, and
730 contemporaneous close-availability files. The frozen allowlist SHA-256 is
`8f8aab65cebb5571d7e3c2cd548c39bc5847d7d846a9a8d3eadca43c2b859089`.
The source code confirms that the P2 control TEST ends on 2024-12-31, the P3
two-session label-safe prediction interval ends on 2024-12-27, and the control
handler applies Qlib's `ExpressionDFilter` through `current_close_filter()`.

The selected control Series was converted losslessly with
`Series.to_frame(name="score")` and stored separately. Its index and order,
dtype, values, and missingness are unchanged; the original artifact still
hashes to
`26c3433faa58a64914393fe13eac169d9ce86dbbe86f16dfb2b24fbd64139dab`.

### Exhaustive row accounting

All 4,353 symmetric-difference rows have mutually exclusive explanations:

```text
OUTSIDE_DECLARED_COMMON_DATE_WINDOW = 1006
EXPLAINED_BY_HISTORICAL_MEMBERSHIP_IDENTITY = 3316
EXPLAINED_BY_CURRENT_CLOSE_AVAILABILITY_RULE = 31
UNEXPLAINED_ROW_COUNT = 0
```

The 1,006 control-only rows are on 2024-12-30 and 2024-12-31, after the
candidate label-safe end. The 3,347 candidate-only rows consist of 2,360
`NO_PROVIDER_ASSET`, 21 `IDENTITY_AMBIGUOUS`, 935
`TERMINAL_POLICY_UNRESOLVED`, 30 `KNOWN_PROVIDER_GAP`, and one
`KNOWN_TERMINAL_SESSION_PROVIDER_GAP`. The availability grid equals the
explicit historical membership grid; every row is backed by date-valid
episode and identity evidence. The Qlib current-close-filtered grid equals the
rows classified as contemporaneously observed.

### Complete population contract

Conditions A-D passed independently of the prediction-file intersection. The
frozen population rule is:

```text
FINAL_POPULATION_RULE = P2_HISTORICAL_MEMBERSHIP_AND_QLIB_CURRENT_CLOSE_AVAILABLE_WITHIN_P3_TWO_SESSION_LABEL_SAFE_INTERVAL
FINAL_POPULATION_ROW_COUNT = 374591
FINAL_POPULATION_SESSION_COUNT = 751
FINAL_POPULATION_INSTRUMENT_COUNT = 547
FINAL_POPULATION_START = 2022-01-03
FINAL_POPULATION_END = 2024-12-27
FINAL_POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
SOURCE_CANDIDATE_ROWS_EXCLUDED = 3347
SOURCE_CONTROL_ROWS_EXCLUDED = 1006
INPUT_CONTRACT_STATUS = COMPLETE
INPUT_CONTRACT_SHA256 = 92de81d0b8b7b7a29891bf523ae8519af44456f52fea3410ebf0ebd210d0f81f
ORIGINAL_ARTIFACT_HASH_CHANGED_COUNT = 0
```

All 17 candidates and the selected OLS control cover this exact ordered grid.
The derived views are private research inputs with explicit source identities;
they do not change P2 populations or source artifacts.

### Session-local qualification policy

All 17 Candidate V3 identities remain in the master roster. The closeout
policy is `SESSION_LOCAL_NONCONSTANT_COMPONENT_EQUAL_WEIGHT`: exact constants
are inactive only on the current session, while missing or non-finite scores
remain errors. At least two active components are mandatory. Qlib's pinned
`AverageEnsemble` remains the owner of standardization and equal averaging.

```text
MASTER_CANDIDATE_COUNT = 17
INACTIVE_CANDIDATE_SESSION_COUNT = 2575
UNIQUE_AFFECTED_SESSION_COUNT = 736
MINIMUM_ACTIVE_COMPONENT_COUNT = 8
MAXIMUM_ACTIVE_COMPONENT_COUNT = 17
ACTIVE_COMPONENT_COUNT_DISTRIBUTION = 8:1,9:37,10:93,11:29,12:13,13:61,14:215,15:204,16:83,17:15
MINIMUM_ACTIVE_COMPONENT_GATE = PASS
```

The original 385 constant candidate-session observations remain historical
input evidence from the strict complete-panel check. The 2,575 count is the
new per-session qualification result on the final eligible grid and is not
forced to equal the historical count.

A 55-line research-only session router reuses the extracted strict validator
and delegates each active, flat component mapping to the existing Qlib
boundary. It contains no z-score, averaging, weighting, learned selection, or
generic framework. The existing strict boundary behavior remains covered.
Seven new synthetic router tests plus the 11 strict-boundary and four splitter
tests pass, 22/22 total. No real score combination was invoked.

### Split feasibility and remaining boundary

Synthetic zero arrays on the final 751-session calendar reproduce three
WalkForward folds and 45 CPCV splits with zero train/test overlap. WalkForward
uses train 504, test 63, purge 2, and leaves 56 trailing sessions unused:

| Fold | Train | Test |
| --- | --- | --- |
| 1 | 2022-01-03..2024-01-04 | 2024-01-09..2024-04-09 |
| 2 | 2022-04-04..2024-04-05 | 2024-04-10..2024-07-10 |
| 3 | 2022-07-06..2024-07-08 | 2024-07-11..2024-10-08 |

CPCV uses 10 folds, two test folds, purge 2 and embargo 2; train sizes are
589..598 and test sizes are 150..151. This remains mechanics evidence only:
the statistical protocol is not frozen. Historical prediction reuse is ready
on the complete derived contract. Prospective model readiness remains blocked
because the 17 candidate model bytes and control model bytes are not persisted;
no refit or fabricated model artifact is authorized here.

```text
P7_STATISTICAL_PROTOCOL_FROZEN = NO
P7_EXIT_CONDITION_SATISFIED = NO
HISTORICAL_PREDICTION_REUSE_READINESS = READY_COMPLETE_INPUT_CONTRACT
PROSPECTIVE_MODEL_READINESS = NOT_READY_MODEL_BYTES_NOT_PERSISTED
REAL_MODEL_TRAINING_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_ENSEMBLE_EXECUTION_COUNT = 0
BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
ENVIRONMENT_MUTATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_RESEARCH_RUNTIME_LOC = 78_ADDED_13_RETIRED_NET_65
NEW_TEST_LOC = 104
NEW_PRODUCTION_LOC = 0
PRIVATE_CLOSEOUT_CHECKSUM_SHA256 = f0b69f8359748ead463ec300de12f10630300c9b709b2e99825365b4830b7b77
CURRENT_DEVELOPMENT_NEXT = P7_FIRST_ENSEMBLE_RESEARCH_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_P7_REAL_DATA_ENSEMBLE_INPUT_AND_CONTROL_CONTRACT_CLOSEOUT
```

### Numeric boundary guard verification

The pinned Qlib 0.9.8.dev26 / pandas 2.3.3 / NumPy 2.2.6 runtime reproduced
the numeric gap with a finite, nonconstant component
`[8e307, 9e307, 1e308]`: native mean and standard deviation became infinite,
its standardized values became `NaN`, and Qlib's final skip-NA mean still
returned the finite vector `[0.0, -0.5, 0.5]`. The component was therefore
effectively lost without a final non-finite result.

The shared validation boundary now uses the same per-session pandas DataFrame
`mean()` and `std()` reductions, including default ddof, before calling Qlib.
An intended nonconstant component fails closed if its mean is non-finite or its
standard deviation is non-finite or nonpositive. Exact constants retain the
existing strict/session-local policy. No replacement standardization, clipping,
rescaling, epsilon threshold, source patch, or generic engine was introduced.

Validation-only rechecking covered 13,518 candidate/control component-session
cross-sections on the already-frozen views. It found zero invalid means and
zero invalid/nonpositive standard deviations. The 2,575 session-local inactive
candidate masks are unchanged. Rehashing all 753 original allowlisted files and
20 derived data files found zero mismatches. The population index and complete
input contract remain byte-identical; the contract does not bind implementation
source and therefore needs no successor identity. Separate numeric-guard
evidence hashes to
`dafd50d31f7dfea85291c808e32d1b7efc6f0083c4cdde1c09d0c620260dc5eb`.

```text
PINNED_RUNTIME_REPRODUCTION_RESULT = PASS_NATIVE_NONFINITE_COMPONENT_SILENTLY_LOST_BY_FINAL_SKIPNA_MEAN
NUMERIC_GUARD_STATUS = PASS_FAIL_CLOSED_BEFORE_ENSEMBLE
REAL_INVALID_MEAN_COUNT = 0
REAL_INVALID_STD_COUNT = 0
ACTIVE_MASK_UNCHANGED = YES
POPULATION_INDEX_UNCHANGED = YES
DATA_ARTIFACT_HASHES_UNCHANGED = YES
INPUT_CONTRACT_IDENTITY_STATUS = UNCHANGED_DATA_CONTRACT_IMPLEMENTATION_GUARD_SEPARATE
SYNTHETIC_TEST_RESULT = 25_OF_25_PASS
ENVIRONMENT_MUTATED = NO
REAL_ENSEMBLE_EXECUTION_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P7_STATISTICAL_PROTOCOL_FROZEN = NO
P7_EXIT_CONDITION_SATISFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_FIRST_ENSEMBLE_RESEARCH_PROTOCOL_FREEZE_001
```
