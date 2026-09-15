# P3 Candidate-to-P2 Identity Contract Materialization

Task:
`AUTONOMOUS-QUANT-P3-CANDIDATE-TO-P2-IDENTITY-CONTRACT-MATERIALIZATION-001`

Status:
`COMPLETE — STATIC CONTRACT ONLY / REAL CANDIDATE DEFERRED`

## 1. Materialized boundary

The previously audited thin cross-upstream identity boundary is now expressed
as exactly two non-executable files:

```text
30-research-system/candidate-handoff/p3-to-p2/candidate-contract-v1.schema.json
30-research-system/candidate-handoff/p3-to-p2/candidate-contract-v1.md
```

The JSON Schema uses Draft 2020-12, closes the root and nested identity
objects to undeclared properties, and requires exactly eight top-level fields:

```text
candidate_contract_version
candidate_id
rdagent_research_identity
qlib_recorder_identity
artifact_identity_bundle
dataset_identity_bundle
runtime_identity_bundle
p2_target_and_eligibility_boundary
```

```text
CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V1
AQ_REQUIRED_IDENTITY_FIELD_COUNT = 8
ROOT_ADDITIONAL_PROPERTIES = FALSE
```

## 2. Candidate ID

The Candidate ID is the lowercase SHA-256 digest of the UTF-8 RFC 8785 JCS
encoding of the seven non-ID top-level fields, prefixed by `sha256:`.
`candidate_id` is excluded from its own projection. Deterministic ordering for
every collection-valued identity is normative in the Markdown contract.

```text
CANDIDATE_ID_INPUT_FIELD_COUNT = 7
CANDIDATE_ID_CANONICALIZATION = RFC8785_JCS_SHA256
CANDIDATE_ID_PATTERN = ^sha256:[0-9a-f]{64}$
AQ_CANONICALIZATION_LIBRARY_CREATED = NO
```

## 3. Authority separation

RD-Agent research content, exact Qlib/MLflow finished-run identity, DVC lock
and output identity, P2 dataset authority, pinned runtime authority, and P2
protocol/eligibility authority remain distinct bundles. Paths, UUIDs as sole
identity, timestamps, hostnames, display names, performance metrics, and
certification outcomes are excluded from Candidate identity.

The schema requires Qlib status `FINISHED`, sealed-OOS access to be false, and
all three P3 authority flags to be false:

```text
P3_CAN_ISSUE_CERTIFIED = NO
P3_CAN_EDIT_PROTOCOL = NO
P3_CAN_PROMOTE_TO_PRODUCTION = NO
```

Protocol V1 eligibility remains explicit and owned by P2 Certification. A new
P3 Candidate cannot silently join its frozen Candidate inventory.

## 4. Validation evidence

The installed `jsonschema` 4.26.0 implementation accepted the schema against
the Draft 2020-12 meta-schema. One in-memory synthetic structural witness
passed. Eight independent negative mutations failed closed:

```text
missing required top-level field = REJECTED
ninth top-level field = REJECTED
RUNNING recorder status = REJECTED
malformed candidate_id = REJECTED
sealed_oos_accessed_by_p3 true = REJECTED
p3_can_issue_certified true = REJECTED
p3_can_edit_protocol true = REJECTED
p3_can_promote_to_production true = REJECTED
```

No witness was persisted or committed.

```text
SCHEMA_VALIDATION = PASS
NEGATIVE_VALIDATION_CASES = 8/8 PASS
CONTRACT_SCHEMA_SHA256 = a30630d41596d5d89da1b4291b07489585e0ca23fbc78ddd822404eb0e3cb795
CONTRACT_SPEC_SHA256 = 0085963ad80b3e8ca526e8749be1eda6a157e7e15908462c8af5633277b8a364
```

## 5. Deferred real instance

No real or fake Candidate instance exists. A real instance requires a
separately authorized P3 execution with a `FINISHED` Qlib/MLflow run, a real P3
DVC lock entry, and real generated-code, rendered-config, model, prediction,
dataset-dependency, runtime, and run-root output identities.

```text
REAL_CANDIDATE_INSTANCE_CREATED = NO
FAKE_CANDIDATE_INSTANCE_CREATED = NO
PLACEHOLDER_RUN_ID = FORBIDDEN
PLACEHOLDER_DVC_HASH = FORBIDDEN
PLACEHOLDER_MODEL_HASH = FORBIDDEN
PLACEHOLDER_PREDICTION_HASH = FORBIDDEN
```

## 6. Non-actions and current state

```text
CUSTOM_REGISTRY_REQUIRED = NO
CUSTOM_RUNTIME_VALIDATOR_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
DVC_YAML_CHANGED = NO
DVC_LOCK_CHANGED = NO
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
P2_PROTOCOL_CHANGED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
DVC_REPRO_EXECUTED = NO
CANDIDATE_TO_P2_CONTRACT = MATERIALIZED
CURRENT_NEXT = P3_FIRST_AUTHORIZED_AUTONOMOUS_SMOKE_AND_CANDIDATE_INSTANCE_001
```
