# Trial Ledger implementation preconditions 001

**Task:** `AUTONOMOUS-QUANT-TRIAL-LEDGER-IMPLEMENTATION-PRECONDITIONS-001`
**Scope:** Project Brain / contract design only. This document authorizes no Trial Ledger runtime, SQLite database, package installation, upstream/environment action, P1 experiment, provider/broker access, or trading action.

## 1. Decision

The Trial Ledger contract is extended with four implementation preconditions: authenticated attribution and one writer boundary, canonical ResearchSpec serialization, pre-feedback family policy registration, and backup/restore anchoring. These are internal responsibilities of the existing leaf; they create no sibling module.

```text
30-research-system/
  experiment-registry/
    trial-ledger/
      contract       <- actor, capability, ResearchSpec, family-policy contracts
      lifecycle      <- public writer boundary and globally chained events
      storage        <- one SQLite writer, backup/restore policy
      snapshot       <- read-only snapshot and LedgerAnchorManifest evidence
```

```text
TRIAL_LEDGER_OWNER = OUR_CODE
CERTIFICATION_POLICY_OWNER = OUR_CODE
DSR_DENOMINATOR_OWNER = CERTIFICATION_POLICY / OUR_CODE
PBO_SELECTION_SET_OWNER = CERTIFICATION_POLICY / OUR_CODE
SPA_MODEL_SET_OWNER = CERTIFICATION_POLICY / OUR_CODE
PROMOTION_AUTHORITY = CERTIFICATION / OUR_CODE
```

The ledger records facts and provides immutable snapshots. It does not calculate DSR/PBO/SPA sets, issue a CertificationDecision, or promote a candidate.

## 2. Precondition 1 — actor identity and public writer boundary

### 2.1 Principle and actor identity

```text
NO_RESEARCH_CLIENT_MAY_WRITE_SQLITE_DIRECTLY = YES
ALL_NORMAL_MUTATIONS = Trial Ledger public writer boundary only
```

Display strings are attribution labels, never authentication. Every future authoritative event carries an immutable `actor_id` resolved by the writer boundary before the event is committed.

| Actor class | Example actor ID | Normal role |
|---|---|---|
| `HUMAN_OWNER` | `human:owner` | local administration and explicitly authorized governance actions |
| `SYSTEM_SERVICE` | `service:scheduler` | controlled local orchestration |
| `RESEARCH_GENERATOR` | `generator:qlib`, `generator:rdagent`, `generator:alphagpt` | request trials and append only permitted research events |
| `MIGRATION_MAINTENANCE` | `maintenance:migration` | exceptional, versioned maintenance only |

`ActorIdentity` is immutable after registration and contains:

| Field | Rule |
|---|---|
| `actor_id` | Opaque stable identifier; not inferred from a display string. |
| `actor_type` | One of the defined actor classes. |
| `actor_version` | Version of the client/process identity contract. |
| `display_name` | Human-readable attribution only. |
| `credential_binding` | Reference/handle to an OS/process-local credential or separately stored capability material; never plaintext secret material. |
| `authentication_method` | Declared verification method/version, such as local OS principal/process binding. |
| `created_at` | UTC registration evidence. |
| `metadata_schema_version` | Versioned interpretation of identity metadata. |

The ledger database stores no plaintext long-lived secret, token, password, or private credential. Local credential/capability material belongs to OS/process-local controls or a separately protected local secret location, not to the ledger.

`ActorIdentity` is an immutable registration/profile, not a mutable status row. Current effective actor status is derived from its identity plus ordered, append-only `ActorStatusEvent` records: `ACTOR_REGISTERED`, `ACTOR_ACTIVATED`, `ACTOR_SUSPENDED`, and `ACTOR_RETIRED`. No operation disables an actor by updating ActorIdentity. An inactive, suspended, or retired actor fails authorization according to that derived status; historical actor/status evidence remains queryable.

### 2.2 Capability model

Capabilities are granted to an actor identity by a versioned, auditable local policy. A capability is specific to the public writer boundary; it is not raw SQLite access.

