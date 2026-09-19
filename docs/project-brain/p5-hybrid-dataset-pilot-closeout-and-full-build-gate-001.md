# P5 Hybrid Dataset Pilot Closeout and Full Build Gate 001

## Outcome

```text
TASK = AUTONOMOUS-QUANT-P5-HYBRID-DATASET-PILOT-CLOSEOUT-AND-FULL-BUILD-GATE-001
BASE_MAIN_SHA = c014be920aed629f15c70123b0341c002ab212a1
PILOT_CLAIMS_RECONCILED = YES
P5_HYBRID_MECHANISM_READINESS = PASS
P5_HYBRID_DATASET_PILOT_CLOSEOUT = BLOCKED_SEMANTIC_POLICY
P5_PILOT_MERGE_READY = NO
P5_FULL_UNIVERSE_IDENTITY_ACCOUNTING_COMPLETE = NO
P5_FULL_BUILD_GATE = FULL_BUILD_BLOCKED_SEMANTIC_POLICY
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_HYBRID_DATASET_PILOT_SEMANTIC_POLICY_CORRECTION_001
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
```

The independent audit confirms the hybrid transport and ownership mechanism,
but it does not authorize a full build or merge the pilot. Two semantic defects
must be corrected: the debt vocabulary does not exactly match EdgarTools'
canonical names, and the session projection collapses annual and quarterly
flow facts into one period class. Full-universe identity accounting is also
not materialized and remains a later mandatory gate.

## Whole-diff and pilot reconciliation

The branch began exactly one commit ahead of and zero commits behind
`origin/main`. Its nine changed files are limited to the new thin historical
dataset leaf, its tests, one pilot Project Brain report, the active Brain
summary, and one appended DVC stage/lock entry. No P1, P2, P3, P4, P12,
existing Qlib runtime, or existing P5 contract file changed.

```text
CHANGED_FILE_COUNT = 9
UNRELATED_RUNTIME_DIFF = NONE
PILOT_INPUT_CASE_COUNT = 8
PILOT_ADMITTED_EPISODE_COUNT = 6
NEGATIVE_IDENTITY_EXCLUSION_COUNT = 2
FSDS_QUARTER_COUNT = 35
FSDS_INDEXED_REPORT_COUNT = 245363
FSDS_INDEXED_CIK_COUNT = 13125
CANDIDATE_ACCESSION_COUNT = 192
EXACT_ADMITTED_ACCESSION_COUNT = 14
FUNDAMENTAL_EVIDENCE_COUNT = 96
UNIQUE_EVIDENCE_ID_COUNT = 96
STANDARDIZED_EVENT_COUNT = 96
STANDARDIZED_METRIC_COUNT = 9
ELIGIBLE_EPISODE_SESSION_COUNT = 7136
SESSION_PROJECTION_ROW_COUNT = 51120
```

The pilot summary and seal recomputed to their recorded SHA-256 values. The
pilot's count claims therefore reconcile; this does not make its bounded sample
a full-universe census.

## Mechanism, implementation, and DVC

The following real path is proven:

```text
InstrumentEpisodeV1
  -> EpisodeSecCikBindingV1
  -> secfsdstools candidate catalog
  -> EdgarTools exact accession
  -> FundamentalEvidenceV1
  -> standardized event
  -> XNYS effective session
  -> pandas.merge_asof
  -> Parquet
  -> DVC
  -> Qlib StaticDataLoader / DataHandlerLP / DatasetH
```

FSDS acceptance, FSDS floating-point NUM values, and the secfsdstools default
standardizer never became admission authority. There were no early-visible,
cross-CIK, membership-leaking, or untraceable projected rows.

The 238 production LOC remain thin domain policy: effective-session selection,
episode/binding/membership containment, one `pandas.merge_asof` invocation,
exact-string Parquet projection, and seal glue. They do not implement a SEC
client, XBRL/statement engine, security master, report index, warehouse,
generic ETL, or generic as-of engine.

The DVC stage seals exactly five private pilot outputs. It does not duplicate
the shared FSDS catalog. Text preceding the new stage in both `dvc.yaml` and
`dvc.lock` is byte-for-byte equivalent after line-ending normalization to
`origin/main`; existing P2/P3 stage semantics are unchanged.

```text
AQ_IMPLEMENTATION_SCOPE = THIN_DOMAIN_SPECIFIC
AQ_NEW_GENERIC_ENGINE_COUNT = 0
DVC_PILOT_AUDIT = PASS
P2_DVC_AUTHORITY_MUTATED = NO
P3_DVC_AUTHORITY_MUTATED = NO
FSDS_BULK_CATALOG_DUPLICATED_IN_DVC = NO
```

