# P6 Global News V1 streaming sufficient-statistics backfill 001

## Official raw-source authority arbitration (authoritative)

The official GDELT raw GKG 2.1 publication stream does **not** provide a clean
replacement for the defective BigQuery sentiment semantics. The arbitration
resolved every archive through the official English and Translingual master
lists and used the GKG 2.1 codebook's documented batch-prefix and stream-class
rules. A bounded, outcome-independent BigQuery sample contained exactly 40
conflicting IDs and 20 non-conflicting controls across 2015–2024. It required
only 27 unique official batch archives totaling 246,256,050 compressed bytes.
All 27 archive byte counts and MD5 identities matched the official master-list
metadata.

The raw ZIPs were streamed without retaining decompressed CSV. For every one of
the 40 conflicted IDs, the canonical archive contained two physical rows with
two distinct `(DATE, SourceCollectionIdentifier, V2Tone)` tuples. In all 40
cases those two raw tuples exactly equaled the two BigQuery variants. All 20
controls occurred once and matched BigQuery exactly. The conflict therefore
belongs to the official raw GKG publication artifacts, not merely to the
BigQuery mirror/load history. An arbitrary first-row, last-row, or other
deduplication rule remains prohibited.

The official master lists also contain 175 raw GKG batches dated 2017-08-29
(95 English and 80 Translingual). The absent BigQuery partition for that date
is therefore a BigQuery mirror coverage gap, not an upstream raw-source gap.
Master-list metadata for the frozen 2015-03-25 through 2024-12-31 interval
contains 337,124 English archives (2,553,726,973,890 compressed bytes) and
331,884 Translingual archives (3,676,360,070,274 compressed bytes), for
669,008 archives and 6,230,087,044,164 compressed bytes combined. This cost
estimate is evidence only; no full raw backfill was started.

```text
CONFLICT_SAMPLE_COUNT = 40
CONTROL_UNIQUE_ID_COUNT = 20
RAW_BATCH_ARCHIVE_COUNT_DOWNLOADED = 27
RAW_COMPRESSED_BYTES_DOWNLOADED = 246256050
RAW_ARCHIVE_HASH_VERIFICATION_PASS_COUNT = 27
RAW_ARCHIVE_HASH_VERIFICATION_FAIL_COUNT = 0
RAW_SINGLE_ROW_COUNT = 0
RAW_MULTIPLE_IDENTICAL_COUNT = 0
RAW_MULTIPLE_CONFLICT_COUNT = 40
RAW_MISSING_COUNT = 0
RAW_MATCHES_EXACTLY_ONE_BIGQUERY_VARIANT_COUNT = 0
RAW_CONFLICT_VARIANT_SET_EXACT_BIGQUERY_MATCH_COUNT = 40
CONTROL_MATCH_COUNT = 20
CONTROL_MISMATCH_COUNT = 0
CONTROL_MISSING_COUNT = 0
RAW_GKG_BATCH_FILE_COUNT_2017_08_29 = 175
RAW_SOURCE_DATE_PRESENT = YES
BIGQUERY_2017_08_29_GAP = BIGQUERY_MIRROR_COVERAGE_GAP
RAW_ENGLISH_ARCHIVE_COUNT_2015_2024 = 337124
RAW_TRANSLINGUAL_ARCHIVE_COUNT_2015_2024 = 331884
RAW_TOTAL_ARCHIVE_COUNT_2015_2024 = 669008
RAW_ENGLISH_COMPRESSED_BYTES_2015_2024 = 2553726973890
RAW_TRANSLINGUAL_COMPRESSED_BYTES_2015_2024 = 3676360070274
RAW_TOTAL_COMPRESSED_BYTES_2015_2024 = 6230087044164
OFFICIAL_RAW_GKG_AUTHORITY = FAIL_SEMANTIC_CONFLICT
BIGQUERY_GKG_SENTIMENT_ROLE = REJECTED_FOR_HISTORICAL_SENTIMENT_BACKFILL
PRIOR_GLOBAL_NEWS_V1_MATERIALIZATION_AUTHORITY = DIAGNOSTIC_ONLY_NOT_SCIENTIFICALLY_AUTHORITATIVE
RAW_GKG_ZIP_RETAINED_COUNT = 0
RAW_GKG_ROWS_PERSISTED = 0
AQ_NEWS_DATABASE_CREATED = NO
AQ_RAW_NEWS_ARCHIVE_CREATED = NO
AQ_GDELT_DOWNLOADER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
OUTCOME_DATA_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_P6_OBJECTIVE = GLOBAL_NEWS_V1_CLOSEOUT
CURRENT_DEVELOPMENT_NEXT = P6_GLOBAL_NEWS_V1_CLOSEOUT_001
FINAL_CLASSIFICATION = PASS_P6_GLOBAL_NEWS_V1_OFFICIAL_RAW_SOURCE_AUTHORITY_ARBITRATION
```

