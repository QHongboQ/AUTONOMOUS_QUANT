# P7 Variable-Roster Upstream Handoff POC 001

## Result

P7 can consume immutable, externally authorized, time-effective candidate
rosters through a narrow identity/time/permission handoff and the existing
session-local Qlib ensemble boundary. The bounded synthetic sequence
`3 -> 5 -> 2` passes. This proves switching mechanics only; it does not prove
profitable adaptive selection, create certification authority, execute a real
ensemble, or satisfy the P7 exit condition.

```text
BASE_MAIN = fcb525a3193d3d914da7c24e122164a69914088e
VARIABLE_ROSTER_HANDOFF_STATUS = PASS_SYNTHETIC_UPSTREAM_HANDOFF
SYNTHETIC_ROSTER_SEQUENCE = 3_TO_5_TO_2
EVIDENCE_CLASSIFICATION = TEST_FIXTURE_NOT_REAL_EVIDENCE
FIXED_17_CANDIDATE_SNAPSHOT_MUTATED = NO
EARLIER_FIXED_ROSTER_RESEARCH_PROTOCOL = PAUSED_REFERENCE_NOT_EXECUTED
P7_EXIT_CONDITION_SATISFIED = NO
```

## Reused ownership and capabilities

| Capability | Owner / existing boundary | This task |
| --- | --- | --- |
| prediction validation and numeric guard | existing P7 `average_ensemble_boundary.py` | executed on synthetic panels through the existing router |
| session-local constant-component policy | existing P7 `session_local_router.py` | executed unchanged; constants are inactive only for that session and fewer than two active components fail closed |
| standardization and equal averaging | Microsoft Qlib `qlib.model.ens.ensemble.AverageEnsemble` | executed on synthetic panels; AQ did not reproduce its math |
| Recorder online/offline state | Qlib `OnlineToolR` | `ONLINE_TAG` reused as member Recorder-state semantics; it is explicitly not certification evidence |
| model lifecycle and eligibility meaning | existing P4 contracts; P2 remains certification owner | inspected and represented only by immutable external evidence references; no real record was opened or mutated |
| online model management | Qlib `OnlineManager`, `RollingStrategy`, `TrainerR`, `OnlineToolR` | existing tested handoff inspected; manager routines were not run because they may train, update predictions, or read provider state |

AQ adds only a pure handoff module. It performs no I/O or persistence and owns
no registry, database, scheduler, model manager, training loop, prediction
store or generic evaluator. A roster contains its content identity, version,
scope, external authorization-evidence identity, evidence cutoff, effective
time, superseded roster identity, and immutable member references. Each member
retains distinct Candidate, model and Recorder identities plus an external
eligibility-evidence identity. Qlib online status alone never admits a member.

## Synthetic proof

The fixtures use five distinct Candidate/model/Recorder identities sharing the
same model class. The effective roster sequence is:

| version | effective UTC boundary | member count | relationship |
| --- | --- | ---: | --- |
| `fixture-v1` | 2024-01-02 | 3 | initial |
| `fixture-v2` | 2024-01-04 | 5 | supersedes v1 |
| `fixture-v3` | 2024-01-06 | 2 | supersedes v2 |

Every decision session selects the latest roster whose evidence cutoff and
effective time are both visible. A later roster cannot change the exact output
prefix produced under earlier versions. New members require no prediction
before entry; removed members require none after removal. Within an applicable
session, every roster member must provide the exact eligible row index.
Missing members, missing/non-finite values, row mismatch, ambiguous effective
times, broken supersession, or fewer than two active components fail closed.

```text
EFFECTIVE_BOUNDARY_ACTIVATION = PASS
ONE_UNAMBIGUOUS_ROSTER_PER_SESSION = PASS
FUTURE_MEMBER_EARLY_CONTRIBUTION_COUNT = 0
FUTURE_ROSTER_BACKWARD_REWRITE_COUNT = 0
SAME_MODEL_CLASS_DISTINCT_IDENTITY = PASS
PREDICTION_ROW_ALIGNMENT = PASS_FAIL_CLOSED
MISSING_OR_NONFINITE_INPUT = PASS_FAIL_CLOSED
SESSION_LOCAL_CONSTANT_POLICY = PASS_UNCHANGED
INSUFFICIENT_ACTIVE_COMPONENT_POLICY = PASS_FAIL_CLOSED
DETERMINISTIC_REPLAY = PASS
SYNTHETIC_TEST_RESULT = 34_OF_34_PASS
```

The 34 checks comprise 30 Qlib-boundary/router/handoff tests in the pinned
Qlib runtime and four existing split-feasibility tests in the pinned skfolio
runtime. No environment or dependency was changed.

## Boundaries and remaining work

The 17 Candidate V3 identities and their immutable input snapshot are
unchanged. No real P4/MLflow/Recorder or certification state was mutated. No
real prediction value, label, return or performance artifact was inspected.
There was no real ensemble, training, prediction generation, backtest, broker
action, P8 implementation or P2 V2 sealed-OOS access.

The POC intentionally does not define how a real roster earns authorization,
how update proposals are scheduled, or which future research protocol may
compare roster policies. It also does not turn missing/numeric failure into
retirement. Those decisions require a separate preregistered policy task; they
must reuse the existing evidence/storage owners and must not add a roster
engine or state store.

```text
REAL_LIFECYCLE_RECORDS_MODIFIED = 0
P2_COHORT_MODIFIED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
REAL_TRAINING_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_ENSEMBLE_COUNT = 0
BACKTEST_COUNT = 0
ENVIRONMENT_MUTATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_DEVELOPMENT_NEXT = P7_ROSTER_UPDATE_POLICY_AND_RESEARCH_PROTOCOL_DESIGN_001
FINAL_CLASSIFICATION = PASS_P7_VARIABLE_ROSTER_UPSTREAM_HANDOFF_POC
```
