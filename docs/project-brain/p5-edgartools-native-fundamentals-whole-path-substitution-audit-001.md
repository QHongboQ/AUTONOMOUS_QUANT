# P5 EdgarTools native fundamentals whole-path substitution audit 001

## Result

The bounded audit passes. The already-installed EdgarTools `5.58.0` runtime
can own issuer-aware SEC filing discovery, typed financial-statement
extraction, and accession-bound XBRL fact extraction for the P5 path. SEC
EDGAR remains source authority; AQ retains only the accepted CIK binding, SEC
acceptance-time eligibility, provenance admission, and thin contracts.

```text
SEC_EDGAR = SOURCE_AUTHORITY
EDGARTOOLS = ISSUER_AWARE_FILING_AND_FINANCIALS_OWNER
SECFSDSTOOLS = OPTIONAL_BULK_ACCELERATOR_AND_CROSSCHECK
AQ = CIK_BINDING + PIT_ELIGIBILITY + PROVENANCE_ADMISSION + THIN_CONTRACTS
QLIB = RESEARCH_CONSUMPTION
```

The unmerged accession-census branch remains
`DIAGNOSTIC_CENSUS_EVIDENCE_PENDING_UPSTREAM_REALIGNMENT`. Its 721 bound
episodes, 711 unique CIKs, 70,021 domestic-periodic accession rows,
acceptance-time completeness, storage measurements, and local FSDS coverage
measurements remain useful. Its domestic-form whitelist and incomplete-FSDS
hard gate are not promoted to authority.

## Runtime and 711-CIK feasibility

The audit used Python `3.14.7` at
`/home/zhou/AQ_ENVS/p5-fundamental-intelligence/bin/python` and the installed
EdgarTools `5.58.0` distribution. No upgrade occurred. Every one of the 711
accepted bound CIKs was addressable through native `Company(CIK)`.

| Measure | Count |
|---|---:|
| bound CIKs | 711 |
| EdgarTools-addressable CIKs | 711 |
| native domestic classification | 677 |
| native foreign-private classification | 29 |
| native classification unavailable | 5 |
| issuers exposing 20-F | 3 |
| issuers exposing 40-F | 0 |
| native financial candidate surface available | 708 |
| native financial candidate surface unavailable | 3 |

“Native financial candidate surface” means at least one issuer-aware native
annual or quarterly candidate form is discoverable through
`Company.get_filings()`. It does not claim that every filing contains
structured statements. The three unavailable cases are FRC, MJN, and LXK
under their accepted CIKs. The bound universe contains no observed 40-F
issuer, so the Canadian control is correctly recorded as
`CONTROL_NOT_PRESENT_IN_BOUND_UNIVERSE`; installed source inspection confirms
that `Company.get_financials()` has a native 40-F fallback.

Five native `filer_type` values are unavailable for terminated or reorganized
registrants. They are retained as unclassified rather than manufactured.

## Native domestic and foreign paths

AAPL's 2024 10-K and 10-Q resolved through native typed `TenK` and `TenQ`
objects. The 10-K exposed balance sheet, income statement, cash-flow
statement, XBRL, accession, report period, and acceptance datetime.

CCEP's 2024 20-F resolved through native `TwentyF` with `Financials`, including
balance sheet, income statement, cash-flow statement, IFRS XBRL facts,
accession, report period, and acceptance datetime. AQ supplied no 20-F routing
branch. Installed-source inspection independently confirms the upstream
fallbacks:

```text
Company.get_financials(): 10-K -> 20-F -> 40-F
Company.get_quarterly_financials(): 10-Q -> 6-K
```

## 6-K boundary

The audit measured all selected-issuer 6-K metadata through 2024-12-31 and
performed native parsing for every SEC-XBRL-marked candidate.

| Issuer | 6-K | typed `SixK` | XBRL | native financials confirmed | event/exhibit/textual |
|---|---:|---:|---:|---:|---:|
| CCEP | 359 | 359 | 16 | 16 | 343 |
| NXPI | 136 | 136 | 0 | 0 | 136 |
| CPRI | 23 | 23 | 0 | 0 | 23 |
| **total** | **518** | **518** | **16** | **16** | **502** |

Therefore:

```text
EDGARTOOLS_6K_ROLE = NATIVE_WHERE_STRUCTURED_OTHERWISE_EVENT_OR_TEXTUAL
```

