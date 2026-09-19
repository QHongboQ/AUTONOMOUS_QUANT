# P5 Full-Universe Accession Authority Census 001

## Outcome

This leaf records the complete, fail-closed authority accounting for all 832
authoritative P1 `InstrumentEpisodeV1` episodes and the periodic SEC accession
census for the CIKs admitted by the existing `EpisodeSecCikBindingV1`
contract. It is a census only: it does not build the historical fundamental
dataset or authorize that build.

```text
TASK = AUTONOMOUS-QUANT-P5-FULL-UNIVERSE-ACCESSION-AUTHORITY-CENSUS-001
BASE_MAIN_SHA = de3c1b8b550a32074b0144b5e24566bca8a6b8d2
FULL_P1_EPISODE_COUNT = 832
UNIQUE_EPISODE_ID_COUNT = 832
DUPLICATE_EPISODE_ID_COUNT = 0
P1_EPISODE_INVENTORY_SHA256 = 5d2732f8a6187bdab342ff09ff3ecdcc7e66d9e755bc364a8f3f822923d877e1
FULL_UNIVERSE_IDENTITY_ACCOUNTING_COMPLETE = YES
FINAL_CLASSIFICATION = PASS_FULL_UNIVERSE_AUTHORITY_AND_ACCESSION_CENSUS
```

## Identity authority accounting

The existing eight-case POC evidence was reused without widening its
authority. Six already-admitted records validated through
`validate_binding_record()` / `validate_binding_set()`. All other episodes
were adjudicated conservatively against the approved retained evidence set.
A provider/current-ticker CIK candidate was recorded as discovery evidence
only and never promoted without date-safe historical authority.

```text
FULL_BINDING_EPISODE_COUNT = 5
PARTIAL_BINDING_EPISODE_COUNT = 1
AMBIGUOUS_EPISODE_COUNT = 1
MISSING_AUTHORITY_EPISODE_COUNT = 825
NO_SEC_FILER_EPISODE_COUNT = 0
UNCLASSIFIED_EPISODE_COUNT = 0

ADMITTED_BINDING_RECORD_COUNT = 6
ADMITTED_BINDING_EPISODE_COUNT = 6
PASS_EXACT_BINDING_COUNT = 3
PASS_CORROBORATED_BINDING_COUNT = 3
UNIQUE_AUTHORITATIVE_CIK_COUNT = 6

TICKER_ONLY_BINDING = PROHIBITED
CURRENT_TICKER_TO_CIK_BACKFILL = PROHIBITED
CURRENT_SP500_SURVIVOR_LIST = PROHIBITED
IMPLICIT_P1_P2_EPISODE_CROSSWALK = PROHIBITED
P2_PROVIDER_BINDING_FACTS_REKEYED_TO_FULL_P1 = NO
```

The control matrix remains unchanged: AAPL, CTL/LUMN, bounded BBBY, DRE, new
DD, and FB/META retain their admitted bindings; old DD remains ambiguous and
old CEG remains missing authority. The BBBY record remains bounded and its
unresolved episode interval is retained explicitly.

## Session-weighted coverage

XNYS sessions use the pinned `exchange_calendars` authority with half-open
episode and binding intervals.

```text
ELIGIBLE_PIT_EPISODE_SESSION_COUNT = 1893759
EXACTLY_ONE_AUTHORITATIVE_CIK_SESSION_COUNT = 11957
NO_AUTHORITATIVE_CIK_SESSION_COUNT = 1881802
MULTIPLE_AUTHORITATIVE_CIK_SESSION_COUNT = 0
SESSION_COUNT_RECONCILIATION = PASS
```

Unresolved and excluded sessions remain in the denominator. No CIK or
fundamental value was inferred for them.

## Periodic SEC accession census

The shared secfsdstools/FSDS catalog supplied candidate discovery. Exact
accession authority came from SEC EDGAR through EdgarTools 5.58.0 for the six
admitted CIKs. The census retains 10-K, 10-Q, 10-K/A, and 10-Q/A as distinct
accessions and does not parse filing XBRL facts.

