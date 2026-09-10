# P0 Upstream Fit Audit

> Status: **REMOTE DESK AUDIT COMPLETE / LOCAL POC NOT STARTED**
>
> Repository: `QHongboQ/AUTONOMOUS_QUANT`
>
> Project phase: **P0 — Upstream Fit Audit**
>
> Rule: this document records capability/maturity fit. It does **not** authorize production trading or imply profitability.

## 1. Audit objective

Determine the smallest mature upstream stack that can support the project goal:

- US-equity / ETF first;
- autonomous factor/model research;
- point-in-time aware data handling;
- model/alpha tournaments;
- robust certification against overfitting;
- portfolio construction and risk controls;
- paper/live execution;
- eventual Robinhood-first execution and later multi-asset expansion;
- minimal self-written infrastructure;
- 256 GB local-storage ceiling.

P0 has two stages:

1. **Remote desk audit** — documentation, architecture, active status, overlap, interfaces, known limitations.
2. **Local POC** — install/run only shortlisted components, measure resource cost, verify contracts and failure modes.

This file completes stage 1 only.

---

## 2. Executive decision

### Preferred modular stack to POC

```text
Data providers
    ↓
OpenBB gateway / direct provider adapters
    ↓
Qlib
    ↓
RD-Agent(Q)
    ↓
Certification layer
    ├── Qlib evaluation
    └── skfolio financial CV / portfolio controls
    ↓
TargetPortfolio contract
    ↓
Execution adapter
    ├── Robinhood Trading MCP — PRIMARY broker candidate
    └── LEAN — mature alternate execution/reference candidate
```

### Full-stack challenger

```text
FinRL-X / FinRL-Trading
```

FinRL-X receives an independent POC because it may replace several modular components with one stack. It is **not** selected as production authority yet because it is still a comparatively new public production-oriented release.

### Research-only challengers

- TradingAgents
- FinGPT / FinBERT
- AlphaGen

These are not production authorities. They may later contribute structured factors or candidate alphas and must prove incremental OOS value through ablation.

---

## 3. Qlib — CORE RESEARCH CANDIDATE

### Classification

**SHORTLIST: YES**

### Why it fits

Qlib is a mature AI-oriented quantitative research platform with:

- US market mode (`REG_US`);
- data/feature pipelines;
- Alpha158 / Alpha360 style factor datasets;
- a broad model zoo;
- model workflows and benchmark tooling;
- signal-level metrics such as IC / Rank IC;
- portfolio-level backtest metrics;
- experiment / workflow support;
- online model rolling support;
- portfolio and strategy components.

Qlib benchmark infrastructure explicitly compares multiple model families on the same dataset/workflow. This matches the project rule that model complexity has no privilege.

### Important observation

Qlib's public benchmark tables demonstrate that model ranking changes by dataset and that sophisticated models can underperform simpler models. Therefore no model is preselected as the permanent Champion.

### POC questions

- Can a clean US-equity daily workflow run locally under the 256 GB ceiling?
- What US data preparation is actually usable today without relying on low-quality demo data?
- Can a point-in-time/dynamic universe be maintained without self-building a market database?
- Can Alpha158/Alpha360-like features be used with US equities cleanly?
- Can all MVP models run under one identical train/valid/test and transaction-cost configuration?
- What artifact/metadata footprint does repeated research create?

### Decision

**Retain as primary Research System candidate.**

---

## 4. RD-Agent(Q) — AUTONOMOUS R&D CANDIDATE

### Classification

**SHORTLIST: YES**

### Why it fits

RD-Agent(Q) is explicitly designed for autonomous quantitative R&D through factor-model co-optimization. It can automate iterative proposal, implementation, experiment and feedback loops.

This directly matches the desired future behavior:

```text
idea
→ implementation
→ experiment
→ result
→ analysis
→ next idea
```

### Boundaries

RD-Agent belongs only in the **Research Plane**.

It is forbidden from:

- editing human risk ceilings;
- directly placing live orders;
- promoting its own artifacts into Production;
- repeatedly optimizing against sealed certification data.

