# Trial Ledger contract design 001

**Task:** `AUTONOMOUS-QUANT-TRIAL-LEDGER-CONTRACT-DESIGN-001`
**Scope:** Project Brain contract design only. No runtime code, database, package, upstream environment, model search, data-provider, broker, account, or trading action is authorized by this document.

## 1. Decision and boundary

The Trial Ledger is the project-owned, authoritative record of research attempt and selection history. It is a child of the Research System because research creates trials and the ledger records them; Certification consumes immutable evidence from it.

```text
30-research-system/
  experiment-registry/
    trial-ledger/
      contract
      lifecycle
      storage
      snapshot

40-certification-system/
  multiple-testing-control/   <- read-only consumer only

70-operations-system/
  audit-trail/                <- may observe/export; never owns the ledger
```

```text
TRIAL_LEDGER_OWNER = OUR_CODE
TRIAL_LEDGER_ROLE = authoritative attempt and selection history
CERTIFICATION_ROLE = read-only policy consumer and decision authority
DSR_DENOMINATOR_OWNER = CERTIFICATION_POLICY / OUR_CODE
PBO_SELECTION_SET_OWNER = CERTIFICATION_POLICY / OUR_CODE
SPA_MODEL_SET_OWNER = CERTIFICATION_POLICY / OUR_CODE
PROMOTION_AUTHORITY = CERTIFICATION / OUR_CODE
```

The ledger is not a Qlib, RD-Agent, future AlphaGPT, arch, skfolio, or MLflow subsystem. Those systems are clients or evidence producers. Neither a research generator nor an upstream package receives authority to delete history, rewrite a frozen specification, reduce attempted/evaluated history, choose Certification's statistical denominator, redefine a favorable trial family after feedback, or promote a candidate.

## 2. Purpose and non-goals

The ledger makes the history that creates selection bias auditable before large model/factor search begins. It records proposed hypotheses before performance feedback, the lifecycle of each execution, immutable references to results/artifacts, and lineage between related trials.

It does **not**:

- train, search, rank, select, or promote a model, factor, or strategy;
- calculate `DSR_NB_TRIALS`, PBO, SPA, RealityCheck, StepM, MCS, or a CertificationDecision;
- own temporal policy, sealed-OOS access, leakage policy, or promotion policy;
- store sealed-OOS contents, raw datasets, model checkpoints, or large artifacts;
- replace MLflow/Qlib Recorder visualization or artifact storage; or
- authorize P1 research or any broker action.

The ledger holds durable metadata and immutable references. Artifact deletion therefore cannot erase registration, lifecycle, result-reference, or protocol-violation history.

## 3. Authority model

| Actor | Allowed through the public contract | Prohibited through the public contract |
|---|---|---|
| Research generator (Qlib, RD-Agent, future AlphaGPT, or human tool) | request registration; append allowed lifecycle events; attach references | mutate a frozen ResearchSpec or historical TrialRegistration; remove history; choose a Certification denominator; promote |
| Trial Ledger | validate contract invariants; retain append-only history; return versioned snapshots | perform statistical tests; silently classify policy trial sets; access sealed OOS |
| Certification | read snapshots; derive versioned, policy-specific sets/counts; issue decisions outside the ledger | silently edit the ledger or overwrite historical family assignment |
| MLflow / Qlib Recorder | expose metrics/artifacts through stable references | become the authoritative attempt/selection history |
| arch / skfolio | calculate bounded statistical/CV evidence on Certification-provided inputs | own trial history, temporal policy, OOS access, or promotion |
| Operations audit trail | observe or export ledger evidence | own, mutate, or truncate the ledger |

The future write surface is deliberately narrow:

```text
generator
  -> TrialLedger.register()
  -> authorized trial_id
  -> experiment execution
  -> TrialLedger.append_event() / append_result()

TrialLedger.snapshot(as_of, policy reference)
  -> Certification
  -> DSR / PBO / arch evidence / CertificationDecision
```

