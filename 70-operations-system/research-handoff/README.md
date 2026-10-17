# P12 durable synthetic research handoff

## Scope and owners

This is a thin, test-only P12 adapter. P4 owns lifecycle meaning and creates
`LifecycleDecisionEvidenceV1` and `ResearchRequestV1`; RD-Agent owns autonomous
research; Qlib owns training and Recorder outputs; P2 alone owns certification.
The default P12 dispatch target is an inert local synthetic executable. One
explicit `TEST_ONLY` option runs a bounded official RD-Agent chat/embedding
backend smoke through the existing Docker Compose/LiteLLM Proxy/mock pattern.
The Docker target does not start a research loop, Qlib, DVC, MLflow, a real
provider, or a broker.

P3's documented future native command remains
`rdagent fin_quant --loop-n 1`. That research loop is not present as a dispatch
option here. The Docker target calls only RD-Agent 1.0.0's native chat and
embedding backend methods. Real dispatch permission is always `DENIED`.

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
tampered policy identity in persisted records. Together the offline suite
contains 42 tests after adding the signed-authority and replay-provenance POC
cases. Its budget checks are synthetic admission tests only: they
do not prove pre-call provider charging enforcement or a race-safe real
concurrency limit.

The acceptance record proves process-level durable replay on this host file
path. It does not prove recovery from power loss, disk/controller failure, or
exactly-once external effects.
