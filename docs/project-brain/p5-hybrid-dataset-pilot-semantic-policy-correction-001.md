# P5 Hybrid Dataset Pilot Semantic Policy Correction 001

## Outcome

```text
TASK = AUTONOMOUS-QUANT-P5-HYBRID-DATASET-PILOT-SEMANTIC-POLICY-CORRECTION-001
BASE_MAIN_SHA = c014be920aed629f15c70123b0341c002ab212a1
BRANCH_INITIAL_SHA = 0a9ca73df085b6bda1cae4ff6d450ca6aaceffdb
P5_HYBRID_DATASET_SEMANTIC_POLICY_CORRECTION = PASS
P5_METRIC_IDENTITY_AUTHORITY = EDGARTOOLS_STANDARD_CONCEPT_ID
P5_PERIOD_SEMANTIC_POLICY = MATERIALIZED
P5_DIMENSION_POLICY = CONSOLIDATED_ONLY
P5_PRETRAIN_LOOKBACK_POLICY = CORRECTED
P5_PILOT_MERGE_READY = PENDING_REVALIDATION
P5_FULL_BUILD_GATE = CLOSED_IDENTITY_ACCOUNTING_REQUIRED
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_HYBRID_DATASET_PILOT_REVALIDATION_AND_MERGE_GATE_001
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
```

The same bounded six-episode pilot and two negative controls were rebuilt from
the frozen private sources. No CIK, episode, accession sample, metric business
scope, or research date window was expanded. Historical TEST and sealed OOS
were not accessed.

## Upstream semantic authority

EdgarTools 5.58.0 at source authority
`e23d04eba952e70310c0f62402f4c2523f9a44bf` remains the owner of standard
concept identity and XBRL duration classification. The frozen 11 business
semantics now use the exact upstream machine identifiers:

```text
Revenue
NetIncome
Assets
Liabilities
CommonEquity
NetCashFromOperatingActivities
CashAndCashEquivalents
CurrentAssetsTotal
CurrentLiabilitiesTotal
ShortTermDebt
LongTermDebt
```

Display labels are presentation metadata only. They do not participate in
event identity, evidence identity, projection admission, grouping, or Qlib
feature identity. No punctuation normalization, synonym table, fuzzy matcher,
or AQ accounting ontology was added.

Duration facts are admitted from EdgarTools' `duration_days` and
`classify_duration` results into the bounded project policy classes
`DURATION_QUARTERLY`, `DURATION_SEMI_ANNUAL`, `DURATION_NINE_MONTHS`,
`DURATION_ANNUAL`, and `DURATION_OTHER`; instant contexts remain `INSTANT`.
AQ adds no duration thresholds or generic classification engine. Direct facts
remain direct: no derived quarterization is performed.

The event semantic stream key is:

```text
CIK + standard_concept + period_class
```

Exact report-period start/end and filing provenance remain attached to each
event. A later amendment may supersede only within the same semantic stream
and becomes visible only on or after its own effective session.

## Dimension, lookback, and membership policy

The initial feature panel is `CONSOLIDATED_ONLY`. Dimension-bearing evidence
is retained and replayable as FundamentalEvidence, but it is not aggregated or
collapsed into a consolidated feature. The frozen AAPL ServiceMember fixture
proved the dimension path and was excluded without changing any consolidated
value.

Pre-train lookback is required only to the extent that authoritative history
for the same CIK exists before the first eligible research session.
Historically nonexistent evidence remains missing. A pre-membership filing can
appear on a later eligible row only when the row has exact same-CIK binding,
required PIT membership, and prior public availability. It creates no row
before membership; a different or predecessor CIK is rejected absent separate
authority.

## Rebuilt pilot evidence

```text
PILOT_INPUT_EPISODES = 8
PILOT_ADMITTED_EPISODES = 6
NEGATIVE_IDENTITY_EXCLUSIONS = 2
EXACT_ADMITTED_ACCESSIONS = 14
FUNDAMENTAL_EVIDENCE_COUNT = 116
DIMENSION_BEARING_EVIDENCE_COUNT = 1
STANDARDIZED_EVENT_COUNT = 115
STANDARDIZED_CONCEPT_COUNT = 11
SESSION_PROJECTION_ROW_COUNT = 78406
NON_NULL_PROJECTED_VALUE_COUNT = 75485
MISSING_PROJECTED_VALUE_COUNT = 2921
METRIC_IDENTITY_MISMATCH_COUNT = 0
INCOMPATIBLE_PERIOD_STREAM_MIX_COUNT = 0
ANNUAL_QUARTERLY_OVERWRITE_COUNT = 0
INSTANT_DURATION_MIX_COUNT = 0
EARLY_VISIBILITY_COUNT = 0
CROSS_CIK_CONTAMINATION_COUNT = 0
UNTRACEABLE_PROJECTED_VALUE_COUNT = 0
SHORT_TERM_DEBT_OBSERVED = YES
LONG_TERM_DEBT_OBSERVED = YES
```

The Qlib handoff uses deterministic machine-key feature identities such as
`Revenue__DURATION_QUARTERLY` and `Assets__INSTANT`. StaticDataLoader,
DataHandlerLP, DatasetH, train access, and validation access pass. Historical
TEST access was not executed; there was no model fit, prediction, or backtest.

The existing P5 DVC stage now seals only the corrected private root. Its two
reproductions produced identical seal bytes. Existing P2/P3 DVC stage bodies
and lock entries are unchanged.

```text
QLIB_HANDOFF = PASS
DVC_PILOT_SEAL = PASS
DETERMINISTIC_REPLAY = PASS
NETWORK_REQUESTS = 0
AQ_NEW_PRODUCTION_LOC = 45
AQ_METRIC_ALIAS_TABLE = NO
AQ_PERIOD_CLASSIFICATION_ENGINE = NO
AQ_DIMENSION_AGGREGATION_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Validation and private evidence

```text
P5_FOCUSED_TESTS = 55 PASSED; 29 SUBTESTS PASSED
P1_RELEVANT_REPLAY = 36 PASSED; 9 SKIPPED; 23 SUBTESTS PASSED
QLIB_ADAPTER_TESTS = 25 PASSED
RUFF = PASS
```

Private evidence remains outside Git at:

```text
D:/AQ_DATA/P5/hybrid-dataset-pilot-semantic-policy-correction-001/correction_summary.json
SHA256 = a1fb9a66c78b090fc2c3fe494f69c3a757bf4134bd175602377db90577b9c122
```

This PASS does not authorize the full historical dataset. Independent pilot
revalidation must decide merge readiness. Full-universe work remains gated on
identity-accounting audit after the corrected pilot reaches main.
