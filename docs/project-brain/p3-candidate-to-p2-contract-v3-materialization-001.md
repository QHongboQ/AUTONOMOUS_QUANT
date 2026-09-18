# P3 Candidate-to-P2 Contract V3 Materialization 001

## Result

```text
P3_CANDIDATE_TO_P2_CONTRACT_V3 = MATERIALIZED
V3_TOP_LEVEL_FIELD_COUNT = 8
PRODUCER_NEUTRAL = YES
SUPPORTED_PRODUCERS = RD_AGENT; FORMULAIC_ALPHA
REAL_CANDIDATES_MATERIALIZED = 17
CANDIDATES_SCHEMA_VALID = 17
CANDIDATE_ID_RECOMPUTE_PASS = 17
CANDIDATE_ID_UNIQUE = 17
FAKE_IDENTITIES_CREATED = 0
CURRENT_P2_PROTOCOL_ELIGIBILITY = INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION
CERTIFIED_CANDIDATE_COUNT = 0
CURRENT_NEXT = P3_CANDIDATE_V3_P2_ELIGIBILITY_AND_PHASE_CLOSEOUT_AUDIT_001
```

The new V3 contract preserves exactly eight top-level fields while replacing
the RD-Agent-only producer field with closed `RD_AGENT` and
`FORMULAIC_ALPHA` branches. The RD-Agent research/artifact/runtime branches
reference immutable V1/V2 definitions, preserving their strict source, wheel,
environment, LLM, trace, embedding, DVC, model, and prediction requirements.
Candidate V1 and V2 were not changed.

## Formulaic instances

Exactly one V3 Candidate was materialized for each of the 17 frozen AlphaGen
expressions. Every instance binds its exact expression and origin provenance,
real FINISHED Qlib recorder, deterministic run configuration, durable native
prediction bytes, evaluation evidence, sealed DVC identity, provider/dataset
authority, and reconstructed runtime freeze.

```text
FORMULAIC_PRODUCER_COUNT = 17
QLIB_FINISHED_RECORDER_COUNT = 17
PREDICTION_IDENTITY_COUNT = 17
DVC_SEAL_IDENTITY_COUNT = 17
RUNTIME_FREEZE_IDENTITY_COUNT = 17
ONE_CANDIDATE_PER_EXPRESSION = YES
SERIALIZED_MODEL_STATUS = NOT_PERSISTED_BY_UPSTREAM
QLIB_NATIVE_RENDERED_CONFIG = ABSENT_NOT_FABRICATED
QLIB_EXECUTION_CONFIG_AUTHORITY = DETERMINISTIC_RUN_CONFIG_JSON
```

No serialized model hash was invented. The closed artifact union permits no
identity alongside `NOT_PERSISTED_BY_UPSTREAM`.

## RFC 8785 and validation

Candidate IDs are SHA-256 over upstream RFC 8785 JCS bytes for exactly the
seven non-`candidate_id` top-level fields. The isolated upstream dependency is
Python `rfc8785` 0.1.4; its wheel SHA-256 is
`520d690b448ecf0703691c76e1a34a24ddcd4fc5bc41d589cb7c58ec651bcd48`.
AQ contains no JCS implementation.

Repository tests independently validated all 17 private instances, recomputed
all IDs, verified deterministic collection ordering, checked RD-Agent V1/V2
schema reuse, excluded performance fields, and passed all 13 required negative
cases.

```text
V3_TESTS = 6/6_PASS
NEGATIVE_TESTS = 13/13_PASS
AQ_CUSTOM_CANONICALIZER = NO
AQ_CANDIDATE_REGISTRY = NO
AQ_CUSTOM_RECORDER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Identity and policy boundary

The Candidate objects contain provenance, not performance ranking. IC,
RankIC, Sharpe, returns, PnL, TEST performance, runtime seconds, and hardware
metrics are absent. Historical TEST remains consumed research evidence and is
not relabelled as pristine or sealed OOS.

```text
HISTORICAL_RESEARCH_TEST_ACCESSED = YES
HISTORICAL_RESEARCH_TEST_STATUS = CONSUMED_AS_RESEARCH_EVIDENCE
SEALED_OOS_ROWS_ACCESSED = 0
P2_PROTOCOL_MODIFIED = NO
P3_CAN_ISSUE_CERTIFIED = NO
P3_CAN_EDIT_PROTOCOL = NO
P3_CAN_PROMOTE_TO_PRODUCTION = NO
```

P2 Protocol V1 remains unchanged and its frozen inventory does not admit these
17 candidates. Protocol expansion is a separate P2 authority decision.

## Evidence

Private instances and reports are stored under:

`D:/AQ_DATA/P3/candidate-v3-materialization-001/`

```text
V3_SPEC_SHA256 = 49974251f0094c0a3d173369ba806e5a44715a3b4433e6c6241e10db54fc16e2
V3_SCHEMA_SHA256 = fb0775c4b8c9a947eb2023d66d3b2c17fda3b3215edcf31a36f3d30ef87fc8f2
MATERIALIZATION_MANIFEST_SHA256 = 511ef7c25e55afc9cded8d6b2f13ed2715d248705c8cbad71918802d5210b8fd
VALIDATION_REPORT_SHA256 = efbbfd90d5068ddb49a787a08e3f8b5f9da526ae7b22fc326e976adf033473db
PRIVATE_REPORT_SHA256 = c56eb3323763492126c31d616334d2f4776c8eedfcc843d895e72880a4657ce5
```

## Non-execution accounting

```text
ALPHAGEN_DISCOVERY_RERUN = NO
QLIB_MODEL_TRAINING_RERUN = NO
QLIB_PREDICTION_RERUN = NO
HISTORICAL_TEST_REEVALUATED = NO
SEALED_OOS_ROWS_ACCESSED = 0
LLM_CALLS = 0
RD_AGENT_EXECUTED = NO
REAL_V3_CANDIDATE_CREATED = YES_17_PRIVATE_INSTANCES
P2_CERTIFICATION_EXECUTED = NO
```
