# P12 durable synthetic research handoff

## Scope and owners

This is a thin, test-only P12 adapter. P4 owns lifecycle meaning and creates
`LifecycleDecisionEvidenceV1` and `ResearchRequestV1`; RD-Agent owns autonomous
research; Qlib owns training and Recorder outputs; P2 alone owns certification.
The default P12 dispatch target is an inert local synthetic executable. One
explicit `TEST_ONLY` option runs a bounded official RD-Agent chat/embedding
backend smoke through the existing Docker Compose/LiteLLM Proxy/mock pattern.
The previous smoke target remains available unchanged. A second explicit
`TEST_ONLY` target starts one bounded native RD-Agent `fin_quant` proposal
step from the already-built P3 runtime image. Neither target enables real
dispatch, provider credentials, certification, or a broker.

P3's documented native command remains `rdagent fin_quant --loop-n 1`. The new
P12 target adds upstream's supported `--step-n 1` bound so the native
application reaches its first `direct_exp_gen` proposal step and stops before
coding, running, feedback, or training. The exact CLI options and step behavior
were verified against the pinned RD-Agent
`484776c211e4fbbeef03e0ec00d6bbee7362a4f4` source in the P3 image:
`rdagent/app/cli.py`, `rdagent/app/qlib_rd_loop/quant.py`, and
`rdagent/utils/workflow/loop.py`. Real dispatch permission remains `DENIED`.

### Opt-in Docker RD-Agent native smoke

The default target remains `INERT_LOCAL_EXECUTABLE`. A caller must explicitly
select `DOCKER_RDAGENT_PROXY_MOCK_SMOKE` and supply a runtime directory outside
the repository. The existing P12 intake validates the synthetic P4 request and
TEST_ONLY policy, creates the same exclusive durable claim, then invokes the
specific Compose target. Claim, dispatch, and terminal records all bind the
selected target identity; an inert-target result cannot replay as Docker
success. A valid terminal replay returns without invoking Compose again. A
worker failure becomes a failed terminal result. If dispatch or cleanup is
ambiguous, P12 returns nonzero and blocks replay without redispatch.

The AQ-owned Compose template pins the verified LiteLLM Proxy v1.105.1 image,
Postgres/Redis and the RD-Agent 1.0.0 worker. Native Compose healthchecks and
`depends_on: service_healthy` gates start. Each claim receives a unique
Compose project and a fresh test database. The controller creates an ephemeral
Proxy admin key and a virtual key scoped only to `deepseek-chat` and
`qwen3-embedding:0.6b` in process memory. The worker receives only the scoped
test key and Proxy URL. It runs as UID 10001 with a read-only root, bounded
tmpfs/resources, no host mounts or Docker socket, and only an internal network
shared with the Proxy. The Proxy routes both model aliases to the local mock.
The smoke verifies one mock chat and one mock embedding call, then tears down
the isolated Compose project and verifies its containers, networks and
volumes are gone. The worker image may remain cached; no credentials are stored
in the repository or runtime directory.

### Opt-in native fin_quant proposal step

Select `DOCKER_RDAGENT_FINQUANT_TEST_ONLY` through the same P12 durable intake.
Before starting Compose, P12 requires the local image ID to equal
`sha256:f0caceba9e06a618dda72bd999de78c13e34e0773831c8796936c80793e4eea2`;
this worker has `pull_policy: never`, and this path does not build an image.
The Proxy, local Mock, Postgres, and Redis remain the existing pinned services.
Only the fin_quant worker is new; the previous smoke worker definition and
target are unchanged.

The new worker runs as UID 10001 with read-only root, bounded resources, no
Docker socket, and only the internal Proxy network. It receives a fresh
Proxy virtual key scoped to the two Mock model aliases and no provider/admin
credentials. Its sole model URL is the Proxy, routed by the pinned LiteLLM
config to the local Mock. Three exact P2/P3 data paths are bind-mounted
read-only: the P3 factor source, the frozen P2 Qlib provider URI, and the
separate frozen Qlib calendar-provider URI. Its writable `/workspace` is a
per-attempt host bind at
`D:\AQ\OPERATIONS\P12\finquant-output\<request-id-hex>\<attempt-uuid>`.
P12 validates the canonical request identity and UUID attempt, creates the
leaf exclusively, and passes only that directory to Compose as `/workspace`.
Compose refuses to create a missing host source implicitly. The native
workspace, trace, pickle cache, MLflow SQLite path, and any task/Recorder
artifacts therefore remain in the request/attempt namespace after temporary
Compose resources are removed. P12 also stores immutable attempt/evidence or
failure records and redacted stdout/stderr beside those native outputs.
Plain `selector.log` credentials are redacted; signed RD-Agent settings
pickles are preserved byte-for-byte. The short-lived test Proxy key in those
signed settings is usable only against the temporary Proxy database, which is
removed during teardown. The frozen P3 binding and US/PIT templates are used
from the image.

The current Mock's chat body is the synthetic string `synthetic-ok`, not a
fabricated hypothesis. The native proposal request may therefore fail while
parsing. P12 records the observed process exit, proposal-phase marker, and
Mock request counters as a failed terminal status when that happens. A same-ID
replay returns the persisted terminal result without starting another process.
Missing data, wrong image, or an invalid worker configuration fail before the
worker runs. Proxy unavailability or an unverified process outcome leaves the
request blocked/unknown and prevents retry.

### Actual TEST_ONLY execution record

On 2026-10-17, P12 accepted a synthetic P4 no-Champion request and started the
one-step official CLI in the verified image
`sha256:f0caceba9e06a618dda72bd999de78c13e34e0773831c8796936c80793e4eea2`.
The first attempt exposed unquoted YAML date values being coerced into
timestamps; P12 marked that request `FAILED_SYNTHETIC` and preserved the
failed terminal record. Date values are now quoted, and Compose rendering plus
the runtime preflight verify the unchanged `YYYY-MM-DD` strings. A separate
synthetic P4 request then verified the corrected end-to-end boundary:
`QlibQuantScenario` initialized, `direct_exp_gen` was reached, the three
approved mounts were read-only, the worker used the internal Proxy-only
network, and the local Mock observed 10 chat requests. The run namespace was
`aq-p12-finquant-5be5898accf0`.

The Mock returned only `synthetic-ok`; RD-Agent exited 1 while processing the
proposal. P12 persisted `FAILED_SYNTHETIC`, return code 1, zero Candidate,
training, certification, and broker counts, and denied real dispatch. Replay
returned `REPLAY_TERMINAL_FAILED_NO_DISPATCH` (P12 exit 4) with zero additional
dispatches. This demonstrates native entry and controlled request routing; it
does not demonstrate a valid hypothesis, completed research, spending
authorization, certification, or production readiness. The unquoted date
regression is covered by a focused Compose assertion.

### Durable output acceptance (2026-10-17)

