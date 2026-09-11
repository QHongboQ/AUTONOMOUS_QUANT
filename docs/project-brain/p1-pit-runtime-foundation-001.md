# P1 PIT Runtime Foundation 001

**Task:** `AUTONOMOUS-QUANT-P1-PIT-RUNTIME-FOUNDATION-001`

**Result:** `PASS`

**Base:** `167b14ea6cf88be28c0fe5649f65cab077adde97` (`origin/main`)

**Branch:** `agent/p1-pit-runtime-foundation-001`

**Evidence commit:** the commit containing this document

## Implemented boundary

The compact leaf `10-data-system/universe/sp500-pit` implements the first
production-intended `InstrumentEpisodeV1` runtime from the approved blueprint.
The implementation is standard-library only. It contains no full security
master, company identity, corporate-lineage graph, price-series stitching,
network client, market data, model, backtest, or RD-Agent integration.

The runtime includes frozen and explicitly versioned contracts for
`SourceManifestV1`, `IndexMembershipEventV1`, `TickerIdentityEventV1`,
`CorporateActionEventV1`, `SnapshotObservationV1`,
`TickerEpisodeOverlayV1`, `MembershipCorrectionV1`,
`InstrumentEpisodeV1`, `ValidationFindingV1`, and `CompilePolicyV1`.

## Canonical and source authority semantics

Canonical records use strict UTF-8 JSON, sorted object keys, contract-defined
tuple ordering, and SHA-256. Authoritative hashing rejects floats,
NaN/Infinity by construction, unsupported objects, and absolute local paths in
logical IDs. Episode identity includes its schema, index, normalized ticker,
half-open validity/membership bounds, and sorted contributing source/event
identities; it is never ticker-only and has no clock or physical-path input.

Source roles are enforced at compilation. A historical seed must cite a
`HISTORICAL_SEED` manifest; membership, ticker-identity, and correction events
must cite their accepted evidence roles. Shared ancestry is represented and a
shared ancestor is explicitly not an independent vote. No majority-voting path
exists.

## Episode, event, and overlay semantics

Membership `ADD` and `REMOVE` are separate from ticker identity events. An
active `OLD -> NEW` event closes `OLD` and opens `NEW` at the supplied effective
session, preserving continuous membership while producing different episode
IDs. Announcement dates never activate a ticker. All intervals are `[from,
to)`; exit/re-entry is non-contiguous and therefore receives a new ID.

The core does not guess exchange sessions. All normalized events carry an
`effective_session`; `AMBIGUOUS` boundary or identity state produces a
structured unresolved error and no resolved transition.

The backfill detector generically reports `FUTURE_TICKER_BEFORE_RENAME` and
`STALE_OLD_TICKER_AFTER_RENAME` from event and observation rows. An accepted
`TickerEpisodeOverlayV1` may map a successor observation back to its predecessor
before the boundary. Raw evidence remains immutable. Overlay content is part of
episode provenance and compilation hashes. There are zero symbol-specific
conditions in runtime code.

`CorporateActionEventV1` is retained in canonical compilation evidence but is
firewalled from membership state. Merger, spin-off, and acquisition context
cannot add, remove, or rename an index member. Only a typed membership event or
accepted evidence-backed correction can change membership.

## Structured gates

The runtime defines all required finding types: ambiguous source boundary,
add-present, remove-absent, duplicate event/episode, overlapping ticker
episodes, future/stale rename observations, ambiguous ticker episode, missing
evidence, unresolved correction, year continuity break, and terminal set
mismatch. Findings have deterministic IDs, severity, affected IDs, messages,
and resolution state.

`validate_publishable` requires only `RESOLVED` episodes and zero unresolved
`ERROR`/`CRITICAL` findings. It has no percentage or unexplained-defect
tolerance. An undated reused-ticker lookup raises
`AMBIGUOUS_TICKER_EPISODE`; a date-scoped lookup must resolve exactly one
non-overlapping episode.

## Verification evidence

