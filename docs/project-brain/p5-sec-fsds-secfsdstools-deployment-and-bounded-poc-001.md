# P5 SEC FSDS / secfsdstools Deployment and Bounded POC 001

## Authority

```text
TASK = AUTONOMOUS-QUANT-P5-SEC-FSDS-SECFSDSTOOLS-DEPLOYMENT-AND-BOUNDED-POC-001
PRIOR_HEAD = bbf7b1cbd4d0f4dc6db899e2caf527b9dc7db335
BASELINE_MAIN_SHA = 4f9430319114ebcf5195a87c7d08f4a6e7bfbf40
FINAL_CLASSIFICATION = PASS
P5_SEC_FSDS_SECFSDSTOOLS_DEPLOYMENT_POC = PASS
P5_FOUNDATION = MERGED
P5_FULL_PHASE_COMPLETE = NO
P5_DATASET_BUILD_PILOT_STATUS = OPEN_HYBRID_PATH
CURRENT_DEVELOPMENT_NEXT = P5_HYBRID_HISTORICAL_DATASET_BUILD_PILOT_001
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
P2_V2_SEALED_OOS_ACCESSED = NO
```

The bounded POC proves the selected hybrid path without building the historical
fundamental dataset. SEC FSDS and secfsdstools own bulk candidate discovery;
EdgarTools retains exact filing and evidence admission authority.

## Frozen ownership boundary

```text
P5_BULK_CANDIDATE_CATALOG = SECFSDSTOOLS
P5_EXACT_EVIDENCE_ADMISSION = EDGARTOOLS
EPISODE_SEC_CIK_BINDING_V1_ROLE = DATE_BOUNDED_PROJECT_IDENTITY_AUTHORITY
FUNDAMENTAL_EVIDENCE_V1_ROLE = EXACT_ADMITTED_NUMERIC_EVIDENCE_CONTRACT
P5_FSDS_ACCEPTANCE_ROLE = DISCOVERY_ONLY
P5_FSDS_NUMERIC_VALUE_ROLE = DISCOVERY_DIAGNOSTIC_ONLY
P5_SECFSDSTOOLS_STANDARDIZER_ROLE = NON_AUTHORITATIVE
FSDS_ACCEPTED_AS_FIRST_AVAILABLE_AT = NO
SECFSDSTOOLS_NUM_FLOAT_AS_AUTHORITATIVE_VALUE = NO
SECFSDSTOOLS_STANDARDIZER_AS_ADMISSION_AUTHORITY = NO
```

The future path is:

```text
EpisodeSecCikBindingV1
-> exact CIK
-> secfsdstools FSDS candidate catalog
-> candidate accession list
-> EdgarTools exact accession admission
-> FundamentalEvidenceV1
-> EdgarTools-supported standardization
-> effective session
-> Qlib
```

Effective-session projection, admitted-event Parquet, and the Qlib handoff were
not implemented here. `FundamentalEvidenceV1` was not changed and no V2 was
created.

## Isolated deployment

```text
SECFSDSTOOLS_RUNTIME = DEPLOYED_ISOLATED
PYTHON_VERSION = 3.12.3
SECFSDSTOOLS_VERSION = 2.4.3
SECFSDSTOOLS_AUDITED_SOURCE_SHA = af83c24f999109322d01b4980d207eec67bc749e
PIP_CHECK = PASS
AUTHORITATIVE_ENV_MUTATION = NO
SECFSDSTOOLS_FULL_SEC_IDENTITY_PATH = PASS_PUBLIC_UPSTREAM_API
SECFSDSTOOLS_BOUNDED_PROCESSING_SEAM = PARTIAL_INTERNAL_UPSTREAM_SEAM
SECFSDSTOOLS_TOP_LEVEL_FULL_UPDATE_USED = NO
```

The dedicated Python 3.12 runtime contains the exact 2.4.3 distribution. The
installed distribution provenance and full package freeze are retained in
private evidence. The existing P5, RD-Agent, P3, and P4 environments were not
modified.

The public `UrlDownloader` path accepted the full process-local SEC identity.
The identity was neither printed nor serialized, and the temporary private
configuration was retired after the POC. The top-level all-missing-quarter
updater was not invoked.

Bounded transformation and indexing used upstream
`ToParquetTransformerProcess` and `ReportParquetIndexerProcess` against an
exact preseeded allowlist. No upstream implementation was copied or
subclassed. Because that quarter-bounded seam is not the clean public
top-level update surface, it remains honestly classified
`PARTIAL_INTERNAL_UPSTREAM_SEAM`.

## Bounded source and catalog

```text
POC_QUARTER_COUNT = 3
POC_QUARTERS = 2009Q4; 2010Q1; 2021Q1
POST_2021_QUARTERS_ACCESSED = 0
FSDS_ZIP_COUNT = 3
FSDS_ZIP_BYTES = 107262972
SECFSDSTOOLS_PARQUET_BYTES = 113347531
SECFSDSTOOLS_SQLITE_BYTES = 2654208
FSDS_CANDIDATE_REPORT_COUNT = 7295
FSDS_INDEXED_ACCESSION_COUNT = 7295
FSDS_CIK_COUNT = 5895
FSDS_SELECTED_CANDIDATE_ACCESSION_COUNT = 4
TICKER_LOOKUP_REQUIRED = NO
CURRENT_TICKER_BACKFILL = 0
SECFSDSTOOLS_SQLITE_INDEX_USED = YES_UPSTREAM_INTERNAL
AQ_REPORT_INDEX_DATABASE = NO
```