P12 accepted a distinct synthetic P4 `NO_CHAMPION` request
`sha256:afecf9df62511496d2c411445a9706f8bddcc238ac7b8add9e7637ce4c2e28e8`
and created attempt `fd605e09-ba11-455c-974e-726e8396e21e` under
`D:\AQ\OPERATIONS\P12\finquant-output\afecf9df62511496d2c411445a9706f8bddcc238ac7b8add9e7637ce4c2e28e8\fd605e09-ba11-455c-974e-726e8396e21e`.
The actual P12 Compose worker used the pinned image, non-root UID 10001,
read-only root, the three approved read-only inputs, and the internal Proxy
network. `QlibQuantScenario` initialized, `direct_exp_gen` was entered, and
the local Mock counted 10 chat requests. The Mock's `synthetic-ok` response
was malformed for RD-Agent, so the native process truthfully exited 1 and P12
persisted `FAILED_SYNTHETIC`; it produced no Candidate, training, certification,
or broker action.

After Compose teardown, 57 files remained in the host attempt directory,
including RD-Agent trace/workspace artifacts, `selector.log`, durable P12
attempt/evidence/failure records, and redacted process logs. The separate
Qlib TEST_ONLY Recorder check created an MLflow SQLite database and a native
Qlib diagnostic Recorder without training. Its writer container was removed;
a second container reopened the same database read-only through Qlib's
`R.get_recorder`, verified the same Recorder and experiment IDs, `FINISHED`
status, and diagnostic parameters (`recorder_id=f03295bec4bc4cbeb32bc8645d0da149`,
`experiment_id=1`). The persistent diagnostic database is
`D:\AQ\OPERATIONS\P12\durable-output-implement-001\qlib-recorder-reopen-001\mlflow.db`.
This checks the native persistence path; it does not claim the failed fin_quant
proposal created a Recorder or database.

Replaying the P12 request returned `REPLAY_TERMINAL_FAILED_NO_DISPATCH` with
`dispatch_count_added: 0`; only the existing healthy P12 health container
remained. Real dispatch remains denied, and the test does not authorize real
spending, certification, or trading.

Invoke it as a one-shot P12 TEST_ONLY request:

```bash
export PYTHONPATH=/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001/upstream-libs
/home/zhou/AQ_ENVS/rdagent/bin/python \
  70-operations-system/research-handoff/p12_research_handoff.py process \
  --request /mnt/d/AQ/OPERATIONS/P12/<run>/request.json \
  --policy /mnt/d/AQ/OPERATIONS/P12/<run>/test-policy.json \
  --state-dir /mnt/d/AQ/OPERATIONS/P12/<run>/state \
  --synthetic-only \
  --target DOCKER_RDAGENT_FINQUANT_TEST_ONLY \
  --docker-runtime-dir /mnt/d/AQ/OPERATIONS/P12/<run>/runtime
```

The temporary host command is:

```bash
export PYTHONPATH=/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001/upstream-libs
/home/zhou/AQ_ENVS/rdagent/bin/python \
  70-operations-system/research-handoff/p12_research_handoff.py process \
  --request /mnt/d/AQ/OPERATIONS/P12/<run>/request.json \
  --policy /mnt/d/AQ/OPERATIONS/P12/<run>/test-policy.json \
  --state-dir /mnt/d/AQ/OPERATIONS/P12/<run>/state \
  --synthetic-only \
  --target DOCKER_RDAGENT_PROXY_MOCK_SMOKE \
  --docker-runtime-dir /mnt/d/AQ/OPERATIONS/P12/<run>/runtime
```

`Invoke-SyntheticResearchHandoff.ps1` accepts the same explicit target and
runtime-directory parameters for a one-shot Task Scheduler invocation. The
existing health tasks and any permanent research schedule are not changed.
TEST_ONLY admission keeps real research spending and dispatch denied.

### Persistent Proxy handoff integration (2026-10-17)

The persistent Compose definition now gives LiteLLM both the existing internal
`core` network and a dedicated internal `worker_proxy` network. PostgreSQL,
Redis, and Mock remain on `core`; the one-off RD-Agent worker joins only
`worker_proxy`, receives a new request-scoped TEST_ONLY LiteLLM virtual key,
and uses the existing pinned image and durable P12 output bind. The key is
created and inspected through LiteLLM's native key APIs on the trusted control
side. Its allowed models route only to the local Mock, with a synthetic native
budget, one-hour reset/expiration, and concurrency of one. The worker does not
receive Proxy admin or database credentials. No host port or Docker socket is
configured. The one-off cleanup leaves the persistent services and named
volumes intact.

The first integration dispatch for request
`sha256:94d8470c76fea98a3ce40260742a7401f88b0c47579bdf9c163c92e2c2e9b3cd`
and attempt `36b84186-be08-4eb8-8070-cfc9df4ce005` entered the native
`direct_exp_gen` proposal path. RD-Agent received the Mock's deliberately
malformed `synthetic-ok` response, retried JSON parsing, and exited with a
failure. Its trace and redacted diagnostic logs remain under
`D:\AQ\OPERATIONS\P12\finquant-output\94d8470c76fea98a3ce40260742a7401f88b0c47579bdf9c163c92e2c2e9b3cd\36b84186-be08-4eb8-8070-cfc9df4ce005`.
LiteLLM/PostgreSQL retained the scoped key's synthetic spend (`0.0005`), and
that key was blocked after the attempt. This is internal Mock accounting, not
provider spending.

The first wrapper attempt encountered a local `NameError` in its
post-dispatch network verification before it could persist a terminal result or
run the configured budget-exhaustion probe. P12 correctly recorded
`BLOCKED_UNKNOWN_POST_DISPATCH_STATE`. Replaying that same request returned the
same blocked state with `dispatch_count_added: 0`; it was not retried.

A separate, freshly generated P4 synthetic request was then dispatched after
the wrapper correction. Request `sha256:e58af0dfc1cad1c53c20f474bf8ab092763979954bbc2e152117e6015b205cf4`,
attempt `0813c673-f557-4ed1-8a16-63489489f1f1`, reached RD-Agent's native
`direct_exp_gen` proposal path and made ten Mock chat requests. The Mock's
deliberately malformed `synthetic-ok` response caused proposal parsing to fail;
P12 persisted `FAILED_SYNTHETIC`, return code 1, zero candidates, and no P2
evaluation. The worker was removed, while 57 run-scoped durable output files
remained under
`D:\AQ\OPERATIONS\P12\finquant-output\e58af0dfc1cad1c53c20f474bf8ab092763979954bbc2e152117e6015b205cf4\0813c673-f557-4ed1-8a16-63489489f1f1`.

The native LiteLLM budget exhaustion probe was denied (`422 budget_exceeded`)
without increasing the Mock request count. PostgreSQL later showed spend
settling from `0.0004` at probe time to `0.0005`; the scoped key remained
blocked, and its native cap was aligned to the settled spend through LiteLLM's
official key API. A follow-up replay returned
`REPLAY_TERMINAL_FAILED_NO_DISPATCH` with zero added dispatches. Regression
coverage now waits for stable native spend before probing exhaustion. These are
TEST_ONLY Mock accounting results, not provider spend or owner authorization.
No Candidate, certification, full training, paid provider call, or broker
action was produced; real research remains denied.

