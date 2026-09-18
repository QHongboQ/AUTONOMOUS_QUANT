# P5 Fundamental Historical Dataset Design 001

## Outcome

```text
TASK = AUTONOMOUS-QUANT-P5-FUNDAMENTAL-HISTORICAL-DATASET-DESIGN-001
EPISODE_SEC_CIK_BINDING_CONTRACT = REQUIRED
UNRESOLVED_IDENTITY_POLICY = FAIL_CLOSED
NO_SURVIVORSHIP_LEAK_DESIGN = PASS
FILING_UNIVERSE = 10-K; 10-Q; 10-K/A; 10-Q/A
EIGHT_K_ROLE = PRELIMINARY_OR_EVENT_EVIDENCE
EDGARTOOLS_STANDARDIZATION_FIT = PARTIAL
FUNDAMENTAL_EFFECTIVE_SESSION_POLICY = FIRST_XNYS_SESSION_WITH_OPEN_STRICTLY_AFTER_FIRST_AVAILABLE_AT
ASOF_PROJECTION_OWNER = pandas.merge_asof
HISTORICAL_STORAGE_FORMAT = PARTITIONED_PARQUET_PLUS_MANIFEST_PLUS_DVC
SOURCE_RETENTION_POLICY = BOUNDED_HYBRID_FAIL_CLOSED
FULL_SEC_MIRROR = NO
QLIB_FUNDAMENTAL_HANDOFF = StaticDataLoader_TO_DataHandlerLP_TO_DatasetH
PRETRAIN_EVIDENCE_LOOKBACK_POLICY = DEPENDENT_ON_FROZEN_FACTOR_INPUT_SEMANTICS
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_DEVELOPMENT_NEXT = P5_FOUNDATION_CLOSEOUT_AND_DATASET_BUILD_PILOT_GATE_001
FINAL_CLASSIFICATION = PASS
```

This task freezes a design; it does not build a historical dataset. It preserves
the active P2 authority:

```text
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
```

## Authority chain and identity policy

The only allowed traversal direction is:

```text
P1 historical InstrumentEpisodeV1
  -> date-valid EpisodeSecCikBindingV1
  -> SEC filer CIK
  -> historical SEC accessions
```

The full P1 authority currently contains 832 episodes. The representative CIK
POC remains authoritative: six of eight cases passed, old DD remains ambiguous,
and old CEG remains missing authority. Neither case may be filled by a current
ticker table, current issuer continuity, name or price similarity, or current
S&P 500 membership.

```text
UNRESOLVED_EPISODE_FUNDAMENTAL_POLICY = NO_AUTHORITATIVE_FUNDAMENTAL_DATA_UNTIL_BINDING_EXISTS
CURRENT_TICKER_TO_CIK_BACKFILL = PROHIBITED
CURRENT_SP500_SURVIVOR_LIST = PROHIBITED
```

`EpisodeSecCikBindingV1` is required as the minimum persistent project-specific
identity contract. It contains exactly:

```text
episode_id
cik
valid_from
valid_to
binding_classification
evidence_source_identities
binding_id
```

Only `PASS_EXACT` and `PASS_CORROBORATED` produce binding records. Ambiguous,
missing-authority, and no-SEC-filer outcomes live in a separate exclusion
ledger so they remain observable without manufacturing a nullable or fake CIK.
The later implementation must validate the frozen P1 episode, ten-digit CIK,
half-open contained interval, nonempty evidence identities, deterministic RFC
8785/SHA-256 `binding_id`, duplicates, and conflicting interval overlaps. It
must not silently cross-walk full-P1 and P2-window episode IDs.

## Coverage accounting

The first build pilot measures rather than optimizes coverage. Episode-level
accounting reports total episodes, full authoritative bindings, bounded partial
bindings, ambiguity, missing authority, and no SEC filer. Full means the union
of admitted binding intervals covers the complete P1 episode interval;
partial means at least one admitted interval exists but leaves a gap.

Session-weighted accounting uses pinned XNYS sessions and reports:

```text
eligible PIT episode-sessions
episode-sessions with exactly one authoritative CIK binding
episode-sessions without an admissible CIK binding
```

No arbitrary coverage percentage is accepted by this design. No-filer and
unresolved episodes remain in the eligible denominator when their P1 episode
and membership are otherwise eligible.

## Filing and raw evidence authority