### Risks / friction to POC

- Linux-oriented operation;
- Docker / environment overhead;
- LLM token/API cost;
- nondeterministic agent behavior;
- potentially large experiment/checkpoint accumulation;
- autonomous repeated trials increase multiple-testing / overfitting risk.

### POC questions

- Can factor loop run reproducibly against our selected Qlib US dataset?
- Can model loop run independently?
- Can joint factor-model loop produce machine-readable experiment lineage?
- Can research budget and storage budget be hard-limited?
- Can the agent be denied access to sealed certification windows?
- Can failed agent runs be isolated without affecting certified artifacts?

### Decision

**Retain as primary autonomous-research candidate, but never as production authority.**

---

## 5. FinRL-X / FinRL-Trading — FULL-STACK CHALLENGER

### Classification

**POC CHALLENGER: YES**

### Why it matters

FinRL-X is designed as a deployment-consistent, weight-centric stack spanning:

- market/fundamental data;
- stock selection;
- portfolio allocation;
- timing adjustment;
- portfolio-level risk overlay;
- professional backtesting;
- Alpaca paper/live execution.

Its weight-centric interface is highly aligned with our intended `TargetPortfolio` boundary.

### Why it is not selected immediately

The current production-oriented codebase is a comparatively recent public release. The project itself describes the current package as its initial public release.

Therefore broad functionality is not enough; operational maturity must be tested.

### POC questions

- Can it reproduce its documented example workflows locally?
- How much of Qlib + portfolio + execution can it truly replace?
- Does it support our desired dynamic US universe cleanly?
- Are transaction costs / no-lookahead semantics strong enough for certification use?
- Is Alpaca coupling too opinionated for a Robinhood-first account?
- Can stock selection and portfolio modules be replaced independently without forking upstream?

### Decision

**Retain as a system-level challenger. Do not combine it with Qlib/LEAN by default.**

If it satisfies 80–90% of requirements with materially lower complexity, architecture may simplify around it. Otherwise retain the modular stack.

---

## 6. QuantConnect LEAN — EXECUTION / REALITY-MODELING CANDIDATE

### Classification

**SHORTLIST AS ALTERNATE EXECUTION ENGINE: YES**

### Strengths

LEAN has mature capabilities around:

- event-driven backtesting/live algorithms;
- brokerage models;
- portfolio/account state;
- order validation;
- open orders and transactions;
- fill/reality modeling;
- fees, slippage and buying power;
- many broker integrations;
- equities, options, futures, forex and crypto depending on broker.

### Critical Robinhood finding

**LEAN does not currently list Robinhood as a supported brokerage.**

Therefore this project must not assume:

```text
Qlib → LEAN → Robinhood
```

as a supported path.

LEAN remains useful as:

- an alternate production engine if the broker changes;
- a reference reality-model/backtest implementation;
- a future execution engine for IBKR / Alpaca / Schwab / Public / supported crypto brokers.

### POC questions

- Can LEAN accept a thin `TargetPortfolio` contract with little custom code?
- What is the smallest local footprint needed for paper execution?
- Is maintaining LEAN justified if Robinhood MCP becomes primary live execution?

### Decision

**Keep, but demote from mandatory component to alternate/reference execution candidate.**

---

## 7. Robinhood Trading MCP — PRIMARY BROKER EXECUTION CANDIDATE

### Classification

**SHORTLIST: YES / PRIMARY FOR USER FIT**

### Why it changes the plan

Robinhood now officially offers Agentic Trading through a dedicated Agentic Account and Robinhood Trading MCP. Connected agents can access account/portfolio information and place trades in the Agentic account. Current supported order domains include long equities, options and crypto.

This is a better user-fit than forcing a separate broker solely for automation.

### Important boundary

Robinhood MCP is not the Research System and not the Certification System.

It should receive only already-certified target actions/weights.

### Critical risks to test

