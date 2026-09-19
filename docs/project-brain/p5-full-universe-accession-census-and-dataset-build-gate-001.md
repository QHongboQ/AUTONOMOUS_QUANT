# P5 full-universe accession census and dataset-build gate 001

## Result

The first complete metadata-only SEC periodic-filing census for the final P5
identity population passed. The historical dataset build is not authorized
yet because the local SEC Financial Statement Data Sets catalog covers only 35
of the 60 required quarters.

```text
IDENTITY_ACCOUNTING = PASS
ACCESSION_CENSUS = PASS
ACCEPTANCE_TIME_COMPLETENESS = 100%
STORAGE_GATE = CAUTION
UPSTREAM_CATALOG_COVERAGE = INCOMPLETE
FULL_DATASET_BUILD_READINESS = FULL_DATASET_BUILD_BLOCKED_FSDS_REQUIRED_HISTORY_COVERAGE_INCOMPLETE
CURRENT_DEVELOPMENT_NEXT = P5_FSDS_REQUIRED_HISTORY_COVERAGE_ACTIVATION_001
```

No filing body corpus or historical dataset was downloaded or built.

## Identity closeout merge

The exact identity-closeout source head was independently revalidated and
squash-merged through PR #62 before the census branch was created:

```text
PRE_MERGE_MAIN = 5fb3a48b884753e155ff10b5711b0783e0d9754f
SOURCE_HEAD = 9122c22a9d684129ba42328e35a5f457fb4f222e
PR = 62
MERGED_AT_UTC = 2026-09-19T19:20:49Z
MERGE_SHA = 73e4bdb92cde3e224f34cb70b8eac5e00fc246c8
MERGE_METHOD = SQUASH
```

## Authoritative population

The census consumes the immutable final binding ledger with SHA-256
`51f61a3bce916e29a300b075d19b6ffe8de371701c836201621b6a740cbbfee2`.

| Measure | Count |
|---|---:|
| bound P1 episodes | 721 |
| binding records | 722 |
| exclusion-ledger episodes | 111 |
| total P1 episodes | 832 |
| unique bound CIKs | 711 |
| CIKs spanning multiple episodes | 11 |
| episodes sharing those CIKs | 22 |
| multi-binding episodes | 1 |

The 111 excluded episodes remain in the historical universe and denominator,
with unavailable fundamental features. They were not sent to filing discovery,
and identity was not reopened.

## Metadata census

EdgarTools 5.58.0 enumerated SEC submissions metadata for all 711 unique bound
CIKs. The required research window is `2010-01-04` through `2024-12-31`.
Metadata enumeration starts at `1994-01-01` solely to retain valid
same-CIK pre-membership lookback candidates. The frozen forms are `10-K`,
`10-Q`, `10-K/A`, and `10-Q/A`; `8-K` remains outside the periodic census.

```text
UNIQUE_CIK_REQUESTED = 711
UNIQUE_CIK_COMPLETED = 711
FAILED_CIK_COUNT = 0
TOTAL_PERIODIC_ACCESSION_COUNT = 70021
UNIQUE_ACCESSION_COUNT = 70021
TEN_K_COUNT = 15574
TEN_Q_COUNT = 50652
TEN_K_A_COUNT = 1995
TEN_Q_A_COUNT = 1800
AMENDMENT_ACCESSION_COUNT = 3795
```

There were 117 duplicate accession observations across multiple bound-CIK
submissions histories. All duplicate metadata matched exactly. The census
stores one accession record plus every observed bound-CIK relation. The CIK-
shaped prefix in an accession number is explicitly non-authoritative for issuer
ownership and is not used as a replacement for the accepted binding ledger.

## Episode and interval accounting

The accession-to-binding relation contains 70,138 accession/bound-CIK rows:

| Relation | Count |
|---|---:|
| `IN_BINDING_INTERVAL` | 27,316 |
| `PRE_MEMBERSHIP_SAME_CIK_LOOKBACK` | 39,633 |
| `POST_BINDING` | 3,054 |
| `OUTSIDE_RELEVANT_HISTORY` | 135 |

