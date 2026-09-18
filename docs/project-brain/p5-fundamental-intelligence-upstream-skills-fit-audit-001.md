# P5 Fundamental Intelligence Upstream Skills Fit Audit 001

## Outcome

```text
TASK = AUTONOMOUS-QUANT-P5-FUNDAMENTAL-INTELLIGENCE-UPSTREAM-SKILLS-FIT-AUDIT-001
BASELINE_MAIN_SHA = 1e19bfe972fc899a2e85435e478f03dad054d1ec
P5_UPSTREAM_STACK_SELECTED = YES
SELECTED_STACK = SEC_EDGAR_RAW_AUTHORITY + OPENBB_SEC_STRUCTURED_PIT_LEAF + EDGARTOOLS_FILING_XBRL_DOCUMENT_SKILL
CURRENT_DEVELOPMENT_NEXT = P5_FUNDAMENTAL_INTELLIGENCE_SELECTED_UPSTREAM_DEPLOYMENT_001
FINAL_CLASSIFICATION = PASS
```

This is an upstream-selection result, not a factor result. It added no SEC
crawler, XBRL parser, filing parser, RAG system, vector database, fundamental
engine, model, signal, backtest, or investment conclusion.

The operational P2 Formulaic Protocol V2 sealed-OOS clock remains unchanged:

```text
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
P2_FORMULAIC_ALPHA_V2_SEALED_OOS_START = 2026-09-18
P2_FORMULAIC_ALPHA_V2_MINIMUM_OOS_SESSIONS = 126
P2_V2_SEALED_OOS_ACCESSED = NO
```

## Selected ownership

| Component | Classification | P5 ownership |
|---|---|---|
| SEC EDGAR | `UPSTREAM_WHOLE_SOURCE_AUTHORITY` | Primary filing/accession/document/XBRL source authority |
| OpenBB SEC | `UPSTREAM_LEAF_PARTIAL_PIT_STRUCTURED_GATEWAY` | Standardized financial-statement leaf, never standalone evidence authority |
| EdgarTools | `UPSTREAM_WHOLE_OR_LEAF_SELECTED` | Filing discovery, retrieval, documents, sections, tables, filing-specific XBRL, financial statements, and Skill guidance |
| EdgarTools Skill | `CLAUDE_SKILL_PACKAGE_CODEX_COMPATIBLE_VIA_PRIVATE_THIN_EXPORT` | Untouched upstream `SKILL.md` package through a private isolated export/install path |
| sec-parser | `REJECT_UNMAINTAINED_DUPLICATE` | Not selected |
| Arelle | `DEFER_CHALLENGER_ADVANCED_XBRL_VALIDATION_ONLY` | Optional future validation fallback only |
| sec-edgar-downloader | `REJECT_DUPLICATE_RETRIEVAL_ONLY` | Not selected |

AQ owns only the PIT admission boundary, evidence identity, factor semantics,
and any later minimal adapter required to connect upstream objects. The SEC is
not replaceable as US filing source authority.

## SEC source authority

Official SEC interfaces provide submissions metadata, accession/form/report
metadata, raw archive documents, and Company Facts/Company Concept XBRL JSON.
Public access requires no API key, but automated clients must send a meaningful
identity/contact and remain within the SEC fair-access limit. This task found no
configured `EDGAR_IDENTITY`, so it issued zero SEC requests and did not invent
one.

```text
LIVE_SEC_POC = BLOCKED_IDENTITY_NOT_CONFIGURED
SEC_NETWORK_REQUESTS = 0
FIRST_AVAILABLE_AT_AUTHORITY = SEC_ACCEPTANCE_DATETIME_OR_RAW_ACCEPTANCE_DATETIME
```

If acceptance time cannot be proven from submissions/current-feed metadata or
the raw submission header, the datum is not admitted. Filing date and report
period are not substitutes for market availability time.

## OpenBB `pit_mode`

Source inspection found that `pit_mode=true` selects the earliest filed record
for a reporting period and disables the later 10-K quarterly-vintage override.
That is useful protection against a common restatement leak.

The standardized balance sheet, income statement, cash-flow, and growth result
records do not themselves retain all P5-required evidence fields: exact
accession, acceptance timestamp, form, source document content hash, and full
filing-vintage identity. OpenBB therefore cannot independently prove the datum's
historical availability.

```text
OPENBB_PIT_MODE = PARTIAL
OPENBB_STANDALONE_PIT_AUTHORITY = NO
OPENBB_ACCEPTANCE_RULE = REQUIRE_EXTERNAL_SEC_ACCESSION_AND_ACCEPTANCE_JOIN
```

## EdgarTools and Skill