## Synthetic request and intake

`create-synthetic-request` calls P4's existing `challenger_needed()` with
`NO_CHAMPION` and `test_fixture=True`, then calls P4's
`build_research_request()`. This exercises initial research without requiring
a Champion. P12 reparses both P4 models, rechecks RFC 8785 request identity,
and verifies the decision/request reason and evidence identities agree. The
P4 request ID and provenance are preserved unchanged.

The decision is marked `TEST_FIXTURE_NOT_REAL_EVIDENCE`. P12 reports external
authorization as `UNVERIFIED_DENIED` and spending permission as
`NOT_PROVEN_DENIED`. The request's `research_budget_identity` is only an
identity; it does not prove or enforce a spending limit. A structurally valid
request cannot grant real authority.

## Standing policy admission boundary

`P12StandingResearchPolicyV1` is an AQ-specific policy record shape, not a
new scheduler, budget service, or trusted approval store. Its RFC 8785
`policy_id` binds the scope, P4 provenance, research families, explicit
provider/model and local/paid classifications, budget identity and limits,
effective/expiry/revocation fields, concurrency, and resource ceilings.
`create-synthetic-test-policy` can produce only a `TEST_ONLY` fixture for
an already synthetic P4 request. It is never an owner approval record.

The intake evaluates expiry, revocation, request scope, provider/model
allowlists, simulated period/per-run spend, concurrency snapshot, and
runtime/memory/storage bounds before creating a durable request claim.

## Disabled DeepSeek Flash staging profile

`docker-rdagent-smoke/compose.deepseek-staging.yaml` and
`config.deepseek-staging.yaml` define a separate opt-in LiteLLM Proxy profile
for the official `deepseek/deepseek-flash` route and the existing local
`ollama/qwen3-embedding:0.6b` model. The ordinary persistent TEST_ONLY Compose
file and its Mock aliases are unchanged. The staging profile has no published
port, uses a separate PostgreSQL database (`litellm_deepseek_staging`) and
Redis DB index, and joins the existing internal `worker_proxy` network only
for its opt-in one-shot worker. The worker profile is disabled unless both
`deepseek-staging` and `p12-owner-oneshot` are selected through the explicit
local owner command; the external provider secret file and separate Proxy
admin key remain required.

The host supplies `P12_DEEPSEEK_API_KEY_FILE` to Compose. Compose mounts that
file as a secret to the Proxy only; its entrypoint loads the value into the
Proxy process environment required by the official LiteLLM config resolver.
Neither the RD-Agent worker nor its P12 TEST_ONLY environment receives the
provider credential. Compose secrets protect the container boundary from the
worker, not from a host Docker administrator. The provider egress network is a
regular Docker bridge; the RD-Agent worker is attached only to the internal
`worker_proxy` network. A host-side one-shot command provisions a native
scoped key only after local interactive owner confirmation. No key is created
at startup.
The pinned LiteLLM 1.105.1 startup path requires `budget_duration` whenever a
PostgreSQL-backed Proxy has a positive global `litellm_settings.max_budget`.
Omitting the duration therefore crashes startup; adding one creates a resetting
global budget, not a lifetime ceiling. This profile does not set a global
`max_budget`. The `default_key_generate_params` and
`upperbound_key_generate_params` instead prepare issuance defaults/bounds for a
future key: USD 5 maximum, 24-hour key expiry, the Flash and local Ollama model
allowlist, and one parallel request. The default key budget explicitly has
`budget_duration: null` (no periodic reset). These are configuration bounds,
not an owner-approved grant, a created key, or proof of spend enforcement.
`default_max_parallel_requests` is under `router_settings`, where the pinned
Router consumes it. Fail-closed budget/rate-limit settings remain enabled, but
the real P12 dispatch target stays disabled.

The pinned image source was checked directly: `proxy_server.py` calls
`_add_proxy_budget_to_db()` only for a positive global budget with PostgreSQL,
and that method raises when `budget_duration` is absent. Its
`LiteLLM_UpperboundKeyGenerateParams` supports `max_budget`, `duration`,
`budget_duration`, `max_parallel_requests`, TPM, and RPM fields; key generation
applies these caps. `GenerateRequestBase` persists per-key `max_budget` and
`budget_duration`. `NewUserRequest` exposes `max_budget` and inherits
`user_id`/budget duration; the native `/user/new` contract documents that an
omitted user `budget_duration` means the budget never resets. These user and
key records use LiteLLM's PostgreSQL-backed tables when configured. The
upper-bound schema does not enforce a `models` field, so the trusted issuer
must apply the two-model allowlist and verify the issued key with LiteLLM's
native key-info API before any future dispatch.

Keep three distinct states clear:

1. **Configured upper bound (present):** the staging profile constrains future
   key issuance to the configured maximum and defaults. No paid key is created.
2. **Experiment aggregate budget (future, not provisioned):** before issuing
   any key, the trusted control side must create one native persistent LiteLLM
   user with `max_budget: 5.0` and no `budget_duration`, using a stable
   `user_id` derived from the authorized experiment identity. Every key for
   that experiment must use that same `user_id`, so LiteLLM's persistent
   per-user spend is shared across keys. The user must not be recreated or
   assigned a new identity on retry/restart; P12's no-redispatch policy remains
   required. Per-key caps alone do not enforce this aggregate, because issuing
   another key could otherwise grant another USD 5. The pinned native user
   API/database provides the cumulative spend boundary; AQ does not keep a
   parallel ledger.
3. **Actual native enforcement after local owner activation:** the interactive
   one-shot control creates one experiment-bound native user and one scoped
   key only after checking the supplied P4 request and P12 policy and receiving
   the exact confirmation phrase. It verifies the user/key through native
   LiteLLM APIs before dispatch. No owner approval file, native user, paid key,
   provider request, or real dispatch was created by this change. The local
   trusted-host exception is not a cloud-grade signer, revocation authority,
   or protection from a malicious host operator.

The configured key bounds alone are not a spending grant. The owner one-shot
path uses a native persistent user budget of USD 5 with
`budget_duration: null` and a key capped at USD 5 with
`budget_duration: null`, maximum 24-hour expiration, the two-model allowlist,
and one parallel request. It refuses prior user spend, any previous key on the
experiment user, mismatched identity, or a replayed P12 request. After the run
or failure it blocks the scoped key; an ambiguous dispatch leaves the P12
claim in place and cannot be retried.

The pinned RD-Agent LiteLLM backend reads `LITELLM_CHAT_MAX_TOKENS` into its
chat completion kwargs and passes them to `litellm.completion`. Its
`chat_model_map` can override the token value, so the worker fixes that map to
`{}` and rejects other values. A no-network, read-only probe of the exact
pinned image verified `max_tokens=8192`, the Flash model, an empty model map,
and native retries disabled. No chat request was made during this check.

The staging profile uses a separate database in the existing persistent
PostgreSQL service. If that database is absent on a new host, an operator can
create it with
`docker exec aq-p12-litellm-persistent-test-postgres-1 createdb -U litellm -O litellm litellm_deepseek_staging`.
This does not touch the existing `litellm` database or its volume. No
verification token or paid-provider virtual key is created by staging.

