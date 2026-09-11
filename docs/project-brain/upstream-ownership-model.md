# Upstream Ownership Model

## Authority

This document defines how the AUTONOMOUS_QUANT logical tree is interpreted.
It is an architecture and governance rule, not an implementation backlog.

```text
TREE != SELF-WRITTEN IMPLEMENTATION MAP
TREE = RESPONSIBILITY AND MAINTENANCE MAP
```

The tree records which capability exists, who owns it, where AQ connects to
it, and where maintainers should look for configuration, replacement,
maintenance, and audit evidence. A tree node may be satisfied by an entire
upstream project, one focused upstream library, or AQ-owned domain/policy
code. An upstream project does not need to be copied, split, vendored, or
reimplemented to mirror AQ's logical tree. A naturally monolithic upstream is
used as a whole and AQ exposes only the necessary interfaces and policy
boundaries.

## Implementation ownership modes

Every implementation task must select exactly one of these three modes.

### 1. `UPSTREAM_WHOLE`

A complete upstream project owns the capability. AQ may contain only the
minimum necessary:

- version/SHA authority;
- configuration;
- adapter;
- public contract;
- health check;
- upgrade notes;
- orchestration entry;
- policy boundary.

AQ must not duplicate the upstream engine. Current examples are Qlib and
RD-Agent. LEAN uses this mode if it is adopted. FinRL-X uses this mode if a
future audit selects it.

### 2. `UPSTREAM_LEAF`

A focused upstream library naturally owns one bounded leaf. AQ may add a thin
wrapper or configuration only when necessary. Current examples are
`exchange_calendars`, Pandera, DVC, and skfolio.

### 3. `AQ_OWNED`

Custom implementation is permitted only for project-specific behavior that
cannot reasonably be delegated upstream. Examples include:

- human-owned capital limits and production permission;
- risk ceilings;
- promotion and certification policy/thresholds;
- AQ-specific accepted PIT facts;
- necessary cross-upstream contracts and thin adapters;
- audit semantics and project-specific routing decisions.

`AQ_OWNED` does not authorize a generic engine by default.

## Root hard rule

```text
NO AQ ENGINE WITHOUT UPSTREAM REJECTION EVIDENCE
```

Before implementing any new capability:

1. Inspect already selected and deployed upstream projects.
2. Inspect other mature upstream projects when necessary.
3. Identify the upstream capability owner.
4. Select one ownership mode.
5. If a mature upstream already owns the capability, limit AQ implementation
   to configuration, adapter, contract, policy, orchestration, or
   project-specific facts.
6. Allow a custom AQ engine only when no suitable upstream exists or the
   behavior is genuinely AQ-specific.
7. Document the reason before implementation.

Any task that skips this ownership check is architecturally invalid.

## Mandatory implementation-task preamble

Every future implementation task must begin with this completed preamble:

```text
CAPABILITY:
<name>

UPSTREAM_OWNER:
<project/library/NONE>

OWNERSHIP_MODE:
UPSTREAM_WHOLE
UPSTREAM_LEAF
or AQ_OWNED

UPSTREAM_ALREADY_DEPLOYED:
YES/NO

AQ_IMPLEMENTATION_ALLOWED:
YES/NO

AQ_ALLOWED_SCOPE:
config
adapter
contract
policy
orchestration
domain-facts
<subset>

CUSTOM_ENGINE_REQUIRED:
YES/NO

CUSTOM_ENGINE_JUSTIFICATION:
<required only if YES>
```

When `UPSTREAM_OWNER != NONE`, the default is
`CUSTOM_ENGINE_REQUIRED = NO`.

## Authoritative capability ownership

### Quant research

**Primary owner:** Microsoft Qlib

**Mode:** `UPSTREAM_WHOLE`

Where its supported interfaces are suitable, Qlib owns Dataset/DatasetH,
data handlers, Alpha158/Alpha360, model training, experiment workflow,
prediction generation, ranking, Top-K strategy, research backtesting,
transaction-cost simulation, portfolio analysis, and rolling/online research
capabilities. AQ must not create duplicate engines for them.

### Autonomous research

**Primary owner:** Microsoft RD-Agent / RD-Agent(Q)

**Mode:** `UPSTREAM_WHOLE`

RD-Agent owns automated factor proposal and implementation, automated model
proposal, iterative factor/model research, and research-loop automation. AQ
owns only policy, budget, and permission boundaries around it.

