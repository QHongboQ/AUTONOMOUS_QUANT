# P7 Variable-Roster Upstream Handoff POC 001

## Result and closeout

The synthetic `3 -> 5 -> 2` variable-roster POC passes after upstream
substitution and code contraction. It proves daily roster switching mechanics,
not profitable adaptive selection, certification, or P7 exit.

```text
BASE_MAIN = fcb525a3193d3d914da7c24e122164a69914088e
VARIABLE_ROSTER_HANDOFF_STATUS = PASS_SYNTHETIC_UPSTREAM_HANDOFF
EVIDENCE_CLASSIFICATION = TEST_FIXTURE_NOT_REAL_EVIDENCE
FIXED_17_CANDIDATE_SNAPSHOT_MUTATED = NO
EARLIER_FIXED_ROSTER_RESEARCH_PROTOCOL = PAUSED_REFERENCE_NOT_EXECUTED
P7_EXIT_CONDITION_SATISFIED = NO
```

## Upstream and project authorities reused

| Capability | Owner | Exercised result |
| --- | --- | --- |
| semantic identity | Python `rfc8785==0.1.4` | SHA-256 over RFC 8785 JCS of every immutable non-ID roster field; member collections sorted before JCS; no AQ canonicalizer or fallback |
| immutable contract style | Pydantic `2.13.5` | frozen models with `extra="forbid"` and existing SHA-256 identity shape |
| daily session authority | `exchange_calendars==4.13.2`, XNYS | effective roster and requested labels must be valid XNYS sessions |
| Candidate/model identity | existing Candidate V3 identity | referenced by `candidate_id`; model class/configuration/dataset facts are not copied into P7 |
| eligibility/lifecycle authority | external P2/P4 or authorized research-policy evidence | referenced by immutable evidence identity; Qlib online state is not authorization |
| runtime lineage/readiness | Qlib Recorder / MLflow run identity | `recorder_id` is used only for prediction retrieval/readiness; no model registration or lifecycle mutation |
| session-local input policy | existing P7 router | missing/non-finite/misaligned inputs and fewer than two active components fail closed; exact constants remain session-local inactive |
| standardization and averaging | Qlib `AverageEnsemble` | executed through the unchanged router on synthetic panels |

The existing P5 contract-authority runtime already contains Pydantic,
RFC8785 and exchange_calendars. It authors and validates the roster contract
and session selection. The pinned Qlib runtime consumes the validated
session-to-members handoff and runs the existing Qlib-owned combiner. No
environment was changed and no cross-environment `site-packages` mixing was
used.

## Contract contraction

`RosterMember` previously duplicated seven fields:

```text
candidate_id
model_class
model_identity
recorder_identity
online_status
eligibility_evidence_identity
evidence_classification
```

It now retains exactly three references:

| Field | Why it remains |
| --- | --- |
| `candidate_id` | selects one immutable Candidate V3 authority; same-class candidates remain distinct through their Candidate identities |
| `authorization_evidence_id` | proves external eligibility/permission without copying lifecycle state into P7 |
| `recorder_id` | identifies the Qlib Recorder/MLflow run needed to retrieve predictions and assess runtime readiness |

Model class, model identity, configuration, dataset identity, lifecycle state,
Qlib online tag and evidence classification are not duplicated. Fixture scope
is held once at roster level as `TEST_FIXTURE_NOT_REAL_EVIDENCE`.

```text
ROSTER_RUNTIME_LOC_BEFORE = 242
ROSTER_RUNTIME_LOC_AFTER = 202
NET_RUNTIME_LOC_CHANGE = -40
AQ_CUSTOM_CANONICALIZER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

The remaining executable functions are limited to project-specific glue:
immutable-field projection into upstream RFC8785; frozen roster construction;
selection by external evidence cutoff plus XNYS effective session; and exact
session/member routing into the existing Qlib combiner. The module performs no
I/O and owns no registry, database, scheduler, model store, alias service,
lifecycle engine or persistence service.

## Daily activation and runtime separation

`effective_session` is an XNYS daily session label. `evidence_cutoff` and each
session's preregistered decision cutoff are timezone-aware UTC instants. A
roster can affect a session only when its effective session is no later than
that session and its evidence was available by that session's cutoff. Evidence
arriving after a session cutoff cannot affect that session, while later
sessions may use it. No intraday activation semantics are implied.

Roster membership means externally authorized. Recorder readiness is supplied
separately to the Qlib handoff. An authorized member lacking a ready Recorder
raises a runtime-readiness error; a ready Recorder that is absent from the
authorized roster contributes nothing. `OnlineToolR.ONLINE_TAG` is neither a
contract field nor certification authority.

## Synthetic evidence

The fixtures use distinct Candidate and Recorder references and roster counts
`3 -> 5 -> 2`. Tests prove RFC8785 determinism, member-order invariance,
identity changes from member/session changes, identity mismatch rejection,
XNYS validation, cutoff/session separation, exact boundary activation,
prospective-only supersession, authorization/readiness separation, unchanged
prior outputs, deterministic replay, exact row alignment, fail-closed numeric
inputs, and the existing constant/minimum-active policy.

```text
SYNTHETIC_TEST_RESULT = 37_OF_37_PASS
FUTURE_ROSTER_BACKWARD_REWRITE_COUNT = 0
QLIB_ONLINE_TAG_IS_CERTIFICATION_AUTHORITY = NO
REAL_LIFECYCLE_RECORDS_MODIFIED = 0
P2_COHORT_MODIFIED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
REAL_TRAINING_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_ENSEMBLE_COUNT = 0
BACKTEST_COUNT = 0
ENVIRONMENT_MUTATED = NO
CURRENT_DEVELOPMENT_NEXT = P7_ROSTER_UPDATE_POLICY_UPSTREAM_SUBSTITUTION_AUDIT_001
FINAL_CLASSIFICATION = PASS_P7_VARIABLE_ROSTER_UPSTREAM_SUBSTITUTION_CLOSEOUT
```

The 37 tests comprise seven contract/session tests in the existing
RFC8785/XNYS authority runtime, 26 Qlib boundary/router/handoff tests in the
pinned Qlib runtime, and four existing skfolio split-feasibility tests. No real
Candidate values, lifecycle records, predictions, labels, returns or
performance evidence were opened.
