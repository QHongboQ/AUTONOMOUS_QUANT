# P5 SEC FSDS / secfsdstools Upstream Substitution Audit 001

## Authority

```text
TASK = AUTONOMOUS-QUANT-P5-SEC-FSDS-SECFSDSTOOLS-UPSTREAM-SUBSTITUTION-AUDIT-001
BASELINE_MAIN_SHA = 4f9430319114ebcf5195a87c7d08f4a6e7bfbf40
AUDIT_CLASSIFICATION = PASS
FINAL_ARCHITECTURE_DECISION = C. HYBRID_WITH_EXACT_BOUNDARIES
P5_FOUNDATION = MERGED
P5_FULL_PHASE_COMPLETE = NO
P5_DATASET_BUILD_PILOT_GATE = OPEN
P5_DATASET_BUILD_PILOT_STATUS = TEMPORARILY_SUPERSEDED_BY_UPSTREAM_SUBSTITUTION_DECISION
CURRENT_DEVELOPMENT_NEXT = P5_SEC_FSDS_SECFSDSTOOLS_DEPLOYMENT_AND_BOUNDED_POC_001
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
P2_V2_SEALED_OOS_ACCESSED = NO
```

This audit changes no evidence contract and admits no new fundamental evidence.
It selects a bounded split of ownership for the next implementation task:

```text
SEC_FSDS_SECFSDSTOOLS_ROLE = BULK_HISTORICAL_CANDIDATE_CATALOG
EDGARTOOLS_ROLE = EXACT_ACCESSION_EVIDENCE_ADMISSION_AND_DEEP_FILING_ACCESS
EPISODE_SEC_CIK_BINDING_V1_ROLE = DATE_BOUNDED_PROJECT_IDENTITY_AUTHORITY
AQ_ROLE = THIN_FAIL_CLOSED_ADMISSION_AND_SESSION_PROJECTION
```

## SEC FSDS authority and PIT boundary

The SEC Financial Statement Data Sets are official, quarterly, flattened,
as-filed data from primary rendered financial statements. The current official
page begins at January 2009; the specification describes the relevant filing
scope beginning with submissions filed on or after 2009-04-15. SUB, NUM, PRE,
and TAG provide accession/submission, numeric fact, statement-presentation, and
taxonomy-tag metadata. The SEC explicitly says the data sets omit some filing
metadata and are not a substitute for the filings.

```text
SEC_FSDS_PIT_FIT = PARTIAL
SEC_FSDS_COVERAGE_START = 2009-01; FILING_SCOPE_FROM_2009-04-15
FSDS_ACCEPTANCE_DATETIME_AUTHORITY = PARTIAL
FSDS_AMENDMENT_VINTAGE = PASS
```

Four historical accessions were compared with preserved SEC submission-header
acceptance datetimes. After interpreting FSDS `accepted` in
`America/New_York`, none matched the raw header at second precision:

| Accession | FSDS normalized UTC | Raw header UTC | Delta |
|---|---:|---:|---:|
| 0001193125-09-214859 | 2009-10-27T20:18:00Z | 2009-10-27T20:18:29Z | -29 s |
| 0001193125-10-012091 | 2010-01-25T21:26:00Z | 2010-01-25T21:25:58Z | +2 s |
| 0001018724-21-000004 | 2021-02-03T00:44:00Z | 2021-02-03T00:44:10Z | -10 s |
| 0001558370-21-001489 | 2021-02-23T22:08:00Z | 2021-02-23T22:08:23Z | -23 s |

Therefore FSDS must not replace the exact submission-header datetime used by
`FIRST_AVAILABLE_AT`. The Apple FY2009 10-K and 10-K/A remain distinct by
accession and acceptance time for the same report period. `prevrpt=1` means
that submission information was subsequently amended; it does not mean that
the row itself is the amendment. No amendment is projected backward.

Official references:

- https://www.sec.gov/data-research/sec-markets-data/financial-statement-data-sets
- https://www.sec.gov/files/fsds.pdf

## secfsdstools 2.4.3 audit

