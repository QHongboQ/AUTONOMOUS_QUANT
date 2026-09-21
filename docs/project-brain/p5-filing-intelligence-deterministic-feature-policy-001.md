# P5 filing-intelligence deterministic feature policy 001

## Authority and result

PR #69 squash-merged the EdgarTools-native filing-intelligence capability
authority into main at
`3503bf11125164b19427fde494eac6c7a0830dfb`. This preregistration selects five
small, deterministic, accession-bound P5 V1 filing features. EdgarTools 5.58.0
remains the whole upstream owner for filing metadata, typed filing objects,
documents, sections, notes, attachments, exhibits, and search. AQ owns only
feature eligibility, exact scalar semantics, PIT availability, missingness,
and immutable evidence identity.

No calculator, transform, parser, pipeline, model, or factor implementation is
added by this task.

```text
CAPABILITY = deterministic filing-derived P5 feature policy
UPSTREAM_OWNER = EdgarTools for filing/document/note/event content access
OWNERSHIP_MODE_EDGARTOOLS = UPSTREAM_WHOLE
OWNERSHIP_MODE_AQ_FEATURE_SEMANTICS = AQ_OWNED_THIN_DOMAIN_POLICY
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = POLICY_ONLY
CUSTOM_ENGINE_REQUIRED = NO
PRIOR_MAIN = 99e5eba56ec5d401f8dc6fbc82e8cc0e2a5dadb0
FILING_INTELLIGENCE_AUTHORITY_PR = 69
FILING_INTELLIGENCE_AUTHORITY_MERGED_AT_UTC = 2026-09-20T07:37:53Z
MERGED_FILING_INTELLIGENCE_MAIN_SHA = 3503bf11125164b19427fde494eac6c7a0830dfb
SEC_DATA_REQUEST_COUNT = 0
```

## Candidate matrix

Every audited candidate has exactly one disposition. `DEFER_P6` means the
candidate is outside P5; it is not authorized for implementation or testing by
this policy.

| # | Candidate | Disposition | Reason |
|---:|---|---|---|
| 1 | `filing_lag_days` | `SELECT_P5_V1` | Exact acceptance date minus report-period end adds timeliness information without restating an accounting value. |
| 2 | `filing_hour` | `REJECT_UNSTABLE_SEMANTICS` | Raw hour creates timezone/DST/cyclical encoding variants; the exact XNYS after-close flag is the bounded alternative. |
| 3 | `accepted_after_market_close` | `SELECT_P5_V1` | Exact acceptance timestamp and the existing XNYS calendar define it without a new timing engine. |
| 4 | `accepted_pre_market` | `REJECT_REDUNDANT` | Existing first-available-session policy already captures whether pre-open information is eligible for that session. |
| 5 | `is_amendment` | `SELECT_P5_V1` | The filed form suffix is exact, cheap, and economically interpretable as a revised filing vintage. |
| 6 | `days_since_original_accession` | `REJECT_UPSTREAM_NOT_DETERMINISTIC_ENOUGH` | An exact original/amendment relationship is not proven uniformly for the authorized historical surface. |
| 7 | `form_10k_event` | `REJECT_REDUNDANT` | Form and annual period class are already retained as evidence metadata. |
| 8 | `form_10q_event` | `REJECT_REDUNDANT` | Form and interim period class are already retained as evidence metadata. |
| 9 | `form_20f_event` | `REJECT_REDUNDANT` | Form and annual period class are already retained as evidence metadata. |
| 10 | `form_6k_event` | `REJECT_HIGH_MULTIPLE_TESTING_COST` | A form one-hot family is not admitted merely to expand the feature set. |
| 11 | `form_8k_event` | `REJECT_HIGH_MULTIPLE_TESTING_COST` | Event content structure is represented more narrowly by the selected native exhibit features. |
| 12 | `transition_filing_event` | `REJECT_HIGH_MULTIPLE_TESTING_COST` | Sparse one-hot form variants would add a low-support hypothesis. |
| 13 | `earnings_release_present` | `REJECT_UPSTREAM_NOT_DETERMINISTIC_ENOUGH` | Native press-release selection does not by itself prove that an exhibit is specifically an earnings release. |
| 14 | `press_release_exhibit_present` | `SELECT_P5_V1` | Native typed `press_releases` selection gives an exact structural observation without reading semantics. |
| 15 | `authorized_exhibit_count` | `SELECT_P5_V1` | Native typed exhibit inventory provides a deterministic, cheap structural count. |
| 16 | `document_length` | `REJECT_UNSTABLE_SEMANTICS` | Filing format, inline XBRL boilerplate, and parser-version rendering can dominate length. |
| 17 | `mda_present` | `REJECT_REDUNDANT` | For applicable periodic forms this is primarily document completeness, not a distinct V1 hypothesis. |
| 18 | `risk_factors_present` | `REJECT_REDUNDANT` | For applicable forms this is primarily document completeness. |
| 19 | `business_section_present` | `REJECT_REDUNDANT` | For applicable annual forms this is primarily document completeness. |
| 20 | `mda_length` | `REJECT_UNSTABLE_SEMANTICS` | Layout and parser rendering confound a raw character-count interpretation. |
| 21 | `risk_factors_length` | `REJECT_UNSTABLE_SEMANTICS` | Layout and parser rendering confound a raw character-count interpretation. |
| 22 | `note_count` | `REJECT_UNSTABLE_SEMANTICS` | XBRL presentation roles and issuer taxonomy design can change the count without an economic change. |
| 23 | `note_table_count` | `REJECT_UNSTABLE_SEMANTICS` | Presentation-role granularity can change the count without an economic change. |
| 24 | `debt_note_present` | `REJECT_REDUNDANT` | Existing short- and long-term debt metrics already provide the admitted V1 accounting signal. |
| 25 | `lease_note_present` | `REJECT_UPSTREAM_NOT_DETERMINISTIC_ENOUGH` | Historical note-title conventions are not proven uniform enough for an exact title-only feature. |
| 26 | `revenue_note_present` | `REJECT_REDUNDANT` | Revenue is already an admitted structured fundamental metric. |
| 27 | `contingency_note_present` | `REJECT_UPSTREAM_NOT_DETERMINISTIC_ENOUGH` | Historical note-title conventions are not proven uniform enough for an exact title-only feature. |
| 28 | `semantic_mda_change` | `DEFER_P6` | Requires semantic/NLP comparison. |
| 29 | `semantic_risk_factor_change` | `DEFER_P6` | Requires semantic/NLP comparison. |
| 30 | `filing_sentiment` | `DEFER_P6` | Sentiment modeling belongs to P6. |
| 31 | `document_embedding_similarity` | `DEFER_P6` | Embedding generation and similarity belong to P6. |
| 32 | `llm_summary_or_topics` | `DEFER_P6` | LLM extraction/topic modeling belongs to P6. |
| 33 | `earnings_call_nlp` | `DEFER_P6` | Earnings-call intelligence belongs to P6 and is not a filing-structure feature. |