### Local owner one-shot entrypoint

`owner_oneshot_research.py` is the explicit local control-side entrypoint. Its
`preflight` command validates either a P4 decision/request plus policy or a
current owner-bootstrap request, checks the pinned image and frozen read-only
inputs, validates the merged Compose config, and probes the RD-Agent token
bound with networking disabled. It does not start services, create a LiteLLM
user/key, or dispatch research. The `run`
command requires an existing P12 state directory, an owner-managed new
provider secret below `D:/AQ/OPERATIONS/P12`, the protected persistent Compose
env file, and an interactive WSL terminal. It asks the owner to type the exact
request-specific `RUN $5 ONCE sha256:...` confirmation phrase before claiming
the request, creating the one native experiment user/key, and invoking the
full upstream command `rdagent fin_quant --loop-n 1`. Do not invoke it from
Task Scheduler or another unattended process.

For example, after those owner-controlled inputs actually exist:

```sh
python owner_oneshot_research.py preflight \
  --request /mnt/d/AQ/OPERATIONS/P12/owner-input/request.json \
  --policy /mnt/d/AQ/OPERATIONS/P12/owner-input/policy.json

python owner_oneshot_research.py run \
  --request /mnt/d/AQ/OPERATIONS/P12/owner-input/request.json \
  --policy /mnt/d/AQ/OPERATIONS/P12/owner-input/policy.json \
  --state-dir /mnt/d/AQ/OPERATIONS/P12/existing-p12-run/state \
  --new-provider-secret-file /mnt/d/AQ/OPERATIONS/P12/owner-one-shot-secrets/deepseek-flash
```

The existing `P4_LIFECYCLE` request path remains as described. A first
experiment may instead use one explicit `OWNER_INITIAL_BOOTSTRAP` request;
this contract asserts no NO_CHAMPION state, P4 decision, or P2 evidence. To
prepare a review-only package, the control verifies the live frozen P3 factor
materialization report and factor files, P2 source manifest and PIT inventory,
Qlib provider tree/calendar/membership, separate runtime calendars, pinned
image identity, and all five frozen US/PIT templates. The request binds these
SHA256 identities, the `p2_pit` scope, research-family identity, deterministic
budget identity, and `trading_authority: NONE` using RFC 8785 + SHA256.

```sh
python owner_oneshot_research.py prepare-bootstrap-review \
  --output-dir /mnt/d/AQ/OPERATIONS/P12/owner-bootstrap-review/review-unique-id

python owner_oneshot_research.py preflight \
  --request /mnt/d/AQ/OPERATIONS/P12/owner-bootstrap-review/review-unique-id/owner-initial-bootstrap-request.json
```

Choose an unused leaf directory under the isolated `owner-bootstrap-review`
root for each review package; existing packages are never overwritten.

The package is explicitly `REVIEW_ONLY_NOT_APPROVED`; it contains no policy,
owner signature, or paid key. A future local interactive `run` for that request
requires the exact phrase `AUTHORIZE INITIAL $5 RUN <request_id>`. Only after
that confirmation does P12 persist the 24-hour, one-run policy and proceed to
the existing P12 claim and Docker target. Bootstrap is pinned to the single
canonical state directory `/mnt/d/AQ/OPERATIONS/P12/owner-one-shot-state` and
an immutable one-allocation marker, so selecting another `--state-dir` cannot
replenish initial authority. Claim, dispatch, and terminal records include
`request_origin`; cross-origin replay is rejected. This confirmation is local
terminal authority, not an independently signed/cloud-verifiable approval.

For either origin, P12 binds the request and policy to the same deterministic
native LiteLLM experiment user, never resets its budget, will not issue a
replacement key for a user with key history or spend, blocks the scoped key
after a completed attempt, and fails closed on ambiguous dispatch. RD-Agent
receives only the scoped key and Proxy URL. The real provider key stays on the
staging Proxy side. P2 is not invoked or modified; no Candidate, certification,
P4 lifecycle decision, or trading authority is implied by successful research.

No paid key, provider request, or real `fin_quant` run was performed while
adding this path. A future run requires the owner to review the package and
enter its exact request-specific phrase in an interactive local terminal, a
newly owner-provisioned DeepSeek credential, the protected staging Proxy
settings, reachable existing Ollama endpoint, and the canonical durable P12
state directory. The review command does not create a P4 lifecycle decision,
owner approval, policy, key, or dispatch.

Staging startup acceptance on 2026-10-18 used the pinned LiteLLM image and a
dummy provider secret. The separate `litellm_deepseek_staging` database already
existed; migrations completed and the Proxy health endpoint returned 200. The
loaded profile had no global `max_budget`, key defaults of USD 5 / 24h / the
two listed models / one parallel request / null `budget_duration`, and
`router_settings.default_max_parallel_requests: 1`. Only the Flash and local
Ollama routes were registered. The staging Proxy had no worker attached; no
key was created and no chat, embedding, or provider request was sent. The
existing TEST_ONLY Proxy, Mock, PostgreSQL, Redis, health service, and both
named volumes remained healthy/present. The temporary staging Proxy and its
provider egress network were removed without removing volumes.

