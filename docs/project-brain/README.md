# AUTONOMOUS_QUANT — Project Brain

> Status: **PLANNING / NO PRODUCTION TRADING**
>
> Current Next: **P1 — PIT Reconciliation Implementation**
>
> Core Principle: **Upstream-first, tree-structured, modular, replaceable, test-before-trust.**

## 1. Mission

Build an **autonomous quant research and investment platform** for personal capital that can:

- continuously acquire market information;
- automatically research and generate candidate alpha factors and models;
- compare candidate models and strategies under the same rules;
- reject overfit or unstable strategies;
- automatically rank investable assets and construct target portfolios;
- paper trade first, then graduate to tightly risk-limited live trading;
- monitor strategy decay and continuously search for better challengers;
- eventually support multiple asset classes such as US equities, ETFs, crypto and futures.

The system is designed for **high automation and low manual intervention**, but it does **not** assume or promise guaranteed profits.

The human owner keeps authority over:
- maximum capital allocation;
- maximum leverage;
- hard risk ceilings;
- permitted asset classes;
- production activation / shutdown permissions.

AI research agents may **never** override these controls.

---

## 2. Product Goal

```text
Market / Fundamental / Filing / News / Macro Data
                       ↓
              Intelligence Factors
                       ↓
             Autonomous Research
               Qlib + RD-Agent
                       ↓
            Candidate Alpha / Models
                       ↓
               Certification Gate
                       ↓
          Champion / Challenger System
                       ↓
             Portfolio + Risk Layer
                       ↓
                  Execution Engine
                       ↓
                      Broker
                       ↓
               Monitoring / Audit
```

Normal operation should require little or no manual input.

The system should eventually be able to:
- decide which stocks / ETFs / supported assets deserve capital;
- adjust weights when opportunities change;
- retrain / refresh models;
- research new factors and strategies;
- retire degraded strategies;
- promote better challengers only after independent certification.

---

## 3. Non-Goals

This project is **not**:

- a 15-minute direction-prediction system;
- a high-frequency trading / microsecond latency system;
- a market-making system;
- a tick/order-book recording project;
- a single "magic AI model";
- an LLM that reads news and directly sends unrestricted live orders;
- a guarantee of passive income.

No production system should depend on winning a latency race against professional HFT firms.

---

## 4. Tree Architecture

```text
AUTONOMOUS_QUANT
│
├── 00-governance
│   ├── capital-policy
│   ├── risk-ceiling
│   ├── promotion-policy
│   └── security-permission
│
├── 10-data-system
│   ├── asset-master
│   ├── universe
│   ├── market-data
│   ├── corporate-actions
│   ├── fundamentals
│   ├── sec-filings
│   ├── news
│   ├── macro
│   └── asset-adapters
│
├── 20-intelligence-system
│   ├── price-factors
│   ├── fundamental-factors
│   ├── news-factors
│   ├── filing-factors
│   ├── macro-factors
│   ├── sentiment-factors
│   └── feature-assembly
│
├── 30-research-system
│   ├── qlib
│   ├── rd-agent
│   ├── model-zoo
│   ├── alpha-mining
│   ├── strategy-research
│   └── experiment-registry
│
├── 40-certification-system
│   ├── temporal-integrity
│   ├── walk-forward
│   ├── purged-cv
│   ├── multiple-testing-control
│   ├── benchmark-suite
│   ├── cost-slippage-stress
│   ├── regime-stress
│   ├── shadow-trading
│   └── champion-challenger
│
├── 50-portfolio-system
│   ├── alpha-ensemble
│   ├── strategy-books
│   ├── portfolio-construction
│   ├── exposure-control
│   └── risk-overlay
│
├── 60-execution-system
│   ├── execution-adapter
│   ├── paper
│   ├── live
│   ├── reconciliation
│   └── kill-switch
│
└── 70-operations-system
    ├── scheduler
    ├── health
    ├── research-budget
    ├── storage-budget
    ├── alert
    ├── audit-trail
    └── dashboard
```

