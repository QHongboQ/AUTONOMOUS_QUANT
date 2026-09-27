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
| daily session authority | existing `aq_xnys_calendar` leaf over `exchange_calendars==4.13.2` | `is_session` validates ISO roster/session identities; P7 no longer accepts or reconstructs a session table |
| Candidate/model identity | existing Candidate V3 identity | referenced by `candidate_id`; model class/configuration/dataset facts are not copied into P7 |
| eligibility/lifecycle authority | external P2/P4 or authorized research-policy evidence | referenced by immutable evidence identity; Qlib online state is not authorization |
| runtime lineage/readiness | Candidate V3 -> Qlib Recorder / MLflow run identity | the caller resolves the existing Candidate authority to a ready Candidate ID; P7 does not duplicate `recorder_id`, search Recorders, or register models |
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

It now retains exactly two references:

| Field | Why it remains |
| --- | --- |
| `candidate_id` | selects one immutable Candidate V3 authority; same-class candidates remain distinct through their Candidate identities |
| `authorization_evidence_id` | proves external eligibility/permission without copying lifecycle state into P7 |

Model class, model identity, configuration, dataset identity, lifecycle state,
Qlib online tag and evidence classification are not duplicated. Fixture scope
is held once at roster level as `TEST_FIXTURE_NOT_REAL_EVIDENCE`.

```text
ROSTER_RUNTIME_LOC_BEFORE = 242
ROSTER_RUNTIME_LOC_AFTER = 198
NET_RUNTIME_LOC_CHANGE = -44
AQ_CUSTOM_CANONICALIZER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

The remaining executable functions are limited to project-specific glue:
immutable-field projection into upstream RFC8785; frozen roster construction;
selection by external evidence cutoff plus `aq_xnys_calendar.is_session`; and
exact session/member routing into the existing Qlib combiner. The module performs no
I/O and owns no registry, database, scheduler, model store, alias service,
lifecycle engine or persistence service.

## Daily activation and runtime separation

`effective_session` is an XNYS daily session label. `evidence_cutoff` and each
session's preregistered decision cutoff are timezone-aware UTC instants. A
roster can affect a session only when its effective session is no later than
that session and its evidence was available by that session's cutoff. Evidence
arriving after a session cutoff cannot affect that session, while later
sessions may use it. No intraday activation semantics are implied.

Roster membership means externally authorized. Runtime readiness is supplied
separately as Candidate IDs already resolved through Candidate V3's immutable
Recorder binding. An authorized member lacking a ready Candidate raises a
runtime-readiness error; a ready Candidate absent from the authorized roster
contributes nothing. `OnlineToolR.ONLINE_TAG` is neither a contract field nor
certification authority.

## Synthetic evidence

The fixtures use distinct Candidate references and roster counts
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
CURRENT_DEVELOPMENT_NEXT = P7_LIFECYCLE_DECISION_TO_EFFECTIVE_ROSTER_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_P7_ROSTER_UPDATE_POLICY_UPSTREAM_SUBSTITUTION_AUDIT
```

The 37 tests comprise seven contract/session tests in the existing
RFC8785/XNYS authority runtime, 26 Qlib boundary/router/handoff tests in the
pinned Qlib runtime, and four existing skfolio split-feasibility tests. No real
Candidate values, lifecycle records, predictions, labels, returns or
performance evidence were opened.

## Roster update policy upstream-substitution audit

The audit inspected the complete 198-line runtime, the pinned AlphaGen source
at `259687e8f316994426416c530a94842a2fe6405e`, the pinned RD-Agent source at
`32b3d395e73d9db5eee3fe9063d69aec0fdc83bd`, pinned Qlib online/rolling
implementations, and existing P2/P4/Frouros/MLflow/DVC/P12 authority. It did
not inspect real Candidate outcomes or execute research.

### Runtime function audit

