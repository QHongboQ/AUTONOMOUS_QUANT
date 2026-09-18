# AUTONOMOUS_QUANT — Project Brain

> Status: **PLANNING / NO PRODUCTION TRADING**
>
> Current Next: **P2 — Formulaic Alpha Sealed OOS Accumulation 001**
>
> Active Development: **P5 — Fundamental Historical Dataset Design 001**
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

Normative interpretation:

```text
TREE != SELF-WRITTEN IMPLEMENTATION MAP
TREE = RESPONSIBILITY AND MAINTENANCE MAP
```

The logical tree records capability ownership, responsibility, navigation,
replacement boundaries, maintenance, and audit locations. A node may be
satisfied by an entire upstream project, a focused upstream library, or
AQ-owned domain/policy code. Physical upstream projects do not need to be
copied, split, vendored, or reimplemented to mirror this tree. The complete
ownership modes, capability map, and mandatory task preamble are authoritative
in [Upstream Ownership Model](upstream-ownership-model.md).

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
│   │   └── sp500-pit
│   │       └── schema
│   │           └── pandera
│   ├── trading-calendar
│   │   └── xnys
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
8. **No AQ engine without upstream rejection evidence.** Every implementation
   task must identify the upstream owner and ownership mode before code is
   authorized.

`10-data-system/trading-calendar/xnys` owns XNYS session semantics through
pinned `exchange_calendars`. It does not own membership, identity, market data,
or certification.

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

## 6. Upstream Ownership Map

Implementation uses exactly three ownership modes:

- `UPSTREAM_WHOLE`: a complete upstream project owns the capability; AQ is
  limited to configuration, adapter, contract, health/upgrade evidence,
  orchestration, and policy boundaries.
- `UPSTREAM_LEAF`: a focused upstream library owns one bounded leaf; AQ may
  add only a necessary thin wrapper/configuration.
- `AQ_OWNED`: project-specific policy, facts, contracts, and routing that
  cannot reasonably be delegated upstream. This does not automatically
  authorize a generic engine.

Current ownership is:

- **Qlib — `UPSTREAM_WHOLE`:** DatasetH, handlers, Alpha158/Alpha360, model
  training, workflow, predictions, ranking, Top-K, research backtesting,
  transaction costs, portfolio analysis, and rolling/online research.
- **RD-Agent(Q) — `UPSTREAM_WHOLE`:** automated factor/model proposal and
  implementation plus iterative research-loop automation; AQ owns its policy,
  budget, and permission boundaries.
- **Qlib + skfolio — `UPSTREAM_WHOLE` / `UPSTREAM_LEAF`:** generic portfolio,
  optimization, WalkForward, CombinatorialPurgedCV, MeanRisk, and compatible
  statistical tooling; AQ owns portfolio policy and risk limits.
- **QuantConnect LEAN — `UPSTREAM_WHOLE` if adopted:** preferred execution
  candidate, not yet production authority. A later execution audit must close
  runtime prerequisites before adoption.
- **OpenBB — `UPSTREAM_WHOLE`, provider-gateway role:** provider access for
  market data, fundamentals, macro, and news where it is the cleanest owner;
  it is not mandatory when another selected upstream owns the path directly.
- **exchange_calendars, Pandera, DVC — `UPSTREAM_LEAF`:** exchange sessions,
  schema validation, and reproducibility/pipeline tracking respectively. AQ
  must not duplicate their generic engines.
- **AQ PIT universe — `AQ_OWNED` thin domain:** accepted S&P 500 PIT facts and
  membership/identity policy only, not a general security master.
- **Trial Ledger custom runtime — retired:** Qlib, RD-Agent, and DVC own the
  generic experiment workflow, research-loop metadata, artifact dependencies,
  and reproducibility responsibilities. AQ has no generic experiment database.
  Historical Trial Ledger documents remain evidence, not current implementation
  authority.
- **FinRL-X — challenger/fallback only:** `UPSTREAM_WHOLE` if a future audit
  selects it; AQ must not mimic it.

The root hard rule and required future-task ownership preamble are defined in
[Upstream Ownership Model](upstream-ownership-model.md). A task that skips
that ownership check is architecturally invalid.

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

At P0 close, the recorded next phase was P1 Minimal Quant, which had not yet
started. This sentence is historical; the current authority is Section 26.

### Historical P0 evaluation requirements

During P0, Qlib, RD-Agent(Q), FinRL-X, LEAN, OpenBB/information providers, and information models were evaluated for functionality, maturity, reproducibility, local operational cost, replacement boundaries, and overlap with other upstream components.

---

## 21. P1 — Minimal Quant