The running pinned LiteLLM 1.105.1 model-cost map contains the canonical
`deepseek/deepseek-flash` entry for DeepSeek-V4.1-Flash-1017 and matches the
[current official DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing/):
peak/off-peak cache-hit input is $0.006/$0.003 per million tokens,
cache-miss input is $0.30/$0.15, and output is $1.20/$0.60. The equivalent
LiteLLM entries and off-peak windows are in the
[pinned v1.105.1 model map](https://raw.githubusercontent.com/BerriAI/litellm/v1.105.1/model_prices_and_context_window.json);
no AQ price override is needed.
The profile blocks models without known pricing, uses native pre-call budget
reservation and fail-closed budget enforcement, and does not retry. The
existing Ollama model is available locally at the pinned P3 name. A local
LiteLLM embedding request reached it successfully and returned 1024 dimensions;
no Mock embedding is used in this profile. The service requires the operator
to supply
`P12_OLLAMA_API_BASE` explicitly because the current WSL Ollama endpoint is
reachable from Docker only at its current private WSL address; the default
`host.docker.internal` address points to a different host endpoint. If the WSL
address changes, the profile must be updated before it can start. No address
is silently guessed.

Offline acceptance used only a generated dummy provider secret. The pinned
Proxy loaded both configured model routes and served one local Ollama embedding
probe at 1024 dimensions; no DeepSeek chat request was sent and no real
provider virtual key exists in the separate database. Compose inspection
confirmed the staging Proxy alone joins the non-internal provider egress
network, while PostgreSQL, Redis, Mock, and the RD-Agent worker do not. The
worker remains on the existing internal `worker_proxy`; the staging Proxy has
no published port and does not join that worker network. Destination-specific
provider egress filtering is not configured.

Candidate V4 remains frozen with its historical `deepseek/deepseek-chat`
identity. The forward-only Candidate V5 schema records the unchanged P3
LiteLLM client version `1.103.1` and `deepseek/deepseek-flash`; it reuses V3
evidence definitions and does not alter the P2 protocol. The existing V4
materializer remains V4-only. A future V5
materializer must bind actual runtime and provider-response evidence, and P2
must independently decide eligibility.
Simulated spend evidence must be present, Decimal-typed, finite, and
nonnegative before budget comparisons; invalid evidence is denied before any
claim is written. The synthetic fixture's example numeric limits exist only to exercise validation;
they are not proposed or approved real spending amounts. A
`research_budget_identity` or policy hash does not enforce a charge ceiling. The admission result
explicitly identifies spending enforcement as simulation-only and keeps real
dispatch permission denied.

There is no trusted owner-approval/revocation source connected to this adapter,
and there is no fail-closed native spending boundary on P3's direct provider
path. Therefore an otherwise well-formed `HUMAN_APPROVED` policy is denied,
and real dispatch remains unavailable. See the installed-runtime findings
below before treating any future provider allowlist or limit as effective.

### TEST_ONLY signed-policy verification POC

`owner_signed_authority.py` is a thin verifier for the existing
`P12StandingResearchPolicyV1`. Because that policy intentionally has no
signature field, the verifier receives a separate, minimal
`{payload, signature}` evidence envelope; the signed payload binds the exact
policy identity, purpose/domain, key identity, approval-evidence identity,
policy version, effective/expiry times, scope, provenance, research families,
budget identity, and authority epoch. It uses PyCA `cryptography`'s supported
Ed25519 public-key verification API and the already available RFC 8785 0.1.4
implementation. It contains no signing operation or private key.

The P12 admission function accepts this envelope only alongside an explicit
trusted-authority snapshot. The snapshot includes a signed revocation view and
an externally supplied minimum epoch. Missing authority, invalid signatures,
purpose reuse, changed policy/request binding, revoked or expired approvals,
and stale/rolled-back epochs fail closed. The checked-in tests create
ephemeral keys in memory and label all evidence `TEST_ONLY`; successful
verification is not human approval and still reports real dispatch `DENIED`.
The synthetic policy gate still denies `HUMAN_APPROVED` policies. The optional
`--test-signed-approval` and `--test-trusted-authority` intake inputs are only
for this offline POC; both are required together, and a request replay must
present the same currently valid approval evidence to match the durable claim.
For signed mode, claim, dispatch, and terminal markers bind an explicit
`SIGNED_TEST_ONLY` mode, signer key ID, authority epoch, RFC 8785 payload hash,
and a fingerprint of the canonical signed envelope. Replay revalidates the
approval against the current signed revocation snapshot and then compares that
metadata across all three markers. Changed signer/epoch/payload or tampered
metadata fails closed without redispatch. New unsigned records carry an
explicit `UNSIGNED_TEST_ONLY` mode; old unsigned PR157/158 and PR159 records
remain compatible, while old signed records lacking immutable provenance are
blocked.

This is not production rollback protection: this host has no independent,
owner-controlled monotonic epoch source. A signed old revocation snapshot can
be replayed if the independent epoch floor is unavailable or controlled by
the worker. Production owner approval therefore remains untrusted and real
dispatch remains denied. The minimum future authority design is an owner-held
signing key and revocation/epoch source outside the research worker, with only
verification keys and authenticated current snapshots available to P12. The
worker must not control the key configuration, approval evidence, revocation
state, verifier executable, or rollback floor.

### Host identity and provider-bypass findings (2026-10-17)

The current Windows user is `DESKTOP-IG1RJUJ\1`; the existing P12 scheduled
tasks run as that same account. The WSL P3 user is `zhou` (`uid=1000`) and is
in the `sudo` and `docker` groups. The P3 `.env` is mode `0600` and owned by
`zhou`, so this worker identity can read it. It contains a
`DEEPSEEK_API_KEY` entry (the value was not read); the current WSL shell did
not inherit that variable. No RD-Agent dotenv auto-loader was found in the
installed package/startup paths inspected, but a worker running as `zhou` can
read and explicitly load the file, and RD-Agent's LiteLLM backend supports
direct provider credentials. Removing one inherited environment variable
would not close this file-based bypass. Proxy-only worker routing is therefore
not established. Before any real research worker is considered, the owner
must revoke/rotate the P3 DeepSeek credential and provision a worker that can
read only restricted Proxy credentials and approved Proxy URLs.

The prior LiteLLM POC still has `.env` (environment/configuration type),
`virtual-key.txt` and `p3-virtual-key.txt` (token text type). Their contents
were not read. The POC Proxy and database/Redis volumes were removed, so the
test virtual keys have no current backing database. The POC `.env` test
master/salt credentials are not believed to be active against a service now;
the owner should rotate them before restoring that POC service or its data.
The POC directory ACL includes the same Windows account, SYSTEM, and
Administrators, and its WSL `/mnt/d` view is not a worker-isolation boundary.
Deletion was previously rejected by automatic safety review; this task did not
retry or work around that rejection.

No production signing private key was generated. The Windows and WSL users
are not separate security principals for this deployment, and the WSL user
can modify the checked-out verifier. ACLs and Unix modes alone therefore do
not establish owner/worker separation. Owner approval remains untrusted until
code integrity, authority configuration, credential paths, and rollback state
are protected from a dedicated research-worker identity.

Official API references: [PyCA Ed25519 signing and verification](https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/)
and [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785).

Focused verification test command (uses the already installed P3 runtime and
RFC 8785 library; no dependency install):

```bash
export PYTHONPATH=/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001/upstream-libs
/home/zhou/miniforge3/envs/rdagent-official-v1/bin/python -m unittest \
  70-operations-system/research-handoff/tests/test_owner_signed_authority.py -v
```

### P3 provider-path findings

The installed P3 runtime inspected for this change is RD-Agent 1.0.0 with
LiteLLM 1.103.1 at
`/home/zhou/miniforge3/envs/rdagent-official-v1`. Its pinned
`rdagent/oai/backend/litellm.py` calls `litellm.completion()` and
`litellm.embedding()` directly. It accounts for cost after receiving the
response and accumulates it in process-local state; if cost calculation fails,
the code logs the error and records `NaN`. There is no P12 policy lookup,
pre-call spend reservation, provider admission check, or durable cost ledger
on this P3 path. A P12 preflight estimate cannot close that gap.

LiteLLM's Proxy virtual-key model/provider allowlists, persistent budgets, and
spend reservation require its Proxy and database-backed configuration; the
current direct SDK route does not use them. LiteLLM documentation also warns
that DB-less global spend budgets do not enforce spend. A Proxy migration would
be a separate upstream/P3 deployment change and is not part of this adapter.

## Durable claim and recovery behavior

The request-ID-specific claim and subsequent dispatching/terminal state markers
use exclusive file creation (`O_CREAT | O_EXCL`) on the isolated D: host
directory. Each file and its directory are flushed before advancing. A marker
is immutable and is never replaced. On this host's WSL `/mnt/d` mount, a
24-process collision check produced exactly one claim winner; file and
directory `fsync` succeeded. A preliminary concurrent-read test found that
same-directory replacement on this 9P mount can briefly return `ENODATA`, so
the implementation avoids replacement. A partial marker is treated as
ambiguous and blocks without retry.

An existing claim with a terminal status is replayed without another dispatch.
A claim without status, corrupt claim/status, or nonterminal `DISPATCHING`
state is blocked without retry. An interruption after the target starts can
leave an unknown outcome; P12 deliberately does not infer success or retry.
Only a fully consistent `SUCCEEDED_SYNTHETIC` replay exits zero. A failed
terminal replay exits 4; blocked, corrupt, mismatched, and ambiguous replay
states exit 3. Success requires matching request and attempt identities across
all markers, the same currently admitted `standing_policy_id` and policy
admission across claim/dispatch/terminal records, and a terminal return code
consistent with the terminal state. A policy change or persisted identity
mismatch blocks replay without redispatch or record replacement.
This is durable at the host filesystem/process level tested here; it is not an
exactly-once guarantee across arbitrary power loss, device failure, or external
side effects.

## Windows Task Scheduler entry point

`Invoke-SyntheticResearchHandoff.ps1` is an action target for a temporary or
future human-approved Windows Task Scheduler task. It calls WSL Ubuntu 24.04,
the existing P4/RFC 8785-compatible Python environment, and the synthetic-only
P12 CLI. It accepts explicit repository, request, and state paths. This POC
does not register or enable a scheduled task. A one-shot temporary task may be
used for acceptance and then removed; existing P12 tasks are not changed.

Example action arguments (substitute the current worktree and request paths):

```text
-NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "<repo>\70-operations-system\research-handoff\Invoke-SyntheticResearchHandoff.ps1" -RepoRoot "<repo>" -RequestPath "D:\AQ\OPERATIONS\P12\research-handoff-synthetic-poc-001\request.json" -PolicyPath "D:\AQ\OPERATIONS\P12\research-handoff-synthetic-poc-001\test-policy.json" -StateDirectory "D:\AQ\OPERATIONS\P12\research-handoff-synthetic-poc-001\scheduler-run"
```

The scheduled action does not include credentials and cannot enable real P3
dispatch. No permanent task is installed by this change.

## Standing research authorization design

Before any unattended real research, the human owner must approve one
revocable, expiring policy record containing:

- permitted research scope, asset universe, and factor/model families;
- explicit model and provider allowlists, including local versus paid providers;
- a human-selected maximum spend and reset window, with a verifiable spending
  boundary that rejects requests when spend cannot be checked;
- effective and expiration times, approving authority, immutable policy
  identity, and a revocation mechanism;
- a maximum concurrent research-run count enforced at the dispatch boundary;
- an explicit statement that research authorization grants no P2
  certification, P4 promotion, portfolio, broker, or production-trading
  authority.

No dollar amount is proposed here. A policy hash alone is not enforcement. The
P4 request contract currently carries only a budget identity, so P12 must
remain fail-closed until a human-approved policy can be resolved and the real
provider spending boundary is verified. Paid LLM calls, training, and real
dispatch remain unauthorized.

## Bootstrap and event-triggered paths

The synthetic path demonstrates the existing P4 `NO_CHAMPION` reason, so the
first research request does not depend on an existing Champion. A future
scheduled bootstrap may use that same P4 policy decision under a standing
human authorization. Later event-driven research must still arrive as a
validated P4 `ResearchRequestV1`; cadence belongs to P12 and does not enter the
P4 request identity. This POC creates no permanent schedule.

P2 frozen protocols/cohorts remain unchanged. Candidate V4 outside the frozen
P2 V2 cohort remains ineligible. P4-to-P7 provenance remains a separate open
gap. No P2 or P4 downstream decision is fabricated by the P12 test.

## Historical first real research readiness review

This review records the earlier state at its named base commit. The local
owner-initiated one-shot path documented below supersedes its “target not
registered” and “not ready” conclusions for one interactive run only. The
ordinary P12 dispatcher remains TEST_ONLY; this does not authorize unattended
research or change certification/trading boundaries.

At base `e2a6a498b9fffa7fe35646982d757538c165b2e4`, the real fin_quant target
is intentionally not registered in P12. The TEST_ONLY target identities and
durable replay rules remain unchanged. A real target must not be added until
all of the independent authorization, provider-budget, and worker-isolation
gates below are established.

| Readiness item | Current state | Evidence / blocker |
| --- | --- | --- |
| Durable Qlib/RD-Agent outputs | **Not ready** | The TEST_ONLY worker writes `/workspace`, its SQLite MLflow URI, traces, and workspaces to tmpfs; Compose cleanup removes the run. No dedicated persistent run volume is mounted. A future volume must be unique per P12 attempt and retain Qlib/MLflow Recorder artifacts, `task`, `params.pkl`, `dataset`, `pred.pkl`, RD-Agent trace, and lineage. |
| Real-provider Proxy route | **Not ready** | The checked-in Compose config routes only to the local Mock. At review time only `aq-p12-health` was running; no LiteLLM/PostgreSQL/Redis research stack or related Docker volumes were present. The P3 Candidate V4 contract identifies DeepSeek chat, but that identity is not owner approval for future spending. |
| Provider credential isolation | **Not ready** | The existing host audit found the P3 DeepSeek credential file-readable by the WSL P3 account that launches Docker. No provider secret was read. The credential must be revoked/rotated and provisioned only to a separately protected Proxy/control identity; the worker may receive only a model-restricted Proxy virtual key. The current shared Windows/WSL/Docker authority does not prove that separation. |
| Persistent native spend gate | **Not ready** | The Proxy configuration in this Compose is TEST_ONLY and its Postgres/Redis data are removed during teardown. The test virtual-key provisioner sets model allowlists but no per-key spend cap or reset window. P12 admission is synthetic-only; `research_budget_identity` and simulated spend are not enforcement. No approved numeric budget is available, so none is supplied here. |
| Trusted owner approval/revocation source | **Not ready** | The local signature verifier has no independent owner-controlled approval store or monotonic revocation/epoch source. Local files, verifier, and rollback state are writable by the same host/WSL operator. Signed or `HUMAN_APPROVED` fields alone cannot authorize dispatch. |
| Candidate V4 handoff | **Existing, separate** | Keep `project_rdagent_candidate_v4.py` and its V4 contract unchanged. It requires a FINISHED native Qlib Recorder and the four native artifacts before hashing them. P2 retains its independent eligibility decision; a V4 Candidate outside the frozen V2 cohort remains ineligible. No P12-to-materializer invocation is wired by this readiness review. |

Therefore the target remains **DISABLED** and no real provider route or
spending amount is configured. The future bounded command remains
`rdagent fin_quant --loop-n 1`; it may be invoked only after trusted owner
approval and revocation, a persistent Proxy/PostgreSQL budget reservation
with a human-approved limit, provider-key rotation/isolation, and a durable
run-scoped artifact volume are verified together. The real worker must preserve
the existing three read-only P2/P3 data mounts and internal Proxy-only egress.
No schedule or service is enabled by this review.

## Local validation

Use the already installed pinned RD-Agent WSL runtime and RFC 8785 0.1.4
distribution; do not install dependencies for this adapter:

```bash
export PYTHONPATH=/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001/upstream-libs
/home/zhou/miniforge3/envs/rdagent-official-v1/bin/python -m unittest discover \
  -s 70-operations-system/research-handoff/tests -p 'test_*.py' -v
```

Acceptance runs use an isolated directory under
`D:\AQ\OPERATIONS\P12\research-handoff-synthetic-poc-001`. They do not touch
the existing health deployment or its scheduled tasks.

## Persistent LiteLLM TEST_ONLY budget deployment

`docker-rdagent-smoke/compose.persistent-test.yaml` runs only the existing
pinned LiteLLM Proxy, PostgreSQL, Redis, and local Mock images. It uses a
dedicated named PostgreSQL volume and Redis volume, an internal Docker network,
and no host-published ports or research worker. The existing `config.yaml`
routes both configured aliases only to `http://mock:8000/v1`. Admin and
database credentials belong in a separately ACL-protected operations env file;
the Proxy admin credential is not mounted into a research worker. The real
P12 research target remains unregistered and denied.

The acceptance harness `docker-rdagent-smoke/persistent_budget_acceptance.py`
calls LiteLLM's native `/key/generate`, `/key/info`, and chat APIs from the
Proxy control container. It uses a synthetic `$0.0001` test key budget, `1h`
budget reset period and key expiry, and a one-request concurrency bound. These
test values are enforcement fixtures, not owner-approved research spending.
It verifies model allowlisting, Mock-only calls, native spending, budget
exhaustion before Mock, service restart persistence, and PostgreSQL-outage
denial before Mock. Test keys/results live only in the separately mounted
operations state directory.

The persistent Compose model can also be used by the original PR #165
standalone service commands without P12 worker variables. Worker-only values
default to empty for model parsing; the TEST_ONLY worker preflight refuses to
execute RD-Agent unless it receives a non-placeholder scoped key, matching
OpenAI key, request-scoped run namespace, and existing durable per-attempt
output directory.

On the Windows/WSL host, create a dedicated operations directory and state
subdirectory with owner-only ACLs. Put fresh `LITELLM_MASTER_KEY`,
`POSTGRES_PASSWORD`, and `P12_LITELLM_STATE_DIR` values in its external Compose
env file; do not put that file in the repository. Then run:

```bash
docker compose --project-name aq-p12-litellm-persistent-test \
  --env-file /mnt/d/AQ/OPERATIONS/P12/persistent-litellm-budget-001/compose.env \
  -f 70-operations-system/research-handoff/docker-rdagent-smoke/compose.persistent-test.yaml \
  up --no-build --pull never -d postgres redis mock litellm

docker compose --project-name aq-p12-litellm-persistent-test \
  --env-file /mnt/d/AQ/OPERATIONS/P12/persistent-litellm-budget-001/compose.env \
  -f 70-operations-system/research-handoff/docker-rdagent-smoke/compose.persistent-test.yaml \
  exec -T litellm python /app/persistent_budget_acceptance.py setup
```

For restart acceptance, stop `litellm postgres`, start PostgreSQL and wait for
its health check, then start LiteLLM and run the harness `after-restart` phase.
Run `prepare-outage`, stop PostgreSQL, run `outage-check`, start PostgreSQL,
restart LiteLLM, and run `after-outage`. Do not remove the named test volume
when stopping the deployment. This stack is a local TEST_ONLY validation
deployment and grants no real provider spending or P12 research permission.

Observed acceptance: native key creation and constraints passed; two Mock chat
calls recorded `$0.0001`; the next request received LiteLLM `budget_exceeded`
HTTP 422 before Mock; spend and allowlist persisted across a Proxy/PostgreSQL
stop/start; and a chargeable probe during PostgreSQL outage returned HTTP 503
without reaching Mock. Paid provider calls, training, P2 certification, and
broker activity were not performed.

## Acceptance record

On the actual host D: path through WSL's `/mnt/d` 9P/DrvFS mount:

- 24 concurrent `O_CREAT | O_EXCL` attempts produced one durable claim winner;
- file and directory `fsync` succeeded for immutable claim and terminal markers;
- the 16-case durable handoff suite passed twice, covering same-ID replay, same-ID concurrent intake,
  post-claim process interruption, unknown post-dispatch state, failed target,
  failed terminal replay, terminal return-code consistency, mismatched attempt
  identity, corrupt records, and malformed/tampered requests;
- a temporary Windows Task Scheduler task invoked the PowerShell-to-WSL entry
  point and recorded `SUCCEEDED_SYNTHETIC`; the task was then removed;
- a separate temporary task replayed an interrupted claim and reported
  `LastTaskResult=3`; successful and failed terminal wrapper replays returned
  0 and 4 respectively. Temporary tasks were removed;
- no P3 command, LLM/provider, Qlib, certification, broker, or production
  action was invoked. The synthetic terminal record has zero Candidates.

The standing-policy tests add eleven focused cases for policy hash tampering,
untrusted owner approval, expiry/revocation, P4 scope/provenance/budget
binding, provider/model allowlists, unknown or exceeded simulated spend,
negative/non-finite/invalid spend representations, concurrency, and resource
caps. Replay tests cover same-policy replay, changed valid policy, and
tampered policy identity in persisted records. The focused offline
suite contains 88 tests. Those synthetic admission tests do not by themselves
prove provider charging enforcement or a race-safe real concurrency limit;
the separate live LiteLLM acceptance above verifies pre-call rejection for
the local TEST_ONLY Mock budget fixture only, not for real provider spending.

The acceptance record proves process-level durable replay on this host file
path. It does not prove recovery from power loss, disk/controller failure, or
exactly-once external effects.

## Native cumulative experiment budget binding

`docker-rdagent-smoke/native_experiment_budget.py` binds P12's canonical
`research_budget_identity` to one domain-separated deterministic LiteLLM
`user_id`. P12 writes that identity and user ID into its immutable claim,
dispatch, and terminal records; replay rejects a changed binding. The
control-side adapter uses LiteLLM's native `/user/new`, `/user/info`,
`/key/generate`, and `/key/info` APIs. A user has one persistent
`max_budget` with `budget_duration: null`; keys attach to that same user and
have their own non-resetting budget cap, no more than 24-hour expiry, exact
Mock/local-embedding model allowlist, and concurrency one. Replays verify the
existing user and never allocate a new one or issue a key. A missing native
user on replay, changed budget, reset, model scope, or mismatched user ID fails
closed.

The live acceptance harness uses a separate synthetic P12 request and a
`$0.00012` TEST_ONLY user budget, not the future `$5.00` owner budget. Two
separately issued Mock keys share the native user spend; a third key is denied
before Mock when aggregate spend is exhausted. The same user budget and spend
were observed after restarting only the existing persistent TEST_ONLY
PostgreSQL container. P12 and LiteLLM replay checks made no user-allocation or
key-generation call. Temporary keys are blocked after the persistence check.

Historical state at this section’s acceptance date: real issuance was
hard-denied because no independent owner-controlled approval/revocation
source was available. The local one-shot mechanism documented above is the
current exception for an owner physically operating the trusted host; it does
not turn local policy files or signed test snapshots into independent
authority, and it does not enable unattended runs. No `$5` user/key was
created by that earlier acceptance. This integration still confers no P2
certification, Candidate eligibility, production, or broker authority.

Live cumulative-budget acceptance on 2026-10-18 used P12 synthetic request
`sha256:94d8470c76fea98a3ce40260742a7401f88b0c47579bdf9c163c92e2c2e9b3cd`,
policy `sha256:15cba385da6e181f862e80873e438978119492fcb686ff302ed3e62f712d371a`,
and deterministic native user `aq-p12-exp-6a7844cc2873afa3176a94a5e4912e5871274eb7267abf842d401718f703effc`.
The `$0.00012` TEST_ONLY user spend rose from `$0` to `$0.00005` through Key A,
then to `$0.00010` through Key B. Key C was denied and the Mock chat count did
not increase. P12 and LiteLLM replay checks reused the same request, attempt,
and native user without `/user/new` or `/key/generate` calls. After restarting
only `aq-p12-litellm-persistent-test-postgres-1` on the existing
`aq-p12-litellm-test-pgdata` volume, the user ID, non-resetting `$0.00012`
budget, and `$0.00010` spend remained; Key C remained denied before Mock.
Temporary keys were blocked after the check. The P12 fixture generated no
Candidate and performed no training, certification, provider, or broker call.

## AWS owner approval and revocation authority (offline implementation)

`aws_owner_authority.py` is a thin adapter around the existing P12 Ed25519/RFC 8785 verifier, native LiteLLM experiment user identity, and the AWS SDK. It introduces no signing format, budget engine, or dispatch permission. The adapter has been exercised only with in-memory local Ed25519 test keys and simulated KMS, DynamoDB, and STS responses. No AWS account, resource, approval, paid key, or provider call was used. Even a verified approval currently returns `real_dispatch_permission: DENIED`; P12 real dispatch remains disabled.

### Authority record and identity

Use one DynamoDB table whose partition key is the string `research_budget_identity`. Each item binds that identity to exactly one P4 `request_id`, P12 `policy_id`, and deterministic `native_experiment_user_id` from `native_experiment_budget.experiment_user_id()`. A conditional create prevents another approval or budget allocation for that identity. The record contains the signed canonical approval, current epoch/status, KMS key ARN, and a separately signed revocation snapshot. Runtime reads use `GetItem(ConsistentRead=True)` on every verification. There is no local APPROVED cache or local flag override.

Approvals are limited by the adapter to the existing P12 policy contract with USD 5.00 maximum run and period spend, DeepSeek Flash plus local Ollama embedding routes, exact P4 request scope/provenance/families, one concurrent run, and an approval interval no longer than 24 hours. It does not issue a LiteLLM key or change any existing key/user. The existing native user budget/key issuance workflow remains a separate boundary and is still hard-denied for real issuance until separately integrated and explicitly authorized.

The KMS key must use `ECC_NIST_EDWARDS25519`, `SIGN_VERIFY`, and `ED25519_SHA_512`; the adapter signs RFC 8785 bytes with `MessageType=RAW`. It checks the returned KMS key ARN and derives the trusted public key identity from `GetPublicKey`. DynamoDB approval creation is conditional on the identity not existing. Revocation conditionally advances the epoch and changes current status; stale writes lose the compare-and-swap. Runtime verifies the current record and both signatures, requires approval and revocation epochs to match the strongly read current epoch, and denies unavailable AWS, stale, revoked, expired, or mismatched state.

### Permission split and setup

Create AWS resources only through the owner's normal infrastructure process. Keep the owner role and research runtime role distinct:

- **Owner role:** require authenticated AWS IAM Identity Center/SSO or equivalent interactive owner session. Grant `sts:GetCallerIdentity`, `kms:GetPublicKey`, `kms:Sign` on the one approval key, and DynamoDB `GetItem`, `PutItem`, `UpdateItem` on the one authority table. Do not grant key administration, table administration, deletion, or permission to use the role from the WSL/research identity.
- **Runtime control role:** grant only DynamoDB `GetItem` on the authority table and KMS `GetPublicKey` on the configured key. It has no signing or write permission. Its credentials, if later deployed, must remain in a trusted P12 control process, outside the RD-Agent container.
- **RD-Agent worker:** no AWS role, credentials, KMS permission, DynamoDB permission, owner secret, Proxy master key, or provider credential.

The runtime verifies the configured KMS key ARN on every lookup and does not trust a key identity supplied by the approval file. Protect the control role and owner role with separate AWS trust policies and independently authenticated principals. Since no AWS account was available for this task, actual IAM separation, key policy, resource policy, and AWS conditional-write behavior have not been live-tested.

For an eventual owner setup, after the owner has provisioned and reviewed the key/table and IAM policies:

1. From the independently controlled owner workstation, authenticate to the owner role with the organization's MFA-backed AWS SSO/assume-role flow. Set `AWS_PROFILE`, `AWS_REGION`, `AQ_OWNER_AUTHORITY_TABLE`, `AQ_OWNER_KMS_KEY_ARN`, and `AQ_OWNER_ROLE_ARN` in that owner shell only.
2. Review the exact P4 ResearchRequestV1 and a genuine, deliberately prepared `HUMAN_APPROVED` P12 policy. Confirm its unique `research_budget_identity`, $5.00 run/period ceiling, exact model routes and US/PIT scope, one run/concurrency, and expiry within 24 hours. The approval command requires the explicit `--confirm-owner-approval` switch and never creates owner approval by itself.
3. Record the approval through `python aws_owner_authority.py approve --request <request.json> --policy <policy.json> --confirm-owner-approval`. The row is immutable with respect to initial issuance; a duplicate identity is denied, not replenished.
4. A trusted control-side verifier may use `python aws_owner_authority.py verify --request <request.json> --policy <policy.json>`; verification is read-only and must be repeated against current AWS state immediately before any future dispatch.
5. To revoke, use the owner role and `python aws_owner_authority.py revoke --research-budget-identity <sha256:...> --approval-evidence-identity <sha256:...> --expected-epoch <current-epoch>`. A successful revocation advances the epoch and cannot be undone by replaying an old approval snapshot.

Do not copy the owner profile or credentials to the Windows research account, WSL research process, Docker image, or worker. There is no automatic approval, renewal, reissue, key creation, deployment, or real dispatch in this implementation. AWS KMS Ed25519 and DynamoDB consistency/conditional-write references: [KMS key specs](https://docs.aws.amazon.com/kms/latest/developerguide/symm-asymm-choose-key-spec.html), [KMS Sign API](https://docs.aws.amazon.com/boto3/latest/reference/services/kms/client/sign.html), [DynamoDB strongly consistent GetItem](https://docs.aws.amazon.com/boto3/latest/reference/services/dynamodb/table/get_item.html), and [DynamoDB conditional expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html).
