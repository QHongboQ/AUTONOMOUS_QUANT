# P5 EdgarTools Native Full-Universe Build Design 001

## Decision

The full-universe historical fundamentals build design is complete and passes
its authorization gate. The build itself was not run.

```text
FULL_UNIVERSE_NATIVE_BUILD_DESIGN = PASS
FULL_HISTORICAL_BUILD_AUTHORIZED = YES
P5_HISTORICAL_DATASET_BUILT = NO
CURRENT_DEVELOPMENT_NEXT = P5_EDGARTOOLS_NATIVE_FULL_UNIVERSE_HISTORICAL_BUILD_001
```

The upstream ownership audit was squash-merged through PR #63. Its source head
was `2b322b8eb3294e614af1bb1f1a73c087c2466b9a`, its base was
`73e4bdb92cde3e224f34cb70b8eac5e00fc246c8`, and the resulting main anchor is
`d0e0f5e3cfc8e5a8aa3c0d3a0a7df7261dfd15c1`. The former diagnostic census
branch remains unmerged evidence only; its useful measurements are retained,
but its domestic-form whitelist and missing-FSDS-quarter hard gate are not
current authority.

## Frozen ownership

| Capability | Owner |
| --- | --- |
| Filing source, accession, acceptance time, source bytes | SEC EDGAR |
| Issuer-aware filing discovery, typed financial statements, XBRL and raw facts | EdgarTools 5.58.0 |
| Optional bulk hints, acceleration and offline cross-check | secfsdstools |
| CIK binding, PIT eligibility, provenance admission and thin contracts | AQ |
| XNYS sessions and opens | exchange_calendars |
| Session projection | pandas `merge_asof` |
| Parquet persistence and reproducibility identity | PyArrow and DVC |
| Research consumption | Qlib |

The audit authority is frozen at 711 addressable bound CIKs. EdgarTools exposes
a native financial surface for 708; FRC, MJN and LXK remain
`TRUE_NO_PERIODIC_FINANCIAL_COVERAGE`. FCPT remains outside episode timing and
CCEP remains on the native foreign-issuer path. No AQ form router, SEC client,
XBRL engine, statement engine, filing-index engine, generic ETL or data
warehouse is introduced.

## Population and ingestion modes

```text
TOTAL_P1_EPISODES = 832
BOUND_EPISODES = 721
EXCLUDED_IDENTITY_EPISODES = 111
UNIQUE_BOUND_CIK_COUNT = 711

HISTORICAL_INGESTION_MODE = ONE_TIME_HISTORICAL_BACKFILL_PLUS_IMMUTABLE_POINT_IN_TIME_VINTAGES
LIVE_INGESTION_MODE = INCREMENTAL_NEW_ACCESSION_ONLY
FULL_HISTORY_REREAD_PER_LIVE_CYCLE = NO
FULL_SUBMISSION_MIRROR = PROHIBITED
```

The 111 identity exclusions remain present in the P1 universe and denominator,
but cannot produce fundamentals without an authoritative date-valid CIK. The
design does not reopen identity work.

Live ingestion is deliberately separate from the historical backfill. A future
watcher may use SEC current/latest filings through EdgarTools, deduplicate by
accession, require an accepted CIK, parse only the new accession, append an
immutable vintage, and advance an accession checkpoint. No watcher is
implemented here.

## Historical build stages

The authorized build shape has ten explicit stages:

1. Validate `InstrumentEpisodeV1`, `EpisodeSecCikBindingV1` and exclusions.
2. Enumerate issuer-aware filing metadata through `Company(CIK)`.
3. Acquire bounded accession source sets from SEC EDGAR.
4. Extract native typed financial/XBRL facts with EdgarTools.
5. Materialize provenance-complete `FundamentalEvidenceV1` records.
6. Project standardized, period-class-isolated consolidated events.
7. Assign the first XNYS session whose open is strictly after SEC acceptance.
8. Project sparse events onto eligible sessions with `pandas.merge_asof`.
9. Seal Parquet outputs and dependency identity with DVC.
10. Validate the Qlib handoff without training, prediction or backtesting.

Every admitted fact must retain CIK, accession, acceptance datetime, form,
report period, taxonomy, raw concept, raw value, unit, context, dimensions,
source hashes and EdgarTools runtime identity. Convenience statements are for
semantic discovery and validation only; they cannot erase accession/raw-fact
lineage.

## Native eligibility and foreign issuers

Enumeration uses native filing metadata predicates instead of a project-owned
form whitelist. A candidate must belong to the accepted CIK population, have a
unique accession and timezone-aware acceptance timestamp, fall within the
authorized time bounds, expose a native typed financial or XBRL surface, and
have no conflicting CIK/source identity.

Domestic and foreign issuers use the same pipeline. EdgarTools owns native
10-K/20-F/40-F and 10-Q/6-K fallback behavior. IFRS facts retain their native
taxonomy-qualified raw concepts. A 6-K enters structured fundamentals only
when EdgarTools establishes a native structured financial/XBRL surface;
otherwise it remains outside this dataset for later event/news work.

