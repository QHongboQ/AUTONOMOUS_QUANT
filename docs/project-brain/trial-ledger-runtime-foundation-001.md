# Trial Ledger runtime foundation 001

**Task:** `AUTONOMOUS-QUANT-TRIAL-LEDGER-RUNTIME-FOUNDATION-FINAL-CLOSURE-001`

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
canonicalization is `AQ_LEDGER_ANCHOR_CANONICAL_V1`. The explicit ResearchSpec
boundary now requires all V1 performance-bearing axes (factor/model/hyperparameter,
data, windows, calendar, portfolio/cost/benchmark, provenance and family input
hash). It rejects registration/result/sealed-OOS metadata including nested forms,
non-string mapping keys, lone surrogates, unknown top-level fields, and native
binary floats in schema-declared decimal parameters. Typed parameters—not callers—
govern decimal identity. Only designated semantic-text fields are NFC-normalized;
opaque identifiers are left byte-distinct.

The 28-test `unittest` matrix passed under CPython 3.12.14. It covers frozen
canonical, anchor, event-hash and deterministic-snapshot digests; V1 identity
and typed-parameter rejection; genesis; actor/capability/policy lifecycle;
idempotency; registration; execution, replay and references; protocol
violations; foreign keys; table trigger coverage; privileged linkage tampering;
historical as-of snapshot stability after future facts; external anchor-artifact
round trip/truncation detection; backup/restore and clean-process reopen; and
actual multi-threaded distinct and duplicate registration races. The required
`compileall` command passed after the same source changes.

Historical snapshots now filter every authoritative object/reference by its
immutable `created_ledger_sequence`, rather than only filtering global events.
Lifecycle projections include immutable global event IDs and fail verification
if a privileged unchained status, capability, or policy record is injected.
The external anchor primitive writes/loads a canonical manifest artifact; tests
place it in a temporary directory distinct from the temporary database.

Windows CPython 3.12.14 and Ubuntu-24.04 `python3` produced identical bytes
and this SHA-256 for the shared committed canonical vector:

```text
6043aedb32b23df715f61d9f2f9ce12d9305f0a14172c6266db9ae38ceb5dd61
```

All test databases and backups were short-lived temporary files and were
removed after validation. No permanent ledger database, external package,
Qlib, RD-Agent, OpenBB, Robinhood, P1 research, account action, or trading
action occurred.

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
