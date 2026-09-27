# P7 Qlib runtime substitution closeout 001

Date: 2026-09-27

## Scope and result

This closeout audited every executable responsibility in the three active P7
runtime-boundary modules against pinned Microsoft Qlib source
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`. It also exercised deletion
counterfactuals with synthetic inputs. The result is:

```text
FINAL_CLASSIFICATION = PASS_RUNTIME_SUBSTITUTION_CLOSED_NO_FURTHER_SAFE_DELETION
```

Qlib already owns collection, rolling model/runtime management, rolling-output
stitching and numerical ensemble combination. AQ does not duplicate those
capabilities. The remaining AQ code is limited to project authorization,
time-effective roster selection, authoritative-row validation, fail-closed
numeric checks, the frozen session-local constant policy and the minimum-active
component rule.

The final boundary is:

```text
EXTERNAL_AUTHORIZED_CANDIDATE_SET
    -> P7 validation / daily-session routing
    -> QLIB upstream runtime / ensemble
```

## Ownership map

| Capability | Owner | AQ executable responsibility | Why the residual remains |
|---|---|---|---|
| Recorder prediction retrieval | Qlib `RecorderCollector` | none | Native collector consumes Recorder artifacts. |
| Duplicate rolling-output stitching | Qlib `RollingGroup` / `RollingEnsemble` | none | Native latest-window semantics were already proven against the P7 fixture. |
| Multi-collector composition | Qlib `MergeCollector` | none | Native collector composition already owns this capability. |
| Per-strategy online history and rolling updates | Qlib `OnlineManager`, `RollingStrategy`, `RollingGen`, `TrainerR` | none | Native runtime owns training/update/history mechanics; this task did not execute them. |
| Runtime online/offline status | Qlib `OnlineToolR` | distinguish runtime readiness from authorization | The tag is operational state, not P2/P4 certification authority. |
| Cross-Candidate authorization and effective roster | P2/P4 evidence projected through P7 policy | select one already-authorized roster for each XNYS session/cutoff | Qlib has no native P2/P4 lifecycle-evidence consumer or cross-Candidate authorization contract. |
| Ensemble standardization and averaging | Qlib `AverageEnsemble` | validate the inputs and delegate combination | Qlib owns numerical combination; AQ retains only the scientific input boundary. |
| Eligible row identity/order | AQ project boundary | require exact authoritative `(datetime, instrument)` rows | Native `AverageEnsemble` accepts a common omitted row and silently emits a shorter result. |
| Finite/standardizable numeric input | AQ project boundary | reject missing, non-finite and invalid standardization statistics | Native pandas reductions may propagate invalid values or silently drop an overflowed component. |
| Session-local constants and minimum activity | frozen P7 research policy | mark exact constants inactive per session and require at least two active components | Native skip-NaN behavior is not an explicit project policy and accepts a one-component result. |

`OnlineManager` therefore remains an upstream runtime owner, but:

```text
P7_ONLINE_MANAGER_DYNAMIC_ROSTER_AUTHORITY = NOT_NATIVE
P7_QLIB_ONLINE_TAG_IS_CERTIFICATION_AUTHORITY = NO
```

## Executable block classification

| Module / block | Classification | Closeout decision |
|---|---|---|
| `RosterMember`, `EffectiveRoster` contract fields | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | Retain immutable references to external authorization and daily effective-roster provenance. |
| UTC, uniqueness, content-identity, ordering and supersession checks | `IRREDUCIBLE_FAIL_CLOSED_BOUNDARY` | Retain; upstream runtime does not validate the project authorization bundle. |
| `_identity_projection` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | Retain the exact immutable roster projection. |
| `roster_content_identity` RFC 8785 serialization and SHA-256 | `UPSTREAM_OWNED_AND_ALREADY_DELEGATED` | Retain only the thin call/binding; canonicalization is owned by `rfc8785==0.1.4`. |
| `build_roster` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | Retain construction of the project-specific handoff. |
| `select_effective_rosters` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | Retain daily XNYS effective-session/cutoff selection and fail-closed chain validation. |
| `combine_selected_roster_predictions` | `IRREDUCIBLE_FAIL_CLOSED_BOUNDARY` | Retain authorization/runtime-readiness separation and exact eligible-row enforcement. |
| `combine_session_local_nonconstant` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | Retain frozen session-local constant and minimum-active rules; delegate the actual combination. |
| `validate_complete_predictions` | `IRREDUCIBLE_FAIL_CLOSED_BOUNDARY` | Retain exact schema, row, order, numeric and standardization guards. |
| `AverageEnsemble()(validated)` | `UPSTREAM_OWNED_AND_ALREADY_DELEGATED` | Qlib remains the sole standardization/averaging owner. |
| `combine_complete_predictions` postconditions | `IRREDUCIBLE_FAIL_CLOSED_BOUNDARY` | Retain output type, identity/order and finiteness checks. |

No block was classified `UNNECESSARY_DUPLICATION`.

## Deletion counterfactuals

The focused synthetic suite covered common-row omissions, mismatched rows,
duplicates, unsorted input, NaN, infinity, extreme finite overflow, exact
constants, fewer than two active components, unauthorized candidates and
authorized-but-not-runtime-ready candidates.

Two counterexamples are decisive:

1. When every component omits the same eligible row, native
   `AverageEnsemble` returns a shorter finite result. Only the external
   `eligible_index` comparison detects the scientific population change.
2. With an extreme but finite component, native pandas standardization
   overflows and Qlib's mean silently produces the same result as if that
   component were absent. The pre-combination standardization-statistic guard
   prevents this unreported roster change.

Accordingly:

```text
EXACT_ROW_GUARD_DECISION = RETAIN_IRREDUCIBLE_FAIL_CLOSED_BOUNDARY
FINITE_NUMERIC_GUARD_DECISION = RETAIN_IRREDUCIBLE_FAIL_CLOSED_BOUNDARY
EXTREME_VALUE_GUARD_DECISION = RETAIN_IRREDUCIBLE_FAIL_CLOSED_BOUNDARY
EXACT_CONSTANT_POLICY_DECISION = RETAIN_IRREDUCIBLE_AQ_DOMAIN_POLICY
MINIMUM_ACTIVE_COMPONENT_GATE_DECISION = RETAIN_IRREDUCIBLE_AQ_DOMAIN_POLICY
RUNTIME_READY_GATE_DECISION = RETAIN_IRREDUCIBLE_FAIL_CLOSED_BOUNDARY
```

## Physical LOC accounting

Physical LOC includes blank lines, comments, imports and declarations so the
file totals are independently reproducible. Ownership-category LOC assigns
executable/declarative blocks to their dominant responsibility; neutral module
scaffolding is reported separately rather than falsely attributed to an
owner.

| File | Physical LOC | Upstream delegated | AQ domain policy | AQ fail-closed | Neutral scaffolding |
|---|---:|---:|---:|---:|---:|
| `time_effective_roster_handoff.py` | 198 | 12 | 94 | 75 | 17 |
| `session_local_router.py` | 55 | 1 | 22 | 8 | 24 |
| `average_ensemble_boundary.py` | 99 | 1 | 0 | 70 | 28 |
| **Total** | **352** | **14** | **116** | **153** | **69** |

The runtime files were not changed:

```text
P7_RUNTIME_LOC_BEFORE = 352
P7_RUNTIME_LOC_AFTER = 352
P7_NET_RUNTIME_LOC_CHANGE = 0
UNNECESSARY_DUPLICATION_COUNT = 0
```

Every retained executable function is project-specific policy or a
fail-closed boundary around an already-delegated upstream operation. Deleting
any of these blocks would either erase P2/P4 authorization/time semantics or
permit a demonstrated silent population/component change.

## Verification and safety

The pinned Qlib runtime passed 38 focused ensemble/router/handoff/collector
tests. The project contract runtime passed 7 roster identity and XNYS tests.
Combined result: 45/45 PASS. No real Candidate artifact, model training,
prediction generation, dynamic roster execution, ensemble execution, backtest
or performance metric was used.

```text
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
TEST_RESULT = PASS_45_OF_45
REAL_CANDIDATE_ARTIFACTS_ACCESSED = 0
REAL_MODEL_TRAINING_COUNT = 0
REAL_MODEL_REFIT_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_DYNAMIC_ROSTER_EXECUTION_COUNT = 0
REAL_ENSEMBLE_EXECUTION_COUNT = 0
BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_COHORT_MODIFIED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P7_DYNAMIC_RESEARCH_EXECUTION_READINESS_AUDIT_001
```