## Period, dimension and amendment policy

Annual, quarterly/interim, instant and other duration streams remain isolated.
The frozen period classes are:

```text
INSTANT
DURATION_QUARTERLY
DURATION_SEMI_ANNUAL
DURATION_NINE_MONTHS
DURATION_ANNUAL
DURATION_OTHER
```

The stream key is CIK plus EdgarTools standard concept ID plus period class.
No quarterization is inferred and instant/duration values are not mixed.

Raw dimension evidence is retained. The first standardized feature surface is
`CONSOLIDATED_ONLY`, with no silent aggregation or dimension collapse.
Amendments are separate immutable accessions and become visible only from their
own effective session. They never overwrite the original vintage backward in
time.

## Batching and recovery

Enumeration is partitioned into stable ordered batches of at most 25 CIKs.
Extraction is partitioned primarily by acceptance year, then ordered accession
batch, with a ceiling of 200 accessions or 2 GiB of temporary source bytes,
whichever comes first. Outputs partition by acceptance year and CIK prefix.

The recovery unit is one accession. A completed ledger records source and
output hashes, terminal status, evidence count, runtime version and build-spec
identity. Transient network/SEC failures receive at most three bounded attempts.
A deterministic parser failure on unchanged bytes is not blindly retried.
Resume skips an accession only when its checkpoint identity and all hashes
match.

Final sealing is prohibited unless every eligible accession has a non-failure
terminal status and there are zero `FAILED_REQUIRED_ACCESSION` rows. One bad
filing is isolated, but it cannot be hidden by sealing a partial build.

## Selective retention and storage

The 629+ GiB provider-reported complete-submission corpus is not mirrored.
Each accession retains only the exact parser-consumed primary filing and XBRL
source assets, metadata, relative paths, byte counts, SHA-256 values, runtime
identity, admitted evidence and terminal classification. Redundant caches,
rendered HTML, unused attachments and in-memory objects are released after the
accession seals.

The 256 GiB storage plan is:

| Surface | GiB |
| --- | ---: |
| Exact parser-consumed source assets | 120 |
| FundamentalEvidenceV1 Parquet | 20 |
| Standardized events and provenance | 12 |
| Session/Qlib projection | 20 |
| Manifests, checkpoints and DVC outputs | 4 |
| Bounded temporary space | 16 |
| Unallocated headroom | 64 |
| Total | 256 |

Persistent bytes target at most 176 GiB and planned peak bytes at most 192 GiB
before headroom. The implementation task must first enumerate metadata and run
a deterministic stratified sample estimate. It must stop before full
acquisition if either threshold is projected to be exceeded; correctness may
not be weakened to fit storage.

## FSDS and Qlib boundaries

secfsdstools is `OPTIONAL_BULK_ACCELERATOR_AND_CROSSCHECK`. Missing local FSDS
quarters do not block correctness, no missing quarters were downloaded, and
AutoUpdate remains disabled. When an accession is absent from local FSDS, the
native EdgarTools/SEC path continues.

The Qlib handoff is sealed Parquet through `StaticDataLoader`, `DataHandlerLP`
and `DatasetH`. Validation requires monotonic unique session indices, zero early
visibility, zero cross-CIK contamination, period-class isolation,
consolidated-only projection, complete evidence lineage, and preservation of
the 111 excluded episodes as rows with missing fundamentals where otherwise
eligible. This task performed no training, prediction or backtest.

## Authorization gate

The following design gates pass: identity accounting; EdgarTools 5.58.0
runtime identity; issuer-aware discovery; raw-fact provenance; SEC acceptance
timestamps; period and dimension policies; amendments; bounded storage;
accession-level recovery; DVC sealing; and Qlib handoff.

```text
EDGARTOOLS_NATIVE_WHOLE_PATH_AUTHORITY = FROZEN
SECFSDSTOOLS_HARD_BUILD_GATE = RETIRED
STORAGE_PLAN_STATUS = COMPLETE
CHECKPOINT_RESUME_PLAN_STATUS = COMPLETE
QLIB_HANDOFF_PLAN_STATUS = COMPLETE
AQ_NEW_GENERIC_ENGINE_COUNT = 0
PRODUCTION_LOC_ADDED = 0
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

The private immutable design ledger is under
`D:\AQ_DATA\P5\edgartools-native-full-universe-build-design-001`. Its
`checksums.json` SHA-256 is
`bd1e8d07fdece2a11b0aafb0f26d5b1905df3802ba35f9f9ce770a4cd26232b1`.
All 16 listed design artifacts and all referenced source-authority hashes were
recomputed successfully; no credentials are present.

## Next

The next development task is
`P5_EDGARTOOLS_NATIVE_FULL_UNIVERSE_HISTORICAL_BUILD_001`. It may implement and
execute only this frozen bounded design. It must not restore FSDS quarter
completion as a correctness gate or add an AQ-owned upstream engine.