| Executable item | Classification | Owner / retained reason |
| --- | --- | --- |
| `EffectiveRoster.require_utc` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | preserves the project non-lookahead boundary between UTC evidence availability and a daily effective session |
| `EffectiveRoster.sort_unique_members` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | makes roster membership nonempty, unique and identity-order invariant |
| `_identity_projection` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | defines the closed immutable non-ID field projection; it implements no canonicalization |
| `roster_content_identity` | `UPSTREAM_LEAF` | delegates semantic canonicalization to `rfc8785==0.1.4`, then applies SHA-256 |
| `build_roster` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | binds one immutable externally authorized roster to its content identity |
| `select_effective_rosters` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | applies only evidence-cutoff, effective-session and supersession semantics; XNYS membership is delegated to `aq_xnys_calendar.is_session` |
| `combine_selected_roster_predictions` | `EXISTING_AQ_AUTHORITY_REUSE` | retains exact candidate/session routing and fail-closed readiness, then calls the existing P7 router and Qlib `AverageEnsemble` |

No item was classified `UNNECESSARY_DUPLICATION` after the two mechanical
deletions in this audit. No function is a roster-selection, lifecycle,
scheduling, persistence, training or model-management engine. The executable
lines attributable to irreducible roster contract/selection policy are
approximately 79 physical lines; the rest are models, validation, upstream
calls, exact routing and reporting.

### Retained field audit

| Field | Classification | Why retained |
| --- | --- | --- |
| member `candidate_id` | `EXISTING_AQ_AUTHORITY_REUSE` | references Candidate V3, which already binds model/runtime, Recorder and prediction artifact identity |
| member `authorization_evidence_id` | `EXISTING_AQ_AUTHORITY_REUSE` | references candidate-specific P2/P4 or preregistered research authorization evidence without copying its state |
| `roster_id` | `UPSTREAM_LEAF` | RFC8785/SHA-256 semantic identity of the immutable roster |
| `use_scope` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | distinguishes the authorized research/use boundary |
| roster `authorization_evidence_id` | `EXISTING_AQ_AUTHORITY_REUSE` | references the whole-roster authorization decision, distinct from member eligibility evidence |
| `evidence_cutoff` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | prevents evidence known after a decision cutoff from entering that session |
| `effective_session` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | declares activation; validity is delegated to the XNYS adapter |
| `supersedes_roster_id` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | closes immutable version lineage and prevents ambiguous parallel rosters |
| `members` | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | is the exact externally authorized Candidate set consumed by P7 |

`recorder_id` was deleted from `RosterMember`. Candidate V3 already binds one
exact `qlib_recorder_identity` and prediction artifact. The runtime caller
that reads Candidate V3 can project successful readiness to Candidate IDs;
P7 then consumes that bounded set. This requires no registry, database,
repository search or fabricated metadata.

### Dynamic research and runtime findings

AlphaGen's pinned `LinearAlphaPool` genuinely owns research-pool `capacity`,
`try_new_expr`, mutual-IC checks, weight optimization, add/remove behavior,
`update_history`, `leave_only` and `bulk_edit`. Those operations optimize an
AlphaGen research expression pool; they are not Candidate certification,
lifecycle, production roster authorization or scheduling authority.

RD-Agent's pinned `RAGEvoAgent.multistep_evolve` and CoSTEER/FactorCoSTEER
surfaces own bounded iterative research generation, evaluation feedback and
knowledge-assisted evolution. They do not decide whether a resulting
Candidate is Certified, Shadow, Champion, Degraded, Retired, or admitted to a
P7 roster.

Qlib owns Recorder-backed training (`TrainerR`), rolling task generation
(`RollingGen`/`RollingStrategy`), online routine orchestration
(`OnlineManager`), runtime online/offline tags and prediction updating
(`OnlineToolR`), and combination (`AverageEnsemble`). These may implement
future runtime mechanics after an externally authorized roster is supplied.
They do not establish scientific certification or roster permission, and
unbounded routines that train, update to provider-latest dates or mutate real
tags were not executed.

P2 owns certification. P4 owns lifecycle meanings and transitions,
challenger-needed decisions, producer-neutral research requests, retirement
authorization and the preregistered financial-decay policy. Frouros owns ADWIN
change-detection mathematics only. MLflow/Qlib own experiment, run, Recorder
and artifact lineage; DVC owns immutable dependency/output identity,
invalidation and reproduction. P12 owns operational scheduling. P7 can define
a preregistered cadence value as policy metadata, but cannot implement the
scheduler.

### Final ownership matrix

