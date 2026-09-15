# P3 Candidate-to-P2 Identity Contract V2

## Status and scope

```text
CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V2
CANDIDATE_TOP_LEVEL_FIELD_COUNT = 8
LLM_EXECUTION_IDENTITY_REQUIRED = YES
REAL_CANDIDATE_INSTANCE_CREATED = NO
FAKE_CANDIDATE_INSTANCE_CREATED = NO
```

V2 preserves the complete V1 Candidate boundary and adds the LLM execution
identity that V1 cannot represent. V1 remains immutable. The normative V2
schema reuses the adjacent immutable V1 bundle definitions and replaces only
the runtime bundle with its V2 extension.

This contract does not execute RD-Agent, Qlib, DVC, Ollama, LiteLLM, or a cloud
provider. It does not confer P2 eligibility or certification.

## Exact top-level contract

V2 has exactly the same eight required top-level fields as V1:

1. `candidate_contract_version`
2. `candidate_id`
3. `rdagent_research_identity`
4. `qlib_recorder_identity`
5. `artifact_identity_bundle`
6. `dataset_identity_bundle`
7. `runtime_identity_bundle`
8. `p2_target_and_eligibility_boundary`

There is no ninth top-level field. `runtime_identity_bundle` retains all four
V1 runtime identities and requires one additional closed sub-bundle:
`llm_execution_identity`.

## Candidate ID

The Candidate ID projection and algorithm are unchanged. It contains exactly
the seven non-`candidate_id` top-level fields, including the complete V2
runtime bundle:

```text
candidate_id =
  "sha256:" + lowercase_hex(
    SHA256(
      UTF8(
        RFC_8785_JCS(projected_object)
      )
    )
  )

CANDIDATE_ID_INPUT_FIELD_COUNT = 7
CANONICALIZATION = RFC_8785_JSON_CANONICALIZATION_SCHEME
ENCODING = UTF-8
DIGEST = SHA-256
```

The V1 collection-sorting rules remain normative. No AQ canonicalization
engine is introduced.

## LLM execution identity

Every V2 Candidate requires:

```text
llm_execution_identity
  litellm_version
  llm_configuration_sha256
  native_trace_artifact_sha256
  chat_logical_slot
  chat_route_mode
  chat_resolutions[]
    provider
    requested_model
    resolved_model
    provider_model_identity_kind
    provider_model_identity
    call_count
  fallback_occurred
  fallback_reason_counts[]
    reason_class
    count
  embedding_logical_slot
  embedding_resolution
    provider
    requested_model
    resolved_model
    provider_model_identity_kind
    provider_model_identity
    dimensions
  embedding_epoch_sha256
```

The native trace hash binds the immutable RD-Agent/LiteLLM evidence from the
real run. The configuration hash binds the non-secret logical-slot mapping and
resolved local identities that affected generation. Declared identities must
be reconciled with the DVC run root and actual upstream evidence; schema
conformance alone cannot prove that external bytes match.

## Current LOCAL_ONLY contract

The only implemented route is:

```text
chat_logical_slot = aq-brain-local
chat_route_mode = LOCAL_ONLY
chat provider = ollama
requested_model = ollama/aq-brain-local
resolved_model = qwen3:4b
provider_model_identity_kind = LOCAL_DIGEST
provider_model_identity = 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7
fallback_occurred = false
fallback_reason_counts = []

embedding_logical_slot = aq-embedding-local
embedding provider = ollama
requested_model = ollama/aq-embedding-local
resolved_model = qwen3-embedding:0.6b
provider_model_identity_kind = LOCAL_DIGEST
provider_model_identity = ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d
dimensions = 1024
embedding_epoch_sha256 = e63389904f57782a645d2f9d79ec5f028b8a7ef99aa051a2cdb0ca2e55dbf6db
```

The schema can represent `CLOUD_ONLY` and `LOCAL_FIRST` later without changing
the eight top-level fields. Those modes are not implemented now. A local-only
Candidate must contain no cloud resolution, placeholder cloud model, or fake
provider version.

## Embedding epoch

The epoch identity is SHA-256 over the RFC 8785 canonical form of the exact
`epoch_identity_projection` stored in
`p3-local-logical-llm-slots-v1.json`. Any provider, requested model, resolved
model, digest, dimension, preprocessing, corpus, cache, or index change
requires a new epoch and a new empty upstream cache/index followed by a full
reindex. Equal dimensions never authorize cross-model vector reuse.

```text
EMBEDDING_AUTO_CROSS_MODEL_FALLBACK = NO
EMBEDDING_EPOCH_REQUIRED_FOR_MODEL_SWITCH = YES
```

## Fail-closed handoff

P2 rejects a V2 handoff when any V1 condition fails or when the LLM identity is
missing, the configuration/trace hashes do not match their artifacts, the
local digest is absent, call counts do not reconcile with native trace
evidence, the embedding epoch is absent or mismatched, or a declared route
contains a provider not authorized for that mode.

The current local route uses only native RD-Agent logging and LiteLLM call
execution. AQ does not add a recorder, router, model loader, provider layer,
spend database, or experiment registry.

## Materialization boundary

No Candidate instance is committed with this contract. A real instance still
requires a separately authorized completed execution with a `FINISHED`
Qlib/MLflow recorder, DVC lock/output identity, native trace artifact, model,
prediction, generated code, and the other existing V1 authorities.

```text
REAL_CANDIDATE_INSTANCE_CREATED = NO
FAKE_CANDIDATE_INSTANCE_CREATED = NO
CUSTOM_AQ_ROUTER_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_LOCAL_BRAIN_RESOURCE_ADMISSION_BENCHMARK_001
```