### Tree rules

1. Parent modules compose; child modules own only their own responsibility.
2. Siblings do not reach into each other's private internals.
3. Cross-module integration happens through explicit public contracts.
4. Mature upstream software is preferred over self-written infrastructure.
5. A leaf can be replaced without forcing unrelated siblings to change.
6. Research code and production trading code must remain separated.
7. Production may consume only **certified artifacts**, never raw experimental output.

---

## 5. Three-Plane Safety Model

### Research Plane

Candidate upstream:
- Microsoft Qlib
- Microsoft RD-Agent(Q)
- optional AlphaGen / future alpha generators
- optional TradingAgents / FinGPT / FinBERT information workers

Research Plane may generate factors, generate model code, train candidate models, run experiments, fail, retry and mutate research hypotheses.

Research Plane may **not** modify production risk ceilings, directly place live orders, or directly promote itself to production.

### Certification Plane

Required controls include:
- point-in-time correctness;
- no look-ahead leakage;
- survivorship-bias controls;
- walk-forward tests;
- purged / embargoed CV where appropriate;
- sealed out-of-sample windows;
- transaction costs;
- slippage;
- turnover;
- liquidity constraints;
- multiple-testing correction;
- parameter perturbation;
- regime robustness;
- benchmark comparison;
- shadow / paper observation.

Only Certification Plane may issue a **CERTIFIED** artifact.

### Production Plane

Production accepts only certified model versions, certified alpha sets, certified portfolio policies, and human-owned capital / risk limits.

Production does not run open-ended research.

---

## 6. Upstream-First Candidate Stack

### Core research candidate — Microsoft Qlib
- quantitative ML research
- datasets / factors
- model training
- backtesting
- online model rolling
- portfolio / strategy components
- experiment recording

### Autonomous R&D candidate — Microsoft RD-Agent(Q)
- automated factor proposal
- automated factor implementation
- automated model proposal / optimization
- factor-model co-optimization
- iterative research loops

### Full-stack challenger — FinRL-X / FinRL-Trading
- data
- ML stock selection
- portfolio allocation
- timing
- risk overlay
- backtest
- paper/live execution

It must be tested against the modular Qlib + RD-Agent route before adoption.

### Production execution candidate — QuantConnect LEAN
- event-driven backtesting
- portfolio state
- order management
- fills
- fees
- slippage
- brokerage models
- paper/live execution
- multi-asset support

Use only if upstream audit shows it adds enough value over simpler execution options.

### Information / data gateway candidate — OpenBB
- market data
- fundamentals
- macro
- news / provider integrations
- AI/agent-friendly interfaces

### Information intelligence candidates
- TradingAgents
- FinGPT
- FinBERT
- general LLM structured extraction

These are **factor producers / research assistants**, not direct production traders.

### Additional research challengers
- AlphaGen
- AlphaBench
- skfolio
- VectorBT
- Lumibot
- Riskfolio-Lib
- future projects discovered during upstream audit

No project is selected only because of GitHub stars.

---

## 7. Information Intelligence / Skills Plan

News, SEC filings, earnings reports, macro releases and sentiment can materially affect prices and must eventually be represented.

```text
Source
  ↓
Skill / Provider Adapter
  ↓
Evidence Document
  ↓
LLM / NLP Extractor
  ↓
Structured Factor
  ↓
Research / Model
```

A Skill is an **information-access capability**, not an alpha strategy by itself.

Historical research may only use information that was actually available at that historical time. This applies to SEC filings, earnings releases, analyst estimates, news, FRED / macro releases and later revisions to economic data.

---

## 8. Lightweight Evidence Ledger

No tick recorder is planned.

For information used by the model, preserve only enough evidence for auditability:

```text
source
document_id
asset
published_at
first_available_at
revision / version
content_hash
extractor_model
extractor_version
prompt_version
factor_output
```

The project has a **256 GB local-storage constraint**, so storage is a first-class design consideration.

---