`PRE_MEMBERSHIP_SAME_CIK_LOOKBACK` is candidate evidence only. It cannot create
pre-membership universe rows and can become usable only on a later eligible
session with the same exact CIK binding and the frozen PIT effective-session
rule.

```text
EPISODE_WITH_AT_LEAST_ONE_PERIODIC_ACCESSION_COUNT = 716
EPISODE_WITH_DIRECT_INTERVAL_ACCESSION_COUNT = 710
BOUND_EPISODE_WITH_NO_PERIODIC_ACCESSION_COUNT = 5
CIK_WITH_NO_PERIODIC_ACCESSION_COUNT = 4
```

The five zero-usable-periodic-accession episode relationships are retained as
missing rather than repaired or substituted:

| Ticker | CIK | Episode interval |
|---|---|---|
| FRC | 0001132979 | 2019-01-02 to 2023-05-04 |
| CCEP | 0001650107 | 2016-01-04 to 2016-05-31 |
| MJN | 0001444904 | 2010-01-04 to 2017-06-15 |
| FCPT | 0001650132 | 2015-11-10 to 2015-11-17 |
| LXK | 0001060259 | 2010-01-04 to 2012-10-01 |

Seven filing-date gaps exceed the diagnostic 550-day threshold. They remain in
the private gap ledger for later build-time missingness handling; no filing or
identity was manufactured.

## Acceptance-time authority

Every enumerated accession has SEC acceptance-time metadata:

```text
ACCESSION_WITH_ACCEPTANCE_TIME_COUNT = 70021
ACCESSION_MISSING_ACCEPTANCE_TIME_COUNT = 0
ACCEPTANCE_TIME_COMPLETENESS_RATE = 1.0
FILING_DATE_USED_AS_PIT_AVAILABILITY = NO
```

The eventual authority remains SEC acceptance datetime followed by the frozen
effective-session rule: the first XNYS session whose open occurs after
`first_available_at_utc`. This census does not project features to sessions.

## Local FSDS catalog and cross-check

The existing secfsdstools 2.4.3 catalog was opened read-only with
`AutoUpdate=False`. No quarterly archive was downloaded.

```text
LOCAL_FSDS_START = 2013-04-01
LOCAL_FSDS_END = 2021-12-31
LOCAL_FSDS_QUARTER_COUNT = 35
REQUIRED_FSDS_QUARTER_COUNT = 60
MISSING_FSDS_QUARTER_COUNT = 25
FSDS_CATALOG_COVERAGE_COMPLETE = NO
INDEXED_SUBMISSION_COUNT = 245363
INDEXED_UNIQUE_CIK_COUNT = 13125
LOCAL_FSDS_STORAGE_BYTES = 6352704147
```

Missing quarters are `2010q1` through `2013q1` and `2022q1` through `2024q4`.

| Cross-check | Count |
|---|---:|
| EdgarTools accessions | 70,021 |
| local FSDS bound-CIK candidate accessions | 21,219 |
| accession matches | 21,217 |
| FSDS-only candidates | 2 |
| EdgarTools-only accessions overall | 48,804 |
| EdgarTools-only accessions inside the local FSDS window | 532 |
| matched rows with bound-CIK conflict | 0 |

FSDS remains a bulk historical candidate catalog, not acceptance-time
authority. The incomplete local quarter range is the exact build blocker.

## Storage gate

The estimate uses the complete 70,021-accession metadata census, provider-
reported submission sizes, measured local catalog bytes, and separately marked
pilot-derived estimates for selected evidence/events/projection. It does not
multiply six pilot episodes to estimate the full filing corpus.

| Surface | Bytes | Class |
|---|---:|---|
| metadata census | 28,259,997 | measured |
| local FSDS catalog | 6,352,704,147 | measured |
| completed 60-quarter FSDS catalog | 10,890,349,966 | sampled estimate from 35 measured quarters |
| full periodic submissions | 629,287,955,695 | provider reported for all 70,021 accessions |
| selected XBRL/evidence | 698,719,553 | sampled estimate |
| standardized events | 206,481,926 | sampled estimate |
| session projection | 9,162,588 | sampled estimate |
| DVC/manifest overhead | 18,852,481 | sampled estimate |