The three official SEC ZIPs were reused from the prior authorized audit only
after exact SHA-256 verification; this task issued zero new SEC network
requests. Their identities are:

| Quarter | Bytes | SHA-256 |
|---|---:|---|
| 2009Q4 | 4,050,938 | `ad23b114ecb430c3a05ee2f2be799e966a67591ef098c44311b2f1f632d3ea82` |
| 2010Q1 | 5,311,282 | `2a4db2340ab1662d5135d7e17be1a58352c5959017350f0ef2174135f9996125` |
| 2021Q1 | 97,900,752 | `6a776a9fa3d974476101efa9a4bfc531b7cdc2763abd45a6f70dd240a223843b` |

SUB, NUM, PRE, and the upstream report index were exercised. Selection began
from exact CIKs already governed by `EpisodeSecCikBindingV1`; no current ticker
lookup or survivor backfill participated.

## Exact accession admission

```text
CANDIDATE_TO_EXACT_ACCESSION_MATCH = PASS
EXACT_ACCESSION_SAMPLE_COUNT = 2
FUNDAMENTAL_EVIDENCE_PROVIDER = EDGARTOOLS
FUNDAMENTAL_EVIDENCE_REPLAY_COUNT = 4
FSDS_ACCEPTANCE_USED_FOR_ADMISSION = NO
FIRST_AVAILABLE_AT_AUTHORITY = EXACT_SEC_SUBMISSION_ACCEPTANCE
```

The catalog selected four accessions by CIK. Preserved exact SEC submission
bytes were parsed with EdgarTools 5.58.0; no live filing retrieval was needed.
Amazon accession `0001018724-21-000004` and IBM accession
`0001558370-21-001489` matched CIK, accession, form, filing date, and report
period exactly. Those two rows constitute the exact match sample count.

The Apple original/amendment pair is intentionally reported separately:

- `0001193125-09-214859`
- `0001193125-10-012091`

For both, the FSDS nominal period is `2009-09-30`, while the exact filing
period is `2009-09-26`. The mismatch was not normalized away. Exact
EdgarTools/SEC filing authority retained the filing period, accession, source
hash, and acceptance timestamp. The accessions and V1 evidence IDs remain
distinct, and the amendment never projects backward.

```text
HYBRID_AMENDMENT_VINTAGE = PASS
```

FSDS acceptance values differed from exact SEC submission acceptance by
-10, -29, +2, and -23 seconds across the four admissions. FSDS therefore
remains minute-resolution discovery metadata only.

## Numeric and standardization boundary

```text
NUMERIC_PRECISION_COMPARISON = REPRESENTATION_BOUNDARY_PROVEN
SECFSDSTOOLS_FLOAT_VALUE_USED_FOR_EVIDENCE_ID = NO
SECFSDSTOOLS_DEFAULT_STANDARDIZER_USED_FOR_ADMISSION = NO
STANDARDIZATION_AUTHORITY = EDGARTOOLS
```

The selected facts agreed semantically, but the raw FSDS lexical value,
secfsdstools `float64`, and exact EdgarTools canonical decimal string are
different representations. The float was never used to issue an evidence ID,
and no exact decimal was reconstructed from it. The balance-sheet,
income-statement, and cash-flow default secfsdstools standardizers were not
used for admission.

## Value and eliminated duplicate ownership

```text
HYBRID_BULK_PATH_VALUE = PROVEN
AQ_QUARTER_ARCHIVE_ENGINE = NO
AQ_ZIP_EXTRACTION_ENGINE = NO
AQ_RAW_FSDS_TRANSFORM_ENGINE = NO
AQ_REPORT_INDEX_DATABASE = NO
AQ_GENERIC_FSDS_QUERY_ENGINE = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

One upstream-owned three-quarter transform/index exposed 7,295 reports and
selected four CIK-driven candidates for four exact EdgarTools admissions,
without per-accession discovery requests. This proves material catalog value
while preserving exact admission boundaries. AQ does not need to implement a
parallel quarterly archive engine, ZIP extractor, bulk FSDS transformer,
report-index database, or generic FSDS query engine.

EdgarTools MCP was not deployed. The retained recommendation is:

```text
P5_AGENT_INTERFACE_RECOMMENDATION = LOCAL_EDGARTOOLS_MCP_PRIMARY_WITH_SKILL_GUIDANCE_FALLBACK
```

## Validation and safety

```text
P5_CONTRACT_TESTS = 43_PASSED; 29_SUBTESTS_PASSED
REPOSITORY_RUNTIME_CODE_CHANGED = NO
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

The exact P5 identity/evidence contract suite replayed successfully. Runtime
ZIPs, Parquet, SQLite, source documents, private evidence, package environment,
and SEC identity remain outside Git.

```text
PRIVATE_REPORT = poc_summary.json
PRIVATE_REPORT_SHA256 = 97ee6c70b8be9a20a3295993c96a199743f3d441baa33d96c62717cf6cc0c8cf
```
