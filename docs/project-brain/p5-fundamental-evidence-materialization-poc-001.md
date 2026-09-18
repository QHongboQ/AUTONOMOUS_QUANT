# P5 Fundamental Evidence Materialization POC 001

## Outcome

```text
TASK = AUTONOMOUS-QUANT-P5-FUNDAMENTAL-EVIDENCE-MATERIALIZATION-POC-001
P5_FUNDAMENTAL_EVIDENCE_MATERIALIZATION_POC = PASS
P5_PIT_CRITICAL_STACK = SEC_EDGAR_PLUS_EDGARTOOLS
P5_REAL_FUNDAMENTAL_EVIDENCE = MATERIALIZED_HISTORICAL_SAFE_POC
P5_OPENBB_SEC_ROLE = SUPPLEMENTARY_NON_AUTHORITATIVE
P5_OPENBB_AUTHORITATIVE_RECORD_COUNT = 0
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_DEVELOPMENT_NEXT = P5_FUNDAMENTAL_HISTORICAL_DATASET_DESIGN_001
FINAL_CLASSIFICATION = PASS
```

The POC materialized real, accession-bound historical SEC XBRL facts through
EdgarTools 5.58.0 into the existing `FundamentalEvidenceV1` contract. The
private EDGAR identity was loaded from its existing mode-600 location and was
never printed, serialized, or committed. Every selected filing has SEC
acceptance time no later than `2021-12-31T23:59:59Z`.

The stale current-state line from before identity configuration is retained
only as explicitly superseded history:

```text
P5_LIVE_SEC_POC = HISTORICAL_SUPERSEDED_BLOCKED_IDENTITY_NOT_CONFIGURED
P5_BRAIN_STALE_IDENTITY_BLOCKER = RESOLVED
P5_SEC_LIVE_IDENTITY = CONFIGURED_LOCAL_PRIVATE
P5_EDGARTOOLS_LIVE_SEC = PASS
```

Operational P2 authority did not change:

```text
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
P2_V2_SEALED_OOS_ACCESSED = NO
```

## Deterministic sample and facts

The issuer sample is fixed independently of performance: Apple
(`0000320193`), Microsoft (`0000789019`), Amazon (`0001018724`), and IBM
(`0000051143`). The latest eligible annual filing was selected by SEC
acceptance time and accession; Apple also supplied the latest eligible 10-Q.
The preserved Apple original/amendment pair is
`0001193125-09-214859` / `0001193125-10-012091`.

```text
MATERIALIZED_RECORD_COUNT = 20
DISTINCT_CIK_COUNT = 4
DISTINCT_ACCESSION_COUNT = 7
DISTINCT_CONCEPT_COUNT = 6
APPLE_2021_10K_NET_SALES = 365817000000 USD
DIMENSION_LIVE_SAMPLE = PASS
```

For each annual filing, the POC projected revenue/net sales, net income, total
assets, and operating cash flow using the exact concepts actually present in
that accession. It did not introduce a universal concept mapper. The Apple
10-Q adds one quarterly revenue atom. One natural dimension-bearing Apple
revenue fact preserves `srt:ProductOrServiceAxis` and its context identity.

The original Apple annual report and its amendment preserve the same report
period but distinct accessions, acceptance times, values, and evidence IDs.
The amendment is available only from its own acceptance time and is never
projected backward.

## Thin ownership boundary

The only repository runtime addition is the pure
`AQ_THIN_EVIDENCE_MATERIALIZER`, a 126-LOC projection from one already-parsed
EdgarTools filing/fact pair into the frozen contract. Its public responsibility
is field projection, exact decimal admission, context/dimension preservation,
and contract validation. It cannot fetch, crawl, parse SEC/XBRL, select an
issuer history, persist records, or schedule work.

```text
UPSTREAM_REJECTION_REASON = PROJECT_SPECIFIC_EVIDENCE_CONTRACT_PROJECTION_ONLY
AQ_SEC_FETCHER = NO
AQ_SEC_HTTP_CLIENT = NO
AQ_XBRL_PARSER = NO
AQ_FILING_PARSER = NO
AQ_FINANCIAL_STATEMENT_PARSER = NO
AQ_GENERIC_ETL = NO
AQ_FUNDAMENTAL_ENGINE = NO
AQ_RAG_ENGINE = NO
AQ_VECTOR_DB = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

SEC EDGAR owns source bytes and acceptance time. EdgarTools owns filing and
XBRL retrieval/parsing. AQ owns only its project-specific immutable admission
projection. No materialized record identifies OpenBB as either source or
parser.

## Validation and replay

```text
SCHEMA_VALID_COUNT = 20
PYDANTIC_VALID_COUNT = 20
ID_RECOMPUTE_PASS_COUNT = 20
UNIQUE_EVIDENCE_ID_COUNT = 20
FIRST_AVAILABLE_AT_POLICY = PASS
SOURCE_DOCUMENT_HASH_PROVEN = YES
REPLAY_RECORD_COUNT_MATCH = YES
REPLAY_EVIDENCE_ID_SET_MATCH = YES
REPLAY_BYTE_IDENTITY = YES
AMENDMENT_VINTAGE_PROOF = PASS
CONTRACT_AND_MATERIALIZER_TESTS = 25/25 PASS
RELEVANT_EXISTING_CONTRACT_REGRESSIONS = 52/52 PASS
TOTAL_TEST_RESULT = 77/77 PASS
```

The second materialization pass used the same frozen accession-bound bytes and
produced byte-identical records and the same evidence-ID set. No generated
timestamp or random identifier participates in evidence identity.

## Storage and non-actions

Private evidence is under
`D:/AQ_DATA/P5/fundamental-evidence-materialization-poc-001/`. Five bounded
candidate submissions totaling 108,050,632 bytes were downloaded; existing
Apple sources were reused. The selected sample uses seven source documents.
Twenty private record files total 30,160 bytes. No filing bytes or private
records entered Git.

```text
OPENBB_AUTHORITATIVE_RECORD_COUNT = 0
OPENBB_ONLY_EVIDENCE_ADMISSION = 0
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
QLIB_DATASET_CREATED = NO
MODEL_TRAINING = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

```text
PRIVATE_REPORT = D:/AQ_DATA/P5/fundamental-evidence-materialization-poc-001/poc_summary.json
PRIVATE_REPORT_SHA256 = b28925f898594b8465bc7d97ea1c19d62c1cad59f208662cd84f1d1bf56ecd88
```