No result can become Certification-eligible by bypassing registration.

## 4. What counts as a trial

Every attempt is recorded, but a process execution is not automatically one statistically independent trial. The ledger preserves raw facts; Certification later applies a declared policy to decide which recorded facts are relevant to a particular denominator or selection set.

| Classification | Meaning | Ledger treatment | Automatic DSR/PBO inclusion |
|---|---|---|---|
| `REGISTERED_ATTEMPT` | One TrialRegistration referencing a proposed ResearchSpec was accepted before performance feedback. | Immutable ResearchSpec, TrialRegistration, and registration event retained. | No; policy-derived only. |
| `PERFORMANCE_EVALUATED_TRIAL` | A registered trial obtained a performance-bearing research/validation result. | Observation/result events and evidence references retained. | No; it is eligible for policy evaluation, not automatically counted. |
| `REPRODUCIBILITY_REPLAY` | Exact frozen specification/data/code/seed rerun solely to verify reproducibility. | Recorded as a linked execution of the original trial. | No; never an independent hypothesis merely because it ran again. |
| `INFRASTRUCTURE_FAILURE` | Execution failed before meaningful performance feedback. | Failure reason, time, and attempt remain visible permanently. | No automatic inclusion; policy may classify it separately. |
| `MUTATED_TRIAL` | A material post-feedback ResearchSpec change. | New ResearchSpec hash and new `trial_id`, with lineage to its parent, are required. | Policy-derived; the old record remains unchanged. |
| `UNREGISTERED_RESULT` | Performance evidence observed without prior accepted registration. | Retain a protocol-violation/result-reference record where safely available. | **NON_CERTIFIABLE**. |

An *execution record* is distinct from both ResearchSpec and TrialRegistration. A registered trial may have several recorded executions: a transient transport retry, an infrastructure failure, or a reproducibility replay. This preserves every attempt without falsely multiplying research hypotheses.

## 5. Pre-registration and admissibility

For a performance result to be admissible to a future Certification policy, registration must be committed before the result is observed:

```text
REGISTER
  -> freeze canonical ResearchSpec hash
  -> execute
  -> observe performance result
  -> append immutable result event
```

The inverse sequence is forbidden:

```text
execute -> inspect favorable result -> register only the winner
```

The contract records timestamps as UTC ISO-8601 instants with sufficient precision and records the clock/source policy version. `registered_at < performance_observed_at` is necessary, but not by itself sufficient: Certification also validates the applicable policy, data/window provenance, and evidence integrity.

`UNREGISTERED_RESULT = NON_CERTIFIABLE`. It is not silently discarded: a `PROTOCOL_VIOLATION_RECORDED` event preserves that a result existed and why it is ineligible, without importing sealed-OOS contents or confidential artifact payloads.

## 6. Immutable ResearchSpec and TrialRegistration contract

`ResearchSpec` is the performance-bearing immutable research specification. It is canonicalized with a versioned, deterministic representation: stable field ordering, explicit null handling, normalized identifiers, normalized UTC times, and no presentation-only fields. `canonical_research_spec_sha256` is calculated from **ResearchSpec only**.

`TrialRegistration` is one intended research-evaluation instance that references the frozen ResearchSpec. `trial_id` is a ledger-generated opaque immutable registration identity, not a content hash. A later implementation may use UUIDv7 under a recorded identifier-format version; consumers must treat it as opaque.

