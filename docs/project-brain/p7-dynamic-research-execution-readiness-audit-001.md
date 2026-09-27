# P7 Dynamic Research Execution Readiness Audit 001

Date: 2026-09-27

## Decision

P7 is not currently ready for real prospective dynamic-roster research.
Qlib's mechanics and the historical static input surface are ready, but there
is no real P7-eligible Candidate and no persisted model artifact for any of
the 17 Formulaic Candidates or the selected OLS control.

```text
DYNAMIC_RESEARCH_EXECUTION_READINESS = NOT_READY_MULTIPLE_BLOCKERS
FINAL_CLASSIFICATION = NOT_READY_MULTIPLE_BLOCKERS
```

This was a metadata/evidence audit. It did not open sealed-OOS evidence,
compute performance, train/refit a model, generate predictions, or execute a
real static or dynamic ensemble.

## Authority and lifecycle census

The active P2 Formulaic Alpha Protocol V2 cohort contains 17 immutable
Candidate V3 identities and remains in one-shot sealed-OOS accumulation. Its
activation authority states `CERTIFIED_CANDIDATE_COUNT = 0`. Candidate V3
objects are real research Candidates, but no P2 certification result has been
issued. P4's only Shadow/online execution is explicitly
`TEST_FIXTURE_NOT_REAL_SHADOW`; private P4 JSON contains no
`REAL_P2_CERTIFICATION_EVIDENCE` or `REAL_EXTERNAL_EVIDENCE` record.

Only real evidence was counted:

```text
REAL_RESEARCH_CANDIDATE_COUNT = 17
REAL_CERTIFIED_CANDIDATE_COUNT = 0
REAL_SHADOW_CANDIDATE_COUNT = 0
REAL_CHAMPION_CANDIDATE_COUNT = 0
REAL_DEGRADED_CANDIDATE_COUNT = 0
REAL_RETIRED_CANDIDATE_COUNT = 0
REAL_P2_CERTIFICATION_EVIDENCE_COUNT = 0
REAL_P4_LIFECYCLE_DECISION_EVIDENCE_COUNT = 0
REAL_P7_ELIGIBLE_CANDIDATE_COUNT = 0
MINIMUM_AUTHORIZED_MEMBER_COUNT = 2
REAL_DYNAMIC_ROSTER_CAN_EXIST_NOW = NO
```

The exact reason is `0 < 2`: no Candidate has a real reconstructed state of
`CERTIFIED`, `SHADOW`, or `CHAMPION`. Qlib online tags, Recorder existence,
synthetic lifecycle decisions and the synthetic 3 -> 5 -> 2 fixture grant no
authorization.

## Historical prediction readiness

Metadata-only validation found all 17 original Candidate `pred.pkl` files at
the paths frozen by the P7 input allowlist. Every current SHA-256 matches its
Candidate/P7 authority. All 17 deterministic `run_config.json` files also
match the hashes in Candidate V3.

The complete derived historical contract is intact:

- 17 Candidate views and the adapted OLS control exist and match their frozen
  hashes;
- the eligible-grid Parquet exists and matches its frozen hash;
- 374,591 ordered rows, 751 sessions and 547 instruments remain bound by
  population-index SHA-256
  `2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e`;
- the complete input-contract identity remains
  `92de81d0b8b7b7a29891bf523ae8519af44456f52fea3410ebf0ebd210d0f81f`.

```text
FORMULAIC_17_HISTORICAL_PREDICTION_COUNT = 17
FORMULAIC_17_HISTORICAL_PREDICTION_ARTIFACT_STATUS = PASS_17_EXISTS_AND_SHA256_MATCH
HISTORICAL_POPULATION_CONTRACT_REPRODUCIBLE = YES_METADATA_AND_HASH_VERIFIED
P7_CLOSEOUT_CHECKSUM_STATUS = PASS_28_OF_28
CANDIDATE_V3_MANIFEST_HASH_STATUS = PASS_17_OF_17
HISTORICAL_PREDICTIONS_AVAILABLE = YES
```

No prediction value was deserialized for this audit.

## Prospective model readiness

Candidate V3 truthfully records
`serialized_model_artifact.status = NOT_PERSISTED_BY_UPSTREAM` for all 17
Candidates. The 17 Qlib Recorder artifact directories each contain only
`pred.pkl`, `label.pkl`, `sig_analysis/ic.pkl`, and
`sig_analysis/ric.pkl`. None contains `params.pkl`, `task`, or `dataset`.

Pinned Qlib `PredUpdater` loads `dataset` and `params.pkl` from its Recorder.
It therefore cannot perform prospective inference from these retained
Recorders. The deterministic run configurations, source/runtime identities
and dataset authorities preserve reproducibility evidence, but recreating a
model from them would be a new refit. No authorized, proven deterministic
model-reconstruction capability converts those identities into persisted
model state.

```text
FORMULAIC_17_MODEL_BYTES_PERSISTED_COUNT = 0
FORMULAIC_17_PROSPECTIVE_INFERENCE_READY_COUNT = 0
FORMULAIC_17_PROSPECTIVE_INFERENCE_BLOCKER = RECORDER_PARAMS_TASK_DATASET_ABSENT_AND_REFIT_NOT_AUTHORIZED
PROSPECTIVE_INFERENCE_READY = NO
```

The selected historical-rehearsal OLS control is in the same state. Its
prediction bytes exist and match SHA-256
`26c3433faa58a64914393fe13eac169d9ce86dbbe86f16dfb2b24fbd64139dab`,
but its Recorder has the same four historical evidence files and no model,
task, or dataset artifact.

```text
OLS_HISTORICAL_PREDICTION_AVAILABLE = YES
OLS_MODEL_ARTIFACT_AVAILABLE = NO
OLS_PROSPECTIVE_INFERENCE_READY = NO_REQUIRES_REFIT
```