SEC EDGAR owns filing source, accession, and acceptance authority. EdgarTools
5.58.0 owns CIK-based retrieval and filing/XBRL parsing. The initial periodic
inventory is `10-K`, `10-Q`, `10-K/A`, and `10-Q/A`. Every amendment is a
distinct accession and becomes visible only at its own acceptance time. An
`8-K` is `PRELIMINARY_OR_EVENT_EVIDENCE`; it cannot replace periodic facts
unless a later preregistered semantic rule explicitly admits a particular
preliminary metric.

`FundamentalEvidenceV1` remains the immutable raw authority:

```text
ONE_ACCESSION
  -> ONE_AVAILABILITY_VINTAGE
  -> FundamentalEvidenceV1
```

It preserves original taxonomy, concept, value, unit, period or instant,
context, dimensions, accession, SEC acceptance time, source identity, source
hash, and EdgarTools identity. The raw layer is append-by-vintage and is never
rewritten by a restatement.

## EdgarTools standardization boundary

EdgarTools standardization is `PARTIAL`, not blocked. The installed runtime
provides direct semantics for the initial vocabulary:

```text
Revenue
Net Income
Total Assets
Total Liabilities
Total Stockholders' Equity
Net Cash from Operating Activities
Cash and Cash Equivalents
Total Current Assets
Total Current Liabilities
Short Term Debt
Long Term Debt
```

Capital expenditures and shares outstanding are not admitted because the
installed standard-concept authority does not provide adequate semantics for
them. A single Total Debt metric is also withheld: combining short- and
long-term debt is later domain/factor semantics, not a synonym mapping. Raw
facts remain available for future explicit admission.