```text
SECFSDSTOOLS_VERSION = 2.4.3
SECFSDSTOOLS_SOURCE_SHA = af83c24f999109322d01b4980d207eec67bc749e
SECFSDSTOOLS_LICENSE = Apache-2.0
SECFSDSTOOLS_AUDIT_PYTHON = 3.12.3
SECFSDSTOOLS_PIP_CHECK = PASS
SECFSDSTOOLS_BULK_INGEST_FIT = PARTIAL
SECFSDSTOOLS_SEC_IDENTITY_CONFIGURATION = PARTIAL
SECFSDSTOOLS_AUTOUPDATE_CAN_BE_DISABLED = YES
SECFSDSTOOLS_DAILYPROCESSING_FOR_P5_HISTORICAL = DISABLED
TICKER_DEPENDENCY_FOR_FSDS = NO
SECFSDSTOOLS_SQLITE_INDEX = UPSTREAM_INTERNAL_ACCEPTABLE
AQ_NEW_DATABASE = NO
```

The package successfully owns quarterly discovery/download, SUB/NUM/PRE
Parquet transformation, its internal SQLite report index, and CIK/adsh/form/
statement/tag selection. The bounded POC used only official 2009Q4, 2010Q1,
and 2021Q1 ZIPs and indexed 7,295 reports. CIK-based collection worked without
a ticker.

The bulk fit is not an unconditional PASS:

- the public top-level updater does not expose a clean quarter-bounded initial
  load and otherwise enumerates all missing quarters;
- transformed Parquet contains SUB, NUM, and PRE but not TAG;
- NUM `value` is coerced to `float64`, which does not preserve exact decimal
  semantics;
- `UserAgentEmail` is an official configuration seam, but its validator accepts
  a bare email rather than the SEC-preferred name-plus-email identity string.

No identity value entered Git or the private reports. `AutoUpdate=False` was
verified as a no-op, and daily processing remained disabled. The established
P5 and RD-Agent environments were not changed.

## Evidence-contract boundary

```text
SECFSDSTOOLS_RAW_FACT_PROVENANCE = PARTIAL
FUNDAMENTAL_EVIDENCE_V1_FSDS_COMPATIBILITY = NO
FUNDAMENTAL_EVIDENCE_V2_REQUIRED = DEFER
```

FSDS/secfsdstools preserves an accession-bound SUB/NUM/PRE relation, but the
transformed output cannot truthfully issue the immutable
`FundamentalEvidenceV1`. V1 freezes `parser_provider=EDGARTOOLS` and requires
the exact acceptance datetime, exact value semantics, source-document identity
and SHA-256, taxonomy metadata, and context/dimensions. A new V2 is deferred:
a provider-neutral schema would not repair missing precision or provenance.
The next task must first use FSDS only as a candidate catalog and retain
EdgarTools as the admission authority.

## Standardization boundary

```text
SECFSDSTOOLS_FAIL_CLOSED_MISSING_MODE = PARTIAL
SECFSDSTOOLS_STANDARDIZATION_PROVENANCE = PARTIAL
SECFSDSTOOLS_CAPEX_SEMANTICS = SUPPORTED
SECFSDSTOOLS_SHARES_SEMANTICS = PARTIAL
EDGARTOOLS_STANDARDIZATION_COMPARISON = EDGARTOOLS_RETAINS_ADMISSION_AUTHORITY; SECFSDSTOOLS_DEFAULT_STANDARDIZERS_NOT_ADMISSIBLE
```

The default standardizers can copy tags, calculate sums or missing summands,
post-process values, and set missing values to zero through `PostSetToZero`.
Public rule-tree composition can omit zero-fill rules, but there is no direct-
reported-only preset. Rule logs identify applied rules, not complete exact
source-row lineage. The bounded POC also observed date-collapsing behavior in
preprocessing that can retain a comparative period rather than the intended
report date. Default standardized values are therefore not admitted evidence.

`PaymentsToAcquirePropertyPlantAndEquipment` is an explicit direct cash-flow
tag and supports a later bounded CapEx contract decision. The package's
`OutstandingShares` output may instead copy weighted-average basic, diluted,
or partnership units; it is not point-in-time shares authority.