EdgarTools source and release surfaces cover company/CIK lookup, form/date
search, amendments, accession-bound filings, attachments, complete submissions,
HTML/text, 10-K/10-Q/8-K objects, sections, tables, inline XBRL, statements,
local evidence reuse, and `edgar.ai`.

The Skill was exported into private staging only; no global Skill installation
occurred. Its `SKILL.md` frontmatter and relative supporting files are portable
to the project's agent Skill shape without rewriting the upstream documentation.

```text
EDGARTOOLS_VERSION = 5.58.0
EDGARTOOLS_SOURCE_SHA = e23d04eba952e70310c0f62402f4c2523f9a44bf
SKILL_MD_SHA256 = 65ff350a67cbb8ff9ca0dc6038aa9b6856fe3855e9e4b008bfe81124617d4791
SKILL_PACKAGE_SHA256 = 63e29e5794ec577817199cf6551c9acd83f988146da7bf20d07d9b74891eaf6c
GLOBAL_SKILL_INSTALL = NO
```

The historical base `Filing` object binds CIK, form, filing date, and accession;
its evidence must still be joined to the SEC acceptance timestamp. EdgarTools
does not replace the SEC as authority.

## Isolated validation

All packages were installed only in:

```text
/home/zhou/AQ_ENVS/p5-fundamental-intelligence-audit
```

Installed audit anchors include:

```text
openbb-core = 1.6.13
openbb-sec = 1.6.7
edgartools = 5.58.0
sec-parser = 0.58.1
arelle-release = 2.45.1
sec-edgar-downloader = 5.1.0
```

EdgarTools upstream offline XBRL-schema and AI-Skill-export tests passed
`45/45`. A deterministic pre-cutoff offline sample proved:

- Apple 2010 10-K, accession `0001193125-10-238044`: 1,377 XBRL facts parsed;
- historical 2021 8-K fixture, accession `0000887919-21-000012`: 6,524 text
  characters, 119 document blocks, and 31 chunks parsed; raw HTML hash
  `506cca6f069ce64b3d8f7199f82be60cfdbb118b5ba8d38f44d20c40cd69ce44`.

The required live 10-Q, amendment, and OpenBB original-versus-latest comparison
remain an exact deployment blocker because there was no configured SEC identity
and no complete local pre-2022 fixture set for those cases. This is not reported
as a completed four-form live POC.

## PIT and restatement contract

A future `FilingEvidence` must retain CIK/entity, accession, form, filing date,
acceptance time/`first_available_at`, report period, fiscal period, amendment
status, source URL, content SHA-256, and upstream parser/provider identity.

A future `FundamentalEvidence` must additionally retain filing evidence ID,
taxonomy/concept, reported value, unit, currency, dimensions/context, fact
period, and filing vintage.

```text
REPORT_PERIOD_END != FIRST_AVAILABLE_AT
RESTATEMENT_HANDLING = FAIL_CLOSED_AND_EXPLICIT
LLM_STRUCTURED_FACT_OVERRIDE = PROHIBITED
```

Original filings, amendments, and later comparative restatements are separate
accession-bound vintages. An amendment becomes usable only at its own verified
acceptance time. A later 10-K comparative value is never projected backward.
Any fact that cannot be tied to one accession and one availability time is
rejected.

## Storage and intelligence boundaries

The 256 GB constraint is respected by retaining bounded accession metadata,
hashes, selected facts/contexts, and only the sections or primary documents
actually used. A full SEC mirror, unbounded attachment archive, embeddings, and
vector database are not part of this design.

Deterministic upstream XBRL/accounting values take precedence. LLM/NLP may later
assist with MD&A, risk factors, business descriptions, footnotes, and event
classification, but cannot silently alter a structured fact.

Candidate P5 factor families are semantic labels only: profitability, growth,
quality, leverage, cash flow, accruals, valuation, and capital efficiency. No
thresholds, optimization, performance metrics, or backtests were produced.

P6 skills remain deferred: news, macro/FRED, earnings calls, social sentiment,
TradingAgents, FinGPT, and FinBERT.

## No implementation creep

```text
AQ_SEC_FETCHER = NO
AQ_XBRL_PARSER = NO
AQ_FILING_PARSER = NO
AQ_DOCUMENT_SEARCH_ENGINE = NO
AQ_VECTOR_DB = NO
AQ_RAG_ENGINE = NO
AQ_FUNDAMENTAL_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_PERFORMANCE_BACKTEST = NO
```

Private evidence is stored under
`D:/AQ_DATA/P5/fundamental-intelligence-upstream-skills-fit-audit-001/`.

```text
PRIVATE_REPORT = D:/AQ_DATA/P5/fundamental-intelligence-upstream-skills-fit-audit-001/audit_summary.json
PRIVATE_REPORT_SHA256 = 689e412d758d76b6253239e2a1d5e7e5a3cfb962977262e9f30512bde52067db
```
