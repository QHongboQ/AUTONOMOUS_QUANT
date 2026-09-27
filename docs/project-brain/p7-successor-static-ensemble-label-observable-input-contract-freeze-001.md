# P7 Successor Static Ensemble Label-Observable Input Contract Freeze 001

Date: 2026-09-27

Status: `PASS_SUCCESSOR_LABEL_OBSERVABLE_INPUT_CONTRACT_FROZEN`

This task freezes a wholly new structural input contract for a possible P7
successor study. It materializes no prediction or label values in Git, creates
no research protocol, and performs no ensemble or performance execution. V1
remains terminal inconclusive and is not superseded.

## Baseline and scientific identity

PR #127 merged as main commit
`e0d33c75748e87d772e5c3e48aaf374fad11da5f`. The successor contract has a
new namespace, population identity and label-validity-mask identity. Its
estimand is explicitly different from V1.

```text
V1_RESULT = STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
V1_RERUN_ALLOWED = NO
V1_IS_SUPERSEDED = NO
V1_INPUT_CONTRACT_SHA256 = 92de81d0b8b7b7a29891bf523ae8519af44456f52fea3410ebf0ebd210d0f81f
SUCCESSOR_INPUT_CONTRACT_REPLACES_V1_HISTORY = NO
ESTIMAND_CHANGED_FROM_V1 = YES
SUCCESSOR_ESTIMAND = CONDITIONAL_ON_PREREGISTERED_LABEL_OBSERVABILITY
```

The exact 17 Candidate V3 identities and source prediction hashes, exact OLS
Alpha158 control identity and hash, Candidate signs, roster, weighting
semantics and primary comparator are unchanged. The normative contract binds
those immutable identities individually.

## Qlib label authority and structural row rule

```text
LABEL_EXPRESSION = Ref($close, -2)/Ref($close, -1) - 1
LABEL_GENERATION_OWNER = QLIB
LABEL_SEMANTICS_OWNER = QLIB
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
LABEL_SHA256 = c14c7c3f1e698126663b85dfcf436cf3258dc4609e8217e95ed188d9be7db35e
LABEL_VALID_ROW = LABEL_KEY_PRESENT AND LABEL_FINITE
SUCCESSOR_ROW_RULE = V1_PREDICTION_CONTROL_POPULATION_VALID AND LABEL_KEY_PRESENT AND LABEL_FINITE
```

The validity rule is the only new row condition. It uses no label magnitude,
sign, rank or distribution and no Candidate/OLS score. AQ does not generate or
repair labels.

## Label-validity mask and population accounting

The private structural mask is keyed in the exact V1 population order and
contains only `datetime`, `instrument` and a Boolean `label_valid`. Its semantic
identity hashes the ordered keys and Boolean state; its Parquet byte identity
is separately sealed in private checksums.

The successor grid contains only `datetime` and `instrument`. It is the strict
ordered V1 subset selected by the frozen Boolean mask.

```text
LABEL_VALIDITY_MASK_ROW_COUNT = 374591
LABEL_VALIDITY_MASK_SHA256 = 2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf
MASK_KEY_IDENTITY = EXACT_V1_POPULATION_KEY_AND_ORDER
V1_ROW_COUNT = 374591
V1_POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
SUCCESSOR_ROW_COUNT = 374477
EXCLUDED_ROW_COUNT = 114
SUCCESSOR_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
SUCCESSOR_SESSION_COUNT = 751
SUCCESSOR_INSTRUMENT_COUNT = 547
SUCCESSOR_START = 2022-01-03
SUCCESSOR_END = 2024-12-27
SUCCESSOR_MINIMUM_ROWS_PER_SESSION = 490
SUCCESSOR_ALL_SESSIONS_RANKIC_STRUCTURALLY_FEASIBLE = YES
```

No session is empty, every retained session has at least two rows, no invalid
V1 row remains and no row absent from V1 was introduced. RankIC itself was not
computed.

## Coverage and structural disclosure

The previously sealed derived-view manifest proves every Candidate and the
OLS control covers every exact V1 population key. Because the successor is a
strict subset, coverage is established without reopening prediction objects.

```text
CANDIDATE_17_SUCCESSOR_ROW_COVERAGE = PASS
OLS_SUCCESSOR_ROW_COVERAGE = PASS
LABEL_NONFINITE_ROWS = 114
MEMBERSHIP_HORIZON_EXCLUSION_COUNT = 72
PROVIDER_GAP_EXCLUSION_COUNT = 42
AFFECTED_SESSION_COUNT = 74
AFFECTED_INSTRUMENT_COUNT = 57
MISSINGNESS_ASSUMPTION = NOT_MCAR
SUCCESSOR_RESULTS_GENERALIZE_ONLY_TO = LABEL_OBSERVABLE_EVALUATION_POPULATION
```

No claim is authorized for excluded observations. The two frozen exclusion
classes are disclosed structurally and may not be split by performance.

## Frozen contract and execution boundary

The normative machine-readable contract is
`30-research-system/qlib/p7-native-ensemble/successor-label-observable-input-contract.json`.
Its RFC 8785 canonical JSON identity is:

```text
SUCCESSOR_INPUT_CONTRACT_SHA256 = b693f43b8dfab0fa04cb12a876fc32928bc5020592a2e137f1c0cbfdde0639ee
CONTRACT_STATUS = FROZEN_PRE_PROTOCOL
```

Private mask/population evidence is sealed at
`D:/AQ_DATA/P7/successor-static-ensemble-label-observable-input-contract-freeze-001`.
The private checksum-manifest SHA-256 is
`f5e7e4b2bbb038b3e8125dd68d50f716397faffd24abe2dee3c1bed381d02baa`.

Any future execution code must be committed before outcome access. Its attempt
manifest must bind the execution commit and script SHA-256 and reject a dirty
worktree or identity mismatch. This task creates no successor research
protocol or execution attempt.

```text
FUTURE_EXECUTION_CODE_COMMITTED_PRE_OUTCOME_REQUIRED = YES
FUTURE_ATTEMPT_MANIFEST_BINDS_COMMIT_SHA = YES
FUTURE_ATTEMPT_MANIFEST_BINDS_SCRIPT_SHA256 = YES
FUTURE_DIRTY_WORKTREE_ALLOWED = NO
FILL_LABEL_WITH_ZERO = PROHIBITED
FORWARD_FILL_LABEL = PROHIBITED
BACKFILL_LABEL = PROHIBITED
SYNTHETIC_RETURN_IMPUTATION = PROHIBITED
CUSTOM_AQ_LABEL_GENERATION = PROHIBITED
AQ_LABEL_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
```

## Scientific firewall

```text
CANDIDATE_PREDICTION_VALUES_ACCESSED_FOR_ANALYSIS = 0
OLS_PREDICTION_VALUES_ACCESSED_FOR_ANALYSIS = 0
LABEL_MAGNITUDES_ACCESSED = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
SPA_MCS_EXECUTION_COUNT = 0
WALKFORWARD_CPCV_EXECUTION_COUNT = 0
PORTFOLIO_BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_LABEL_OBSERVABLE_INPUT_CONTRACT_FROZEN
```
