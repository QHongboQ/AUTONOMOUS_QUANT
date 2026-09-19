# P5 Hybrid Historical Dataset Build Pilot 001

## Authority

```text
TASK = AUTONOMOUS-QUANT-P5-HYBRID-HISTORICAL-DATASET-BUILD-PILOT-001
BASELINE_MAIN_SHA = c014be920aed629f15c70123b0341c002ab212a1
P5_HYBRID_HISTORICAL_DATASET_BUILD_PILOT = PASS
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_HYBRID_DATASET_PILOT_CLOSEOUT_AND_FULL_BUILD_GATE_001
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
```

This bounded pilot proves the real hybrid path for six admitted historical
episodes and two fail-closed identity controls. It does not authorize or build
the 832-episode dataset.

## Frozen ownership and scope

```text
PILOT_INPUT_CASE_COUNT = 8
PILOT_ADMITTED_EPISODE_COUNT = 6
NEGATIVE_IDENTITY_EXCLUSION_COUNT = 2
CURRENT_TICKER_BACKFILL = 0
P5_BULK_CANDIDATE_CATALOG = SECFSDSTOOLS
P5_EXACT_EVIDENCE_ADMISSION = EDGARTOOLS
FIRST_AVAILABLE_AT_AUTHORITY = EXACT_SEC_SUBMISSION_ACCEPTANCE
P5_ASOF_PROJECTION_OWNER = pandas.merge_asof
P5_SESSION_AUTHORITY = exchange_calendars:XNYS
P5_RESEARCH_CONSUMER = Qlib
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

The admitted cases are AAPL, CTL, bounded BBBY, DRE, new DD, and FB, using
their exact existing `EpisodeSecCikBindingV1` records. Old DD remains
`AMBIGUOUS_FAIL_CLOSED`; old CEG remains `MISSING_AUTHORITY`. Neither ticker
text nor a current-survivor CIK was used to create authority.

## Shared FSDS candidate catalog

```text
INITIAL_FSDS_QUARTER = 2014Q1
FINAL_EARLIEST_FSDS_QUARTER = 2013Q2
FINAL_LATEST_FSDS_QUARTER = 2021Q4
FSDS_QUARTER_COUNT = 35
FSDS_NETWORK_DOWNLOAD_COUNT = 34
FSDS_CACHE_REUSE_COUNT = 1
FSDS_TOTAL_COMPRESSED_BYTES = 3082782186
FSDS_TOTAL_PARQUET_BYTES = 3186478249
FSDS_SQLITE_BYTES = 83443712
FSDS_INDEXED_REPORT_COUNT = 245363
FSDS_INDEXED_CIK_COUNT = 13125
CANDIDATE_ACCESSION_COUNT = 192
POST_2021_FSDS_QUARTERS_ACCESSED = 0
```

The quarter window was extended backward one quarter at a time until 2013Q2.
Five CIKs then met the frozen pre-TRAIN endpoint requirement. New DD filer CIK
`0001666700` has no pre-2015 history because that filer did not yet exist; this
is retained as a concrete historical limitation. No predecessor CIK or ticker
backfill was admitted to make the lookback pass.

The shared catalog was created through secfsdstools 2.4.3 upstream transform
and index processes. Its roughly 3 GB acquisition/transform cost is shared
infrastructure and must not be multiplied by episode count.

## Exact evidence and semantic projection

```text
EXACT_ADMITTED_ACCESSION_COUNT = 14
TEN_K_COUNT = 7
TEN_Q_COUNT = 6
TEN_KA_COUNT = 1
TEN_QA_COUNT = 0
FUNDAMENTAL_EVIDENCE_COUNT = 96
UNIQUE_EVIDENCE_ID_COUNT = 96
DIMENSION_BEARING_EVIDENCE_COUNT = 0
STANDARDIZED_EVENT_COUNT = 96
DIRECT_STANDARDIZED_COUNT = 96
DERIVED_STANDARDIZED_COUNT = 0
UNTRACEABLE_STANDARDIZED_COUNT = 0
STANDARDIZED_METRIC_COUNT = 9
FSDS_ACCEPTANCE_USED_FOR_ADMISSION = NO
SECFSDSTOOLS_FLOAT_VALUE_USED_FOR_EVIDENCE = NO
SECFSDSTOOLS_DEFAULT_STANDARDIZER_USED_FOR_ADMISSION = NO
AMENDMENT_VINTAGE_PROOF = PASS
```

Twelve deterministic FSDS candidates—one 10-K and one 10-Q within each
admitted binding where available by the bounded selection rule—were admitted
through exact EdgarTools submission parsing. The retained Apple original and
10-K/A pair adds the amendment proof. The task made 12 bounded exact-source
requests and reused two preserved amendment sources. Every authoritative
numeric value is an exact canonical decimal string from file-level XBRL;
FSDS NUM remained discovery diagnostic only.

EdgarTools' default concept mapper produced direct events in nine of the eleven
frozen metrics. Metrics without a unique traceable direct value remain missing;
no AQ alias or substitute standardization was introduced.

## Temporal and physical proof

```text
EFFECTIVE_SESSION_POLICY = PASS
ELIGIBLE_EPISODE_SESSION_COUNT = 7136
SESSION_PROJECTION_ROW_COUNT = 51120
EARLY_VISIBILITY_COUNT = 0
MEMBERSHIP_ALIGNMENT_FAILURE_COUNT = 0
CROSS_CIK_CONTAMINATION_COUNT = 0
UNTRACEABLE_PROJECTED_VALUE_COUNT = 0
PARQUET_ROUNDTRIP = PASS
ADMITTED_EVENT_PARQUET_BYTES = 41284
PROJECTION_PARQUET_BYTES = 42241
PROVENANCE_BYTES = 34008
```

Effective dates use the first XNYS session whose open is strictly after the
exact SEC acceptance time. Episode, binding, and P1 membership containment is
applied before `pandas.merge_asof`. Missing values remain missing. Provenance
is a sidecar and is not exposed as a Qlib feature.

## DVC, Qlib, and replay

```text
DVC_STAGE = p5_hybrid_historical_dataset_pilot_seal
DVC_LOCK_ENTRY_IDENTITY = 0207e922a8893e873493f13749cda7b3c2c181f9992f88d265149002eb963360
PILOT_SEAL_SHA256 = ec03e87b0b376de6223837c4affae5a6324990209a8454238eb57b202ff43f73
DVC_PILOT_SEAL = PASS
QLIB_STATIC_DATA_LOADER = PASS
QLIB_DATAHANDLERLP = PASS
QLIB_DATASETH = PASS
TRAIN_SEGMENT_ACCESS = PASS
VALID_SEGMENT_ACCESS = PASS
HISTORICAL_TEST_SEGMENT_ACCESS = NOT_EXECUTED
DETERMINISTIC_REPLAY = PASS
```

DVC seals exactly the pilot manifest, admitted sparse events, session
projection, provenance sidecar, and quality report. It does not create a
second DVC copy of the FSDS bulk catalog. Offline replay reproduced the
evidence set, standardized events, session projection, and manifest identity.

The authoritative Qlib 0.9.8.dev26 runtime consumed the table through public
`StaticDataLoader`, `DataHandlerLP`, and `DatasetH` APIs. No model was trained,
no prediction or backtest was run, and no historical TEST segment was read.

## Validation and scaling boundary

```text
FOCUSED_P5_TESTS = 50_PASSED; 29_SUBTESTS_PASSED
P1_RELEVANT_TESTS = 36_PASSED; 9_SKIPPED; 23_SUBTESTS_PASSED
QLIB_HANDOFF_RELEVANT_TESTS = 17_PASSED
RUFF = PASS
AQ_NEW_PRODUCTION_LOC = 238
FULL_BUILD_SCALE_MODEL = SHARED_CATALOG_PLUS_PER_ACCESSION_ADMISSION
```

The P1 replay used a temporary LF-preserving tracked archive because the
Windows checkout uses `core.autocrlf=true`; the tracked P1 authority blobs were
not changed. The next independent closeout must audit metric coverage,
missingness, shared catalog scaling, per-accession scaling, disk/runtime cost,
DVC replay, Qlib handoff, and AQ architecture drift before any full build.

```text
PRIVATE_REPORT = D:/AQ_DATA/P5/hybrid-historical-dataset-build-pilot-001/reports/pilot_summary.json
PRIVATE_REPORT_SHA256 = 333dcbaa72815880de1d29ad9280e7f070d3bb0b889bc4abfe5c3b753a212649
```
