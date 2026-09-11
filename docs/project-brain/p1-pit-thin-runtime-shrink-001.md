# P1 PIT Thin Runtime Shrink 001

## Scope and result

P1 now has one active S&P 500 PIT research path:
`aq_pit.build_research_ready_universe`. Upstream Pandera owns generic table
structure and the unchanged exchange-calendars leaf owns session calculation.
AQ owns only the pinned-source adapter, accepted real-world facts, membership /
identity / episode semantics, research-ready assertions, and primitive export.

The active path is intentionally research-domain infrastructure, not a source
authority framework, artifact system, Qlib adapter, market-data pipeline, or
certification engine. It neither imports nor runs the old generic correction,
authority, terminal-reference, or publication path.

## Declarative facts and compatibility

`accepted_reconciliation_facts.json` stores the accepted knowledge outside
executable orchestration. It contains 37 canonical finding resolutions, 20
identity events, and 9 overlay cases. No accepted ticker appears as a runtime
branch in active Python.

Against the frozen local FJA source, the single active composition reproduces
the reference-oracle behavior:

| Observable | Result |
|---|---:|
| accepted findings accounted for | 37 |
| identity events | 20 |
| overlay cases | 9 |
| applied overlay rows | 3,236 |
| reconciled membership events | 630 |
| instrument episodes | 832 |

Representative tests cover DLPH/APTV, KORS/CPRI, Q/IQV, GAS, the old IR to TT
boundary plus the later distinct IR episode, and the AMD, TER, JBL, FSLR, EQT,
and PCG exit/re-entry gaps. The active gate reports no unexplained ticker
boundary, overlap, duplicate, `ADD_PRESENT`, or `REMOVE_ABSENT` error and proves
repeat compilation deterministic. Undated reused-ticker lookup remains
fail-closed.

## Active ownership and deferred code

| Area | Classification | Reason |
|---|---|---|
| `thin_runtime.py`, `adapters`, `domain`, `facts`, `gates/research_ready`, `export` | ACTIVE_P1 | single research-ready path |
| Pandera leaf | UPSTREAM_ACTIVE | generic structural validation only |
| XNYS calendar leaf | UPSTREAM_UNCHANGED | public sibling contract; no mutation |
| old compiler/contracts/overlays/validation/source adapter and ingestion script | KEEP_ORACLE_TEST_ONLY | preserves 93 prior behavioral tests and 13 frozen regressions; not imported/exported by active path |
| generic corrections, authority, publication and terminal certification | DEFER_P2 | no P1 research-readiness responsibility |

There is no second active PIT pipeline. The package root exports only the thin
research composition. Historical implementations remain reviewable in Git and
testable as a black-box oracle.

## Production LOC accounting

Method: nonblank, non-comment physical Python lines. Tests, docs, declarative
JSON, upstream/vendor code, and code classified `KEEP_ORACLE_TEST_ONLY` after
the shrink are excluded. The before baseline is the production PIT Python path
at stack base `d82c7fd58d4533642a57a7eba607e30ff9e4d432`; the after set is the
transitive active research path and its script.

| File | Before | After | Delta | Action |
|---|---:|---:|---:|---|
| `aq_pit/__init__.py` | 29 | 6 | -23 | thin public surface |
| `aq_pit/canonical.py` | 64 | 64 | 0 | shared deterministic IDs |
| `aq_pit/compiler.py` | 497 | 0 | -497 | KEEP_ORACLE_TEST_ONLY |
| `aq_pit/contracts.py` | 393 | 0 | -393 | KEEP_ORACLE_TEST_ONLY |
| `aq_pit/overlays.py` | 254 | 0 | -254 | KEEP_ORACLE_TEST_ONLY |
| `aq_pit/validation.py` | 146 | 0 | -146 | KEEP_ORACLE_TEST_ONLY |
| `aq_pit/sources/__init__.py` | 23 | 0 | -23 | KEEP_ORACLE_TEST_ONLY |
| `aq_pit/sources/fja_sp500.py` | 433 | 0 | -433 | KEEP_ORACLE_TEST_ONLY |
| `scripts/run_fja_ingestion.py` | 564 | 0 | -564 | KEEP_ORACLE_TEST_ONLY |
| `aq_pit/schema/__init__.py` | 1 | 1 | 0 | retained upstream boundary |
| `aq_pit/schema/pandera/__init__.py` | 15 | 15 | 0 | retained upstream boundary |
| `aq_pit/schema/pandera/boundaries.py` | 240 | 240 | 0 | retained upstream boundary |
| `aq_pit/adapters/__init__.py` | 0 | 3 | +3 | active thin adapter |
| `aq_pit/adapters/fja.py` | 0 | 79 | +79 | active thin adapter |
| `aq_pit/domain/__init__.py` | 0 | 17 | +17 | active domain surface |
| `aq_pit/domain/models.py` | 0 | 157 | +157 | minimum active contracts |
| `aq_pit/domain/thin.py` | 0 | 330 | +330 | generic domain composition |
| `aq_pit/facts/__init__.py` | 0 | 9 | +9 | declarative-facts surface |
| `aq_pit/facts/accepted.py` | 0 | 101 | +101 | immutable facts loader |
| `aq_pit/gates/__init__.py` | 0 | 1 | +1 | namespace |
| `aq_pit/gates/research_ready/__init__.py` | 0 | 3 | +3 | gate surface |
| `aq_pit/gates/research_ready/gate.py` | 0 | 146 | +146 | research assertions |
| `aq_pit/export/__init__.py` | 0 | 3 | +3 | export surface |
| `aq_pit/export/rows.py` | 0 | 27 | +27 | primitive output rows |
| `aq_pit/thin_runtime.py` | 0 | 36 | +36 | single parent composition |
| `scripts/build_research_ready_universe.py` | 0 | 32 | +32 | single active CLI |
| **Total active production PIT LOC** | **2,659** | **1,270** | **-1,389** | **responsibility shrink** |

The zero after-count for oracle-only files means they are excluded from the
active production path, not deleted from Git. They remain solely to run the
required frozen behavioral suite. No test was removed or reclassified to make
the count smaller.

## State and non-actions

```text
P0 = COMPLETE
P1 = STARTED
P1_MINIMAL_QUANT = IN_PROGRESS
P1_PIT_THIN_RUNTIME = COMPLETE
PIT_ACTIVE_RESPONSIBILITY = THIN_RESEARCH_DOMAIN_ADAPTER
PIT_UNIVERSE_RESEARCH_READY = YES
PIT_UNIVERSE_CERTIFIED = NO
P2_CERTIFICATION_ACTIVE_IN_P1 = NO
CURRENT_NEXT = P1_MINIMAL_QUANT_RESEARCH_DATASET
DVC_ADDED = NO
QLIB_ADDED = NO
OPENBB_ADDED = NO
ZIPLINE_ADDED = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
```
