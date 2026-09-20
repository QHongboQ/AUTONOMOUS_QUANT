# P5 EdgarTools capability authority merge and native live path offline activation 001

## Result

PR #67 merged the complete EdgarTools capability census into main by squash at
`5ad77c006a25f5fcd0739d0f355824f368368e11`. From that merged authority, an
isolated zero-network proof activated the callable boundary for one native
`CurrentFilings` page without creating a poller, scheduler, SEC client, feed
parser, filing parser, XBRL engine, or second materializer.

```text
PRIOR_MAIN = 3814bfe85aaa8f6d699f97e77b8ef32b141cf97c
CAPABILITY_AUTHORITY_PR = 67
CAPABILITY_AUTHORITY_MERGE_METHOD = SQUASH
MERGED_CAPABILITY_AUTHORITY_MAIN_SHA = 5ad77c006a25f5fcd0739d0f355824f368368e11
MERGED_AT_UTC = 2026-09-20T07:09:04Z
SEC_DATA_REQUEST_COUNT = 0
```

## Ownership and callable boundary

EdgarTools remains the whole upstream owner. AQ now exposes only one pure
single-page policy function, `plan_native_current_filings_page`. It consumes
the native `CurrentFilings.data` table already produced by EdgarTools and does
not fetch, refresh, parse, or paginate the feed.

```text
EdgarTools get_current_filings / CurrentFilings page
  -> plan_native_current_filings_page
       accepted-CIK membership
       exact-accession processed state
       frozen periodic/transition-form eligibility
       explicit source-unavailable accounting
  -> existing execute_accession_set
  -> existing process_exact_accession
  -> existing EdgarTools Filing / XBRL
  -> existing FundamentalEvidenceV1 materializer
  -> existing PIT/effective-session and seal policy
```

The historical `_process_accession` implementation was given the public,
specific name `process_exact_accession`; its processing logic was not copied.
`execute_accession_set` now calls that same function. A small fallback obtains
`Filing.period_of_report` from the native filing when the current feed row does
not contain report-period metadata. Historical rows continue to use their
already-frozen report period.

The live-page function accepts no URL, client, polling interval, retry policy,
or pagination state. A future mature scheduler may call EdgarTools and then
this boundary once per returned page/cycle. Scheduling is not implemented by
this task.

## Offline cases

The proof constructed an actual EdgarTools `CurrentFilings` instance over a
local PyArrow table; no SEC function was invoked.

| Case | Expected and observed result |
|---|---|
| unseen bound-CIK 10-Q | `ADMIT_EXISTING_ACCESSION_PROCESSOR` |
| same accession repeated | first admitted; second `SKIP_DUPLICATE_ACCESSION` |
| original 10-K plus later 10-K/A | two distinct accessions and immutable processing units |
| bound-CIK 10-KT | admitted through the existing four-form transition leaf |
| non-bound CIK 10-Q | `REJECT_NON_BOUND_CIK` before processing |
| known source-unavailable 10-Q | explicit `SOURCE_UNAVAILABLE_FOR_FINAL_PROVENANCE`; no processor call |
| native bound-CIK 8-K | retained in native page metadata but `SKIP_NON_PERIODIC_NATIVE_FILING` for structured fundamentals |

The selected rows were passed into `execute_accession_set` with a spy replacing
only `process_exact_accession`. The spy proved all and only selected accessions
reach the existing processor, once each, with zero network requests.

```text
NEW_ACCESSION_ADMITTED = YES
DUPLICATE_ACCESSION_REPROCESSED = NO
AMENDMENT_NEW_VINTAGE = YES
TRANSITION_FORM_NATIVE_PATH = PASS
NON_BOUND_CIK_REJECTED = YES
SOURCE_UNAVAILABLE_NO_FAKE_EVIDENCE = YES
NON_PERIODIC_NATIVE_FILING_NO_FALSE_FUNDAMENTAL_ADMISSION = YES
ACCESSION_IS_DEDUP_KEY = YES
EXISTING_ACCESSION_PROCESSOR_REUSED = YES
```

## Code budget and non-ownership

The activation adds 78 net production lines: 75 lines for the bounded
single-page policy/constants/export and three net lines to expose/reuse the
exact historical processor and resolve a missing native report period. Tests
and this authority document are not included in that production count.

```text
NEW_LIVE_PRODUCTION_LOC = 78_NET
AQ_SEC_CLIENT = NO
AQ_SEC_POLLER = NO
AQ_RSS_PARSER = NO
AQ_CURRENT_FILINGS_ENGINE = NO
AQ_FORM_ROUTER_ENGINE = NO
AQ_XBRL_ENGINE = NO
AQ_FINANCIAL_STATEMENT_ENGINE = NO
AQ_DOCUMENT_PARSER_ENGINE = NO
AQ_GENERIC_ETL = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Safety and state

The long-running historical build remained in its original process/worktree.
This task did not read or mutate its private root. The live interface is proven
offline but is not scheduled or operational.

```text
HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
HISTORICAL_BUILD_INTERFERENCE = NO
SEC_DATA_REQUEST_COUNT = 0
P5_LIVE_INCREMENTAL_INTERFACE_OFFLINE_POC = PASS
P5_LIVE_INCREMENTAL_PRODUCTION_ACTIVE = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

Validation:

```text
TEST_RESULT = 125/125 PASS
RUFF = PASS
DIFF_CHECK = PASS
SEC_DATA_REQUEST_COUNT = 0
```

## Next parallel development

```text
PARALLEL_DEVELOPMENT_NEXT = P5_EDGARTOOLS_NATIVE_FILING_INTELLIGENCE_CAPABILITY_ACTIVATION_001
```

That task may use native `Document`, `Notes`, MD&A, Risk Factors, and 8-K/6-K
narrative interfaces. It may not create custom document or filing parsers.
