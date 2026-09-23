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

## Four operating rules

These are the four root operating rules. They are one consolidated authority,
not a stack of independent governance frameworks.

### 1. `UPSTREAM_FIRST`

Use a mature upstream capability directly. AQ does not reimplement a
capability already owned by a mature selected upstream.

From AQ's perspective, selected upstream implementation code is read-only. AQ
production must not:

- modify installed `site-packages`;
- monkeypatch upstream methods or classes;
- vendor and modify upstream source;
- retain an AQ fork as a hidden production dependency;
- override upstream parser, accounting, period, or statement algorithms;
- introduce issuer-specific patches to repair upstream output; or
- reproduce an upstream internal algorithm to fix edge cases.

AQ may pin an official release/SHA, configure it, call public APIs, validate
and adopt a later official release, replace it with another mature upstream,
or exclude/defer unsupported cases.

The existing hard rule remains:

```text
NO AQ ENGINE WITHOUT UPSTREAM REJECTION EVIDENCE
```

It is a necessary condition, not a sufficient one:

```text
UPSTREAM_REJECTION_EVIDENCE != CUSTOM_ENGINE_AUTHORIZATION
```

The default decision order is:

1. use the current mature upstream as-is;
2. when necessary, evaluate an official newer version;
3. evaluate another mature upstream;
4. exclude, mark missing, defer, or narrow scientific scope; and
5. consider custom AQ implementation only for a genuinely AQ-specific
   capability with no reasonable upstream owner, or, after determining no
   mature upstream is reasonable, with separate explicit human authorization.

An upstream edge case or incomplete coverage alone does not authorize custom
AQ repair code.

### 2. `THIN_INTERFACE_ONLY`

AQ may connect upstreams through the smallest required project-specific
boundary. Allowed scope includes configuration, input/output shape conversion,
column/name projection, AQ episode/CIK identity, AQ PIT admission, AQ
calendar/session visibility policy, AQ feature inventory, AQ
certification/risk policy, and narrow provenance contracts.

A thin interface may apply AQ-owned project semantics. It must not alter or
"correct" semantics owned by an upstream project.

- Allowed: upstream `Total Assets` to AQ column `Assets`.
- Allowed: SEC acceptance datetime to AQ's first XNYS-visible session.
- Not allowed: a custom AQ semantic correction table that overrides an
  upstream accounting classification.

### 3. `FAIL_CLOSED_NOT_FIX_EVERYTHING`

Unsupported, ambiguous, unavailable, or unverifiable upstream cases default
to `MISSING`, `EXCLUDED`, `DEFERRED`, or `UPSTREAM_REPLACEMENT`. They do not
automatically authorize custom AQ repair code.

### 4. `ONE_PRODUCTION_OWNER_PER_CAPABILITY`

One capability has one production owner. A pipeline may compose multiple
upstreams only when each owns a distinct capability. AQ must not retain a
second production implementation of an upstream-owned capability.

## Correctness and coverage

```text
ADMITTED_DATA_INTEGRITY = STRICT
SOURCE_COVERAGE_TARGET = NOT_UNIVERSALLY_100_PERCENT
UNVERIFIABLE_SOURCE_ROWS = MISSING_OR_EXCLUDED
HEURISTIC_REPAIR = PROHIBITED
```

AQ requires complete correctness and provenance for admitted records, not
universal source coverage by default. For example, 53,213 authoritative
records plus five unverifiable records is valid as 53,213 admitted, five
excluded, and zero guessed. Five exclusions do not by themselves require a
resolver, patch, new engine, or phase blocker.

## Phase-specific completeness

A frozen scientific or certification contract may genuinely require complete
coverage of its defined population. Unresolved coverage may then block that
specific experiment. Permitted responses are to narrow and re-freeze scope
before evaluation, replace the upstream, defer the capability, or classify the
experiment incomplete. This does not authorize patching upstream semantics or
creating another generic AQ implementation.

## Anti-bloat interpretation

A governance rule should normally reduce implementation surface. If satisfying
a rule appears to require a new `Engine`, `Framework`, `Registry`, `Store`,
`Runner`, `Coordinator`, `Resolver`, `Finalizer`, or `Manager`, re-examine the
rule and design before implementation. Governance must not create machinery
solely to prove compliance with governance.

