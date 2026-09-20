# P5 EdgarTools Selective Historical Build Production Canary 001

Status: **PASS**

The frozen deterministic production canary contains exactly 256 unique
accessions from the 36,206-accession selective inventory. Its canonical set
identity was sealed before retrieval:

```text
PRODUCTION_CANARY_ACCESSION_SET_SHA256 =
6ba66a7b9c91d43a39d315b487d593d8a7f487b7d28f71677ff63d5e4462f214
```

The canary exercised EdgarTools 5.58.0 remote-first filing-homepage XBRL
attachments, the existing `FundamentalEvidenceV1` materializer, the frozen
standardized-event policy, XNYS effective sessions, `pandas.merge_asof`,
Parquet, and Qlib `StaticDataLoader -> DataHandlerLP -> DatasetH`. No model
training, prediction, backtest, full-universe execution, or sealed-OOS access
occurred.

Three bounded execution defects were corrected during the canary. The runner now
passes only filing-homepage native XBRL attachments into EdgarTools
`XBRL.from_filing`, avoiding the implicit complete-SGML path in
`Filing.attachments`. Exact XBRL decimal lexical forms are normalized without
rounding before the unchanged canonical evidence validator. Duplicate
statement-role enumeration is removed only when the existing immutable
`evidence_id` is identical. Both interrupted pre-fix attempts remain preserved
as private diagnostic evidence.

Final accounting:

```text
CANARY_ACCESSION_COUNT = 256
COMPLETE_WITH_EVIDENCE_COUNT = 256
ALL_OTHER_TERMINAL_STATE_COUNTS = 0
UNACCOUNTED_CANARY_ACCESSION_COUNT = 0

FUNDAMENTAL_EVIDENCE_COUNT = 34,379
UNIQUE_EVIDENCE_ID_COUNT = 34,379
DUPLICATE_EVIDENCE_ID_COUNT = 0
STANDARDIZED_EVENT_COUNT = 8,668
AMENDMENT_ACCESSION_COUNT = 24
DIMENSION_BEARING_RAW_FACT_COUNT = 25,711
CONSOLIDATED_ADMITTED_EVENT_COUNT = 8,668

NETWORK_REQUEST_COUNT = 1,790
NETWORK_BYTES = 91,626,045
NATIVE_SOURCE_ASSET_BYTES = 1,613,917,486
MAX_OBSERVED_CACHE_BYTES = 126,355,806
CACHE_LIMIT_BREACH_COUNT = 0
TRANSIENT_CACHE_EVICTED = YES

EARLY_VISIBILITY_FAILURE_COUNT = 0
CROSS_CIK_CONTAMINATION_COUNT = 0
PERIOD_CLASS_MIX_FAILURE_COUNT = 0
QLIB_CANARY_HANDOFF = PASS

SECOND_PASS_RESUME = PASS
SECOND_PASS_REPROCESSED_COMPLETE_ACCESSION_COUNT = 0
SECOND_PASS_NETWORK_BYTES = 0
```

Private evidence root:

`D:\AQ_DATA\P5\edgartools-native-full-universe-historical-build-001\canary-001`

Key private identities:

```text
production_canary_report.json =
22a0af271252045203830e3bd89f014b7390e7a29563469c97ee3b906e7a8e98

canary_artifact_manifest.json =
5e185a3f6d099b23718f302a54a4961c810942d22062519f15afc3456a3cd95f

checksums.json =
7b401a6375cd3f70b14264f065d1b924995790344cfe7265ce37ed0e0254ede1
```

Authority:

```text
FULL_BUILD_CANARY_STATUS = PASS
BROAD_FULL_UNIVERSE_EXECUTION_STARTED = NO
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_DEVELOPMENT_NEXT =
P5_EDGARTOOLS_SELECTIVE_FULL_HISTORICAL_BUILD_EXECUTION_001
```
