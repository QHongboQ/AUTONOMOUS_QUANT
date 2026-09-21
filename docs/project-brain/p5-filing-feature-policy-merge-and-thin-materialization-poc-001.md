# P5 filing-feature policy merge and thin materialization POC 001

## Authority and ownership

PR #70 squash-merged the five-feature preregistration into main at
`f2b2c20977f607062f0d334f79441ccfa899502f`. The implementation POC then
started from that exact merge on the isolated branch
`agent/p5-filing-intelligence-selected-feature-thin-materialization-poc-001`.

EdgarTools 5.58.0 remains the upstream owner of filing metadata, typed filing
objects, attachments, press-release selection, and exhibits.
`exchange_calendars` remains the XNYS schedule owner, and the existing
`aq_hybrid_fundamentals.effective_session` function remains the PIT
availability owner. AQ adds only the five frozen scalar policies, explicit
missingness, and immutable observation identity.

```text
CAPABILITY = materialization of five preregistered deterministic filing features
UPSTREAM_OWNER = EDGARTOOLS + EXCHANGE_CALENDARS
OWNERSHIP_MODE = UPSTREAM_WHOLE / UPSTREAM_LEAF + AQ_OWNED_THIN_DOMAIN_POLICY
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = THIN_DOMAIN_CONTRACT_PLUS_PURE_PROJECTION_ONLY
CUSTOM_ENGINE_REQUIRED = NO
FILING_FEATURE_POLICY_MERGE_PR = 70
FILING_FEATURE_POLICY_MERGE_SHA = f2b2c20977f607062f0d334f79441ccfa899502f
SEC_DATA_REQUEST_COUNT = 0
```

## Contract audit

No existing observation contract fits without semantic distortion:

- `FundamentalEvidenceV1` is restricted to accession-bound numeric XBRL
  facts with taxonomy, unit, context, and source-document hash semantics;
- P1 `SnapshotObservationV1` is an index-membership snapshot;
- P4 `MetricObservationStreamV1` is a fixed RANK_IC monitoring stream;
- the Qlib handoff contract describes universe artifacts, not observations.

The POC therefore adds exactly one narrow immutable contract,
`FilingFeatureObservationV1`. It retains the frozen required fields and uses
RFC 8785 plus SHA-256 over every validated non-ID field. It is not a feature
registry, generic event model, transform graph, factor hierarchy, provider
abstraction, or plugin system. It is deliberately separate from
`FundamentalEvidenceV1`. Before merge, semantic closeout corrected the native
class field name to `native_edgartools_object_type`; its value is the exact
installed `module.qualname`, not a specific object identity.

```text
FEATURE_CONTRACT_REUSED_EXISTING = NO
NEW_NARROW_FEATURE_CONTRACT_CREATED = YES
NEW_NARROW_FEATURE_CONTRACT_COUNT = 1
```

## Exact materialized surface

`materialize_selected_filing_features` always returns exactly these five IDs
in the frozen order:

1. `p5_filing_lag_days_v1`
2. `p5_accepted_after_market_close_v1`
3. `p5_is_amendment_v1`
4. `p5_press_release_exhibit_present_v1`
5. `p5_authorized_exhibit_count_v1`

Filing lag is the New York acceptance calendar date minus report-period end;
negative values become `INVALID_VALUE`. After-close uses the official XNYS
close and a strict greater-than comparison. A non-session acceptance uses the
narrow `NOT_APPLICABLE_SESSION_DATE` state and no scalar; filing-family
inapplicability remains `NOT_APPLICABLE_FORM`. Amendment status uses only the
exact `/A` form suffix. Event-form features read only native `CurrentReport`
or `SixK` interfaces; empty loaded inventories are zero-valued
`VALIDATED_ABSENCE`, whereas an absent native object remains missing.

Every observation uses the existing first-XNYS-open-strictly-after-acceptance
policy. Original and amended accessions remain separate immutable
observations. No value is clipped, logged, winsorized, forward-filled, or
inferred from text.

## Offline proof

The focused suite covers all 16 required A-P cases: positive and invalid lag,
after-close/before-close/non-session acceptance, ordinary and amended forms,
native 8-K and 6-K press releases, validated absence, exact native exhibit
count, non-applicable forms, missing report period, unavailable source,
identity stability, and identity sensitivity. Additional checks cover a
missing event-form native object, exact immutable contract shape, the exact
five-ID inventory, no early visibility, and absence of network/parser/generic
engine code.

```text
SELECTED_FEATURE_POC_CASE_COUNT = 16
SELECTED_FEATURE_POC_CASES = PASS
FOCUSED_TEST_RESULT = 21/21 PASS
FULL_P5_TEST_RESULT = 151/151 PASS
EARLY_VISIBILITY_COUNT = 0
MATERIALIZED_FEATURE_ID_COUNT = 5
LLM_CALL_COUNT = 0
EMBEDDING_COUNT = 0
SENTIMENT_FEATURE_COUNT = 0
SEMANTIC_FEATURE_COUNT = 0
RAG = NO
```

No SEC endpoint was contacted. All evidence came from local native-object
fixtures and the installed EdgarTools/exchange-calendars runtimes.

## Thinness and non-ownership

Production LOC is reported as nonblank, non-comment physical Python lines.
The contract count includes the bounded package export surface.

```text
NEW_FEATURE_MATERIALIZATION_PRODUCTION_LOC = 217
NEW_FEATURE_CONTRACT_PRODUCTION_LOC = 174
TOTAL_NEW_PRODUCTION_LOC = 391
AQ_FEATURE_ENGINE = NO
AQ_FACTOR_ENGINE = NO
AQ_FILING_PARSER = NO
AQ_DOCUMENT_PARSER = NO
AQ_EXHIBIT_CLASSIFIER = NO
AQ_MARKET_HOURS_ENGINE = NO
AQ_GENERIC_ETL = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

No historical feature build, model training, prediction, backtest, or sealed
OOS access occurred. The independently running historical fundamentals build
remained in PID 403 and its worktree, checkpoints, cache, evidence, events,
and manifests were not mutated.

```text
HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
HISTORICAL_BUILD_INTERFERENCE = NO
P5_FILING_FEATURE_THIN_MATERIALIZATION_POC = PASS
V1_NEVER_MERGED_OR_USED_FOR_PERFORMANCE = YES
CONTRACT_VERSION_DECISION = V1_CORRECTED_IN_PLACE_BEFORE_FIRST_MERGE
P2_V2_SEALED_OOS_ACCESSED = NO
PARALLEL_DEVELOPMENT_NEXT = P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_DESIGN_AND_ABLATION_PROTOCOL_001
```
