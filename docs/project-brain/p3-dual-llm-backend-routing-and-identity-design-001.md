# P3 Dual LLM Backend Routing and Identity Design 001

Design date: 2026-09-15

## Scope and baseline

This is a documentation-only, upstream-first design audit. It does not start
RD-Agent, execute the P3 DVC stage, call a cloud model, download an Ollama
model, train, predict, or backtest.

```text
BASE_HEAD = ded599367d6ce269d962532e91e88bdbfaba214e
RDAGENT_VERSION = 0.8.1.dev37
RDAGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
LITELLM_VERSION = 1.100.1
OLLAMA_VERSION = 0.34.0
OLLAMA_ENDPOINT = http://127.0.0.1:11434
LOCAL_CHAT_MODEL = ollama/qwen3:4b
LOCAL_CHAT_MODEL_DIGEST = 359d7dd4bcdab3d86b87d73ac27966f4dbb9f5efdfcc75d34a8764a09474fae7
LOCAL_EMBEDDING_MODEL = ollama/qwen3-embedding:0.6b
LOCAL_EMBEDDING_MODEL_DIGEST = ac6da0dfba84a81fdbfbaf330198c33cd77c4cdfc53e8bc50eb581914a15621d
```

The evidence base is the installed LiteLLM 1.100.1 and RD-Agent runtime plus
the matching LiteLLM v1.100.1 release/source. Primary upstream references:

