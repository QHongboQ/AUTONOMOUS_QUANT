# S&P 500 PIT research-ready universe

The single active P1 path is `aq_pit.build_research_ready_universe`. It converts
the pinned FJA snapshot shape, applies immutable accepted facts, derives
identity-aware membership transitions, constructs episodes, and runs the small
research-ready gate. The stable output row contains only `episode_id`, `ticker`,
`membership_from`, and `membership_to`.

It deliberately does not implement a permanent security master, corporate
lineage, price history, price stitching, source downloading, or a published
2010–2024 universe.

## Active responsibilities

- `adapters/fja.py` — pinned external source shape to observations only.
- `facts/accepted_reconciliation_facts.json` — the 37 accepted findings, 20
  identity boundaries, and 9 observation-overlay cases as declarative facts.
- `domain` — thin membership, identity, overlay, and episode semantics.
- `schema/pandera` — generic table-boundary shape, type, null, format,
  uniqueness, structural enum, and simple interval validation, pinned to
  `pandera==0.33.1` through its leaf-local dependency declaration.
- `gates/research_ready` — bounded domain assertions and black-box count oracle.
- `export` — primitive research-universe rows for a future DatasetSnapshot.
- `thin_runtime.py` — parent composition; this is the only active P1 PIT path.

The sibling XNYS calendar leaf remains unchanged. This path requires no calendar
calculation because its pinned input already consists of effective sessions.

Pandera owns no membership or identity truth, reconciliation fact, calendar
semantics, market data, or certification decision. Domain objects remain plain
immutable AQ contracts; pandas and Pandera objects do not cross the leaf.

## Retained reference oracle

`compiler.py`, `contracts.py`, `overlays.py`, `validation.py`,
`sources/fja_sp500.py`, and `scripts/run_fja_ingestion.py` are
`KEEP_ORACLE_TEST_ONLY`. They preserve the 93 pre-stack behavioral tests and 13
frozen regressions, but are not exported or imported by the active composition.
They are not a second active pipeline. Corporate-action context, generic
correction/authority machinery, terminal comparison, evidence publication, and
certification are inactive in P1. Strict institutional certification belongs to
P2. Historical Git evidence is preserved.

## Research-ready invariants

- A rename closes the old ticker episode and opens the new one at the same
  session without manufacturing membership events.
- Exit and later re-entry create different episode IDs.
- Undated lookup of reused ticker text fails with
  `AMBIGUOUS_TICKER_EPISODE`.
- `ADD_PRESENT`, `REMOVE_ABSENT`, overlaps, unexplained successor/predecessor
  labels, incomplete fact accounting, or nondeterminism block research output.
- Only accepted declarative observation overlays affect state; raw bytes and
  normalized observations are never rewritten.
- Reconciled membership derivation transforms the prior roster through accepted
  identity events before diffing, so ticker changes cannot manufacture churn.
- Absolute machine paths, floats, unsupported objects, clocks, hostnames,
  caches, and network state do not participate in logical identity.

Wikipedia terminal comparison is diagnostic only and cannot control the P1
research-ready result. `PIT_UNIVERSE_RESEARCH_READY = YES` does not mean
`PIT_UNIVERSE_CERTIFIED`; certification remains `NO`.

## Verification

From this directory:

```text
set AQ_PIT_DATA_ROOT=D:\AQ_DATA\P1\pit
python -m unittest discover -s tests -v
python -m compileall -q aq_pit tests
```

The committed suite uses only tiny local fixtures and includes all 13 frozen
blueprint regressions. No source or market data is downloaded.
