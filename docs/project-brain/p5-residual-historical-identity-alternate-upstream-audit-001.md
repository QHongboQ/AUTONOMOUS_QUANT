# P5 Residual Historical Identity Alternate-Upstream Audit 001

## Authority and scope

```text
TASK = AUTONOMOUS-QUANT-P5-VALUEIN-IDENTITY-CLOSEOUT-MERGE-AND-RESIDUAL-HISTORICAL-IDENTITY-UPSTREAM-AUDIT-001
INITIAL_MAIN = ba3d988bf8c92dcefa3526025b20417921b27e11
VALUEIN_CLOSEOUT_PR = 57
VALUEIN_SOURCE_HEAD = 674fb4de1a26caa1714658896b1125c665914f65
VALUEIN_CLOSEOUT_MERGE_SHA = b226af16514cb32d2b4f9d3d6e82582f4283183a
VALUEIN_CLOSEOUT_MERGED_AT_UTC = 2026-09-19T08:01:42Z
AUDIT_BASE = b226af16514cb32d2b4f9d3d6e82582f4283183a
TOTAL_P1_EPISODES = 832
VALUEIN_ADMITTED = 1
RESIDUAL_EPISODES = 831
AUDIT_PRODUCTION_LOC_ADDED = 0
```

PR #57 passed the 59 affected tests, Ruff, `git diff --check`, exact head/base checks, and the credential/private-evidence gate before squash merge. `FundamentalEvidenceV1` implementation, schema, and core tests remained byte-identical to the pre-merge main. Valuein remains an exact-only external identity evidence leaf; its fundamentals role remains oracle-only and EdgarTools remains the exact fundamentals authority.

## Existing SEC and EdgarTools route