| Capability | Meaning | Research generator |
|---|---|---|
| `TRIAL_REGISTER` | Submit a TrialRegistration referencing a canonical ResearchSpec. | permitted when granted |
| `EXECUTION_APPEND` | Append allowed lifecycle/replay/failure events for an authorized trial. | permitted when granted |
| `RESULT_ATTACH` | Attach a permitted result reference to an authorized execution. | permitted when granted |
| `ARTIFACT_ATTACH` | Attach a permitted artifact reference. | permitted when granted |
| `SNAPSHOT_READ` | Read an immutable, scoped ledger snapshot. | no default grant; Certification/owner use read-only access |
| `MAINTENANCE_ENTER` | Enter exceptional migration/maintenance mode. | prohibited |

Capability changes are also immutable lifecycle evidence: `CAPABILITY_GRANTED` and `CAPABILITY_REVOKED` reference the actor, capability, policy version, grant/revoke actor, UTC time, and reason. Effective authorization is derived from ordered capability events plus current actor status; no historical grant is rewritten in place.

`RESEARCH_GENERATOR` cannot update/delete historical facts, grant itself capabilities, enter maintenance mode, select Certification denominators, or promote. `HUMAN_OWNER` retains administration authority but still uses an explicit, audited maintenance path. `MIGRATION_MAINTENANCE` is disabled by default, short-lived, versioned, and records entry/exit, actor, reason, migration identifier, and backup/anchor references.

### 2.3 Windows / WSL writer direction

The selected future default is **one Windows-local authoritative Trial Ledger writer runtime**. It owns the SQLite database in a private Windows-local directory and may be an on-demand local process; this decision does not authorize a Windows Service, a public Internet service, or a cloud database.

```text
Windows Certification / local owner
  -> Trial Ledger public writer boundary
  -> authoritative SQLite database

WSL Qlib/RD-Agent generator
  -> authenticated public-contract request or tested local handoff adapter
  -> Windows-local writer boundary
  -> authoritative SQLite database
```

WSL generators do not directly mutate the database through `/mnt/d`, and Windows/WSL may not concurrently open the same SQLite database for writes. A future handoff adapter must preserve actor identity, request/idempotency evidence, canonical bytes/hash, and response receipt; it must be tested before use. No remote/cloud database is selected.

```text
AUTHORITATIVE_WRITER_MODEL = ONE_WINDOWS_LOCAL_SQLITE_WRITER_RUNTIME
WINDOWS_WSL_DIRECT_SHARED_SQLITE_ALLOWED = NO
```

## 3. Precondition 2 — AQ_RESEARCH_SPEC_CANONICAL_V1

`AQ_RESEARCH_SPEC_CANONICAL_V1` defines the bytes used for:

```text
canonical_research_spec_sha256 = SHA256(canonical UTF-8 bytes)
```

It applies to ResearchSpec only, never TrialRegistration metadata. The canonical envelope contains `canonicalization_version = "AQ_RESEARCH_SPEC_CANONICAL_V1"` and the validated ResearchSpec object. It excludes `trial_id`, `idempotency_key`, `request_id`, `registered_at`, `registration_actor`, `execution_id`, result references, and performance metrics.

### 3.1 Canonical JSON rules

1. Encode exactly one JSON value as UTF-8, with no byte-order mark and no insignificant whitespace.
2. Object keys are unique; duplicate keys are rejected by the input parser before canonicalization. Keys are sorted lexicographically by Unicode code point.
3. JSON uses only primitives for `true`, `false`, and `null`; locale-dependent formatting is prohibited.
4. Strings in schema-designated normalized semantic-text fields use Unicode NFC. Semantically opaque strings—hashes, opaque IDs, source identifiers, URIs, and declared literal labels—are not case-folded, trimmed, or Unicode-normalized; they are validated against their field contract instead.
5. Arrays preserve declared semantic order. A schema-marked unordered collection is sorted by each member's canonical UTF-8 representation before serialization. No caller may silently choose a collection's ordering semantics.
6. Timestamp instants require an explicit offset at input and serialize as UTC RFC3339 with exactly six fractional digits and `Z`, for example `2026-09-10T12:34:56.000000Z`. Inputs requiring rounding beyond microseconds are rejected in V1. Date-only fields serialize as `YYYY-MM-DD`.
7. Identifiers use only their declared field-specific canonical casing rules (for example, a SHA-256 hex field is lowercase). Opaque identifiers are not transformed merely to make them look similar.
8. Logical/versioned identifiers replace filesystem paths when available. An environment-dependent Windows or WSL path cannot be hashed as an alias for a logical dataset, source, or environment identifier.
9. `NaN`, `+Inf`, `-Inf`, implicit timezone values, and unknown schema/canonicalization versions are rejected.