### Portfolio and statistical tooling

**Primary owners:** Qlib and skfolio

**Modes:** `UPSTREAM_WHOLE` and `UPSTREAM_LEAF`, respectively

Qlib owns its native portfolio and backtest components. skfolio may own
portfolio optimization, WalkForward, CombinatorialPurgedCV, MeanRisk, and
compatible statistical/portfolio tooling. AQ owns portfolio policy and risk
limits, not a generic optimizer engine.

### Execution

**Preferred candidate:** QuantConnect LEAN

**Mode if adopted:** `UPSTREAM_WHOLE`

LEAN is a selected execution candidate, not yet adopted as production
authority. Adoption requires a later execution audit to close its runtime
prerequisites. If adopted, LEAN owns the event engine, order management,
fills, fees, slippage, brokerage models, paper/live execution, and
portfolio/account state. AQ would own only the TargetPortfolio-to-LEAN
adapter, production permission, risk envelope, kill authorization/policy, and
audit mapping.

### Data and information gateway

**Owner/candidate:** OpenBB

**Mode:** `UPSTREAM_WHOLE`

**Role:** provider gateway

OpenBB owns provider access for market data, fundamentals, macro, news, and
provider integrations where suitable. It is not mandatory when another
selected upstream owns the needed capability more cleanly; for example, a
Qlib-native market-data path may directly serve a Qlib-native P1 baseline.

### Trading calendar

**Owner:** `exchange_calendars`

**Mode:** `UPSTREAM_LEAF`

AQ must not implement an exchange-calendar engine.

### Schema validation

**Owner:** Pandera

**Mode:** `UPSTREAM_LEAF`

AQ owns only its domain-specific invariants.

### Reproducibility and data-pipeline tracking

**Owner:** DVC

**Mode:** `UPSTREAM_LEAF`

AQ must not implement a generic artifact engine, cache engine, dependency
graph engine, or pipeline reproducibility engine.

### PIT universe

**Mode:** `AQ_OWNED` thin domain

AQ owns only the accepted project-specific S&P 500 PIT facts,
membership/identity semantics, ticker reuse/re-entry facts, and the
research-ready policy boundary. This must not grow into a generic security
master. Strict institutional-grade PIT completeness remains deferred.

### FinRL-X

**Status:** challenger/fallback only

**Mode if selected:** `UPSTREAM_WHOLE`

AQ must not mimic FinRL-X. FinRL-X is not selected unless a future audit
explicitly adopts it.

## Logical versus physical repository shape

The logical tree remains the navigation map for ownership, responsibility,
replacement boundaries, maintenance, and audits. Physical implementation may
live entirely in an external upstream project. For example,
`30-research-system/model-training` can mean `OWNER = Qlib` and require no AQ
model-training engine. Execution nodes can mean `OWNER = LEAN` and contain
only documentation, configuration, or an adapter if LEAN is adopted.

An upstream-owned node may, where useful, contain only:

```text
README.md
owner.yaml (or an equivalent ownership descriptor)
config/
adapter/
tests/
```

This shape is optional, not universal. Third-party source and runtime remain
outside the authoritative AQ repository unless a future explicit decision
says otherwise.

## P1 composition rule

P1 Minimal Quant primarily composes Qlib:

```text
selected upstream market data
        ↓
Qlib native data layer
        ↓
Qlib DatasetH
        ↓
Qlib Alpha158
        ↓
Qlib model
        ↓
Qlib prediction / ranking
        ↓
Qlib Top-K
        ↓
Qlib backtest
        ↓
Qlib portfolio analysis
```

AQ responsibility on this path is limited to configuration, policy metadata,
minimal experiment/run routing, result classification, and project-specific
boundaries. These Qlib-owned capabilities are not AQ engines to implement.

## Prospective P2+ rule

- Certification uses upstream statistical libraries first; AQ owns decision
  and promotion policy.
- Autonomous research uses RD-Agent for the research loop.
- Portfolio construction uses Qlib/skfolio generic machinery.
- Execution uses LEAN or another explicitly selected execution upstream for
  generic execution machinery.
- Operations uses mature scheduler and monitoring infrastructure where
  appropriate; the tree does not mandate a custom AQ scheduler, dashboard,
  or health platform.

Historical Project Brain documents remain evidence of their time. If their
wording implies that every logical node requires custom AQ implementation,
that interpretation is superseded by this decision.