Reconciliation:

```text
CANDIDATE_FEATURE_COUNT = 33
SELECTED_P5_V1_FEATURE_COUNT = 5
DEFERRED_P6_FEATURE_COUNT = 6
REJECTED_FEATURE_COUNT = 22
5 + 6 + 22 = 33
```

## Frozen P5 V1 feature policy

All observations are accession-bound. They are not permitted to appear before
the existing acceptance-time-to-XNYS-effective-session policy makes the source
filing available. The materialization POC must emit event observations at the
first available session; no forward-fill, persistence horizon, decay rule,
threshold, or alternate variant is authorized by this preregistration.

### `p5_filing_lag_days_v1`

- **Applicability:** filings with a verified SEC acceptance datetime and an
  exact report-period end date.
- **Formula:** calendar date of the SEC acceptance timestamp in
  `America/New_York` minus the report-period end date, in whole calendar days.
- **Value:** non-negative integer. A negative result is invalid and becomes
  missing with an explicit validation status.
- **Native source:** filing metadata exposed by EdgarTools.
- **Economic rationale:** reporting delay is a direct measure of information
  timeliness and does not duplicate any admitted accounting value.
- **Expected direction:** `DIRECTION_UNSPECIFIED`.
- **Normalization:** none; retain the exact raw integer. No clipping,
  winsorization, log variant, or tuned threshold is authorized.

### `p5_accepted_after_market_close_v1`

- **Applicability:** an acceptance whose New York calendar date is an XNYS
  session with an exact official close.
- **Formula:** `1` iff the verified SEC acceptance timestamp is strictly later
  than that session's official XNYS close; otherwise `0`.
- **Non-session acceptance date:** missing/not-applicable, not zero.
- **Native source:** EdgarTools acceptance datetime plus the already-selected
  `exchange_calendars` XNYS schedule.
- **Economic rationale:** after-close releases have a different immediately
  tradable information boundary, already enforced by the PIT session policy.
- **Expected direction:** `DIRECTION_UNSPECIFIED`.
- **Normalization:** none; exact binary value only.

### `p5_is_amendment_v1`