## Full-universe identity gate

The repository has a materialized `EpisodeSecCikBindingV1` contract and six
POC/pilot fixtures, but no accepted full-universe binding ledger. Fixtures and
private pilot examples are not promoted into a full-universe authority table.

```text
FULL_P1_EPISODE_COUNT = 832
FULL_UNIVERSE_ADMITTED_BINDING_EPISODE_COUNT = 0
FULL_UNIVERSE_FULL_BINDING_EPISODE_COUNT = 0
FULL_UNIVERSE_PARTIAL_BINDING_EPISODE_COUNT = 0
FULL_UNIVERSE_UNBOUND_EPISODE_COUNT = 832
FULL_UNIVERSE_AMBIGUOUS_EPISODE_COUNT = 0_UNMEASURED
FULL_UNIVERSE_MISSING_AUTHORITY_EPISODE_COUNT = 0_UNMEASURED
FULL_UNIVERSE_NO_SEC_FILER_EPISODE_COUNT = 0_UNMEASURED
FULL_UNIVERSE_BINDING_COVERAGE_MEASURED = NO
FULL_UNIVERSE_IDENTITY_ACCOUNTING_COMPLETE = NO
```

Here `832 unbound` means only that no full-universe materialized binding record
exists. It is not an adjudication that all 832 lack SEC filers. The zero
exclusion counts are likewise zero materialized classifications, not evidence
that no ambiguous, missing-authority, or no-filer cases exist.

## Sample, scaling, and storage

The 14 exact accessions are a mechanism sample, not a full filing census for
the six episodes. The 192 FSDS rows are CIK/form-filtered candidates across the
catalog window; they are not a sealed episode/binding-interval exact-accession
census. They cannot be multiplied or extrapolated to 832 episodes.

```text
PILOT_EXACT_ACCESSION_SELECTION = MECHANISM_SAMPLE
SIX_EPISODE_FULL_FILING_CENSUS = NO
FULL_BUILD_ACCESSION_CENSUS_REQUIRED = YES
EXACT_ADMISSION_SCALE_ESTIMATE = BOUNDED_LOWER_EVIDENCE
FULL_BUILD_SCALE_MODEL = SHARED_CATALOG_PLUS_PER_ACCESSION_ADMISSION
STORAGE_SCALE_STATUS = NEEDS_ACCESSION_CENSUS
```

The shared catalog cost remains about 3.08 GB compressed, 3.19 GB Parquet,
and 83 MB SQLite and must not be multiplied by episode count. Exact admission
observed 14 accessions and 196,511,283 source bytes. The 256 GB constraint is
plausible under bounded-hybrid retention, but it cannot be certified until a
full eligible-accession census exists.

## Lookback and pre-membership policy clarification

The pilot's universal five-quarter/two-year pre-2015 wording is not valid for
a filer such as new DD CIK `0001666700`, which did not yet exist. The active
policy is now:

```text
PRETRAIN_LOOKBACK_POLICY_AUDIT = REQUIRES_CLARIFICATION
PRETRAIN_LOOKBACK_POLICY = LOOKBACK_IS_REQUIRED_ONLY_TO_THE_EXTENT_SAME_CIK_AUTHORITATIVE_HISTORY_EXISTS_BEFORE_THE_FIRST_ELIGIBLE_RESEARCH_SESSION; HISTORICALLY_NONEXISTENT_EVIDENCE_REMAINS_MISSING; FACTOR_SPECIFIC_MINIMUM_HISTORY_IS_A_LATER_ELIGIBILITY_RULE_AND_MUST_NOT_REPAIR_IDENTITY_OR_SUBSTITUTE_A_PREDECESSOR_CIK
```

The corresponding pre-membership rule is:

```text
PRE_MEMBERSHIP_SAME_CIK_EVIDENCE_POLICY = A_FILING_ACCEPTED_BEFORE_EPISODE_OR_INDEX_MEMBERSHIP_MAY_BE_USED_ONLY_ON_A_LATER_ELIGIBLE_SESSION_WHEN_THE_SESSION_HAS_A_VALID_EXACT_SAME_CIK_BINDING_AND_REQUIRED_PIT_MEMBERSHIP_AND_THE_FILING_WAS_PUBLICLY_AVAILABLE_BEFORE_THAT_SESSION; IT_CREATES_NO_PRE_MEMBERSHIP_ROW_AND_A_DIFFERENT_OR_PREDECESSOR_CIK_REQUIRES_SEPARATE_AUTHORITY
```

These rules separate issuer evidence existence from research-universe row
eligibility and do not manufacture predecessor continuity.

## Metric and dimension gate