## 9. Model Tournament

### MVP control set
- Linear / Ridge baseline
- LightGBM
- XGBoost
- CatBoost
- DoubleEnsemble

### Later challengers
- MLP
- LSTM
- GRU
- TCN
- Transformer
- TRA
- HIST
- IGMTF
- RL models when justified

Rules:
- same dataset
- same universe
- same label
- same train/validation/test periods
- same cost assumptions
- same portfolio rules
- same benchmark suite

Complexity has no privilege. A simple model that wins net-of-cost OOS remains Champion.

---

## 10. Alpha Zoo

```text
Alpha Zoo
│
├── Classic Price Alpha
│   ├── Momentum
│   ├── Reversal
│   ├── Trend
│   ├── Volatility
│   └── Volume
│
├── Qlib Factors
│   ├── Alpha158
│   └── Alpha360
│
├── Fundamental Alpha
├── RD-Agent Generated Alpha
├── AlphaGen Generated Alpha
├── News Alpha
├── Filing Alpha
├── Macro Alpha
└── Sentiment Alpha
```

All generated alphas enter the same Candidate Pool and face the same certification process.

---

## 11. Benchmark Suite

VOO / SPY is an important personal benchmark, but cannot be the only benchmark.

Required benchmark families:
- VOO / SPY
- QQQ
- matched-universe cap-weight benchmark
- matched-universe equal-weight benchmark
- simple momentum strategy
- simple trend strategy
- cash / Treasury-bill benchmark
- factor-adjusted alpha where feasible

A strategy is not considered valuable merely because it beats SPY by taking hidden leverage, sector concentration, or factor beta.

---

## 12. Multiple-Testing Protection

Autonomous research can generate thousands of strategies. The project must track how many factors, models, hyperparameter combinations and strategy variations were evaluated.

Certification should consider:
- Deflated Sharpe Ratio or an equivalent multiple-testing-aware statistic
- Probability of Backtest Overfitting or equivalent robustness analysis
- stability across windows
- stability under parameter perturbation

Only showing the best backtest from thousands of attempts is prohibited.

---

## 13. Sealed OOS Policy

Repeatedly looking at an OOS result turns it into training feedback.

```text
Research Window
    ↓
Validation Window
    ↓
Sealed Certification Window
    ↓
Live Shadow Future
```

The autonomous research agent must not repeatedly optimize against the sealed certification window.

---

## 14. Portfolio Layer

Models produce scores / forecasts. Models do **not** directly choose unrestricted dollar orders.

```text
Alpha / Model Outputs
        ↓
Alpha Ensemble
        ↓
Portfolio Construction
        ↓
Risk Overlay
        ↓
Target Weights
```

Portfolio methods should also compete:
- Equal Weight
- Inverse Volatility
- Risk Budgeting
- HRP / hierarchical methods
- mean-risk / constrained optimization
- ML / DRL allocation only if it proves incremental value

Simple portfolio methods are always retained as controls.

---

## 15. Multi-Asset End State

```text
US Equity Alpha Book
        \
ETF / Macro Book
         \
Crypto Alpha Book
           → Meta Portfolio
Futures Trend Book /
         /
Cash / Defensive Book
```

Each asset book may use different factors and models. A higher-level Meta Portfolio decides capital allocation across books.

First implementation remains **US equities / ETFs only**.

---

## 16. Execution Layer

Production research should terminate in a simple contract such as:

```text
TargetPortfolio
- asset
- target_weight
- effective_time
- strategy_version
- certification_id
```

Execution is downstream and should own brokerage connectivity, order state, partial fills, fees, slippage, reconciliation, buying-power checks, retry semantics and live account state.

Do not self-build these unless upstream audit proves necessary.

---

## 17. Human-Owned Risk Ceiling

The autonomous system may adjust allocations **inside** the approved envelope. It may not automatically expand the envelope.

