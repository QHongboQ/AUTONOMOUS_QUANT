# P5 EdgarTools native filing intelligence capability activation 001

## Result

PR #68 squash-merged the previously proven native live-path activation into
main at `99e5eba56ec5d401f8dc6fbc82e8cc0e2a5dadb0`. From that exact merged
baseline, the installed EdgarTools 5.58.0 runtime was exercised offline with
frozen HTML, mock `Filing` objects, native typed reports, native `Document`,
native `Note`/`Notes`, and native `Attachment`/`Attachments` objects.

EdgarTools directly owns parsing, typed filing objects, item/section access,
document text/markdown/search, notes, tables, attachments, exhibits, and press
release selection. AQ needs no filing-intelligence production wrapper. Future
AQ code may only define which native observation is feature-eligible, bind it
to accession/acceptance-time identity, enforce PIT availability, and seal
immutable evidence identity.

```text
CAPABILITY = SEC filing narrative / document / disclosure intelligence access
UPSTREAM_OWNER = EdgarTools
OWNERSHIP_MODE = UPSTREAM_WHOLE
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = THIN_ONLY
CUSTOM_ENGINE_REQUIRED = NO
EDGARTOOLS_VERSION = 5.58.0
PRIOR_MAIN = 5ad77c006a25f5fcd0739d0f355824f368368e11
NATIVE_LIVE_PR = 68
NATIVE_LIVE_MERGED_AT_UTC = 2026-09-20T07:19:44Z
MERGED_NATIVE_LIVE_MAIN_SHA = 99e5eba56ec5d401f8dc6fbc82e8cc0e2a5dadb0
SEC_DATA_REQUEST_COUNT = 0
```

## Native interface inventory

The following 20 filing-intelligence surfaces are native EdgarTools
capabilities and require no AQ mirror object.

| # | Capability | Native surface | Classification |
|---:|---|---|---|
| 1 | 10-K typed report | `TenK` | `EDGARTOOLS_NATIVE_DIRECT` |
| 2 | 10-Q typed report | `TenQ` | `EDGARTOOLS_NATIVE_DIRECT` |
| 3 | 20-F typed report | `TwentyF` | `EDGARTOOLS_NATIVE_DIRECT` |
| 4 | 40-F typed report | `FortyF` | `EDGARTOOLS_NATIVE_DIRECT` |
| 5 | 8-K typed report | `CurrentReport` / `EightK` | `EDGARTOOLS_NATIVE_DIRECT` |
| 6 | 6-K typed report | `SixK` | `EDGARTOOLS_NATIVE_DIRECT` |
| 7 | Filing document | `Filing.document` | `EDGARTOOLS_NATIVE_DIRECT` |
| 8 | Filing text | `Filing.text` | `EDGARTOOLS_NATIVE_DIRECT` |
| 9 | Filing markdown | `Filing.markdown`, `Document.to_markdown` | `EDGARTOOLS_NATIVE_DIRECT` |
| 10 | Filing parsing | `Filing.parse`, `parse_html` | `EDGARTOOLS_NATIVE_DIRECT` |
| 11 | Filing search/grep | `Filing.search`, `Filing.grep`, `Document.search` | `EDGARTOOLS_NATIVE_DIRECT` |
| 12 | SEC section access | `Document.get_sec_section` | `EDGARTOOLS_NATIVE_DIRECT` |
| 13 | Typed item access | `items`, `get`, typed section properties | `EDGARTOOLS_NATIVE_DIRECT` |
| 14 | Financial statement notes | `XBRL.notes`, `Notes` | `EDGARTOOLS_NATIVE_DIRECT` |
| 15 | XBRL disclosures | `XBRL.disclosures` | `EDGARTOOLS_NATIVE_DIRECT` |
| 16 | Note narrative/search | `Note.text`, `Notes.search`, `Notes.grep` | `EDGARTOOLS_NATIVE_DIRECT` |
| 17 | Note tables/policies/details | `Note.tables`, `policies`, `details` | `EDGARTOOLS_NATIVE_DIRECT` |
| 18 | Attachments | `Attachment`, `Attachments` | `EDGARTOOLS_NATIVE_DIRECT` |
| 19 | Exhibits | typed report exhibit interfaces | `EDGARTOOLS_NATIVE_DIRECT` |
| 20 | Press releases / earnings exhibits | typed report `press_releases` | `EDGARTOOLS_NATIVE_DIRECT` |

## Offline native proofs

All proofs used local strings or in-memory native objects. The 6-K exhibit
content method was replaced in the fixture with local HTML specifically to
ensure the native `SixK` renderer ran without transport. No SEC method or HTTP
request was executed.

