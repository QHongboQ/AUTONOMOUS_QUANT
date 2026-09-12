# P2 Frozen Certification Dataset Contract 001

**Task:** `AUTONOMOUS-QUANT-P2-FROZEN-CERTIFICATION-DATASET-CONTRACT-001`
**Base:** `a71df867c6d46a1844f3899a7d2cb47b6f9e873f`
**Result:** `PASS`

## Authority and scope

This document freezes the composition and acceptance boundary for the future
P2 certification dataset. It defines what the dataset must contain, how every
observation is bound and classified, how a version becomes immutable, and
which downstream certification consumers may use it. It does not build the
dataset or select certification partitions.

```text
CAPABILITY = FROZEN_CERTIFICATION_DATASET_CONTRACT
UPSTREAM_OWNER = DVC_PLUS_PANDERA_PLUS_EXCHANGE_CALENDARS_PLUS_QLIB_PLUS_QUANTIACS_PLUS_SIMFIN
OWNERSHIP_MODE = UPSTREAM_LEAF_PLUS_UPSTREAM_WHOLE_PLUS_AQ_OWNED_THIN_POLICY
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = CONTRACT_POLICY_SCHEMA_BOUNDARY_ONLY
AQ_ALLOWED_SCOPE = DATASET_COMPOSITION_POLICY_IDENTITY_BINDING_SOURCE_PRECEDENCE_MISSING_DATA_CLASSIFICATION_FREEZE_VERSION_CONTRACT_CERTIFICATION_CONSUMER_BOUNDARY
CUSTOM_ENGINE_REQUIRED = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

DVC owns snapshot and dependency reproducibility, Pandera owns generic tabular
validation, `exchange_calendars` owns XNYS sessions, Qlib owns downstream
research interfaces, and Quantiacs/SimFin own their provider observations. AQ
owns only the thin project-specific policy joining accepted identities,
episodes, membership, provenance, gaps, and certification boundaries.

## Reconciliation with historical authority

The historical `CertificationDataContractV1` remains an accurate record of
the earlier institutional-style qualification stage and is not rewritten.
The later accepted authority changes only the requirements explicitly
reclassified for the current profile:

```text
CURRENT_PROFILE = PERSONAL_CAPITAL_CERTIFICATION
DAILY_PRICE_VENDOR_REVISION_ID_REQUIRED = NO_IF_AUTHORIZED_SEALED_LOCAL_OBSERVATION_SNAPSHOT
QUANTIACS_INDEFINITE_ARCHIVAL_RIGHT = NOT_ESTABLISHED_NOT_REQUIRED
KNOWN_TERMINAL_SESSION_PROVIDER_GAP = ACCEPTED_NONBLOCKING_ONLY_WHEN_ALL_POLICY_CONDITIONS_HOLD
```

This reconciliation does not weaken PIT membership, security identity,
ticker-reuse protection, episode boundaries, corporate-action correctness,
no-lookahead rules, the prohibition on silent synthetic fills,
survivorship-bias controls, sealed OOS, or multiple-testing controls.

## Contract identity and history floor

```text
FROZEN_CERTIFICATION_DATASET_CONTRACT_V1 = FROZEN
DATASET_CONTRACT_VERSION = FROZEN_CERTIFICATION_DATASET_CONTRACT_V1
CURRENT_MODEL_LINEAGE_HISTORY_FLOOR = 2015-01-02
P2_CERTIFICATION_WINDOW_STATUS = NOT_YET_PREREGISTERED
```

The history floor is the current source-data lineage boundary. It is not a
train, validation, or sealed-certification-OOS boundary. A dataset conforming
to this contract must support later deterministic partitioning into `TRAIN`,
`VALIDATION`, and `SEALED_CERTIFICATION_OOS` without changing the underlying
observations.

## Logical components

### 1. Security and episode table

Each record must carry:

```text
security_identity
instrument_episode_id
valid_from
valid_to
ticker
exchange
membership_from
membership_to
identity_status
identity_evidence_hash
```

This is a bounded certification table, not a generic security master.

### 2. Daily price table

Each admitted observation must carry:

```text
instrument_episode_id
security_identity
session
open
high
low
close
volume
provider
provider_asset_identifier
provider_symbol
adjustment_semantics
source_observation_status
source_content_hash
```

The price table stores observed provider facts only. Absence belongs in the
gap/availability component, not in a fabricated rectangular price row.

### 3. Corporate-action table

Each applicable event must carry:

```text
instrument_episode_id
security_identity
event_type
effective_date
ex_date
split_ratio
cash_distribution
successor_security
conversion_ratio
event_status
authority_source
authority_hash
```

Inapplicable optional values remain explicitly null under the frozen schema;
they are not guessed. Corporate-action evidence does not manufacture a price
or membership event.

### 4. Gap and availability table

Each classified unavailable episode/session must carry:

```text
session
instrument_episode_id
gap_classification
tradable
reason
corroboration_status
terminal_event_reference
```

The table is authoritative for explicit absence. It must not create an OHLCV
row merely to make a matrix rectangular.

### 5. Certification dataset manifest

Every frozen version must record:

```text
dataset_contract_version
dataset_version
dataset_id
created_at_utc
provider_set
source_versions
tool_versions
calendar_name
calendar_version
identity_policy_hash
mapping_policy_hash
schema_hash
component_hashes
code_sha
dvc_hashes
known_gap_inventory
row_counts
episode_counts
coverage_metrics
```

The manifest is canonical and machine-readable when built. A sidecar SHA-256
is computed over canonical manifest bytes excluding self-referential
`dataset_id` and manifest-digest fields. `dataset_id` is then derived as
`FCDCV1:<manifest_sha256>`. The build task must freeze the exact canonical
serialization; this contract does not implement it.

## Deterministic source precedence

```text
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
SOURCE_PRECEDENCE = QUANTIACS_PRIMARY_SIMFIN_BOUNDED_SECONDARY
PRIMARY_PRICE_PROVIDER = QUANTIACS
BOUNDED_SECONDARY_PRICE_PROVIDER = SIMFIN
YAHOO = RETIRED_FROM_CERTIFICATION_PRICE_ROUTE
TIINGO_STARTER = RETIRED_FROM_CERTIFICATION_PRICE_ROUTE
PUBLIC_HISTORICAL_SITES = CORROBORATION_ONLY_NOT_DATASET_PROVIDER
```

Quantiacs is consulted first for an accepted episode/session. SimFin may
contribute only when the Quantiacs observation is absent and accepted
security/episode policy explicitly permits the exact SimFin observation.
Provider identity, episode validity, source status, and adjustment semantics
must all pass before admission. A row is never selected because its value is
more convenient or visually preferable. Every final observation retains its
provider and source-content provenance.

Provider mixing is a deterministic, auditable exception path. It may not
silently combine fields from different providers into one OHLCV observation.

## Security identity and episode contract

```text
SECURITY_IDENTITY_NOT_EQUAL_TICKER_EPISODE = YES
FB_META_CROSS_EPISODE_DIRECT_RELABEL = 0
SECURITY_EPISODE_CONTRACT = FROZEN
```

A security may have multiple ticker episodes. Provider observations bind first
to `SecurityIdentity` and then to the date-valid `InstrumentEpisode` only when
accepted stable-security evidence supports continuity. Ticker text, issuer-name
similarity, or price continuity alone is insufficient. Ticker reuse never
collapses unrelated securities, and non-contiguous exit/re-entry intervals
remain separate episodes.

An undated or ambiguous provider symbol is fail-closed and cannot enter the
certification dataset.

## PIT membership contract

```text
PIT_MEMBERSHIP_AUTHORITY = AQ_ACCEPTED_SP500_EPISODE_FACTS
PIT_MEMBERSHIP_CONTRACT = FROZEN
CURRENT_CONSTITUENT_BACKFILL = PROHIBITED
SURVIVORSHIP_ONLY_UNIVERSE = PROHIBITED
```

AQ's accepted project-specific S&P 500 episode facts remain authoritative for
membership. Provider convenience lists and present-day constituent lists
cannot override them. For every certification session, membership is evaluated
from information valid for that session. Price availability never creates or
extends membership.

## Session contract

```text
SESSION_AUTHORITY = EXCHANGE_CALENDARS_XNYS
SESSION_CONTRACT = FROZEN
AQ_CUSTOM_CALENDAR_LOGIC = NONE
```

Every admitted daily US-equity observation must map to an accepted XNYS
session through the pinned `exchange_calendars` authority. A separately
documented market-specific exception would require a new dataset version and
policy review; it cannot be inferred during ingestion.

## Corporate-action contract

```text
CORPORATE_ACTION_CONTRACT = FROZEN
CORPORATE_ACTION_CREATES_PRICE = NO
CORPORATE_ACTION_CREATES_MEMBERSHIP = NO
```

Actions bind to exact security identities and valid episodes with explicit
effective/ex-date semantics and authority hashes. Splits, distributions,
renames, conversions, and successor treatment remain distinct from price and
membership. Missing action evidence is explicit and fail-closed where the
action is required by the registered dataset scope.

## Missing-data contract

The closed classification set is:

```text
OBSERVED
KNOWN_PROVIDER_GAP
KNOWN_TERMINAL_SESSION_PROVIDER_GAP
NOT_APPLICABLE_OUTSIDE_EPISODE
NOT_MEMBER_ON_SESSION
UNRESOLVED_ERROR
```

```text
MISSING_DATA_CONTRACT = FROZEN
MISSING_EQUALS_ZERO = NO
MISSING_EQUALS_FORWARD_FILLED_PRICE = NO
MISSING_EQUALS_SUCCESSOR_PRICE = NO
MISSING_EQUALS_SYNTHETIC_ROW = NO
UNKNOWN_GAP_CLASSIFICATION = FAIL_CLOSED
```

`OBSERVED` requires a valid source row and full provenance.
`KNOWN_PROVIDER_GAP` records accepted provider absence without making the
session tradable. `KNOWN_TERMINAL_SESSION_PROVIDER_GAP` is allowed only under
the eight-condition policy frozen by the preceding blocker-resolution task.
The two outside-scope classes distinguish episode and membership absence from
data error. `UNRESOLVED_ERROR` is blocking.

For DISCK on 2022-04-08 the accepted state is frozen exactly:

```text
DISCK_2022_04_08_CLASSIFICATION = KNOWN_TERMINAL_SESSION_PROVIDER_GAP
DISCK_2022_04_08_PRIMARY_ROW = ABSENT
DISCK_SYNTHETIC_ROW = NO
DISCK_FORWARD_FILL = NO
DISCK_SESSION_TRADABLE = NO
DISCK_TERMINAL_ACTION = CLOSED_1_TO_1_WBD
DISCK_EXTERNAL_CORROBORATION_ROLE = CORROBORATION_ONLY_NOT_DATASET_OBSERVATION
```

No externally corroborated OHLCV may be inserted into the primary dataset,
and no WBD, DISCA, or DISCB row may substitute for DISCK. The known accepted
terminal gap is counted separately from unresolved errors.

## Price and adjustment contract

```text
PRICE_ADJUSTMENT_CONTRACT = FROZEN
SILENT_ADJUSTMENT_MIXING = PROHIBITED
```

Every admitted series and field must state whether it is raw,
split-adjusted, dividend-adjusted, or total-return-adjusted. The frozen dataset
manifest must declare the exact representation used for model features,
labels, execution simulation, and corporate-action handling. Two providers or
fields with incompatible semantics cannot be merged without an explicit new
policy and dataset version.

This contract does not create a normalization engine or choose a representation
without observed provider evidence. The future build must resolve and freeze
one internally consistent representation before the dataset can pass.

## Reproducibility and version contract

```text
SNAPSHOT_AUTHORITY = DVC
REPRODUCIBILITY_CONTRACT = FROZEN
IN_PLACE_MUTATION = PROHIBITED
```

A frozen version requires its immutable dataset ID, canonical manifest,
component hashes, code SHA, source/tool versions, provider request/config
evidence, policy hashes, schema hashes, known-gap inventory, and DVC hashes.
The underlying private licensed/provider bytes remain outside Git; Git may
contain only contracts and non-sensitive hashes/manifests permitted by source
terms.

Any change to source observations, identity mapping, membership facts,
corporate actions, gap classification, schema, or policy creates a
`NEW_DATASET_VERSION`. Downstream certification evidence must reference the
exact immutable dataset ID. A later provider correction never overwrites prior
certification history silently.

## Validation contract

```text
GENERIC_TABULAR_VALIDATION_OWNER = PANDERA
AQ_VALIDATION_SCOPE = PROJECT_SPECIFIC_ACCEPTANCE_RULES_ONLY
VALIDATION_CONTRACT = FROZEN
```

The future build fails closed on at least:

- duplicate episode/session observations;
- out-of-episode joins;
- invalid XNYS sessions;
- nonfinite required observed OHLC;
- negative volume;
- silent forward fill;
- undisclosed synthetic rows;
- cross-security ticker-reuse joins;
- membership leakage or current-constituent backfill;
- missing provider provenance;
- unknown gap classifications.

Validation success cannot repair missing authority or silently reclassify an
unresolved error.

## Coverage contract

Every frozen manifest must record:

```text
REQUIRED_EPISODES
MAPPED_EPISODES
PRICE_COVERED_EPISODES
ACTION_COVERED_EPISODES
KNOWN_PROVIDER_GAPS
KNOWN_TERMINAL_GAPS
UNRESOLVED_ERRORS
TOTAL_SESSIONS
OBSERVED_PRICE_ROWS
```

An accepted nonblocking terminal gap is a known gap, not an unresolved error.
Counts must reconcile deterministically to the manifest's component hashes and
registered scope.

## Sealed-OOS and consumer boundary

The frozen dataset may eventually contain observations spanning several
partitions. Sealed status belongs to a later preregistered partition contract,
not to this dataset-contract task.

```text
P1_OBSERVED_TEST_INTERVAL = 2022-01-03_THROUGH_2025-12-29
P1_TEST_SET_IS_PRISTINE_OOS = NO
SEALED_OOS_DATES_SELECTED = NO
P2_CERTIFICATION_WINDOW_STATUS = NOT_YET_PREREGISTERED
```

Only a successfully built and frozen dataset version may be consumed by future
P2 temporal-integrity checks, deterministic train/validation partitioning,
sealed-OOS preregistration, skfolio CV, arch multiple-testing, Qlib benchmark
and stress evaluation, or `CertificationDecision`. Research code may read but
must not mutate the frozen dataset. No consumer may repair or reinterpret it
in place.

## Current state and non-actions

```text
P2_DATA_SOURCE_VALIDATION = CLOSED
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
REMAINING_CERTIFICATION_DATA_HARD_BLOCKERS = NONE
NO_ADDITIONAL_PRICE_PROVIDER_REQUIRED = YES
PROVIDER_EXPANSION_GATE = CLOSED
FROZEN_CERTIFICATION_DATASET_CONTRACT_V1 = FROZEN
P2_CERTIFICATION_WINDOW_STATUS = NOT_YET_PREREGISTERED
MARKET_DATA_DOWNLOADED = NO
MARKET_DATA_IN_GIT = NO
PROVIDER_RESPONSE_BODY_IN_GIT = NO
CREDENTIAL_IN_GIT = NO
NEW_PROVIDER_ADDED = NO
MODEL_TRAINING = NO
BACKTEST = NO
QLIB_EXECUTED = NO
SKFOLIO_EXECUTED = NO
ARCH_EXECUTED = NO
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
PUSHED = NO
PR_CREATED = NO
MERGED = NO
CURRENT_NEXT = P2_FROZEN_CERTIFICATION_DATASET_BUILD_001
```

The dataset build, partition preregistration, and every certification consumer
remain unstarted.
