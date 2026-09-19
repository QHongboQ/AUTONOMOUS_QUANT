# P5 Valuein Thin Identity and Fundamentals Adapter 001

## Authority

```text
TASK = AUTONOMOUS-QUANT-P5-VALUEIN-THIN-IDENTITY-AND-FUNDAMENTALS-ADAPTER-001
BASE_MAIN = ba3d988bf8c92dcefa3526025b20417921b27e11
CAPABILITY = P5_HISTORICAL_IDENTITY_AND_COVERED_HISTORICAL_FUNDAMENTALS_ACQUISITION
UPSTREAM_OWNER = VALUEIN_PLUS_EDGARTOOLS_EXACT_FALLBACK
OWNERSHIP_MODE = UPSTREAM_LEAF_OR_UPSTREAM_WHOLE_WHERE_CONTRACT_COMPLETE
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = YES
AQ_ALLOWED_SCOPE = THIN_ADAPTER; CONTRACT_VALIDATION; PROJECT_ADMISSION_POLICY; EXPLICIT_FIELD_MAPPING; SOURCE_PRECEDENCE; PROVENANCE_PROJECTION
CUSTOM_ENGINE_REQUIRED = NO
```

P1 `InstrumentEpisodeV1` remains the historical identity authority. Valuein is external evidence, not an alternate security master. SEC EDGAR source identity and the existing `FundamentalEvidenceV1` invariants remain mandatory. EdgarTools remains the exact historical fallback.

## Implemented boundary

One direct module maps Valuein rows into existing contracts. It contains no provider registry, generic adapter/router, security master, identity engine, standardization engine, SEC client, or fallback engine.

The identity path classifies first and admits only an exact, unambiguous security/CIK interval with containing historical membership evidence. The fundamentals path uses a fixed 11-concept map and accepts a Valuein row only when exact accession, CIK, form, acceptance time, period, value, amendment state, upstream identity, and SEC source-document SHA-256 can all be retained truthfully.

The existing `FundamentalEvidenceV1` upstream field is now a strict discriminated union for EdgarTools and Valuein. Existing EdgarTools fixture identities remain unchanged.

## Identity result

The direct adapter was replayed against all 832 P1 episodes and the immutable `snapshot_20260918` Valuein rows:

```text
TOTAL_P1_EPISODES = 832
VALUEIN_EXACT_COUNT = 1
VALUEIN_COMPATIBLE_CANDIDATE_COUNT = 710
VALUEIN_ADMITTED_BINDING_COUNT = 1
VALUEIN_PARTIAL_COUNT = 41
VALUEIN_AMBIGUOUS_COUNT = 3
VALUEIN_CONFLICT_COUNT = 0
VALUEIN_NO_MATCH_COUNT = 77
VALUEIN_UNRESOLVED_COUNT = 831
```

The sole admitted record is the exact FRC episode (`P1EP-7c61a918cb137912cc24bae07274c8bb632952f5caf937488ad2523b7d82f16c`) bound to CIK `0001132979` for 2019-01-02 through 2023-05-04. Its `EpisodeSecCikBindingV1` identifier is `sha256:94c5a0e288982bdfa02317e68616f9d574b6c0002731c56df0bfcee46b83a847`; the evidence includes the combined security/membership snapshot identity `c8ec61502757b84c5b7cc3c627a7226c218a1f74fb5d4d2cd97c9c220b367a26`.

The eight AAPL, CTL/LUMN, historical BBBY, DRE, old DD, new DD, FB/META, and old CEG controls retain their audited boundaries. In particular, none of the 710 compatible candidates is silently promoted.

```text
VALUEIN_COMPATIBLE_MATCH_AUTO_ADMISSION = NO
VALUEIN_PARTIAL_MATCH_AUTO_ADMISSION = NO
VALUEIN_AMBIGUOUS_MATCH_AUTO_ADMISSION = NO
VALUEIN_NO_MATCH_BACKFILL = NO
VALUEIN_TICKER_ONLY_BACKFILL = NO
```