### 3.1.1 Exact V1 JSON string bytes

The canonical writer emits permitted Unicode scalar values directly as UTF-8; it does not ASCII-escape ordinary non-ASCII characters and does not optionally escape otherwise valid Unicode. It emits no byte-order mark and no trailing newline.

- Quotation mark `U+0022` is always encoded as `\"`; reverse solidus `U+005C` is always encoded as `\\`.
- Every control character `U+0000` through `U+001F` is always encoded as a six-byte JSON escape of the form `\u00xx`, using lowercase hexadecimal digits. Short escapes such as `\n`, `\r`, `\t`, `\b`, and `\f` are forbidden in canonical output.
- Solidus `U+002F` is emitted as `/`, never `\/`.
- Lone UTF-16 surrogate code points are rejected. Valid non-BMP Unicode scalar values are emitted as their UTF-8 bytes, never as optional surrogate-pair escapes.

The implementation must not rely on a runtime/library serializer default unless its emitted bytes pass the required canonical vectors.

### 3.2 Numeric V1 rule

Performance-bearing numeric configuration values are represented in the canonical ResearchSpec as normalized **decimal strings**, never uncontrolled binary floating-point values. Input adapters parse a permitted decimal lexical form using exact decimal arithmetic before any native-float conversion.

The canonical decimal output has no leading `+`, no exponent, no leading zeros except `0`, no unnecessary trailing fractional zeros, and normalizes signed zero to `"0"`. Thus supported equivalents `"0.10"`, `"0.100"`, and `"1e-1"` canonicalize to `"0.1"`; `"5"` remains `"5"`. Examples include `"learning_rate": "0.05"`, `"transaction_cost_bps": "5"`, and `"max_weight": "0.1"`.

The schema must mark which fields are decimal-valued and which are opaque strings. It must not parse, round, or normalize an opaque identifier as a number. No final example hash is asserted by this design document; implementation acceptance requires independently reproducible exact bytes and vectors.

### 3.3 Fixed future canonicalization vectors

| Vector | Required assertion |
|---|---|
| `VECTOR_001_KEY_ORDER` | Same semantic object with different input object-key order produces identical canonical bytes/hash. |
| `VECTOR_002_REGISTRATION_METADATA_EXCLUDED` | Changed `trial_id`, idempotency key, request ID, or registration timestamp leaves ResearchSpec bytes/hash unchanged. |
| `VECTOR_003_NUMERIC_NORMALIZATION` | Equivalent supported decimal spellings (`0.10`, `0.100`, `1e-1`) produce the same canonical decimal string, bytes, and hash. |
| `VECTOR_004_MATERIAL_PARAMETER_CHANGE` | `learning_rate` `0.05` to `0.06` changes canonical bytes/hash. |
| `VECTOR_005_TIMEZONE_NORMALIZATION` | Same allowed instant with different explicit offsets serializes to the same UTC representation, bytes, and hash. |
| `NAN_REJECTED` | Non-finite numeric input is rejected before canonical bytes exist. |
| `INFINITY_REJECTED` | Infinite numeric input is rejected before canonical bytes exist. |
| `DUPLICATE_KEY_REJECTED` | Duplicate JSON key is rejected before canonicalization. |
| `NAIVE_DATETIME_REJECTED` | Timestamp with no explicit timezone is rejected. |
| `UNKNOWN_SCHEMA_VERSION_REJECTED` | Unknown schema/canonicalization version is rejected. |
| `UNICODE_UTF8_CANONICAL` | Permitted non-ASCII Unicode emits direct UTF-8 bytes with no optional ASCII escape. |
| `ESCAPE_QUOTE_CANONICAL` | Quotation mark emits exactly `\"`. |
| `ESCAPE_BACKSLASH_CANONICAL` | Reverse solidus emits exactly `\\`. |
| `CONTROL_CHARACTER_CANONICAL` | Every `U+0000`–`U+001F` control character emits lowercase `\u00xx`, never a short escape. |
| `SOLIDUS_NOT_ESCAPED` | Solidus emits `/`, never `\/`. |
| `LONE_SURROGATE_REJECTED` | A lone surrogate is rejected before canonical bytes exist. |
| `NO_TRAILING_NEWLINE` | Canonical output ends with the final JSON byte, not a newline. |
| `WINDOWS_WSL_BYTE_IDENTITY` | Supported Windows and WSL contexts emit byte-identical canonical JSON and SHA-256 for the same ResearchSpec. |