```text
Selected upstream market data
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

P1 primarily **composes Qlib upstream capabilities**; it does not implement AQ
equivalents of these engines. AQ responsibility is limited to configuration,
policy metadata, minimal experiment/run routing when required, result
classification, and project-specific boundaries. Later model comparison may
configure multiple Qlib-supported models without creating an AQ model engine.

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

The certification Git-data boundary is defined precisely in
[P2 Frozen Certification Dataset Git Scope Clarification 001](p2-frozen-certification-dataset-git-scope-clarification-001.md). Historical public corroboration in documentation is evidence only, never a certification dataset row or provider substitute.

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
P1_PIT_THIN_RUNTIME = COMPLETE
PIT_ACTIVE_RESPONSIBILITY = THIN_RESEARCH_DOMAIN_ADAPTER
PIT_UNIVERSE_RESEARCH_READY = YES
PIT_UNIVERSE_CERTIFIED = NO
PIT_REFERENCE_ORACLE_EXECUTABLE = RETIRED
PIT_REGRESSION_ORACLE = STATIC_FIXTURES_BLACK_BOX_TESTS
PIT_FROZEN_REGRESSIONS = 13_PASSING
P1_DVC_DATASET_SNAPSHOT = COMPLETE
P1_QLIB_DATASET_HANDOFF = COMPLETE
P1_UPSTREAM_SUBSTITUTION_STACK = COMPLETE
TRIAL_LEDGER_CUSTOM_RUNTIME = RETIRED
TRIAL_LEDGER_GENERIC_EXPERIMENT_OWNERS = QLIB_RDAGENT_DVC
AQ_EXPERIMENT_DATABASE = NONE
DATASET_SNAPSHOT_READY = YES
QLIB_HANDOFF_READY = YES
P1_QLIB_NATIVE_BASELINE = COMPLETE
P1_QLIB_NATIVE_MODEL_COMPARISON = COMPLETE
MODEL_COMPARISON_CLASSIFICATION = EXPLORATORY_RESEARCH_ONLY_NOT_CERTIFIED
MODEL_COMPARISON_EXECUTED = LIGHTGBM_REUSED, LINEAR_OLS
MODEL_COMPARISON_CATBOOST = NOT_RUN_EXISTING_ENV_DEPENDENCY_UNAVAILABLE
P1_QLIB_NATIVE_STRATEGY_COMPARISON = COMPLETE
STRATEGY_COMPARISON_CLASSIFICATION = EXPLORATORY_RESEARCH_ONLY_NOT_CERTIFIED
BEST_OBSERVED_P1_STRATEGY_CANDIDATE = TOPK_30_NDROP_3
P1_CLOSEOUT = COMPLETE
P1_EXPLORATORY_MODEL_REFERENCE = LIGHTGBM_ALPHA158
P1_EXPLORATORY_STRATEGY_REFERENCE = TOPK_30_NDROP_3
P1_RESULT_CLASSIFICATION = RESEARCH_ONLY_NOT_CERTIFIED
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
TEST_SET_IS_PRISTINE_OOS = NO
REAL_MARKET_DATA_READY = YES (RESEARCH BASELINE DATASET ONLY)
REAL_ALPHA158_RUN = YES
REAL_MODEL_TRAINING = YES
REAL_PREDICTIONS = YES
REAL_BACKTEST = YES
REAL_PORTFOLIO_ANALYSIS = YES
P1_BASELINE_CLASSIFICATION = RESEARCH_ONLY_NOT_CERTIFIED
NEXT_PHASE = P3_AUTONOMOUS_RESEARCH
RESEARCH_WEB_UI_UPSTREAM_ACTIVATION = COMPLETE
RESEARCH_WEB_UI_OWNER = MLFLOW
RESEARCH_WEB_UI_IMPLEMENTATION = UPSTREAM_MLFLOW_UI
RESEARCH_WEB_UI_VERIFIED = YES
RESEARCH_WEB_UI_PERSISTENT = YES
RESEARCH_WEB_UI_PORTS = BASELINE:5000, MODEL_COMPARISON:5001, STRATEGY_COMPARISON:5002
AQ_CUSTOM_WEB_UI = NONE
AQ_CUSTOM_WEB_BACKEND = NONE
WEB_BIND_SCOPE = LOCALHOST_ONLY
P1 = COMPLETE
P1_MINIMAL_QUANT = COMPLETE
P2_CERTIFICATION_ENTRY = COMPLETE
P2_CERTIFICATION = COMPLETE
HISTORICAL_P2_FIRST_BLOCKER = CERTIFICATION_DATA_AUTHORITY_INCOMPLETE_SUPERSEDED_BY_CURRENT_DATA_VALIDATION_CLOSURE
P2_FIRST_EXECUTION_TASK = P2_CERTIFIED_DATA_FOUNDATION
P2_CERTIFIED_DATA_FOUNDATION = COMPLETE
P2_DATA_AUTHORITY_QUALIFICATION = COMPLETE
HISTORICAL_CERTIFICATION_DATA_PROVIDER_DECISION_REQUIRED = YES_SUPERSEDED_BY_QUANTIACS_PLUS_SIMFIN_ROUTE
BEST_PERSONAL_PROJECT_OPTION = NORGATE_DATA_US_STOCKS_PLATINUM_OR_DIAMOND
BEST_INSTITUTIONAL_REFERENCE = CRSP_US_STOCK_DATABASE
QUANTIACS_FREE_ROUTE_AUDIT = COMPLETE
QUANTIACS_FREE_DATA_PILOT = COMPLETE
QUANTIACS_FREE_DATA_PILOT_CORRECTION = COMPLETE
QUANTIACS_TECHNICAL_VALIDATION = PASS_WITH_EXPLICIT_PRICE_GAPS
QUANTIACS_PILOT_RESULT = PASS_TECHNICAL_PILOT_FREE_GAP_FILL_REQUIRED
QUANTIACS_CLASSIFICATION = TECHNICAL_PILOT_ONLY_NOT_CERTIFICATION_GRADE
QUANTIACS_PROVIDER_RIGHTS_CONFIRMATION = NOT_REQUIRED_FOR_CURRENT_PERSONAL_LOCAL_OPERATIONAL_PROFILE
RECOMMENDED_CERTIFICATION_DATA_ROUTE = QUANTIACS_PRIMARY_PLUS_FREE_GAP_FILL_AUDIT
P2_CERTIFICATION_WINDOW_STATUS = PREREGISTERED_SEALED_OOS_NOT_YET_AVAILABLE
P2_DATA_UPSTREAM_SUBSTITUTION_AUDIT = COMPLETE
DATA_GENERIC_ENGINE_POLICY = UPSTREAM_FIRST_NO_CUSTOM_ENGINE_WITHOUT_REJECTION_EVIDENCE
P2_DATA_PILOT_LOCAL_HYGIENE_AUDIT = COMPLETE
P2_DATA_PILOT_LOCAL_HYGIENE_CLEANUP = COMPLETE
LOCAL_HYGIENE_CLEANUP_REQUIRED = NO
LOCAL_HYGIENE_DEFERRED_RETENTION_REMAINS = YES
P2_FREE_DATA_GAP_FILL_AUTHORITY_AUDIT = COMPLETE
YAHOO_GAP_FILL_RESULT = REJECTED_FOR_CURRENT_FB_DISCK_QWEST_GAPS
YAHOO_REVISION_ADDRESSABILITY = FAIL
YAHOO_RETENTION_RIGHTS = UNRESOLVED
P2_CERTIFICATION_DATA_ROUTE_POLICY = FREE_ONLY
TIINGO_FREE_DATA_AUTHORITY_AUDIT = COMPLETE
TIINGO_TECHNICAL_GAP_COVERAGE = PARTIAL_DISCK_ONLY
TIINGO_CERTIFICATION_AUTHORITY_ACCEPTANCE = REJECTED_STARTER_RETENTION_AND_REVISION
TIINGO_FREE_ROUTE_DECISION = TIINGO_PARTIAL_ANOTHER_FREE_SOURCE_REQUIRED
P2_FREE_DATA_SECONDARY_GAP_FILL_DECISION = COMPLETE
NEXT_FREE_PROVIDER_CANDIDATE = SIMFIN
SIMFIN_SELECTION_SCOPE = NEXT_BOUNDED_TECHNICAL_AUTHORITY_AUDIT_ONLY
P2_SIMFIN_FREE_DATA_AUTHORITY_AUDIT = COMPLETE
SIMFIN_ACCESS = PASS
SIMFIN_2022_IDENTITY = NOT_CERTIFICATION_USABLE
SIMFIN_QWEST_2011_POTENTIAL = NO
QWEST_2011_GAP = UNRESOLVED
FREE_ROUTE_DECISION = SIMFIN_2022_IDENTITY_NOT_CERTIFICATION_USABLE
HISTORICAL_P2_EXISTING_FREE_DATA_BLOCKER_CLOSURE = COMPLETE_WITH_REMAINING_BLOCKERS_SUPERSEDED_BY_CURRENT_RESOLUTION
P2_EXISTING_FREE_DATA_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
FB_META_SECURITY_CONTINUITY = PROVEN
FB_PRICE_AUTHORITY = CLOSED_SECURITY_IDENTITY_DATE_VALID_TICKER_EPISODE
FB_META_CROSS_EPISODE_DIRECT_RELABEL = 0
DISCK_SECURITY_IDENTITY = CLOSED_BY_NASDAQ_SEC
DISCK_TERMINAL_CORPORATE_ACTION = CLOSED_1_TO_1_WBD
DISCK_PRICE_AUTHORITY = PRIMARY_PROVIDER_ROW_ABSENT
DISCK_2022_04_08_CLASSIFICATION = KNOWN_TERMINAL_SESSION_PROVIDER_GAP
DISCK_PRICE_GAP = KNOWN_EXPLICIT_NONBLOCKING_TERMINAL_PROVIDER_GAP
DISCK_EXACT_PRICE_AUTHORITY_HARD_BLOCKER = NO
DAILY_PRICE_VENDOR_REVISION_ID_REQUIRED = NO_IF_SEALED_LOCAL_SNAPSHOT_AUTHORIZED
DAILY_PRICE_REPRODUCIBILITY = CLOSED
P2_DATA_USAGE_PROFILE = PERSONAL_PRIVATE_NONCOMMERCIAL_NONREDISTRIBUTED
QUANTIACS_PERSONAL_LOCAL_OPERATIONAL_RETENTION = ACCEPTED
QUANTIACS_PRIVATE_LOCAL_RETENTION_WRITTEN_CONFIRMATION_REQUIRED = NO_FOR_CURRENT_PERSONAL_PROFILE
QUANTIACS_INDEFINITE_ARCHIVAL_RIGHT = NOT_ESTABLISHED_NOT_REQUIRED
CURRENT_MODEL_LINEAGE_HISTORY_FLOOR = 2015-01-02
QWEST_2011_IDENTITY_REGRESSION = RETAIN
QWEST_2011_CURRENT_MODEL_PRICE_BLOCKER = NO
P2_REMAINING_DATA_BLOCKERS_RESOLUTION = COMPLETE
REMAINING_CERTIFICATION_DATA_HARD_BLOCKERS = NONE
NO_ADDITIONAL_PRICE_PROVIDER_REQUIRED = YES
PROVIDER_EXPANSION_GATE = CLOSED
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
P2_DATA_SOURCE_VALIDATION = CLOSED
CURRENT_PROFILE = PERSONAL_CAPITAL_CERTIFICATION
FROZEN_CERTIFICATION_DATASET_CONTRACT_V1 = FROZEN
SOURCE_PRECEDENCE = QUANTIACS_PRIMARY_SIMFIN_BOUNDED_SECONDARY
SECURITY_EPISODE_CONTRACT = FROZEN
PIT_MEMBERSHIP_CONTRACT = FROZEN
SESSION_CONTRACT = FROZEN
CORPORATE_ACTION_CONTRACT = FROZEN
MISSING_DATA_CONTRACT = FROZEN
PRICE_ADJUSTMENT_CONTRACT = FROZEN
REPRODUCIBILITY_CONTRACT = FROZEN
VALIDATION_CONTRACT = FROZEN
P2_CERTIFICATION_GIT_DATA_SCOPE = CLARIFIED
CERTIFICATION_DATASET_ROWS_IN_GIT = NO
HISTORICAL_PUBLIC_CORROBORATION_VALUES_IN_DOCUMENTATION = ALLOWED_EVIDENCE_ONLY
SEALED_OOS_START_SESSION_SELECTED = YES
P2_CERTIFICATION_WINDOW_STATUS = PREREGISTERED_SEALED_OOS_NOT_YET_AVAILABLE
P2_FREE_UPSTREAM_IDENTITY_BINDING_IMPLEMENTATION = COMPLETE
P2_FREE_UPSTREAM_IDENTITY_BINDING_IMPLEMENTATION_CLASSIFICATION = UPSTREAM_FIRST_THIN_BOUNDARY
P2_FREE_UPSTREAM_IDENTITY_BINDING_MINIMIZATION_CLEANUP = COMPLETE
P2_FREE_UPSTREAM_IDENTITY_BINDING_FAIL_CLOSED_HARDENING = COMPLETE
P2_PROVIDER_BINDING_LOCATION = 10_DATA_SYSTEM_MARKET_DATA_PROVIDER_BINDING_AUTHORITY
P2_PROVIDER_BINDING_TREE_OWNERSHIP = CORRECT
P2_PROVIDER_BINDING_AUTHORITY_FACTS = 12
P2_PROVIDER_BINDING_AUTHORITY_TREE_OWNER = MARKET_DATA_P2_BINDING
P1_UNIVERSE_AUTHORITY_UNCHANGED = YES
P2_QLIB_NATIVE_RAGGED_PANEL = COMPLETE
QLIB_RESEARCH_RUNTIME_OWNER = MICROSOFT_QLIB
QLIB_REAL_INTEGRATION = PASS
P2_QLIB_SECURITY_IDENTITIES = 730
P2_QLIB_MEMBERSHIP_RANGES = 745
P2_QLIB_MEMBER_SESSION_ROWS = 1267963
P2_QLIB_MISSING_SESSION_POLICY = PRESERVE_MEMBERSHIP_AND_MASK_SESSION
P2_QLIB_MISSING_SESSION_CAUSES_WHOLE_YEAR_REJECTION = NO
P2_RESEARCH_RUNTIME_EXTERNAL_API_COUNT = 0
P2_DATA_PROVIDER_REMEDIATION = CLOSED
P2_LEGACY_PROVIDER_BINDING_EXECUTABLE = REMOVED
P2_UPSTREAM_CERTIFICATION_STACK_INTEGRATION = COMPLETE
P2_UPSTREAM_CERTIFICATION_STACK_INTEGRATION_CLASSIFICATION = PASS
P2_UPSTREAM_CERTIFICATION_STACK_RUNTIME_ACTIVATION = COMPLETE
P2_UPSTREAM_CERTIFICATION_STACK_P2_BLOCKING_BLOCKERS = 0
P2_UPSTREAM_CERTIFICATION_STACK_BLOCKED_COMPONENTS = NONE
P2_UPSTREAM_CERTIFICATION_STACK_GENERIC_ENGINE_COUNT = 0
P2_CERTIFICATION_PROTOCOL = FROZEN
P2_CERTIFICATION_PROTOCOL_VERSION = V1
P2_CERTIFICATION_PROTOCOL_SHA256 = a9aed881c229f9eb7f85fa23b866168a55dc9c00be3c3b178d91a4af20451dfb
P2_CERTIFICATION_PROTOCOL_ACTIVATION = COMPLETE
SEALED_OOS_START_SESSION = 2026-09-14
MINIMUM_SEALED_OOS_SESSIONS = 126
EARLY_SEALED_RESULT_ACCESS = PROHIBITED
INTERMEDIATE_PEEK = PROHIBITED
ONE_SHOT_RELEASE = YES
P2_HISTORICAL_REHEARSAL = COMPLETE_REJECTED_BY_FROZEN_STATISTICAL_GATES
P2_HISTORICAL_REHEARSAL_STATUS = REJECTED
P2_HISTORICAL_REHEARSAL_READY = NO_REJECTED
P2_HISTORICAL_REHEARSAL_CALENDAR_BLOCKER = RESOLVED_QLIB_NATIVE_FUTURE_CALENDAR
P2_HISTORICAL_REHEARSAL_FAILED_MANDATORY_GATES = SPA, REALITY_CHECK, STEPM
SEALED_OOS_AVAILABLE = NO
P2 = COMPLETE
P2_EXIT_CONDITION = SATISFIED
FALSE_ALPHA_CONTROLS_OPERATIONAL = YES
CERTIFICATION_SYSTEM_OPERATIONAL = YES
P2_COMPLETION_REQUIRES_CERTIFIED_MODEL = NO
P3_AUTONOMOUS_RESEARCH = COMPLETE
P3_RESEARCH_CAN_START = YES
P3_CAN_ACCESS_SEALED_OOS = NO
P3_CAN_ISSUE_CERTIFIED = NO
RD_AGENT_ROLE = P3_AUTONOMOUS_RESEARCH_OWNER_WITH_QLIB
P3_UPSTREAM_RESEARCH_STACK_INTEGRATION = COMPLETE_WITH_RDAGENT_RUNTIME_ALIGNMENT_PASS
P3_RDAGENT_RUNTIME = PASS_AUDITED_SOURCE_0_8_1_DEV37
P3_RDAGENT_PROVENANCE_ALIGNMENT = PASS_SOURCE_SHA_32B3D395E73D9DB5EEE3FE9063D69AEC0FDC83BD
P3_RDAGENT_DEPENDENCY_ALIGNMENT = PASS
P3_RDAGENT_FSSPEC_CONFLICT_ANALYSIS = SAFE_BOUNDED_FSSPEC_DOWNGRADE
P3_RDAGENT_FSSPEC_ALIGNMENT = PASS_2026_6_0
P3_RDAGENT_CONDA_DISCOVERY_PATH_CONFIGURATION = PASS_PROCESS_LOCAL_PATH_ONLY
P3_RDAGENT_QLIB_PIN_ALIGNMENT = PASS_2FB9380B342556DDB50A4B24E4FE8655D548B2B8
P3_RDAGENT_TO_QLIB_RUNTIME_BRIDGE = PASS_NATIVE_QLIBCONDAENV_RUN
P3_US_RAGGED_SCENARIO_CONFIGURATION_PROOF = PASS_THIN_STATIC_CONFIG_REQUIRED
P3_US_RAGGED_STATIC_CONFIG = COMPLETE
P3_US_SCENARIO_CONFIGURATION = THIN_STATIC_CONFIG_MATERIALIZED
P3_US_STATIC_CONFIG_COUNT = 2
P3_CANDIDATE_TO_P2_IDENTITY_CONTRACT_AUDIT = COMPLETE
P3_TO_P2_HANDOFF = THIN_STATIC_MANIFEST_REQUIRED_AFTER_DVC_STAGE
P3_CANDIDATE_ID_STRATEGY = DETERMINISTIC_HASH
P3_CANDIDATE_IDENTITY_FIELD_COUNT = 8
P3_CANDIDATE_IDENTITY_IS_CERTIFICATION_RESULT = NO
P3_RDAGENT_US_TEMPLATE_BINDING_UPSTREAM_AUDIT = COMPLETE
RD_AGENT_US_TEMPLATE_BINDING = THIN_SCENARIO_BINDING_REQUIRED
OFFICIAL_RDAGENT_TEMPLATE_OVERRIDE_AVAILABLE = NO
THIN_RDAGENT_SCENARIO_BINDING_FEASIBLE = YES
P3_RDAGENT_US_THIN_SCENARIO_BINDING_DESIGN = COMPLETE
PREFERRED_RDAGENT_US_BINDING = HYPOTHESIS2EXPERIMENT_SUBCLASS_BINDING
RDAGENT_US_BINDING_MODULE_COUNT = 1
RDAGENT_US_TEMPLATE_FILE_COUNT = 5
RDAGENT_US_PROMPT_OVERRIDE_REQUIRED = NO
RDAGENT_FACTOR_SOURCE_DATA_PATH = THIN_BINDING_REQUIRED
RDAGENT_US_THIN_BINDING_DESIGN = READY_FOR_IMPLEMENTATION
P3_RDAGENT_US_FACTOR_SOURCE_DATA_CONTRACT_PROOF = COMPLETE
P3_RDAGENT_US_FACTOR_PRESERVATION_AND_MATERIALIZATION = COMPLETE
QLIB_FACTOR_AVAILABLE_IN_IMMUTABLE_P2_PROVIDER = NO
QLIB_FACTOR_SEMANTICS = RESTORATION_PRICE_ADJUSTMENT_FACTOR_SPLIT_ADJUSTED
AQ_PROVIDER_PRICE_ADJUSTMENT_SEMANTICS = SPLIT_ADJUSTED_OHLC_WITH_EXPLICIT_NONCONSTANT_SPLIT_CUMPROD_AT_SOURCE
CONSTANT_FACTOR_SEMANTICALLY_VALID = NO
QLIB_FACTOR_FIELD_PRESERVATION = PASS
SOURCE_DATA_MATERIALIZATION = THIN_CONFIGURED_QLIB_EXPORT
MATERIALIZER_IMPLEMENTATION = ONE_THIN_CONTRACT_MATERIALIZER
RDAGENT_US_FACTOR_SOURCE_DATA = PASS
FACTOR_SOURCE_DATA_CONTRACT = SATISFIED_BY_THIN_BINDING
P3_RDAGENT_US_THIN_SCENARIO_BINDING_IMPLEMENTATION = COMPLETE
RD_AGENT_US_THIN_BINDING = PASS
RDAGENT_US_PROJECT_BINDING_MODULE_COUNT = 1
RDAGENT_US_PROJECT_TEMPLATE_FILE_COUNT = 5
RDAGENT_US_ACTIVE_CHINA_EXECUTION_DEFAULTS = 0
RDAGENT_US_TEMPLATE_HASH_GUARD = PASS
RDAGENT_US_FACTOR_SOURCE_GUARD = PASS
RDAGENT_US_QUANT_SOURCE_GUARD = PASS
REAL_RDAGENT_US_TEMPLATE_PATH = PROVEN_WITHOUT_AUTONOMOUS_EXECUTION
P3_DVC_STAGE_ACTIVATION = PASS
P3_DVC_STAGE_NAME = p3_rdagent_us_quant_research
P3_DVC_STAGE = ACTIVATED_DEFINITION_ONLY
P3_DVC_LOCK_ENTRY = PENDING_FIRST_AUTHORIZED_AUTONOMOUS_RUN
RUN_SCOPED_MLFLOW_DB_IS_DVC_OUTPUT = YES
OLD_SHARED_MLFLOW_DB_IS_DVC_OUTPUT = NO
MLFLOW_ARTIFACTS_UNDER_DVC_OUTPUT = YES
P3_MLFLOW_DVC_ARTIFACT_ALIGNMENT = PASS
DVC_REQUIRED_IDENTITY_COVERAGE = READY_FOR_FIRST_AUTHORIZED_RUN
P3_CANDIDATE_TO_P2_IDENTITY_CONTRACT = MATERIALIZED
P3_CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V1
P3_CANDIDATE_REQUIRED_IDENTITY_FIELD_COUNT = 8
P3_CANDIDATE_ID_INPUT_FIELD_COUNT = 7
P3_REAL_CANDIDATE_INSTANCE_CREATED = NO
P3_LOCAL_FREE_LLM_BACKEND = ACTIVE
P3_LOCAL_CHAT_BACKEND = OLLAMA_QWEN3_4B
P3_LOCAL_EMBEDDING_BACKEND = OLLAMA_QWEN3_EMBEDDING_0_6B
P3_LOCAL_LLM_ENDPOINT_SCOPE = LOCALHOST_ONLY
P3_PAID_LLM_REQUESTS = 0
P3_PAID_EMBEDDING_REQUESTS = 0
P3_LLM_ROUTER_OWNER = LITELLM
P3_CHAT_LOGICAL_SLOT = aq-brain
P3_CHAT_LOCAL_SLOT = aq-brain-local
P3_CHAT_CLOUD_SLOT = aq-brain-cloud
P3_DEFAULT_CHAT_POLICY = LOCAL_ONLY_WITH_MANUAL_CLOUD_OVERRIDE
P3_AUTO_CLOUD_FALLBACK_SAFE = NO
P3_CLOUD_CHAT_STATE = CONFIGURED_NOT_ARMED
P3_EMBEDDING_LOGICAL_SLOT = aq-embedding
P3_EMBEDDING_LOCAL_SLOT = aq-embedding-local
P3_EMBEDDING_CLOUD_SLOT = aq-embedding-cloud
P3_EMBEDDING_AUTO_CROSS_MODEL_FALLBACK = NO
P3_EMBEDDING_EPOCH_REQUIRED_FOR_MODEL_SWITCH = YES
P3_CANDIDATE_V1_BINDS_LLM_EXECUTION_IDENTITY = NO
P3_CANDIDATE_CONTRACT_UPGRADE_REQUIRED = YES
P3_PROPOSED_CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V2
P3_CUSTOM_AQ_ROUTER_REQUIRED = NO
P3_CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V2
P3_CANDIDATE_TOP_LEVEL_FIELD_COUNT = 8
P3_LLM_EXECUTION_IDENTITY_REQUIRED = YES
P3_LOCAL_CHAT_LOGICAL_SLOT = aq-brain-local
P3_LOCAL_CHAT_RESOLVED_MODEL = qwen3:4b
P3_LOCAL_EMBEDDING_LOGICAL_SLOT = aq-embedding-local
P3_LOCAL_EMBEDDING_RESOLVED_MODEL = qwen3-embedding:0.6b
P3_EMBEDDING_EPOCH_IDENTITY = e63389904f57782a645d2f9d79ec5f028b8a7ef99aa051a2cdb0ca2e55dbf6db
P3_MODEL_RESIDENCY_POLICY = ON_DEMAND
P3_CLOUD_CHAT_INTERFACE = RESERVED_NOT_IMPLEMENTED
P3_CLOUD_EMBEDDING_INTERFACE = RESERVED_NOT_IMPLEMENTED
P3_LITELLM_GATEWAY_DEPLOYED = NO
P3_AUTO_CLOUD_FALLBACK = NO
P3_DVC_LLM_CONFIGURATION_DEPENDENCY = ACTIVE
P3_LOCAL_BRAIN_RESOURCE_ADMISSION = PASS
P3_LOCAL_CHAT_RESOLVED_MODEL = qwen2.5-coder:7b
P3_LOCAL_CHAT_RESOLVED_DIGEST = dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
P3_LOCAL_CHAT_BASELINE_FALLBACK = qwen3:4b
P3_LOCAL_EMBEDDING_CHANGED = NO
P3_MODEL_RESIDENCY_POLICY = ON_DEMAND
P3_LOCAL_BRAIN_RESOURCE_RECOVERY = PASS
P3_POST_LLM_QLIB_RESOURCE_READINESS = PASS
P3_CANDIDATE_V2_SCHEMA_CHANGE_REQUIRED = NO
INITIAL_V2_MATERIALIZATION_COMMIT = c3f2374d29ba9e691a8cf4fb4eb00283d4416b3d
INITIAL_V2_SPEC_SHA256 = d052a429269995e12c572863c307f6a8eb9adcf70f97a460e1ea16274dc44c1c
CURRENT_V2_SPEC_SHA256 = a5ca1f92684cc2eec3bed9024e4c9f221cc23b4c4992029d4d41963ac088837a
CURRENT_V2_SCHEMA_SHA256 = a7f1c175c68188e641eacc61da2ba2683a9b1b6d6021cf1faa25f5543818266b
SPEC_EVOLUTION_COMMIT = 184031d4b9b58b913fa8fa5c063cfe3a9a6b2d1e
SPEC_EVOLUTION_REASON = LOCAL_CHAT_MODEL_IDENTITY_MOVED_FROM_HARDCODED_SPEC_VALUE_TO_DVC_BOUND_RUNTIME_IDENTITY
SCHEMA_CHANGED_BY_SPEC_EVOLUTION = NO
CANDIDATE_TOP_LEVEL_FIELD_COUNT = 8
CANDIDATE_V2_CONTRACT_STATUS = ACTIVE
P3_RDAGENT_LITELLM_EFFECTIVE_CONTEXT_HEADROOM_RESOLUTION = PASS
P3_LITELLM_CONTEXT_RESOLUTION_MODE = LITELLM_PUBLIC_REGISTER_MODEL
P3_EFFECTIVE_CHAT_INPUT_LIMIT = 28672
P3_CHAT_MAX_OUTPUT_TOKENS = 4096
P3_CONTEXT_HEADROOM_GATE = PASS
P3_LOCAL_CHAT_HEALTH = PASS
P3_LOCAL_EMBEDDING_HEALTH = PASS
P3_CUSTOM_COMPLETION_LOGIC = 0
P3_CUSTOM_EMBEDDING_LOGIC = 0
P3_CUSTOM_ROUTER_LOGIC = 0
P3_FAILED_ATTEMPT_001_STATE = PRESERVED_IMMUTABLE_PRE_RESEARCH_FAILURE
P3_FAILED_ATTEMPT_001_MANIFEST_SHA256 = 1f671a5ee8a0a854731750a03ad50683a9d938ea0c473ef075ae678ed18e48b2
P3_RUNTIME_NAMESPACE_DECOUPLING = PASS
P3_CONDA_DEFAULT_ENV = rdagent4qlib
P3_FAILED_ATTEMPT_002_STATE = PRESERVED_IMMUTABLE_LOOP_0_FACTOR_CODING_EXECUTION_FAILURE
P3_FAILED_ATTEMPT_002_FAILURE_PHASE = LOOP_0_FACTOR_CODING_EXECUTION
P3_FAILED_ATTEMPT_002_ROOT_CAUSE = FACTOR_SUBPROCESS_PYTHON_INTERPRETER_MISALIGNMENT
P3_FAILED_ATTEMPT_002_LOCAL_CHAT_CALL_COUNT = 28
P3_FAILED_ATTEMPT_002_MODEL_TRAINING = NO
P3_FAILED_ATTEMPT_002_NEW_PREDICTIONS = NO
P3_FAILED_ATTEMPT_002_BACKTEST = NO
P3_FAILED_ATTEMPT_002_CANDIDATE_V2_CREATED = NO
P3_RDAGENT_FACTOR_RUNTIME_PYTABLES_DEPENDENCY = RESOLVED
P3_FACTOR_RUNTIME_TABLES_VERSION = 3.10.1
P3_FACTOR_RUNTIME_PYTHON = /home/zhou/miniforge3/envs/rdagent4qlib/bin/python
P3_FACTOR_RUNTIME_PANDAS_VERSION = 2.3.3
P3_FACTOR_RUNTIME_NUMPY_VERSION = 2.2.6
P3_FACTOR_RUNTIME_HDF_PROOF = PASS
P3_FACTOR_RUNTIME_PIP_CHECK = PASS
P3_FACTOR_SUBPROCESS_INTERPRETER_ALIGNMENT = PASS
P3_FACTOR_SUBPROCESS_PYTHON = /home/zhou/miniforge3/envs/rdagent4qlib/bin/python
P3_FACTOR_SUBPROCESS_HDF_READ = PASS
P3_FACTOR_SUBPROCESS_REGRESSION_TEST = PASS
P3_BINDING_TESTS = 15/15_PASS
P3_MATERIALIZER_TESTS = 5/5_PASS
P3_LLM_BACKEND_TESTS = 7/7_PASS
P3_TOTAL_RELEVANT_TESTS = 27/27_PASS
P3_DVC_STAGE_PARSE = PASS
P3_DVC_DAG = PASS
P3_NEXT_RUN_NAMESPACE = p3-fin-quant-004
P3_TEMPLATE_ATTEMPT_ID_COUNT = 0
P3_FUTURE_ATTEMPT_REQUIRES_TEMPLATE_CHANGE = NO
P3_FUTURE_ATTEMPT_REQUIRES_HASH_REFRESH = NO
P3_FAILED_ATTEMPT_003_STATE = PRESERVED_IMMUTABLE_LOOP_0_FACTOR_CODING_AND_EVALUATION_FAILURE
P3_FAILED_ATTEMPT_003_FAILURE_PHASE = RD_AGENT_FACTOR_CODING_AND_EVALUATION
P3_FAILED_ATTEMPT_003_LOCAL_CHAT_CALL_COUNT = 35
P3_FAILED_ATTEMPT_003_ENTRY_COUNT = 733
P3_FAILED_ATTEMPT_003_REGULAR_FILE_COUNT = 731
P3_FAILED_ATTEMPT_003_SYMLINK_COUNT = 2
P3_FAILED_ATTEMPT_003_TOTAL_REGULAR_BYTES = 3949151
P3_FAILED_ATTEMPT_003_COMPLETE_ENTRY_MANIFEST_SHA256 = 4ddca2def8b5ba1ed21c8f6dbf1c69aa0dbe87bba8521bb94e4fb95cca83bd84
P3_FAILED_ATTEMPT_003_MODEL_TRAINING = NO
P3_FAILED_ATTEMPT_003_NEW_PREDICTIONS = NO
P3_FAILED_ATTEMPT_003_BACKTEST = NO
P3_FAILED_ATTEMPT_003_CANDIDATE_V2_CREATED = NO
P3_AUTONOMOUS_ATTEMPT_COUNT_THIS_TASK = 1
P3_ATTEMPT_003_FACTOR_BLOCKER_PRIMARY = MODEL_INSTRUCTION_NONCOMPLIANCE
P3_ATTEMPT_003_FACTOR_BLOCKER_SECONDARY = UPSTREAM_PROMPT_CONTRACT_GAP; COSTEER_EVALUATOR_FEEDBACK_GAP; MISSING_SUCCESS_KNOWLEDGE
P3_ATTEMPT_003_FACTOR_RESOLUTION = B_PLUS_C_UPSTREAM_STRATEGY_EXPOSURE_AND_OFFICIAL_FACTOR_ADMISSION
P3_ATTEMPT_003_DVC_BLOCKER = WINDOWS_DVC_CANNOT_INSPECT_WSL_CREATED_SYMLINK_ON_EXTERNAL_D_MOUNT_OUTPUT
P3_ATTEMPT_003_DVC_RESOLUTION = A_PLUS_C_PINNED_WSL_DVC_AND_PORTABLE_P3_PATHS
P3_FACTOR_STRATEGY_EXPOSURE = PASS
P3_UPSTREAM_FACTOR_STRATEGY_COPIED_TO_AQ = NO
P3_FACTOR_CODER_ADMISSION_CASES = alpha053; alpha053_15; alpha053_5
P3_FACTOR_CODER_ADMISSION_ROUNDS = 2
P3_FACTOR_CODER_ADMISSION_TOTAL_REQUIRED = 6
P3_FACTOR_CODER_ADMISSION_COMPLETED = 0
P3_FACTOR_CODER_ADMISSION_PASSES = 0
P3_FACTOR_CODER_ADMISSION_FAILURES = 6
P3_FACTOR_CODER_ADMISSION = FAIL
P3_WSL_DVC_ENV = /home/zhou/AQ_ENVS/dvc-p3
P3_WSL_DVC_VERSION = 3.67.1
P3_WSL_DVC_FREEZE_SHA256 = 4d40f9b8475d5a9cf06bc30e73159f44eb9b4e57a59e6663f9ab3d95cc6614ec
P3_WSL_DVC_WSL_SYMLINK_TEST = PASS
P3_DVC_EXECUTION_OS = WSL_LINUX
P3_WINDOWS_DVC_EXECUTION = NOT_AUTHORIZED
P3_PORTABLE_EXTERNAL_PATHS = PASS
P3_RUN_004_ROOT_CREATED = NO
P3_ATTEMPT_003_DVC_BLOCKER_RESOLVED = YES
P3_ATTEMPT_003_FACTOR_STRATEGY_GAP_RESOLVED = YES
P3_ATTEMPT_003_BLOCKERS_RESOLVED = NO_FACTOR_CODER_ADMISSION_FAILED
P3_OFFICIAL_OLLAMA_CHAT_PATH = SUPPORTED
P3_OFFICIAL_OLLAMA_STRUCTURED_OUTPUT = SUPPORTED
P3_PINNED_LITELLM_RESPONSE_FORMAT_MAPPING = SUPPORTED
P3_OLLAMA_ROUTE_SUPPORTS_RESPONSE_SCHEMA_BEFORE = FALSE
P3_OLLAMA_CHAT_ROUTE_SUPPORTS_RESPONSE_SCHEMA_BEFORE = FALSE
P3_PUBLIC_CAPABILITY_METADATA_SEAM = PASS
P3_LOCAL_CHAT_ROUTE = ollama_chat/aq-brain-local
P3_LOCAL_CHAT_STRUCTURED_OUTPUT = PASS
P3_LOCAL_CHAT_MARKDOWN_FENCE_PRESENT = NO
P3_LLM_CONFIGURATION_SHA256 = 770f25c549a83b709535e376cca519d7c7fb1c988eb4f68cb76d8df0fbfaddf9
P3_EMBEDDING_EPOCH_CHANGED = NO
P3_FACTOR_CODER_ADMISSION_002_REPORT_SHA256 = b963e550197ae12850991ed1e673b68d2f34850d7e511aca93bc7cc5bfca98cb
P3_FACTOR_CODER_ADMISSION_002_COMPLETED = 0
P3_FACTOR_CODER_ADMISSION_002_PASSES = 0
P3_FACTOR_CODER_ADMISSION_002_FAILURES = 6
P3_FACTOR_CODER_ADMISSION_002_FAILURE_TAXONOMY = COSTEER_RECOVERY:6
P3_QWEN2_5_CODER_7B_FACTOR_ADMISSION = FAIL
P3_MODEL_REPLACEMENT_REQUIRED = YES
P3_NEXT_AUTONOMOUS_ATTEMPT_AUTHORIZED = NO
P3_LLM_BACKEND_TESTS = 8/8_PASS
P3_TOTAL_RELEVANT_TESTS = 28/28_PASS
P3_OLLAMA_CONTEXT_CERTIFICATION_REPORT_SHA256 = 914b87f29a8bedc2c78fd80273c8a53f660bdde736d2e09f038a1a95d7b0a6e7
P3_CERTIFIED_OLLAMA_CONTEXT = 32768
P3_PRODUCTION_OLLAMA_CONTEXT = 32768
P3_OLLAMA_NUM_PARALLEL = 1
P3_OLLAMA_CONTEXT_MISMATCH = CLOSED
P3_QWEN2_5_HISTORICAL_ADMISSION = VALID_FAIL
P3_FACTOR_CODER_CANDIDATE_BENCHMARK_001 = PROVISIONAL_NOT_VALID_FOR_SELECTION
P3_BENCHMARK_RESTART_AUTHORIZED = YES
P3_AUTONOMOUS_ATTEMPT_004_AUTHORIZED = NO
P3_FACTOR_CODER_CANDIDATE_BENCHMARK_002 = FAIL_INFRASTRUCTURE_CONTEXT_GATE_MISMATCH
P3_BENCHMARK_002_GROUND_TRUTH_SELF_TEST = PASS
P3_BENCHMARK_002_CANDIDATES_RUNTIME_TESTED = 3
P3_BENCHMARK_002_SCREENS_EXECUTED = 0
P3_BENCHMARK_002_FULL_ADMISSIONS_EXECUTED = 0
P3_BENCHMARK_002_SELECTED_MODEL = NONE
P3_BENCHMARK_002_DEEPSEEK_ACTUAL_CONTEXT = 16384
P3_BENCHMARK_002_REPORT_SHA256 = 0742fdb7e3d468e7cde2e008dceda607dcdfd4e7c268dc5e51180c032767bbe5
P3_BENCHMARK_002_EXECUTION_RECORD = PRESERVED_UNCHANGED
P3_BENCHMARK_002_GROUND_TRUTH_SELF_TEST = PASS
P3_GLOBAL_OLLAMA_32K_CONTRACT = PASS
P3_QWEN3_5_4B_CONTEXT_GATE = CONTEXT_ELIGIBLE
P3_GRANITE_CODE_8B_INSTRUCT_CONTEXT_GATE = CONTEXT_ELIGIBLE
P3_DEEPSEEK_CODER_6_7B_INSTRUCT_CONTEXT_GATE = CONTEXT_INELIGIBLE_FOR_P3
P3_DEEPSEEK_RESULT = EXPECTED_CANDIDATE_NATIVE_LIMIT
P3_LLAMA3_1_8B_CONTEXT_GATE = CONTEXT_ELIGIBLE
P3_GLOBAL_INFRASTRUCTURE_DEFECT = NO
P3_CANDIDATE_NATIVE_CONTEXT_BELOW_32768_ACTION = REJECT_CANDIDATE_INDIVIDUALLY
P3_BENCHMARK_003_AUTHORIZED = YES
P3_NEXT_AUTONOMOUS_ATTEMPT_AUTHORIZED = NO
P3_FACTOR_CODER_CANDIDATE_BENCHMARK_003 = PASS_NO_FIRST_TIER_CANDIDATE_ADMITTED
P3_BENCHMARK_003_CANDIDATES_TESTED = qwen3.5:4b; granite-code:8b-instruct; llama3.1:8b
P3_BENCHMARK_003_QWEN3_5_SCREEN = PASS
P3_BENCHMARK_003_QWEN3_5_FULL_ADMISSION = FAIL_0_OF_6
P3_BENCHMARK_003_GRANITE_SCREEN = FAIL_TYPED_SCHEMA
P3_BENCHMARK_003_LLAMA_SCREEN = FAIL_AFTER_10_COSTEER_LOOPS
P3_BENCHMARK_003_SELECTED_MODEL = NONE
P3_BENCHMARK_003_ALIAS_RESTORED_MODEL = qwen2.5-coder:7b
P3_BENCHMARK_003_ALIAS_RESTORED_DIGEST = dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
P3_BENCHMARK_003_LLM_CONFIGURATION_SHA256 = 770f25c549a83b709535e376cca519d7c7fb1c988eb4f68cb76d8df0fbfaddf9
P3_BENCHMARK_003_PRIVATE_REPORT_SHA256 = b16cf0d9e839d9f6638816270cf8e3f82ae7ed4d3fcf3088dd2b9fe68d9f4397
P3_BENCHMARK_003_REPOSITORY_TESTS = 28/28_PASS
P3_NEXT_AUTONOMOUS_ATTEMPT_AUTHORIZED = NO
P3_RD_AGENT_LOCAL_BRAIN_SEARCH = PAUSED_NOT_P3_BLOCKER
P3_FORMULAIC_ALPHA_NATIVE_DEPLOYMENT = PASS_WITH_UPSTREAM_DEPENDENCY_BLOCKERS
P3_ALPHAGEN_NATIVE_DEPLOYMENT = BLOCKED_UPSTREAM_DEPENDENCY_INSTALL
P3_ALPHAFORGE_NATIVE_DEPLOYMENT = BLOCKED_UPSTREAM_DEPENDENCY_INSTALL
P3_ALPHAGPT_NATIVE_DEPLOYMENT = DEPLOYED_WITH_OFFICIAL_DATA_CREDENTIAL_BLOCKER
P3_FORMULAIC_ALPHA_NATIVE_DEPLOYMENT_REPORT_SHA256 = dd606f06458c2904c7b69fc4f8e38ae670eb9f925950bb5cf4154473626eca52
P3_FORMULAIC_ALPHA_UPSTREAM_NATIVE_POC = PASS_EVALUATION_NO_NATIVE_ALPHA_ARTIFACT
P3_ALPHAGEN_UPSTREAM_GUIDANCE_ENV = IMPORT_AND_CLI_PASS_PIP_METADATA_AND_UNBOUNDED_DATA_BLOCKED
P3_ALPHAFORGE_README_ENV = IMPORT_AND_CLI_PASS_DEPENDENCY_AND_SOURCE_CONFIGURATION_BLOCKED
P3_ALPHAGPT_NATIVE_POC = READY_FOR_NATIVE_POC_PENDING_CREDENTIAL
P3_FORMULAIC_ALPHA_NATIVE_ALPHA_GENERATION_EXECUTED = NO
P3_FORMULAIC_ALPHA_NATIVE_ALPHA_ARTIFACTS_PRODUCED = 0
P3_FORMULAIC_ALPHA_POC_SUMMARY_SHA256 = 4d7d0603682fa3915615a5b9f7af12011dd2550f5c46924b9ecb704bd5b84773
P3_FORMULAIC_ALPHA_PERMANENT_AUTHORITY_SELECTED = NO
P3_FORMULAIC_ALPHA_UPSTREAM_BLOCKER_CLOSEOUT = COMPLETE_WITH_ALPHAGEN_EXTERNAL_CALCULATOR_BOUNDARY
P3_ALPHAGEN_NATIVE_CN_DATA_BLOCKER = NON_BLOCKING_FOR_EXTERNAL_CALCULATOR_INTEGRATION
P3_ALPHAGEN_EXTERNAL_CALCULATOR_INTERFACE = PASS
P3_ALPHAGEN_US_PIT_THIN_ADAPTER_POC = BLOCKED_FEATURE_SPACE_COMPATIBILITY
P3_ALPHAGEN_AQ_AUTHORITATIVE_FEATURES = OPEN,HIGH,LOW,CLOSE,VOLUME
P3_ALPHAGEN_VWAP_AVAILABLE = NO
P3_ALPHAGEN_PUBLIC_FEATURE_SPACE_RESTRICTION = ABSENT
P3_ALPHAGEN_PRIOR_UPSTREAM_MODIFICATION_CONCLUSION = SUPERSEDED_BY_SB3_ACTION_MASKER
P3_ALPHAGEN_AQ_ADAPTER_CREATED = YES_DOMAIN_SPECIFIC_THIN_ADAPTER
P3_ALPHAGEN_PRIOR_BLOCKED_RL_TIMESTEPS = 0
P3_ALPHAGEN_PRIOR_BLOCKER_POC_SUMMARY_SHA256 = a8d5d2084c4ca288b7ffdd3ec9076f25f1c8c942b86388489c421a642ecc2d98
P3_ALPHAGEN_PERMANENT_AUTHORITY_SELECTED = NO
P3_ALPHAGEN_VWAP_FEATURE_SPACE_BLOCKER = RESOLVED_BY_UPSTREAM_SB3_ACTION_MASKER
P3_ALPHAGEN_SB3_CONTRIB_VERSION = 2.0.0
P3_ALPHAGEN_VWAP_ACTION_INDEX = 27
P3_ALPHAGEN_MASK_DIFF_COUNT_MAX = 1
P3_ALPHAGEN_VWAP_ACTION_SELECTION_COUNT = 0
P3_ALPHAGEN_US_PIT_ACTION_MASK_POC = PASS_RUNTIME_POC_ONLY_NOT_RESEARCH_EVIDENCE
P3_ALPHAGEN_POC_INSTRUMENTS = 32
P3_ALPHAGEN_POC_EVALUATION_SESSIONS = 61
P3_ALPHAGEN_POC_RL_TIMESTEPS = 2048
P3_ALPHAGEN_POC_EXPRESSIONS_GENERATED = 9
P3_ALPHAGEN_POC_EXPRESSIONS_EVALUATED = 7
P3_ALPHAGEN_POC_POOL_ADMISSION_COUNT = 5
P3_ALPHAGEN_POC_SUMMARY_SHA256 = 8acde157d3dfed66e70891de7d639ba9fa246e7dd01924fddc86be9cd19db4c0
P3_ALPHAGEN_UPSTREAM_SOURCE_MODIFIED = NO
P3_ALPHAGEN_US_PIT_INTEGRATION = ACTIVE
P3_ALPHAGEN_UPSTREAM_SHA = 259687e8f316994426416c530a94842a2fe6405e
P3_ALPHAGEN_UPSTREAM_MODIFIED = NO
P3_ALPHAGEN_VWAP_FEATURE_SPACE_BLOCKER = CLOSED_RESOLVED_BY_SB3_ACTION_MASKER
P3_RUNTIME_POC_ALPHA = PROOF_ONLY_NOT_RESEARCH_EVIDENCE
P3_FORMULAIC_ALPHA_CHALLENGERS = ALPHAFORGE_AND_ALPHAGPT_NOT_CURRENT_MAINLINE
P3_ALPHAGEN_INTEGRATION_TESTS = 9/9_PASS
P3_ALPHAGEN_RUNTIME_PARITY = PASS_2048_STEPS
P3_ALPHAGEN_INTEGRATION_SUMMARY_SHA256 = 28cc750721f7d8a61e44e107cd5ddf12bf6149aec934562c8fc9b9a28204d2a7
P3_AUTONOMOUS_ATTEMPT_004_AUTHORIZED = NO
P3_PRIOR_DISCOVERY_RUN_001 = ABORTED_RESOURCE_CALIBRATION_INVALID
P3_ALPHAGEN_RUNTIME_ROOT_CAUSE = UPSTREAM_L1_POOL_OPTIMIZATION_NONLINEAR_COST
P3_ALPHAGEN_RAGGED_PIT_CORRECTNESS = PASS
P3_ALPHAGEN_MSE_LSTSQ_FAST_V1 = QUALIFIED
P3_ALPHAGEN_MSE_LSTSQ_FAST_V1_L1_ALPHA = 0.0
P3_ALPHAGEN_MSE_LSTSQ_FAST_V1_FORMAL_TIMESTEPS_PER_SEED = 32768
P3_ALPHAGEN_MSE_L1_REFERENCE_V1 = REFERENCE_RESOURCE_EXPENSIVE
P3_ALPHAGEN_FASTPATH_CLOSEOUT_SUMMARY_SHA256 = d807aa503f082f6c526bd67606dc6e3a142426ef2ded2d85ce5dcd4c7a3d83af
P3_ALPHAGEN_MSE_LSTSQ_FAST_V1 = FORMAL_DISCOVERY_CONFIG
P3_ALPHAGEN_FACTOR_DISCOVERY_LSTSQ_RUN_001 = PASS
P3_ALPHAGEN_FORMAL_SEEDS_COMPLETED = 3
P3_ALPHAGEN_EXPRESSIONS_GENERATED_TOTAL = 7993
P3_ALPHAGEN_EXPRESSIONS_EVALUATED_TOTAL = 2720
P3_ALPHAGEN_RAW_POOL_ENTRY_COUNT = 60
P3_ALPHAGEN_UNIQUE_EXPRESSION_COUNT = 60
P3_ALPHAGEN_CORRELATION_CLUSTER_COUNT = 17
P3_ALPHAGEN_RESEARCH_ALPHA_CANDIDATE_COUNT = 17
P3_ALPHAGEN_DISCOVERY_HISTORICAL_TEST_ROWS_ACCESSED = 0
P3_ALPHAGEN_DISCOVERY_SEALED_OOS_ROWS_ACCESSED = 0
P3_ALPHAGEN_DISCOVERY_SUMMARY_SHA256 = 5212564ed15b3fa15bde40f14b9fe9a067b725bc5dd472a6046af0013893523a
P3_ALPHAGEN_QLIB_CANDIDATE_EVALUATION = PASS
P3_ALPHAGEN_FROZEN_CANDIDATE_COUNT = 17
P3_ALPHAGEN_FROZEN_CANDIDATE_MANIFEST_SHA256 = de536d7396f6786ea7b27c6a2f5f0970826ce7894b1e17d80361bf11085ff145
P3_ALPHAGEN_QLIB_EVALUATION_MODEL = qlib.contrib.model.linear.LinearModel(estimator=ols)
P3_ALPHAGEN_QLIB_FIT_POLICY = TRAIN_ONLY
P3_ALPHAGEN_HISTORICAL_TEST_EFFECTIVE_RANGE = 2022-01-03_THROUGH_2024-12-27
P3_ALPHAGEN_QLIB_CANDIDATES_EVALUATED = 17
P3_ALPHAGEN_QLIB_RECORDERS_FINISHED = 17
P3_ALPHAGEN_QLIB_PREDICTION_ARTIFACTS = 17
P3_ALPHAGEN_HISTORICAL_TEST_ROWS_ACCESSED = 377938
P3_ALPHAGEN_HISTORICAL_TEST_STATUS = CONSUMED_AS_RESEARCH_EVIDENCE
P3_ALPHAGEN_EVALUATION_SEALED_OOS_ROWS_ACCESSED = 0
P3_ALPHAGEN_RANKIC_SIGN_CONSISTENT_COUNT = 7
P3_ALPHAGEN_IC_SIGN_CONSISTENT_COUNT = 11
P3_ALPHAGEN_QLIB_EVALUATION_SUMMARY_SHA256 = c077196473711ebcbd33e572cb4e3de5a07103dba9e7aa8f88f255a7acf9b6a0
P3_ALPHAGEN_QLIB_ARTIFACT_MANIFEST_V2_SHA256 = 4da1e39480f84c284a7bd7d01bdc921226b4752e1759aff82dbf2d576214e01f
P3_ALPHAGEN_CANDIDATE_V2_CREATED = NO
P3_ALPHAGEN_CANDIDATE_V2_COMPATIBILITY = INCOMPATIBLE_REQUIRES_RDAGENT_LLM_IDENTITY
P3_FORMULAIC_ALPHA_HANDOFF_CONTRACT = AUDIT_REQUIRED
P3_FORMULAIC_ALPHA_CANDIDATE_HANDOFF_CONTRACT_AUDIT = PASS
P3_CANDIDATE_V1 = IMMUTABLE
P3_CANDIDATE_V2 = IMMUTABLE_RDAGENT_LLM_SPECIFIC
P3_CANDIDATE_V1_V2_RDAGENT_SPECIFIC_FIELD_COUNT = 22
P3_CANDIDATE_V2_LLM_SPECIFIC_FIELD_COUNT = 26
P3_CANDIDATE_GENERIC_REUSABLE_FIELD_COUNT = 61
P3_FORMULAIC_ALPHA_RECOMMENDED_CONTRACT = P3_CANDIDATE_TO_P2_CONTRACT_V3
P3_FORMULAIC_ALPHA_RECOMMENDED_TOP_LEVEL_FIELD_COUNT = 8
P3_FORMULAIC_ALPHA_CANDIDATE_CARDINALITY = ONE_CANDIDATE_PER_EXPRESSION
P3_FORMULAIC_ALPHA_DVC_IDENTITY = ABSENT_REQUIRES_REPRODUCIBILITY_SEAL
P3_FORMULAIC_ALPHA_CURRENT_P2_PROTOCOL_ELIGIBILITY = INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION
P3_FORMULAIC_ALPHA_HANDOFF_AUDIT_REPORT_SHA256 = 280b214026f3490e58cf8bca04a532300eaa54a7337c34b2f40e551188280c74
P3_FORMULAIC_ALPHA_DVC_REPRODUCIBILITY_SEAL = PASS
P3_FORMULAIC_ALPHA_DVC_IDENTITY = PRESENT
P3_FORMULAIC_ALPHA_RUNTIME_FREEZE = PASS
P3_FORMULAIC_ALPHA_RUNTIME_ENV_DRIFT_SINCE_RESEARCH = NO_PROVEN_DRIFT
P3_FORMULAIC_ALPHA_DVC_STAGE = p3_formulaic_alpha_reproducibility_seal
P3_FORMULAIC_ALPHA_DVC_STAGE_LOCK_ENTRY_SHA256 = 659b1ae448be57c915d5f096fa3b112afef0232f69739fb4eaa7ab267c301df1
P3_FORMULAIC_ALPHA_DVC_SEAL_OUTPUT_SHA256 = 60e5d0b271fa6e5a074f329a752ea5d80abfe2a1cb49dd89d1ed33609052fecb
P3_FORMULAIC_ALPHA_DVC_SEAL_PRIVATE_REPORT_SHA256 = a9f5dce9dee55f87e72a6b31d71b7f77fbf15db42cf0c68ce07f7c7b8dab7e10
P3_FORMULAIC_ALPHA_DVC_SECOND_REPRO = UNCHANGED_DATA_AND_PIPELINES_UP_TO_DATE
P3_FORMULAIC_ALPHA_HISTORICAL_RESEARCH_TEST_STATUS = CONSUMED_AS_RESEARCH_EVIDENCE
P3_FORMULAIC_ALPHA_CURRENT_P2_PROTOCOL_ELIGIBILITY = INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION
P3_CANDIDATE_TO_P2_CONTRACT_V3 = MATERIALIZED
P3_CANDIDATE_V3_TOP_LEVEL_FIELD_COUNT = 8
P3_CANDIDATE_V3_PRODUCER_NEUTRAL = YES
P3_CANDIDATE_V3_REAL_INSTANCE_COUNT = 17
P3_CANDIDATE_V3_SCHEMA_VALID_COUNT = 17
P3_CANDIDATE_V3_ID_RECOMPUTE_PASS_COUNT = 17
P3_CANDIDATE_V3_UNIQUE_ID_COUNT = 17
P3_CANDIDATE_V3_CURRENT_P2_ELIGIBILITY = INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION
P3_CANDIDATE_V3_RFC8785_IMPLEMENTATION = Python_rfc8785_0.1.4
P3_CANDIDATE_V3_MATERIALIZATION_MANIFEST_SHA256 = 511ef7c25e55afc9cded8d6b2f13ed2715d248705c8cbad71918802d5210b8fd
P3_CANDIDATE_V3_VALIDATION_REPORT_SHA256 = efbbfd90d5068ddb49a787a08e3f8b5f9da526ae7b22fc326e976adf033473db
P3_CANDIDATE_V3_PRIVATE_REPORT_SHA256 = c56eb3323763492126c31d616334d2f4776c8eedfcc843d895e72880a4657ce5
P3_CANDIDATE_V1 = IMMUTABLE
P3_CANDIDATE_V2 = IMMUTABLE_RDAGENT_LLM_SPECIFIC
P3_ALPHAFORGE = CHALLENGER_NOT_CURRENT_MAINLINE
P3_ALPHAGPT = CHALLENGER_NOT_CURRENT_MAINLINE
P3_RD_AGENT_LOCAL_BRAIN_SEARCH = PAUSED_NOT_P3_BLOCKER
P3_EXIT_CONDITION = SATISFIED
P3_AUTHORITATIVE_EXIT_CONDITION = candidates produced automatically
P3_RESEARCH_RUN_INTERNAL_AUTOMATION = PASS
P3_SYSTEM_LEVEL_SELF_TRIGGERING = NOT_IMPLEMENTED_DEFERRED_TO_P4_P12
P3_REAL_CANDIDATE_V3_COUNT = 17
P3_CANDIDATE_V3 = ACTIVE_PRODUCER_NEUTRAL_HANDOFF_CONTRACT
P3_P2_ELIGIBILITY = PENDING_PROTOCOL_EXPANSION_OUTSIDE_P3
FORMULAIC_ALPHA_P2_PROTOCOL_EXPANSION = REQUIRED_BEFORE_FORMULAIC_CERTIFICATION
P4_ENTRY_ALLOWED = YES
P4_ENTRY_ALLOWED_BEFORE_PROTOCOL_EXPANSION = YES
P4_EXIT_REQUIRES_CERTIFIED_ARTIFACT = YES
P4_EXIT_ALLOWED_WITHOUT_CERTIFIED_ARTIFACT = NO
P3_HYGIENE_AUDIT = PASS
P3_PHASE_CLOSEOUT_PRIVATE_REPORT_SHA256 = 99d7faf1459a9a2438162b23bd1adc9f7ca2ff653ce590b389c103d58311835c
P4_CHAMPION_SYSTEM_UPSTREAM_FIT_AND_AUTONOMY_BOUNDARY_AUDIT = PASS
P4_ENTRY = ACTIVE
P4_SYSTEM_LEVEL_SELF_TRIGGERING_BOUNDARY = DETERMINISTIC_POLICY_IN_P4_SCHEDULING_IN_P12
P4_QLIB_ONLINE_MANAGER_FIT = PARTIAL_UPSTREAM_WHOLE_FOR_ONLINE_MODEL_SET_HISTORY_AND_REFRESH_NOT_P4_POLICY
P4_QLIB_ONLINE_STRATEGY_FIT = UPSTREAM_EXTENSION_SEAM_WITH_AQ_THIN_POLICY_INPUT
P4_QLIB_ROLLING_GEN_FIT = PASS_UPSTREAM_WHOLE
P4_QLIB_RECORDER_FIT = PASS_UPSTREAM_WHOLE
P4_MLFLOW_REGISTRY_FIT = PARTIAL_UPSTREAM_LEAF_FOR_MODEL_VERSION_IDENTITY_AND_ALIASES_NOT_CERTIFICATION_POLICY
P4_DVC_LIFECYCLE_FIT = REPRODUCIBILITY_ONLY_NOT_RUNTIME_LIFECYCLE
P4_P2_CERTIFICATION_AUTHORITY = EXTERNAL_SOLE_AUTHORITY
P4_CHALLENGER = ROLE_NOT_SEPARATE_STATE
P4_INITIAL_AUDIT_NEW_UPSTREAM_ADOPTED = NONE
P4_INITIAL_AUDIT_NEW_UPSTREAM_REJECTED_OR_DEFERRED = EVIDENTLY_DEFER; NANNYML_DEFER
P4_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P4_ENTRY_BLOCKERS = NONE
P4_EXIT_BLOCKERS = FORMULAIC_ALPHA_P2_PROTOCOL_EXPANSION; REAL_P2_ISSUED_CERTIFIED_ARTIFACT; SHADOW_EVIDENCE_CONTRACT_AND_OBSERVATION_PATH; LIFECYCLE_POLICY_IMPLEMENTATION_AND_TRANSITION_TESTS; QLIB_MLFLOW_IDENTITY_PROJECTION_INTEGRATION; REAL_END_TO_END_CANDIDATE_CERTIFIED_SHADOW_CHAMPION_PROOF
P4_PRIVATE_REPORT_SHA256 = a1f4a58c7755eae2559249ac200beba8b1322b6703a4efa26491397b55948ade
P4_RESIDUAL_UPSTREAM_SUBSTITUTION_AUDIT = PASS
P4_ALL_RESIDUAL_CAPABILITIES_AUDITED = YES
P4_MODULE_LEVEL_REUSE_AUDITED = YES
P4_SELECTED_NEW_UPSTREAMS = FROUROS_0_9_0_ADWIN_ISOLATED_RUNTIME
P4_KEEP_EXISTING_UPSTREAMS = QLIB; MLFLOW; DVC; RFC8785; P2; P12; PYDANTIC_JSON_SCHEMA; PANDERA_DATAFRAMES_ONLY
P4_REJECTED_OR_DEFERRED_UPSTREAMS = TRANSITIONS_REJECT_OVERABSTRACTION; PYTHON_STATEMACHINE_REJECT_OVERABSTRACTION; AUTOMAT_REJECT_OVERABSTRACTION; RULE_ENGINE_REJECT_OVERABSTRACTION; OPA_REJECT_OVERWEIGHT; DURABLE_RULES_REJECT_OVERWEIGHT; PYTHON_JSONLOGIC_DEFER; CEL_PYTHON_REJECT_RUNTIME_INCOMPATIBLE; RIVER_DEFER_RUNTIME_INCOMPATIBLE_ALTERNATE; ALIBI_DETECT_REJECT_OVERWEIGHT_LICENSE; EVIDENTLY_REJECT_OVERWEIGHT; NANNYML_REJECT_SEMANTIC_MISMATCH; MENELAUS_REJECT_MAINTENANCE; DEEPCHECKS_REJECT_OVERWEIGHT_LICENSE; CLOUDEVENTS_DEFER_TO_P12; KSERVE_SELDON_ARGO_BENTOML_REJECT_SEMANTIC_MISMATCH
P4_RESIDUAL_AQ_SCOPE = DOMAIN_FACTS_AND_CONFIG; CONTRACT_SCHEMAS; BOUNDED_EVIDENCE_ADAPTER_AND_IDENTITY_PROJECTION; SMALL_PURE_FINANCIAL_AND_LIFECYCLE_PREDICATES
P4_FSM_UPSTREAM_DECISION = REJECT_OVERABSTRACTION
P4_POLICY_ENGINE_DECISION = REJECT_OVERABSTRACTION
P4_DRIFT_DETECTION_DECISION = POC_PASS_ADOPT_FROUROS_0_9_0_ADWIN_ISOLATED_RUNTIME
P4_SHADOW_UPSTREAM_DECISION = KEEP_EXISTING_QLIB_MLFLOW_DVC_PLUS_AQ_ADMISSION_CONTRACT
P4_RESEARCH_EVENT_DECISION = CLOUDEVENTS_DEFER_TO_P12
P4_SCHEMA_VALIDATION_DECISION = PYDANTIC_JSON_SCHEMA_RFC8785_WITH_PANDERA_FOR_DATAFRAMES_ONLY
P4_PERSISTENCE_DECISION = NO_NEW_AQ_STATE_DATABASE
P4_RESIDUAL_AUDIT_PRIVATE_REPORT_SHA256 = ce72d65b8b42c66fe4ece4891d814ce785d8f8fbce4a6a7500340b80c32fe117
P4_SELECTED_UPSTREAM_COMPONENTS_DEPLOYMENT = PASS
P4_FROUROS_VERSION = 0.9.0
P4_FROUROS_RUNTIME = ISOLATED_PYTHON_3_10_21
P4_FROUROS_ADWIN = DEPLOYED_UPSTREAM_LEAF
P4_FROUROS_RUNTIME_FREEZE_SHA256 = 8c66ad3fde0f116d89aa31c0454a093eba00b16fe6d5946ac973bd5850dfb5d5
P4_FROUROS_PACKAGE_INVENTORY_SHA256 = c079dfacf4481e34dcc163835b6b7538321e74b4ee6bc1715625dc817d72b9d9
P4_FROUROS_INSTALLED_ADWIN_MODULE_SHA256 = f3b2c06acf88b6938eac907909ca16b8daa382133eb1247e297a12f299ebd8fd
P4_FROUROS_OFFSET_INVARIANCE = PASS
P4_FROUROS_PRIOR_POC_REPLAY = PASS
P4_FROUROS_SOURCE_MODIFIED = NO
P4_FROUROS_SOURCE_COPIED = NO
P4_FROUROS_THIN_EVIDENCE_ADAPTER = PASS
P4_FROUROS_SUPPORTED_METRIC = RANK_IC_ONLY
P4_FROUROS_TRANSLATION = PLUS_1_CONSTANT_OFFSET
P4_FROUROS_DETECTOR_EVIDENCE = MATERIALIZED
P4_FROUROS_STATE_AUTHORITY = REPLAY_FROM_IMMUTABLE_OBSERVATIONS
P4_FROUROS_THIN_ADAPTER_PRIVATE_REPORT_SHA256 = 3d7d34141e7c5b2ffa9afab3e0e15b03d057ac4aaa457d432ba2287894774592
P4_AQ_FINANCIAL_DECAY_POLICY_CREATED = YES_THIN_PREREGISTERED_V2
P4_AQ_DRIFT_ENGINE = NO
P4_SELECTED_UPSTREAM_DEPLOYMENT_PRIVATE_REPORT_SHA256 = 0e5534ff3f17f203e4085fec44e3e598dad173ef3449a81f32d17f24c17a242d
P4_QLIB_MLFLOW_DVC_IDENTITY_PROJECTION_INTEGRATION = PASS
P4_REAL_QLIB_RECORDER_MECHANISM = PASS_SYNTHETIC_FIXTURE
P4_REAL_MLFLOW_RUN_MECHANISM = PASS_SYNTHETIC_FIXTURE
P4_DVC_IDENTITY_PROJECTION = PASS
P4_UPSTREAM_IDENTITY_PROJECTION_V1 = MATERIALIZED
P4_IDENTITY_PROJECTION_SHA256 = 8b7fdf79d5b5d5805cefdc94488bb0ba4b408331daa0578f86676b22585e5725
P4_IDENTITY_PROJECTION_DVC_STAGE = p4_frouros_identity_projection
P4_IDENTITY_PROJECTION_DVC_STAGE_LOCK_ENTRY_SHA256 = 9c8fd01b2cd3000c92fb04043ad16c70cb70d4acc3bb285a9614d4038fbcdfe9
P4_IDENTITY_PROJECTION_DVC_SEAL_SHA256 = 3397523b2d1e2fcd1e7d2ddde999855ef7252d1b6cac15fea8ebf45230c4c7ab
P4_IDENTITY_PROJECTION_PRIVATE_REPORT_SHA256 = 4e6468a8466783b9cacf6e5f383e7a85cecf510876dd1e5e8acc86287d2ac5dd
P4_FINANCIAL_DECAY_POLICY = PREREGISTERED_PRODUCTION_POLICY_V2
P4_LIFECYCLE_POLICY = MATERIALIZED
P4_UPSTREAM_COMPONENTS_INTEGRATION_AND_OWNERSHIP_REAUDIT = PASS_UPSTREAM_INTEGRATION_CLEAN
P4_UPSTREAM_STACK = QLIB_MLFLOW_DVC_FROUROS_INTEGRATED
P4_ADDITIONAL_UPSTREAM_DEPLOYMENT_REQUIRED = NO
P4_GENERIC_AQ_ENGINE_COUNT = 0
P4_RESIDUAL_AQ_SCOPE = EXPLICIT_AND_DOMAIN_SPECIFIC_ONLY
P4_UPSTREAM_OWNERSHIP_REAUDIT_PRIVATE_REPORT_SHA256 = abe2d366c672cea0b9235e6f6db87bbd88826e06af64eb0d3011d522b8661992
P4_RESIDUAL_THIN_POLICY_IMPLEMENTATION = PASS
P4_LIFECYCLE_STATE_COUNT = 6
P4_AUTHORIZED_TRANSITION_COUNT = 5
P4_CHALLENGER = ROLE_NOT_STATE
P4_SHADOW_CONTRACT = MATERIALIZED
P4_RESEARCH_REQUEST_V1 = MATERIALIZED
P4_FINANCIAL_DECAY_POLICY_STRUCTURE = MATERIALIZED
P4_PRODUCTION_DECAY_POLICY_STATUS = PREREGISTERED
P4_FINANCIAL_DECAY_POLICY_PREREGISTRATION = PASS
P4_PRODUCTION_DECAY_POLICY_VERSION = FinancialDecayPolicyConfigV2
P4_PRODUCTION_DECAY_POLICY_ID = sha256:3b95c4671bf75c933437659b971477ae6241f70428c638ae81690c4aa6182854
P4_PRODUCTION_DECAY_POLICY_SHA256 = 1cb73a05d9f36d8df66a8b044778d37f1812902ad8c2b3c1560b191955053c78
P4_PRODUCTION_DECAY_POLICY_EFFECTIVE_EPOCH = 2026-10-01
P4_PRODUCTION_DECAY_POLICY_METRIC = RANK_IC_ONLY
P4_REAL_DATA_USED_FOR_PREREGISTRATION = NO
P4_RETROACTIVE_THRESHOLD_REWRITE = PROHIBITED
P4_FINANCIAL_DECAY_PREREGISTRATION_PRIVATE_REPORT_SHA256 = c5d852de5873c87ae5fff68d29f3ad07da2d05be7a026e074506523545616f82
P4_REAL_CERTIFIED_ARTIFACT_COUNT = 0
P4_REAL_CHAMPION_COUNT = 0
P4_RESIDUAL_POLICY_RUNTIME_LOC = 646
P4_RESIDUAL_POLICY_PRIVATE_REPORT_SHA256 = 7d6d5282f781545f1181b2d59d6d153b7b2160a4837163cdab7e679358bf79ae
P4_SHADOW_EVIDENCE_PATH_AND_QLIB_ONLINE_INTEGRATION = PASS
P4_QLIB_ONLINE_MANAGER = INTEGRATED_UPSTREAM
P4_QLIB_ROLLING_STRATEGY = INTEGRATED_UPSTREAM
P4_QLIB_ONLINE_TOOL_R = INTEGRATED_UPSTREAM
P4_SHADOW_CONTRACT_VERSION = ShadowEvidenceV2
P4_SHADOW_MECHANISM = PASS_TEST_FIXTURE_ONLY
P4_REAL_SHADOW_EVIDENCE_COUNT = 0
P4_PRE_EPOCH_PRODUCTION_EVIDENCE = INELIGIBLE
P4_SHADOW_FIXTURE_SHA256 = 5f1eb7dd740e810d870bdd0850f2ee14f316fd5c9d120f20cd51707158dcc5fb
P4_SHADOW_DVC_STAGE = p4_shadow_evidence_path_fixture_seal
P4_SHADOW_DVC_SEAL_SHA256 = ea59eb9291bf9ea8fd729c10e90efd5f2bccbbd789e3d61a19ef50f0def8b6bc
P4_SHADOW_INTEGRATION_PRIVATE_REPORT_SHA256 = 19e3cd11612ff98da65e9660a6e74a99829bfc241ae1e8d02cc1ad25420cb073
P2_CERTIFICATION_PROTOCOL_V1 = IMMUTABLE_ACTIVE_EXISTING_COHORT
P2_CERTIFICATION_PROTOCOL_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
P2_CERTIFICATION_PROTOCOL_V2_SHA256 = 18b80277b6529422298e43681bb344e54199a58477cdba20d96fd8220bdc950a
P2_FORMULAIC_ALPHA_V2_COHORT_COUNT = 17
P2_FORMULAIC_ALPHA_V2_COHORT_SHA256 = 53920302856592fb43bbffb011423731893ac0a995a04194541c39d69ecfde70
P2_FORMULAIC_ALPHA_CURRENT_ELIGIBILITY = ELIGIBLE_UNDER_P2_CERTIFICATION_PROTOCOL_V2
P2_FORMULAIC_ALPHA_HISTORICAL_TEST = CONSUMED_AS_RESEARCH_EVIDENCE
P2_FORMULAIC_ALPHA_V2_SEALED_OOS_START = 2026-09-18
P2_FORMULAIC_ALPHA_V2_MINIMUM_OOS_SESSIONS = 126
P2_FORMULAIC_ALPHA_V2_DVC_STAGE = p2_formulaic_alpha_protocol_v2_freeze
P2_FORMULAIC_ALPHA_V2_DVC_SEAL_SHA256 = 135b7728ce73875a353ba7ddf833b3bc166420b2b15ddf571214a4cb4118cd98
P2_FORMULAIC_ALPHA_V2_PRIVATE_REPORT_SHA256 = 1694ec0360f610be0e7d37cfdadbc273618a94c059743ef4f788ab08f6a1ad94
P2_FORMULAIC_ALPHA_V2_BRANCH_FREEZE_HEAD = 6c7f7cd7449a6d421489f9c90eea44490e608aad
P2_FORMULAIC_ALPHA_V2_BRANCH_FREEZE_HEAD_MUST_BE_MAIN_ANCESTOR = NO
P2_FORMULAIC_ALPHA_V2_MERGE_ANCHOR_SEMANTICS = V1_CONSISTENT_MAIN_COMMIT_CONTAINING_EXACT_FROZEN_BYTES
P2_FORMULAIC_ALPHA_V2_ALLOWED_MERGE_METHOD = SQUASH_MERGE
P2_FORMULAIC_ALPHA_V2_ACTIVATION_ANCHOR = POST_MERGE_ORIGIN_MAIN_COMMIT_AFTER_EXACT_BYTE_VERIFICATION
P2_FORMULAIC_ALPHA_V2_PRIOR_EXACT_ANCESTRY_INTERPRETATION = SUPERSEDED_BY_V1_PRECEDENT
P2_FORMULAIC_ALPHA_V2_REPOSITORY_MERGE_POLICY_CHANGE_REQUIRED = NO
P2_FORMULAIC_ALPHA_V2_PROTOCOL_BYTES_MODIFIED_BY_CORRECTION = NO
P2_FORMULAIC_ALPHA_V2_COHORT_BYTES_MODIFIED_BY_CORRECTION = NO
P2_CERTIFICATION_PROTOCOL_V2_ACTIVATION = COMPLETE
P2_FORMULAIC_ALPHA_V2_FREEZE_MERGE_SHA = 9f97c1dc9fd419cadb5bb5a9a304505a5d87411b
P2_FORMULAIC_ALPHA_V2_FREEZE_MERGED_AT_UTC = 2026-09-18T07:50:31Z
P2_FORMULAIC_ALPHA_V2_ACTIVATION_SHA256 = ff3356850e2a6799c1a8827c0c9aa93e1b54e991d54bca10329471f40abcf9ae
P2_FORMULAIC_ALPHA_V2_PRE_ACTIVATION_SESSIONS_COUNT = 0
P2_FORMULAIC_ALPHA_V2_EARLY_RESULT_ACCESS = PROHIBITED
P2_FORMULAIC_ALPHA_V2_ONE_SHOT_RELEASE = YES
P2_FORMULAIC_ALPHA_V2_CERTIFIED_CANDIDATE_COUNT = 0
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
ACTIVE_DEVELOPMENT_PHASE = P5_FUNDAMENTAL_INTELLIGENCE
P5_FUNDAMENTAL_INTELLIGENCE = ENTRY_ACTIVE
P5_UPSTREAM_STACK_SELECTED = SEC_EDGAR_AUTHORITATIVE_SOURCE; EDGARTOOLS_PIT_CRITICAL_FILING_XBRL_STATEMENT_SKILL; OPENBB_SUPPLEMENTARY_NON_AUTHORITATIVE
P5_OPENBB_PIT_MODE = PARTIAL
P5_RESTATEMENT_POLICY = FAIL_CLOSED_AND_EXPLICIT
P5_LIVE_SEC_POC = HISTORICAL_SUPERSEDED_BLOCKED_IDENTITY_NOT_CONFIGURED
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_UPSTREAM_SKILLS_AUDIT_PRIVATE_REPORT_SHA256 = 689e412d758d76b6253239e2a1d5e7e5a3cfb962977262e9f30512bde52067db
P5_SELECTED_UPSTREAM_DEPLOYMENT = PASS
P5_RUNTIME = ISOLATED
P5_OPENBB_SEC = DEPLOYED_SUPPLEMENTARY_NON_AUTHORITATIVE
P5_EDGARTOOLS = DEPLOYED
P5_EDGARTOOLS_SKILL = PRIVATE_UPSTREAM_EXPORT_DEPLOYED
P5_SEC_LIVE_IDENTITY = CONFIGURED_LOCAL_PRIVATE
P5_AQ_GENERIC_ENGINE_COUNT = 0
P5_SELECTED_UPSTREAM_DEPLOYMENT_PRIVATE_REPORT_SHA256 = 04bdf3b384f04a6cae991f53c988b0c774207397c0d5c48b23c8d507099cc8b8
P5_SEC_LIVE_POC = BOUNDED_PARTIAL_OPENBB_SAFE_LIVE_BOUNDARY_BLOCKED
P5_EDGARTOOLS_LIVE_SEC = PASS
P5_EDGARTOOLS_SKILL_LIVE_ROUTING = PASS
P5_OPENBB_SEC_LIVE = BLOCKED_UPSTREAM_SAFE_IDENTITY_AND_HISTORICAL_SCOPE
P5_THREE_WAY_PIT_BINDING = RETIRED_NOT_REQUIRED
P5_AQ_THIN_BINDER_REQUIRED = NO_OR_MINIMAL_EVIDENCE_CONTRACT_ONLY
P5_SEC_LIVE_POC_PRIVATE_REPORT_SHA256 = c15db43defa31dc1194eed0fe4afae4d26c9d4803e8f138069ceef28bbad7fae
P5_PIT_CRITICAL_STACK = SEC_EDGAR_PLUS_EDGARTOOLS
P5_OPENBB_SEC_ROLE = SUPPLEMENTARY_NON_AUTHORITATIVE
P5_PRIOR_OPENBB_PIT_SELECTION = SUPERSEDED_BY_LIVE_POC
P5_FUNDAMENTAL_EVIDENCE_CONTRACT_V1 = MATERIALIZED
P5_FIRST_AVAILABLE_AT_AUTHORITY = SEC_ACCEPTANCE_DATETIME
P5_OPENBB_ONLY_EVIDENCE_ADMISSION = REJECT
P5_FUNDAMENTAL_EVIDENCE_CONTRACT_PRIVATE_REPORT_SHA256 = 3603ae04d87ed92a32875a3aa2a6dfdb49423b4c8f33ccc99189af6f2ed72d0d
P5_BRAIN_STALE_IDENTITY_BLOCKER = RESOLVED
P5_FUNDAMENTAL_EVIDENCE_MATERIALIZATION_POC = PASS
P5_REAL_FUNDAMENTAL_EVIDENCE = MATERIALIZED_HISTORICAL_SAFE_POC
P5_OPENBB_AUTHORITATIVE_RECORD_COUNT = 0
P5_AQ_THIN_EVIDENCE_MATERIALIZER = YES
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_FUNDAMENTAL_EVIDENCE_MATERIALIZATION_PRIVATE_REPORT_SHA256 = b28925f898594b8465bc7d97ea1c19d62c1cad59f208662cd84f1d1bf56ecd88
P5_EPISODE_TO_SEC_CIK_BINDING = PARTIAL_TRACTABLE_FAIL_CLOSED
P5_EPISODE_TO_SEC_CIK_SAMPLE_COUNT = 8
P5_EPISODE_TO_SEC_CIK_PASS_COUNT = 6
P5_EPISODE_TO_SEC_CIK_AMBIGUOUS_COUNT = 1
P5_EPISODE_TO_SEC_CIK_MISSING_AUTHORITY_COUNT = 1
P5_CURRENT_TICKER_MAPPING_USED_AS_SOLE_AUTHORITY = NO
P5_EPISODE_SEC_CIK_BINDING_CONTRACT_IMPLEMENTED = NO
P5_AQ_SECURITY_MASTER = NO
P5_AQ_GENERIC_IDENTITY_ENGINE = NO
P5_EPISODE_TO_SEC_CIK_BINDING_PRIVATE_REPORT_SHA256 = aa4eb177174fb42419e2e407458baf4aab1f6b7e3413347ea364b23316380945
CURRENT_DEVELOPMENT_NEXT = P5_FUNDAMENTAL_HISTORICAL_DATASET_DESIGN_001
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
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