## Storage and ownership decision

```text
PREFERRED_HISTORICAL_BULK_PATH = SEC_FSDS_SECFSDSTOOLS_CANDIDATE_CATALOG_PLUS_EDGARTOOLS_EXACT_ACCESSION_ADMISSION
AQ_RAW_SEC_PARQUET_LAYER_REQUIRED = NO
```

The three-quarter POC downloaded 107,262,972 compressed bytes in three official
HTTP interactions and produced the upstream Parquet/index representation.
Official SEC ZIP sizes total about 2,319.57 MB for 2015-2021 before Parquet and
index overhead. That estimate is not extrapolated from the small POC.

`AQ_RAW_SEC_PARQUET_LAYER_REQUIRED=NO` means AQ must not duplicate the upstream
bulk archive, transform, and index. It does **not** remove the thin AQ admitted
exact evidence-event Parquet or the later effective-session/Qlib projection.

Planned future AQ components eliminated by the selected boundary are:

- quarterly archive discovery/acquisition orchestration;
- ZIP extraction and bulk SUB/NUM/PRE Parquet conversion;
- a parallel AQ report-index database;
- generic CIK/adsh/form/statement/tag selection;
- a duplicate raw SEC bulk Parquet layer.

AQ retains `EpisodeSecCikBindingV1`, exact accession admission, exact SEC
submission acceptance, exact decimal/source-document evidence, the frozen
semantic vocabulary, effective-session policy, and Qlib projection.

## EdgarTools, MCP, and challengers

```text
EDGARTOOLS_POST_FSDS_ROLE = EXACT_ACCESSION_ACCEPTANCE_DOCUMENT_HASH_XBRL_CONTEXT_DIMENSIONS_NOTES_TEXT_8K_DEEP_VERIFICATION_AND_MCP
EDGARTOOLS_MCP_FIT = PARTIAL
P5_AGENT_INTERFACE_RECOMMENDATION = LOCAL_EDGARTOOLS_MCP_PRIMARY_WITH_SKILL_GUIDANCE_FALLBACK
EPISODE_SEC_CIK_BINDING_REPLACEMENT = NONE
ONE_STACK_REPLACEMENT_FOUND = NO
```

The official local EdgarTools MCP uses stdio by default, supports streamable
HTTP, is stateless, queries EDGAR directly, and currently documents 13 intent-
oriented tools. It is a good consolidation target for agent-facing filing,
financial, section, note, text, ownership, fund, and proxy access. The fit is
PARTIAL because no MCP client deployment or Codex integration was performed in
this audit. The hosted commercial MCP is supplementary and is not evidence
authority. A Skill remains useful as guidance/fallback, not as a second manual
tool router.

- https://github.com/dgunning/edgartools/blob/main/docs/ai/mcp-setup.md
- https://github.com/dgunning/edgartools/blob/main/docs/ai/mcp-tools.md

Datamule and OpenFIGI remain supplemental utilities/corroboration. Neither
replaces project-specific, date-bounded Episode-to-CIK authority. Commercial
integrated services reviewed did not provide a provenance-equivalent one-stack
replacement without new lock-in or opaque transformations.

## Safety and private evidence

```text
AQ_SEC_CRAWLER = NO
AQ_SEC_HTTP_CLIENT = NO
AQ_XBRL_ENGINE = NO
AQ_STATEMENT_ENGINE = NO
AQ_STANDARDIZATION_ENGINE = NO
AQ_SECURITY_MASTER = NO
AQ_GENERIC_ETL = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_REPORT = audit_summary.json
PRIVATE_REPORT_SHA256 = 202f5b822a091a4e879d62427f09c74b128d87c7abb71ed2d8920eac1033db74
```

The private evidence contains 21 audit JSON artifacts plus a checksum file
under the authorized private audit root. Downloaded ZIPs, Parquet data, SQLite
index, environment, source checkout, scripts, identity configuration, and
private reports remain outside Git.