| ResearchSpec field group | Required fields or fingerprints | Contract rule |
|---|---|---|
| Generator and hypothesis | `generator`, `generator_version`, `hypothesis_id` or `hypothesis_hash` | Generator identity/version are evidence, not authority. |
| Factor, model, and parameters | `factor_spec_hash`, `model_spec_hash`, `hyperparameter_hash` | A material change creates a new ResearchSpec hash. |
| Data and labels | `dataset_snapshot_id`, `universe_id` or `universe_hash`, `label_spec_hash`, `feature_set_hash` | References are immutable and versioned; raw data stays outside the ledger. |
| Windows and calendar | `train_window`, `validation_window`, exchange/calendar convention | Bounds, inclusivity, timezone, and calendar version must be explicit. |
| Portfolio/evaluation assumptions | `portfolio_rule_hash`, `cost_assumption_hash`, `benchmark_policy_hash` | Performance-bearing assumptions cannot be rewritten after feedback. |
| Runtime provenance | `git_commit_sha`, `environment_fingerprint`, `random_seed` | A missing seed is explicitly recorded, never implied. |
| Family-policy inputs | `family_policy_inputs_hash` and declared inputs as applicable | Inputs support a deterministic family assignment; the resulting registration membership is separate. |

`canonical_research_spec_sha256` **must not include** `trial_id`, `idempotency_key`, `request_id`, `registered_at`, `registration_actor`, `execution_id`, a result, or performance metrics. It also excludes sealed-OOS contents, account data, broker credentials, and artifact payloads. A future Certification linkage may carry only an opaque Certification-controlled identifier.

| TrialRegistration field | Contract rule |
|---|---|
| `trial_id` | Opaque, ledger-generated registration identity. |
| `canonical_research_spec_sha256` | Immutable reference to exactly one ResearchSpec. |
| `trial_family_id`, `parent_trial_id`, `trial_kind` | Registration/lineage facts; `parent_trial_id` never turns a child into an update of its parent. |
| `registration_actor`, `registered_at`, `schema_version` | Immutable registration evidence. |
| idempotency evidence | Stores the actor-scoped idempotency key and canonical registration-request hash; it is never part of the ResearchSpec hash. |

Two intentional independent evaluations may validly use the same `canonical_research_spec_sha256` with different `trial_id` and different idempotency keys. A material ResearchSpec change requires both a new `canonical_research_spec_sha256` and a new `trial_id`. An exact reproducibility replay remains an execution linked to the original ResearchSpec and TrialRegistration, not a new independent hypothesis.

## 7. Lifecycle and append-only event model

The authoritative lifecycle is a globally ordered, append-only event stream. Public contract operations never update or delete an existing ResearchSpec, TrialRegistration, execution record, or event.

```text
TRIAL_REGISTERED
  -> TRIAL_STARTED
  -> TRIAL_COMPLETED | TRIAL_FAILED | TRIAL_CANCELLED

RESULT_ATTACHED
ARTIFACT_ATTACHED
REPLAY_LINKED
PROTOCOL_VIOLATION_RECORDED
FAMILY_POLICY_APPLIED
```

Each authoritative event contains at least: `event_id`, `trial_id` (or protocol-violation linkage), per-trial `event_sequence`, globally monotonic `ledger_sequence`, event type, UTC `occurred_at`, actor, contract/schema version, canonical event-payload hash, `previous_global_event_hash`, and `global_event_hash`. Per-trial sequence remains useful for lifecycle reads; the global sequence is the authoritative ordering across every trial stream.

`ledger_sequence` is assigned once and never reused by the normal public API. `global_event_hash` commits to the canonical event payload, its `ledger_sequence`, and `previous_global_event_hash`. Consequently, a deletion, insertion, or reordering of an event—including deletion of an entire trial stream—creates a sequence gap or global-chain mismatch when verified against retained snapshot/export anchors. Snapshot manifests and backups record the latest `ledger_sequence` and `global_event_hash` so that the chain has an externally retained verification point.

This is tamper-evident evidence, not a claim that a privileged storage administrator cannot alter the database and every unanchored copy. The future implementation may use a SQLite transaction to atomically assign the global sequence and hashes; it must not rely on caller discipline.

Valid transition checks fail closed. For example, a `RESULT_ATTACHED` must link to an already registered trial and a declared execution record; it cannot alter any field in the stored ResearchSpec or TrialRegistration. A failure does not disappear if a later execution succeeds. A cancellation is a retained terminal event for that execution, not deletion of the trial.

