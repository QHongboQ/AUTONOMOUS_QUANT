# Trial Ledger runtime foundation 001

**Latest task:** `AUTONOMOUS-QUANT-TRIAL-LEDGER-RUNTIME-PREMERGE-HARDENING-001`

The completed standard-library foundation is at
`30-research-system/experiment-registry/trial-ledger/aq_trial_ledger`.
The compact module tree separates canonical bytes (`canonical.py`), frozen
contract values (`contract.py`), lifecycle helpers (`lifecycle.py`), SQLite
writer/storage (`storage.py`), snapshots (`snapshot.py`), and backup/restore
verification (`backup.py`). Schema version is `1`.

## Evidence

The append-only SQLite schema protects identities, actor and capability
lifecycle facts, policy specs/events, ResearchSpec blobs, registrations and
idempotency evidence, executions, global events, references, violations, and
anchor evidence from normal UPDATE or DELETE. Actor status and capability
state are derived from ordered immutable events. Foreign keys block ordinary
orphan references.

`AQ_LEDGER_EVENT_HASH_V1` hashes a canonical event envelope containing the
ledger identity, schema version, global sequence, prior global hash, immutable
event ID, execution ID/null, occurred-at instant, event type, actor, trial
identity/null, and canonical payload. Chain verification requires sequence one,
contiguous sequence, the zero-hash genesis predecessor, recomputed hashes, and
one-to-one lifecycle-to-global-event linkage. A retained anchor also fails
verification if the local database is truncated below its sequence.

ResearchSpec canonicalization is `AQ_RESEARCH_SPEC_CANONICAL_V1`; anchor
canonicalization is `AQ_LEDGER_ANCHOR_CANONICAL_V1`. Its token-aware JSON encoder
emits direct UTF-8, a solidus unchanged, lower-case `\\u00xx` control escapes,
and separately escapes quotes and literal backslashes. It does not rewrite an
already serialized JSON string. Thus actual newline/tab values, literal `\\n` /
`\\t`, and literal `\\u000a` remain injectively distinct and strictly round-trip
through `parse_json_strict`.

The explicit ResearchSpec boundary requires all V1 performance-bearing axes
(factor/model/hyperparameter, data, windows, calendar, portfolio/cost/benchmark,
provenance and family input hash). It rejects registration/result/sealed-OOS
metadata including nested forms, non-string mapping keys, lone surrogates,
unknown top-level fields, and any native Python float recursively anywhere in
the V1 identity. Typed decimal parameters—not callers—govern decimal identity.
Only designated semantic-text fields are NFC-normalized; opaque identifiers are
left byte-distinct.

Historical integrity-closure evidence: the then-60-test `unittest` matrix
passed under CPython 3.12.14, and required
`compileall aq_trial_ledger tests` passed after the same source changes. Fixed
byte-and-SHA vectors now cover ResearchSpec, event, anchor, deterministic
snapshot, family-policy identity, actual newline/tab, literal backslash+n/t,
and literal backslash+u000a. The matrix also proves rejection of finite floats
in extensions and nested research fields; family-input hash match/mismatch;
model/hyperparameter invariance and required-axis sensitivity; and distinct
policy rules/spec hashes.

Every authorization-, idempotency-, lineage-, replay-, reference-, violation-,
and snapshot-relevant projection is content-bound to its global event; this
includes actor identity, actor status, capability, family-policy specification
and lifecycle, ResearchSpec, trial registration, idempotency mapping, execution,
result/artifact references, and protocol violations. Lifecycle projection rows
and their chained events use one occurred-at value. Privileged disposable-copy
tamper tests cover actor target/time; capability target/name/policy/reason;
family-policy ID/version; trial sequence/family; ResearchSpec blob; idempotency;
execution trial; result sequence/locator; artifact locator; and violation
content. Each fails both chain verification and snapshot issuance.

`Ledger.canonical_family_inputs` is the single deterministic source for family
assignment and `ResearchSpec.family_policy_inputs_hash`; registration rejects a
mismatch. Family policy identity separately hashes policy ID, version, schema
version, rules hash, and effective-from. Consequently `policy_rules_hash` is
not aliased as `canonical_policy_hash`.

