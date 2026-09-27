# P7 Lifecycle Decision to Effective Roster Protocol Freeze 001

## Result

The minimal P7-owned policy is frozen without implementing a selection,
lifecycle, drift, scheduling, persistence or model-management engine. P7
consumes already-authorized P2/P4 decisions and produces only a prospective,
immutable logical roster handoff for the existing Qlib runtime.

```text
PROTOCOL_STATUS = FROZEN_PRE_EXECUTION
PROTOCOL_SHA256 = fa8107fe9bf834f1d088e22fcf2500f3160e94337bc92ff63e494519d0f4171e
ROSTER_MEMBER_COUNT_IS_FIXED = NO
ELIGIBILITY_AUTHORITY = P2_CERTIFICATION_AND_P4_LIFECYCLE_DECISIONS
PRODUCTION_TRADING_AUTHORIZATION_IMPLIED = NO
P7_PERIODIC_REEVALUATION_ENGINE = NONE
AQ_NEW_GENERIC_ENGINE_COUNT = 0
AQ_NEW_PRODUCTION_LOC = 0
```

The normative machine-readable artifact is
`30-research-system/qlib/p7-native-ensemble/lifecycle-decision-to-effective-roster-protocol.json`.
Its reported identity is SHA-256 over the upstream `rfc8785==0.1.4` JCS bytes
of the complete JSON object. AQ contains no canonicalizer.

## Eligibility mapping

P4 already closes the only mapping needed: its Challenger role is permitted
only for `CERTIFIED` and `SHADOW`, and a subject cannot simultaneously be the
Champion and a Challenger. P7 therefore introduces no lifecycle state and no
new scoring result.

| Lifecycle state | P7 research-roster eligibility | Authority |
| --- | --- | --- |
| `RESEARCH_CANDIDATE` | not eligible | no valid P2 certification yet |
| `CERTIFIED` | eligible | P2 certification |
| `SHADOW` | eligible | P4 `ADMIT_SHADOW` decision |
| `CHAMPION` | not eligible | P4 Challenger-role exclusion; may remain a separate research comparator |
| `DEGRADED` | not eligible | P4 `MARK_DEGRADED` decision |
| `RETIRED` | not eligible | P4 `RETIRE` decision |

Eligibility is research-only. It grants no production activation, live
trading, capital, leverage, execution or risk-limit authority.

P7 directly consumes only valid Candidate V3 identity,
`P2CertificationEvidenceV1`, and `LifecycleDecisionEvidenceV1`. It does not
interpret `ShadowEvidenceV2`, `RetirementAuthorizationV1`, Frouros detector
output, RankIC summaries or financial-decay thresholds. Those may be source
identities behind a P4 decision, but P4 alone interprets them. Raw RankIC,
returns, Sharpe, correlations, AlphaGen pool metrics and recent performance
are structurally absent from roster formation.

A real roster accepts only `REAL_P2_CERTIFICATION_EVIDENCE` and
`REAL_EXTERNAL_EVIDENCE`. Test-fixture classifications remain valid only for
synthetic protocol proof and can never authorize a real roster.

## Prospective daily activation

`DECISION_EVIDENCE_CUTOFF` is the latest authoritative availability timestamp
of the complete verified decision bundle, normalized to timezone-aware UTC.
It must come from the immutable authority-delivery envelope, never the local
P7 wall clock. Missing, reconstructed or ambiguous availability fails closed.

The effective session is the first XNYS session whose session date is
strictly later than the `America/New_York` calendar date containing that UTC
cutoff. `aq_xnys_calendar` owns date/session resolution. This intentionally
forbids same-session activation, requires no intraday engine, and guarantees
that later evidence cannot alter earlier sessions.

Updates are event-driven from P2/P4 decisions. P7 defines no periodic cadence
and owns no scheduler. The existing P4 financial-decay evaluation cadence
remains P4 policy; operational delivery remains P12-owned.

## Roster formation and failure policy

At a decision event, the immutable current roster plus the complete verified
P2/P4 decision bundle produces at most one manifest for the derived effective
session. Every Candidate must have one unambiguous authoritative state at the
cutoff. Members are exactly those in `CERTIFIED` or `SHADOW`, sorted by
Candidate ID and bound to their authorization evidence. Conflicting decisions,
duplicate identities or ambiguous state fail closed.

The roster count is variable:

```text
N_t = count(externally authorized CERTIFIED or SHADOW members at time t)
TARGET_MEMBER_COUNT = NONE
HISTORICAL_17 = SNAPSHOT_METADATA_ONLY
```

At least two authorized members are required for a runnable roster. If fewer
than two remain, P7 stops from that prospective effective session. It does not
carry forward newly unauthorized members, resurrect Retired members, or add a
replacement merely to preserve count. Separately, the existing Qlib handoff
requires at least two session-active nonconstant components. Missing,
non-finite or misaligned prediction data remains a hard failure, not ordinary
inactivity.

Exactly one roster is effective per session. Every new version names its
immediate predecessor, uses RFC8785/SHA-256 semantic identity, and cannot
rewrite earlier outputs. Historical versions remain immutable and replayable.
DVC remains the future persistence/reproducibility owner; no roster database,
registry, mutable service or IPC design is introduced.

## Cross-runtime logical boundary

The minimum replayable serialized handoff remains:

```text
roster_id
use_scope
authorization_evidence_id
evidence_cutoff
effective_session
supersedes_roster_id
members[].candidate_id
members[].authorization_evidence_id
```

Runtime readiness is a separate set of Candidate IDs already resolved through
Candidate V3's Qlib Recorder authority. Authorization and Qlib readiness are
not conflated.

## Synthetic feasibility and safety

The protocol records only the existing synthetic concept:

```text
3 externally authorized
-> add 2 externally authorized
-> three later external lifecycle decisions make members ineligible
-> 2 remain
```

This proves logical variable-count formation only. It does not use real
Candidate identities, mutate lifecycle evidence, run Qlib, or inspect any
scientific outcome.

```text
REAL_CANDIDATE_SELECTION_COUNT = 0
REAL_LIFECYCLE_TRANSITION_COUNT = 0
REAL_ROSTER_MUTATION_COUNT = 0
REAL_MODEL_TRAINING_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_ENSEMBLE_COUNT = 0
BACKTEST_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_DYNAMIC_ROSTER_RESEARCH_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_P7_LIFECYCLE_DECISION_TO_EFFECTIVE_ROSTER_PROTOCOL_FREEZE
```
