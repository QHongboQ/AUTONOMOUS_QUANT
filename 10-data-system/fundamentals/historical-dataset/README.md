# P5 minimal upstream historical fundamentals

This leaf reads the externally supplied, hash-frozen SEC `companyfacts.zip` and
`submissions.zip` without a network fallback. `p5-minimal-upstream-v1.json`
freezes their identities, the 711 bound CIKs, five exact-acceptance exclusions,
and the ordered ten-concept P5 V1 inventory. `ShortTermDebt` is retired from V1;
its raw SEC source is not rewritten.

The `p5_bulk_fundamentals` DVC stage uses EdgarTools 5.58.0's EntityFacts parser,
native synonym groups, and duration classifier. SEC Submissions is canonical
for `(CIK, accession, form, acceptanceDateTime)`. A fact without exact acceptance
is excluded, never assigned a filed-date proxy. The existing
`FundamentalEvidenceV1` contract retains raw fact and source identity. AQ keeps
only exact admission, provenance, XNYS effective-session, membership/CIK
containment, consolidated-only, and missingness policy.

`p5_pit_projection` retains native period streams separately, chooses the most
recent economic period visible in each stream, and applies the existing
`pandas.merge_asof` PIT join. Older comparative facts and amendments remain in
bulk evidence; a late amendment to an obsolete period does not regress the
current feature. No quarterization, TTM, currency conversion, or inferred
acceptance is performed. Identity-excluded sessions remain present with missing
fundamentals.

The Qlib handoff uses `StaticDataLoader` → `DataHandlerLP` → `DatasetH` and does
not fit a model, predict, or backtest. `p5-v1-qlib-period-selection.json`
freezes `DURATION_ANNUAL` for Revenue, NetIncome, and
NetCashFromOperatingActivities, and `INSTANT` for the seven stock features.
There is no fallback or derivation: an unavailable selected stream remains
null. Non-selected native period streams remain in the evidence/projection
layer and are excluded only from this ten-column evaluation view.

DVC owns the bulk, projection, and Qlib handoff stages. PyArrow/Parquet stores
tables, Pandera validates the bounded schemas, and Qlib owns dataset reading.
No AQ SEC client, retry/checkpoint engine, XBRL parser, statement engine,
workflow runner, source mirror, or SQLite state is active here. The former
36,206-accession selective implementation remains historical evidence only;
its executable runner and pilot sealer are retired from production.

## Production LOC contraction

The repository-wide P5 production inventory uses the established physical-line
counting rule. It contracts from 2,849 to 2,053 lines (796 retired), but does
not reach the aspirational 1,600-line target. The surviving lines are not a
hidden replacement engine:

| Module | LOC | Surviving responsibility |
| --- | ---: | --- |
| Episode-to-CIK binding | 312 | Existing immutable episode/CIK contract and validation |
| Valuein identity leaf | 181 | Existing exact-only external identity evidence leaf |
| FundamentalEvidenceV1 contract | 164 | Existing immutable evidence schema and identities |
| Fundamental evidence materializer | 204 | Existing EdgarTools projection plus bounded bulk-fact projection |
| Filing-feature package surface | 17 | Existing public exports |
| Filing-feature contract | 157 | Existing five-feature immutable observation contract |
| Filing-feature materializer | 217 | Existing exact five-feature policy projection |
| Frozen SEC bulk reader | 279 | Hash/source validation, native EdgarTools parsing, exact Submissions join |
| Historical thin policy | 213 | Ten concepts, XNYS visibility, containment, consolidated admission |
| PIT projection | 170 | P1 session grid, non-regressing vintage selection, `merge_asof` glue |
| Qlib handoff | 139 | Fixed ten-column selection and public Qlib dataset validation |

Further contraction would require removing an existing public contract or
combining distinct evidence, identity, filing-feature, PIT, and Qlib ownership
boundaries. No generic abstraction was introduced to conceal those lines.
