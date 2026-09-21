# P5 filing-feature POC semantic closeout and merge 001

## Scope

The unmerged five-feature POC received exactly two pre-analysis contract
corrections. No feature formula, feature ID, upstream owner, PIT rule, or
materialization scope changed.

```text
AUTHORITATIVE_MAIN = f2b2c20977f607062f0d334f79441ccfa899502f
PRIOR_SOURCE_HEAD = bf0c7a4f7325d92585c94176f87972b1df15debe
CAPABILITY = five deterministic filing-feature observations
UPSTREAM_OWNER = EDGARTOOLS + EXCHANGE_CALENDARS
OWNERSHIP_MODE = UPSTREAM_SOURCE_SEMANTICS + AQ_THIN_IMMUTABLE_FEATURE_CONTRACT
CUSTOM_ENGINE_REQUIRED = NO
```

## Corrected semantics

`p5_accepted_after_market_close_v1` now uses
`NOT_APPLICABLE_SESSION_DATE` only when the New York acceptance calendar date
is not an XNYS session. Non-8-K/6-K filing-family applicability continues to
use `NOT_APPLICABLE_FORM`; the two meanings are no longer overloaded.

The field formerly named `native_edgartools_object_identity` is now
`native_edgartools_object_type`. Its value remains the exact installed Python
class identity, `module.qualname`. No source identity system or source hash was
added.

```text
WEEKEND_ACCEPTANCE_MISSINGNESS = NOT_APPLICABLE_SESSION_DATE
NON_EVENT_FORM_EXHIBIT_MISSINGNESS = NOT_APPLICABLE_FORM
MISLEADING_NATIVE_OBJECT_IDENTITY_FIELD = NO
NATIVE_OBJECT_FIELD_NAME = native_edgartools_object_type
NATIVE_EDGARTOOLS_OBJECT_TYPE_SEMANTICS = EXACT_CLASS_TYPE
```

## Contract version decision

The POC V1 had never been merged, historically materialized, or used for
training, prediction, ranking, IC inspection, or backtesting. Correcting it in
place before first merge is the smallest truthful path. The changed
authoritative field name and the new missingness value participate in RFC 8785
+ SHA-256 identity, so corrected observations deterministically receive new
evidence IDs. No stale evidence IDs or migration alias survive.

```text
V1_NEVER_MERGED_OR_USED_FOR_PERFORMANCE = YES
CONTRACT_VERSION_DECISION = V1_CORRECTED_IN_PLACE_BEFORE_FIRST_MERGE
STALE_EVIDENCE_IDS_PRESERVED = NO
```

## Validation and thinness

All original cases remain. Saturday and Sunday acceptances both prove the new
session-date missingness; ordinary XNYS before/after-close values remain zero
and one; non-event exhibit features retain form missingness; class-type naming
and deterministic evidence-ID behavior remain explicit.

Production LOC is the same nonblank, non-comment physical-Python measure used
by the POC report.

```text
MATERIALIZED_FEATURE_ID_COUNT = 5
FOCUSED_TEST_RESULT = 21/21 PASS
FULL_TEST_RESULT = 151/151 PASS
SEC_DATA_REQUEST_COUNT = 0
PRIOR_TOTAL_NEW_PRODUCTION_LOC = 390
FINAL_TOTAL_NEW_PRODUCTION_LOC = 391
LOC_DELTA = +1
AQ_FEATURE_ENGINE = NO
AQ_FACTOR_ENGINE = NO
AQ_GENERIC_ETL = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

The independent historical fundamentals build remained in its original
process. Its worktree, PID, cache, checkpoints, evidence, events, and manifests
were not changed.

```text
HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
HISTORICAL_BUILD_INTERFERENCE = NO
P2_V2_SEALED_OOS_ACCESSED = NO
PARALLEL_DEVELOPMENT_NEXT = P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_DESIGN_AND_ABLATION_PROTOCOL_001
```
