# P12 durable synthetic research handoff

## Scope and owners

This is a thin, test-only P12 adapter. P4 owns lifecycle meaning and creates
`LifecycleDecisionEvidenceV1` and `ResearchRequestV1`; RD-Agent owns autonomous
research; Qlib owns training and Recorder outputs; P2 alone owns certification.
This adapter does not run RD-Agent, Qlib, DVC, MLflow, a provider, or a broker.
Its only dispatch target is a local inert executable that records a synthetic
invocation and reports zero Candidates.

P3's documented future native command remains
`rdagent fin_quant --loop-n 1`. The real command is not present as a dispatch
option here. Real dispatch permission is always `DENIED`.

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
all markers and a terminal return code consistent with the terminal state.
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
-NoLogo -NoProfile -NonInteractive -ExecutionPolicy RemoteSigned -File "<repo>\70-operations-system\research-handoff\Invoke-SyntheticResearchHandoff.ps1" -RepoRoot "<repo>" -RequestPath "D:\AQ\OPERATIONS\P12\research-handoff-synthetic-poc-001\request.json" -StateDirectory "D:\AQ\OPERATIONS\P12\research-handoff-synthetic-poc-001\scheduler-run"
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

Use the already installed WSL runtime and RFC 8785 0.1.4 distribution; do not
install dependencies for this adapter:

```bash
export PYTHONPATH=/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001/upstream-libs
/home/zhou/AQ_ENVS/rdagent/bin/python -m unittest discover \
  -s 70-operations-system/research-handoff/tests -p 'test_*.py' -v
```

Acceptance runs use an isolated directory under
`D:\AQ\OPERATIONS\P12\research-handoff-synthetic-poc-001`. They do not touch
the existing health deployment or its scheduled tasks.

## Acceptance record

On the actual host D: path through WSL's `/mnt/d` 9P/DrvFS mount:

- 24 concurrent `O_CREAT | O_EXCL` attempts produced one durable claim winner;
- file and directory `fsync` succeeded for immutable claim and terminal markers;
- the 13-case suite passed twice, covering same-ID replay, same-ID concurrent intake,
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

The acceptance record proves process-level durable replay on this host file
path. It does not prove recovery from power loss, disk/controller failure, or
exactly-once external effects.