Private bounded comparison evidence is retained at
`D:/AQ_DATA/P6/global-news-v1-official-raw-source-authority-arbitration-001`.
The SHA-256 of its `checksums.json` is
`09fd75d89fd7d276ee736de756e98ff1da4f2a811d869dd0727e290dd468d1a9`.
No raw ZIP, decompressed GKG row, article URL, headline, body, credential, or
outcome data is retained or committed. The sections below remain historical
diagnostic evidence and are superseded wherever they imply that an official
raw-stream retry could restore sentiment authority.

## GKGRECORDID integrity correction (authoritative)

The follow-up integrity gate found that the materialization described below is
not scientifically authoritative. The official [GDELT GKG 2.1
codebook](https://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf)
defines `GKGRECORDID` as a globally unique record identifier and states that
each row represents one document codified by the GKG. One logical
`GKGRECORDID` therefore may receive at most one weight in every frozen Global
News V1 feature.

The retained SQL used `COUNT(DISTINCT GKGRECORDID)` only for volume. Its Tone,
Negative Score, and Polarity sums and valid counts were calculated directly
over physical rows. The observed excess was 273,386,857 physical rows, or
0.16891797618879278 of all 1,618,459,226 qualifying WEB rows.

A single partition-pruned BigQuery pass first grouped the selected population
by `GKGRECORDID`, then measured duplicate consistency before any candidate
daily aggregation. Its dry-run and exact actual scan were both
216,430,419,549 bytes, below the 250 GiB follow-up ceiling. The result fails
closed: the duplicate records are not semantically identical on the selected
sentiment fields, so no first-row, last-row, `ANY_VALUE`, or other arbitrary
selection is admissible.

```text
GKGRECORDID_SEMANTICS = GLOBALLY_UNIQUE_LOGICAL_GKG_RECORD
EXISTING_SENTIMENT_DEDUP_SEMANTICS = PHYSICAL_ROWS
SOURCE_RECORD_COUNT = 1618459226
DISTINCT_GKGRECORDID_COUNT = 1345072369
DUPLICATE_PHYSICAL_ROW_EXCESS = 273386857
DUPLICATE_PHYSICAL_ROW_RATE = 0.16891797618879278
DUPLICATE_GKGRECORDID_COUNT = 241297210
DUPLICATE_ID_DATE_CONFLICT_COUNT = 0
DUPLICATE_ID_SOURCE_COLLECTION_CONFLICT_COUNT = 0
DUPLICATE_ID_TONE_CONFLICT_COUNT = 240643925
DUPLICATE_ID_NEGATIVE_CONFLICT_COUNT = 240604624
DUPLICATE_ID_POLARITY_CONFLICT_COUNT = 241180404
BIGQUERY_ADDITIONAL_ESTIMATED_BYTES = 216430419549
BIGQUERY_ADDITIONAL_ACTUAL_BYTES = 216430419549
RETURNED_RAW_GKG_ROW_COUNT = 0
RAW_GKG_ROWS_PERSISTED = 0
```

The local calendar comparison independently found the only missing source date
to be `2017-08-29`. A smallest-possible BigQuery check against only that
partition processed zero bytes and returned zero partition rows: the partition
is absent, rather than a present day with zero qualifying WEB documents. Under
strict-next XNYS mapping, it feeds the previously empty `2017-08-30` session.
That session is a source-coverage gap and all four feature values must be NULL;
zero volume is rejected.

```text
EXPECTED_SOURCE_CALENDAR_DATE_COUNT = 3570
OBSERVED_SOURCE_CALENDAR_DATE_COUNT = 3569
MISSING_SOURCE_CALENDAR_DATE_COUNT = 1
MISSING_SOURCE_CALENDAR_DATES = 2017-08-29
EMPTY_SESSION = 2017-08-30
EMPTY_SESSION_CLASSIFICATION = SOURCE_COVERAGE_GAP
SOURCE_COVERAGE_GAP_FEATURE_POLICY = ALL_FOUR_FEATURES_NULL
```

Because duplicate sentiment semantics conflict, no corrected daily or session
artifact was sealed and no replacement materialization identity was created.
The prior materialization ID and hashes remain retained as diagnostic evidence
only; they must not enter an ablation. The task stops at
`BLOCKED_GDELT_DUPLICATE_RECORD_SEMANTIC_CONFLICT`.

The remainder of this document records the pre-audit materialization as
historical evidence and is superseded by this integrity correction wherever it
claims scientific authority.

## Result

PR #104 was squash-merged as
`db36a63aaeda5a86c303996e50e1f6b0bf4dfb55`. This branch started from that
exact clean main. After the initial fail-closed access check, the owner supplied
an authorized BigQuery Sandbox project (`gen-lang-client-0604242375`) and
completed browser authentication. No credential value, hash, prefix, or suffix
was read or retained.

The official partitioned GDELT GKG 2.1 table was verified through BigQuery
metadata before execution:

```text
BIGQUERY_AUTH_AVAILABLE = YES
BIGQUERY_PROJECT_AVAILABLE = YES
BIGQUERY_BILLING_STATUS = BIGQUERY_SANDBOX_NO_PAID_BILLING_ENABLED
BIGQUERY_SOURCE_TABLE = gdelt-bq.gdeltv2.gkg_partitioned
BIGQUERY_PARTITIONING = DATE(_PARTITIONTIME)
BIGQUERY_VERIFIED_COLUMNS = GKGRECORDID:STRING,DATE:INT64,SourceCollectionIdentifier:INT64,V2Tone:STRING
BIGQUERY_DRY_RUN = PASS
BIGQUERY_ESTIMATED_BYTES_PROCESSED = 216430419549
BIGQUERY_TOTAL_ESTIMATED_SCAN_BYTES = 432860839098
BIGQUERY_TASK_CEILING_BYTES = 805306368000
BIGQUERY_ACTUAL_BYTES_PROCESSED = 216430419549
BIGQUERY_QUERY_SQL_SHA256 = 93ecce9771cc6aa312dea8e557264ca84fe257fc853aaf9e6919e222b03d4375
```

The daily sufficient-statistics query and the separate global quality-count
query each processed `216430419549` bytes. Together they remained below the
750 GiB task ceiling. The daily query returned 3,569 aggregate rows and no raw
GKG row. The two BigQuery job IDs, exact SQL, schema snapshot, scan accounting,
and output hashes are retained privately.

## Materialized feature history

BigQuery owned the server-side reduction. Only daily distinct-document counts
and sum/count pairs for Tone, Negative Score, and Polarity crossed into AQ.
The existing pinned `aq_xnys_calendar` / `exchange_calendars==4.13.2` authority
mapped every date to the first strictly later XNYS session. DuckDB `1.5.5`
combined multiple calendar dates mapping to one session using sums and valid
counts, not daily-mean averaging. Pandera `0.33.1` validated the final narrow
boundary.

```text
SOURCE_QUERY_START = 2015-03-25
SOURCE_QUERY_END = 2024-12-31
SOURCE_COLLECTION = WEB_ONLY
SOURCE_RECORD_COUNT = 1618459226
DISTINCT_GKGRECORDID_COUNT = 1345072369
TONE_MALFORMED_COUNT = 0
NEGATIVE_MALFORMED_COUNT = 0
POLARITY_MALFORMED_COUNT = 0

RETURNED_RAW_GKG_ROW_COUNT = 0
DAILY_SUFFICIENT_STATISTICS_ROW_COUNT = 3569
EXPECTED_XNYS_SESSION_COUNT = 2455
MATERIALIZED_SESSION_COUNT = 2455
EMPTY_SESSION_COUNT = 1
RIGHT_EDGE_POST_2024_SESSION_COUNT = 1
RIGHT_EDGE_POST_2024_DOCUMENT_COUNT = 302925

GLOBAL_NEWS_V1_FEATURE_COUNT = 4
GLOBAL_NEWS_V1_FEATURES = global_news_log1p_volume,global_news_mean_tone,global_news_mean_negative_score,global_news_mean_polarity
GLOBAL_NEWS_V1_MATERIALIZATION_ID = 293f69052f3184ca798a55ce2183c5c8c4bf179c72b78d1247f58d2282fb4c4f
DAILY_SUFFICIENT_STATISTICS_SHA256 = 5d85aba4f584c08178100638709cc3cda4e7472f1a72da29c677777834b77e9d
XNYS_SESSION_MAP_SHA256 = 6320694f350d0f0faa889319ffc53f290174d021113b4bfdbda72294e7b9d311
SESSION_FEATURE_HISTORY_SHA256 = 3184ab20246300465dc34b1aa2dd7c5f0938e69439581d2bb4b022bc9ce448cb
```

The one empty session is `2017-08-30`; it correctly contains volume `0` and
NULL means. Source date `2024-12-31` maps strictly forward into one 2025
session, so its 302,925 distinct documents are counted as right-edge evidence
and excluded from the frozen scientific range. The retained session history
has exactly one ascending unique row for every XNYS session from 2015-04-01
through 2024-12-31.

## Integrity and ownership

```text
P6_GLOBAL_NEWS_V1 = MATERIALIZED
HISTORICAL_BACKFILL_MODEL = UPSTREAM_SERVER_SIDE_STREAMING_REDUCTION
GLOBAL_NEWS_STORAGE_MODEL = SESSION_FEATURE_HISTORY_ONLY
RAW_NEWS_RETENTION = NONE
FUTURE_REALTIME_STATE_MODEL = MUTABLE_LATEST_STATE_PLUS_IMMUTABLE_SESSION_SNAPSHOTS
REALTIME_STATEFUL_STREAM_PROCESSOR_SELECTION = DEFERRED_TO_P9

STRICT_NEXT_SESSION_GATE = PASS
EXACT_SESSION_COVERAGE_GATE = PASS
PANDERA_BOUNDARY_VALIDATION = PASS
DUCKDB_REPEAT_DETERMINISM = PASS
NO_FORWARD_FILL = PASS
NO_BACKFILL = PASS
NO_FUTURE_INFORMATION = PASS

RAW_GKG_ROWS_PERSISTED = 0
RAW_NEWS_RECORDS_PERSISTED = 0
RAW_GDELT_ZIP_RETAINED_COUNT = 0
ARTICLE_BODY_RETAINED_COUNT = 0
ARTICLE_HEADLINE_RETAINED_COUNT = 0
AQ_NEWS_DATABASE_CREATED = NO
AQ_RAW_NEWS_ARCHIVE_CREATED = NO
AQ_NEWS_CRAWLER_CREATED = NO
AQ_GDELT_DOWNLOADER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
OUTCOME_DATA_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
```

Private evidence is retained at
`D:/AQ_DATA/P6/global-news-v1-streaming-sufficient-statistics-backfill-001`.
The complete evidence set is 394,939 bytes; the SHA-256 of `checksums.json` is
`75e0e85e0448d28abb3df18e0802f1d7574d5c628fb386f2d8fc6574d8e57118`.
No private Parquet, query result row, credential, or GDELT content is committed.

```text
CURRENT_P6_OBJECTIVE = GLOBAL_NEWS_V1_GKGRECORDID_INTEGRITY_BLOCKER
CURRENT_DEVELOPMENT_NEXT = BLOCKED_GDELT_DUPLICATE_RECORD_SEMANTIC_CONFLICT
FINAL_CLASSIFICATION = BLOCKED_GDELT_DUPLICATE_RECORD_SEMANTIC_CONFLICT
```