## 8. Idempotency, repeats, and replays

Registration accepts three distinct identifiers:

| Identifier | Scope and purpose | Retry behavior |
|---|---|---|
| `request_id` | One transport delivery/correlation record. It may differ on a retransmission. | Trace only; never creates trial identity. |
| `idempotency_key` | Stable client key for one intended registration request, scoped to `registration_actor`. | Same key plus identical canonical registration request returns the original `trial_id`. |
| `canonical_research_spec_sha256` | Frozen content identity of ResearchSpec only. | Evidence of identical research specifications; it is not globally unique trial identity. |

The ledger records a canonical registration-request hash that includes registration semantics and its ResearchSpec reference, but not as an input to `canonical_research_spec_sha256`. A unique constraint on `(registration_actor, idempotency_key)` makes exact transport retry idempotent. Reusing that key with a different canonical request is rejected and recorded as a protocol error; it must never silently register a changed specification.

An **intentional independent evaluation** uses a new idempotency key, a new `trial_id`, and `trial_kind = INDEPENDENT_EVALUATION`; it may reference the same `canonical_research_spec_sha256` and a parent/lineage trial. Certification decides whether and how it contributes to a selected trial set.

An **exact reproducibility replay** creates a new immutable execution record, not a new independent hypothesis trial. It must use `trial_kind = REPRODUCIBILITY_REPLAY`, link to the original `trial_id`, and assert the same frozen ResearchSpec/data/code/environment/seed inputs. Any mismatch is a material mutation and requires a new ResearchSpec hash and trial.

## 9. Trial families and anti-gaming rules

`trial_family_id` groups related searches such as one factor family across parameter searches, one hypothesis across model variants, or one dataset/label across hyperparameter variants. It is assigned at registration through a declared `family_policy_id` and `family_policy_version`, or derived by that already-declared deterministic policy. The assignment basis and policy inputs are retained.

The original registered family assignment is immutable. A changed interpretation cannot overwrite it. If a later policy version is genuinely necessary, it creates an append-only `FAMILY_POLICY_APPLIED` event with its policy identifier/version, actor, reason, effective scope, and a reproducible derived-membership reference. Historical snapshots continue to return the original view.

For Certification eligibility, the family policy/version governing a selected set must be declared before performance feedback for those included trials. A later remapping remains auditable research history but cannot silently shrink an already relevant family after favorable results. Certification—not the ledger and not a generator—selects the policy version and derives its denominator.

## 10. Read-only evidence outputs for Certification

The ledger provides immutable, versioned snapshots rather than statistical conclusions.

| Output | Contents | Explicitly excluded |
|---|---|---|
| `TrialHistorySnapshot` | Globally ordered registrations, execution/lifecycle events, result/artifact references, failure and violation counts, lineage, ResearchSpec provenance hashes, and global-chain anchor | DSR, PBO, promotion decision, sealed-OOS contents |
| `TrialFamilySnapshot` | Registered and policy-versioned family membership, variation history, family assignment evidence | A declaration that a family is the correct statistical denominator |
| `SelectionHistorySummary` | Total registered attempts, performance-evaluated count, pre-evaluation failures, replay count, parameter/model/factor/data/window history | `DSR_NB_TRIALS`, `PBO_SELECTION_SET`, `SPA_MODEL_SET` |

Every snapshot includes `snapshot_id`, `as_of_event_id`, `as_of_ledger_sequence`, `global_event_hash`, UTC creation time, canonical query/policy reference, schema versions, deterministic ordering, and a content hash. Certification consumes the snapshot read-only and records the snapshot ID/hash with its independently owned policy and decision. A snapshot is a fact boundary: it cannot issue `CertificationDecision` or mutate the ledger.

```text
Trial Ledger
  -> immutable TrialHistorySnapshot
  -> Certification (policy-owned selected sets)
      -> DSR / PBO / arch SPA, RealityCheck, StepM, MCS / other evidence
      -> CertificationDecision
```

