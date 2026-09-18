# P4 Champion System Upstream Fit and Autonomy Boundary Audit 001

## Decision

```text
P4_CHAMPION_SYSTEM_UPSTREAM_FIT_AND_AUTONOMY_BOUNDARY_AUDIT = PASS
P3_AUTONOMOUS_RESEARCH = COMPLETE
P4_ENTRY = ACTIVE
P4_ENTRY_BLOCKERS = NONE
CURRENT_NEXT = P4_LIFECYCLE_CONTRACT_AND_STATE_POLICY_001
```

This audit defines the smallest lawful P4 architecture. It does not implement
the Champion System, issue a Certified artifact, change P2 Protocol V1, run
research, consume historical TEST, or access sealed OOS.

## Recovered authority

The Project Brain roadmap defines P4 as the **Champion System**, with the goal
of automating the promotion lifecycle and the exit condition that
Candidate → Certified → Shadow → Champion works. P3 is complete and produced
17 producer-neutral Candidate V3 instances. They remain
`INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION`; this is an explicit P2 boundary, not
a reason to block P4 architecture work or fabricate certification.

P2 remains the sole certification authority:

```text
P4_CAN_ISSUE_CERTIFIED = NO
P4_CAN_EDIT_P2_PROTOCOL = NO
P4_CAN_BYPASS_CERTIFICATION = NO
```

## Upstream capability findings

The pinned Qlib runtime is `0.9.8.dev26`, sourced from commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`. Its online workflow already owns
generic online-model history and refresh mechanics. `OnlineManager` coordinates
one or more `OnlineStrategy` instances, `RollingStrategy` and `RollingGen`
provide rolling-model mechanics, trainers own upstream model training/recording,
and `OnlineToolR` persists online/offline recorder tags and prediction updates.
These are runtime capabilities, not Champion semantics.

The audited fits are:

| Capability | Audited fit |
| --- | --- |
| Qlib OnlineManager | `PARTIAL_UPSTREAM_WHOLE_FOR_ONLINE_MODEL_SET_HISTORY_AND_REFRESH_NOT_P4_POLICY` |
| Qlib OnlineStrategy | `UPSTREAM_EXTENSION_SEAM_WITH_AQ_THIN_POLICY_INPUT` |
| Qlib RollingGen | `PASS_UPSTREAM_WHOLE` |
| Qlib Recorder | `PASS_UPSTREAM_WHOLE` |
| MLflow Registry | `PARTIAL_UPSTREAM_LEAF_FOR_MODEL_VERSION_IDENTITY_AND_ALIASES_NOT_CERTIFICATION_POLICY` |
| DVC lifecycle fit | `REPRODUCIBILITY_ONLY_NOT_RUNTIME_LIFECYCLE` |

Qlib's documented online stack confirms that `OnlineManager` coordinates
online strategies and that rolling strategies handle rolling tasks and models:
<https://qlib.readthedocs.io/en/latest/component/online.html>.

MLflow `3.16.0` owns run/experiment identity, statuses, tags, metrics, artifacts,
and, where a persisted model artifact exists, generic registered-model version
identity and aliases. Its registry workflow explicitly supports aliases and
tags: <https://mlflow.org/docs/latest/ml/model-registry/workflow>. It does not
own AQ certification policy, financial decay thresholds, or Champion
promotion. Current Formulaic Candidate V3 model artifacts are not all persisted
as registerable upstream model artifacts, so the registry cannot be assumed to
cover every candidate automatically. AQ must not create a second model
registry.

DVC `3.67.1` owns dependency/output identity, reproducible DAG evidence, and
configuration/output invalidation. Its command surface is pipeline and data
versioning, not a runtime promotion state machine:
<https://dvc.org/doc/command-reference/>. Champion history, promotion decisions,
and decay decisions therefore do not belong in DVC.

## Minimum lifecycle model

| Concept | Classification | Authority |
| --- | --- | --- |
| `RESEARCH_CANDIDATE` | AQ policy state | P3 Candidate contract |
| `CERTIFIED` | AQ-consumed policy state | P2 only |
| `SHADOW` | AQ policy state | P4 over upstream evidence |
| `CHAMPION` | AQ policy role/state | P4 policy |
| `CHALLENGER` | role, not a separate state | attached to Certified or Shadow |
| `DEGRADED` | AQ policy state | P4 deterministic decision |
| `RETIRED` | AQ policy state | P4 terminal decision |

Qlib online/offline tags and MLflow run statuses are upstream runtime states.
They may be evidence or projections, but they are not semantic authority for
this lifecycle.

The minimum lawful graph is:

```text
RESEARCH_CANDIDATE --P2 only--> CERTIFIED
CERTIFIED --------------------> SHADOW
SHADOW -----------------------> CHAMPION
CHAMPION ---------------------> DEGRADED
DEGRADED ---------------------> RETIRED
```

A Challenger is a role attached to a Certified or Shadow artifact. Candidate
may never jump directly to Champion. Champion is a research-system role and is
not authorization to allocate or trade capital.

## Ownership

```text
LIFECYCLE_STATE_OWNER = AQ_THIN_DETERMINISTIC_POLICY_WITH_CERTIFIED_OWNED_SOLELY_BY_P2
ONLINE_MODEL_HISTORY_OWNER = QLIB_ONLINE_MANAGER_ONLINE_TOOL_R_AND_RECORDER
ROLLING_UPDATE_OWNER = QLIB_ROLLING_STRATEGY_ROLLING_GEN_AND_TRAINER
METRIC_COMPUTATION_OWNER = QLIB_RECORD_TEMPLATES_AND_RECORDER
DECAY_DECISION_OWNER = AQ_THIN_DETERMINISTIC_POLICY
RESEARCH_REQUEST_OWNER = AQ_THIN_PRODUCER_NEUTRAL_CONTRACT
PROMOTION_DECISION_OWNER = AQ_THIN_POLICY_CONSUMING_P2_CERTIFICATION_AND_SHADOW_EVIDENCE
OPERATIONAL_SCHEDULER_OWNER = P12
```

`SigAnaRecord` already produces per-session IC and RankIC series, while
`PortAnaRecord` produces portfolio reports and risk analysis. Qlib/MLflow own
the metric and artifact records. AQ may later evaluate a small deterministic
policy over those inputs, but this audit selects no numerical decay thresholds
and authorizes no AQ metric or drift engine.

Evidently provides regression-quality and drift reports
(<https://docs.evidentlyai.com/metrics/preset_regression>), and NannyML provides
performance-estimation methods
(<https://nannyml.readthedocs.io/en/v0.10.3/how_it_works/performance_estimation.html>).
Both are deferred: neither has yet been proven to fit financial rank-signal and
portfolio-return semantics, and the shadow evidence contract is not yet frozen.
No new upstream is adopted by this audit.

## Research request boundary

P4 may emit a producer-neutral thin request containing only:

- request identity and canonical hash;
- reason and source evidence identities;
- asset or universe scope;
- allowed research families;
- budget identity;
- required target and protocol context;
- evidence cutoff and provenance.

It must not know AlphaGen internals, PPO details, RD-Agent prompts, or carry
promotion authority. P3 research orchestration chooses an eligible producer.
No generic router is introduced.

## Self-triggering and scheduling

```text
P4_SYSTEM_LEVEL_SELF_TRIGGERING_BOUNDARY = DETERMINISTIC_POLICY_IN_P4_SCHEDULING_IN_P12
```

The eventual architecture is:

```text
P12 schedule/wake
  -> collect Qlib + MLflow + DVC + shadow evidence
  -> invoke deterministic P4 policy
  -> emit lifecycle decisions and producer-neutral research request
  -> P3 research orchestration selects the producer