| # | Representative case | Result | Evidence |
|---:|---|---|---|
| 1 | 10-K MD&A | `PASS` | `TenK.management_discussion` returned frozen Item 7 text. |
| 2 | 10-K Risk Factors | `PASS` | `TenK.risk_factors` returned frozen Item 1A text. |
| 3 | 10-K Business | `PASS` | `TenK.business` returned frozen Item 1 text. |
| 4 | 10-Q narrative | `PASS` | `TenQ.get("Item 2")` returned frozen quarterly MD&A. |
| 5 | 8-K items/exhibits | `PASS` | `CurrentReport.items`, `get`, and `get_exhibits` used native interfaces. |
| 6 | 6-K text/exhibits | `PASS` | `SixK.text` rendered a local EX-99.1 attachment and `SixK.exhibits` selected it. |
| 7 | Financial statement note | `PASS` | Native `Note.text` exposed frozen XBRL-note narrative. |
| 8 | Note table | `PASS` | Native `Note.tables` and `Notes.with_tables` retained the local statement. |
| 9 | Debt note search | `PASS` | `Notes.search` and `Notes.grep` found native note title/content. |
| 10 | Lease note search | `PASS` | `Notes.search("leases")` returned the native note. |
| 11 | Revenue note search | `PASS` | `Notes.search("revenue")` returned the native note. |
| 12 | Filing markdown | `PASS` | `Document.to_markdown` rendered frozen 10-K content. |
| 13 | Document search/grep | `PASS_WITH_INTERFACE_ONLY_SUBSURFACE` | `Document.search` ran on frozen text; `Filing.grep` is installed but no base `Filing` fixture was constructed. |
| 14 | Attachments | `PASS` | Native `Attachment` and `Attachments` selected EX-99.1. |
| 15 | Press release/earnings exhibit | `PASS` | Native `SixK.press_releases` selected the local earnings-release attachment. |

The following interfaces are present in the exact installed runtime but lack
an available representative local content fixture in this task. They are not
reported as failed and are not represented as content-proven:

- `TwentyF` and `FortyF` narrative properties;
- parsed `XBRL.notes` and `XBRL.disclosures` from a frozen XBRL filing;
- anchor-dependent positive output from `Document.get_sec_section` (the local
  synthetic HTML has no SEC anchor navigation).

Their proof classification is:

```text
INTERFACE_PRESENT_FIXTURE_NOT_AVAILABLE
```

## Future feature ownership matrix

Native content access is distinct from AQ feature eligibility. A feature may
require thin AQ policy even though its parser and content object are entirely
native.

| Feature | Classification | AQ's only allowed future scope |
|---|---|---|
| MD&A | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Preregister section/form eligibility, accession identity, PIT timing, and immutable evidence hash. |
| Risk Factors | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Same bounded feature policy; consume native section text. |
| Business | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Same bounded feature policy; consume native section text. |
| 8-K narrative | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Select authorized native items/exhibits by explicit policy. |
| 6-K narrative | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Select authorized native report/exhibit content by explicit policy. |
| Debt disclosures | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Select admissible native notes/tables; no parsing. |
| Lease disclosures | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Select admissible native notes/tables; no parsing. |
| Revenue disclosures | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Select admissible native notes/tables; no parsing. |
| Contingencies | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Select admissible native notes/tables; no parsing. |
| Earnings releases | `EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY` | Select authorized native press-release exhibits and PIT identity. |
| Exhibits | `EDGARTOOLS_NATIVE_DIRECT` | Consume native exhibit objects directly. |
| Financial statement notes | `EDGARTOOLS_NATIVE_DIRECT` | Consume native `Note`/`Notes` objects directly. |

Across the 20 native-interface rows and 12 feature-ownership rows:

```text
FILING_INTELLIGENCE_CAPABILITY_COUNT_AUDITED = 32
EDGARTOOLS_NATIVE_DIRECT_COUNT = 22
EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY_COUNT = 10
TRUE_UPSTREAM_GAP_COUNT = 0
22 + 10 + 0 = 32
```

## Non-ownership and safety

No production module was added. The focused tests are evidence that AQ can
consume upstream objects directly; they do not implement an alternate parser
or runtime facade.

```text
NEW_FILING_INTELLIGENCE_PRODUCTION_LOC = 0
AQ_HTML_PARSER = NO
AQ_DOCUMENT_PARSER = NO
AQ_SECTION_EXTRACTOR = NO
AQ_NOTE_PARSER = NO
AQ_TABLE_PARSER = NO
AQ_FILING_SEARCH_ENGINE = NO
AQ_XBRL_ENGINE = NO
AQ_GENERIC_NLP_PIPELINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
LLM_SUMMARIZATION = NO
EMBEDDINGS = NO
RAG = NO
MODEL_TRAINING = NO
BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

The independent historical build remained live in its existing process and
worktree. This task did not read or mutate its private root, cache,
checkpoints, evidence, events, or manifests.

```text
HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
HISTORICAL_BUILD_INTERFERENCE = NO
SEC_DATA_REQUEST_COUNT = 0
```

## Validation and next

```text
OFFLINE_NATIVE_PROOF_TESTS = 5/5 PASS
TEST_RESULT = 130/130 PASS
RUFF = PASS
DIFF_CHECK = PASS
PARALLEL_DEVELOPMENT_NEXT = P5_FILING_INTELLIGENCE_FEATURE_POLICY_SELECTION_001
```

The next task may preregister a small set of filing-derived features over
EdgarTools-native content. It may not create a filing, document, section,
note, table, search, XBRL, or generic NLP engine.
