# Trial Ledger runtime foundation 001

**Task:** `AUTONOMOUS-QUANT-TRIAL-LEDGER-RUNTIME-FOUNDATION-COMPLETION-001`

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
ledger identity, schema version, global sequence, prior global hash, event
type, actor, trial identity/null, and canonical payload. Chain verification
requires sequence one, contiguous sequence, the zero-hash genesis predecessor,
and recomputed hashes. A retained anchor also fails verification if the local
database is truncated below its sequence.

ResearchSpec canonicalization is `AQ_RESEARCH_SPEC_CANONICAL_V1`; anchor
canonicalization is `AQ_LEDGER_ANCHOR_CANONICAL_V1`. The explicit ResearchSpec
boundary rejects registration/result/sealed-OOS metadata including nested
forms, non-string mapping keys, lone surrogates, unknown top-level fields, and
native binary floats in declared decimal fields. Only designated semantic-text
fields are NFC-normalized; opaque identifiers are left byte-distinct.

The 17-test `unittest` matrix passed under CPython 3.12.14. It covers canonical
vectors and rejection cases; genesis; actor/capability/policy lifecycle;
idempotency; registration; execution, replay and references; protocol
violations; foreign keys; all table trigger coverage; tamper/anchor detection;
deterministic snapshots; backup/restore and clean-process reopen; and actual
multi-threaded distinct and duplicate registration races. The required
`compileall` command passed after the same source changes.

Windows CPython 3.12.14 and Ubuntu-24.04 `python3` produced identical bytes
and this SHA-256 for the shared committed canonical vector:

```text
11a98432b8ce042da7620003344499b1796a1b27cf1f82b40a74457991dc996b
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