## 11. MLflow, Qlib, RD-Agent, skfolio, and arch

| System | Role under this contract | Stable linkage |
|---|---|---|
| MLflow | Optional experiment/artifact visualization backend; not ledger authority. | `mlflow_experiment_id`, `mlflow_run_id` |
| Qlib Recorder | Native research metrics/artifacts; not attempt/selection authority. | `qlib_recorder_id` |
| RD-Agent / future AlphaGPT | Future generators that must register before eligible execution. | `generator`, generator version, registered `trial_id` |
| skfolio | Temporal-CV and portfolio/risk algorithm provider. Certification owns temporal policy and split authority. | Certification evidence reference, never a ledger mutation |
| arch | Multiple-comparison statistical evidence provider only. It consumes Certification-prepared inputs. | Certification evidence reference, never a ledger mutation |

An MLflow or Qlib Recorder failure must not remove the registered trial. The ledger records the failed/missing external reference and lifecycle evidence. Conversely, a standalone MLflow run cannot make an unregistered result certifiable.

## 12. Storage decision — design only

**Authoritative recommendation: SQLite as the local Trial Ledger metadata store.** It is Windows-compatible, durable, transactional, compact relative to artifacts, supports deterministic queries and backup/export, and avoids a distributed database for this personal/local project. This is a design decision, not authorization to create a database.

| Candidate | Strengths | Contract limitation | Decision |
|---|---|---|---|
| SQLite | ACID transactions, unique constraints, foreign keys, indexes, crash recovery, compact single-file backup | Requires an explicit schema/migration and single-writer/concurrency policy | **AUTHORITATIVE** |
| JSONL/files | Human-readable, simple append/export | Cannot alone reliably enforce idempotency, atomic cross-record registration, foreign keys, or concurrent writer semantics | Export/interchange only, not authority |
| Existing MLflow storage | Existing metrics/artifacts and UI | Does not preserve this project's immutable registration/family/policy boundary or fail-closed admission rules | Linked evidence only, not authority |

### 12.1 Conceptual SQLite schema

| Table / view | Purpose and key constraints |
|---|---|
| `schema_metadata` | Schema and migration versions; never infer interpretation from application version alone. |
| `research_specs` | One immutable canonical ResearchSpec per `canonical_research_spec_sha256`; no public update/delete operation. |
| `trial_registrations` | One immutable registration per `trial_id`, referencing `canonical_research_spec_sha256`, lineage/family/kind facts, and registration metadata. |
| `registration_idempotency` | `(registration_actor, idempotency_key)` unique; stores canonical registration-request hash and admitted `trial_id`, separate from ResearchSpec identity. |
| `execution_records` | Every execution/replay/attempt with immutable execution ID, kind, original-trial linkage, and lifecycle state evidence. |
| `trial_events` | Append-only stream with unique `ledger_sequence`, unique `(trial_id, event_sequence)`, `previous_global_event_hash`, and `global_event_hash`. |
| `result_references` / `artifact_references` | Immutable external references, content hashes, and provenance; artifact retention state does not delete history. |
| `family_policy_versions` | Registered family-policy texts/hashes and versions. |
| `family_assignment_events` | Immutable registered and later policy-versioned membership observations. |
| `snapshot_manifests` | Deterministic snapshot query/policy/hash/as-of evidence, including global sequence/hash anchors. |

Foreign keys prevent orphaned event/reference records. Registration commits the ResearchSpec (if not already retained), TrialRegistration, idempotency record, and `TRIAL_REGISTERED` event in one transaction; an incomplete transaction is not a registration. Appending an event validates the state transition and atomically assigns both per-trial and global sequence/hash values. Required query indexes include trial family/policy, global and per-trial event sequence, parent lineage, generator/version, dataset/window references, and immutable snapshot `as_of_ledger_sequence` lookup.

### 12.2 Durability, concurrency, migration, and export

