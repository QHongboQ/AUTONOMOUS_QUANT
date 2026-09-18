# P4 residual thin policy

## Ownership preamble

```text
CAPABILITY = P4 research lifecycle meaning and decision policy
UPSTREAM_OWNER = NONE_FOR_AQ_DOMAIN_MEANINGS
OWNERSHIP_MODE = AQ_OWNED
UPSTREAM_ALREADY_DEPLOYED = YES_FOR_METRICS_IDENTITY_DRIFT_AND_REPRODUCIBILITY
AQ_IMPLEMENTATION_ALLOWED = YES
AQ_ALLOWED_SCOPE = DOMAIN_FACTS; CONTRACT; POLICY
CUSTOM_ENGINE_REQUIRED = NO
```

Qlib owns metric computation and Recorder/online mechanics, MLflow owns
experiment/run/artifact identity, Frouros owns ADWIN mathematics, DVC owns
reproducibility identity, RFC 8785 owns semantic canonicalization, P2 alone
owns certification, and P12 owns scheduling. This directory contains one
closed P4 policy module, one generated JSON Schema snapshot, and focused
synthetic tests. It contains no workflow, FSM, rules, metric, drift,
persistence, registry, event-store, or scheduler engine.

## Closed V1 and preregistered V2 semantics

The lifecycle states are exactly `RESEARCH_CANDIDATE`, `CERTIFIED`, `SHADOW`,
`CHAMPION`, `DEGRADED`, and `RETIRED`. The only edges are:

```text
RESEARCH_CANDIDATE -> CERTIFIED  (P2 authority only)
CERTIFIED -> SHADOW
SHADOW -> CHAMPION
CHAMPION -> DEGRADED
DEGRADED -> RETIRED
```

`CHALLENGER` is a role permitted only for Certified or Shadow subjects.
Champion is a research lifecycle role and never authorizes production, live
trading, capital, leverage, or risk-limit changes.

The module consumes closed references to P2 certification, Shadow evidence,
Qlib/MLflow/DVC identity, the immutable RankIC observation stream, Frouros
detector evidence, and its upstream identity projection. A Frouros change is
insufficient for degradation without separately supplied adverse RankIC
summary evidence and an explicit policy configuration.

V1 remains unchanged and retains its historical unset/test-only meanings:

```text
PRODUCTION_DECAY_POLICY_STATUS = UNSET_REQUIRES_PREREGISTRATION
DEFAULT_PRODUCTION_DECAY_THRESHOLDS = NONE
```

Only synthetic tests may use `TEST_ONLY_POLICY_CONFIG` and
`TEST_FIXTURE_NOT_REAL_EVIDENCE`.

The first production policy is the immutable
`config/financial_decay_policy_v2.json`. Its RFC 8785 semantic identity is:

```text
sha256:3b95c4671bf75c933437659b971477ae6241f70428c638ae81690c4aa6182854
```

It monitors only upstream-computed daily RankIC. The reference is a frozen
252-session baseline; the current window contains 63 trailing XNYS sessions;
policy evaluation occurs every 21 sessions; and three consecutive eligible
evaluations are required. A current window may not begin before the
2026-10-01 effective epoch. One ADWIN event alone is never sufficient:
financial deterioration of at least 0.03, complete sample counts, and all
three persistence confirmations must also be present. Pre-epoch observations
may establish the frozen reference, but they are not prospective validation
evidence.

Any threshold change requires a new version, content identity, rationale, and
future effective epoch. Retroactive relabeling is prohibited.

## Research Request identity

`ResearchRequestV1` is producer-neutral. Its ID is SHA-256 over the upstream
Python `rfc8785` 0.1.4 JCS bytes of every immutable non-ID field. The contract
cannot carry AlphaGen parameters, RD-Agent prompts, training commands,
scheduler cadence, or promotion authority.

## Validation

Tests use the already-frozen RFC 8785 distribution under private P3 evidence;
no package is installed or added by this implementation:

```bash
PYTHONPATH=/mnt/d/AQ_DATA/P3/candidate-v3-materialization-001/upstream-libs \
  /home/zhou/miniforge3/envs/rdagent4qlib/bin/python -m unittest discover \
  -s 40-certification-system/champion-challenger/p4-residual-thin-policy/tests \
  -p 'test_*.py' -v
```

The test suite covers all 36 ordered state pairs, P2 and Shadow fail-closed
boundaries, statistical-versus-financial corroboration, retirement authority,
RFC 8785 request and policy identity, prospective effective-epoch enforcement,
deterministic replay, and absence of runtime or persistence dependencies. It
uses no real Candidate RankIC, historical TEST, Shadow, or sealed OOS data.
