# P5 EdgarTools Selective Full Historical Build Execution 001

Status: **BLOCKED — PRE-EXECUTION INPUT INTEGRITY**

The production runner was invoked from authoritative main
`ffc8607c9e3d2b4d89d73461b89d222a11df996e`. Offline validation confirmed the
frozen EntityFacts-first selection identity and exactly 36,206 unique required
accessions. Execution then failed closed before configuring EdgarTools or
issuing a build request because four selected accessions have no row in the
frozen 36,582-row native filing-metadata inventory.

The exact blockers are:

| accession | CIK | EntityFacts form | native SEC/EdgarTools result |
| --- | --- | --- | --- |
| `0001100682-20-000033` | `0001100682` | `10-Q` | absent from `Company(CIK).get_filings()` and exact filing homepage has zero attachments |
| `0001108524-21-000014` | `0001108524` | `10-K` | absent from `Company(CIK).get_filings()` and exact filing homepage has zero attachments |
| `0001193125-10-257767` | `0001339947` | `10-K` | exact SEC filing exists as `10-KT`, outside the frozen EdgarTools native periodic-object admission |
| `0001418135-18-000016` | `0001418135` | `10-Q` | exact SEC filing exists as `10-QT`, outside the frozen EdgarTools native periodic-object admission |

No accession substitution, form rewriting, current-filing backfill, or manual
exception was admitted. The production build has zero formal checkpoints,
evidence partitions, event partitions, source manifests, or failure-ledger
rows. The limited diagnostic EdgarTools cache was evicted after classification.
The certified canary and frozen inputs remain unchanged.

```text
ENTITYFACTS_FIRST_PATH = PASS
FULL_BUILD_CANARY_STATUS = PASS
SELECTIVE_REQUIRED_ACCESSION_COUNT = 36206
PREEXECUTION_REQUIRED_ACCESSION_BLOCKER_COUNT = 4
FORMAL_ACCESSION_PROCESSING_STARTED = NO
FORMAL_BUILD_SOURCE_NETWORK_BYTES = 0
UNACCOUNTED_ACCESSION_COUNT = 36206
P5_HISTORICAL_DATASET_BUILT = NO
DVC_SEAL_STATUS = NOT_RUN
OFFLINE_DERIVED_EVIDENCE_REPLAY = NOT_RUN
QLIB_FULL_HISTORICAL_HANDOFF = NOT_RUN
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_DEVELOPMENT_NEXT =
P5_HISTORICAL_BUILD_REQUIRED_ACCESSION_FAILURE_CLOSEOUT_001
```
