# P2 Frozen Certification Dataset Git Scope Clarification 001

**Task:** `AUTONOMOUS-QUANT-P2-FROZEN-CERTIFICATION-DATASET-GIT-SCOPE-CLARIFICATION-001`
**Base:** `e17bd5bf971086619730a1d9766e17b611171852`
**Result:** `PASS`

## Purpose

This record resolves one reporting ambiguity in the frozen certification
dataset contract. It does not change dataset composition, source precedence,
identity, membership, session, corporate-action, missing-data, adjustment,
freeze, validation, or consumer policy.

The repository already contains two public DISCK OHLCV corroboration rows in
historical Project Brain evidence. They predate the frozen-contract commit and
remain necessary audit evidence. They are not provider payloads, certification
dataset observations, DVC artifacts, private/licensed data, or training input.
The historical evidence is preserved unchanged.

## Precise Git safety boundary

The authoritative certification Git boundary is:

```text
CERTIFICATION_DATASET_ROWS_IN_GIT = NO
PROVIDER_PAYLOADS_IN_GIT = NO
PRIVATE_MARKET_DATA_IN_GIT = NO
LICENSED_MARKET_DATA_IN_GIT = NO
DVC_DATA_ARTIFACTS_IN_GIT = NO
CREDENTIALS_IN_GIT = NO
PRIVATE_EVIDENCE_IN_GIT = NO
HISTORICAL_PUBLIC_CORROBORATION_VALUES_IN_DOCUMENTATION = ALLOWED_EVIDENCE_ONLY
HISTORICAL_PUBLIC_CORROBORATION_IS_CERTIFICATION_DATA = NO
HISTORICAL_PUBLIC_CORROBORATION_IS_PROVIDER_SUBSTITUTE = NO
HISTORICAL_PUBLIC_CORROBORATION_IS_TRAINING_INPUT = NO
HISTORICAL_PUBLIC_CORROBORATION_MAY_FILL_MISSING_PRICE = NO
```

The unqualified field `MARKET_DATA_IN_GIT` must not be used by itself as a
repository-wide certification criterion. A validation or final report must use
the scoped fields above. Historical public values may appear in documentation
only when necessary as audit evidence; this allowance does not authorize new
dataset rows, payloads, private evidence, or training inputs in Git.

## DISCK preservation

```text
DISCK_2022_04_08_CLASSIFICATION = KNOWN_TERMINAL_SESSION_PROVIDER_GAP
DISCK_2022_04_08_PRIMARY_ROW = ABSENT
DISCK_SYNTHETIC_ROW = NO
DISCK_FORWARD_FILL = NO
DISCK_SESSION_TRADABLE = NO
DISCK_TERMINAL_ACTION = CLOSED_1_TO_1_WBD
DISCK_EXTERNAL_PUBLIC_VALUES = CORROBORATION_ONLY_NOT_CERTIFICATION_DATA
WBD_DISCA_DISCB_SUBSTITUTION = PROHIBITED
```

No public corroboration value may fill the missing DISCK observation or make
the session tradable.

## Frozen contract and ownership preservation

```text
CURRENT_PROFILE = PERSONAL_CAPITAL_CERTIFICATION
FROZEN_CERTIFICATION_DATASET_CONTRACT_V1 = FROZEN
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
SOURCE_PRECEDENCE = QUANTIACS_PRIMARY_SIMFIN_BOUNDED_SECONDARY
SECURITY_EPISODE_CONTRACT = FROZEN
PIT_MEMBERSHIP_CONTRACT = FROZEN
SESSION_CONTRACT = FROZEN
CORPORATE_ACTION_CONTRACT = FROZEN
MISSING_DATA_CONTRACT = FROZEN
PRICE_ADJUSTMENT_CONTRACT = FROZEN
REPRODUCIBILITY_CONTRACT = FROZEN
VALIDATION_CONTRACT = FROZEN
SEALED_OOS_DATES_SELECTED = NO
P2_CERTIFICATION_WINDOW_STATUS = NOT_YET_PREREGISTERED
CUSTOM_ENGINE_REQUIRED = NO
```

DVC retains snapshot/freeze/reproducibility mechanics; Pandera retains generic
schema validation; `exchange_calendars` retains XNYS sessions; Qlib remains the
downstream research consumer; and Quantiacs plus SimFin remain price providers.
AQ owns only the project-specific contract, precedence, identity/episode,
membership, missing-data, and certification-acceptance policy.

## Non-actions and next state

```text
HISTORICAL_PUBLIC_EVIDENCE_PRESERVED = YES
FROZEN_CONTRACT_SUBSTANCE_CHANGED = NO
PRODUCTION_CODE_CHANGED = NO
DATASET_BUILD_STARTED = NO
MARKET_DATA_DOWNLOADED = NO
PROVIDER_PAYLOAD_ADDED = NO
PRIVATE_ARTIFACT_ADDED = NO
MODEL_TRAINING = NO
BACKTEST = NO
QLIB_EXECUTED = NO
SKFOLIO_EXECUTED = NO
ARCH_EXECUTED = NO
PUSHED = NO
PR_CREATED = NO
MERGED = NO
CURRENT_NEXT = P2_FROZEN_CERTIFICATION_DATASET_BUILD_001
```