- The implementation must use SQLite transactions and run `PRAGMA integrity_check` in a recorded maintenance/backup procedure; a failed check blocks authoritative snapshot issuance until investigated.
- Concurrent registration uses a documented local single-writer/transaction policy. It must be tested; no caller may implement read-modify-write outside the ledger transaction boundary.
- Append-only enforcement uses both a narrow application/public write API **and** database-level controls where practical: no public `UPDATE`/`DELETE` path; SQLite constraints and foreign keys; and triggers that reject `UPDATE`/`DELETE` on immutable authoritative tables unless an explicit, versioned migration/maintenance mode is invoked. Such maintenance mode is itself recorded and may never silently erase historical semantics.
- WAL is a conditional implementation choice, not an automatic requirement. It may be enabled only after local concurrent-reader/crash/backup tests demonstrate it is appropriate. If used, online backup/checkpoint handling must be documented so copied backups are consistent. A rollback-journal configuration remains acceptable if it meets the same durability tests.
- Schema migration is append-preserving: pre-migration database copy, versioned migration plan, integrity check, deterministic before/after export comparison, and rollback procedure. No migration may delete or rewrite historical semantics.
- Backup/export produces a SQLite backup plus deterministic, canonical JSONL/CSV-style manifests ordered by `ledger_sequence`. Export includes schema/policy versions, content hashes, and global-chain anchors, never sealed-OOS content.

## 13. Fail-closed invariants

1. No Certification-eligible result exists without prior committed registration.
2. A frozen ResearchSpec and TrialRegistration cannot be edited through the normal contract.
3. A result/event cannot change its original ResearchSpec or TrialRegistration.
4. Failed and cancelled attempts remain visible.
5. Exact transport retries are idempotent.
6. Replays are linked and classified; they cannot masquerade as independent hypotheses.
7. A material ResearchSpec mutation creates a new `canonical_research_spec_sha256` and a new `trial_id`.
8. A generator cannot reduce trial history through public operations.
9. A trial family cannot be opportunistically rewritten after feedback; later mappings are versioned events.
10. Certification reads immutable snapshots and has no silent ledger-write path.
11. Sealed-OOS contents never enter the Research Trial Ledger.
12. Promotion authority remains outside the ledger.
13. Artifact deletion or external-run failure cannot delete experiment metadata/history.
14. All recorded clock fields use the canonical UTC representation and record their time-source policy.
15. Every schema, canonicalization, family-policy, and interpretation-affecting policy version is recorded.
16. An idempotency key reused for different canonical registration content is rejected, never repurposed.
17. A snapshot carries an immutable as-of boundary, `ledger_sequence`, global hash anchor, and deterministic content hash.
18. Every authoritative event has a unique, monotonically increasing `ledger_sequence` and commits to the prior global event hash.
19. Public API and database-level controls reject normal updates/deletes of immutable authoritative records.

Any violation blocks Certification eligibility for the affected evidence until an independently recorded policy disposition exists. Recording a violation does not erase it.

## 14. Future implementation test matrix