## Fundamentals result

The frozen Valuein evidence still identifies 10 of the 14 pilot accessions and exposes rows for the fixed 11 metrics. It does not, however, retain the independently verifiable SEC source-document SHA-256 needed by `FundamentalEvidenceV1`; the frozen filing cache also lacks filing rows for those 10 covered pilot accessions. The cross-source comparison additionally found an exact-acceptance-time disagreement for accession `0000018926-16-000047` (Valuein facts report midnight on the filing date while the exact EdgarTools evidence records `2016-02-24T22:39:52Z`).

No provenance field was fabricated and no Valuein fact was admitted:

```text
PILOT_ACCESSION_COUNT = 14
VALUEIN_ACCESSION_COVERED_COUNT = 10
VALUEIN_CONTRACT_ADMITTED_ACCESSION_COUNT = 0
EDGARTOOLS_FALLBACK_ACCESSION_COUNT = 14
VALUEIN_EDGARTOOLS_REGRESSION_RESULT = EXPLICIT_BLOCKER_MISSING_IMMUTABLE_PROVENANCE_AND_ACCEPTANCE_TIME_DISAGREEMENT
EDGARTOOLS_EXACT_FALLBACK_PRESERVED = YES
FROZEN_11_METRIC_MAPPING_EXPLICIT = YES
```

This is a bounded upstream-data/provenance gap, not permission to weaken the evidence contract or add a generic router.

## Retirement and ownership

Three unreferenced generic helpers were deleted from the hybrid dataset module:

- `write_exact_event_parquet` — Parquet writing remains owned by PyArrow at explicit materialization boundaries;
- `canonical_sha256` — artifact identity remains owned by DVC/native SHA-256 evidence;
- `artifact_identity` — same DVC/native ownership.

Their two implementation-specific tests were also retired. The EdgarTools materializer cannot be retired because all 14 pilot accessions still require its exact path. `seal_pilot.py` remains oracle/test evidence. The existing binding/evidence contracts, effective-session policy, episode/session eligibility, consolidation, `pandas.merge_asof` projection, frozen metric semantics, provenance projection, and Qlib handoff remain thin domain boundaries.

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
VALUEIN_ADAPTER_TESTS = 13/13_PASS
FUNDAMENTAL_EVIDENCE_AND_MATERIALIZER_TESTS = 26/26_PASS
EPISODE_SEC_CIK_BINDING_TESTS = 18/18_PASS
HYBRID_FUNDAMENTALS_TESTS = 10/10_PASS
RUFF = PASS
AQ_EFFECTIVE_SESSION_POLICY_UNCHANGED = YES
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

Private evidence is under `D:\AQ_DATA\P5\valuein-thin-identity-and-fundamentals-adapter-001` and includes the full 832-episode accounting, controls, sole admitted binding, 14-accession comparison, source precedence, retirement scan/execution, regression result, and checksums. The checksum ledger SHA-256 is `db01fd29dc2f970e33574914c18b3ce53441d84aa877e41c1e656c55cdf8b8bc`. It contains no credentials or provider tokens.

## Decision

```text
VALUEIN_THIN_IDENTITY_ADAPTER = PASS
VALUEIN_THIN_FUNDAMENTALS_ADAPTER = EXPLICIT_BLOCKER_MISSING_IMMUTABLE_PROVENANCE
AQ_RETIREMENT_SCAN_COMPLETE = YES
AQ_REDUNDANT_COMPONENTS_RETIRED_OR_EXPLICITLY_BLOCKED = YES
CURRENT_DEVELOPMENT_NEXT = P5_VALUEIN_ADAPTER_GAP_ADJUDICATION_001
FINAL_CLASSIFICATION = PASS_BOUNDED_ADAPTER_WITH_EXPLICIT_VALUEIN_PROVENANCE_BLOCKER
```

The next task may adjudicate the Valuein provenance/acceptance-time gap and the 831 non-admitted identity episodes. It must not broaden AQ code as the default response.