The two missing frozen metrics are `Short Term Debt` and `Long Term Debt`.
Frozen exact-source filings contain relevant debt tags, and EdgarTools' mapper
supports those concepts, but it emits the canonical labels `Short-Term Debt`
and `Long-Term Debt`. Those strings do not exactly equal the frozen unhyphenated
vocabulary, so the pilot silently excluded both metrics.

```text
FROZEN_METRIC_COUNT = 11
PILOT_OBSERVED_METRIC_COUNT = 9
MISSING_METRIC_IDENTITIES = Short Term Debt; Long Term Debt
METRIC_COVERAGE_CLASSIFICATION = SEMANTIC_MAPPING_MISMATCH_ARCHITECTURE_BLOCKER
AQ_ALIASES_ADDED = NO
DIMENSION_BEARING_EVIDENCE_COUNT = 0
DIMENSION_PATH_EXERCISED = NO
DIMENSION_FOLLOWUP_REQUIRED = YES
```

This is not ordinary sample missingness. The next correction must reconcile
the frozen vocabulary with upstream canonical authority without creating an
ad hoc AQ alias table. The pilot also selected only non-dimensioned consolidated
facts; schema support alone does not prove the dimension execution path.

## Period semantics and session projection gate

The effective-session, containment, CIK isolation, metric isolation, and
backward-as-of mechanics pass. The semantic stream does not. Every one of the
96 events uses `period_class = STANDARD`, while `project_events_asof()` groups
only by CIK, metric, and that period class.

For example, AAPL CIK `0000320193` places 10-Q Revenue `58,010,000,000` from
accession `0001193125-15-153166` and 10-K Revenue `233,715,000,000` from
accession `0001193125-15-356351` in the same stream. The event retains
`report_period_end`, but that field does not participate in grouping. Annual
and quarterly flow values are therefore treated as interchangeable latest
values.

```text
AMENDMENT_TEMPORAL_AUDIT = PASS
SESSION_PROJECTION_POLICY_AUDIT = BLOCKED_INCOMPATIBLE_REPORT_PERIOD_SEMANTICS
EARLY_VISIBILITY_COUNT = 0
CROSS_CIK_CONTAMINATION_COUNT = 0
MEMBERSHIP_ALIGNMENT_FAILURE_COUNT = 0
```

The next correction must freeze a non-performance-derived period semantic for
instant and duration facts and prove that incompatible annual/quarterly flows
cannot share an as-of stream. No full build or pilot merge is authorized while
this remains unresolved.

## Numeric, Qlib, and reproducibility closeout

Authoritative evidence and admitted events retain canonical decimal strings;
Parquet reload preserves them exactly and evidence identity never depends on a
binary float. Conversion to numeric values in the Qlib feature table is a
model-consumption representation, not evidence authority.

```text
AUTHORITATIVE_NUMERIC_EXACTNESS = PASS
QLIB_STATIC_DATA_LOADER = PASS
QLIB_DATAHANDLERLP = PASS
QLIB_DATASETH = PASS
QLIB_ROWS = 10212
QLIB_FEATURE_COLUMNS = 11
QLIB_TRAIN_ROWS = 7182
QLIB_VALID_ROWS = 3030
QLIB_HANDOFF_CLOSEOUT = PASS
PILOT_REPRODUCIBILITY_CLOSEOUT = PASS
DVC_STATUS = UP_TO_DATE
```

No model, prediction, backtest, historical TEST access, or sealed-OOS access
occurred.

## Gate decision and next task

```text
PILOT_MERGE_READY = NO
FULL_BUILD_AUTHORIZED = NO
FULL_BUILD_GATE_CLASSIFICATION = FULL_BUILD_BLOCKED_SEMANTIC_POLICY
ADDITIONAL_GATE = FULL_UNIVERSE_IDENTITY_ACCOUNTING_REQUIRED
CURRENT_DEVELOPMENT_NEXT = P5_HYBRID_DATASET_PILOT_SEMANTIC_POLICY_CORRECTION_001
```

The semantic correction must remain bounded to vocabulary authority, report-
period classification, incompatible-flow isolation, and one dimension-path
fixture. After it passes and the pilot becomes merge-ready, the still-required
full-universe task is
`P5_FULL_UNIVERSE_EPISODE_SEC_CIK_BINDING_COVERAGE_001`. Neither task may
start the 832-episode historical build.

## Private evidence

```text
PRIVATE_REPORT = D:/AQ_DATA/P5/hybrid-dataset-pilot-closeout-and-full-build-gate-001/closeout_summary.json
PRIVATE_REPORT_SHA256 = 87c67888baa5fe2a6ff807840fa5258d73e504a76e72a644b3716fa612341351
```