| Test | Required future assertion |
|---|---|
| `REGISTER_BEFORE_EXECUTION` | Registration commits ResearchSpec/hash, TrialRegistration, and event before an execution record may start. |
| `DUPLICATE_TRANSPORT_RETRY` | Same actor/idempotency key/canonical request returns the original `trial_id` and adds no independent trial. |
| `INTENTIONAL_REPEAT` | New idempotency key and independent-evaluation intent create a distinct trial with explicit lineage. |
| `SAME_RESEARCH_SPEC_INTENTIONAL_REPEAT` | Same `canonical_research_spec_sha256` with a new intentional idempotency key creates a different `trial_id`. |
| `RESEARCH_SPEC_HASH_EXCLUDES_REGISTRATION_METADATA` | Changing `trial_id`, `request_id`, `idempotency_key`, `registered_at`, actor, execution ID, result, or metrics does not change the ResearchSpec hash. |
| `RESEARCH_SPEC_MUTATION_CHANGES_HASH` | A material performance-bearing ResearchSpec change produces a different canonical ResearchSpec hash. |
| `EXACT_REPLAY` | Exact frozen inputs create a linked replay execution, not a new independent hypothesis trial. |
| `SPEC_MUTATION_REJECTED` | Attempted update of frozen ResearchSpec/TrialRegistration fields fails and is audited. |
| `NEW_SPEC_NEW_TRIAL` | Material changed ResearchSpec produces a new hash and `trial_id`; parent remains unchanged. |
| `FAILURE_RETAINED` | Pre-evaluation infrastructure failure persists in snapshot/export after subsequent activity. |
| `RESULT_WITHOUT_REGISTRATION_REJECTED` | Eligible result append fails; violation evidence is retained as non-certifiable. |
| `FAMILY_REWRITE_REJECTED` | Original family membership cannot be overwritten after feedback. |
| `CRASH_RESTART_PRESERVES_HISTORY` | Interrupted transactions do not create partial registration/event state; committed history survives restart. |
| `CONCURRENT_REGISTRATION` | Competing registrations preserve unique idempotency and valid event ordering. |
| `GLOBAL_EVENT_DELETE_DETECTED` | Removal of any anchored global event, including a whole trial stream, creates a sequence/hash-anchor verification failure. |
| `GLOBAL_EVENT_REORDER_DETECTED` | Reordered events fail global sequence/hash-chain verification. |
| `GLOBAL_EVENT_INSERTION_DETECTED` | Inserted event without a valid globally chained transaction fails verification. |
| `DATABASE_UPDATE_IMMUTABILITY` | Database-level controls reject normal `UPDATE` of authoritative immutable rows. |
| `DATABASE_DELETE_IMMUTABILITY` | Database-level controls reject normal `DELETE` of authoritative immutable rows. |
| `READ_ONLY_CERTIFICATION_SNAPSHOT` | Certification consumer can reproduce a snapshot but has no mutation operation. |
| `MLFLOW_RUN_MISSING_HISTORY_RETAINED` | Missing/failed MLflow linkage does not remove registration/lifecycle history. |
| `ARTIFACT_DELETED_METADATA_RETAINED` | Artifact retention-state change leaves trial/result metadata and prior reference auditable. |
| `SEALED_OOS_DATA_REJECTED` | Sealed-OOS payloads/contents are rejected; only authorized opaque IDs can be linked. |
| `DETERMINISTIC_EXPORT` | Same as-of boundary produces byte-stable canonical export/hash. |
| `SCHEMA_MIGRATION_PRESERVES_HISTORY` | Versioned migration preserves all historical ResearchSpecs, TrialRegistrations, and events and validates before/after manifests. |

## 15. Open design questions before implementation authorization

1. Define the authenticated local actor model and how a human, local generator, and future service identity are represented without granting raw database write access.
2. Select the canonical ResearchSpec serialization standard and identifier format version, then publish test vectors before an implementation is accepted.
3. Define the Certification-owned family-policy registration workflow, including how a late policy-version event is marked ineligible for retroactive favorable remapping.
4. Set concrete local backup cadence, retention, restore drill cadence, and storage-budget thresholds under the 256 GB policy.
5. Define the artifact-reference retention-state vocabulary and evidence location rules while preserving no sealed-OOS content in Research storage.

These questions do not authorize P1 experimentation. They are implementation-entry decisions for a separately authorized task.

## 16. Current project state

This contract is pre-P1 safety infrastructure design only. It does not change the global phase.

```text
P0 = COMPLETE
P1 = NOT_STARTED
CURRENT_NEXT = P1_MINIMAL_QUANT

CODE_CHANGED = NO
PACKAGES_CHANGED = NO
DATABASE_CREATED = NO
QLIB_EXECUTED = NO
RDAGENT_EXECUTED = NO
OPENBB_CALLED = NO
ROBINHOOD_TOOLS_INVOKED = NONE
TRADING_ACTIONS = NONE
```