- **Applicability:** any filing with a verified filed form.
- **Formula:** `1` iff the exact form ends with `/A`; otherwise `0`.
- **Native source:** EdgarTools filing metadata.
- **Economic rationale:** an amendment is a separate revised-information
  vintage and may reflect reporting or disclosure correction risk.
- **Expected direction:** `DIRECTION_UNSPECIFIED`.
- **Normalization:** none; exact binary value only.

### `p5_press_release_exhibit_present_v1`

- **Applicability:** native 8-K/8-K/A or 6-K/6-K/A typed reports with a loaded
  attachment inventory.
- **Formula:** `1` iff the native typed report `press_releases` collection has
  at least one member; otherwise `0`.
- **Native source:** EdgarTools typed report and native attachment selection.
- **Economic rationale:** a furnished press release is a deterministic event
  structure distinct from periodic accounting metrics.
- **Expected direction:** `DIRECTION_UNSPECIFIED`.
- **Normalization:** none; exact binary value only.

### `p5_authorized_exhibit_count_v1`

- **Applicability:** native 8-K/8-K/A or 6-K/6-K/A typed reports with a loaded
  attachment inventory.
- **Formula:** exact length of the typed report's native content-exhibit
  collection after EdgarTools' native exclusions of the primary filing,
  graphics, and XBRL infrastructure where the typed interface applies.
- **Native source:** `CurrentReport.get_exhibits` or `SixK.exhibits`.
- **Economic rationale:** exhibit count measures event-package structure
  without interpreting or summarizing content.
- **Expected direction:** `DIRECTION_UNSPECIFIED`.
- **Normalization:** none; retain the exact non-negative integer. No cap or
  threshold is authorized.

## PIT and evidence contract

Every future materialized feature observation must carry:

```text
feature_id
source_accession
cik
form
sec_acceptance_datetime
first_available_xnys_session
native_edgartools_object_identity
exact_scalar_value
missingness_status
amendment_status
source_availability_status
edgartools_runtime_identity
immutable_evidence_identity
```

The source accession and CIK are mandatory. The first available session is
the first XNYS session whose open is strictly after the acceptance timestamp,
as computed by the already-frozen effective-session policy. There is no early
visibility and no current-ticker inference.

Amendments are separate immutable accessions. Each amendment's features become
available only after its own acceptance time. No original observation is
rewritten and no amendment value is projected backward.

Missingness is explicit:

| State | Meaning | Zero allowed? |
|---|---|---|
| `NOT_APPLICABLE_FORM` | Feature does not apply to that filing family. | No |
| `NATIVE_OBJECT_UNAVAILABLE` | Required typed/native object was unavailable. | No |
| `SOURCE_UNAVAILABLE` | Required source asset was unavailable. | No |
| `REQUIRED_METADATA_MISSING` | Acceptance, report period, form, or CIK needed by the formula is missing. | No |
| `VALIDATED_ABSENCE` | Applicable native inventory loaded and the selected item was absent. | Yes, only for the two exact binary/count exhibit features. |
| `INVALID_VALUE` | Native values violate the frozen scalar contract. | No |

No missing state is coerced to zero merely to increase completeness.

## P5/P6 boundary and non-ownership

P5 V1 contains no sentiment, embedding, semantic change, LLM summary, topic,
RAG, or earnings-call feature. Those remain P6 candidates and are not
authorized by this document.

```text
LLM_FEATURE_COUNT = 0
EMBEDDING_FEATURE_COUNT = 0
CUSTOM_PARSER_FEATURE_COUNT = 0
NEW_FEATURE_PRODUCTION_LOC = 0
AQ_HTML_PARSER = NO
AQ_DOCUMENT_PARSER = NO
AQ_NOTE_PARSER = NO
AQ_GENERIC_NLP_PIPELINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

The concurrent historical build remained in its existing process and
worktree. This task did not read or mutate its private checkpoints, data,
cache, manifests, or output.

```text
HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
HISTORICAL_BUILD_INTERFERENCE = NO
SEC_DATA_REQUEST_COUNT = 0
```

## Decision and next

```text
P5_FILING_FEATURE_POLICY_SELECTED = YES
SELECTED_P5_V1_FEATURE_COUNT = 5
TEST_RESULT = PASS
RUFF = PASS
DIFF_CHECK = PASS
PARALLEL_DEVELOPMENT_NEXT = P5_FILING_INTELLIGENCE_SELECTED_FEATURE_THIN_MATERIALIZATION_POC_001
```

The next task may materialize only these five exact policies from native
EdgarTools objects. It may not add parsing, NLP, parameter search, threshold
tuning, model training, or backtesting.