Prefer updating existing authority, reusing upstream evidence, simple tests,
and explicit missing/exclusion states over permanent verifier stacks, artifact
registries, orchestration layers, or documentation cascades.

## Implementation ownership modes

Every implementation task must select exactly one of these three modes.

### 1. `UPSTREAM_WHOLE`

A complete upstream project owns the capability. AQ may contain only the
minimum necessary configuration, adapter, public contract, project policy,
version/SHA authority, and health or upgrade evidence. AQ must not duplicate
the upstream engine. Current examples are Qlib and RD-Agent. LEAN uses this
mode if it is adopted. FinRL-X uses this mode if a future audit selects it.

### 2. `UPSTREAM_LEAF`

A focused upstream library naturally owns one bounded leaf. AQ may add a thin
wrapper or configuration only when necessary. Current examples are
`exchange_calendars`, Pandera, DVC, and skfolio.

### 3. `AQ_OWNED`

Custom implementation is permitted only for project-specific behavior that
cannot reasonably be delegated upstream. Examples include human-owned capital
limits and production permission, risk ceilings, promotion/certification
policy, AQ-specific accepted PIT facts, necessary cross-upstream contracts,
thin adapters, and project-specific audit semantics.

`AQ_OWNED` does not authorize a generic engine by default.

## Mandatory implementation-task preamble

The preamble is a human-readable design checkpoint. Do not build tooling to
enforce it.

```text
CAPABILITY:
<name>

PRODUCTION_OWNER:
<upstream project/library/AQ>

OWNERSHIP_MODE:
UPSTREAM_WHOLE
UPSTREAM_LEAF
AQ_OWNED

AQ_ALLOWED_SCOPE:
<none/config/adapter/contract/policy/domain-facts>

CUSTOM_ENGINE_REQUIRED:
YES/NO
```

If `CUSTOM_ENGINE_REQUIRED = YES`, also provide:

```text
CUSTOM_ENGINE_JUSTIFICATION:
<why this is genuinely AQ-specific and why mature upstreams cannot own it>
```

When `PRODUCTION_OWNER` is an upstream, the default is
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

### P2 certification-data composition

The authoritative capability split is recorded in
`p2-data-upstream-substitution-audit-001.md`:

- Quantiacs remains a direct primary data candidate; OpenBB is the gateway for
  compatible alternate providers, with yfinance owning Yahoo acquisition.
- edgartools owns generic SEC retrieval and parsing; OpenFIGI is supporting
  identifier evidence, not PIT episode authority.
- DuckDB owns deterministic relational composition, joins, gap queries, and
  duplicate/conflict query mechanics. AQ owns source-precedence policy.
- Pandera, `exchange_calendars`, DVC, and Qlib retain validation, session,
  reproducibility, and downstream research ownership respectively.
- AQ retains only thin `InstrumentEpisodeV1` facts, provenance contracts,
  certification/terminal policy, adapters, and configuration.

```text
DATA_GENERIC_ENGINE_POLICY = UPSTREAM_FIRST_NO_CUSTOM_ENGINE_WITHOUT_REJECTION_EVIDENCE
CUSTOM_ENGINE_REQUIRED = NO
```

AQ must not add generic downloader/provider, HTTP/retry/cache, SEC parser,
security-master, merge/composition, artifact/version, or training-data engines
unless a later audit first records explicit upstream rejection evidence.

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

## Historical authority and P5 example

Historical Project Brain documents remain evidence of decisions at their
time. Where historical wording implies that every source row must be repaired
or admitted, every upstream gap requires AQ remediation, every logical tree
node requires AQ implementation, every failure blocks the whole phase, or
upstream-owned semantics should be corrected in AQ, that interpretation is
superseded by this consolidated Upstream Ownership Model. Historical documents
do not need to be mass-edited.

For P5, five unverifiable accession cases may remain excluded; old PID403
failures do not require AQ repair; ambiguity in the upstream semantics of
`ShortTermDebt` does not authorize AQ accounting patches; a selected upstream
remains untouched; and unsupported optional capabilities may be deferred.
These examples do not change P5 implementation or scientific scope.
