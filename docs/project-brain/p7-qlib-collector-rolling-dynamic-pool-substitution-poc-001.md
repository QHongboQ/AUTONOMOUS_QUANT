# P7 Qlib collector / rolling dynamic-pool substitution POC 001

Date: 2026-09-27
Classification: `PASS_PARTIAL_SUBSTITUTION`

## Scope

This bounded synthetic POC tests whether pinned Microsoft Qlib can own the
mechanical runtime work around a time-effective P7 roster. It does not select
or authorize Candidates, use real Candidate artifacts, train a model, generate
real predictions, run an ensemble research result, backtest, or access P2 V2
sealed OOS.

The exercised runtime is Qlib `0.9.8.dev26`. The inspected source is the pinned
Microsoft Qlib commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`. The installed copies of the five
relevant source modules are byte-identical to that checkout.

## Actual upstream exercise

Seven isolated Qlib Recorder/MLflow runs stored synthetic `pred.pkl` artifacts:
C1 and C2 each had rolling versions R1 and R2 with an overlapping session;
C3, C4, and C5 supplied the remaining fixture streams. Every artifact was
tagged `TEST_FIXTURE_NOT_REAL_EVIDENCE`.

The public upstream chain was exercised directly:

```text
Recorder / pred.pkl
-> RecorderCollector (Candidate ID, rolling version key)
-> RollingGroup / RollingEnsemble
-> MergeCollector (Candidate -> rolled prediction)
-> existing P7 authorization, row, numeric and session-local gates
-> AverageEnsemble
```

`RollingEnsemble` retained the later rolling-window value at the duplicated
prediction identity. The 3 -> 5 -> 2 effective-roster sequence then produced
the same result as the current path supplied with manually pre-rolled fixture
inputs:

```text
OUTPUT_INDEX_MATCH = YES
OUTPUT_VALUE_MATCH = YES
ROSTER_PERIOD_MATCH = YES
ACTIVE_COMPONENT_MATCH = YES
CURRENT_PATH_OUTPUT_SHA256 = 4e25040e0d764eb06e9c3262d1f192121967309a7496ca9e0ae30e97cdc101b2
QLIB_NATIVE_PATH_OUTPUT_SHA256 = 4e25040e0d764eb06e9c3262d1f192121967309a7496ca9e0ae30e97cdc101b2
```

`OnlineToolR` owned fixture runtime-ready tags only. C4 and C5 were runtime
ready but excluded from early sessions because they were not authorized by the
effective roster. Removing C2 from runtime readiness while it remained
authorized failed closed. Recorder existence, prediction availability, and
Qlib online tags therefore remain non-authoritative for certification and
roster permission.

## OnlineManager boundary

Pinned source confirms that `OnlineManager` natively owns per-strategy rolling
updates, runtime history, Collector construction, and signal preparation. Its
strategy-local history does not natively consume P2/P4 lifecycle authority to
decide cross-Candidate roster membership. No subclass or custom manager was
created to force that capability.

```text
ONLINE_MANAGER_PER_STRATEGY_ROLLING_OWNER = YES
ONLINE_MANAGER_RUNTIME_HISTORY_OWNER = YES
ONLINE_MANAGER_SIGNAL_PREPARATION_OWNER = YES
ONLINE_MANAGER_DYNAMIC_ROSTER_AUTHORITY = NOT_NATIVE
```

## Ownership and contraction decision

Qlib can own Recorder artifact retrieval, rolling-version stitching,
multi-Candidate collection, runtime online/offline state, and standardized
averaging. P7 must retain the external Candidate-ID allowlist, exact session
routing, row-identity and numeric fail-closed checks, its frozen session-local
constant policy, and minimum-active-component enforcement.

The current 198-LOC handoff does not implement Recorder loading, rolling
stitching, or multi-Candidate collection, so deleting code now would remove
required authorization/validation semantics rather than duplicate upstream
machinery. No runtime file was changed. The safe result is a partial
substitution boundary for closeout, not a claim that Qlib owns authorization.

```text
P7_RUNTIME_LOC_BEFORE = 198
P7_RUNTIME_LOC_AFTER = 198
NET_RUNTIME_LOC_CHANGE = 0
NEW_PRODUCTION_LOC = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Evidence and safety

Focused pinned-runtime result: `8/8 PASS`.

Private evidence root:
`D:/AQ_DATA/P7/qlib-collector-rolling-dynamic-pool-substitution-poc-001`

Private checksum manifest SHA-256:
`f260973cfce4ae43791d5c38445db14a3049ca1b9c7138630174aaa5466d8b8e`

```text
REAL_CANDIDATE_ARTIFACTS_ACCESSED = 0
REAL_MODEL_TRAINING_COUNT = 0
REAL_MODEL_REFIT_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_DYNAMIC_ROSTER_EXECUTION_COUNT = 0
REAL_ENSEMBLE_EXECUTION_COUNT = 0
BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
ENVIRONMENT_MUTATED = NO
```

## Next

`P7_QLIB_RUNTIME_SUBSTITUTION_CLOSEOUT_001`

That task may close the proven wiring boundary without introducing an AQ
collector, rolling stitcher, runtime store, model manager, or authorization
engine.