```

P4 logic must be callable as `current evidence -> decisions/events`; it does
not own periodic wake-up, polling, retries, alerts, or job timing.

## Shadow boundary

Research shadow evidence may use Qlib rolling predictions and online
simulation. Real event-driven paper execution remains a later P9 concern. P4
consumes a bounded evidence contract containing candidate/certification
identity, observation interval and calendar, predictions, realized outcomes or
returns where available, costs, lineage, Qlib Recorder/MLflow/DVC identities,
completion status, and zero-capital attestation. This audit implements none of
that execution.

## Human authority

No automatic P4 transition may override maximum capital, maximum leverage,
hard risk ceilings, permitted asset classes, or production activation/shutdown.
A degraded Champion may lose its research Champion role before a replacement
exists, but safe/no-position/previous-Champion portfolio behavior is deliberately
unresolved and belongs to downstream portfolio/execution policy and human
authority.

## Generic-engine prohibition

```text
AQ_WORKFLOW_ENGINE_REQUIRED = NO
AQ_MODEL_REGISTRY_REQUIRED = NO
AQ_METRIC_ENGINE_REQUIRED = NO
AQ_SCHEDULER_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Entry and exit blockers

```text
P4_ENTRY_BLOCKERS = NONE
P4_EXIT_BLOCKERS =
  FORMULAIC_ALPHA_P2_PROTOCOL_EXPANSION;
  REAL_P2_ISSUED_CERTIFIED_ARTIFACT;
  SHADOW_EVIDENCE_CONTRACT_AND_OBSERVATION_PATH;
  LIFECYCLE_POLICY_IMPLEMENTATION_AND_TRANSITION_TESTS;
  QLIB_MLFLOW_IDENTITY_PROJECTION_INTEGRATION;
  REAL_END_TO_END_CANDIDATE_CERTIFIED_SHADOW_CHAMPION_PROOF
```

P12 scheduling, P9 paper execution, and live-money activation do not block P4
entry and are not redefined as P4 exit work.

## Next slice

```text
RECOMMENDED_FIRST_IMPLEMENTATION_SLICE = P4_LIFECYCLE_CONTRACT_AND_STATE_POLICY_001
CURRENT_NEXT = P4_LIFECYCLE_CONTRACT_AND_STATE_POLICY_001
```

The first implementation should freeze the minimal pure lifecycle contract and
deterministic transition policy before any Qlib integration POC. That order
makes the semantic boundary testable and prevents upstream runtime tags from
accidentally becoming lifecycle authority.

## Private evidence

```text
PRIVATE_REPORT = D:/AQ_DATA/P4/champion-system-upstream-fit-and-autonomy-boundary-audit-001/audit_summary.json
PRIVATE_REPORT_SHA256 = a1f4a58c7755eae2559249ac200beba8b1322b6703a4efa26491397b55948ade
```

The private directory also contains the recovered authority snapshot, exact
Qlib/MLflow/DVC capability matrices, lifecycle analysis, decay ownership,
research-request boundary, upstream-gap analysis, responsibility tree, and
entry/exit blocker ledger.