- exact tool schema and order-type coverage;
- idempotency / duplicate-submit protection;
- partial fills;
- cancel/replace behavior;
- reconciliation after process restart;
- rate limits;
- fractional-share behavior;
- market-session handling;
- current long-only equity limitation;
- disconnect / revoke behavior;
- whether deterministic machine-to-machine use can be made reliable enough for our production adapter.

### Decision

**Promote to primary live-execution POC.**

LEAN remains the mature alternate rather than a required middle layer.

---

## 8. OpenBB — DATA / INFORMATION GATEWAY CANDIDATE

### Classification

**SHORTLIST: YES, AS GATEWAY — NOT AS SOURCE OF TRUTH**

### Why it fits

OpenBB provides a normalized access layer over multiple financial-data providers through Python and REST, and supports MCP for AI-agent consumption.

This is highly useful for the future Information Intelligence tree:

- price data;
- fundamentals;
- SEC-related data;
- macro providers;
- news providers;
- agent-facing data access.

### Important boundary

OpenBB is primarily a **gateway/standardization layer**. Data quality, licensing, point-in-time semantics and historical coverage still depend on the underlying provider.

The project must never write:

```text
OpenBB data = automatically PIT-correct
```

without provider-specific verification.

### POC questions

- Which providers cover US price + corporate action + fundamental + news needs?
- Which provider supports historical point-in-time fundamentals / analyst estimates?
- What can be used without excessive subscription cost?
- Does MCP add value versus direct Python/REST for automated research?
- What data should be cached locally versus re-downloadable?

### Decision

**Retain as preferred data/information gateway candidate, subject to provider-level audit.**

---

## 9. skfolio — CERTIFICATION / PORTFOLIO CANDIDATE

### Classification

**SHORTLIST: YES**

### Why it fits

skfolio offers finance-aware validation and portfolio tools including:

- WalkForward;
- CombinatorialPurgedCV;
- purging / embargo;
- MultipleRandomizedCV;
- portfolio optimization;
- transaction-cost constraints;
- turnover / weight / group constraints;
- multiple risk measures.

This directly fills a gap that should not be self-built casually.

### Boundary

skfolio does not certify an autonomous strategy by itself. We still own:

- sealed OOS policy;
- multiple-testing accounting;
- Deflated Sharpe / PBO or equivalent policy;
- promotion thresholds;
- Champion/Challenger lifecycle.

### Decision

**Retain for P2 Certification/Portfolio POC.**

---

## 10. TradingAgents — INFORMATION INTELLIGENCE CHALLENGER

### Classification

**RESEARCH CHALLENGER ONLY**

### Fit

TradingAgents decomposes analysis into fundamental, sentiment, news, technical, trader and risk/portfolio roles. This is useful as a potential structured-information factor generator.

### Boundary

The project itself is positioned for research, and its native trading flow is not selected as our production execution authority.

### Intended use

Potential future ablation:

```text
Base Quant
vs
Base Quant + TradingAgents-derived structured factors
```

If it does not improve sealed-OOS performance net of cost, it is rejected.

### Decision

**Do not install in P1. Revisit in P6.**

---

## 11. FinBERT / FinGPT — TEXT-FACTOR CHALLENGERS

### Classification

**LATER CHALLENGERS**

### Fit

FinBERT provides finance-domain sentiment classification. FinGPT provides broader financial-LLM research capabilities.

### Intended role

They may produce structured factors from:

- news;
- filings;
- earnings text;
- financial sentiment.

They never directly control production orders.

### Decision

**Do not install in P1. Compare against general-LLM extraction and no-news control in P6.**

---

## 12. AlphaGen — AUTOMATIC ALPHA CHALLENGER

### Classification

**OPTIONAL RESEARCH CHALLENGER**

### Why it is relevant

AlphaGen performs automatic formulaic-alpha generation with reinforcement learning, includes Qlib-specific APIs, and also includes LLM-based iterative alpha-generation routines.

### Why it is not core

It overlaps substantially with RD-Agent's role, while RD-Agent has a broader factor-model joint optimization mission.

### Decision

**Do not add by default. POC only if RD-Agent leaves a clear alpha-generation gap or if ablation shows independent value.**