The full local suite passed under CPython 3.13.15 and the existing uv-managed
CPython 3.12.14:

```text
TOTAL_TEST_COUNT = 51
TEST_RESULT = PASS
REGRESSION_COUNT = 13
REGRESSION_RESULT = PASS
COMPILEALL = PASS
LINT = NOT_CONFIGURED
TYPECHECK = NOT_CONFIGURED
```

All frozen regressions passed:

| Regression | Result | Proven property |
|---|---|---|
| R01 `MMM` date | PASS | Invalid ISO date rejected |
| R02 `FB -> META` | PASS | Adjacent distinct episodes at 2022-06-09 |
| R03 `CDAY -> DAY` | PASS | No early successor after overlay |
| R04 `RE -> EG` | PASS | Adjacent episodes at 2023-07-10 |
| R05 `WLTW -> WTW` | PASS | Announcement does not activate early |
| R06 `KORS -> CPRI` | PASS | No `CPRI` before 2019-01-02 |
| R07 `Q -> IQV` | PASS | Adjacent rename plus distinct historical `Q` |
| R08 old/new `DLPH` | PASS | Separate non-overlapping IDs; undated ambiguity |
| R09 `DISCK` / `WBD` | PASS | Corporate context alone cannot transfer membership |
| R10 `APTV` guard | PASS | Generic overlay prevents pre-2017-12-05 successor |
| R11 `CPRI` guard | PASS | Generic overlay prevents pre-2019-01-02 successor |
| R12 `IQV` guard | PASS | Generic overlay prevents pre-2017-11-15 successor |
| R13 fictional `XYZ` reuse | PASS | Separate IDs, gap, dated resolution, undated failure |

Additional tests cover deterministic canonical hashes; absolute-path exclusion;
source mutation; immutable contracts; ancestry; event separation; source-role
enforcement; add/remove failure; re-entry; ambiguous boundaries; duplicate
canonical events; unresolved correction/publication; accepted correction;
overlap; overlay provenance mutation; raw-input immutability; and identical
output from repeated compilation.

## Independent-review closeout

The initial foundation at
`56e393373daaa6ec651e4fc690e251eb5167a4fc` passed its original 43 tests,
but independent review found four bounded state-corruption defects: foreign
index membership inputs were not isolated, `IGNORE_EVENT` targets could be
collected before correction authority validation, an accepted overlay could
suppress a future-ticker finding without actually applying, and duplicate
`source_id` values were silently reduced by dictionary construction.

The closeout fixes all four paths. Foreign-index events/corrections now emit a
blocking structured finding and cannot mutate state. Only a same-index,
officially sourced, accepted correction targeting a real membership event can
suppress that event. Overlay detection suppression consumes only the exact
observation/event pairs returned by the single successful application path.
Duplicate source IDs are removed from authority and emit `ERROR` when identical
or `CRITICAL` when conflicting. Eight focused tests cover these cases; all 43
original tests and all 13 frozen regressions remain passing.

This closeout adds no architecture or contract schema. Market-data ticker
validity, pre-membership price history, permanent security identity, and
corporate lineage remain intentionally deferred. No real source data was
ingested.

## Known limitations and next authority

This task uses tiny in-memory fixtures only. It does not implement source
adapters, exchange-calendar normalization, persistent DatasetSnapshot output,
real year/terminal reconciliation evidence, or authoritative 2010–2024
membership. The compiler intentionally requires one start-session seed;
source-ingestion work must produce that seed and normalized typed events before
full compilation is authorized.

```text
P0 = COMPLETE
P1 = STARTED
P1_PIT_RUNTIME_FOUNDATION = COMPLETE
CURRENT_NEXT = P1_PIT_SOURCE_INGESTION
P1_MINIMAL_QUANT = IN_PROGRESS
REAL_2010_2024_DATA_INGESTED = NO
MARKET_DATA_COLLECTED = NO
MODEL_TRAINED = NO
PERFORMANCE_EVALUATED = NO
BACKTEST_RUN = NO
RDAGENT_EXECUTED = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
```