## Qlib and statistical mechanics

The pinned Qlib runtime is mechanically ready if valid authorized Candidate
model Recorders exist. PRs #118 and #119 exercised and closed the ownership
boundary for `RecorderCollector`, `RollingGroup`, `RollingEnsemble`,
`MergeCollector`, `OnlineToolR`, `OnlineManager` / `RollingStrategy`, and
`AverageEnsemble`. Qlib remains runtime owner; it does not supply P2/P4
authorization.

```text
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_DYNAMIC_RUNTIME_MECHANICS_READY = YES_CONDITIONAL_ON_VALID_AUTHORIZED_MODEL_RECORDERS
REAL_CANDIDATE_EVIDENCE_READY = NO
```

The existing statistical upstreams import successfully and prior synthetic
751-session feasibility remains intact:

```text
QLIB_STATISTICS_OWNER = RANK_IC_AND_PORTFOLIO_ANALYSIS
SKFOLIO_VERSION = 1.0.6
SKFOLIO_OWNERS = WalkForward; CombinatorialPurgedCV
ARCH_VERSION = 8.0.0
ARCH_OWNERS = SPA; RealityCheck; StepM; MCS
STATISTICAL_STACK_READY = YES_MECHANICALLY_ONCE_PROSPECTIVE_OBSERVATIONS_EXIST
```

No statistical procedure consumed real Candidate values in this audit.

## Comparator audit

| Option | Classification | Reason |
|---|---|---|
| `HISTORICAL_STATIC_17` | `HISTORICAL_ONLY` | Exact historical views exist, but no member model state supports future inference. |
| `PROSPECTIVE_FIXED_ROSTER_AT_STUDY_START` | `NOT_CURRENTLY_VALID` | This is the fairest dynamic-policy comparator, but no real eligible start roster or prospective models exist. |
| `OLS_ALPHA158_CONTROL` | `REQUIRES_REFIT` | Historical prediction exists; model/task/dataset artifacts do not. |
| Other already-authorized Qlib prospective control | `NOT_CURRENTLY_VALID` | No additional prospectively reproducible authorized control was found. |

```text
FAIREST_PROSPECTIVE_CONTROL = PROSPECTIVE_FIXED_ROSTER_AT_STUDY_START
FAIREST_PROSPECTIVE_CONTROL_READINESS = NO_REAL_ELIGIBLE_START_ROSTER_AND_NO_PROSPECTIVE_MODEL_ARTIFACTS
```

The OLS Alpha158 control remains an appropriate secondary historical baseline,
but it is not a substitute for the fixed-roster control needed to isolate the
effect of dynamic roster changes.

## Historical static study

The immutable 17-Candidate panel and selected OLS view are ready for a
separately preregistered, research-only historical static study through Qlib
`AverageEnsemble`:

```text
HISTORICAL_STATIC_ENSEMBLE_EXECUTION_READY = YES_RESEARCH_ONLY_NOT_DYNAMIC_NOT_CERTIFICATION
```

This conclusion is mechanical only. The 17 Candidates are members of one
Formulaic Alpha family, the historical interval is consumed research evidence,
and execution would neither create lifecycle history nor satisfy the P7 exit
condition.

## Prohibited retroactive construction

```text
RETROACTIVE_SYNTHETIC_P2_CERTIFICATION_FOR_VALUE_TEST = PROHIBITED
RETROACTIVE_SYNTHETIC_P4_LIFECYCLE_FOR_VALUE_TEST = PROHIBITED
HISTORICAL_PERFORMANCE_DERIVED_LIFECYCLE_EVENTS = PROHIBITED
```

The 2022-2024 predictions may not be mined for dates on which Candidates
"would have" entered, been promoted, degraded, or retired. The 3 -> 5 -> 2
fixture remains mechanism evidence only.

## Prospective start condition and blockers

The first usable session must be selected prospectively and must not be
backdated:

```text
DYNAMIC_STUDY_START_CONDITION = FROZEN_P7_PROTOCOL_AND_AT_LEAST_2_REAL_ELIGIBLE_CANDIDATES_AND_PROSPECTIVE_INFERENCE_FOR_EVERY_ADMITTED_CANDIDATE_AND_VALID_QLIB_RUNTIME_AND_PROSPECTIVELY_REPRODUCIBLE_COMPARATOR_AND_ALL_IDENTITIES_SEALED_BEFORE_START
```

Current blockers are:

1. zero real Candidates are in `CERTIFIED`, `SHADOW`, or `CHAMPION`;
2. all 17 Formulaic Candidate model artifacts are absent;
3. the OLS model artifact is absent, and the fairest fixed-roster comparator
   cannot exist until an eligible roster and prospective models exist.

P2 Formulaic Alpha sealed-OOS accumulation remains the independent eligibility
gate. Model persistence/reproducibility is a separate upstream-first blocker.

## Safety and routing

```text
REAL_LIFECYCLE_RECORDS_MODIFIED = 0
REAL_ROSTER_MUTATION_COUNT = 0
MODEL_TRAINING_COUNT = 0
MODEL_REFIT_COUNT = 0
PREDICTION_GENERATION_COUNT = 0
REAL_DYNAMIC_ENSEMBLE_EXECUTION_COUNT = 0
REAL_STATIC_ENSEMBLE_EXECUTION_COUNT = 0
BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
ENVIRONMENT_MUTATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P7_PROSPECTIVE_MODEL_PERSISTENCE_UPSTREAM_SUBSTITUTION_AUDIT_001
INDEPENDENT_OPTIONAL_STATIC_ROUTE = P7_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_PROTOCOL_FREEZE_001
```