The [EdgarTools standardization reference](https://edgartools.readthedocs.io/en/latest/xbrl/concepts/standardization/)
documents standard concepts while preserving filer labels, and its
[fact query interface](https://edgartools.readthedocs.io/en/latest/xbrl-querying/)
exposes period, unit, context, and dimensions. Installed-source inspection also
found that `XBRLS.from_filings` defaults to filtering amendments and stitched
facts retain a source filing index rather than the complete accession and SEC
acceptance boundary. `Financials`, `MultiFinancials`, and statement stitching
are therefore convenience views only; every accepted value must reconcile to
the accession-bound raw evidence.

## Effective session and restatement policy

`exchange_calendars==4.13.2` with `XNYS` is the only session authority. All
timestamps are timezone-aware UTC. The frozen rule is:

```text
effective_session =
  the first XNYS session s for which session_open_utc(s) > first_available_at_utc
```

Consequently, an acceptance before open is available that session; an
acceptance exactly at or after open is available next session; after-close,
weekend, and holiday acceptances are available on the next XNYS session.
`filing_date` is never used as the availability boundary.

For the same semantic fact and report-period identity, the original is visible
before an amendment's effective session. On and after that session, the latest
eligible acceptance vintage may supersede it, while both raw records remain.
Ties are resolved only by acceptance timestamp, accession, and evidence ID—
never by model or factor performance.

## Session projection and membership

The authoritative Qlib runtime already contains pandas 2.3.3 and does not
contain Polars. The selected primitive is
[`pandas.merge_asof`](https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html)
with an ascending time key, `direction="backward"`, exact effective-session
matches allowed, and grouping by CIK, standardized metric, and period class.
AQ owns only eligibility, deterministic ordering, and vintage precedence; it
does not own a generic as-of engine.

The left relation is the eligible episode/session/CIK grid. The right relation
is the standardized accession-vintage event stream linked to evidence IDs.
Before joining, an episode and its CIK binding must both contain the requested
session. Where active PIT membership is required, the membership interval must
also contain it. There is no row before `episode.valid_from`, at or after
`episode.valid_to`, or outside required active membership. Carrying a valid
event through an upstream as-of join does not forward-fill or duplicate the
raw evidence store.

## Physical store, source retention, and replay

The physical design is partitioned Parquet plus a manifest and DVC seal. Raw
events partition only by `first_available_year`; rows sort by CIK, availability
time, accession, and evidence ID. The session projection partitions only by
session year. This bounds file counts and supports the common time-range scan
without high-cardinality CIK directories. PyArrow owns writes and reads; a
sealed snapshot is written to a new root with existing-data errors rather than
mutated. The [PyArrow Dataset API](https://arrow.apache.org/docs/python/generated/pyarrow.dataset.dataset.html)
provides partition discovery, projection, filtering, and multi-file reads.

`FundamentalDatasetSnapshotV1` is not required: DVC plus the immutable manifest,
`EpisodeSecCikBindingV1`, and `FundamentalEvidenceV1` already identify the
artifact. The manifest must contain authority hashes, binding/evidence manifest
identities, upstream versions, XNYS authority, partition inventory, row counts,
artifact hashes, and the quality-report hash.

The 108,050,632 bytes observed for five new SEC candidate submissions rejects
a full mirror. The policy is a bounded hybrid:

- always retain compact evidence, binding evidence, accession/acceptance/source
  metadata, hashes, amendment/restatement replay bytes, identity-decision bytes,
  adjudication fixtures, manifests, and any source for which byte-identical
  reacquisition has not been proven;
- cache complete submissions and unselected attachments only within a bounded
  build/troubleshooting window;
- evict only redundant bytes with no decision or offline-replay role after all
  admitted evidence and provenance are sealed and the eviction is recorded;
- accept a later re-download only if SHA-256 exactly matches the retained
  source identity. A mismatch fails closed.

No claim of SEC byte-stable re-download is made.

## Lookback, Qlib handoff, and quality

The global pre-2015 start is deliberately not guessed:

```text
PRETRAIN_EVIDENCE_LOOKBACK_POLICY = DEPENDENT_ON_FROZEN_FACTOR_INPUT_SEMANTICS
```

For the bounded pilot, each selected CIK traverses backward from 2015-04-01
only until it has at least five distinct fiscal-quarter endpoints and two
distinct fiscal-year endpoints available by that date, including amendments
for selected periods. This is enough to test one-year YoY, TTM, and prior-year
balance-sheet availability without freezing a global calendar start.

The selected native handoff is:

```text
session-projection Parquet
  -> Qlib StaticDataLoader
  -> DataHandlerLP
  -> DatasetH with existing train/valid/historical-test segments
```

The [Qlib data layer](https://qlib.readthedocs.io/en/latest/component/data.html)
retains loading, handling, segmentation, and research consumption. The future
table uses `(datetime, instrument)` with frozen fundamental fields. Missing
values stay missing; no feature, model, or backtest is authorized here.

The mandatory quality report measures episode and session-weighted binding
coverage, filing/accession/form counts, acceptance and source-hash completeness,
XBRL parsing, standardized metric coverage and missingness, dimensions,
duplicate evidence IDs, effective-session validity, membership alignment,
identity exclusions, runtime, storage, and retention classes. Hard failures
include duplicate evidence IDs, missing authoritative timestamps/hashes,
invalid effective sessions, projection outside episode/membership intervals,
untraceable projected values, history rewrites, or sealed-OOS access.

## Bounded next pilot

The next pilot starts from the six admitted POC cases, keeps old DD and old CEG
as negative tests, and deterministically adds the lexicographically smallest
fully bound TRAIN/VALID-era amendment case only if the six do not already
contain one. It uses multiple CIKs, a rename/reuse case, and original/amendment
vintages. It initially accesses TRAIN and VALID only and measures identity,
filing, metric, storage, runtime, session, amendment, offline-replay, and Qlib
handoff evidence. It performs no factor creation, training, prediction,
backtest, historical-test performance access, or sealed-OOS access.

## Ownership and non-actions

```text
AQ_SECURITY_MASTER = NO
AQ_SEC_CRAWLER = NO
AQ_SEC_HTTP_CLIENT = NO
AQ_XBRL_ENGINE = NO
AQ_STATEMENT_ENGINE = NO
AQ_STANDARDIZATION_ENGINE = NO
AQ_GENERIC_ASOF_ENGINE = NO
AQ_GENERIC_DATA_WAREHOUSE = NO
AQ_GENERIC_ETL = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0

P2_V2_SEALED_OOS_ACCESSED = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P5_HISTORICAL_DATASET_BUILT = NO
```

## Private design evidence

Fourteen JSON design artifacts were validated under:

```text
D:/AQ_DATA/P5/fundamental-historical-dataset-design-001/
```

The authoritative summary is:

```text
PRIVATE_REPORT = D:/AQ_DATA/P5/fundamental-historical-dataset-design-001/design_summary.json
PRIVATE_REPORT_SHA256 = 1d7ddf23f2351ec5fe2f949005382d2b1a2bf3973695dcf70398d030286a7755
```