```text
FULL_UNIVERSE_ACCESSION_CENSUS_COMPLETE = YES
INCOMPLETE_CIK_COUNT = 0
ACCESSION_RELATION_EDGE_COUNT = 588
UNIQUE_EXACT_ACCESSION_COUNT = 588
UNIQUE_10K_ACCESSION_COUNT = 138
UNIQUE_10Q_ACCESSION_COUNT = 433
UNIQUE_10K_AMENDMENT_ACCESSION_COUNT = 9
UNIQUE_10Q_AMENDMENT_ACCESSION_COUNT = 8
UNIQUE_CIK_WITH_PERIODIC_ACCESSION_COUNT = 6
AUTHORITATIVE_ACCEPTANCE_DATETIME_COUNT = 588
MISSING_EXACT_ACCEPTANCE_DATETIME_COUNT = 0
DUPLICATE_ACCESSION_ID_COUNT = 0
CIK_ACCESSION_MISMATCH_COUNT = 0

FSDS_CANDIDATE_ACCESSION_COUNT = 191
FSDS_CANDIDATES_MISSING_FROM_SEC_AUTHORITY = 0
IN_BINDING_INTERVAL_RELATION_COUNT = 196
PRE_BINDING_SAME_CIK_HISTORY_RELATION_COUNT = 312
POST_BINDING_OR_OTHER_NONELIGIBLE_RELATION_COUNT = 80
```

`PRE_BINDING_SAME_CIK_HISTORY` remains evidence inventory only. It creates no
pre-membership row and cannot substitute a predecessor CIK.

## Storage, replay, and ownership

SEC submission metadata supplies source-size values for every admitted
accession. These are metadata measurements, not a retained full SEC mirror.

```text
KNOWN_SOURCE_BYTE_ACCESSION_COUNT = 588
UNKNOWN_SOURCE_BYTE_ACCESSION_COUNT = 0
KNOWN_SOURCE_BYTE_TOTAL = 4117878634
STORAGE_SCALE_STATUS = EXACT_METADATA_COMPLETE
FULL_SEC_MIRROR = NO
DETERMINISTIC_REPLAY = PASS

AQ_SECURITY_MASTER = NO
AQ_TICKER_RESOLVER = NO
AQ_CORPORATE_LINEAGE_ENGINE = NO
AQ_SEC_CRAWLER = NO
AQ_SEC_HTTP_CLIENT = NO
AQ_XBRL_ENGINE = NO
AQ_GENERIC_ACCESSION_DATABASE = NO
AQ_GENERIC_IDENTITY_ENGINE = NO
AQ_GENERIC_ETL = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
AQ_NEW_PRODUCTION_LOC = 0
```

The deterministic replay reproduced all ten authoritative census artifacts
byte-for-byte from the frozen episode, binding, provider, FSDS, and retained
SEC submission metadata inputs.

## Sealed boundaries and next gate

```text
P2_V2_SEALED_OOS_ACCESSED = NO
P5_HISTORICAL_DATASET_BUILT = NO
FULL_FUNDAMENTAL_EVIDENCE_MATERIALIZATION = NO
FULL_XBRL_PARSE_EXECUTED = NO
FULL_SESSION_PROJECTION_BUILT = NO
QLIB_FULL_FUNDAMENTAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
PREDICTION = NO
P5_BACKTEST = NO

FULL_BUILD_GATE_INPUT_READY = YES
FULL_BUILD_AUTHORIZED = NO
CURRENT_DEVELOPMENT_NEXT = P5_FULL_UNIVERSE_ACCESSION_AUTHORITY_CENSUS_CLOSEOUT_AND_FULL_BUILD_GATE_001
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
```

## Private evidence

```text
PRIVATE_ARTIFACT_ROOT = D:/AQ_DATA/P5/full-universe-accession-authority-census-001
PRIVATE_REPORT = D:/AQ_DATA/P5/full-universe-accession-authority-census-001/census_report.json
PRIVATE_REPORT_SHA256 = 3b2021347121caf1e73c444fe418a204d3fd32dfa31fc2212fe3acd5cc39a617
ARTIFACT_MANIFEST_SHA256 = 25ea83585d2bcd735d94fa7a3a341122890c274f4cd07b0d1e2940899a793a7c
SEC_PERIODIC_SUBMISSION_SNAPSHOT_SHA256 = 124f04eabeaddd6e54b2bce8e110289e6314da3c6ce09dd87d126cdecdb69058
```
