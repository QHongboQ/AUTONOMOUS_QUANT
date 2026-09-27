# P7 Successor Historical Static-Ensemble Research Protocol Freeze 001

Date: 2026-09-27

Status: `PASS_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_PROTOCOL_FROZEN`

## Authority

This task freezes one wholly new, research-only successor study before any
successor outcome access or execution-code creation. PR #128 is merged in the
exact baseline `212ef12db64073e82da69a6954a5a3e192f88164`. The predecessor V1
result remains permanently `STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE`; it is not
superseded and may not be rerun.

The successor is conditional on the preregistered label-observable population:

```text
SUCCESSOR_INPUT_CONTRACT_SHA256 = b693f43b8dfab0fa04cb12a876fc32928bc5020592a2e137f1c0cbfdde0639ee
LABEL_VALIDITY_MASK_SHA256 = 2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf
SUCCESSOR_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
SUCCESSOR_ROW_COUNT = 374477
SESSION_COUNT = 751
INSTRUMENT_COUNT = 547
STUDY_TYPE = NEW_RESEARCH_ONLY_POST_FAILURE_DISCLOSED_HISTORICAL_STATIC_ENSEMBLE
ESTIMAND = CONDITIONAL_ON_PREREGISTERED_LABEL_OBSERVABILITY
```

## Frozen scientific protocol

All V1 pre-outcome scientific and statistical choices remain unchanged. The
fixed snapshot contains all 17 Formulaic Candidate V3 identities from one
alpha family. Pinned Qlib `AverageEnsemble` owns session-local standardization
and equal averaging; exact constants are inactive only for their session, at
least two active components are required, and missing, non-finite, or
misaligned inputs fail closed. Component selection, learned weights, sign
changes, and AlphaGen-optimized weights are prohibited.

The sole primary endpoint is the mean daily cross-sectional RankIC delta of the
static all-17 ensemble minus the preregistered OLS Alpha158 control. The exact
V1 SPA procedure, WalkForward and CPCV robustness partitions, MCS descriptive
family diagnostic, and secondary Top-30/drop-3 portfolio projection are
preserved. A synthetic 751-session feasibility replay confirmed three usable
WalkForward folds, 56 unused tail sessions, and 45 CPCV splits.

Supportive classification requires all six preregistered gates: positive
full-period mean RankIC delta; SPA consistent p-value at most 0.05; at least
0.6 positive WalkForward folds; positive median WalkForward fold mean delta;
at least 0.6 positive CPCV splits; and positive median CPCV split mean delta.
A complete valid execution with any false gate is not supportive. Required
input or method integrity failure is inconclusive. These are historical
research classifications only and confer no certification, production
authority, dynamic-roster evidence, or P7 exit evidence.

## Structural disclosure

The predecessor population had 374,591 rows. The successor excludes exactly
114 rows: 72 membership-horizon exclusions and 42 provider-gap exclusions,
affecting 74 sessions and 57 instruments. Missingness is explicitly not
assumed MCAR. Results generalize only to the label-observable evaluation
population; no claim or performance stratification is permitted for excluded
observations.

## Execution provenance firewall

No successor execution code exists in this task. Before later outcome access,
the bounded execution code must be independently reviewed, committed, merged
to `origin/main`, and bound by an attempt manifest. The manifest must bind the
protocol, input-contract, population, label-mask, execution-commit, execution-
script, Candidate, OLS, label, and dependency-version identities. A dirty
worktree, HEAD mismatch, or script-hash mismatch fails closed.

```text
SUCCESSOR_PROTOCOL_PATH = 30-research-system/qlib/p7-native-ensemble/successor-historical-static-ensemble-research-protocol.json
SUCCESSOR_PROTOCOL_SHA256 = a4ca307c3e3a245bb211978d36f03d8a2552c81df28049ddb6b667231689a894
SUCCESSOR_PROTOCOL_STATUS = FROZEN_PRE_EXECUTION_CODE
CANDIDATE_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
OLS_PREDICTION_VALUES_DESERIALIZED_FOR_ANALYSIS = 0
LABEL_MAGNITUDES_ACCESSED = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
SPA_MCS_EXECUTION_COUNT = 0
WALKFORWARD_CPCV_EXECUTION_COUNT = 0
PORTFOLIO_BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
```

## Ownership and next task

Qlib owns ensemble construction, RankIC, labels, and run lineage with MLflow;
skfolio owns temporal partitions; arch owns statistical tests; DVC owns
reproducibility. AQ owns only preregistered semantics, immutable bindings,
structural disclosure, and mechanical classification.

```text
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_CODE_PRECOMMIT_AND_PREFLIGHT_FREEZE_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_PROTOCOL_FROZEN
```
