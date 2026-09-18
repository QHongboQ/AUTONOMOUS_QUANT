# P5 OpenBB Role Closeout and Fundamental Evidence Contract 001

## Outcome

```text
TASK = AUTONOMOUS-QUANT-P5-OPENBB-ROLE-CLOSEOUT-AND-FUNDAMENTAL-EVIDENCE-CONTRACT-001
P5_PIT_CRITICAL_STACK = SEC_EDGAR_PLUS_EDGARTOOLS
OPENBB_P5_ROLE = SUPPLEMENTARY_NON_AUTHORITATIVE
PRIOR_OPENBB_PIT_CRITICAL_SELECTION = SUPERSEDED_BY_LIVE_POC_EVIDENCE
P5_FUNDAMENTAL_EVIDENCE_CONTRACT_V1 = MATERIALIZED
CURRENT_DEVELOPMENT_NEXT = P5_FUNDAMENTAL_EVIDENCE_MATERIALIZATION_POC_001
FINAL_CLASSIFICATION = PASS
```

The completed live POC is authoritative: SEC acceptance-time authority,
SEC-to-EdgarTools identity, accession-bound documents, filing XBRL, statements,
and the upstream Skill path passed. OpenBB SEC remained blocked by its current
aggregate Company Facts transport and the lack of a clean project-approved SEC
identity boundary. The prior OpenBB PIT-critical selection is therefore
superseded rather than patched.

The operational P2 authority did not change:

```text
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
P2_V2_SEALED_OOS_ACCESSED = NO
```

## Final P5 ownership

| Capability | Owner | Authority |
|---|---|---|
| US filing source and acceptance time | SEC EDGAR | Authoritative |
| Filing discovery/retrieval, accession-bound documents, XBRL, financial statements, sections/tables, Skill | EdgarTools | PIT-critical upstream |
| Standardized-statement convenience and cross-checking | OpenBB SEC | Supplementary, non-authoritative |
| PIT admission and later factor semantics | AQ | Thin project domain contract only |

OpenBB may remain installed and may be used for diagnostics, developer
exploration, cross-checking, and non-authoritative statement comparison. Its
output cannot directly become `FundamentalEvidence`, a factor, Candidate input,
or P2 evidence. No OpenBB rebinding path was implemented.

```text
AQ_OPENBB_PATCH = NO
AQ_OPENBB_FORK = NO
AQ_OPENBB_MONKEYPATCH = NO
AQ_CUSTOM_COMPANYFACTS_BUILDER = NO
AQ_SEC_FETCHER = NO
AQ_SEC_HTTP_CLIENT = NO
AQ_XBRL_PARSER = NO
AQ_FILING_PARSER = NO
AQ_FINANCIAL_STATEMENT_PARSER = NO
AQ_GENERIC_ETL = NO
AQ_RAG_ENGINE = NO
AQ_VECTOR_DB = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## FundamentalEvidenceV1

The materialized contract is under
`20-intelligence-system/fundamental-factors/evidence-contract/`. It represents
one numeric fact from one SEC accession vintage with one provable market
availability time. It contains exactly eight top-level fields:

```text
schema_version
evidence_id
entity
filing
availability
source
fact
upstream
```

Admission freezes these invariants:

```text
FIRST_AVAILABLE_AT_SOURCE = SEC_ACCEPTANCE_DATETIME_ONLY
ACCESSION_REQUIRED = YES
SOURCE_DOCUMENT_SHA256 = REQUIRED
CURRENT_COMPANYFACTS_AGGREGATE_AS_SOLE_AUTHORITY = PROHIBITED
TICKER_ONLY_EVIDENCE = PROHIBITED
CIK_ONLY_EVIDENCE = INSUFFICIENT_WITHOUT_ACCESSION
AMENDMENT_PROJECTED_BACKWARD = NO
LATER_RESTATEMENT_PROJECTED_BACKWARD = NO
SAME_REPORT_PERIOD_DIFFERENT_ACCESSION = DISTINCT_VINTAGE
OPENBB_ONLY_EVIDENCE_ADMISSION = REJECT
```

The ID is `sha256:` plus SHA-256 over Python `rfc8785` 0.1.4 canonical bytes
for all seven authoritative non-ID fields. Numeric values use the exact
canonical decimal-string V1 policy: no binary float, exponent, redundant zero,
NaN/Infinity, or implicit rounding. Context and dimension identity participate
in the evidence ID when present. Missing optional metadata remains explicit
`null`; it is never fabricated.

The historical-safe fixtures cover Apple 2021 10-K net sales and the distinct
2009 original/amended annual-report vintages. They contain no personal SEC
identity and require no network access.

## Validation

```text
FUNDAMENTAL_EVIDENCE_SCHEMA = PASS
DETERMINISTIC_ID = PASS
FIRST_AVAILABLE_AT_FAIL_CLOSED = PASS
AMENDMENT_VINTAGE = PASS
OPENBB_ONLY_ADMISSION = REJECT_AS_EXPECTED
NEW_CONTRACT_TESTS = 19/19 PASS
RELEVANT_EXISTING_CONTRACT_REGRESSIONS = 52/52 PASS
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
DATASET_BUILT = NO
```

Negative tests reject missing accession or acceptance time, substituted
availability dates, missing source hash, ticker-only identity, amendment
overwrite, reused IDs after accession/time/value changes, dimension collapse,
and OpenBB-only values without SEC provenance.

## Storage boundary

The evidence atom retains accession, acceptance time, source identity/hash,
selected fact, selected context/dimensions, and upstream identity. It does not
require a full SEC mirror or every attachment. Source bytes may be re-downloaded
only when the exact accession-bound document remains available and recomputes
to the retained SHA-256; otherwise admission fails closed.

Private evidence is stored under
`D:/AQ_DATA/P5/openbb-role-closeout-and-fundamental-evidence-contract-001/`.

```text
PRIVATE_REPORT = D:/AQ_DATA/P5/openbb-role-closeout-and-fundamental-evidence-contract-001/contract_summary.json
PRIVATE_REPORT_SHA256 = 3603ae04d87ed92a32875a3aa2a6dfdb49423b4c8f33ccc99189af6f2ed72d0d
```
