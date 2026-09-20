# P5 Historical Build Required Accession Failure Closeout 001

Status: **PASS**

The exact four-accession pre-execution blocker set is closed. No EntityFacts
census, broad acquisition, or full historical build was run.

Two accessions remain explicitly unavailable for final provenance:

| accession | CIK | result |
| --- | --- | --- |
| `0001100682-20-000033` | `0001100682` | no exact EdgarTools filing row and zero exact SEC homepage attachments |
| `0001108524-21-000014` | `0001108524` | no exact EdgarTools filing row and zero exact SEC homepage attachments |

They are sealed in a build-specific ledger as
`SOURCE_UNAVAILABLE_FOR_FINAL_PROVENANCE`. The records contain no source hash
and no replacement accession, and they are not `FundamentalEvidenceV1`.

The other two blockers are valid transition financial filings. A bounded
compatibility leaf admits exactly `10-KT`, `10-KT/A`, `10-QT`, and `10-QT/A`
into the existing EdgarTools native XBRL path; it does not normalize forms or
infer periods. Production-path validation completed both exact accessions:

| accession | actual form | terminal state | evidence rows | standardized events |
| --- | --- | --- | ---: | ---: |
| `0001193125-10-257767` | `10-KT` | `COMPLETE_WITH_EVIDENCE` | 74 | 46 |
| `0001418135-18-000016` | `10-QT` | `COMPLETE_WITH_EVIDENCE` | 41 | 22 |

All required source URLs, native source-asset hashes, exact accessions,
acceptance datetimes, filed forms, raw facts, contexts, dimensions, and
EdgarTools runtime identity are retained. A second checkpoint replay reused
2/2 accessions with zero network bytes and zero reprocessing. The transient
source cache was then evicted.

Private authority root:

`D:\AQ_DATA\P5\edgartools-native-full-universe-historical-build-001`

```text
SELECTIVE_DISCOVERED_ACCESSION_COUNT = 36206
SOURCE_VERIFIABLE_REQUIRED_ACCESSION_COUNT = 36204
SOURCE_UNAVAILABLE_ACCESSION_COUNT = 2
SOURCE_UNAVAILABLE_LEDGER_SHA256 = 57f22bfa0f392995fb250e5c1b1ba5469a1a1cc3b298d68f7cf0fa7c1e11fb51
SELECTIVE_EXECUTION_INVENTORY_V2_SHA256 = 1b5c311186446513272891a9075d3dac132b19a6fc1cad9916b5cd0508340642
PRIVATE_CLOSEOUT_REPORT_SHA256 = 40c67f664c5d74d7c631c84d79daa7231840fb14dae44106684b7d5aca660595
TRANSITION_FINANCIAL_ACCESSION_COUNT = 2
TRANSITION_EVIDENCE_COUNT = 115
FAILED_REQUIRED_ACCESSION_COUNT = 0
AQ_FORM_ROUTER_ENGINE = NO
AQ_XBRL_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
BROAD_FULL_UNIVERSE_EXECUTION_STARTED = NO
P5_HISTORICAL_DATASET_BUILT = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_EDGARTOOLS_SELECTIVE_FULL_HISTORICAL_BUILD_EXECUTION_RESUME_001
```