- [LiteLLM v1.100.1 release](https://github.com/BerriAI/litellm/releases/tag/v1.100.1)
- [LiteLLM v1.100.1 Router source](https://github.com/BerriAI/litellm/blob/v1.100.1/litellm/router.py)
- [LiteLLM v1.100.1 Proxy source](https://github.com/BerriAI/litellm/blob/v1.100.1/litellm/proxy/proxy_server.py)
- [LiteLLM Gateway and SDK overview](https://docs.litellm.ai/)

## Ownership decision

```text
LLM_ROUTER_OWNER = LITELLM
LLM_GATEWAY_OWNER = LITELLM
RETRY_AND_COOLDOWN_OWNER = LITELLM
FALLBACK_OWNER = LITELLM
LLM_CLIENT_OWNER = LITELLM
EMBEDDING_ENGINE_OWNER = LITELLM_PLUS_SELECTED_PROVIDER
AQ_OWNERSHIP = CONFIGURATION_POLICY_LOGICAL_ROLES_IDENTITY_BINDING_HEALTH_EVIDENCE
CUSTOM_AQ_ROUTER_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

LiteLLM 1.100.1 exposes a native `Router`, model lists/model groups, regular,
context-window and content-policy fallbacks, per-error retry counts, cooldowns,
Ollama and OpenAI providers, embeddings, standard logging payloads, and an
OpenAI-compatible Gateway. A second AQ router, retry engine, fallback filter,
LLM client, embedding engine, or spend-accounting engine is prohibited.

```text
LITELLM_NATIVE_MULTI_PROVIDER = YES
LITELLM_NATIVE_FALLBACK = YES
LITELLM_NATIVE_GATEWAY = YES
```

The installed RD-Agent environment contains the LiteLLM SDK and Gateway CLI,
but the Gateway is not runnable as installed: importing its server reports the
missing `backoff` proxy dependency. `fastapi` and `uvicorn` are installed;
`prisma` is not. No package was installed in this audit. A later implementation
must use a dedicated isolated Gateway environment pinned to LiteLLM 1.100.1
with its official proxy extra, rather than mutate the accepted RD-Agent
environment.

## Native configuration indirection

LiteLLM Proxy recursively resolves values of the exact form
`os.environ/VARIABLE`. The installed Router also resolves such values inside
`litellm_params`. Therefore the stable group name remains literal while the
provider model is replaceable natively:

```yaml
model_list:
  - model_name: aq-brain-local
    litellm_params:
      model: os.environ/AQ_LOCAL_CHAT_MODEL
      api_base: os.environ/OLLAMA_API_BASE
  - model_name: aq-brain-cloud
    litellm_params:
      model: os.environ/AQ_CLOUD_CHAT_MODEL
      api_key: os.environ/OPENAI_API_KEY
  - model_name: aq-embedding-local
    litellm_params:
      model: os.environ/AQ_LOCAL_EMBEDDING_MODEL
      api_base: os.environ/OLLAMA_API_BASE
  - model_name: aq-embedding-cloud
    litellm_params:
      model: os.environ/AQ_CLOUD_EMBEDDING_MODEL
      api_key: os.environ/OPENAI_API_KEY
```

This is a design fragment, not a materialized config. Secrets remain
environment-only. Model-group aliases are not part of the critical design.

## Chat logical slots and safe routing policy

Exactly three stable chat roles are reserved:

| Slot | Semantic role | Current activation |
|---|---|---|
| `aq-brain` | local-first route, cloud fallback only when a safe policy and hard budget are armed | `NOT_ARMED` |
| `aq-brain-local` | local Ollama only | `DEFAULT_ACTIVE` |
| `aq-brain-cloud` | OpenAI only | `CONFIGURED_NOT_ARMED`, manual override only |

The current local model value is supplied as
`AQ_LOCAL_CHAT_MODEL=ollama/qwen3:4b`; it is not embedded in RD-Agent, Qlib,
or DVC research logic. The future cloud value is supplied through
`AQ_CLOUD_CHAT_MODEL`, and its API key through `OPENAI_API_KEY`. No key is
required or stored by this design.

The desired `aq-brain` route is local primary then cloud. The installed Router
can express that chain, but its regular fallback is not sufficiently narrow
for automatic paid use. Source inspection gives this error disposition:

| Failure class | LiteLLM 1.100.1 capability | Paid auto-fallback decision |
|---|---|---|
| connection refused / transport failure | retry and regular fallback | eligible in principle |
| timeout | per-error retry and regular fallback | eligible in principle |
| local 5xx / service failure | retry and regular fallback | eligible in principle |
| model unavailable / 404 | regular fallback can run after local failure | eligible only under a future bounded policy |
| OOM/backend failure | fallback when mapped as server/backend error | eligible only under a future bounded policy |
| authentication / permission | regular fallback can still run | prohibited for automatic paid fallback |
| invalid request / other non-retryable 4xx | retry is rejected, but regular fallback can still run | prohibited for automatic paid fallback |
| context-window failure | separable through `context_window_fallbacks`; explicit empty route fails closed | no paid fallback |
| content-policy failure | separable through `content_policy_fallbacks`; explicit empty route fails closed | no paid fallback |

`retry_policy` controls retry counts by error class, but the general fallback
chain is not an equivalent error allowlist. Adding an AQ exception filter would
violate ownership. Consequently:

```text
LOCAL_RETRY_COUNT_DESIGN = 1
AUTO_CLOUD_FALLBACK_SAFE = NO
DEFAULT_CHAT_POLICY = LOCAL_ONLY_WITH_MANUAL_CLOUD_OVERRIDE
AQ_BRAIN_AUTO_LOCAL_FIRST = RESERVED_NOT_ARMED
CLOUD_CHAT_STATE = CONFIGURED_NOT_ARMED
PAID_LLM_REQUESTS = 0
```

Each new default request therefore selects `aq-brain-local`. Local recovery
naturally affects the next request because there is no sticky promotion.
`aq-brain-cloud` requires explicit, process-local human authorization.

## Spend safety

LiteLLM upstream provides budget enforcement. Its durable Gateway budget
surfaces are tied to Gateway state, database-backed spend tracking and
virtual-key/user/team/project policy. The SDK also exposes a process-memory
global `max_budget`, but that is neither durable across restarts nor a
cloud-fallback-specific authorization boundary.

```text
UPSTREAM_HARD_CLOUD_BUDGET_AVAILABLE = YES
HARD_BUDGET_REQUIRES = LITELLM_GATEWAY_DATABASE_VIRTUAL_KEY_AND_PROXY_STATE
HARD_BUDGET_DEPLOYED = NO
AQ_SPEND_ACCOUNTING = PROHIBITED
CLOUD_FALLBACK_ARMED = NO
```

The later implementation must fail closed unless the upstream hard budget and
cloud credential are explicitly armed. No extra infrastructure is deployed by
this design task.

## Embedding slots and epoch boundary

Exactly three embedding roles are reserved:

| Slot | Semantic role | Current activation |
|---|---|---|
| `aq-embedding` | stable logical role for the selected embedding epoch | resolves to local only |
| `aq-embedding-local` | local Ollama embedding only | active |
| `aq-embedding-cloud` | cloud embedding only | configured interface, not armed |

The current value is supplied as
`AQ_LOCAL_EMBEDDING_MODEL=ollama/qwen3-embedding:0.6b`. There is no fallback
from local to cloud.

Installed RD-Agent evidence makes the restriction mandatory:

- reference/document embeddings and query embeddings are both produced by
  `APIBackend().create_embedding()`;
- `PDVectorBase` stores vectors and later compares query vectors by cosine
  similarity;
- CoSTEER knowledge bases can be serialized and loaded again;
- RD-Agent's SQLite embedding cache keys only the input content hash, not the
  provider/model/digest/epoch;
- vector dimensional equality does not establish vector-space compatibility.

```text
EMBEDDING_AUTO_CROSS_MODEL_FALLBACK = NO
EMBEDDING_EPOCH_REQUIRED_FOR_MODEL_SWITCH = YES
```

The minimum switch boundary is an upstream-owned clean rebuild: select one
exact embedding provider/model/revision, allocate a new empty prompt-cache and
knowledge/index root, regenerate all stored document/reference embeddings,
and generate all query embeddings with that same identity. No old vector,
embedding cache row, or serialized knowledge base may cross the epoch. The
epoch binds provider, requested model, resolved model/revision or local digest,
dimension, truncation/preprocessing configuration, corpus identity, and the
resulting cache/index identity. AQ does not implement vector migration.

## Logical identity versus resolved execution identity

A logical slot is routing policy, not execution identity. Every real Candidate
must bind the actual provider/model evidence used during the run.

LiteLLM's native `StandardLoggingPayload` contains per-call `trace_id`,
`litellm_call_id`, `custom_llm_provider`, `model`, `model_id`, `model_group`,
status, error information, timing, tokens and cost. Router responses also
carry deployment metadata. Those are suitable upstream evidence ingredients.

The current RD-Agent `LiteLLMAPIBackend`, however, consumes completion content
and finish reason and does not persist an immutable run-level aggregate of
resolved deployments, local digests, fallback counts/reasons, and routing
config hash. Native upstream fields exist, but the currently activated P3
boundary does not seal all of them.

```text
UPSTREAM_PER_CALL_IDENTITY_FIELDS = AVAILABLE
IMMUTABLE_RUN_SCOPED_LLM_TRACE = NOT_YET_BOUND
AQ_RUNTIME_RECORDER_REQUIRED = NO
RESIDUAL_IDENTITY_GAP = NATIVE_LITELLM_LOG_EVIDENCE_MUST_BE_RUN_SCOPED_AND_CONTENT_BOUND
```

The later implementation should retain LiteLLM-native structured call/log
evidence beneath the DVC run root and bind its content hash. It must not create
an AQ logging service or recorder.

## Candidate Contract V1 audit and V2 design

Candidate V1 has exactly four `runtime_identity_bundle` fields:

```text
rdagent_source_git_sha
rdagent_installed_wheel_sha256
rdagent_environment_freeze_sha256
qlib_source_git_sha
```

Its `rdagent_research_identity` binds research content and lineage but not the
concrete LLM provider/model route. `additionalProperties=false` prevents a
sound V1 extension. Unrelated fields cannot be reinterpreted.

```text
CANDIDATE_V1_BINDS_LLM_EXECUTION_IDENTITY = NO
CANDIDATE_CONTRACT_UPGRADE_REQUIRED = YES
PROPOSED_CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V2
```

V2 should preserve the same eight top-level bundles and extend only
`runtime_identity_bundle` with required `llm_execution_identity`. The minimum
closed sub-bundle is:

```text
llm_execution_identity
  litellm_version
  routing_config_sha256
  native_trace_artifact_sha256
  chat_logical_slot
  chat_route_mode                  # LOCAL_ONLY | CLOUD_ONLY | LOCAL_FIRST
  chat_resolutions[]
    provider
    requested_model
    response_model
    provider_model_identity_kind   # LOCAL_DIGEST | PROVIDER_SNAPSHOT |
                                   # RESPONSE_MODEL_ONLY | UNAVAILABLE
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
    response_model
    provider_model_identity_kind
    provider_model_identity
    dimensions
  embedding_epoch_sha256
```

For Ollama, `provider_model_identity` is the exact local model digest. For a
cloud call it binds the exact requested model, response `model`, and immutable
provider snapshot/version when one is exposed; otherwise the identity kind
must truthfully say `RESPONSE_MODEL_ONLY` or `UNAVAILABLE`. The latter may be
recordable but can remain ineligible under later P2 policy. Counts reconcile
to the sealed native trace. This shape represents local-only, cloud-only,
local-first without fallback, and local-first with fallback without adding a
ninth top-level field.

V1 remains unchanged. V2 is not implemented in this task.

## Gateway placement and DVC impact

```text
GATEWAY_PLACEMENT = UBUNTU_24_04_WSL_LOCALHOST_ONLY_DEDICATED_PINNED_ENV
GATEWAY_LISTENER = 127.0.0.1_ONLY
LAN_EXPOSURE = NO
PUBLIC_EXPOSURE = NO
CURRENT_RDAGENT_ENV_GATEWAY_READY = NO_MISSING_PROXY_EXTRA_DEPENDENCY
```

The later isolated Gateway owns logical model groups. RD-Agent continues to
use its existing LiteLLM backend against the Gateway's OpenAI-compatible
localhost endpoint. No RD-Agent, Qlib, scenario-binding, or research-logic
change is required when an underlying model value changes.

The current `p3_rdagent_us_quant_research` stage still selects concrete
process-local Ollama models and is unchanged here. A later authorized change
must select the safe logical slots, add the materialized routing config as a
DVC dependency, and bind these resolved identities for the run:

```text
LiteLLM version and dedicated-environment freeze hash
routing config content hash
resolved non-secret environment model values
Gateway listener/route mode
local Ollama model digests
cloud requested and response model identities, if used
native per-call trace content hash and reconciled call counts
embedding epoch/cache/index identities
```

Secrets are never DVC dependencies or committed content.

```text
ROUTING_CONFIG_DVC_DEPENDENCY_REQUIRED = YES
DVC_YAML_CHANGED = NO
DVC_LOCK_CHANGED = NO
DVC_REPRO_EXECUTED = NO
```

## Replaceability proof

Replacing `AQ_LOCAL_CHAT_MODEL`, `AQ_CLOUD_CHAT_MODEL`, or their embedding
counterparts changes only upstream-owned routing configuration and the
immutable resolved identity. It does not change RD-Agent source, Qlib source,
the P3 scenario binding, DVC research logic, or Candidate top-level structure.

```text
MODEL_REPLACEMENT_REQUIRES_RDAGENT_CODE_CHANGE = NO
MODEL_REPLACEMENT_REQUIRES_QLIB_CODE_CHANGE = NO
MODEL_REPLACEMENT_REQUIRES_AQ_ROUTER_CODE_CHANGE = NO
```

An embedding replacement additionally starts a new epoch and rebuilds the
upstream cache/index; it never reuses the prior vector space.

## Final decision and non-actions

```text
CHAT_LOGICAL_SLOT = aq-brain
CHAT_LOCAL_SLOT = aq-brain-local
CHAT_CLOUD_SLOT = aq-brain-cloud
DEFAULT_CHAT_POLICY = LOCAL_ONLY_WITH_MANUAL_CLOUD_OVERRIDE
AUTO_CLOUD_FALLBACK_SAFE = NO
EMBEDDING_LOGICAL_SLOT = aq-embedding
EMBEDDING_LOCAL_SLOT = aq-embedding-local
EMBEDDING_CLOUD_SLOT = aq-embedding-cloud
EMBEDDING_AUTO_CROSS_MODEL_FALLBACK = NO
EMBEDDING_EPOCH_REQUIRED_FOR_MODEL_SWITCH = YES
CUSTOM_AQ_ROUTER_REQUIRED = NO
CANDIDATE_CONTRACT_UPGRADE_REQUIRED = YES
CURRENT_NEXT = P3_CANDIDATE_CONTRACT_V2_AND_DUAL_LLM_BACKEND_IMPLEMENTATION_001

PAID_LLM_REQUESTS = 0
PAID_EMBEDDING_REQUESTS = 0
CLOUD_INFERENCE_REQUESTS = 0
AUTONOMOUS_ATTEMPT_COUNT = 0
RD_AGENT_RESEARCH_LOOP_EXECUTED = NO
DVC_REPRO_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
OLLAMA_MODEL_DOWNLOAD = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Local-only implementation resolution

The subsequent bounded implementation intentionally activated only the safe
local subset of this design. Native Ollama aliases now provide stable
`aq-brain-local` and `aq-embedding-local` roles; no Gateway, cloud credential,
or automatic fallback was introduced. Candidate V2 preserves all eight
top-level bundles and adds required `llm_execution_identity` under the runtime
bundle. The local slot configuration is now a P3 DVC dependency.

```text
CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V2
CANDIDATE_TOP_LEVEL_FIELD_COUNT = 8
LLM_EXECUTION_IDENTITY_REQUIRED = YES
DEFAULT_CHAT_POLICY = LOCAL_ONLY
LOCAL_CHAT_LOGICAL_SLOT = aq-brain-local
LOCAL_CHAT_RESOLVED_MODEL = qwen3:4b
LOCAL_EMBEDDING_LOGICAL_SLOT = aq-embedding-local
LOCAL_EMBEDDING_RESOLVED_MODEL = qwen3-embedding:0.6b
EMBEDDING_EPOCH_IDENTITY = e63389904f57782a645d2f9d79ec5f028b8a7ef99aa051a2cdb0ca2e55dbf6db
CLOUD_CHAT_INTERFACE = RESERVED_NOT_IMPLEMENTED
CLOUD_EMBEDDING_INTERFACE = RESERVED_NOT_IMPLEMENTED
LITELLM_GATEWAY_DEPLOYED = NO
AUTO_CLOUD_FALLBACK = NO
MODEL_RESIDENCY_POLICY = ON_DEMAND
DVC_YAML_CHANGED = YES_P3_STAGE_ONLY
DVC_LOCK_CHANGED = NO
DVC_REPRO_EXECUTED = NO
CUSTOM_AQ_ROUTER_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_LOCAL_BRAIN_RESOURCE_ADMISSION_BENCHMARK_001
```