---

## 13. Upstream overlap map

```text
OPENBB
Data gateway
    ↓
QLIB
Research data/features/models/backtest
    ↓
RD-AGENT
Autonomous factor/model R&D
    ↓
OUR CERTIFICATION POLICY
sealed OOS / multiple-testing / promotion
    ↓
skfolio
financial CV + portfolio/risk tools
    ↓
TargetPortfolio
    ↓
ROBINHOOD MCP       LEAN
primary broker      alternate/reference execution
```

FinRL-X is tested **against this whole composition**, not automatically added beside it.

TradingAgents / FinGPT / FinBERT / AlphaGen are optional research leaves.

---

## 14. What should NOT be self-built in early phases

Do not self-build unless POC proves upstream inadequate:

- generic ML training framework;
- model zoo;
- factor-expression engine;
- general-purpose backtest engine;
- brokerage order-state engine;
- raw news browser/scraper framework;
- generic portfolio optimizer;
- purged CV implementation;
- tick recorder;
- order-book recorder;
- always-on local market database.

Expected custom ownership should remain thin:

- project contracts/adapters;
- sealed-certification policy;
- multiple-testing ledger;
- Champion/Challenger lifecycle;
- human-owned risk envelope;
- production health / kill policy;
- storage budget / retention policy.

---

## 15. Revised P0 local-POC order

To minimize local pollution and disk usage, do **not** install everything at once.

### P0-A — Qlib POC

Goal: prove core US-equity research workflow.

Exit evidence:
- clean isolated environment;
- one US dataset path;
- one Alpha158-style workflow;
- Linear + LightGBM run;
- reproducible report;
- disk/RAM/time measured.

### P0-B — RD-Agent(Q) POC

Only after Qlib passes.

Goal: prove autonomous research can operate against the selected research substrate without owning production.

### P0-C — FinRL-X challenger POC

Run independently, not merged into the Qlib environment.

Goal: determine whether a single stack can replace enough components to justify switching architecture.

### P0-D — Robinhood Trading MCP POC

Read-only first.

Then paper/sandbox-like safety path if available; no unrestricted live capital.

Verify account read, quote read, order preview, order lifecycle and reconciliation semantics.

### P0-E — LEAN POC

Run only if needed as alternate/reference execution after Robinhood MCP findings.

### P0-F — OpenBB/provider POC

Verify gateway and provider quality. Do not download large historical datasets until provider choice is made.

### Deferred to later phases

- TradingAgents
- FinGPT
- FinBERT
- AlphaGen
- advanced portfolio models

---

## 16. P0 desk-audit conclusions

```text
QLIB                        = SHORTLIST / PRIMARY RESEARCH
RD_AGENT_Q                  = SHORTLIST / PRIMARY AUTONOMOUS R&D
FINRL_X                     = SHORTLIST / FULL-STACK CHALLENGER
OPENBB                      = SHORTLIST / DATA GATEWAY
SKFOLIO                     = SHORTLIST / CERTIFICATION + PORTFOLIO
ROBINHOOD_TRADING_MCP       = SHORTLIST / PRIMARY EXECUTION POC
LEAN                        = SHORTLIST / ALTERNATE EXECUTION + REFERENCE
TRADINGAGENTS               = DEFER / INFORMATION FACTOR CHALLENGER
FINBERT                     = DEFER / TEXT FACTOR CHALLENGER
FINGPT                      = DEFER / TEXT FACTOR CHALLENGER
ALPHAGEN                    = DEFER / AUTO-ALPHA CHALLENGER
TICK_RECORDER               = REJECT / OUT OF SCOPE
ORDERBOOK_RECORDER          = REJECT / OUT OF SCOPE
```

---

## 17. P0 current status

```text
P0_REMOTE_DESK_AUDIT = COMPLETE
P0_LOCAL_POC = NOT STARTED
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
```

### Current Next

**P0-A — Qlib isolated local POC design and execution.**

No other upstream should be installed locally before P0-A evidence is reviewed.