| Capability | Current implementation | Mature upstream/existing owner | Decision | Residual AQ responsibility |
| --- | --- | --- | --- | --- |
| candidate generation | external research candidates | AlphaGen; RD-Agent/CoSTEER | `UPSTREAM_WHOLE` | reference immutable Candidate V3 only |
| candidate pool maintenance | none in P7 | AlphaGen research pool | `UPSTREAM_WHOLE` | none; not production authorization |
| redundancy screening | none in P7 | AlphaGen mutual IC | `UPSTREAM_WHOLE` | preregister use if future research invokes it |
| research-pool weight optimization | none in P7 | AlphaGen `optimize` | `UPSTREAM_WHOLE` | none; not P7 roster or ensemble weights |
| model training | none in this POC | Qlib `TrainerR`; research producer | `UPSTREAM_WHOLE` | fixed task/config authority only |
| rolling retraining | none in P7 | Qlib `RollingGen`/`RollingStrategy`/`OnlineManager` | `UPSTREAM_WHOLE` | authorize when/if policy permits; no scheduler |
| Recorder/runtime status | Candidate-ready ID set | Candidate V3 + Qlib Recorder/`OnlineToolR` | `EXISTING_AQ_AUTHORITY_REUSE` | fail closed on unresolved/not-ready Candidate |
| experiment lineage | referenced through Candidate | Qlib/MLflow | `UPSTREAM_WHOLE` | cross-authority identity consistency only |
| artifact identity | referenced through Candidate/evidence | DVC | `UPSTREAM_LEAF` | bind exact identity in evidence |
| certification | consumed external evidence | P2 | `EXISTING_AQ_AUTHORITY_REUSE` | none |
| lifecycle transition | consumed external decision | P4 `LifecycleDecisionEvidenceV1` | `EXISTING_AQ_AUTHORITY_REUSE` | none |
| drift detection | none in P7 | Frouros ADWIN | `UPSTREAM_LEAF` | consume immutable detector evidence only |
| financial decay policy | none in P7 | P4 frozen policy | `EXISTING_AQ_AUTHORITY_REUSE` | none |
| XNYS session semantics | direct `is_session` call | `aq_xnys_calendar` | `EXISTING_AQ_AUTHORITY_REUSE` | provide ISO session identity |
| semantic identity | thin call | `rfc8785==0.1.4` | `UPSTREAM_LEAF` | choose closed non-ID projection |
| roster membership authorization | immutable external references | P2/P4 or explicit research authority | `EXISTING_AQ_AUTHORITY_REUSE` | assemble only already-authorized candidate references |
| roster effective-session policy | cutoff/session/supersession predicate | no upstream owns AQ's daily authorization semantics | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | small pure prospective selector |
| roster persistence | not implemented | DVC immutable artifacts | `UPSTREAM_LEAF` | future bounded schema/artifact identity only |
| policy cadence value | not frozen | future preregistered P7/P4 policy | `IRREDUCIBLE_AQ_DOMAIN_POLICY` | define value only if authorized |
| scheduling | not implemented | P12 operations | `UPSTREAM_WHOLE` | none |
| ensemble | existing router calls Qlib | Qlib `AverageEnsemble` | `UPSTREAM_WHOLE` | exact eligibility/routing and fail-closed guard |
| cross-validation | not run | skfolio | `UPSTREAM_WHOLE` | preregister split configuration only |
| multiple-testing correction | not run | arch | `UPSTREAM_WHOLE` | preregister classification policy only |

No installed quant/trading skill exposes a stable runtime machine interface in
this environment. Generic review templates may assist future human checklist
review, but no Skill owns certification, lifecycle transitions, roster
mutation or statistical truth and none is a production dependency.

```text
XNYS_DUPLICATION_STATUS = REMOVED
AQ_XNYS_ADAPTER_REUSED = YES
RECORDER_ID_FIELD_DECISION = REMOVED_REUSE_CANDIDATE_V3
ROSTER_MEMBER_FIELDS_FINAL = candidate_id; authorization_evidence_id
QLIB_ONLINE_TAG_IS_CERTIFICATION_AUTHORITY = NO
POLICY_CADENCE_VALUE_OWNER = PREREGISTERED_P7_OR_P4_POLICY
SCHEDULER_OWNER = P12
AQ_NEW_GENERIC_ENGINE_COUNT = 0
REAL_TRAINING_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_ENSEMBLE_COUNT = 0
BACKTEST_COUNT = 0
P2_SEALED_OOS_ACCESSED = NO
```
