# P5 EdgarTools complete capability census and native interface activation 001

## Decision

EdgarTools 5.58.0 is the whole upstream owner for SEC filing discovery,
issuer filing history, filing/document access, typed periodic and current
reports, XBRL, financial statements, notes, attachments, storage, and the
polling surface needed by future incremental ingestion. AQ retains only CIK
eligibility, accession processed/not-processed state, authorized fact policy,
PIT availability/effective-session policy, immutable evidence identity, and
bounded execution/seal policy.

No new runtime wrapper is activated by this task. The required production
interfaces are already native imports used directly by the historical path;
adding a cosmetic AQ facade would create a second owner. This report activates
the same direct-native ownership for the future live and narrative paths.

```text
CAPABILITY = SEC filing / financial statement / fundamental intelligence ingestion
UPSTREAM_OWNER = EdgarTools
OWNERSHIP_MODE = UPSTREAM_WHOLE
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = THIN_ONLY
CUSTOM_ENGINE_REQUIRED = NO
EDGARTOOLS_VERSION = 5.58.0
AUDITED_SOURCE_COMMIT = e23d04eba952e70310c0f62402f4c2523f9a44bf
SEC_DATA_REQUEST_COUNT = 0
```

## Isolation and evidence

The census ran from main `3814bfe85aaa8f6d699f97e77b8ef32b141cf97c`
in the isolated worktree
`D:\AUTONOMOUS_QUANT_P5_EDGARTOOLS_AUDIT`. The independent historical build
continued in its original worktree and process. This task did not read or
write its checkpoint, evidence, event, manifest, or cache roots.

Evidence was limited to:

- the installed 5.58.0 distribution under
  `/home/zhou/AQ_ENVS/p5-fundamental-intelligence`;
- the source identity already frozen in
  `10-data-system/fundamentals/upstream/runtime-authority.json`;