```text
CANONICALIZATION_VERSION = AQ_RESEARCH_SPEC_CANONICAL_V1
CANONICALIZATION_V1_CLOSED = YES
```

## 4. Precondition 3 — FamilyPolicySpec registration workflow

Family-policy authority is Certification/Governance policy owned by our code. Research generators supply declared policy inputs; they do not choose favorable families after observing performance.

`FamilyPolicySpec` is one immutable policy version and contains `family_policy_id`, `family_policy_version`, `policy_schema_version`, `policy_text_or_rules_hash`, `effective_from`, `registered_at`, `registered_by`, and `canonical_policy_hash`. A policy meaning/ruleset change requires a new version and a new policy hash.

```text
Certification / Governance
  -> register FamilyPolicySpec
  -> freeze version and canonical policy hash
  -> TrialRegistration references policy
  -> deterministic trial_family_id assignment
  -> performance evaluated later
```

`trial_family_id` is a deterministic identifier derived from the declared `family_policy_id`, `family_policy_version`, and canonical family-policy input fields. The related family-assignment evidence is canonicalized and hashed. It cannot use observed performance, result rank, or later selection outcome.

```text
FAMILY_POLICY_REGISTERED_BEFORE_FEEDBACK = YES
```

Later policy versions may form a separately labelled analytical view but cannot overwrite the original assignment. The original policy and family evidence remain queryable, the new version has an explicit effective boundary, and retroactive favorable remapping is `NON_CERTIFIABLE` for the affected historical selection claim unless an independent policy allowed that exact use before feedback.

Policy lifecycle is separate append-only evidence: `FAMILY_POLICY_REGISTERED`, `FAMILY_POLICY_ACTIVATED`, and `FAMILY_POLICY_RETIRED`. No immutable FamilyPolicySpec row is updated merely to change status. Retiring a version prevents new use according to the derived current status but never removes its historical queryability.

### P1 conservative default — design only

`P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1` is the default for the future P1 baseline model tournament, not a universal future policy. Related variants share one broad search family when they share dataset snapshot, universe, label, feature family, research objective, and evaluation-window policy—even if model type or hyperparameters differ. Linear/Ridge, LightGBM, XGBoost, CatBoost, and DoubleEnsemble therefore cannot claim unrelated statistical discoveries solely because implementations differ.

```text
FAMILY_POLICY_OWNER = CERTIFICATION_POLICY / OUR_CODE
FAMILY_POLICY_WORKFLOW_CLOSED = YES
P1_DEFAULT_FAMILY_POLICY = P1_MODEL_TOURNAMENT_FAMILY_POLICY_V1
```

## 5. Precondition 4 — backup, restore, and independent anchor policy

The authoritative SQLite database is metadata-small but statistically critical. It is never stored in Git. A live database is backed up only with SQLite-supported consistent backup semantics, never by blindly copying a live database file.

| Trigger | Minimum required action |
|---|---|
| Periodic local operation | One consistent backup at least once per local operating day in which the ledger changed. |
| Certification boundary | Consistent backup and anchor before and after an important Certification snapshot/decision. |
| Migration | Mandatory verified backup/anchor before every schema migration. |
| Retention | Keep at least 7 daily, 4 weekly, and 12 monthly backups. |
| Restore drill | At least monthly during active development/operation and mandatory before production activation. |