The bounded-hybrid planning range is:

```text
ESTIMATED_BUILD_STORAGE_LOW = 13851826511 bytes (12.90 GiB)
ESTIMATED_BUILD_STORAGE_BASE = 106245019865 bytes (98.95 GiB)
ESTIMATED_BUILD_STORAGE_HIGH = 1270427737901 bytes (1183.18 GiB)
PROJECT_AVAILABLE_STORAGE_CONSTRAINT = 256 GiB
STORAGE_GATE = CAUTION
```

The base estimate assumes only 15% of provider-reported full submission bytes
are retained after exact bounded extraction; this is a planning assumption,
not a measured compression ratio. The high case demonstrates that redundant
full-corpus retention is incompatible with the storage limit. Build design
must use bounded batches and retain immutable authoritative evidence rather
than a permanent redundant filing mirror.

## Historical and live ingestion architecture

The production architecture is frozen as:

```text
HISTORICAL_INGESTION_MODE = ONE_TIME_BACKFILL_PLUS_IMMUTABLE_VINTAGES
LIVE_INGESTION_MODE = INCREMENTAL_NEW_ACCESSION_ONLY
FULL_HISTORY_REREAD_PER_LIVE_CYCLE = NO
LIVE_FILING_DISCOVERY_UPSTREAM = SEC_EDGAR_VIA_EDGARTOOLS_OR_OFFICIAL_CURRENT_FILINGS
SECFSDSTOOLS_LIVE_ROLE = NONE
FULL_DOCUMENT_LLM_REQUIRED_FOR_HISTORICAL_CENSUS = NO
NEWS_INTELLIGENCE_IMPLEMENTED = NO
LIVE_INCREMENTAL_WATCHER_IMPLEMENTED = NO
```

The one-time historical backfill will seal structured facts, accession,
acceptance datetime, source identity/hash, and amendment lineage as immutable
PIT vintages. Historical extraction prefers SEC metadata, XBRL, and EdgarTools
typed parsing. Narrative/full-text parsing requires a later separately
authorized feature; there is no general historical filing summarizer.

The future live path is SEC current/latest filings or EdgarTools
`get_current_filings()`, authoritative-CIK/form filtering, accession
deduplication, retrieval of new accessions only, metadata/XBRL extraction,
append-only PIT vintage creation, and release after the frozen effective-
session rule. Its minimum future state is:

```text
LAST_SEEN_ACCESSION_SET_OR_CHECKPOINT
NEW_ACCESSION_COUNT
DUPLICATE_ACCESSION_COUNT
LAST_SUCCESSFUL_POLL_AT
SOURCE_STATUS
```

Periodic forms represent fundamental state, amendments create later immutable
restatement vintages, `8-K`/earnings exhibits remain event or preliminary
information, and general news/IR/media remains separate news intelligence.

## Evidence and replay

All authoritative outputs are private under:

```text
D:\AQ_DATA\P5\full-universe-accession-census-and-dataset-build-gate-001
```

The core checksum ledger SHA-256 is
`2d389ade8f96e427a2367f4f37ea35e5507607b550035ad6a34812dd3b6e9dc8`.
Two consecutive offline-only finalizations produced this identical hash;
replay stderr was empty. Credentials and full filing bodies are absent from
Git.

## Ownership and non-actions

```text
AQ_SEC_CRAWLER = NO
AQ_SEC_HTTP_CLIENT = NO
AQ_XBRL_ENGINE = NO
AQ_STATEMENT_ENGINE = NO
AQ_FILING_INDEX_ENGINE = NO
AQ_GENERIC_ETL = NO
AQ_GENERIC_DATA_WAREHOUSE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
PRODUCTION_LOC_ADDED = 0
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

The next work is the separately authorized acquisition and sealing of the 25
missing FSDS quarters. It is not identity research and does not start the full
dataset build.