- import/signature/source inspection and existing offline AQ tests;
- official [current-filings documentation](https://edgartools.readthedocs.io/en/stable/guides/current-filings/),
  [financial-data documentation](https://edgartools.readthedocs.io/en/stable/guides/financial-data/),
  [XBRL API](https://edgartools.readthedocs.io/en/latest/api/xbrl/),
  [dimension handling](https://edgartools.readthedocs.io/en/latest/xbrl/concepts/dimension-handling/),
  and [multi-period analysis](https://edgartools.readthedocs.io/en/latest/xbrl/guides/multi-period-analysis/).

No `Company`, `Filing`, current-feed, archive, submissions, or facts method was
executed against SEC data.

## Native API inventory

The exact installed runtime exposes the following relevant surfaces.

- Live discovery: `get_current_filings`, `CurrentFilings.next`,
  `CurrentFilings.previous`, `iter_current_filings_pages`, and
  `get_all_current_filings`. The feed schema includes form, company, CIK,
  filing date, accession, and accepted timestamp.
- Issuer discovery: `Company`/`Entity`, `get_filings`, `latest`, `get_facts`,
  `get_financials`, `get_quarterly_financials`, and `EntityFacts` queries.
- Financials: `Financials`, `MultiFinancials`, `XBRLS.from_filings`,
  `XBRLS.get_statement`, standardized concepts, period selection, and stitched
  statements.
- XBRL: facts, contexts, units, axes/domains, dimensions, calculation,
  presentation and definition relationships, footnotes, statements,
  disclosures, notes, source attachment selection, and inline XBRL parsing.
- Typed reports: `TenK`, `TenQ`, `TwentyF`, `FortyF`, `SixK`, and
  `CurrentReport`/`EightK`. The 5.58.0 object registry does not map `10-KT` or
  `10-QT`, although its XBRL form classification explicitly recognizes both.
- Documents: `Filing.document`, `html`, `text`, `markdown`, `parse`, `grep`,
  `search`, `sections`, tables, attachments, exhibits, and primary documents.
- Notes: `XBRL.notes`, `XBRL.disclosures`, `Note`/`Notes`, narrative text/HTML,
  tables, policies, details, search/grep, markdown, and AI-oriented context.
- Storage: native throttled/retrying HTTP, response cache, local storage,
  network fallback control, filing/bulk download APIs, cache inspection and
  clearing, filing compression/decompression, and storage optimization.
- AI/tooling: document chunks, `prepare_for_llm`, `to_context`, native skills,
  and the installed `edgartools-mcp` console entry point.

## Capability crosswalk

`NATIVE_WITH_THIN_AQ_POLICY` below never means an AQ parser or engine. It means
that EdgarTools produces the native object and AQ applies only a bounded
project contract or policy decision.

| # | Capability | EdgarTools native API/object | Classification | AQ thin scope, current duplication, and evidence |
|---:|---|---|---|---|
| 1 | Current filing discovery | `get_current_filings` | EDGARTOOLS_NATIVE_DIRECT | Direct feed API; no AQ duplicate. |
| 2 | Current filing pagination | `CurrentFilings.next/previous`, `iter_current_filings_pages` | EDGARTOOLS_NATIVE_DIRECT | Native page state/refresh; no AQ duplicate. |
| 3 | Current form filtering | `get_current_filings(form=...)` | EDGARTOOLS_NATIVE_DIRECT | Native form parameter; no AQ router. |
| 4 | Current CIK/company/ticker filtering | inherited `Filings.filter` and feed table | EDGARTOOLS_NATIVE_DIRECT | Native filtering; AQ later supplies eligible CIKs only. |
| 5 | Latest filings | `Company.latest`, `Company.get_filings` | EDGARTOOLS_NATIVE_DIRECT | Native issuer history and sorting. |
| 6 | Filing metadata | `Filing`, `EntityFiling` | EDGARTOOLS_NATIVE_DIRECT | Form, issuer, dates, document metadata native. |
| 7 | Accession identity | `accession_no` / `accession_number` | EDGARTOOLS_NATIVE_DIRECT | Stable native identifier. |
| 8 | Acceptance datetime | current feed `accepted`; `EntityFiling.acceptance_datetime` | EDGARTOOLS_NATIVE_DIRECT | Native availability timestamp. |
| 9 | Issuer-aware filing discovery | `Company(cik).get_filings` | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | AQ supplies only accepted episode-to-CIK eligibility. |
| 10 | Processed-accession deduplication | native accession plus AQ checkpoint | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | AQ stores processed/not-processed state; no generic dedup engine. |
| 11 | Company/entity metadata | `Company`, `Entity` | EDGARTOOLS_NATIVE_DIRECT | Native entity model. |
| 12 | Filer/foreign-issuer metadata | entity metadata and filing forms | EDGARTOOLS_NATIVE_DIRECT | Native CIK/form evidence. |
| 13 | Historical EntityFacts discovery | `Company.get_facts`, `EntityFacts.query/time_series` | EDGARTOOLS_NATIVE_DIRECT | Native historical facts; final AQ evidence still accession-bound. |
| 14 | Annual financials | `Company.get_financials` | EDGARTOOLS_NATIVE_DIRECT | Native financial object. |
| 15 | Quarterly financials | `Company.get_quarterly_financials` | EDGARTOOLS_NATIVE_DIRECT | Native quarterly surface. |
| 16 | Income statement | `Financials.income_statement` | EDGARTOOLS_NATIVE_DIRECT | Native statement. |
| 17 | Balance sheet | `Financials.balance_sheet` | EDGARTOOLS_NATIVE_DIRECT | Native statement. |
| 18 | Cash-flow statement | `Financials.cash_flow_statement` | EDGARTOOLS_NATIVE_DIRECT | Native statement. |
| 19 | Foreign issuer financials | `TwentyF`, `FortyF`, native XBRL/Financials | EDGARTOOLS_NATIVE_DIRECT | Native foreign-report objects. |
| 20 | Multi-period financials | `MultiFinancials`, `XBRLS` | EDGARTOOLS_NATIVE_DIRECT | Native multi-filing composition. |
| 21 | Statement stitching | `XBRLS.get_statement`, `XBRL.stitch_statements` | EDGARTOOLS_NATIVE_DIRECT | Native stitching owner. |
| 22 | Statement standardization | XBRL standardization / standard concepts | EDGARTOOLS_NATIVE_DIRECT | AQ only maps the frozen approved metric vocabulary. |
| 23 | Duration, period, comparative-period semantics | current-period and period-selector modules | EDGARTOOLS_NATIVE_DIRECT | Native instant/duration and optimal-period semantics. |
| 24 | XBRL extraction | `Filing.xbrl`, `XBRL.from_filing` | EDGARTOOLS_NATIVE_DIRECT | Native parser; no AQ XBRL parser. |
| 25 | Dimensions | `FactsView`, axes/domains and dimension APIs | EDGARTOOLS_NATIVE_DIRECT | Raw dimensions retained natively. |
| 26 | Contexts | `XBRL.contexts` | EDGARTOOLS_NATIVE_DIRECT | Native context model. |
| 27 | Units | `XBRL.units` | EDGARTOOLS_NATIVE_DIRECT | Native unit model. |
| 28 | Calculation relationships | `calculation_linkbase/trees` | EDGARTOOLS_NATIVE_DIRECT | Native relationship model. |
| 29 | Presentation relationships | `presentation_roles/trees` | EDGARTOOLS_NATIVE_DIRECT | Native relationship model. |
| 30 | Definition relationships | `definition_roles`, dimensions/domains | EDGARTOOLS_NATIVE_DIRECT | Native relationship model. |
| 31 | Inline XBRL | native filing/XBRL parser and `is_inline_xbrl` | EDGARTOOLS_NATIVE_DIRECT | Native parser. |
| 32 | Exact native XBRL source assets | `XBRLAttachments` over `Filing.attachments` | EDGARTOOLS_NATIVE_DIRECT | AQ hashes the selected native bytes but does not discover/parse them. |
| 33 | Typed 10-K reports | `TenK` | EDGARTOOLS_NATIVE_DIRECT | Native item and financial interfaces. |
| 34 | Typed 10-Q reports | `TenQ` | EDGARTOOLS_NATIVE_DIRECT | Native item and financial interfaces. |
| 35 | Typed 20-F reports | `TwentyF` | EDGARTOOLS_NATIVE_DIRECT | Native foreign annual report. |
| 36 | Typed 40-F reports | `FortyF` | EDGARTOOLS_NATIVE_DIRECT | Native Canadian annual report. |
| 37 | Typed 6-K reports | `SixK` / current-report object | EDGARTOOLS_NATIVE_DIRECT | Native text, exhibits and press-release surface. |
| 38 | Typed 8-K reports | `CurrentReport` / `EightK` | EDGARTOOLS_NATIVE_DIRECT | Native items, exhibits, earnings and press releases. |
| 39 | 10-KT/10-QT transition reports | native XBRL core, no typed registry entry | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | Existing four-form leaf admits only native structured XBRL; filed form preserved. |
| 40 | Filing document/HTML | `Filing.document/html/parse` | EDGARTOOLS_NATIVE_DIRECT | Native document parser. |
| 41 | Filing text | `Filing.text`, `Document.text` | EDGARTOOLS_NATIVE_DIRECT | Native text extraction. |
| 42 | Filing markdown | `Filing.markdown`, `Document.to_markdown` | EDGARTOOLS_NATIVE_DIRECT | Native markdown conversion. |
| 43 | Section/item extraction | typed report `get/items/sections`; `Document.get_sec_section` | EDGARTOOLS_NATIVE_DIRECT | Native section model. |
| 44 | Search/grep | `Filing.grep/search`, `Document.search` | EDGARTOOLS_NATIVE_DIRECT | Native exact/regex/semantic document search surfaces. |
| 45 | Tables | `Document.tables`, XBRL statements | EDGARTOOLS_NATIVE_DIRECT | Native HTML/XBRL tables. |
| 46 | Attachments and exhibits | `Attachments`, `Attachment`, typed exhibits | EDGARTOOLS_NATIVE_DIRECT | Native discovery/content/download. |
| 47 | Financial statement notes | `XBRL.notes`, `Note`, `Notes` | EDGARTOOLS_NATIVE_DIRECT | Native hierarchy, text, tables, policies and details. |
| 48 | Debt disclosures | `Notes.search/grep`, note tables/text | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | AQ may select an authorized debt feature contract; no custom parser. |
| 49 | Lease disclosures | `Notes.search/grep`, note tables/text | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | AQ may select an authorized lease feature contract; no custom parser. |
| 50 | Revenue disclosures | `Notes.search/grep`, note tables/text | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | AQ may select an authorized revenue feature contract; no custom parser. |
| 51 | Contingency disclosures | `Notes.search/grep`, note tables/text | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | AQ may select an authorized contingency feature contract; no custom parser. |
| 52 | Risk factors | `TenK/TwentyF/FortyF.risk_factors` | EDGARTOOLS_NATIVE_DIRECT | Native typed section. |
| 53 | MD&A | `TenK/TwentyF.management_discussion` and typed item access | EDGARTOOLS_NATIVE_DIRECT | Native typed section. |
| 54 | Amended filing discovery | `get_filings(amendments=...)`, `/A` typed mapping, `related_filings` | EDGARTOOLS_NATIVE_DIRECT | Native discovery and relationships. |
| 55 | Original/amendment PIT vintage semantics | native accession/acceptance plus AQ PIT contract | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | AQ prevents backward rewrite and applies each acceptance session. |
| 56 | Remote HTTP retry/cache/rate limit | native HTTP manager/request helpers | EDGARTOOLS_NATIVE_DIRECT | No AQ SEC client. |
| 57 | Local storage/download | `use_local_storage`, `download_filings`, attachment download | EDGARTOOLS_NATIVE_DIRECT | Native storage/download owner. |
| 58 | Cache management/compression | `clear_cache`, `cleanup_storage`, `compress_filing(s)` | EDGARTOOLS_NATIVE_DIRECT | Native lifecycle utilities. |
| 59 | Immutable source identity/hash evidence | native assets plus AQ evidence contract | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | AQ hashes exactly the consumed native assets for offline provenance. |
| 60 | Current filing polling/refresh | current-filings functions and pagination | EDGARTOOLS_NATIVE_DIRECT | A bounded scheduler may call the API; no AQ poller engine. |
| 61 | Live incremental ingestion | current filings plus native filing/XBRL objects | EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY | AQ only filters CIK/forms, checks accession checkpoint, and projects evidence. |
| 62 | Push/webhook delivery | none in audited 5.58.0 | TRUE_UPSTREAM_GAP | Polling is sufficient for planned P5; no replacement engine is authorized. |
| 63 | AI-friendly documents | chunks, `prepare_for_llm`, `to_context` | EDGARTOOLS_NATIVE_DIRECT | Native preparation; model/prompt policy remains separate. |
| 64 | MCP tools | installed `edgartools-mcp` entry point | EDGARTOOLS_NATIVE_DIRECT | Optional native tooling surface; not required for historical build. |
| 65 | 8-K narrative intelligence | `CurrentReport` items/text/exhibits/press releases | EDGARTOOLS_NATIVE_DIRECT | Future feature policy may consume native content. |
| 66 | 6-K narrative intelligence | `SixK` text/exhibits/press releases | EDGARTOOLS_NATIVE_DIRECT | Future feature policy may consume native content. |

Reconciliation:

```text
EDGARTOOLS_CAPABILITY_COUNT_AUDITED = 66
EDGARTOOLS_NATIVE_DIRECT_COUNT = 55
EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY_COUNT = 10
TRUE_UPSTREAM_GAP_COUNT = 1
55 + 10 + 1 = 66
```

## Existing AQ duplication audit

| AQ surface | Decision | Reason |
|---|---|---|
| `aq_fundamental_evidence.materialize_edgartools_fact` | KEEP_AQ_DOMAIN_POLICY | Projects one already-parsed native fact into `FundamentalEvidenceV1`; no parsing. |
| `aq_hybrid_fundamentals` | KEEP_AQ_DOMAIN_POLICY | Frozen metric, PIT session, dimension and as-of policy only. |
| `aq_edgartools_full_build` | KEEP_AQ_DOMAIN_POLICY | Finite inventory, asset hashing, batch/checkpoint and fail-closed seal policy. |
| `_HomepageFilingView` transition/source leaf | KEEP_AQ_DOMAIN_POLICY | Selects native homepage attachments and keeps `XBRL.from_filing` as parser owner. |
| transient asset meter/cache ceiling | KEEP_AQ_DOMAIN_POLICY | Bounded evidence retention and resource policy; it does not implement transport. |
| SEC client/downloader/parser/router | NO_DUPLICATION | No AQ implementation exists. |
| current filing watcher/poller | NO_DUPLICATION | No AQ implementation exists. |
| statement standardizer/stitcher | NO_DUPLICATION | EdgarTools is called directly. |
| document/section/note parser | NO_DUPLICATION | No AQ implementation exists. |

Accordingly:

```text
CURRENT_AQ_DUPLICATE_COUNT = 0
AQ_DUPLICATES_RETIREABLE_COUNT = 0
```

The 5.58.0 transition-form typed-object omission is a bounded upstream surface
gap, not evidence for a generic AQ form router. Existing AQ code calls the
unchanged native XBRL path and preserves the filed form.

## Activated future live path

The selected future path is:

```text
EdgarTools get_current_filings / page iteration
  -> AQ accepted-CIK and authorized-form filter
  -> AQ accession checkpoint (processed / not processed)
  -> EdgarTools Filing / typed object / XBRL / Financials
  -> FundamentalEvidenceV1 projection
  -> existing acceptance-time and XNYS effective-session policy
  -> immutable new PIT vintage
```

This requires a bounded scheduler, not a custom SEC polling engine. The
scheduler must not parse RSS/Atom, own HTTP retry/cache, or recreate filing,
document, XBRL, or financial logic. Accession is the recovery and deduplication
unit. Full history is not reread on each cycle.

## Activated future narrative path

```text
EdgarTools typed filing object / Document / Notes / Attachments
  -> AQ separately preregistered narrative or disclosure feature policy
  -> immutable accession/acceptance-bound evidence
```

MD&A, risk factors, 8-K/6-K narrative, exhibits, notes, and note tables can all
start from native interfaces. Debt, lease, revenue, and contingency features
may require a small domain contract specifying which native notes/tables are
admissible, but never a new HTML, section, filing, or XBRL parser.

## Offline interface proof

Import/signature/source inspection against the installed 5.58.0 runtime proved
the current-feed object, issuer/EntityFacts surface, Financials/MultiFinancials,
XBRL/XBRLS, all six typed report families, Document text/markdown/section APIs,
Note/Notes, Attachments, storage/cache APIs, and the MCP entry point. Existing
mock/frozen P5 tests exercise the AQ contract boundary without SEC access.

Validation results:

```text
OFFLINE_INTERFACE_PROOFS = 15/15 PASS
P5_AFFECTED_TESTS = 123/123 PASS
RUFF_PRODUCTION_SCOPE = PASS
DIFF_CHECK = PASS
```

```text
AQ_SEC_CLIENT = NO
AQ_SEC_POLLER = NO
AQ_RSS_PARSER = NO
AQ_FILING_DOWNLOADER = NO
AQ_FORM_ROUTER_ENGINE = NO
AQ_XBRL_ENGINE = NO
AQ_FINANCIAL_STATEMENT_ENGINE = NO
AQ_DOCUMENT_PARSER_ENGINE = NO
AQ_STATEMENT_STITCHING_ENGINE = NO
AQ_GENERIC_ETL = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
HISTORICAL_BUILD_INTERFERENCE = NO
HISTORICAL_BUILD_PROCESS_STOPPED = NO
HISTORICAL_BUILD_PROCESS_RESTARTED = NO
HISTORICAL_BUILD_CHECKPOINTS_MUTATED = NO
HISTORICAL_BUILD_DATA_MUTATED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

## Next

The historical build remains the active development operation. After that
build reaches its own terminal closeout, the now-frozen direct-native live path
can be exercised by:

```text
CURRENT_DEVELOPMENT_NEXT = P5_LIVE_INCREMENTAL_FILING_INGESTION_DESIGN_AND_POC_001
```

That future task may implement only the scheduler/checkpoint/policy boundary;
it must call EdgarTools directly for discovery and filing intelligence.
