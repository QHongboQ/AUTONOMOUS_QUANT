# Trial Ledger runtime foundation 001

**Task:** `AUTONOMOUS-QUANT-TRIAL-LEDGER-RUNTIME-FOUNDATION-001`

The standard-library foundation is implemented at `30-research-system/experiment-registry/trial-ledger/aq_trial_ledger` with leaf-local `unittest` tests. Schema version is `1`; canonicalization versions are `AQ_RESEARCH_SPEC_CANONICAL_V1` and `AQ_LEDGER_ANCHOR_CANONICAL_V1`.

The public foundation provides strict ResearchSpec bytes/SHA-256, strict JSON parsing, explicit SQLite-path construction, atomic initialization/registration, actor-scoped idempotency, immutable trial rows, append-only global events, global-chain verification, deterministic snapshots, self-excluding anchor digests, and SQLite backup primitives. Genesis uses a 64-zero previous hash. The SQLite connection enables foreign keys and a busy timeout; no WAL mode is selected.

Executed with CPython 3.12.14:

```text
py -V:Astral/CPython3.12.14 -m unittest discover -s tests -v
Ran 4 tests ... OK
py -V:Astral/CPython3.12.14 -m compileall aq_trial_ledger tests
PASS
```

The tests use only temporary SQLite databases/backups. No permanent database, external dependency, Qlib, RD-Agent, OpenBB, Robinhood, P1 research, or trading action occurred. WSL byte-identity was not executed in this bounded Windows test run; it remains a required follow-up validation before cross-runtime handoff use.

```text
P0 = COMPLETE
P1 = NOT_STARTED
CURRENT_NEXT = P1_MINIMAL_QUANT
PERMANENT_DATABASE_CREATED = NO
```