[SEC submissions JSON](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) supplies CIK-scoped filings, current entity metadata, former names, current ticker/exchange metadata, accessions, and filing dates. [SEC's access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) explicitly describes the ticker files as periodically updated and does not guarantee their accuracy or scope. EdgarTools 5.58.0 exposes those SEC surfaces, but its bundled ticker lookup is a current SEC mirror rather than historical interval authority.

The residual replay measured:

```text
SEC_CURRENT_TICKER_UNIQUE_MATCH = 606
SEC_CURRENT_TICKER_NO_MATCH = 225
SEC_CURRENT_TICKER_AMBIGUOUS = 0
VALUEIN_CURRENT_MAPPING_COMPARABLE = 590
VALUEIN_CURRENT_MAPPING_EXACT_SET = 579
VALUEIN_CURRENT_MAPPING_DISAGREEMENT = 11
EXISTING_P1_SEC_DATE_VALID_BINDINGS = 6
SEC_EDGARTOOLS_EXACT_INTERVAL_OWNER = NO
SEC_EDGARTOOLS_IDENTITY_RESULT = SEC_EDGARTOOLS_CORROBORATION_ONLY
```

The 606 current-symbol matches are not admitted. Historical BBBY resolves to a different present-day CIK; old CEG resolves to the later CEG issuer; and old DD resolves to new DD. SEC accessions and cover-page observations can corroborate a known episode/CIK relation, but sparse filings do not create a ticker interval. The already-accepted six date-bounded P1/SEC relations therefore remain the only proven residual coverage, leaving 825 unresolved.

## Sharadar / Nasdaq Data Link

Nasdaq's official [Tables API](https://docs.data.nasdaq.com/docs/api-and-analysis-tools-for-tables-data) requires an API key, and [data organization documentation](https://docs.data.nasdaq.com/docs/data-organization) classifies Sharadar Core Fundamentals as premium. Anonymous metadata requests succeeded for `SHARADAR/TICKERS`, `SHARADAR/ACTIONS`, and `SHARADAR/SP500`, while every bounded AAPL row request returned HTTP 403. No Nasdaq Data Link key, local credential, SDK, or licensed cache was present.

`TICKERS` permanent identity/reference metadata plus `ACTIONS` and `SP500` event history is a credible interval-leaf candidate, but two claims remain unproven without authenticated rows: full 831 coverage and a deterministic upstream CIK relation. AQ must not bridge those gaps through ticker/name/price matching.

```text
SHARADAR_RESULT = ACCESS_BLOCKED_FOR_FULL_831_POC
SHARADAR_RESIDUAL_COVERAGE = NOT_MEASURABLE_WITHOUT_SUBSCRIPTION
SHARADAR_DIRECT_CIK_AUTHORITY = NOT_PROVEN
```

## CRSP / Compustat / WRDS

[CRSP](https://www.crsp.org/research/) documents permanent PERMNO security identity, active/inactive coverage, and continuity through name changes and corporate events. Its stock guide documents date-effective ticker, name, CUSIP, exchange, status, and delisting structures. WRDS documents Compustat [`sec_history` and `sec_idhist`](https://wrds-www.wharton.upenn.edu/pages/wrds-research/database-linking-matrix/using-compustat-historical-identifier-notebook/) effective-date histories and official [SEC-to-Compustat link tables](https://wrds-www.wharton.upenn.edu/pages/wrds-research/database-linking-matrix/linking-sec-with-compustat/) for GVKEY/CIK and CIK/CUSIP.

This is the strongest documented whole-capability candidate: CRSP owns the permanent security interval, Compustat owns date-valid identifiers, and WRDS SEC linking owns the CIK bridge. No WRDS credentials, `.pgpass`, client, or local CRSP/Compustat data were present, so the 831-case POC was correctly left unmeasured rather than inferred.

```text
CRSP_SECURITY_INTERVAL_AUTHORITY = DOCUMENTED_ACCESS_BLOCKED
CRSP_CIK_BRIDGE_AUTHORITY = WRDS_COMPUSTAT_SEC_LINKING_DOCUMENTED_ACCESS_BLOCKED
CRSP_SP500_MEMBERSHIP_ROLE = DOCUMENTED_ACCESS_BLOCKED
CRSP_DELISTER_RENAME_ROLE = DOCUMENTED_ACCESS_BLOCKED
CRSP_WRDS_RESULT = ACCESS_BLOCKED_FULL_POC_DOCUMENTED_WHOLE_CAPABILITY_CANDIDATE
```

## OpenFIGI and SEC mapping utilities

[OpenFIGI's API](https://www.openfigi.com/api/documentation) maps supported identifiers into FIGI, share-class FIGI, composite FIGI, ticker, name, exchange, and security descriptors. It exposes no historical valid-from/valid-to relation and no CIK. The frozen 47-case POC returned four results and explicitly recorded `historical_asof_authority=false`; no new requests were needed. Existing Valuein candidates expose 583 FIGIs across the residual inventory, but they remain supporting identifiers only.

`sec-cik-mapper` mirrors SEC's current mappings. Its repository is archived, latest release is 2.1.0 from 2022-01-09, last push was 2025-02-28, and neither it nor the inspected public forks/successors provides historical ticker intervals. Its 606 current-symbol matches therefore have zero historical admission count.

```text
OPENFIGI_RESULT = CORROBORATION_ONLY
OPENFIGI_HISTORICAL_DATE_VALID_MATCH = 0
SEC_CIK_MAPPER_RESULT = REJECT_CURRENT_ONLY_AND_ARCHIVED
MAINTAINED_SUCCESSOR_WITH_HISTORICAL_INTERVALS = NONE_FOUND
```

LSEG Open PermID remains a possible permanent-identifier bridge: its official search surface supports organization/instrument identities and CIK lookup. No local token or date-valid 831-case proof existed, so it is deferred rather than adopted.

## Control cases

| Case | Result | Critical observation |
|---|---|---|
| AAPL | existing corroborated binding | Current SEC mapping agrees, but admission also uses bounded P1/SEC evidence. |
| CTL → LUMN | existing exact binding | Current CTL lookup is absent; LUMN backfill is prohibited. |
| historical BBBY | existing corroborated binding | Current SEC mapping resolves the reused symbol to the wrong CIK for the historical episode. |
| DRE | existing exact binding | SEC evidence corroborates the acquisition boundary; it does not manufacture it. |
| old DD | fail closed | Current DD belongs to the later issuer/security. |
| new DD | existing exact binding | The date-bounded relation distinguishes it from old DD. |
| FB → META | existing corroborated binding | Current FB mapping is absent; SEC/P1 continuity is retained. |
| old CEG | missing authority | Current CEG belongs to a later issuer/security. |
| FRC | Valuein exact admission | Sole Valuein admission; excluded from the residual 831. |

## One-owner decision

No new production owner is admitted because the only candidates capable of materially expanding coverage were access-blocked. The minimum preferred licensed POC is:

```text
PREFERRED_PRIMARY_SECURITY_INTERVAL_OWNER = CRSP_US_STOCK_PLUS_COMPUSTAT_SEC_IDHIST
PREFERRED_CIK_BRIDGE_OWNER = WRDS_SEC_GVKEY_CIK_AND_CIK_CUSIP_LINK_TABLES
SELECTED_CORROBORATION_OWNER = SEC_EDGAR_EDGARTOOLS_PLUS_OPENFIGI_SUPPORTING_ONLY
P1_EPISODE_AUTHORITY = AQ_EXISTING_DOMAIN_FACT
AQ_ADMISSION_POLICY = EXACT_JOIN; DATE_CONTAINMENT; FAIL_CLOSED_CONFLICT
```

This is a recommendation for an access decision and authenticated POC, not deployment. Sharadar remains the retail-access alternative to compare once an authorized subscription is available, but its CIK bridge must be upstream-provided and exact.

```text
COMBINED_UPSTREAM_RESIDUAL_COVERAGE = 6_OF_831_PROVEN; 825_UNRESOLVED
AQ_MANUAL_IDENTITY_RULE_COUNT = 0
AQ_SECURITY_MASTER_CREATED = NO
AQ_GENERIC_IDENTITY_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

Private evidence is sealed under `D:\AQ_DATA\P5\residual-historical-identity-alternate-upstream-audit-001`. The checksum-ledger SHA-256 is `a7d14051c37e634d28f1cf14260db77fb748dadb5e8e8d75fa2544cadd47eb6b`; no credentials or tokens are recorded.

## Decision

```text
VALUEIN_CLOSEOUT_MERGED = YES
RESIDUAL_IDENTITY_AUDIT_COMPLETE = YES
RESIDUAL_831_FIT_MEASURED = EXPLICIT_ACCESS_BLOCKERS_FOR_SHARADAR_AND_CRSP_WRDS
COMBINED_UPSTREAM_FIT_AUDITED = YES
CURRENT_DEVELOPMENT_NEXT = P5_RESIDUAL_HISTORICAL_IDENTITY_ACCESS_AND_DATA_TIER_DECISION_001
FINAL_CLASSIFICATION = PASS_AUDIT_COMPLETE_ACCESS_DATA_TIER_DECISION_REQUIRED
```