Historical snapshots filter every authoritative object/reference by its
immutable `created_ledger_sequence` only after content/sequence binding is
verified. A snapshot at boundary N remains byte-identical after future activity,
whereas privileged mutation of an authoritative historical projection blocks
all snapshot issuance. The external anchor primitive writes/loads a canonical
manifest artifact; tests place it in a temporary directory distinct from the
temporary database.

Windows CPython 3.12.14 and Ubuntu-24.04 `python3` produced byte-for-byte
identical output and this SHA-256 for the shared committed canonical vector:

```text
a200675434f562226d4caf596cedfb41f31a2d3deaf1b8e57f0d2c6ff91f5948
```

All test databases and backups were short-lived temporary files and were
removed after validation. No permanent ledger database, external package,
Qlib, RD-Agent, OpenBB, Robinhood, P1 research, account action, or trading
action occurred.

## Runtime pre-merge hardening evidence

Normal mutations now accept an opaque `auth_context`, not a caller-selected
actor ID. The small project-owned `Authenticator` boundary resolves the acting
principal; the production-foundation default rejects every normal mutation
until an authenticator is injected. `DeterministicFakeAuthenticator` is
test-only and persists neither tokens nor credentials. Tests prove unauthenticated
and unknown contexts fail, a generator context cannot impersonate the owner,
and the resolved authenticated actor is what is recorded in chained events.
This is a local injection boundary, not an HTTP, OAuth, Internet, or credential
storage implementation.

The runtime no longer exposes a public `db` connection. SQLite is held as
private `_db`; tests use that explicitly private hook only for privileged-copy
tamper simulation. Python privacy is not a sandbox, so this removes the normal
client API write surface without claiming to contain a process with filesystem
access.

Public `snapshot(auth_context, ...)` now requires an active authenticated actor
with `SNAPSHOT_READ`. The deterministic internal verified snapshot builder is
reserved for anchor and restored-backup validation, which do not simulate an
external principal. A missing capability and a suspended actor both fail closed.

Opening an existing initialized ledger performs one full chain, projection, and
metadata verification before establishing the in-process verified head. Normal
writes use `BEGIN IMMEDIATE`, compare the persisted head to that verified head,
verify the authenticated actor's identity/status/capability against their own
chained projections, then refresh the in-process head only after commit. An
external/concurrent head change raises `EXTERNAL_OR_CONCURRENT_WRITER_DETECTED`.
Full scans remain mandatory for explicit verification, public snapshot issuance,
anchor/backup/restore validation, and startup; they are not performed once per
normal registration. The bounded smoke registered 1,000 sequential trials,
created 1,015 total events, performed one final full verification, and passed.

Trial registration kinds are now an explicit versioned allow-list containing
`INDEPENDENT_EVALUATION`. `REPRODUCIBILITY_REPLAY` remains an execution kind
only and cannot create a new trial. Capability grants verify that the target
actor is currently active; registered-only, suspended, and retired targets are
rejected, while revocation remains an auditable append-only lifecycle action.

Genesis now chain-binds `ledger_id`, schema version, event-hash domain version,
ResearchSpec canonicalization version, and anchor canonicalization version.
Open/full verification requires database metadata, supported runtime constants,
and genesis metadata to agree; five privileged-copy metadata tamper variants
are detected. ResearchSpec NFC normalization is explicitly path-scoped in V1:
only top-level `hypothesis_text`, `research_objective`, and `semantic_text`
normalize. Same-named or other Unicode values beneath `extensions` remain
opaque and byte-distinct.

The 72-test `unittest` matrix passed under CPython 3.12.14, including all prior
60 integrity tests plus authentication, raw-connection surface, `SNAPSHOT_READ`,
incremental writer-head, scale, trial-kind, active-target capability, metadata,
and schema-path normalization coverage. `compileall aq_trial_ledger tests`
passed. Windows CPython 3.12.14 and Ubuntu-24.04 `python3` again produced the
same canonical bytes and SHA-256:

```text
a200675434f562226d4caf596cedfb41f31a2d3deaf1b8e57f0d2c6ff91f5948
```

## Known limitations

The foundation is a one-process local writer rather than a deployed service.
It does not authorize P1 research, sealed-OOS access, statistical selection,
Certification decisions, or production operation. Anchor independence and
backup retention are operational policies for a later authorized deployment.

```text
P0 = COMPLETE
P1 = NOT_STARTED
CURRENT_NEXT = P1_MINIMAL_QUANT
PERMANENT_DATABASE_CREATED = NO
```