Human-owned limits include:
- maximum live capital
- maximum leverage
- maximum gross exposure
- maximum single-name weight
- maximum sector exposure
- maximum crypto allocation
- maximum daily turnover
- maximum drawdown before de-risk / shutdown
- permitted brokers / exchanges

Research agents cannot edit these controls.

---

## 18. Storage Policy

Local target hardware: **256 GB**.

Default rules:
- no tick recorder
- no full order-book archive
- no raw WebSocket archive
- market history should be reproducibly downloadable when possible
- structured daily/hourly data may be cached
- news should prefer metadata/hash/extracted factor storage over unlimited duplicate raw content
- failed model checkpoints should be garbage-collected
- experiment metadata should outlive disposable training artifacts
- Champion / important Challenger artifacts must remain reproducible

---

## 19. Roadmap

| Phase | Goal | Primary upstream | Exit condition |
|---|---|---|---|
| **P0 Upstream Fit Audit** | Run real POCs for candidate upstreams | Qlib, RD-Agent, FinRL-X, LEAN, OpenBB, information-model candidates | dependency decision recorded |
| **P1 Minimal Quant** | Dynamic US universe → factors → model tournament → Top-K → backtest | Qlib | complete reproducible benchmark report |
| **P2 Certification** | Build trustworthy exam system | Qlib + skfolio / statistical controls | false-alpha controls operational |
| **P3 Autonomous Research** | Automate factor/model research | RD-Agent + Qlib | candidates produced automatically |
| **P4 Champion System** | Automate promotion lifecycle | thin policy layer | Candidate→Certified→Shadow→Champion works |
| **P5 Fundamental Intelligence** | Add PIT fundamentals / filings | SEC / OpenBB / upstream | measurable incremental OOS test |
| **P6 News / Macro / Skills** | Add news, macro, sentiment and LLM extraction | OpenBB + TradingAgents/FinGPT/FinBERT challengers | factor ablation proves value or module rejected |
| **P7 Multi-Alpha Ensemble** | Combine independent alpha families | Qlib | ensemble beats component controls on certification criteria |
| **P8 Portfolio / Risk** | Portfolio tournament and production risk overlay | Qlib + skfolio | TargetPortfolio contract stable |
| **P9 Paper Production** | Real event-driven paper execution | LEAN or selected execution upstream | stable broker reconciliation |
| **P10 Small Live** | Tightly capped real-money deployment | broker + execution engine | live behavior matches certified expectations within tolerance |
| **P11 Multi-Asset** | Add crypto / futures / expanded ETF books | adapters + execution upstream | each new book independently certified |
| **P12 Autonomous Ops** | Low-touch operation | scheduler / monitoring | normal operation requires no manual action |

---

## 20. P0 — Complete

P0 upstream fit, interface audit, and four functional POCs are complete.

P0 established the selected upstream topology and verified its bounded integration contracts. It did not authorize production trading.

Current next is P1 Minimal Quant, which is not started.

### Historical P0 evaluation requirements

During P0, Qlib, RD-Agent(Q), FinRL-X, LEAN, OpenBB/information providers, and information models were evaluated for functionality, maturity, reproducibility, local operational cost, replacement boundaries, and overlap with other upstream components.

---

## 21. P1 — Minimal Quant

```text
Point-in-Time US Universe
        ↓
Daily Market Data
        ↓
Qlib Alpha158
        ↓
Model Tournament
  Linear / Ridge
  LightGBM
  XGBoost
  CatBoost
  DoubleEnsemble
        ↓
Cross-Sectional Ranking
        ↓
Top-K Portfolio
        ↓
Equal Weight / Inverse Vol
        ↓
Backtest
        ↓
Benchmark Suite
```

P1 does **not** include RD-Agent autonomous promotion, news, TradingAgents, crypto, live money, high-frequency data or tick recording.

P1 exit artifact is a **complete reproducible backtest and benchmark report**.

---

## 22. Promotion Lifecycle

```text
RESEARCH
   ↓
CANDIDATE
   ↓
CERTIFIED
   ↓
SHADOW
   ↓
CHAMPION / ACTIVE
   ↓
DEGRADED
   ↓
RETIRED
```

