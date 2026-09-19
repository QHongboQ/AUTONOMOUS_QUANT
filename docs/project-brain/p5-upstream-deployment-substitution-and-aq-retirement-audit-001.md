# P5 upstream deployment substitution and AQ retirement audit 001

## Authority and scope

```text
TASK = AUTONOMOUS-QUANT-P5-UPSTREAM-DEPLOYMENT-SUBSTITUTION-AND-AQ-RETIREMENT-AUDIT-001
AUTHORITATIVE_MAIN = de3c1b8b550a32074b0144b5e24566bca8a6b8d2
DIAGNOSTIC_CENSUS_BRANCH = 5fa00c38d9048e47d0cf4e6c452a00e6a3112dcb
DIAGNOSTIC_CENSUS_BRANCH_ROLE = EVIDENCE_ONLY_NOT_BASE
FULL_P1_EPISODE_COUNT = 832
ADMITTED_BINDING_EPISODE_COUNT = 6
MISSING_AUTHORITY_EPISODE_COUNT = 825
```

This audit pauses custom P5 expansion. It does not repair the 825 diagnostic
gaps, materialize production bindings, build the full historical dataset, or
change accepted P1/P2/P5 authority.

## Isolated deployments and bounded POCs

All deployments are isolated from established P2, P5, and Qlib runtimes.

| Upstream | Runtime/source | POC result | Ownership decision |
|---|---|---|---|
| Valuein | Python 3.14.7; `valuein-sdk` 5.2.0 | Actual authenticated SDK tables exercised | Material identity/fundamental leaf, not whole historical authority |
| RFundamentals | source `d259b4153358d2683e7078b4a4c220b31a02e45b` | Static source POC; R runtime unavailable | Formula/panel/incremental-design oracle only |
| Arelle | Python 3.12.3; `arelle-release` 2.45.1 | Isolated parser load and capability-module audit | EdgarTools primary, Arelle fallback |
| Alphalens-reloaded | Python 3.12.3; 0.4.6 | IC, quantile return, turnover synthetic POC passed | Leaf for turnover/quantile/group/tear-sheet analysis |
| purgedcv | Python 3.12.3; 0.1.6 | PurgedKFold/audit and DSR POC passed | PSR/DSR candidate leaf only; CV splitters not adopted |

The Arelle incomplete-schema fixture loaded the model and failed closed with
`xbrl:schemaImportMissing`. XBRL, dimension, and inline-transform modules are
present; a SEC EFM plugin path was not activated by this bounded POC. No
concrete EdgarTools gap presently requires Arelle as the primary path.

RFundamentals has valuable formula and panel design, but its source claims a
filing-date boundary, contains no `accepted_at` use in the audited source,
resolves a current ticker through a current master, and includes Yahoo price
dependencies. It is therefore not exact AQ PIT authority.

## Valuein historical identity fit

The current SDK exposed security/entity intervals, CIK-bearing entity IDs,
historical membership intervals, filing accessions, amendments, `accepted_at`,
raw facts, standardized concepts, ratios, restatement events, and source
lineage. Its exact 832-episode result is:

```text
P1_EPISODE_COUNT = 832
VALUEIN_EXACT_INTERVAL_MATCH_COUNT = 1
VALUEIN_COMPATIBLE_INTERVAL_MATCH_COUNT = 710
VALUEIN_PARTIAL_INTERVAL_MATCH_COUNT = 41
VALUEIN_AMBIGUOUS_MATCH_COUNT = 3
VALUEIN_NO_MATCH_COUNT = 77
VALUEIN_CIK_AVAILABLE_COUNT = 755
VALUEIN_MEMBERSHIP_AVAILABLE_COUNT = 755
```

The counts reconcile to 832. A compatible interval is evidence, not automatic
authority. Partial, ambiguous, and absent rows remain fail-closed.

The eight controls prevent overclaiming:

| Case | Valuein result | Evidence role |
|---|---|---|
| AAPL | unique CIK 0000320193, containing interval | direct-authority candidate |
| CTL to LUMN | historical CTL row absent | no coverage |
| historical BBBY | old CIK/security row absent | no coverage |
| DRE | unique CIK 0000783280, containing interval | direct-authority candidate |
| old DD | overlaps current CIK 0001666700 only partially | conflict; current-symbol backfill rejected |
| new DD | unique CIK 0001666700, containing interval | direct-authority candidate |
| FB to META | historical FB row absent | no coverage |
| old CEG | old episode row absent | no coverage |

Therefore:

```text
VALUEIN_HISTORICAL_IDENTITY_LAYER = MATERIAL_PARTIAL_REPLACEMENT_ONLY
VALUEIN_SOLE_EPISODE_CIK_AUTHORITY = NO
CURRENT_P5_AUTHORITY_OVERWRITTEN = NO
```

## Valuein fundamentals fit

The POC used the six admitted CIKs and the 14 exact pilot accessions. The SDK
returned 82,235 fact rows, 9,201 ratio rows, 50 restatement rows, and 1,317
non-null acceptance timestamps for the selected issuer route. Ten of the 14
pilot accessions matched. Four removed-issuer filings did not:

```text
0000783280-17-000066
0000783280-18-000012
0001171843-15-002257
0001171843-15-003732
```

Those are the DRE and historical BBBY filings, so the current S&P 500 tier
cannot replace the existing exact EdgarTools historical path.

All frozen 11 metric identities have explicit candidate equivalents with
nonzero rows in the exercised Valuein facts:

```text
Revenue -> TotalRevenue
NetIncome -> NetIncome
Assets -> TotalAssets
Liabilities -> TotalLiabilities
CommonEquity -> StockholdersEquity
NetCashFromOperatingActivities -> OperatingCashFlow
CashAndCashEquivalents -> CashAndEquivalents
CurrentAssetsTotal -> CurrentAssets
CurrentLiabilitiesTotal -> TotalCurrentLiabilities
ShortTermDebt -> ShortTermDebt
LongTermDebt -> LongTermDebt
```

This mapping is a candidate fit, not a silent authority rewrite. Exact
accession, period, numeric/canonical value, amendment, and source-lineage
regressions are required before an adapter can admit evidence.

```text
VALUEIN_ACCEPTED_AT_AVAILABLE_FOR_POC_FILINGS = YES
VALUEIN_FILING_AND_FACT_ACQUISITION = CAN_REPLACE_EXISTING_UPSTREAM_PATH_WHERE_COVERED
VALUEIN_STANDARDIZATION = CAN_REPLACE_AQ_WHERE_EXPLICITLY_MAPPED_AND_REGRESSION_PROVEN
VALUEIN_OVERALL = SUPPLEMENT_ONLY_UNTIL_REMOVED_ISSUER_HISTORY_IS_COVERED
AQ_EFFECTIVE_SESSION_POLICY = KEEP_THIN_DOMAIN
```

AQ retains only:

```text
effective_session = FIRST_XNYS_SESSION_WITH_OPEN_STRICTLY_AFTER_FIRST_AVAILABLE_AT
```

## Factor analysis and certification ownership

- Qlib remains primary for factor dataset/model/experiment execution and IC.
- Alphalens-reloaded is a non-duplicative leaf for quantile returns, turnover,
  group/sector analysis, and tear sheets.
- skfolio remains the one production owner for WalkForward, purged/embargo CV,
  and CPCV.
- `purgedcv` splitters are duplicate and are not adopted. Its public PSR/DSR
  functions are a candidate leaf only, subject to a separate P2 protocol
  authority decision.
- `arch` remains the owner of SPA, RealityCheck, StepM, and MCS.

## Retirement and surviving AQ boundary

The private ownership matrix assigns exactly one production owner to every
audited capability. No code is deleted in this task.

Delete or never implement:

- AQ security master, generic identity inference, or manual 825-episode rules;
- AQ SEC HTTP client/crawler;
- AQ XBRL, Inline XBRL, dimensions, or SEC-transform engines;
- generic statement/standardization, ratio, factor, CV, statistics, or factor
  analysis engines.

Keep as thin domain policy:

- `EpisodeSecCikBindingV1` admission against exact P1 episodes;
- `FundamentalEvidenceV1` immutable evidence/provenance identity;
- explicit frozen 11-metric identity mapping;
- exact XNYS effective-session and membership containment rules;
- fail-closed source precedence and Qlib schema/provenance handoff.

Retire after adapter and regression evidence:

- provider-specific evidence materialization that is fully replaced on the
  admitted route;
- generic Parquet/hash helper ownership duplicated by Parquet plus DVC.

The diagnostic census implementation and the pilot seal remain oracle/test
evidence, not a second production pipeline.

## Minimum adapter plan

1. Valuein identity rows -> deterministic interval candidate relation -> P1
   episode reconciliation -> `EpisodeSecCikBindingV1`. No ticker-only backfill.
2. Valuein filing/fact rows for exact covered accessions -> explicit frozen
   concept aliases -> `FundamentalEvidenceV1` -> AQ session rule ->
   `pandas.merge_asof` -> Qlib. EdgarTools remains primary for uncovered
   historical filings.
3. Existing Qlib factor data -> thin dataframe mapping -> Alphalens leaves.
4. Existing P2 return evidence -> direct purgedcv PSR/DSR calls only after P2
   protocol authorization.

No plugin system, provider registry, security master, data engine, or generic
adapter framework is authorized.

## Private evidence

Root:

`D:\AQ_DATA\P5\upstream-deployment-substitution-and-aq-retirement-audit-001`

```text
upstream_versions.json = sha256:699fd7ee48b37bcacbc3d04aeeec7bd612284249ef255473d95110a0d9bf3d57
valuein_identity_poc.json = sha256:a4590bd9d50dbe0e303c3c0e7773db1479edbea75b6548388e60ff9d0059d2c8
valuein_fundamentals_poc.json = sha256:e30d2dc9cb83341d8b60113ee0fe3ce57c0430dd128e1dc29fb4d34e18cef365
rfundamentals_poc.json = sha256:d125754811a55bdf13f187a1cc1dc4e424c69200116a2d8717d40ec2d22c53d0
arelle_fit.json = sha256:29cc2c0d79263d7e2e9c528044618067a9317fc685a477b9435008d3c327e86b
factor_analysis_fit.json = sha256:850644782a02b54a14a83be5158798d7456227f13d28cc5cb5aab3434d4dbc91
purged_cv_fit.json = sha256:0bfb3041525f1a63864dd9f542f951dd817f4818384f9b958274206cd4b472b5
capability_ownership_matrix.json = sha256:31418830ffbc27c1e3f59d8d802939be4ef836ef63500411ca2464fe8a916c2e
aq_retirement_matrix.json = sha256:5f38430e35dda099fb7c5b63d4297637f9e235bf38cb39fb16a452be7fd7ed93
thin_adapter_plan.json = sha256:37ebeb1db288cedc194ddbba049175af7baa4e42edbb1a29f0978dc64722cec8
```

No credential or token is present in tracked or private reports.

## Final state

```text
UPSTREAM_CAPABILITY_AUDIT_COMPLETE = YES
VALUEIN_DEPLOYMENT_POC = PASS
RFUNDAMENTALS_DEPLOYMENT_POC = EXPLICIT_BLOCKER_R_RUNTIME_UNAVAILABLE_AND_EXACT_PIT_INCOMPATIBLE
ARELLE_FALLBACK_AUDIT = COMPLETE
FACTOR_ANALYSIS_UPSTREAM_AUDIT = COMPLETE
PURGED_CV_UPSTREAM_AUDIT = COMPLETE
AQ_DUPLICATE_PRODUCTION_OWNER_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_VALUEIN_THIN_IDENTITY_AND_FUNDAMENTALS_ADAPTER_001
```