A restore drill validates SQLite integrity, schema version, deterministic snapshot/export, the complete global event hash chain, and the selected anchor. Existing historical data is never silently recreated or reset to make a drill pass.

### 5.1 LedgerAnchorManifest

`LedgerAnchorManifestPayload` is the immutable payload with `ledger_id`, `as_of_ledger_sequence`, `global_event_hash`, database/schema version, `created_at`, `created_by`, and `manifest_schema_version`. Its canonicalization version is `AQ_LEDGER_ANCHOR_CANONICAL_V1`, a separately versioned anchor schema that may reuse primitive JSON rules but is not assumed identical to ResearchSpec.

```text
manifest_sha256 = SHA256(canonical UTF-8 bytes of LedgerAnchorManifestPayload)
LedgerAnchorManifest = { payload, manifest_sha256 }
ANCHOR_MANIFEST_HASH_SELF_REFERENTIAL = NO
```

`manifest_sha256` never hashes an envelope that already includes `manifest_sha256`. Verification recomputes the digest from payload bytes, rejects a wrong digest, and validates the payload schema/version before trusting an anchor.

Required future tests are `ANCHOR_HASH_EXCLUDES_DIGEST_FIELD`, `ANCHOR_PAYLOAD_MUTATION_CHANGES_HASH`, `ANCHOR_DIGEST_REPRODUCIBLE`, and `ANCHOR_WRONG_DIGEST_REJECTED`.

For P1/local development, a separately written backup/anchor artifact outside the authoritative database directory is sufficient. The primary SQLite database and anchor must not rely solely on the same mutable file. Before production/live authorization, at least one independent backup/anchor destination outside the authoritative database directory is required. This policy selects neither public GitHub storage nor a cloud vendor and never exposes private research metadata or experiment counts publicly.

### 5.2 Fail-closed restoration rule

If `integrity_check` fails, global hash-chain verification fails, an anchor mismatches, a required migration backup is absent, or restore verification fails, then:

```text
AUTHORITATIVE_SNAPSHOT_ISSUANCE = BLOCKED
```

The failure is retained as evidence. No new authoritative Certification snapshot may issue until the failure is independently resolved and recorded.

```text
BACKUP_RESTORE_POLICY_CLOSED = YES
DAILY_BACKUP = ON_CHANGED_LOCAL_OPERATING_DAY
CERTIFICATION_BOUNDARY_BACKUP = BEFORE_AND_AFTER_IMPORTANT_SNAPSHOT_OR_DECISION
MIGRATION_BACKUP = MANDATORY
RETENTION_POLICY = 7_DAILY / 4_WEEKLY / 12_MONTHLY
RESTORE_DRILL = MONTHLY_ACTIVE_OPERATION_AND_PRE_PRODUCTION
INDEPENDENT_ANCHOR_DEFINED = YES
ANCHOR_CANONICALIZATION_VERSION = AQ_LEDGER_ANCHOR_CANONICAL_V1
```

## 6. Implementation readiness

```text
ACTOR_MODEL_CLOSED = YES
CANONICALIZATION_V1_CLOSED = YES
FAMILY_POLICY_WORKFLOW_CLOSED = YES
BACKUP_RESTORE_POLICY_CLOSED = YES
IMPLEMENTATION_READY = YES
REMAINING_IMPLEMENTATION_BLOCKERS = NONE
```

This means the contract is ready for a separately authorized local runtime implementation task. It does not itself authorize that task, create a database, or start P1.

Future lifecycle tests additionally require `ACTOR_STATUS_APPEND_ONLY`, `SUSPENDED_ACTOR_WRITE_REJECTED`, `CAPABILITY_GRANT_APPEND_ONLY`, `CAPABILITY_REVOKE_EFFECTIVE`, `HISTORICAL_CAPABILITY_EVIDENCE_RETAINED`, `FAMILY_POLICY_STATUS_APPEND_ONLY`, `RETIRED_POLICY_HISTORY_RETAINED`, and `POLICY_RULE_CHANGE_REQUIRES_NEW_VERSION`.

## 7. Current project state and non-actions

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