Promotion is rule-based. No research agent may skip states.

---

## 23. Module Admission Rule

Every later module must be evaluated by ablation, for example:

```text
Base Quant
vs
Base Quant + News Factor
```

A new module is admitted only if it adds measurable value under certification criteria.

No module is added because it is popular, has many GitHub stars, uses a newer AI model, or produces attractive in-sample charts.

---

## 24. Definition of Passive

Target normal operation:

```text
data update
→ research
→ factor/model refresh
→ candidate certification
→ strategy monitoring
→ asset ranking
→ portfolio construction
→ paper/live execution
→ reconciliation
→ reporting
```

should run automatically.

Human intervention should normally be required only for risk-ceiling changes, capital increases, new broker credentials, new asset-class authorization, persistent system failure, compliance/data-license issues or emergency shutdown.

---

## 25. Success Criteria

Evaluation includes:
- net return after estimated/real costs
- CAGR
- Sharpe / Sortino
- maximum drawdown
- turnover
- liquidity
- robustness across regimes
- benchmark-relative performance
- factor-adjusted alpha where appropriate
- paper/live divergence
- operational reliability

A sophisticated model that cannot beat simpler controls on an appropriate risk-adjusted basis is rejected.

If the autonomous system fails to add value over simple passive investing after robust testing, capital should remain in the simpler benchmark rather than forcing deployment.

---

## 26. Authority / Status

```text
PROJECT_STATUS = PLANNING
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
HIGH_FREQUENCY_TRADING = OUT OF SCOPE
TICK_RECORDER = OUT OF SCOPE

TARGET_ARCHITECTURE = DEFINED
P0 = COMPLETE
P0_UPSTREAM_BATCH_DEPLOYMENT = COMPLETE_WITH_DOCUMENTED_BLOCKERS
P0_INTERFACE_AUDIT = COMPLETE
P0_FUNCTIONAL_POC_DESIGN = COMPLETE
P0_POC_B_LINUX_QLIB_RDAGENT_RUNTIME = PASS
P0_POC_A_OPENBB_LINUX_QLIB_HANDOFF = PASS
P0_POC_C_QLIB_CERTIFICATION_SKFOLIO = PASS
P0_POC_D_TARGETPORTFOLIO_EXECUTIONPLAN = PASS
P0_FUNCTIONAL_POC = COMPLETE
P1_OPEN_SOURCE_PIT_BLUEPRINT_DESIGN = COMPLETE
P1_PIT_RUNTIME_FOUNDATION = COMPLETE
P1_PIT_SOURCE_INGESTION = COMPLETE
P1_PIT_RECONCILIATION_RUNTIME_GAP_CLOSURE = COMPLETE
P1_PIT_RECONCILIATION_IMPLEMENTATION = COMPLETE_WITH_CERTIFICATION_BLOCKERS
PIT_UNIVERSE_CERTIFIED = NO
PIT_CERTIFICATION_BLOCKERS = PRIMARY_EVIDENCE_CONTENT_MISSING / OFFICIAL_TERMINAL_AUTHORITY_MISSING / HISTORICAL_SAMPLE_AUTHORITY_MISSING
CURRENT_NEXT = P1_PIT_RECONCILIATION_IMPLEMENTATION
P1 = STARTED
P1_MINIMAL_QUANT = IN_PROGRESS
P2_CERTIFICATION = PLANNED / NOT STARTED
P3_AUTONOMOUS_RESEARCH = PLANNED / NOT STARTED
NEWS_INTELLIGENCE = PLANNED / NOT STARTED
MULTI_ASSET = PLANNED / NOT STARTED
```

---

## 27. First Principle

> **Do not build what a mature upstream already solves.**
>
> **Do not trust what has not survived independent out-of-sample certification.**
>
> **Do not let autonomous research directly control unrestricted real capital.**
>
> **Build the smallest runnable system first, while preserving interfaces for the complete tree.**
