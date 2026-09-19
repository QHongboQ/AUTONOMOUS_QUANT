# P5 Valuein Scope Contraction and Identity-Only Closeout

## Authority

```text
TASK = AUTONOMOUS-QUANT-P5-VALUEIN-SCOPE-CONTRACTION-AND-IDENTITY-ONLY-CLOSEOUT-001
BASE_MAIN = ba3d988bf8c92dcefa3526025b20417921b27e11
PRIOR_HEAD = 79ba943062bd4db21e337ad8fb43136813708f4c
CAPABILITY = P5_BOUNDED_HISTORICAL_IDENTITY_EVIDENCE
UPSTREAM_OWNER = VALUEIN_IDENTITY_LEAF; EDGARTOOLS_EXACT_FUNDAMENTALS
OWNERSHIP_MODE = UPSTREAM_LEAF
AQ_IMPLEMENTATION_ALLOWED = YES
AQ_ALLOWED_SCOPE = DIRECT_IDENTITY_CLASSIFICATION; EXACT_CONTRACT_ADMISSION
CUSTOM_ENGINE_REQUIRED = NO
```

P1 `InstrumentEpisodeV1` remains the historical identity authority. Valuein is bounded external evidence, not a historical security master, sole Episode-to-CIK authority, fundamentals authority, or generic provider.

## Identity-only production role

The tracked Valuein module now contains only `ValueinIdentityDecision`, `classify_valuein_identity`, `admit_exact_valuein_binding`, and the minimum parsing/validation helpers those functions require. It has no SEC/fundamentals construction, metric mapping, source-precedence routing, provider registry, security master, identity engine, or generic adapter framework.

The immutable `snapshot_20260918` replay remains:

```text
TOTAL_P1_EPISODES = 832
VALUEIN_EXACT_COUNT = 1
VALUEIN_COMPATIBLE_CANDIDATE_COUNT = 710
VALUEIN_ADMITTED_BINDING_COUNT = 1
VALUEIN_PARTIAL_COUNT = 41
VALUEIN_AMBIGUOUS_COUNT = 3
VALUEIN_CONFLICT_COUNT = 0
VALUEIN_NO_MATCH_COUNT = 77
VALUEIN_UNRESOLVED_IDENTITY_COUNT = 831
```

The sole admitted relation remains the exact FRC episode (`P1EP-7c61a918cb137912cc24bae07274c8bb632952f5caf937488ad2523b7d82f16c`) to CIK `0001132979`, valid 2019-01-02 through 2023-05-04. No admission count changed in this closeout.

```text
VALUEIN_IDENTITY_ROLE = EXACT_ONLY_EXTERNAL_EVIDENCE_LEAF
VALUEIN_EXACT_AUTO_ADMISSION = ONLY_AFTER_ALL_EXISTING_CONTRACT_INVARIANTS_PASS
VALUEIN_COMPATIBLE_MATCH_AUTO_ADMISSION = NO
VALUEIN_PARTIAL_MATCH_AUTO_ADMISSION = NO
VALUEIN_AMBIGUOUS_MATCH_AUTO_ADMISSION = NO
VALUEIN_NO_MATCH_BACKFILL = NO
VALUEIN_TICKER_ONLY_BACKFILL = NO
CURRENT_SYMBOL_BACKFILL = NO
```

## Fundamentals contraction

The audit remains authoritative: Valuein identifies 10 of 14 pilot accessions but admits 0 of 14 into `FundamentalEvidenceV1`. The tested cache lacks independently verifiable immutable SEC source-document hashes, lacks filing rows for the covered pilot accessions, and includes an acceptance-time disagreement for accession `0000018926-16-000047`.

The premature Valuein production union in `FundamentalEvidenceV1`, the hypothetical Valuein fact materializer, the source-precedence function, the production 11-metric map, and their synthetic-only tests were removed. The contract and schema are byte-identical to `BASE_MAIN`; existing EdgarTools evidence identities remain unchanged.

The audited 11-metric correspondence remains private/Brain oracle evidence and is not a production mapping:

```text
VALUEIN_THIN_FUNDAMENTALS_ADAPTER = NOT_ADOPTED_MISSING_IMMUTABLE_PROVENANCE
VALUEIN_FUNDAMENTALS_PRODUCTION_CODE = 0
VALUEIN_FUNDAMENTALS_PRODUCTION_ROLE = NONE
VALUEIN_FUNDAMENTALS_ORACLE_ROLE = YES
VALUEIN_11_METRIC_MAPPING = ORACLE_EVIDENCE_ONLY
FUNDAMENTAL_EVIDENCE_V1_VALUEIN_EXPANSION = REVERTED
FUNDAMENTAL_EVIDENCE_V1_VALUEIN_PROVIDER_ADMISSION = NO
EDGARTOOLS_EXACT_FUNDAMENTALS_AUTHORITY = PRESERVED
SECFSDSTOOLS_BULK_CANDIDATE_CATALOG = YES
VALUEIN_GAP_REPAIR_WORK = STOP
```

## Retirement and ownership

The prior deletion of these unreferenced generic helpers remains valid:

- `aq_hybrid_fundamentals.write_exact_event_parquet` — PyArrow owns Parquet writing at explicit materialization boundaries;
- `aq_hybrid_fundamentals.canonical_sha256` — DVC/native SHA-256 evidence owns artifact identity;
- `aq_hybrid_fundamentals.artifact_identity` — same DVC/native ownership.

Their two implementation-specific tests remain retired. Repository search found no authoritative runtime import. The EdgarTools materializer, binding/evidence contracts, effective-session rule, episode/session eligibility, consolidation, `pandas.merge_asof` projection, frozen fundamental semantics, provenance projection, pilot seal oracle, and Qlib handoff remain thin domain boundaries.

```text
AQ_DUPLICATE_PRODUCTION_OWNER_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
AQ_SECURITY_MASTER = NO
AQ_IDENTITY_ENGINE = NO
AQ_PROVIDER_FRAMEWORK = NO
AQ_GENERIC_ADAPTER_FRAMEWORK = NO
AQ_FUNDAMENTAL_ENGINE = NO
AQ_STANDARDIZATION_ENGINE = NO
AQ_XBRL_ENGINE = NO
AQ_GENERIC_ETL = NO
AQ_GENERIC_ASOF_ENGINE = NO
```

## Validation and safety

```text
VALUEIN_IDENTITY_TESTS = 6/6_PASS
FUNDAMENTAL_EVIDENCE_AND_MATERIALIZER_TESTS = 25/25_PASS
EPISODE_SEC_CIK_BINDING_TESTS = 18/18_PASS
HYBRID_FUNDAMENTALS_TESTS = 10/10_PASS
RUFF = PASS
DIFF_CHECK = PASS
EXISTING_EDGARTOOLS_EVIDENCE_IDENTITY_BYTES_UNCHANGED = YES
AQ_EFFECTIVE_SESSION_POLICY_UNCHANGED = YES
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

Private evidence remains under `D:\AQ_DATA\P5\valuein-thin-identity-and-fundamentals-adapter-001`. Historical adapter evidence is preserved; the scope-contraction report and checksum ledger record the identity-only production decision. The scope-contraction checksum-ledger SHA-256 is `0f87041631688c4810b638008d0bb91f9e0d0ce895ebf535aab5126a6631d171`. No credentials or provider tokens are present.

## Decision

```text
VALUEIN_THIN_IDENTITY_ADAPTER = PASS
VALUEIN_IDENTITY_ROLE = EXACT_ONLY_EXTERNAL_EVIDENCE_LEAF
VALUEIN_ADMITTED_BINDING_COUNT = 1
VALUEIN_UNRESOLVED_IDENTITY_COUNT = 831
VALUEIN_THIN_FUNDAMENTALS_ADAPTER = NOT_ADOPTED_MISSING_IMMUTABLE_PROVENANCE
VALUEIN_FUNDAMENTALS_PRODUCTION_ROLE = NONE
VALUEIN_FUNDAMENTALS_ORACLE_ROLE = YES
FUNDAMENTAL_EVIDENCE_V1_VALUEIN_EXPANSION = REVERTED
EDGARTOOLS_EXACT_FUNDAMENTALS_AUTHORITY = PRESERVED
CURRENT_DEVELOPMENT_NEXT = P5_RESIDUAL_HISTORICAL_IDENTITY_ALTERNATE_UPSTREAM_AUDIT_001
FINAL_CLASSIFICATION = PASS_VALUEIN_IDENTITY_ONLY_CLOSEOUT
```

The next task targets only the unresolved compatible, partial, ambiguous, no-match, and conflict populations through mature upstream ownership. It must not return to custom AQ identity inference or Valuein fundamentals repair.