The 502 non-XBRL filings are not silently promoted to periodic structured
fundamentals. No AQ 6-K heuristic or form router was created.

## PIT and raw-fact provenance

For the selected AAPL 10-K and CCEP 20-F, the lower native EdgarTools XBRL
fact surface retained taxonomy-qualified concept, context, dimensions, unit,
period, statement classification, accession, CIK, filing date, report period,
and SEC acceptance datetime. Each selected primary filing document was hashed,
and both facts successfully projected through the existing
`FundamentalEvidenceV1` materializer.

The AAPL control retained a dimensioned `us-gaap` revenue fact; the CCEP
control retained an `ifrs-full` cost-of-sales fact. Convenience statements are
not sole authority. The project availability authority remains exact SEC
acceptance datetime, never filing date.

Native `get_current_filings()` is present for the future live path, where
accession number is the deduplication key. The frozen ingestion model remains:

```text
HISTORICAL = ONE_TIME_BACKFILL_PLUS_IMMUTABLE_VINTAGES
LIVE = INCREMENTAL_NEW_ACCESSION_ONLY
REPEATED_FULL_HISTORY_REREAD = NO
FULL_DOCUMENT_LLM_REQUIRED = NO
```

## Zero-periodic reinterpretation

The five prior diagnostic cases now have issuer-aware classifications:

| Ticker | Classification |
|---|---|
| FRC | `TRUE_NO_PERIODIC_FINANCIAL_COVERAGE` |
| CCEP | `FOREIGN_ISSUER_NATIVE_PATH` |
| MJN | `TRUE_NO_PERIODIC_FINANCIAL_COVERAGE` |
| FCPT | `OUTSIDE_EPISODE_TIMING` |
| LXK | `TRUE_NO_PERIODIC_FINANCIAL_COVERAGE` |

CCEP proves the prior domestic whitelist produced a false-negative shape:
native discovery exposes 20-F and 6-K. FCPT's first census periodic filing is
2015-12-04, after its short P1 episode ended on 2015-11-17. The other three
accepted CIKs expose no native 10-K/10-Q/20-F/40-F/6-K candidate; their
identity authority is not reopened or substituted.

## FSDS and ownership decision

Complete local FSDS quarter coverage is not required for correctness. SEC
EDGAR plus EdgarTools already provide issuer-aware discovery, exact filing
retrieval, acceptance metadata, typed reports, and accession-bound XBRL facts.
FSDS remains useful for bulk catalog acceleration and offline cross-checking,
but neither FSDS acceptance timestamps nor missing-quarter completion is an
admission authority.

```text
SECFSDSTOOLS_CLASSIFICATION = OPTIONAL_BULK_ACCELERATOR
SECFSDSTOOLS_ROLE = OPTIONAL_BULK_ACCELERATOR_AND_CROSSCHECK
CAN_SECFSDSTOOLS_BE_DEMOTED_FROM_FULL_BUILD_GATE = YES
SECFSDSTOOLS_MISSING_QUARTERS_DOWNLOADED = 0
SECFSDSTOOLS_AUTOUPDATE_DEFAULT_TRUSTED = NO
IS_AQ_PERIODIC_FORM_WHITELIST_REQUIRED = NO
IS_AQ_FINANCIAL_STATEMENT_ENGINE_REQUIRED = NO
```

## Reproducibility and safety

Private evidence is stored at:

```text
D:\AQ_DATA\P5\edgartools-native-fundamentals-whole-path-substitution-audit-001
CHECKSUMS_SHA256 = f1d0a03069d5d4ffa95953aba5fdf1538852c5bebc62e959021633e259d9a4fb
```

No production code, form router, XBRL engine, statement engine, SEC client,
filing-index engine, historical dataset, factor, model training, or backtest
was added. P2 V2 sealed OOS was not accessed.

```text
PRODUCTION_LOC_ADDED = 0
AQ_FORM_ROUTER_ENGINE = NO
AQ_XBRL_ENGINE = NO
AQ_STATEMENT_ENGINE = NO
AQ_SEC_CLIENT = NO
AQ_FILING_INDEX_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_EDGARTOOLS_NATIVE_FULL_UNIVERSE_BUILD_DESIGN_001
```
