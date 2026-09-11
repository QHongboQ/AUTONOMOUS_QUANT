# P1 PIT Pandera Boundaries

Task: `AUTONOMOUS-QUANT-P1-PIT-PANDERA-BOUNDARIES-001`

Status: COMPLETE

Stack base: `a298a1a4dd9821b0b253615036663ef3373cf259`

## Ownership

`10-data-system/universe/sp500-pit/aq_pit/schema/pandera` owns only generic
tabular structure validation for the P1 PIT leaf. Its exact leaf-local upstream
dependency is `pandera[pandas]==0.33.1`.

The boundary validates required columns, column types, nullability, canonical
ISO date text, normalized ticker shape, unique identifiers, selected logical
row uniqueness, structural enum values, and simple interval ordering for:

- snapshot observations;
- membership events;
- ticker identity events;
- instrument episodes.

The decoded FJA two-column CSV also uses Pandera for generic header, type, null,
date, uniqueness, ordering, and non-empty-table checks. Roster interpretation,
source authority, pinning, hashing, and membership meaning remain AQ domain
responsibilities.

Validators return `None` or raise `ValueError`; no pandas DataFrame, Pandera
schema/error, or upstream-specific object becomes a domain or cross-tree API.

## Production boundary use

The schema leaf is invoked after FJA decoding and normalized snapshot creation,
by both membership-event derivation paths, after diagnostic identity-event
construction, and for compiler episode output when no duplicate/overlap domain
finding is present. It does not replace the compiler's structured fail-closed
findings.

## Existing helper classification

| Existing validation | Classification | Reason |
|---|---|---|
| FJA header/date/order/unique/non-empty table checks | `REPLACED_BY_PANDERA` | External generic table boundary now validates these properties. |
| `_require_text` | `KEEP_NON_TABULAR` | Scalar invariant for immutable in-memory domain contracts. |
| `_date` | `KEEP_NON_TABULAR` | Scalar domain-contract construction remains independent of tables. |
| `_hash` | `KEEP_NON_TABULAR` | Canonical content-identifier invariant, not table ownership. |
| `_sorted_unique` | `KEEP_NON_TABULAR` | Canonicalizes immutable provenance tuples. |
| `normalize_ticker` | `KEEP_DOMAIN` | One small domain normalization function; schema validates its output shape. |
| compiler `_duplicate_ids` and canonical-event duplicate checks | `KEEP_DOMAIN` | They emit deterministic domain findings and prevent authority overwrite. |
| remaining resolved-observation/context comparisons | `DEFER_TO_RUNTIME_SHRINK` | They enforce reconciliation authority, not generic table shape. |

LOC accounting counts nonblank bespoke generic-validation lines outside the
Pandera leaf in the five named helpers plus the FJA table checks. Before: 32.
After: 20. The 12 removed lines were FJA header/date/order/uniqueness/non-empty
checks now executed by the production Pandera boundary. Pandera schema/check
declarations and adapter glue are excluded from "custom validation" by this
ownership-based measure.

## Semantic firewall

Pandera does not decide membership truth, identity truth, ticker reuse,
membership gaps, reconciliation facts, evidence authority, XNYS session truth,
artifact versioning, market data, Qlib behavior, or certification. No real
symbol appears in schema implementation conditions. No generic registry,
plugin system, datasource framework, validation service, or abstract validation
engine was added.

## Verification

- Python validation runtime: 3.12.14
- pinned Pandera: 0.33.1
- new Pandera boundary tests: 14 PASS
- original authoritative-main PIT tests: 93 PASS
- frozen regressions within the PIT suite: 13 PASS
- stacked exchange-calendar tests: 11 PASS
- package dependency check: PASS
- touched Python `compileall`: PASS
- exchange-calendar leaf diff against stack base: none

PIT certification state and current-next state are unchanged. DVC, Qlib,
OpenBB, Zipline, market-data, model, account, and trading work remain outside
this task.
