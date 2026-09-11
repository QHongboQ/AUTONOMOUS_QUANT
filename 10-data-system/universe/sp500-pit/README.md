# S&P 500 PIT universe foundation

This leaf implements the first production-intended runtime boundary from the
approved open-source-assisted PIT blueprint. It compiles pinned, typed evidence
into immutable `InstrumentEpisodeV1` rows and answers only: **which ticker
episode is eligible on trading session t?**

It deliberately does not implement a permanent security master, corporate
lineage, price history, price stitching, source downloading, or a published
2010–2024 universe.

## Responsibilities

- `canonical.py` — strict UTF-8 canonical JSON and SHA-256 logical identities.
- `contracts.py` — frozen, versioned source, event, overlay, correction,
  episode, policy, and finding contracts.
- `overlays.py` — generic, episode-scoped rename detection and reviewed,
  evidence-driven observation reconciliation, including duplicate successors.
- `sources/fja_sp500.py` — preserves the historical raw exact-difference path
  and exposes a distinct identity-aware resolved-observation derivation path.
- `schema/pandera` — generic table-boundary shape, type, null, format,
  uniqueness, structural enum, and simple interval validation, pinned to
  `pandera==0.33.1` through its leaf-local dependency declaration.
- `compiler.py` — pure membership/rename state transitions over half-open
  intervals. Corporate actions are retained as context but cannot mutate
  membership.
- `validation.py` — structured reconciliation findings, date-scoped lookup,
  ticker-reuse ambiguity, overlap checks, and the fail-closed publication gate.

The compiler requires exactly one pinned `HISTORICAL_SEED` observation at the
policy start session. Normalized events must already contain a resolved trading
session; calendar conversion belongs to the sibling `trading-calendar/xnys`
leaf and is not owned by Pandera.

Pandera owns no membership or identity truth, reconciliation fact, calendar
semantics, market data, or certification decision. Domain objects remain plain
immutable AQ contracts; pandas and Pandera objects do not cross the leaf.

## Safety invariants

- A rename closes the old ticker episode and opens the new one at the same
  session without manufacturing membership events.
- Exit and later re-entry create different episode IDs.
- Undated lookup of reused ticker text fails with
  `AMBIGUOUS_TICKER_EPISODE`.
- `ADD_PRESENT`, `REMOVE_ABSENT`, ambiguous boundaries, missing evidence,
  overlaps, duplicate events, and unresolved corrections block publication.
- Only accepted overlays/corrections affect state; raw observations are frozen
  and never rewritten.
- Reconciled membership derivation transforms the prior roster through accepted
  identity events before diffing, so ticker changes cannot manufacture churn.
- Absolute machine paths, floats, unsupported objects, clocks, hostnames,
  caches, and network state do not participate in logical identity.

## Verification

From this directory:

```text
python -m unittest discover -s tests -v
python -m compileall -q aq_pit tests
```

The committed suite uses only tiny local fixtures and includes all 13 frozen
blueprint regressions. No source or market data is downloaded.
