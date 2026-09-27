# P7 Lifecycle Decision to Effective Roster Protocol Freeze 001

## Semantically corrected result

The P7 lifecycle-to-roster policy is frozen as a thin, research-only
projection over existing P2 certification and P4 lifecycle state. It does not
reuse P4's Challenger-role predicate as general P7 research-roster authority.

```text
PROTOCOL_STATUS = FROZEN_PRE_EXECUTION_SEMANTICALLY_CORRECTED
P7_RESEARCH_ROSTER_ELIGIBILITY_AUTHORITY = P7_RESEARCH_ROSTER_PROJECTION_OVER_EXISTING_P2_P4_LIFECYCLE_STATE
P4_CHALLENGER_ROLE_USED_AS_ROSTER_AUTHORITY = NO
RESEARCH_ROSTER_ELIGIBLE_STATES = CERTIFIED; SHADOW; CHAMPION
RESEARCH_ROSTER_INELIGIBLE_STATES = RESEARCH_CANDIDATE; DEGRADED; RETIRED
CHAMPION_ROSTER_ELIGIBILITY = ELIGIBLE_RESEARCH_ONLY_NO_PRODUCTION_OR_LIVE_CAPITAL_AUTHORITY
ROSTER_MEMBER_COUNT_IS_FIXED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
AQ_NEW_PRODUCTION_LOC = 0
```

The normative machine-readable artifact is
`30-research-system/qlib/p7-native-ensemble/lifecycle-decision-to-effective-roster-protocol.json`.
Its current identity is SHA-256 over the `rfc8785==0.1.4` JCS bytes of the
complete JSON object:
`5034cd1fb5ef6969e7116fa63d5ac40ce22e05f8b16688e0e77f2f72bae97c02`.
The prior identity
`fa8107fe9bf834f1d088e22fcf2500f3160e94337bc92ff63e494519d0f4171e`
is superseded PR history, not the current protocol identity.

## Research-roster eligibility is not the Challenger role

`challenger_role_allowed()` answers whether a lifecycle state may hold the P4
Challenger role. It does not answer whether a model may remain an input to a
P7 research ensemble. No stronger existing authority was found that excludes
the Champion from a general research roster. The corrected projection is:

| Lifecycle state | P7 research-roster eligibility | Reason |
| --- | --- | --- |
| `RESEARCH_CANDIDATE` | not eligible | no valid P2 certification |
| `CERTIFIED` | eligible | valid P2 certification |
| `SHADOW` | eligible | valid post-certification research state |
| `CHAMPION` | eligible | valid research lifecycle state; Challenger-role exclusion is irrelevant |
| `DEGRADED` | not eligible | explicit adverse lifecycle state |
| `RETIRED` | not eligible | terminal adverse lifecycle state |

```text
P7_RESEARCH_ROSTER_ELIGIBILITY != P4_CHALLENGER_ROLE_ELIGIBILITY
CHAMPION_IN_P7_RESEARCH_ROSTER != PRODUCTION_OR_LIVE_CAPITAL_AUTHORIZATION
```

## Exact lifecycle decision semantics

Every real `DecisionKind` in `LifecycleDecisionEvidenceV1` is frozen
explicitly; no invented umbrella enum is used.

| DecisionKind | State effect |
| --- | --- |
| `ADMIT_SHADOW` | set `SHADOW` |
| `PROMOTE_CHAMPION` | set `CHAMPION` |
| `MARK_DEGRADED` | set `DEGRADED` |
| `RETIRE` | set `RETIRED` |
| `NO_CHANGE` | retain prior authoritative state |
| `CHALLENGER_NEEDED` | retain prior authoritative state |
| `RESEARCH_REQUESTED` | retain prior authoritative state |
| `REJECT_TRANSITION` | retain prior authoritative state; rejected target never becomes current |

For each Candidate, reconstruction begins at `CERTIFIED` only when valid P2
certification evidence exists. P7 then applies accepted P4 state-changing
decisions in authoritative chronological/evidence order available by the
cutoff. Non-state-changing and rejected decisions leave state unchanged.
Candidate mismatch, a broken lifecycle edge, conflicting accepted
transitions, ambiguous ordering, or missing authority fails closed. P7 does
not reinterpret Shadow, decay, detector, RankIC, retirement, or other raw
evidence behind P4's decisions.

## Whole-roster field audit

No existing P2 or P4 contract authorizes a complete P7 roster as one object.
P2 authorizes individual certification and P4 authorizes individual lifecycle
decisions. Therefore the prior whole-roster `authorization_evidence_id` was an
unsupported semantic claim and is removed from the successor protocol.

The corrected non-authoritative field is:

```text
source_decision_bundle_identity =
  immutable RFC8785/SHA-256 identity of the exact external P2/P4 evidence set
  and authority-delivery metadata used to form the roster
```

It provides provenance, not authorization. Member-level fields remain
`members[].candidate_id` and `members[].authorization_evidence_id`; `roster_id`
continues to identify the immutable roster manifest.

PR #116's merged `EffectiveRoster.authorization_evidence_id` field is now
known to be semantically misnamed/unsupported for whole-roster authorization.
This documentation-only correction does not silently mutate that reviewed
runtime contract. A tiny successor task must rename or remove that field and
update its schema/tests before any real roster use. No
`RosterAuthorizationEvidenceV1`, P7 certification object, approval engine, or
new authorization authority is introduced.

The corrected logical cross-runtime fields are:

```text
roster_id
use_scope
source_decision_bundle_identity
evidence_cutoff
effective_session
supersedes_roster_id
members[].candidate_id
members[].authorization_evidence_id
```

## Prospective XNYS activation

The evidence cutoff is a timezone-aware UTC instant from immutable external
authority-delivery evidence. Its conversion is explicit:

1. convert the UTC instant to `America/New_York`;
2. take that local calendar date;
3. select the first XNYS session strictly after that date through
   `aq_xnys_calendar`.

Using the UTC date directly is prohibited. Same-session and intraday
activation remain prohibited. Later decisions never rewrite earlier sessions.

Roster size remains variable and has no target. `N_t` is the count of
authoritative Candidates in `CERTIFIED`, `SHADOW`, or `CHAMPION` at time `t`.
The historical 17-Candidate snapshot remains immutable evidence only. At
least two authorized members and, separately, at least two session-active
components are required. A valid Champion is not an unauthorized member.

## Synthetic semantic proof and safety

The bounded synthetic validation covers:

- Certified eligible;
- Certified to Shadow remains eligible;
- Shadow to Champion remains eligible;
- Champion to Degraded becomes ineligible prospectively;
- Degraded to Retired remains ineligible;
- rejected Shadow-to-Champion remains Shadow and eligible;
- `CHALLENGER_NEEDED` leaves Champion eligible;
- `RESEARCH_REQUESTED` leaves state unchanged;
- one Champion plus one Certified yields two authorized members, runnable only
  if the existing session-active gate also passes.

The prior synthetic `3 -> 5 -> 2` variable-count evidence remains intact.

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
CURRENT_DEVELOPMENT_NEXT = P7_PR116_EFFECTIVE_ROSTER_SOURCE_BUNDLE_FIELD_ALIGNMENT_001
FINAL_CLASSIFICATION = PASS_P7_LIFECYCLE_TO_ROSTER_SEMANTIC_CORRECTION
```
