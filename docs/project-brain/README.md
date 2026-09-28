# AUTONOMOUS_QUANT — Project Brain

> Status: **PLANNING / NO PRODUCTION TRADING**
>
> Current Next: **P2 — Formulaic Alpha Sealed OOS Accumulation 001**
>
> Active Development: **P3 — RD-Agent native handoff thin Candidate projection POC**
>
> P5 V1 scope: **complete; Attempt 005 found no measurable incremental value from the exact ten PIT fundamentals under the frozen H1 protocol.**
>
> Development Next: **P3 — RD-Agent fin_quant autonomous loop reactivation**
>
> Core Principle: **Upstream-first; thin interfaces; fail-closed gaps; one production owner per capability.** See the [Upstream Ownership Model](upstream-ownership-model.md).

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
4. Governance is upstream-first: use thin interfaces, fail closed on gaps,
   and keep one production owner per capability.
5. A leaf can be replaced without forcing unrelated siblings to change.
6. Research code and production trading code must remain separated.
7. Production may consume only **certified artifacts**, never raw experimental output.
8. **No AQ engine without upstream rejection evidence.** That evidence is
   necessary, not sufficient: custom code still requires genuinely AQ-specific
   scope or separate explicit authorization.

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
  and policy boundaries.
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

The four operating rules and simplified future-task ownership preamble are
defined in [Upstream Ownership Model](upstream-ownership-model.md). A task that
skips that ownership check is architecturally invalid.

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
P5_FUNDAMENTAL_INTELLIGENCE = FOUNDATION_DESIGN_COMPLETE
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
P5_EPISODE_SEC_CIK_BINDING_CONTRACT_IMPLEMENTED = YES
P5_EPISODE_SEC_CIK_BINDING_CONTRACT = MATERIALIZED
P5_EPISODE_SEC_CIK_BINDING_CONTRACT_VERSION = EpisodeSecCikBindingV1
P5_EPISODE_SEC_CIK_BINDING_ADMITTED_CLASSIFICATIONS = PASS_EXACT; PASS_CORROBORATED
P5_IMPLICIT_P1_P2_EPISODE_CROSSWALK = PROHIBITED
P5_AQ_SECURITY_MASTER = NO
P5_AQ_GENERIC_IDENTITY_ENGINE = NO
P5_EPISODE_TO_SEC_CIK_BINDING_PRIVATE_REPORT_SHA256 = aa4eb177174fb42419e2e407458baf4aab1f6b7e3413347ea364b23316380945
P5_FUNDAMENTAL_HISTORICAL_DATASET_DESIGN = PASS
P5_EPISODE_SEC_CIK_BINDING_CONTRACT_DECISION = MATERIALIZED
P5_UNRESOLVED_IDENTITY_POLICY = FAIL_CLOSED
P5_NO_SURVIVORSHIP_LEAK_DESIGN = PASS
P5_FILING_UNIVERSE = 10-K; 10-Q; 10-K/A; 10-Q/A
P5_EIGHT_K_ROLE = PRELIMINARY_OR_EVENT_EVIDENCE
P5_EDGARTOOLS_STANDARDIZATION_FIT = PARTIAL
P5_FUNDAMENTAL_EFFECTIVE_SESSION_POLICY = FIRST_XNYS_SESSION_WITH_OPEN_STRICTLY_AFTER_FIRST_AVAILABLE_AT
P5_ASOF_PROJECTION_OWNER = pandas.merge_asof
P5_HISTORICAL_STORAGE_FORMAT = PARTITIONED_PARQUET_PLUS_MANIFEST_PLUS_DVC
P5_SOURCE_RETENTION_POLICY = BOUNDED_HYBRID_FAIL_CLOSED
P5_FULL_SEC_MIRROR = NO
P5_QLIB_FUNDAMENTAL_HANDOFF = StaticDataLoader_TO_DataHandlerLP_TO_DatasetH
P5_PRETRAIN_EVIDENCE_LOOKBACK_POLICY = DEPENDENT_ON_FROZEN_FACTOR_INPUT_SEMANTICS
P5_FUNDAMENTAL_DATASET_SNAPSHOT_V1 = NOT_REQUIRED
P5_FUNDAMENTAL_HISTORICAL_DATASET_BUILT = NO
P5_FUNDAMENTAL_HISTORICAL_DATASET_DESIGN_PRIVATE_REPORT_SHA256 = 1d7ddf23f2351ec5fe2f949005382d2b1a2bf3973695dcf70398d030286a7755
P5_EPISODE_SEC_CIK_BINDING_CONTRACT_PRIVATE_REPORT_SHA256 = 335062fcb20476c5d5390701b9e7dc42e1ef1d10ee4106a142b464e5b50978be
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_FOUNDATION = MERGED
P5_FOUNDATION_CLOSEOUT = PASS
P5_FOUNDATION_MERGE_PR = 50
P5_FOUNDATION_MERGE_SHA = 12729c7267667a57f9bc26b1781ec3927b66e0f0
P5_FOUNDATION_MERGED_AT_UTC = 2026-09-18T22:44:42Z
P5_FOUNDATION_SOURCE_BRANCH = MERGED_RETIRED
P5_DATASET_BUILD_PILOT_GATE = OPEN
P5_FULL_PHASE_COMPLETE = NO
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P5_FOUNDATION_CLOSEOUT_PRIVATE_REPORT_SHA256 = d3c3e8a58fc18cdb33e12995604aa41e28738f344f9e0d0e5b2f2dfa7441995f
P5_SEC_FSDS_SECFSDSTOOLS_UPSTREAM_SUBSTITUTION_AUDIT = PASS
P5_SEC_FSDS_PIT_FIT = PARTIAL
P5_FSDS_ACCEPTANCE_DATETIME_AUTHORITY = PARTIAL
P5_FSDS_AMENDMENT_VINTAGE = PASS
P5_SECFSDSTOOLS_BULK_INGEST_FIT = PARTIAL
P5_FUNDAMENTAL_EVIDENCE_V1_FSDS_COMPATIBILITY = NO
P5_SEC_FSDS_ARCHITECTURE_DECISION = HYBRID_WITH_EXACT_BOUNDARIES
P5_DATASET_BUILD_PILOT_STATUS = OPEN_HYBRID_PATH
P5_SEC_FSDS_SECFSDSTOOLS_AUDIT_PRIVATE_REPORT_SHA256 = 202f5b822a091a4e879d62427f09c74b128d87c7abb71ed2d8920eac1033db74
P5_SEC_FSDS_SECFSDSTOOLS_DEPLOYMENT_POC = PASS
P5_BULK_CANDIDATE_CATALOG = SECFSDSTOOLS
P5_EXACT_EVIDENCE_ADMISSION = EDGARTOOLS
P5_FSDS_ACCEPTANCE_ROLE = DISCOVERY_ONLY
P5_FSDS_NUMERIC_VALUE_ROLE = DISCOVERY_DIAGNOSTIC_ONLY
P5_SECFSDSTOOLS_STANDARDIZER_ROLE = NON_AUTHORITATIVE
P5_SEC_FSDS_SECFSDSTOOLS_DEPLOYMENT_POC_PRIVATE_REPORT_SHA256 = 97ee6c70b8be9a20a3295993c96a199743f3d441baa33d96c62717cf6cc0c8cf
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_HYBRID_HISTORICAL_DATASET_BUILD_PILOT = PASS
P5_PILOT_INPUT_CASE_COUNT = 8
P5_PILOT_ADMITTED_EPISODE_COUNT = 6
P5_PILOT_NEGATIVE_IDENTITY_EXCLUSIONS = 2
P5_PILOT_FSDS_QUARTER_COUNT = 35
P5_PILOT_EXACT_ACCESSION_COUNT = 14
P5_PILOT_FUNDAMENTAL_EVIDENCE_COUNT = 96
P5_PILOT_STANDARDIZED_EVENT_COUNT = 96
P5_PILOT_SESSION_PROJECTION_ROW_COUNT = 51120
P5_PILOT_EARLY_VISIBILITY_COUNT = 0
P5_PILOT_CROSS_CIK_CONTAMINATION_COUNT = 0
P5_PILOT_UNTRACEABLE_PROJECTED_VALUE_COUNT = 0
P5_PILOT_DVC_SEAL = PASS
P5_PILOT_QLIB_HANDOFF = PASS
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_UPSTREAM_DEPLOYMENT_SUBSTITUTION_AND_AQ_RETIREMENT_AUDIT = PASS
P5_VALUEIN_HISTORICAL_IDENTITY_LAYER = MATERIAL_PARTIAL_REPLACEMENT_ONLY
P5_VALUEIN_SOLE_EPISODE_CIK_AUTHORITY = NO
P5_VALUEIN_832_EXACT_INTERVAL_MATCH_COUNT = 1
P5_VALUEIN_832_COMPATIBLE_INTERVAL_MATCH_COUNT = 710
P5_VALUEIN_832_PARTIAL_INTERVAL_MATCH_COUNT = 41
P5_VALUEIN_832_AMBIGUOUS_MATCH_COUNT = 3
P5_VALUEIN_832_NO_MATCH_COUNT = 77
P5_VALUEIN_832_CIK_AVAILABLE_COUNT = 755
P5_VALUEIN_832_MEMBERSHIP_AVAILABLE_COUNT = 755
P5_VALUEIN_PILOT_ACCESSION_MATCH = 10_OF_14
P5_VALUEIN_FUNDAMENTALS_ROLE = SUPPLEMENTARY_ORACLE_ONLY
P5_VALUEIN_THIN_IDENTITY_ADAPTER = PASS
P5_VALUEIN_IDENTITY_ROLE = EXACT_ONLY_EXTERNAL_EVIDENCE_LEAF
P5_VALUEIN_THIN_FUNDAMENTALS_ADAPTER = NOT_ADOPTED_MISSING_IMMUTABLE_PROVENANCE
P5_VALUEIN_FUNDAMENTALS_PRODUCTION_ROLE = NONE
P5_VALUEIN_FUNDAMENTALS_ORACLE_ROLE = YES
P5_FUNDAMENTAL_EVIDENCE_V1_VALUEIN_EXPANSION = REVERTED
P5_FUNDAMENTAL_EVIDENCE_V1_VALUEIN_PROVIDER_ADMISSION = NO
P5_EDGARTOOLS_EXACT_FUNDAMENTALS_AUTHORITY = PRESERVED
P5_SECFSDSTOOLS_BULK_CANDIDATE_CATALOG = YES
P5_VALUEIN_GAP_REPAIR_WORK = STOP
P5_VALUEIN_ADMITTED_BINDING_COUNT = 1
P5_VALUEIN_UNRESOLVED_IDENTITY_COUNT = 831
P5_VALUEIN_CONTRACT_ADMITTED_ACCESSION_COUNT = 0
P5_VALUEIN_EDGARTOOLS_REGRESSION_RESULT = EXPLICIT_BLOCKER_MISSING_IMMUTABLE_PROVENANCE_AND_ACCEPTANCE_TIME_DISAGREEMENT
P5_EDGARTOOLS_FALLBACK_ACCESSION_COUNT = 14
P5_VALUEIN_11_METRIC_MAPPING = ORACLE_EVIDENCE_ONLY
P5_AQ_REDUNDANT_COMPONENTS_RETIRED = aq_hybrid_fundamentals.write_exact_event_parquet; aq_hybrid_fundamentals.canonical_sha256; aq_hybrid_fundamentals.artifact_identity
P5_VALUEIN_SCOPE_CONTRACTION_PRIVATE_CHECKSUM_LEDGER_SHA256 = 0f87041631688c4810b638008d0bb91f9e0d0ce895ebf535aab5126a6631d171
P5_RFUNDAMENTALS_ROLE = ORACLE_ONLY
P5_ARELLE_ROLE = EDGARTOOLS_PRIMARY_ARELLE_FALLBACK
P5_ALPHALENS_ROLE = NON_DUPLICATIVE_LEAF
P5_PURGEDCV_ROLE = PSR_DSR_CANDIDATE_LEAF_CV_DUPLICATE_NOT_ADOPTED
P5_AQ_DUPLICATE_PRODUCTION_OWNER_COUNT = 0
P5_UPSTREAM_SUBSTITUTION_PRIVATE_EVIDENCE_ROOT = D:\AQ_DATA\P5\upstream-deployment-substitution-and-aq-retirement-audit-001
P5_UPSTREAM_SUBSTITUTION_CAPABILITY_MATRIX_SHA256 = 31418830ffbc27c1e3f59d8d802939be4ef836ef63500411ca2464fe8a916c2e
P5_UPSTREAM_SUBSTITUTION_RETIREMENT_MATRIX_SHA256 = 5f38430e35dda099fb7c5b63d4297637f9e235bf38cb39fb16a452be7fd7ed93
P5_UPSTREAM_SUBSTITUTION_THIN_ADAPTER_PLAN_SHA256 = 37ebeb1db288cedc194ddbba049175af7baa4e42edbb1a29f0978dc64722cec8
SELECTED_UPSTREAM_RUNTIME_CONSOLIDATION_WAVE = PASS
SELECTED_UPSTREAM_INVENTORY_COMPLETE = YES
SELECTED_UPSTREAM_RUNTIME_COVERAGE = ALL_DEPLOYED_OR_EXPLICIT_BLOCKER
VALUEIN_RUNTIME_READY = YES
EDGARTOOLS_RUNTIME_READY = YES
SECFSDSTOOLS_RUNTIME_READY = YES
OPENBB_RUNTIME_READY = YES
ARELLE_FALLBACK_RUNTIME_READY = YES
ALPHALENS_LEAF_RUNTIME_READY = YES
PURGEDCV_CANDIDATE_RUNTIME_READY = YES
RFUNDAMENTALS_RUNTIME_STATUS = RUNTIME_READY_ORACLE_ONLY
SECFSDSTOOLS_AUTOUPDATE_DEFAULT_TRUSTED = NO
SECFSDSTOOLS_REQUIRED_RUNTIME_POLICY = EXPLICIT_AUTOUPDATE_FALSE_UNLESS_SEPARATELY_AUTHORIZED
VALUEIN_COMPATIBLE_MATCH_AUTO_ADMISSION = PROHIBITED
VALUEIN_PARTIAL_MATCH_AUTO_ADMISSION = PROHIBITED
VALUEIN_AMBIGUOUS_MATCH_AUTO_ADMISSION = PROHIBITED
VALUEIN_NO_MATCH_BACKFILL = PROHIBITED
VALUEIN_TICKER_ONLY_BACKFILL = PROHIBITED
AQ_SECURITY_MASTER = NO
AQ_PROVIDER_FRAMEWORK = NO
AQ_GENERIC_ADAPTER_FRAMEWORK = NO
AQ_IDENTITY_ENGINE = NO
AQ_FUNDAMENTAL_ENGINE = NO
AQ_DUPLICATE_PRODUCTION_OWNER_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_HYBRID_HISTORICAL_DATASET_BUILD_PILOT_PRIVATE_REPORT_SHA256 = 333dcbaa72815880de1d29ad9280e7f070d3bb0b889bc4abfe5c3b753a212649
P5_HYBRID_DATASET_PILOT_CLOSEOUT = BLOCKED_SEMANTIC_POLICY
P5_HYBRID_MECHANISM_READINESS = PASS
P5_PILOT_MERGE_READY = PENDING_REVALIDATION
P5_FULL_UNIVERSE_IDENTITY_ACCOUNTING_COMPLETE = NO
P5_FULL_BUILD_GATE = CLOSED_IDENTITY_ACCOUNTING_REQUIRED
P5_SESSION_PROJECTION_POLICY_AUDIT = PASS_PERIOD_CLASS_ISOLATED
P5_METRIC_COVERAGE_CLASSIFICATION = CORRECTED_EDGARTOOLS_STANDARD_CONCEPT_ID
P5_DIMENSION_PATH_EXERCISED = YES
P5_FULL_BUILD_ACCESSION_CENSUS_REQUIRED = YES
P5_PRETRAIN_EVIDENCE_LOOKBACK_POLICY = SAME_CIK_HISTORY_ONLY_TO_EXTENT_HISTORICALLY_EXISTS; NONEXISTENT_HISTORY_REMAINS_MISSING; NO_PREDECESSOR_SUBSTITUTION
P5_PRE_MEMBERSHIP_SAME_CIK_EVIDENCE_POLICY = LATER_ELIGIBLE_SESSION_ONLY_WITH_EXACT_SAME_CIK_BINDING_AND_REQUIRED_PIT_MEMBERSHIP
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_HYBRID_DATASET_PILOT_CLOSEOUT_PRIVATE_REPORT_SHA256 = 87c67888baa5fe2a6ff807840fa5258d73e504a76e72a644b3716fa612341351
P5_HYBRID_DATASET_SEMANTIC_POLICY_CORRECTION = PASS
P5_METRIC_IDENTITY_AUTHORITY = EDGARTOOLS_STANDARD_CONCEPT_ID
P5_PERIOD_SEMANTIC_POLICY = MATERIALIZED
P5_DIMENSION_POLICY = CONSOLIDATED_ONLY
P5_PRETRAIN_LOOKBACK_POLICY = CORRECTED
P5_HYBRID_DATASET_SEMANTIC_POLICY_CORRECTION_PRIVATE_REPORT_SHA256 = a1fb9a66c78b090fc2c3fe494f69c3a757bf4134bd175602377db90577b9c122
P5_HYBRID_DATASET_PILOT_REVALIDATION = PASS
P5_HYBRID_DATASET_PILOT_MERGE_READY = YES
P5_HYBRID_DATASET_PILOT_MERGED = YES
P5_HYBRID_DATASET_PILOT_MERGE_PR = 53
P5_HYBRID_DATASET_PILOT_MERGE_SHA = 5fb34f88a68d109be4486a8dab6cbe05fac52af0
P5_HYBRID_DATASET_PILOT_FINAL_CLASSIFICATION = PASS_MERGED_REVALIDATED_PILOT
P5_FULL_UNIVERSE_IDENTITY_ACCOUNTING_COMPLETE = NO
P5_FULL_BUILD_GATE = CLOSED_IDENTITY_ACCOUNTING_REQUIRED
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_RESIDUAL_HISTORICAL_IDENTITY_ALTERNATE_UPSTREAM_AUDIT_BRANCH = SUPERSEDED_DIAGNOSTIC_EVIDENCE_ONLY
P5_RESIDUAL_HISTORICAL_IDENTITY_ALTERNATE_UPSTREAM_AUDIT_MERGED = NO
P5_MASSIVE_PIT_IDENTITY_SEMANTIC_REALIGNMENT = PASS
P5_PRIOR_EXACT_INTERVAL_EQUALITY_RULE = SUPERSEDED_WITH_EVIDENCE
P5_P1_MEMBERSHIP_EPISODE_SEPARATED_FROM_SECURITY_LIFETIME = YES
P5_EPISODE_SEC_CIK_BINDING_V1_CHANGED = NO
P5_VALUEIN_COMPATIBLE_REJECTION_EXACT_EQUALITY_ONLY_COUNT = 710
P5_VALUEIN_COMPATIBLE_REMAINING_CONFLICT_COUNT = 0
P5_VALUEIN_COMPATIBLE_REMAINING_AMBIGUOUS_COUNT = 0
P5_VALUEIN_COMPATIBLE_MISSING_REQUIRED_EVIDENCE_COUNT = 0
P5_MASSIVE_SDK = DEPLOYED_OFFICIAL_2_8_0_ISOLATED
P5_MASSIVE_POINT_IN_TIME_POC = ACCESS_TIER_BLOCKED
P5_MASSIVE_FULL_P1_EPISODE_COUNT = 832
P5_MASSIVE_FULL_P1_ACCESS_BLOCKED_COUNT = 832
P5_MASSIVE_FUNDAMENTALS_AUTHORITY = NO
P5_EDGARTOOLS_EXACT_FUNDAMENTALS_AUTHORITY = YES
P5_MASSIVE_SEMANTIC_POC_PRIVATE_CHECKSUM_LEDGER_SHA256 = cdae0cff6a1243f4ccc0f12afe94cfb9e3aee10b447f397363cb83b2fed14fc0
P5_AQ_MANUAL_IDENTITY_RULE_COUNT = 0
P5_AQ_SECURITY_MASTER_CREATED = NO
P5_AQ_GENERIC_IDENTITY_ENGINE_CREATED = NO
P5_AUDIT_PRODUCTION_LOC_ADDED = 0
P5_VALUEIN_NATIVE_PIT_WHOLE_PATH_REVALIDATION = PASS
P5_VALUEIN_ACCESS_TIER = FREE_BENCHMARK_SP500
P5_VALUEIN_NATIVE_FULL_832_REPLAY = PASS
P5_VALUEIN_NATIVE_EXACT_AGREEMENT_COUNT = 1
P5_VALUEIN_NATIVE_CONTAINING_AGREEMENT_COUNT = 708
P5_VALUEIN_NATIVE_PARTIAL_AGREEMENT_COUNT = 1
P5_VALUEIN_NATIVE_MEMBERSHIP_BOUNDARY_DIFFERENCE_COUNT = 0
P5_VALUEIN_NATIVE_TICKER_BOUNDARY_DIFFERENCE_COUNT = 41
P5_VALUEIN_NATIVE_AMBIGUOUS_COUNT = 0
P5_VALUEIN_NATIVE_CONFLICT_COUNT = 2
P5_VALUEIN_NATIVE_NO_COVERAGE_COUNT = 79
P5_VALUEIN_NATIVE_PROJECTABLE_BINDING_COUNT = 709
P5_VALUEIN_NATIVE_UNRESOLVED_COUNT = 123
P5_VALUEIN_PRIOR_831_RESIDUAL_RESOLVED_COUNT = 708
P5_VALUEIN_HISTORICAL_SECURITY_IDENTITY_OWNER = PARTIAL
P5_VALUEIN_SP500_MEMBERSHIP_ROLE = ORACLE_ONLY
P5_VALUEIN_EXACT_ONLY_ADAPTER_ROLE = REWRITE_THIN_PROJECTION_ONLY
P5_VALUEIN_FUNDAMENTALS_PRODUCTION_ROLE = NONE
P5_EDGARTOOLS_EXACT_FUNDAMENTALS_AUTHORITY = YES
P5_VALUEIN_NATIVE_REVALIDATION_PRIVATE_CHECKSUM_LEDGER_SHA256 = 1ac91680183225ce04711b72e4861c8e3cb05aa4ee604ad338b7289e325a87d4
P5_VALUEIN_NATIVE_IDENTITY_PROJECTION = PASS
P5_VALUEIN_NATIVE_BINDING_COUNT = 709
P5_VALUEIN_UNRESOLVED_COUNT = 123
P5_VALUEIN_PASS_EXACT_COUNT = 1
P5_VALUEIN_PASS_CORROBORATED_COUNT = 708
P5_VALUEIN_SP500_MEMBERSHIP_SOURCE = INDEX_MEMBERSHIP_INDEX_NAME_SP500_ONLY
P5_VALUEIN_SP500_MEMBERSHIP_HARD_GATE = PASS
P5_VALUEIN_RUSSELL_CONTAMINATION_COUNT = 0
P5_VALUEIN_FUND_HOLDINGS_CONTAMINATION_COUNT = 0
P5_VALUEIN_LEGACY_EXACT_ONLY_PATH = RETIRED
P5_VALUEIN_DUPLICATE_PRODUCTION_PATH_COUNT = 0
P5_VALUEIN_NATIVE_PROJECTION_PRIVATE_CHECKSUM_LEDGER_SHA256 = b0c3cb1d58fa50838c368c4678bd82e3735d9e977ca1e49483fff97d48f3d239
P5_VALUEIN_NATIVE_RESIDUAL_123_FREE_UPSTREAM_AUDIT = PASS
P5_VALUEIN_NATIVE_RESIDUAL_TOTAL = 123
P5_VALUEIN_NATIVE_RESIDUAL_PROJECTABLE_COUNT = 12
P5_VALUEIN_NATIVE_RESIDUAL_STILL_UNRESOLVED_COUNT = 111
P5_VALUEIN_NATIVE_TICKER_BOUNDARY_PROJECTABLE_COUNT = 9
P5_VALUEIN_NATIVE_NO_COVERAGE_PROJECTABLE_COUNT = 2
P5_VALUEIN_NATIVE_CONFLICT_RESOLVED_COUNT = 0
P5_VALUEIN_NATIVE_PARTIAL_RESOLVED_COUNT = 1
P5_VALUEIN_NATIVE_QUANT_LODGE_MATCH_COUNT = 13
P5_VALUEIN_NATIVE_SEC_EDGAR_CORROBORATED_COUNT = 2
P5_VALUEIN_NATIVE_RENAME_CORROBORATED_COUNT = 0
P5_VALUEIN_NATIVE_TOTAL_PROJECTABLE_AFTER_AUDIT = 721
P5_VALUEIN_NATIVE_TOTAL_UNRESOLVED_AFTER_AUDIT = 111
P5_VALUEIN_NATIVE_RESIDUAL_PRIVATE_CHECKSUM_LEDGER_SHA256 = 508d560b61915726de49beef36ca4d430eaf478a2da44e93c7687e4abf604d45
P5_VALUEIN_NATIVE_RESIDUAL_OFFLINE_REPLAY = PASS
P5_PAID_DATA_DEPENDENCY_COUNT = 0
P5_IDENTITY_ACCOUNTING_FINAL_CLOSEOUT = PASS
P5_RESIDUAL_AUDIT_MERGE_PR = 61
P5_RESIDUAL_AUDIT_MERGE_SHA = 5fb3a48b884753e155ff10b5711b0783e0d9754f
P5_EXISTING_709_BINDINGS_PRESERVED = YES
P5_COMMON_IDENTITY_PATH = VALUEIN_NATIVE_THIN_PROJECTION
P5_RESIDUAL_ADJUDICATION_STORAGE = IMMUTABLE_SUPPLEMENTAL_BINDING_LEDGER
P5_UNRESOLVED_STORAGE = IMMUTABLE_EXCLUSION_LEDGER
P5_VALUEIN_RESIDUAL_RUNTIME_ENGINE = NONE
P5_COMMON_VALUEIN_BOUND_EPISODES = 709
P5_SUPPLEMENTAL_BOUND_EPISODES = 12
P5_SUPPLEMENTAL_BINDING_RECORDS = 13
P5_NEW_RESIDUAL_BOUND_EPISODE_COUNT = 12
P5_FINAL_BOUND_EPISODE_COUNT = 721
P5_FINAL_BINDING_RECORD_COUNT = 722
P5_PASS_EXACT_TOTAL = 2
P5_PASS_CORROBORATED_TOTAL = 720
P5_INSUFFICIENT_EVIDENCE_EXCLUSION_COUNT = 33
P5_NO_FREE_UPSTREAM_COVERAGE_EXCLUSION_COUNT = 76
P5_CONFLICT_REMAINS_FAIL_CLOSED_EXCLUSION_COUNT = 2
P5_FINAL_EXCLUSION_EPISODE_COUNT = 111
P5_TOTAL_P1_EPISODES = 832
P5_UNACCOUNTED_EPISODE_COUNT = 0
P5_DUPLICATE_ACCOUNTING_COUNT = 0
P5_EPISODE_IN_BOTH_BINDING_AND_EXCLUSION_COUNT = 0
P5_FULL_UNIVERSE_IDENTITY_ACCOUNTING_COMPLETE = YES
P5_FULL_UNIVERSE_BOUND_EPISODE_COUNT = 721
P5_FULL_UNIVERSE_EXCLUSION_EPISODE_COUNT = 111
P5_FULL_UNIVERSE_UNACCOUNTED_EPISODE_COUNT = 0
P5_UNBOUND_EPISODE_REMOVED_FROM_UNIVERSE = NO
P5_UNBOUND_EPISODE_REMOVED_FROM_DENOMINATOR = NO
P5_UNBOUND_EPISODE_PREDECESSOR_CIK_SUBSTITUTION = NO
P5_UNBOUND_EPISODE_SUCCESSOR_CIK_SUBSTITUTION = NO
P5_UNBOUND_EPISODE_CURRENT_CIK_BACKFILL = NO
P5_IDENTITY_ACCOUNTING_PRIVATE_CHECKSUM_LEDGER_SHA256 = 32cba10a8f50c2a2a7dc1c9480547272b6f9ef501c49ef4c2a644c711f53dcd5
P5_IDENTITY_CONTRACTION_OFFLINE_REPLAY_SHA256 = faab5726a5792b3d15cb1150f409845614a1b9bf8e2664e668ab46a5b2fbfb65
P5_PRE_CONTRACTION_VALUEIN_ADAPTER_LOC = 419
P5_POST_CONTRACTION_VALUEIN_ADAPTER_LOC = 181
P5_VALUEIN_ADAPTER_LOC_REMOVED = 238
P5_IDENTITY_BINDING_CONTRACT_LOC = 312
P5_TOTAL_PRODUCTION_LOC_DELTA_VS_POST_PR60_MAIN = 110
P5_FULL_BUILD_GATE = IDENTITY_ACCOUNTING_COMPLETE_READY_FOR_ACCESSION_CENSUS
P5_AQ_MANUAL_IDENTITY_RULE_COUNT = 0
P5_AQ_SECURITY_MASTER_CREATED = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_EDGARTOOLS_NATIVE_WHOLE_PATH_AUDIT = PASS
P5_DIAGNOSTIC_CENSUS_BRANCH = DIAGNOSTIC_CENSUS_EVIDENCE_PENDING_UPSTREAM_REALIGNMENT
P5_BOUND_CIK_COUNT = 711
P5_EDGARTOOLS_CIK_ADDRESSABLE_COUNT = 711
P5_EDGARTOOLS_DOMESTIC_ISSUER_COUNT = 677
P5_EDGARTOOLS_FOREIGN_PRIVATE_ISSUER_COUNT = 29
P5_EDGARTOOLS_UNCLASSIFIED_ISSUER_COUNT = 5
P5_EDGARTOOLS_FORTY_F_ISSUER_COUNT = 0
P5_EDGARTOOLS_NATIVE_FINANCIAL_SURFACE_AVAILABLE_COUNT = 708
P5_EDGARTOOLS_NATIVE_FINANCIAL_SURFACE_UNAVAILABLE_COUNT = 3
P5_EDGARTOOLS_6K_ROLE = NATIVE_WHERE_STRUCTURED_OTHERWISE_EVENT_OR_TEXTUAL
P5_EDGARTOOLS_ISSUER_AWARE_FILING_DISCOVERY_OWNER = YES
P5_EDGARTOOLS_FINANCIAL_STATEMENT_EXTRACTION_OWNER = YES
P5_EDGARTOOLS_XBRL_FACT_EXTRACTION_OWNER = YES
P5_SECFSDSTOOLS_ROLE = OPTIONAL_BULK_ACCELERATOR_AND_CROSSCHECK
P5_SECFSDSTOOLS_FULL_BUILD_GATE = RETIRED
P5_AQ_PERIODIC_FORM_WHITELIST_REQUIRED = NO
P5_AQ_FINANCIAL_STATEMENT_ENGINE_REQUIRED = NO
P5_EDGARTOOLS_NATIVE_WHOLE_PATH_PRIVATE_CHECKSUM_LEDGER_SHA256 = f1d0a03069d5d4ffa95953aba5fdf1538852c5bebc62e959021633e259d9a4fb
P5_AQ_FORM_ROUTER_ENGINE = NO
P5_AQ_XBRL_ENGINE = NO
P5_AQ_STATEMENT_ENGINE = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_EDGARTOOLS_NATIVE_FULL_UNIVERSE_BUILD_DESIGN = PASS
P5_EDGARTOOLS_NATIVE_WHOLE_PATH_AUTHORITY = FROZEN
P5_EDGARTOOLS_NATIVE_BUILD_DESIGN_POST_AUDIT_MAIN = d0e0f5e3cfc8e5a8aa3c0d3a0a7df7261dfd15c1
P5_EDGARTOOLS_NATIVE_HISTORICAL_INGESTION_MODE = ONE_TIME_HISTORICAL_BACKFILL_PLUS_IMMUTABLE_POINT_IN_TIME_VINTAGES
P5_EDGARTOOLS_NATIVE_LIVE_INGESTION_MODE = INCREMENTAL_NEW_ACCESSION_ONLY
P5_EDGARTOOLS_NATIVE_FULL_HISTORY_REREAD_PER_LIVE_CYCLE = NO
P5_EDGARTOOLS_NATIVE_FULL_SUBMISSION_MIRROR = PROHIBITED
P5_EDGARTOOLS_NATIVE_STORAGE_PLAN = COMPLETE_256_GIB_BOUNDED
P5_EDGARTOOLS_NATIVE_CHECKPOINT_RESUME_PLAN = COMPLETE_ACCESSION_GRANULARITY
P5_EDGARTOOLS_NATIVE_QLIB_HANDOFF_PLAN = COMPLETE
P5_FULL_HISTORICAL_BUILD_AUTHORIZED = YES
P5_HISTORICAL_DATASET_BUILT = NO
P5_EDGARTOOLS_NATIVE_BUILD_DESIGN_PRIVATE_CHECKSUM_LEDGER_SHA256 = bd1e8d07fdece2a11b0aafb0f26d5b1905df3802ba35f9f9ce770a4cd26232b1
P5_ENTITYFACTS_FIRST_PATH = PASS
P5_SELECTIVE_REQUIRED_ACCESSION_COUNT = 36206
P5_SELECTED_SOURCE_ACQUISITION = EDGARTOOLS_NATIVE_REQUIRED_ASSETS_REMOTE_FIRST
P5_SAMPLE_SOURCE_NETWORK_REDUCTION_RATE = 69.1469159664%
P5_SELECTIVE_BUILD_PRODUCTION_LOC = 758
P5_DUPLICATE_DECIMAL_IMPLEMENTATION_COUNT = 0
P5_BROAD_ACCESSION_ACQUISITION_STARTED = NO
P5_FULL_HISTORICAL_BUILD_STARTED = NO
CURRENT_DEVELOPMENT_NEXT = P5_EDGARTOOLS_SELECTIVE_FULL_HISTORICAL_BUILD_EXECUTION_001
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
P2_V2_SEALED_OOS_ACCESSED = NO
NEWS_INTELLIGENCE = PLANNED / NOT STARTED
MULTI_ASSET = PLANNED / NOT STARTED
```

### P5 EdgarTools selective historical build production canary

The frozen 256-accession production canary is complete and passed. All 256
accessions reached `COMPLETE_WITH_EVIDENCE`; 34,379 unique immutable evidence
rows and 8,668 consolidated standardized events were sealed with zero duplicate
evidence IDs. Effective-session projection reported zero early visibility,
cross-CIK contamination, or period-class mixing failures. Qlib
`StaticDataLoader -> DataHandlerLP -> DatasetH` consumed the 508,842-row canary
panel without training, prediction, or backtest.

The final checkpoint replay reused 256/256 accessions, reprocessed zero, and
read zero network bytes. The 2 GiB cache ceiling was not approached, and the
ordinary transient source cache was evicted after seal verification. The broad
36,206-accession execution did not start. See
[P5 EdgarTools Selective Historical Build Production Canary 001](p5-edgartools-selective-historical-build-production-canary-001.md).

```text
P5_EDGARTOOLS_PRODUCTION_CANARY = PASS
PRODUCTION_CANARY_ACCESSION_COUNT = 256
FULL_BUILD_CANARY_STATUS = PASS
BROAD_FULL_UNIVERSE_EXECUTION_STARTED = NO
P5_HISTORICAL_DATASET_BUILT = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_EDGARTOOLS_SELECTIVE_FULL_HISTORICAL_BUILD_EXECUTION_001
```

### P5 EdgarTools selective full historical build execution

The full execution failed closed before accession processing because the frozen
36,206-accession selection is not completely joinable to the frozen native
filing-metadata inventory. Four required accessions lack native metadata. Two
resolve to empty SEC filing homepages, while the other two are authoritative
`10-KT` / `10-QT` filings outside the frozen EdgarTools periodic-object
admission. Substituting another accession or rewriting the source form would
break accession-bound provenance, so no broad acquisition or final seal was
started. See [P5 EdgarTools Selective Full Historical Build Execution
001](p5-edgartools-selective-full-historical-build-execution-001.md).

```text
P5_EDGARTOOLS_FULL_BUILD_EXECUTION = BLOCKED_PREEXECUTION_INPUT_INTEGRITY
SELECTIVE_REQUIRED_ACCESSION_COUNT = 36206
PREEXECUTION_REQUIRED_ACCESSION_BLOCKER_COUNT = 4
BROAD_FULL_UNIVERSE_EXECUTION_STARTED = NO
P5_HISTORICAL_DATASET_BUILT = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_HISTORICAL_BUILD_REQUIRED_ACCESSION_FAILURE_CLOSEOUT_001
```

### P5 historical build required-accession failure closeout

The four pre-execution blockers are closed without rerunning discovery or
starting the broad build. Exact SEC/EdgarTools confirmation found no filing row
and no usable attachments for `0001100682-20-000033` and
`0001108524-21-000014`; both remain explicit
`SOURCE_UNAVAILABLE_FOR_FINAL_PROVENANCE` records and cannot become final
fundamental evidence. The exact filings `0001193125-10-257767` (`10-KT`) and
`0001418135-18-000016` (`10-QT`) passed the unchanged EdgarTools XBRL,
provenance, materialization, and seal path with 115 evidence rows. Filed forms
and native period semantics remain unchanged.

The immutable corrected execution inventory reconciles 36,204 source-verifiable
required accessions plus two source-unavailable records to the original 36,206.
No replacement accession, fabricated source hash, custom form router, or custom
XBRL engine was introduced. See [P5 Historical Build Required Accession Failure
Closeout 001](p5-historical-build-required-accession-failure-closeout-001.md).

```text
P5_REQUIRED_ACCESSION_FAILURE_CLOSEOUT = PASS
SELECTIVE_DISCOVERED_ACCESSION_COUNT = 36206
SOURCE_VERIFIABLE_REQUIRED_ACCESSION_COUNT = 36204
SOURCE_UNAVAILABLE_ACCESSION_COUNT = 2
TRANSITION_FINANCIAL_ACCESSION_COUNT = 2
BROAD_FULL_UNIVERSE_EXECUTION_STARTED = NO
P5_HISTORICAL_DATASET_BUILT = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_EDGARTOOLS_SELECTIVE_FULL_HISTORICAL_BUILD_EXECUTION_RESUME_001
```

### P5 EdgarTools complete capability census and native interface activation

An isolated, zero-SEC-request census of the installed EdgarTools 5.58.0
runtime audited 66 filing-intelligence capabilities. EdgarTools directly owns
55, and ten require only thin AQ eligibility, accession-state, evidence, or PIT
policy. The only upstream gap is push/webhook delivery; the native current
filings feed and pagination already provide the polling surface required for
future incremental ingestion, so no AQ SEC poller or watcher engine is needed.

Current AQ P5 code contains no duplicate SEC client, filing/XBRL/financial
statement engine, statement stitcher, document parser, or live poller. The
future live and narrative paths are therefore activated as direct EdgarTools
interfaces, without adding a cosmetic wrapper or production code. The active
historical build remains untouched. See [P5 EdgarTools Complete Capability
Census and Native Interface Activation 001](p5-edgartools-complete-capability-census-native-interface-activation-001.md).

```text
P5_EDGARTOOLS_CAPABILITY_COUNT_AUDITED = 66
P5_EDGARTOOLS_NATIVE_DIRECT_COUNT = 55
P5_EDGARTOOLS_NATIVE_WITH_THIN_AQ_POLICY_COUNT = 10
P5_EDGARTOOLS_TRUE_UPSTREAM_GAP_COUNT = 1
P5_CURRENT_AQ_DUPLICATE_COUNT = 0
P5_AQ_DUPLICATES_RETIREABLE_COUNT = 0
P5_SELECTED_LIVE_FILING_DISCOVERY_OWNER = EDGARTOOLS
P5_SELECTED_FINANCIAL_STATEMENT_OWNER = EDGARTOOLS
P5_SELECTED_XBRL_OWNER = EDGARTOOLS
P5_SELECTED_DOCUMENT_OWNER = EDGARTOOLS
P5_SELECTED_NOTES_OWNER = EDGARTOOLS
P5_HISTORICAL_BUILD_INTERFERENCE = NO
P5_SEC_DATA_REQUEST_COUNT = 0
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT_AFTER_HISTORICAL_BUILD = P5_LIVE_INCREMENTAL_FILING_INGESTION_DESIGN_AND_POC_001
```

### P5 EdgarTools capability authority merge and native live-path offline activation

PR #67 squash-merged the 66-capability EdgarTools ownership census at
`5ad77c006a25f5fcd0739d0f355824f368368e11`. An isolated offline proof now
composes one native `CurrentFilings` page with accepted-CIK, exact-accession
deduplication, frozen form, and source-availability policy, then passes selected
rows to the same exact-accession processor used by the historical build.

The proof covers unseen periodic filings, duplicate observations, amendments,
transition forms, non-bound CIKs, source-unavailable accessions, and an 8-K
that remains natively readable without false structured-fundamental admission.
No scheduler, poller, SEC client, feed parser, form router, XBRL engine,
document parser, or second materializer was introduced. Live production is not
active. See [P5 EdgarTools Capability Authority Merge and Native Live Path
Offline Activation 001](p5-edgartools-capability-authority-merge-and-native-live-path-offline-activation-001.md).

```text
P5_EDGARTOOLS_CAPABILITY_AUTHORITY_MERGE_PR = 67
P5_EDGARTOOLS_CAPABILITY_AUTHORITY_MERGE_SHA = 5ad77c006a25f5fcd0739d0f355824f368368e11
P5_EDGARTOOLS_CURRENT_FILINGS_OWNER = EDGARTOOLS
P5_EXISTING_ACCESSION_PROCESSOR_REUSED = YES
P5_ACCESSION_IS_DEDUP_KEY = YES
P5_LIVE_INCREMENTAL_INTERFACE_OFFLINE_POC = PASS
P5_LIVE_INCREMENTAL_PRODUCTION_ACTIVE = NO
P5_NEW_LIVE_PRODUCTION_LOC = 78_NET
P5_SEC_DATA_REQUEST_COUNT = 0
P5_HISTORICAL_BUILD_INTERFERENCE = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PARALLEL_DEVELOPMENT_NEXT = P5_EDGARTOOLS_NATIVE_FILING_INTELLIGENCE_CAPABILITY_ACTIVATION_001
```

### P5 EdgarTools native filing-intelligence capability activation

PR #68 squash-merged the offline native live-path activation at
`99e5eba56ec5d401f8dc6fbc82e8cc0e2a5dadb0`. A new isolated zero-network proof
then exercised EdgarTools 5.58.0 typed 10-K, 10-Q, 8-K, and 6-K objects plus
native `Document`, `Note`/`Notes`, `Attachment`/`Attachments`, exhibits, and
press-release selection. Foreign-report and parsed-XBRL interfaces without a
local content fixture are explicitly classified as interface-present rather
than falsely reported as content-proven.

The filing-intelligence matrix contains 32 rows: 22 are direct upstream
capabilities, ten need only future AQ feature eligibility/PIT/evidence policy,
and none is a true upstream gap. No production wrapper or parsing code was
added. The independent historical build remains untouched. See [P5 EdgarTools
Native Filing Intelligence Capability Activation 001](p5-edgartools-native-filing-intelligence-capability-activation-001.md).

```text
P5_NATIVE_LIVE_MERGE_PR = 68
P5_NATIVE_LIVE_MERGE_SHA = 99e5eba56ec5d401f8dc6fbc82e8cc0e2a5dadb0
P5_FILING_INTELLIGENCE_CAPABILITY_COUNT_AUDITED = 32
P5_EDGARTOOLS_NATIVE_DIRECT_COUNT = 22
P5_EDGARTOOLS_NATIVE_WITH_THIN_AQ_FEATURE_POLICY_COUNT = 10
P5_TRUE_UPSTREAM_GAP_COUNT = 0
P5_NEW_FILING_INTELLIGENCE_PRODUCTION_LOC = 0
P5_SEC_DATA_REQUEST_COUNT = 0
P5_HISTORICAL_BUILD_INTERFERENCE = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PARALLEL_DEVELOPMENT_NEXT = P5_FILING_INTELLIGENCE_FEATURE_POLICY_SELECTION_001
```

### P5 deterministic filing-intelligence feature policy

PR #69 squash-merged the EdgarTools filing-intelligence authority at
`3503bf11125164b19427fde494eac6c7a0830dfb`. A policy-only preregistration then
audited 33 candidates and selected five P5 V1 filing features: filing lag,
after-close acceptance, amendment status, native press-release exhibit
presence, and native authorized exhibit count.

The five features are accession-bound, deterministic, visible only from the
existing XNYS effective session, and distinct from the eleven structured
fundamental metrics. Six semantic/LLM/embedding candidates remain deferred to
P6 and 22 candidates are explicitly rejected. No parser, NLP pipeline,
calculator, production feature code, model training, backtest, or SEC request
was added. See [P5 Filing Intelligence Deterministic Feature Policy
001](p5-filing-intelligence-deterministic-feature-policy-001.md).

```text
P5_FILING_INTELLIGENCE_AUTHORITY_MERGE_PR = 69
P5_FILING_INTELLIGENCE_AUTHORITY_MERGE_SHA = 3503bf11125164b19427fde494eac6c7a0830dfb
P5_FILING_FEATURE_CANDIDATE_COUNT = 33
P5_SELECTED_V1_FILING_FEATURE_COUNT = 5
P5_DEFERRED_P6_FILING_FEATURE_COUNT = 6
P5_REJECTED_FILING_FEATURE_COUNT = 22
P5_LLM_FEATURE_COUNT = 0
P5_EMBEDDING_FEATURE_COUNT = 0
P5_CUSTOM_PARSER_FEATURE_COUNT = 0
P5_NEW_FEATURE_PRODUCTION_LOC = 0
P5_FILING_FEATURE_POLICY_SELECTED = YES
P5_SEC_DATA_REQUEST_COUNT = 0
P5_HISTORICAL_BUILD_INTERFERENCE = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PARALLEL_DEVELOPMENT_NEXT = P5_FILING_INTELLIGENCE_SELECTED_FEATURE_THIN_MATERIALIZATION_POC_001
```

### P5 filing-feature policy merge and thin materialization POC

PR #70 squash-merged the five-feature preregistration at
`f2b2c20977f607062f0d334f79441ccfa899502f`. An isolated, zero-network POC then
materialized exactly those five accession-bound features from native
EdgarTools objects, the existing XNYS effective-session policy, and one narrow
immutable `FilingFeatureObservationV1` contract.

All 16 required A-P cases pass, along with immutable-identity, exact-inventory,
native-object-unavailable, Sunday applicability, early-visibility, and
no-network/parser checks. Semantic closeout uses
`NOT_APPLICABLE_SESSION_DATE` for non-XNYS acceptance dates and correctly names
the native class field `native_edgartools_object_type`. The full P5 regression
set is 151/151 PASS. No registry, transform graph, parser,
market-hours engine, factor engine, generic ETL, LLM/NLP path, SEC request,
historical feature build, training, or backtest was introduced. The concurrent
historical build remains untouched. See [P5 Filing Feature Policy Merge and
Thin Materialization POC 001](p5-filing-feature-policy-merge-and-thin-materialization-poc-001.md).

```text
P5_FILING_FEATURE_POLICY_MERGE_PR = 70
P5_FILING_FEATURE_POLICY_MERGE_SHA = f2b2c20977f607062f0d334f79441ccfa899502f
P5_FILING_FEATURE_THIN_MATERIALIZATION_POC = PASS
P5_MATERIALIZED_FEATURE_ID_COUNT = 5
P5_SELECTED_FEATURE_POC_CASE_COUNT = 16
P5_SELECTED_FEATURE_POC_CASES = PASS
P5_EARLY_VISIBILITY_COUNT = 0
P5_WEEKEND_ACCEPTANCE_MISSINGNESS = NOT_APPLICABLE_SESSION_DATE
P5_NON_EVENT_FORM_EXHIBIT_MISSINGNESS = NOT_APPLICABLE_FORM
P5_NATIVE_OBJECT_FIELD_NAME = native_edgartools_object_type
P5_NATIVE_OBJECT_FIELD_SEMANTICS = EXACT_CLASS_TYPE
P5_CONTRACT_VERSION_DECISION = V1_CORRECTED_IN_PLACE_BEFORE_FIRST_MERGE
P5_V1_NEVER_MERGED_OR_USED_FOR_PERFORMANCE = YES
P5_SEC_DATA_REQUEST_COUNT = 0
P5_HISTORICAL_BUILD_INTERFERENCE = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PARALLEL_DEVELOPMENT_NEXT = P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_DESIGN_AND_ABLATION_PROTOCOL_001
```

### P5 filing-feature historical materialization design and ablation protocol

The historical design keeps the five merged filing features as immutable,
accession-bound sparse point events. The 36,204-accession structured-fundamental
inventory is not incorrectly reused as the complete filing-feature population:
the future EdgarTools-native population covers all date-valid filings for the
three metadata features and exactly 8-K/8-K/A/6-K/6-K/A for the two exhibit
features. No SEC census or materialization ran in this task.

The future Qlib handoff uses `(datetime, instrument=episode_id)`, exact five
numeric columns, null-preserving missingness, and no forward fill. The primary
ablation is frozen to two trials—control versus the identical Qlib baseline
plus all five features—with eight zero-tolerance leakage gates. A single P5
model/workflow is not yet authorized, so model authority remains pending
rather than being inferred from P1 exploratory or P2 certification choices.
See [P5 Filing Feature Historical Materialization Design and Ablation Protocol
001](p5-filing-feature-historical-materialization-design-and-ablation-protocol-001.md).

```text
P5_FILING_FEATURE_PRIMARY_STORAGE_SHAPE = SPARSE_ACCESSION_BOUND_OBSERVATIONS
P5_FILING_FEATURE_TEMPORAL_SEMANTICS = ALL_FIVE_POINT_EVENT
P5_FILING_FEATURE_STRUCTURED_FUNDAMENTAL_INVENTORY_REUSABLE_FOR_ALL = NO
P5_FILING_FEATURE_QLIB_HANDOFF_OWNER = MICROSOFT_QLIB
P5_FILING_FEATURE_EVALUATION_MODEL_AUTHORITY = EVALUATION_MODEL_AUTHORITY_PENDING
P5_FILING_FEATURE_PREREGISTERED_TRIAL_COUNT = 2
P5_FILING_FEATURE_MULTIPLE_TESTING_OWNER = ARCH_8.0.0
P5_FILING_FEATURE_LEAKAGE_GATE_COUNT = 8
P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_DESIGN = DESIGN_READY_WAITING_FOR_HISTORICAL_BUILD
P5_FILING_FEATURE_ABLATION_PROTOCOL = PREREGISTERED_WAITING_FOR_DATA_AND_MODEL_AUTHORITY
P5_SEC_DATA_REQUEST_COUNT = 0
P5_HISTORICAL_BUILD_INTERFERENCE = NO
P5_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
PARALLEL_DEVELOPMENT_NEXT = P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_001
```

### P6 information-intelligence upstream handoff preaudit census

PR #72 squash-merged the completed P5 filing-feature historical
materialization and ablation design at
`2e194950e70bc3860e9d5b41dd9c416a6cadd25b`. P5 upstream ownership is closed:
EdgarTools remains the filing, fundamentals, XBRL, document, and notes owner,
and the independently running historical build was not disturbed.

The future-phase P6 preaudit census audited 23 news, macro, sentiment,
text/LLM, earnings-call, and multi-agent capabilities across nine current
upstream projects/services. P6 is not active and no selected upstream
deployment has started.
Official FRED/ALFRED through `fredapi` is the macro PIT owner. OpenBB is the
news/provider and FRED-calendar gateway, but not universal PIT authority.
Current Transformers plus the pinned ProsusAI/finbert model is the narrow
financial-sentiment leaf. GDELT is supplementary historical news/event
metadata. TradingAgents remains an information-synthesis challenger, while
FinGPT and general LLM paths remain deferred. Exact universal news
`first_available_at` and historical PIT social sentiment are the two true
upstream gaps; neither authorizes a custom AQ engine. See [P6 Information
Intelligence Upstream Handoff Census 001](p6-information-intelligence-upstream-handoff-census-001.md).

```text
P5_UPSTREAM_HANDOFF_STATUS = COMPLETE_WITH_POST_BUILD_HYGIENE
P5_UPSTREAM_HANDOFF = COMPLETE_WITH_POST_BUILD_HYGIENE
P5_NEW_GENERIC_ENGINE_REQUIRED = NO
P5_UPSTREAM_HANDOFF_BLOCKER_COUNT = 0
CURRENT_PHASE = P5_FUNDAMENTAL_INTELLIGENCE
P5_COMPLETE = NO
P5_HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
P5_EXIT_CONDITION_SATISFIED = NO
P6_PREAUDIT_COMPLETE = YES
P6_ACTIVE = NO
P6_PHASE_ENTRY_AUTHORIZED = NO
P6_SELECTED_UPSTREAM_DEPLOYMENT_STARTED = NO
P6_CAPABILITY_COUNT_AUDITED = 23
P6_UPSTREAM_PROJECT_COUNT_AUDITED = 9
MACRO_PIT_OWNER = OFFICIAL_FRED_ALFRED_VIA_FREDAPI
MACRO_RELEASE_CALENDAR_OWNER = OPENBB_FRED_PROVIDER_SUPPLEMENTARY_CALENDAR
NEWS_DISCOVERY_OWNER = OPENBB_NEWS_PROVIDER_GATEWAY_PENDING_BOUNDED_PROVIDER_POC
HISTORICAL_NEWS_OWNER = GDELT_2X_SUPPLEMENTARY_ONLY
FINANCIAL_SENTIMENT_OWNER = HUGGINGFACE_TRANSFORMERS_PLUS_PINNED_PROSUSAI_FINBERT
LLM_TEXT_EXTRACTION_OWNER = DEFER_PENDING_POC
MULTI_AGENT_INFORMATION_OWNER = TRADINGAGENTS_CHALLENGER_PENDING_POC
P6_TRUE_UPSTREAM_GAP_COUNT = 2
P6_PAID_REQUIRED_SELECTED_OWNER_COUNT = 0
P6_DUPLICATE_SEC_STACK = NO
P6_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P6_NEW_PRODUCTION_LOC = 0
P6_SEC_DATA_REQUEST_COUNT = 0
P6_FRED_DATA_REQUEST_COUNT = 0
P6_NEWS_DATA_REQUEST_COUNT = 0
P6_LLM_CALL_COUNT = 0
P5_HISTORICAL_BUILD_INTERFERENCE = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
CURRENT_DEVELOPMENT_NEXT = P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_001
CURRENT_DEVELOPMENT_NEXT_GATE = WAITING_FOR_P5_HISTORICAL_FUNDAMENTALS_BUILD_TERMINAL_CLOSEOUT
FUTURE_AFTER_P5_CLOSEOUT = P6_SELECTED_UPSTREAM_LEAVES_DEPLOYMENT_AND_BOUNDED_POC_001
```

### P5 post-build readiness and evaluation-authority freeze

The terminal-closeout authority now contains 26 exact gates covering global
36,206-accession accounting, the 36,204 source-verifiable denominator, the two
separate source-unavailable records, evidence/PIT integrity, zero-network
checkpoint replay, cache/storage hygiene, DVC identity, and the full-history
Qlib handoff. The independently running historical build was not read or
modified.

Four existing model authorities were audited without performance selection.
Qlib `LinearModel(estimator=ols)` is the strongest fixed-vehicle candidate on
ex-ante simplicity and reuse grounds, but its exact current recipe fails the
P5 processor-semantics gate. `DataHandlerLP` append processing applies
`RobustZScoreNorm` and then `Fillna(feature, 0)` to both inference and learning
surfaces, which would erase the frozen distinction between missing sparse
point events and legitimate zero. Simply removing `Fillna` would let
`LinearModel.fit().dropna()` change the challenger row population. No model,
processor, mask, or replacement authority was invented. See [P5 Post-Build
Readiness and Evaluation Authority Freeze 001](p5-post-build-readiness-and-evaluation-authority-freeze-001.md).

The processor-semantics follow-up preserves that Linear rejection and freezes
the already-existing Qlib `LGBModel` path as the evaluation vehicle. An
in-memory upstream-only proof showed that
`StaticDataLoader -> DataHandlerLP -> DatasetH -> LGBModel` preserves every
NaN, legitimate zero, and nonzero value when shared/inference processors are
empty and learning processors are label-only. Native LightGBM dataset
construction accepted those NaNs without a fit. No AQ processor, missing-value
engine, model engine, training, prediction, or backtest was introduced. See
[P5 Filing-Feature Processor-Semantics Authority Resolution 001](p5-filing-feature-processor-semantics-authority-resolution-001.md).

The evaluation-authority closeout makes the remaining boundaries exact.
LightGBM 4.7.0 retains explicit CPU deterministic mode, forced column-wise
histograms, all component seeds, eight fixed threads, fixed row/column order,
and the existing `colsample_bytree=0.8879` recipe. CONTROL is the ordered
157-column P2 OHLCV-only `RaggedAlpha158` surface over the authoritative P1/P5
episode-session universe. The earlier eleven-feature and mandatory S2/H2
scope is **SUPERSEDED_PRE_EVALUATION**. Final P5 V1 has two surfaces: S0 is
BASE_157 and S1 is BASE_157 plus exactly ten PIT fundamentals, for the single
required H1 comparison. The five filing-derived features remain valid
historical research ideas, but their stopped mass materialization and S2/H2
are deferred optional extensions rather than P5 V1 completion blockers. No
project model training, prediction, backtest, H1/H2 execution, or performance
inspection preceded this contraction. H1 attempt-001 is retained only as
diagnostic evidence because it omitted the already-frozen
`CSZScoreNorm(fields_group=label)` processor. The clean authority-corrected
attempt-002 passed its processor/input gate and completed S0 with finite Rank
IC, but WSL killed the process for global OOM after the S1 recorder started and
before S1 fit completion. No retry or resume path was used. H1 therefore remains
`INCONCLUSIVE`, P5 remains active, and attempt-001 performance is not used.
After the owner increased WSL to approximately 10 GiB RAM plus 4 GiB swap,
attempt-003 used separate preflight, S0, S1, and composition processes. Both
fresh fits completed without OOM and produced finite Rank IC values, and both
Qlib backtests completed. The single authorized DVC execution then failed
before WalkForward/CPCV/SPA/RealityCheck because the WSL-to-Windows PowerShell
command passed a quoted base-interpreter path that the skfolio virtual
environment could not resolve. No partial continuation or retry was performed.
The corrected direct Windows-environment entrypoint is statically validated in
the DVC definition, but requires separate owner authorization before another
scientific execution. H1 therefore remains `INCONCLUSIVE` because the frozen
post-prediction evidence family is incomplete. The separately authorized final
clean attempt-004 recreated every input from a new root and again completed
both fresh fits plus both Qlib backtests, but the direct Windows virtual-
environment launcher failed from the real WSL stage with the same quoted
base-interpreter path before skfolio began. The zero-science probe therefore
did not establish runtime-equivalent entrypoint validity. Attempt-004 stopped
without continuation or retry, so no WalkForward, CPCV, SPA, RealityCheck, or
eligible final H1 classification exists. Attempt-005 then performed the
stronger native Windows and WSL-interoperability import probes for both pinned
statistics environments; all four passed without runtime repair. Its new-root
execution again completed both fresh fits and both Qlib backtests, but the
skfolio launcher failed with the quoted base-interpreter path when invoked by
the real DVC stage. No retry or partial continuation was performed. This proves
that the remaining defect is specific to the DVC-to-WSL-to-Windows process
boundary rather than the pinned skfolio or arch imports themselves. Attempt-005
also has no WalkForward, CPCV, SPA, RealityCheck, or eligible final H1
classification. See
[P5 Evaluation Reproducibility and
Control-Surface Authority Closeout
001](p5-evaluation-reproducibility-and-control-surface-authority-closeout-001.md)
for the final authority and `p5-minimal-upstream-v1.json` for the data scope.

```text
CURRENT_PHASE = P5_FUNDAMENTAL_INTELLIGENCE
P5_COMPLETE = NO
HISTORICAL_BUILD_STATUS = MINIMAL_UPSTREAM_V1_BUILD_COMPLETE
HISTORICAL_BUILD_INTERFERENCE = NO
P5_MINIMAL_UPSTREAM_DATA_LAYER = COMPLETE
MODEL_AUTHORITIES_AUDITED = 4
LINEAR_OLS_NULL_PRESERVING_COMPATIBLE = NO
LIGHTGBM_NULL_PRESERVING_COMPATIBLE = YES
EVALUATION_MODEL_AUTHORITY = FROZEN
P5_EVALUATION_MODEL = qlib.contrib.model.gbdt.LGBModel
P5_EVALUATION_MODEL_ROLE = FIXED_FEATURE_ABLATION_VEHICLE
P5_DATA_LOADER = qlib.data.dataset.loader.StaticDataLoader
P5_DATA_HANDLER = qlib.data.dataset.handler.DataHandlerLP
P5_FEATURE_SHARED_PROCESSORS = []
P5_FEATURE_INFER_PROCESSORS = []
P5_LEARN_PROCESSORS = DropnaLabel(label)->CSZScoreNorm(label)
PROCESSOR_SEMANTICS_GATE = PASS
SYNTHETIC_NULL_SEMANTICS_POC = PASS
REPRODUCIBILITY_GATE = PASS
CONTROL_SURFACE_GATE = PASS
P5_EXIT_COVERAGE_GATE = BLOCKED_STATISTICS_RUNTIME_DVC_WSL_BOUNDARY
LIGHTGBM_DETERMINISTIC = true
LIGHTGBM_FORCE_COL_WISE = true
LIGHTGBM_FORCE_ROW_WISE = false
LIGHTGBM_NUM_THREADS = 8
FEATURE_SUBSAMPLING_ABLATION_COMPATIBILITY = PASS
CONTROL_FEATURE_FAMILY = P2_RAGGED_ALPHA158_OHLCV_157
CONTROL_FEATURE_COLUMN_COUNT = 157
CONTROL_FEATURE_MANIFEST_SHA256 = 7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463
CONTROL_DATASET_IDENTITY = P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135
SCIENTIFIC_SCOPE_CHANGE = PRE_EVALUATION_SCOPE_CONTRACTION
PRIOR_11_FEATURE_AUTHORITY = SUPERSEDED_PRE_EVALUATION
STRUCTURED_FUNDAMENTAL_FEATURE_COUNT = 10
P5_V1_REQUIRED_FUNDAMENTAL_FEATURE_COUNT = 10
P5_V1_FEATURES = Revenue; NetIncome; Assets; Liabilities; CommonEquity; NetCashFromOperatingActivities; CashAndCashEquivalents; CurrentAssetsTotal; CurrentLiabilitiesTotal; LongTermDebt
P5_V1_RETIRED_FEATURE = ShortTermDebt
SHORTTERMDEBT_STATUS = RETIRED_FROM_P5_V1
SHORTTERMDEBT_RETIREMENT_REASON = UPSTREAM_SEMANTIC_AMBIGUITY
UPSTREAM_PATCH_ALLOWED = NO
STRUCTURED_FUNDAMENTALS_INCLUDED_IN_CONTROL = NO
P5_FILING_INTERFACE_CAPABILITY = PROVEN_UPSTREAM_AVAILABLE
HISTORICAL_FILING_FEATURE_IDEA_COUNT = 5
P5_V1_REQUIRED_FILING_DERIVED_FEATURE_COUNT = 0
P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION = DEFERRED_OPTIONAL_P5_EXTENSION
FILING_FEATURE_HISTORICAL_MATERIALIZATION_STATUS = DEFERRED_OPTIONAL_P5_EXTENSION
HISTORICAL_FILING_ABLATION_TRIAL_COUNT = 2
P5_V1_EVALUATION_SURFACE_COUNT = 2
P5_EVALUATION_SURFACE_S0 = BASE_157
P5_EVALUATION_SURFACE_S1 = BASE_157_PLUS_EXACT_10_FUNDAMENTALS
S0_COLUMN_COUNT = 157
S1_COLUMN_COUNT = 167
P5_EVALUATION_SURFACE_S2 = DEFERRED_OPTIONAL_EXTENSION
P5_V1_REQUIRED_HYPOTHESIS_COUNT = 1
P5_H1 = S0_VS_S1
P5_H2 = DEFERRED_OPTIONAL_EXTENSION
P5_H2_STATUS = DEFERRED_OPTIONAL_EXTENSION
H2_EXECUTION_REQUIRED_FOR_P5_V1_EXIT = NO
MULTIPLE_TESTING_FAMILY_SIZE = 1
P5_REQUIRED_EVALUATION = H1_S0_VS_S1
PRIOR_SELECTIVE_ACCESSION_CENSUS = HISTORICAL_SUPERSEDED_PRE_EVALUATION
P5_V1_ACCESSION_ADMISSION = EXACT_ACCEPTANCE_REQUIRED_ELSE_EXCLUDE
P5_V1_FROZEN_UNRESOLVED_ACCEPTANCE_EXCLUSIONS = 5
P5_V1_UNRESOLVED_ACCEPTANCE_ADMITTED = 0
P5_V1_UNVERIFIABLE_ACCESSION_COUNT = 5
P5_V1_UNVERIFIABLE_ACCESSION_POLICY = EXCLUDED
REPAIR_REQUIRED = NO
HEURISTIC_SUBSTITUTION = NO
P5_V1_RAW_FINANCIAL_FACT_OWNER = SEC_COMPANYFACTS_BULK
P5_V1_HISTORICAL_FILING_METADATA_OWNER = SEC_SUBMISSIONS_BULK
P5_V1_STANDARD_CONCEPT_AND_PERIOD_OWNER = EDGARTOOLS_5_58
P5_V1_SECFSDSTOOLS_ROLE = REFERENCE_PARITY_ONLY
P5_V1_FLOW_PERIOD_AUTHORITY = DURATION_ANNUAL
P5_V1_STOCK_PERIOD_AUTHORITY = INSTANT
P5_V1_PERIOD_FALLBACK = NONE
P5_V1_FLOW_DERIVATION_COUNT = 0
P5_V1_UPSTREAM_MIGRATION_GATE = PASS
P5_V1_FULL_FROZEN_BULK_BUILD = PASS
P5_V1_QLIB_FULL_HISTORICAL_HANDOFF = PASS
P5_V1_SESSION_ROWS = 1893759
P5_V1_IDENTITY_EXCLUSION_SESSION_ROWS = 210966
P5_V1_NON_MISSING_FEATURE_CELLS = 15087774
P5_V1_EARLY_VISIBILITY_COUNT = 0
P5_V1_CROSS_CIK_CONTAMINATION_COUNT = 0
P5_V1_DUPLICATE_FINAL_EVENT_ID_COUNT = 0
QLIB_FULL_HISTORICAL_HANDOFF_REQUIRED = SATISFIED
ALL_FORM_POPULATION_CENSUS = DIAGNOSTIC_SUPERSEDED_PRE_EVALUATION
ALL_FORM_POPULATION_CENSUS_STATUS = DIAGNOSTIC_SUPERSEDED_PRE_EVALUATION
TOTAL_ADMITTED_FILING_ACCESSIONS = 826859
EVENT_FORM_ACCESSION_COUNT = 62371
PARTIAL_COMPLETED_ACCESSION_COUNT = 20000
PARTIAL_COMPLETED_OBSERVATION_COUNT = 100000
PARTIAL_OUTPUT_CLASSIFICATION = PARTIAL_ABORTED_SUPERSEDED_SCOPE
PID403_ROLE = HISTORICAL_REFERENCE_ONLY
PID403_FAILURE_COUNT = 392
PID403_FAILURES_REQUIRE_REPAIR = NO
P5_PRODUCTION_LOC_BASELINE = 2849
P5_PRODUCTION_LOC_FINAL = 2053
P5_PRODUCTION_LOC_RETIRED = 796
P5_PRODUCTION_LOC_TARGET_1600_MET = NO_SURVIVING_CONTRACTS_JUSTIFIED_IN_HISTORICAL_DATASET_README
POST_BUILD_HYGIENE_CANDIDATE_COUNT = 2
PR74_NEW_PRODUCTION_LOC = 0
AQ_MODEL_ENGINE = NO
AQ_TRAINING_ENGINE = NO
AQ_BACKTEST_ENGINE = NO
AQ_TERMINAL_CLOSEOUT_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
ATTEMPT_001_CLASSIFICATION = INVALID_IMPLEMENTATION_DEVIATION
ATTEMPT_001_PROCESSOR_AUTHORITY_MATCH = NO
ATTEMPT_001_MISSING_FROZEN_PROCESSOR = CSZScoreNorm(fields_group=label)
ATTEMPT_002_CLASSIFICATION = INCONCLUSIVE_RESOURCE_OOM
ATTEMPT_002_PREFIT_PROCESSOR_GATE = PASS
ATTEMPT_002_S0_MODEL_FIT_COUNT = 1
ATTEMPT_002_S1_MODEL_FIT_COUNT = 1_INCOMPLETE_RESOURCE_OOM
ATTEMPT_003_AUTHORITY = PROCESS_ISOLATED_AUTHORITY_CORRECTED
ATTEMPT_003_EXECUTION_STATUS = FAIL_POST_PREDICTION_STATISTICS_ENTRYPOINT
ATTEMPT_003_S0_MODEL_FIT_COUNT = 1_COMPLETE
ATTEMPT_003_S1_MODEL_FIT_COUNT = 1_COMPLETE
ATTEMPT_003_S0_MAX_RSS_KIB = 6180492
ATTEMPT_003_S1_MAX_RSS_KIB = 7509472
ATTEMPT_003_S0_TEST_RANK_IC = 0.0021911029598144574
ATTEMPT_003_S1_TEST_RANK_IC = 0.004588185207288156
ATTEMPT_003_H1_TEST_RANK_IC_DELTA = 0.0023970822474736987
ATTEMPT_004_AUTHORITY = FINAL_CLEAN_NO_PROTOCOL_CHANGE
ATTEMPT_004_EXECUTION_STATUS = FAIL_POST_PREDICTION_STATISTICS_ENTRYPOINT
ATTEMPT_004_FINAL_CLASSIFICATION_ELIGIBLE = NO
ATTEMPT_004_S0_MODEL_FIT_COUNT = 1_COMPLETE
ATTEMPT_004_S1_MODEL_FIT_COUNT = 1_COMPLETE
ATTEMPT_004_S0_MAX_RSS_KIB = 6168912
ATTEMPT_004_S1_MAX_RSS_KIB = 7514992
ATTEMPT_004_S0_TEST_RANK_IC = 0.0021911029598144574
ATTEMPT_004_S1_TEST_RANK_IC = 0.004588185207288156
ATTEMPT_004_H1_TEST_RANK_IC_DELTA = 0.0023970822474736987
ATTEMPT_005_AUTHORITY = FINAL_END_TO_END_NO_PROTOCOL_CHANGE
ATTEMPT_005_EXECUTION_STATUS = FINAL_END_TO_END_MODEL_EVIDENCE_COMPLETE_STATISTICS_COMPLETED_SEPARATELY
ATTEMPT_005_FINAL_CLASSIFICATION_ELIGIBLE = YES
ATTEMPT_005_S0_MODEL_FIT_COUNT = 1_COMPLETE
ATTEMPT_005_S1_MODEL_FIT_COUNT = 1_COMPLETE
ATTEMPT_005_S0_MAX_RSS_KIB = 6162212
ATTEMPT_005_S1_MAX_RSS_KIB = 7507124
ATTEMPT_005_S0_TEST_RANK_IC = 0.0021911029598144574
ATTEMPT_005_S1_TEST_RANK_IC = 0.004588185207288156
ATTEMPT_005_H1_TEST_RANK_IC_DELTA = 0.0023970822474736987
ATTEMPT_005_QLIB_REPORT_SHA256 = ad0ae88ab2d19229352f3b8d89eaca096df516320e5781c64ed97375a902cb58
ATTEMPT_005_DAILY_RETURNS_SHA256 = 74f4628f8ef2e2dcd51cbad575074f23748f632deac77b96068dc3ef1d97709a
ATTEMPT_005_S0_PREDICTION_SHA256 = 52d7f8bbf56ff565f5b77584786f59c3279e31895d54e42bbf0183246a950df6
ATTEMPT_005_S1_PREDICTION_SHA256 = dcc6e984189fc6068b20d84d79e2465bd479db6fa66399b2e9553d57abc53bd9
ATOMIC_SINGLE_PROCESS_H1_REQUIRED = NO
MODEL_AND_STATISTICS_SAME_RUNTIME_REQUIRED = NO
ATTEMPT_005_STATISTICS_CONTINUATION_IS_PROTOCOL_CHANGE = NO
ATTEMPT_006_CREATED = NO
WSL_STATISTICS_RUNTIME = /home/zhou/AQ_ENVS/p5-h1-statistics
WSL_STATISTICS_PYTHON_VERSION = 3.10.21
WSL_STATISTICS_SKFOLIO_VERSION = 1.0.6
WSL_STATISTICS_ARCH_VERSION = 8.0.0
WSL_STATISTICS_NUMPY_VERSION = 2.2.6
WSL_STATISTICS_PANDAS_VERSION = 2.3.3
WSL_STATISTICS_PIP_CHECK = PASS
CROSS_OS_STATISTICS_RUNTIME_DEPENDENCY = NO
PROJECT_MODEL_TRAINING_COUNT = 10
PROJECT_PREDICTION_COUNT = 9
PROJECT_BACKTEST_COUNT = 8
H1_EXECUTED = COMPLETE_ATTEMPT_005
H2_EXECUTED = NO
H1_RESULT_CLASSIFICATION = NO_MEASURABLE_INCREMENTAL_VALUE
S0_TEST_RANK_IC = 0.0021911029598144574
S1_TEST_RANK_IC = 0.004588185207288156
H1_TEST_RANK_IC_DELTA = 0.0023970822474736987
WALKFORWARD_STATUS = PASS_EXECUTED_GATE_FALSE
WALKFORWARD_POSITIVE_ACTIVE_RETURN_FRACTION = 0.3333333333333333
WALKFORWARD_MEDIAN_ACTIVE_RETURN = -0.008056716227315519
CPCV_STATUS = PASS_EXECUTED_GATE_TRUE
CPCV_POSITIVE_ACTIVE_RETURN_FRACTION = 0.7555555555555555
CPCV_MEDIAN_ACTIVE_RETURN = 0.03305404742863449
SPA_STATUS = PASS_EXECUTED
SPA_PVALUE = 0.077
REALITYCHECK_STATUS = PASS_EXECUTED
REALITYCHECK_PVALUE = 0.077
DVC_H1_REPRO_STATUS = SEALED_COMPLETE_EXISTING_ATTEMPT_005_OUTPUT
DVC_SEAL_METHOD = DVC_COMMIT_FORCE_EXISTING_OUTPUT
ACCEPTANCE_TIME_LEAKAGE_COUNT = 0
REPORT_PERIOD_LEAKAGE_COUNT = 0
AMENDMENT_BACKWARD_LEAKAGE_COUNT = 0
CROSS_CIK_CONTAMINATION_COUNT = 0
EPISODE_MEMBERSHIP_LEAKAGE_COUNT = 0
CURRENT_TICKER_LEAKAGE_COUNT = 0
SOURCE_UNAVAILABLE_SUBSTITUTION_COUNT = 0
FUTURE_FILING_VISIBILITY_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
P5_COMPLETE = YES
CURRENT_PHASE = P6_NEWS_MACRO_SKILLS
P6_ACTIVE = YES
P6_UPSTREAM_DEPLOYMENT_AUDIT = PASS
P6_DEPLOYED_UPSTREAM_COUNT = 6
P6_CAPABILITY_COUNT = 23
P6_UPSTREAM_WHOLE_DEPLOYED_COUNT = 1
P6_UPSTREAM_LEAF_DEPLOYED_COUNT = 10
P6_UPSTREAM_CHALLENGER_DEPLOYED_COUNT = 2
P6_DEFER_NO_MATURE_UPSTREAM_COUNT = 3
P6_DEFER_ACCESS_OR_CREDENTIAL_COUNT = 7
P6_GENUINE_AQ_SPECIFIC_THIN_LOGIC_COUNT = 0
P6_TRUE_UNSOLVED_UPSTREAM_GAP_COUNT = 1
P6_TRUE_UNSOLVED_UPSTREAM_GAPS = REDDIT_SENTIMENT_LICENSE_AND_REDDIT_TERMS_AUTHORITY
P6_RESIDUAL_CUSTOM_CAPABILITY_COUNT = 4
P6_CUSTOM_ENGINE_REQUIRED_COUNT = 0
P6_NEW_PRODUCTION_LOC = 0
P6_FREDAPI_RUNTIME = /home/zhou/AQ_ENVS/p6-data-gateways
P6_FREDAPI_VERSION = 0.5.2
P6_INITIAL_FRED_CREDENTIAL_GATE = BLOCKED_CREDENTIAL_REQUIRED
P6_FRED_API_KEY_AVAILABLE = YES
P6_FRED_NETWORK_REQUEST_COUNT = 15
P6_FRED_MACRO_PIT_POC = PASS
P6_FRED_ALFRED_PIT_FITNESS = PASS_CAN_PROVE_WHAT_WAS_KNOWN_WHEN
P6_THIN_MACRO_SHAPE_ADAPTER_REQUIRED = NO_SUPERSEDED_BY_VINTAGE_NATIVE_RELATION
P6_THIN_MACRO_SHAPE_ADAPTER_IMPLEMENTED = NO
P6_MACRO_PIT_NORMALIZATION_OWNER = VINTAGE_0_9_0
P6_MACRO_PIT_NORMALIZATION_OWNERSHIP_MODE = UPSTREAM_LEAF
P6_CAN_UPSTREAM_OWN_MACRO_EVIDENCE_SHAPE = YES
P6_CAN_UPSTREAM_OWN_MACRO_SESSION_VISIBLE_REVISION_RELATION = YES_VIA_UPSTREAM_NATIVE_RELATIONAL_COMPOSITION
P6_CAN_UPSTREAM_OWN_FINAL_MACRO_FEATURE_PANEL = YES_POLICY_FROZEN_COMPOSITION_IMPLEMENTATION_PENDING
P6_MACRO_PIT_PANEL_CODE_REQUIRED = NO_FOR_SESSION_VISIBILITY_COMPOSITION
P6_MACRO_SESSION_NATIVE_COMPOSITION_POC = PASS
P6_MACRO_SESSION_POLICY = FIRST_XNYS_SESSION_STRICTLY_AFTER_KNOWN_AT_DATE
P6_MACRO_SESSION_POLICY_OWNER = AQ_DECLARATIVE_PREDICATE_ONLY
P6_MACRO_SESSION_RELATION_OWNER = EXCHANGE_CALENDARS_VIA_AQ_XNYS_CALENDAR
P6_MACRO_RELATIONAL_COMPOSITION_OWNER = DUCKDB_1_5_5
P6_MACRO_VINTAGE_AS_OF_EQUIVALENCE = PASS
P6_MACRO_AS_OF_SESSION_CUTOFF_RULE = TARGET_SESSION_MINUS_ONE_CALENDAR_DAY
P6_MACRO_REVISION_RELATION_PRESERVED = PASS
P6_MACRO_FINAL_OBSERVED_AT_FEATURE_POLICY_SELECTED = YES
P6_CUSTOM_ENGINE_REQUIRED = NO
P6_RESIDUAL_UPSTREAM_SKILLS_SUBSTITUTION_AUDIT = PASS
P6_FRED_MD_QD_STATUS = PRIMARY_MACRO_FEATURE_TRANSFORMATION_REFERENCE
P6_MACRO_TRANSFORMATION_POLICY_UPSTREAM_REDUCTION = BENCHMARK_CODES_REUSED_AS_PRIMARY_REFERENCE_FINAL_SELECTION_REMAINS_AQ_SCIENTIFIC_POLICY
P6_LANGEXTRACT_STATUS = VALID_BUT_MODEL_DEPENDENT_UPSTREAM_EXTRACTION_MECHANICS
P6_LANGEXTRACT_AGENT_SKILL_STATUS = ADOPT_AS_IS_PRIVATE_USAGE_GUIDANCE
P6_FINGPT_STRUCTURED_EXTRACTION_ROLE = REFERENCE_OR_CHALLENGER_ONLY
P6_FINANCIAL_SKILLS_ADOPTION_MODE = SELECTED_UPSTREAM_SKILL_WORKFLOW_ONLY
P6_ALPHA_VANTAGE_TRANSCRIPT_STATUS = BLOCKED_CREDENTIAL_COST_AND_TERMS_VALIDATION
P6_MEDIA_CLOUD_SAFE_AVAILABILITY_STATUS = VALID_CONSERVATIVE_UPPER_BOUND_CREDENTIAL_REQUIRED
P6_COMMON_CRAWL_CAPTURE_STATUS = SELECTED_SUPPLEMENTARY_CAPTURE_PROVENANCE_LEAF
P6_ARCTIC_SHIFT_STATUS = SERIOUS_TECHNICAL_CANDIDATE_BLOCKED_LICENSE_OR_TERMS
P6_SOCIAL_SENTIMENT_CLASSIFICATION = TRUE_GAP_RETAINED_REDDIT_LICENSE_AND_TERMS
P6_MLFLOW_DATASET_LINEAGE_STATUS = SELECTED_EXISTING_OWNER_WITH_DVC
P6_NEWS_EXACT_FIRST_AVAILABLE_AT = NOT_UNIVERSALLY_PROVEN
P6_NEWS_SAFE_AVAILABLE_AT = CONSERVATIVE_CAPTURE_UPPER_BOUND_AVAILABLE
P6_MACRO_FEATURE_OBSERVED_AT_POLICY_FREEZE = PASS
P6_MACRO_SOURCE_AUTHORITY = OFFICIAL_FRED_ALFRED
P6_MACRO_TRANSFORMATION_REFERENCE = FRED_MD_QD
P6_GDP_STATUS = DEFERRED
P6_GDP_STATUS_REASON = NO_EXACT_CURRENT_BENCHMARK_TRANSFORMATION
P6_GDPC1_STATUS = REJECTED
P6_GDPC1_STATUS_REASON = DISTINCT_REAL_GDP_IDENTITY_NOT_SELECTED_FOR_V1
P6_GDP_TO_GDPC1_SILENT_SUBSTITUTION = NO
P6_CPIAUCSL_STATUS = SELECTED
P6_CPIAUCSL_TRANSFORMATION = CODE_6_SECOND_LOG_DIFFERENCE
P6_UNRATE_STATUS = SELECTED
P6_UNRATE_TRANSFORMATION = CODE_2_FIRST_LEVEL_DIFFERENCE
P6_MACRO_V1_SELECTED_SERIES_COUNT = 2
P6_MACRO_V1_SELECTED_SERIES = CPIAUCSL,UNRATE
P6_MACRO_SESSION_STATE_CARRY_FORWARD = YES
P6_UPSTREAM_MISSING_OBSERVATION_IMPUTATION = NO
P6_MACRO_INTERPOLATION = NO
P6_MACRO_BACKFILL = NO
P6_MONTHLY_QUARTERLY_INDEPENDENT_STATE = YES
P6_MACRO_V1_QUARTERLY_SERIES_ACTIVE = NO
P6_MACRO_V1_QLIB_FEATURE_CONTRACT_FROZEN = YES
P6_MACRO_V1_FEATURES = macro_v1_cpiaucsl_d2_log,macro_v1_unrate_d1
P6_AQ_MACRO_FEATURE_ENGINE_CREATED = NO
P6_AQ_MACRO_TRANSFORMATION_ENGINE_CREATED = NO
P6_MACRO_V1_UPSTREAM_NATIVE_COMPOSITION_POC = PASS
P6_VINTAGE_PUBLIC_API_USED = YES
P6_XNYS_EXISTING_LEAF_REUSED = YES
P6_DUCKDB_COMPOSITION_OWNER = YES
P6_PANDERA_BOUNDARY_VALIDATION = PASS
P6_REVISION_BACKWARD_LEAKAGE_COUNT = 0
P6_GLOBAL_MACRO_NATIVE_QLIB_SUPPORT = NO
P6_GLOBAL_TO_INSTRUMENT_MECHANISM = DUCKDB_MECHANICAL_BROADCAST
P6_INSTRUMENT_DEPENDENT_MACRO_VALUE_COUNT = 0
P6_MANUFACTURED_INSTRUMENT_SESSION_ROW_COUNT = 0
P6_QLIB_VERSION = 0.9.8.dev26
P6_QLIB_SOURCE_IDENTITY = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
P6_QLIB_ROUNDTRIP_EQUALITY = PASS
P6_MACRO_V1_PROVENANCE_RECOVERABILITY = PASS
P6_MACRO_V1_DETERMINISM = PASS
P6_MACRO_V1_PRIVATE_EVIDENCE_CHECKSUMS_SHA256 = 29cf981db3501ac7894d29ff00749deb9f9bee9183d32054ee01e413a5246a3d
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_V1_MINIMAL_PRODUCTION_MATERIALIZATION_001
CURRENT_DEVELOPMENT_NEXT_GATE = MACRO_V1_UPSTREAM_NATIVE_COMPOSITION_POC_PASS
```

### P6 Macro V1 minimal production materialization (2026-09-25)

The frozen two-feature macro surface is now materialized as a session-global
artifact. Vintage 0.9.0 supplies official FRED/ALFRED PIT evidence, the existing
XNYS leaf supplies sessions, DuckDB owns relational composition, and Pandera and
PyArrow own validation and Parquet storage. The only downstream instrument
expansion proven is a consumer-side mechanical DuckDB join; it is not retained
as canonical history.

```text
P6_MACRO_V1_MINIMAL_PRODUCTION_MATERIALIZATION = PASS
P6_MACRO_V1_PRODUCTION_LOCATION = 20-intelligence-system/macro-factors/macro-v1
P6_MACRO_V1_OUTPUT_ROOT = D:/AQ_DATA/P6/macro-v1-001
P6_MACRO_V1_CANONICAL_STORAGE_GRAIN = SESSION_GLOBAL
P6_MACRO_V1_PERMANENT_INSTRUMENT_BROADCAST_STORAGE = NO
P6_MACRO_V1_FEATURES = macro_v1_cpiaucsl_d2_log,macro_v1_unrate_d1
P6_MACRO_V1_SESSION_BOUNDS = 2015-04-01..2024-12-31
P6_MACRO_V1_SOURCE_AS_OF = 2024-12-31
P6_MACRO_V1_EVIDENCE_ROWS = 745
P6_MACRO_V1_SESSION_ROWS = 2455
P6_MACRO_V1_PROVENANCE_ROWS = 611
P6_MACRO_V1_EVIDENCE_LOGICAL_SHA256 = 281ca7ff1a18700ad1453d62d4a2f239690cedb97c413ee4639acd4766899866
P6_MACRO_V1_STATE_LOGICAL_SHA256 = 3dbb88c1529d259b6447fc3f2e6e2d9124efa2bce8466b12b43f631a849d20fc
P6_MACRO_V1_PROVENANCE_LOGICAL_SHA256 = 4974edca45e48e67e61446341ba1cf3fdb037e41b5878c95ea13e9321512e55a
P6_MACRO_V1_MANIFEST_SHA256 = 23dee6c4430d68e26068305f3e929a3c2cba59d30dd38d5ba97fd1fe6e39e44c
P6_MACRO_V1_DVC_STAGE = p6_macro_v1_materialization
P6_MACRO_V1_DVC_STATUS = UP_TO_DATE
P6_MACRO_V1_PROVENANCE_RECOVERABILITY = PASS
P6_MACRO_V1_DETERMINISM = PASS_LOGICAL_AND_PHYSICAL
P6_MACRO_V1_REAL_OUTPUT_BROADCAST_CANARY = PASS
P6_MACRO_V1_QLIB_REAL_OUTPUT_CANARY = PASS
P6_MACRO_V1_PRODUCTION_PYTHON_LOC = 153
P6_AQ_NEW_GENERIC_ENGINE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_V1_ABLATION_PROTOCOL_FREEZE_001
CURRENT_DEVELOPMENT_NEXT_GATE = MACRO_V1_MINIMAL_PRODUCTION_MATERIALIZATION_PASS
```

### P6 Macro V1 ablation protocol freeze (2026-09-25)

Macro V1 has exactly one preregistered historical comparison: `BASE_157`
versus `BASE_157 + EXACT_MACRO_V1_2`. P5 fundamentals are not part of either
surface. The accepted P5 Attempt-005 Qlib/LightGBM, strategy, temporal CV, and
arch settings remain unchanged. No fit, prediction, backtest, metric
inspection, or ablation was executed while freezing this authority.

```text
P6_MACRO_V1_ABLATION_PROTOCOL = FROZEN_PRE_EXECUTION
P6_MACRO_V1_ABLATION_PROTOCOL_SHA256 = 5aad8128f9473558689b602edc91850022b0667826ee0dd8eb126fab7c58b116
P6_MACRO_V1_CONTROL_SURFACE = BASE_157
P6_MACRO_V1_CONTROL_FEATURE_COUNT = 157
P6_MACRO_V1_CONTROL_FEATURE_MANIFEST_SHA256 = 7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463
P6_MACRO_V1_CONTROL_DATASET_IDENTITY = P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135
P6_MACRO_V1_P5_FUNDAMENTALS_INCLUDED_IN_BASELINE = NO
P6_MACRO_V1_SURFACE_M0 = BASE_157
P6_MACRO_V1_SURFACE_M1 = BASE_157_PLUS_EXACT_MACRO_V1_2
P6_MACRO_V1_SCIENTIFIC_HYPOTHESIS_COUNT = 1
P6_MACRO_V1_PRIMARY_SURFACE_COMPARISON_COUNT = 1
P6_MACRO_V1_MODEL_CONFIG_SHA256 = f75355629e7ad6b85f100627dbc055712d7f72d1e1e31783736f1ce4cc10a61a
P6_MACRO_V1_PRIMARY_METRIC = QLIB_RANK_IC
P6_MACRO_V1_PRIMARY_DIRECTION = M1_MINUS_M0
P6_MACRO_V1_CLASSIFICATION_SET = INCREMENTAL_VALUE_SUPPORTED,DEGRADED,NO_MEASURABLE_INCREMENTAL_VALUE,INCONCLUSIVE
P6_MACRO_V1_MODEL_TRAINING_COUNT = 0
P6_MACRO_V1_PREDICTION_COUNT = 0
P6_MACRO_V1_BACKTEST_COUNT = 0
P6_MACRO_V1_ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_V1_FIRST_AUTHORIZED_ABLATION_EXECUTION_001
CURRENT_DEVELOPMENT_NEXT_GATE = MACRO_V1_ABLATION_PROTOCOL_FROZEN
```

### P6 Macro V1 first authorized ablation result (2026-09-25)

The sole preregistered family comparison completed on identical 1,196,594-row
surfaces. `M1` added only the two canonical Macro V1 columns and produced a
lower test Rank IC than `M0`; neither the complete forward support condition
nor the complete reverse degraded condition passed. The frozen classification
is `NO_MEASURABLE_INCREMENTAL_VALUE`. Macro V1 is closed without search and its
materialization is retained as historical evidence only.

```text
P6_MACRO_V1_M0_TEST_RANK_IC = 0.0021911029598144574
P6_MACRO_V1_M1_TEST_RANK_IC = 0.001851944467966326
P6_MACRO_V1_RANK_IC_DELTA = -0.00033915849184813144
P6_MACRO_V1_M1_MINUS_M0_WALKFORWARD_GATE = FALSE
P6_MACRO_V1_M0_MINUS_M1_WALKFORWARD_GATE = TRUE
P6_MACRO_V1_M1_MINUS_M0_CPCV_GATE = FALSE
P6_MACRO_V1_M0_MINUS_M1_CPCV_GATE = FALSE
P6_MACRO_V1_M1_MINUS_M0_SPA_PVALUE = 0.4356
P6_MACRO_V1_M1_MINUS_M0_REALITY_CHECK_PVALUE = 0.4356
P6_MACRO_V1_M0_MINUS_M1_SPA_PVALUE = 0.5644
P6_MACRO_V1_M0_MINUS_M1_REALITY_CHECK_PVALUE = 0.5644
P6_MACRO_V1_FINAL_SCIENTIFIC_CLASSIFICATION = NO_MEASURABLE_INCREMENTAL_VALUE
P6_MACRO_V1_POST_RESULT_STATUS = HISTORICAL_EVIDENCE_ONLY_QUESTION_CLOSED
P6_MACRO_V1_MODEL_FIT_ATTEMPT_COUNT = 2
P6_MACRO_V1_MODEL_FIT_COMPLETED_COUNT = 2
P6_MACRO_V1_PREDICTION_COUNT = 2
P6_MACRO_V1_BACKTEST_SURFACE_COUNT = 2
P6_MACRO_V1_ABLATION_COUNT = 1
P6_MACRO_V1_P5_FUNDAMENTAL_FEATURE_VALUE_COUNT = 0
P6_MACRO_V1_CONTROL_PLANE_INTERRUPTION_COUNT = 1
P6_MACRO_V1_CONTROL_PLANE_INTERRUPTION_CLASSIFICATION = CODEX_AUTH_401_PRE_SCIENTIFIC_EXECUTION
P6_MACRO_V1_PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/macro-v1-ablation-001/attempt-001
P6_MACRO_V1_PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 05383ece11ddc5ecbe26fb025323e5ffc810f9c4347f4f0552e37911128b980d
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P6_MACRO_V1_NEGATIVE_RESULT_CLOSEOUT_001
```

### P6 Macro V1 terminal negative-result closeout (2026-09-25)

The sole preregistered Macro V1 family did not demonstrate measurable
incremental value over `BASE_157`. This conclusion applies only to the exact
two-feature family and frozen protocol. Macro V1 is retired from every active
candidate and production path without rescue search; its code, materialized
artifacts, and ablation evidence remain historical reproducibility references.
P6 remains active and advances to the news evidence-policy lane.

```text
P6_MACRO_V1_FINAL_CLASSIFICATION = NO_MEASURABLE_INCREMENTAL_VALUE
P6_MACRO_V1_ACTIVE = NO
P6_MACRO_V1_CANDIDATE_ELIGIBLE = NO
P6_MACRO_V1_PROMOTION_ELIGIBLE = NO
P6_MACRO_V1_RESEARCH_QUESTION_CLOSED = YES
P6_MACRO_V1_MATERIALIZATION_ROLE = HISTORICAL_EVIDENCE_ONLY
P6_MACRO_V1_ACTIVE_DVC_STAGE = NO
P6_MACRO_V1_ACTIVE_DVC_DOWNSTREAM_DEPENDENCY_COUNT = 0
P6_MACRO_V1_ACTIVE_FEATURE_CONSUMER_COUNT = 0
P6_MACRO_V1_FURTHER_SEARCH_AUTHORIZED = NO
P6_MACRO_V1_CPI_ONLY_RETEST_AUTHORIZED = NO
P6_MACRO_V1_UNRATE_ONLY_RETEST_AUTHORIZED = NO
P6_MACRO_V1_GDP_AUTHORIZED = NO
P6_MACRO_V1_GDPC1_AUTHORIZED = NO
P6_MACRO_V1_MORE_SERIES_AUTHORIZED = NO
P6_MACRO_V1_ALTERNATE_TRANSFORM_AUTHORIZED = NO
P6_MACRO_V1_LAG_TUNING_AUTHORIZED = NO
P6_MACRO_V1_MODEL_TUNING_AUTHORIZED = NO
P6_MACRO_V1_HYPERPARAMETER_SEARCH_AUTHORIZED = NO
P6_MACRO_V1_HISTORICAL_ARTIFACT_RETAINED = YES
P6_MACRO_V1_ABLATION_EVIDENCE_RETAINED = YES
P6_MACRO_V1_PRIVATE_MATERIALIZATION_MANIFEST_SHA256 = 23dee6c4430d68e26068305f3e929a3c2cba59d30dd38d5ba97fd1fe6e39e44c
P6_MACRO_V1_ABLATION_EVIDENCE_CHECKSUM_SHA256 = 05383ece11ddc5ecbe26fb025323e5ffc810f9c4347f4f0552e37911128b980d
POST_MACRO_CONTROL_SURFACE = BASE_157
POST_MACRO_CONTROL_FEATURE_COUNT = 157
P6_ACTIVE = YES
P6_MACRO_V1_LANE = CLOSED_NEGATIVE
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_EVIDENCE_AND_SAFE_AVAILABILITY_POLICY_FREEZE_001
```

### P6 News V1 evidence and safe-availability authority (2026-09-25)

News V1 does not require or claim a universal exact first-publication time. Its
admission authority is a conservative upstream observation: an accepted
archive/capture/processing event proving that the exact document URL existed
no later than that event. Publication dates remain metadata only unless a
provider-specific contract is separately proven.

The primary historical candidate is raw GDELT GKG 2.1, restricted to source
collection `1` (`WEB`). The official codebook defines `GKGRECORDID` as the
unique record identity whose prefix is the full date/time of the 15-minute
batch in which the record was created, while `V2.1DATE` is the document's
publication date. The codebook does not normatively define the record-prefix
timezone. GDELT is therefore admitted only at date precision: the first XNYS
session strictly after the batch calendar date. It is not admitted as an
intraday UTC timestamp.

Official master metadata and two tiny boundary samples established availability
over the required 2015-04-01 through 2024-12-31 range. Each sample contained 27
columns and only `WEB` rows in the bounded sample. Organizations and themes
were present but legitimately sparse; tone and GCAM were present in every
sampled row. This is evidence-policy validation, not a corpus build or feature
selection.

For an exact same URL, the tightest conservative authority is the earliest
qualified capture/processing observation, with its original precision and
semantics retained. Date-only observations are not ordered as intraday events,
and no fuzzy-title or approximate-URL join is allowed. A timezone-aware instant
uses the existing daily timing rule: first XNYS session whose market open is
strictly later. A date-only or timezone-unproven observation uses the more
conservative first XNYS session strictly after its calendar date.

```text
NEWS_EXACT_FIRST_AVAILABLE_AT = NOT_REQUIRED_NOT_UNIVERSALLY_PROVABLE
GDELT_GKG_ROLE = PRIMARY_HISTORICAL_SAFE_AVAILABILITY_EVIDENCE_CANDIDATE
GDELT_GKG_RECORD_ID_SEMANTICS = UNIQUE_RECORD_ID_WITH_15_MINUTE_CREATION_BATCH_PREFIX_NOT_PUBLICATION_TIME
GDELT_GKG_BATCH_TIMEZONE = UNPROVEN
GDELT_GKG_SAFE_AVAILABILITY_STATUS = PASS_DATE_ONLY_CONSERVATIVE
GDELT_GKG_HISTORICAL_COVERAGE_STATUS = PASS_2015_04_01_THROUGH_2024_12_31_BOUNDARY_VERIFIED
GDELT_WEB_SOURCE_COLLECTION_ONLY = YES
GDELT_DOC_ROLE = SUPPLEMENTARY_QUERY_INTERFACE
OPENBB_NEWS_ROLE = NEWS_PROVIDER_GATEWAY
OPENBB_PUBLISHED_AT_ADMISSION_AUTHORITY = NO
MEDIA_CLOUD_ROLE = SUPPLEMENTARY_SAFE_AVAILABILITY_AUTHORITY
MEDIA_CLOUD_INDEXED_DATE_SEMANTICS = CONSERVATIVE_CAPTURE_PROCESSING_UPPER_BOUND
COMMON_CRAWL_ROLE = SUPPLEMENTARY_CAPTURE_PROVENANCE_LEAF
COMMON_CRAWL_CAPTURE_TIMESTAMP_SEMANTICS = ARCHIVE_CAPTURE_TIME_FOR_KNOWN_URL_NOT_PUBLICATION_OR_DISCOVERY
NEWS_SAFE_AVAILABLE_AT_POLICY = EARLIEST_QUALIFIED_PROVEN_CAPTURE_OR_PROCESSING_OBSERVATION_FOR_EXACT_SAME_URL_PRECISION_PRESERVED
NEWS_SESSION_VISIBILITY_POLICY = AWARE_INSTANT_FIRST_XNYS_OPEN_STRICTLY_AFTER_INSTANT_ELSE_FIRST_XNYS_SESSION_STRICTLY_AFTER_CALENDAR_DATE
NEWS_FULL_TEXT_REQUIRED_FOR_EVIDENCE = NO
GDELT_NATIVE_ORGANIZATION_METADATA = UPSTREAM_NATIVE_PARTIAL_NOT_SECURITY_IDENTITY
GDELT_NATIVE_THEME_METADATA = UPSTREAM_NATIVE_USABLE_AS_EVIDENCE_METADATA
GDELT_NATIVE_TONE_GCAM_METADATA = TONE_UPSTREAM_NATIVE_USABLE_GCAM_CHALLENGER_ONLY_NO_DIMENSION_SELECTED
LANGEXTRACT_REQUIRED_FOR_NEWS_V1_EVIDENCE = NO
FINBERT_REQUIRED_FOR_NEWS_V1_EVIDENCE = NO
NEWS_ENTITY_TO_AQ_SECURITY_BINDING = UNRESOLVED_SEPARATE_POLICY
AQ_NEWS_CRAWLER_CREATED = NO
AQ_NEWS_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_SEALED_OOS_RESULT_USED = NO
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_GDELT_GKG_HISTORICAL_SAFE_AVAILABILITY_POC_001
```

### P6 News V1 raw GKG historical safe-availability POC (2026-09-25)

The bounded real-data POC promoted the raw GDELT GKG 2.1 archive to the primary
historical news safe-availability evidence leaf. Five frozen date anchors and
three adjacent 2022-01-03 batches selected from streamed official master
metadata totaled 46,237,000 compressed bytes. All eight archives matched their
advertised size and MD5; no full master list or archive entered Git.

Across 11,750 rows, 11,749 decoded strictly as UTF-8 and contained exactly the
official 27 fields. One source row failed strict UTF-8 decoding and was counted
as malformed, then excluded without replacement or repair. Every valid row was
`WEB`, had a non-empty exact URL, passed the official record-ID grammar, and
matched its file batch prefix. The four-batch exact-URL probe found 2,875 unique
URLs and no repeated exact URL; that zero result is retained rather than widened
with fuzzy identity.

The existing `aq_xnys_calendar` leaf mapped the five dates to 2015-04-02,
2017-07-05, 2020-03-16, 2022-01-04, and 2025-01-02 respectively. Therefore no
2024-12-31 GKG record becomes visible inside the 2024 research cutoff. Two
normalization passes over the same verified archives were identical. GKG batch
time remains timezone-unproven and date-only; publication metadata never acts
as a fallback.

```text
HISTORICAL_NEWS_SAFE_AVAILABILITY_OWNER = GDELT_GKG_2_1_RAW_ARCHIVE
GDELT_GKG_OWNER_DECISION = SELECTED_PRIMARY_HISTORICAL_NEWS_EVIDENCE_LEAF
SELECTED_GKG_FILE_COUNT = 8
SELECTED_GKG_COMPRESSED_BYTES = 46237000
GDELT_SELECTED_FILE_INTEGRITY = PASS
EXPECTED_MAJOR_FIELD_COUNT = 27
TOTAL_ANALYZED_ROW_COUNT = 11750
VALID_27_FIELD_ROW_COUNT = 11749
MALFORMED_ROW_COUNT = 1
WEB_ROW_COUNT = 11749
NON_WEB_EXCLUDED_ROW_COUNT = 0
INVALID_GKGRECORDID_COUNT = 0
DUPLICATE_GKGRECORDID_COUNT = 0
BATCH_PREFIX_FILE_MATCH_COUNT = 11749
BATCH_PREFIX_FILE_MISMATCH_COUNT = 0
GDELT_BATCH_TIMEZONE = UNPROVEN
SAFE_AVAILABILITY_PRECISION = DATE
FABRICATED_GDELT_INTRADAY_TIMESTAMP_COUNT = 0
EMPTY_WEB_DOCUMENT_IDENTIFIER_COUNT = 0
XNYS_DATE_ONLY_MAPPING_STATUS = PASS
END_BOUNDARY_FUTURE_SESSION_LEAKAGE_COUNT = 0
PUBLISHED_AT_FALLBACK_USED = NO
SOURCE_ARTICLE_REQUEST_COUNT = 0
NORMALIZATION_DETERMINISM = PASS
NEWS_ENTITY_TO_AQ_SECURITY_BINDING = UNRESOLVED_SEPARATE_POLICY
NEWS_FEATURE_FAMILY_SELECTED = NO
AQ_NEWS_CRAWLER_CREATED = NO
AQ_NEWS_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-gdelt-gkg-historical-safe-availability-poc-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = dcca9cfa4e041b5f08c54ae95f7834ea3a3a761685e0790c48fb05f0e8a314f6
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_ENTITY_TO_SECURITY_UPSTREAM_SUBSTITUTION_AUDIT_001
```

### P6 News V1 entity-to-security upstream substitution audit (2026-09-25)

The capability audit selected official SEC Submissions current/former names as
the primary organization-name-to-CIK leaf and the existing P1/P5
EpisodeSecCikBindingV1 ledger as the only CIK-to-episode authority. Valuein
5.2.0 `snapshot_20260918` is supplementary historical security/FIGI
corroboration; EdgarTools name ranking and RapidFuzz are candidate generation
only; OpenFIGI is duplicative security corroboration; GLEIF is nonessential
without a proven CIK bridge; cleanco 2.3 is suffix normalization only. No
organization text may bind directly to ticker, and neither fuzzy scores nor an
LLM may admit a CIK.

The reused SEC `submissions.zip` exactly covers all 711 bound CIKs and exposes
711 current names plus 676 former-name rows. Its SHA-256 remains
`702fbcd8b4335bc649e9e4eab3a202f3effc314b43421664bfecb59365767165`.
However, 11 former-name records have `from > to`, the official API page does
not define interval-boundary inclusion, and current names have no safe inferred
historical start. Those cases fail closed. Normalization also increases alias
collisions: ambiguous cross-CIK keys rise from 1 at raw exact matching to 5
after cleanco suffix removal.

The requested bounded real matching matrix could not run truthfully. The prior
POC retained 2,500 records with an organization-presence boolean but omitted
the organization strings, then deleted the verified source ZIPs. This task
forbids redownloading the GKG corpus. Consequently all reported match counts
are zero-input counts, not evidence of zero failures or zero coverage. The
precise blocker is organization-text retention, not missing custom resolution
logic.

```text
PR95_MERGE_SHA = 1fcd062ba54597c692e832b342f0de883723038b
SEC_SUBMISSIONS_ALIAS_STATUS = SELECTED_PRIMARY_UPSTREAM_LEAF_FULL_711_CIK_COVERAGE
SEC_FORMER_NAMES_DATE_SEMANTICS = FROM_TO_PRESENT_11_INVERTED_BOUNDARY_INCLUSION_UNDOCUMENTED_FAIL_CLOSED
EXISTING_P5_SEC_BULK_REUSED = YES
EXISTING_EPISODE_CIK_AUTHORITY_REUSED = YES
VALUEIN_VERSION = 5.2.0
VALUEIN_SECURITY_SCD2_STATUS = PASS
EDGARTOOLS_NAME_SEARCH_STATUS = CANDIDATE_GENERATION_ONLY
OPENFIGI_STATUS = VALID_BUT_DUPLICATIVE_SUPPLEMENTARY_SECURITY_CORROBORATION
GLEIF_STATUS = VALID_BUT_NONESSENTIAL
COMPANY_NAME_NORMALIZATION_LEAF = CLEANCO_2_3_SUPPLEMENTARY_ONLY
FUZZY_MATCH_AUTO_BIND = NO
LLM_ENTITY_BINDING_AUTHORITY = NO
TOTAL_ORGANIZATION_STRING_COUNT = 0
BOUNDED_MATCH_METRIC_INTERPRETATION = ZERO_ELIGIBLE_INPUT_NOT_ZERO_FAILURE_RATE
NEWS_ENTITY_TO_AQ_SECURITY_BINDING_STATUS = BLOCKED_BOUNDED_REAL_POC_INPUT_NOT_RETAINED
AQ_ENTITY_RESOLUTION_ENGINE_REQUIRED = NO
AQ_NEWS_ENTITY_RESOLVER_CREATED = NO
AQ_GENERIC_IDENTITY_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
NEWS_FEATURE_FAMILY_SELECTED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-entity-to-security-upstream-substitution-audit-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 83a45d07265f3758df33be3b15c2065f25f27faa351cd47d0044c915052d56f2
CURRENT_DEVELOPMENT_NEXT = BLOCKED_RETAINED_GKG_ORGANIZATION_TEXT_UNAVAILABLE
FINAL_CLASSIFICATION = BLOCKED_RETAINED_GKG_SAMPLE_LACKS_ORGANIZATION_TEXT
```

### P6 News V1 entity-resolution upstream deployment POC (2026-09-25)

The recovered `V1ORGANIZATIONS` evidence closed the prior input blocker without
redownloading GKG. A deterministic first-500 exact-string sample was passed
unchanged to `cyanheads/secedgar-mcp-server` `0.15.1`. Its public native result
does not expose whether name resolution used exact, former-name, prefix, or
substring matching, so it is selected only as a candidate-generation leaf. It
returned 459 no-match, 34 unique-CIK, and 7 multi-CIK results with zero runtime
errors; exact-classifiable result count is zero.

`john-friedman/datamule-data` at
`a68aa57c641db777ffd860a0c8befbe740048c58` is selected as the exact historical
alias-relation owner. DuckDB raw case-sensitive equality produced zero matches
for the lower-case GKG sample. No AQ case folding, suffix handling, fuzzy
matching, manual dictionary, or alias table was introduced. Consequently 34
unique MCP candidates remain historical-start-unproven, seven are ambiguous,
and zero episode bindings are admitted. This is fail-closed low recall, not an
authorization to create an AQ entity resolver.

```text
RECOVERED_ORGANIZATION_EVIDENCE_SHA256 = 4d5651b76d5e5941cf1f837c579c35c9288cb4ecda0b7b59c0faf4139578816e
BOUNDED_ORGANIZATION_SAMPLE_COUNT = 500
SECEDGAR_VERSION = 0.15.1
SECEDGAR_SOURCE_SHA = e356eb4db3c5027862e5e78afdd88d05c1867652
SECEDGAR_STATUS = SELECTED_CANDIDATE_GENERATION_LEAF
SECEDGAR_ZERO_RESULT_COUNT = 459
SECEDGAR_UNIQUE_CIK_RESULT_COUNT = 34
SECEDGAR_MULTI_CIK_RESULT_COUNT = 7
SECEDGAR_EXACT_CLASSIFIABLE_COUNT = 0
SECEDGAR_NONEXACT_OR_UNKNOWN_MATCH_CLASS_COUNT = 41
DATAMULE_SOURCE_SHA = a68aa57c641db777ffd860a0c8befbe740048c58
DATAMULE_DATA_IDENTITY = 82ab4b7b7ce45108ca0f69324c414c2d2b3c18dc393c5c67f359e5ae21df77d4
DATAMULE_STATUS = SELECTED_HISTORICAL_ALIAS_RELATION_OWNER
DATAMULE_EXACT_ALIAS_MATCH_COUNT = 0
DATAMULE_UNIQUE_CIK_MATCH_COUNT = 0
DATAMULE_AMBIGUOUS_CIK_MATCH_COUNT = 0
DATAMULE_NO_MATCH_COUNT = 500
UPSTREAM_AGREE_UNIQUE_CIK_COUNT = 0
UPSTREAM_CONFLICT_COUNT = 0
CURRENT_NAME_HISTORICAL_START_UNPROVEN_COUNT = 34
HISTORICALLY_VALID_UNIQUE_CIK_COUNT = 0
IDENTITY_CONFLICT_COUNT = 7
FINAL_ADMITTED_AQ_EPISODE_COUNT = 0
SELECTED_ENTITY_RESOLUTION_MECHANICS_OWNER = SECEDGAR_MCP_SERVER_0_15_1_CANDIDATE_GENERATION_ONLY
SELECTED_HISTORICAL_ALIAS_RELATION_OWNER = DATAMULE_DATA_A68AA57_EXACT_RAW_RELATION
AQ_ENTITY_RESOLUTION_ENGINE_REQUIRED = NO
AQ_HISTORICAL_ALIAS_POLICY_LOC_ESTIMATE = 26
AQ_NEWS_ENTITY_RESOLVER_CREATED = NO
AQ_NAME_NORMALIZATION_ENGINE_CREATED = NO
AQ_FUZZY_MATCHER_CREATED = NO
AQ_ALIAS_DATABASE_BUILDER_CREATED = NO
AQ_GENERIC_IDENTITY_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
NEWS_FEATURE_FAMILY_SELECTED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-entity-resolution-upstream-deployment-poc-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = b204820eb43f2baabce073fa10d06824ed6ccfd02440d817b320f830f3b830c2
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_ENTITY_BINDING_POLICY_FREEZE_001
FINAL_CLASSIFICATION = PASS_P6_NEWS_V1_ENTITY_RESOLUTION_UPSTREAM_DEPLOYMENT_POC
```

### P6 News V1 OpenCorporates/Wikidata upstream substitution POC (2026-09-25)

PR #97 was squash-merged at
`983c8abb0291b7ea727c14697785d17d92164b64`. The stronger whole-path audit found
OpenCorporates semantically suitable, but its API and reconciliation service
require a token, the default allowance is only 50 requests/day and 200/month,
and the open-data plan carries ODbL attribution/share-alike obligations. No
authorized token was present, so no live request or HTML scraping occurred.

The same 500 raw strings were tested through Wikidata's public Action API. It
returned 80 unique items, 208 multi-item results, and 212 no-matches, with zero
runtime errors. Four unique items had P5531 CIKs and all four passed frozen SEC
validation, but none carried date-valid name semantics covering the news date.
OpenTapioca was frozen at source commit
`977a4f0409f06b90b9fc34645147ab5d8f460ef1`; its live domain had no A/AAAA
record and a local equivalent requires its pretrained model and Solr index, so
it remains a blocked candidate-generation-only challenger.

No episode was admitted. The operational policy-freeze gate therefore remains
closed, and no AQ resolver or normalization stack is resumed.

```text
PR97_MERGE_SHA = 983c8abb0291b7ea727c14697785d17d92164b64
OPENCORPORATES_ACCESS_STATUS = BLOCKED_CREDENTIAL_REQUIRED
OPENCORPORATES_LICENSE_STATUS = ODBL_SHARE_ALIKE_OPEN_DATA_OR_PAID_NON_SHARE_ALIKE; PRIVATE_PLAN_COMPATIBILITY_UNPROVEN
OPENCORPORATES_RECONCILIATION_STATUS = BLOCKED_CREDENTIAL_REQUIRED_STATIC_SEMANTICS_PASS
OPENCORPORATES_INPUT_COUNT = 500_NOT_SENT
OPENCORPORATES_RESOLVED_ENTITY_COUNT = 0_NOT_MEASURED
OPENCORPORATES_US_SEC_CIK_COUNT = 0_NOT_MEASURED
OPENCORPORATES_HISTORICALLY_VALID_NAME_COUNT = 0_NOT_MEASURED
OPENCORPORATES_MULTI_CIK_CONFLICT_COUNT = 0_NOT_MEASURED
OPENCORPORATES_NO_CIK_COUNT = 0_NOT_MEASURED
WIKIDATA_UNIQUE_ITEM_COUNT = 80
WIKIDATA_P5531_CIK_COUNT = 4
WIKIDATA_MULTI_ITEM_COUNT = 208
WIKIDATA_NO_MATCH_COUNT = 212
WIKIDATA_RUNTIME_ERROR_COUNT = 0
SEC_CIK_VALIDATION_PASS_COUNT = 4
SEC_CIK_CONFLICT_COUNT = 0
OPENTAPIOCA_VERSION = 0.1.2_PACKAGE_METADATA
OPENTAPIOCA_SOURCE_SHA = 977a4f0409f06b90b9fc34645147ab5d8f460ef1
OPENTAPIOCA_STATUS = BLOCKED_RUNTIME_CANDIDATE_GENERATION_ONLY
FINAL_ADMITTED_AQ_EPISODE_COUNT = 0
SELECTED_NEWS_ENTITY_UPSTREAM_STACK = NONE_OPERATIONALLY_SUFFICIENT
SECEDGAR_ACTIVE_ROLE_AFTER_POC = DIAGNOSTIC_CANDIDATE_GENERATION_ONLY_NOT_ACTIVE
DATAMULE_ACTIVE_ROLE_AFTER_POC = DIAGNOSTIC_EXACT_ALIAS_RELATION_ONLY_NOT_ACTIVE
AQ_ENTITY_RESOLUTION_ENGINE_REQUIRED = NO
AQ_NAME_NORMALIZATION_ENGINE_CREATED = NO
AQ_FUZZY_MATCHER_CREATED = NO
AQ_ALIAS_DATABASE_BUILDER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
NEWS_FEATURE_FAMILY_SELECTED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-opencorporates-wikidata-upstream-substitution-poc-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = cea565c735fe3a2013f851a83b6615858b642496db7f7e5bdbfeac663aae90c5
CURRENT_DEVELOPMENT_NEXT = BLOCKED_OPENCORPORATES_CREDENTIAL_US_SEC_CIK_COVERAGE_AND_HISTORICAL_NAME_DATE_AUTHORITY
FINAL_CLASSIFICATION = BLOCKED_OPENCORPORATES_CREDENTIAL_US_SEC_CIK_COVERAGE_AND_HISTORICAL_NAME_DATE_AUTHORITY
```

### P6 News V1 real-time upstream streaming stack POC (2026-09-25)

PR #98 squash-merged the superseded entity-resolution diagnostic at
`fec1fab07e0be1bf7c446a8bb58d7c861e6bd70b`. The architecture is now reset:
real-time company-news identity is provider-owned through Alpaca/Benzinga
native `symbols[]`; no organization-string resolver is required.

The isolated `alpaca-py 0.44.0` runtime proved the native
`NewsDataStream.subscribe_news(handler, "*")` surface and upstream-owned
reconnect mechanics without opening a socket. No authorized Alpaca credential
pair was available, so connection, authentication, live messages, and FinBERT
inference were correctly not attempted. The already-pinned Transformers
`5.17.0` plus `ProsusAI/finbert` revision
`4556d13015211d73dccd3fdd39d39232506f3e43` was verified in place.

The independent official-event lane passed: `feedparser 6.0.12` read 20 Federal
Reserve feed entries and one BLS feed entry while retaining source timestamps
separately from actual AQ UTC observation time. EdgarTools `5.58.0` exposes the
native current-filings interface, but its private SEC identity is absent, so
the POC made zero SEC requests and recorded the exact blocker.

```text
P6_NEWS_COMPANY_ENTITY_RESOLUTION_LANE = CLOSED_NOT_REQUIRED_FOR_REALTIME_COMPANY_NEWS
ALPACA_PY_VERSION = 0.44.0
ALPACA_CREDENTIAL_AVAILABLE = NO
ALPACA_STREAM_CONNECTION_STATUS = NOT_ATTEMPTED_CREDENTIAL_REQUIRED
ALPACA_STREAM_AUTH_STATUS = NOT_ATTEMPTED_CREDENTIAL_REQUIRED
ALPACA_STREAM_SUBSCRIPTION_STATUS = STATIC_INTERFACE_PROVEN_LIVE_BLOCKED_CREDENTIAL_REQUIRED
ALPACA_SUBSCRIPTION = *
LIVE_OBSERVATION_MINUTES = 0
LIVE_MESSAGES_TOTAL = 0
ANALYZED_LIVE_MESSAGE_COUNT = 0
COMPANY_NEWS_SECURITY_ASSOCIATION_OWNER = ALPACA_BENZINGA_PROVIDER_NATIVE_SYMBOLS
CUSTOM_WEBSOCKET_RECONNECT_CODE = NO
FINBERT_VERSION = TRANSFORMERS_5.17.0
FINBERT_MODEL_REVISION = 4556d13015211d73dccd3fdd39d39232506f3e43
LANGEXTRACT_INFERENCE_COUNT = 0
LLM_CALL_COUNT = 0
FED_FEED_ACCESS = PASS
FED_LATEST_ITEM_COUNT = 20
BLS_FEED_ACCESS = PASS
BLS_LATEST_ITEM_COUNT = 1
RSS_ATOM_PARSER_OWNER = FEEDPARSER
RSS_ATOM_PARSER_VERSION = 6.0.12
SEC_CURRENT_FILINGS_OWNER = EDGARTOOLS_NATIVE_CURRENT_FILINGS
SEC_CURRENT_FILINGS_POC_STATUS = BLOCKED_PRIVATE_EDGAR_IDENTITY_REQUIRED
SEC_CURRENT_FILINGS_RECORD_COUNT = 0
REALTIME_COMPANY_NEWS_OWNER = BLOCKED_CREDENTIAL_REQUIRED
FINANCIAL_SENTIMENT_OWNER = TRANSFORMERS_PLUS_PINNED_PROSUSAI_FINBERT
OFFICIAL_MACRO_EVENT_OWNER = FED_BLS_NATIVE_FEEDS
REALTIME_NEWS_PUSH_ARCHITECTURE = UPSTREAM_OWNED
AQ_NEWS_CRAWLER_REQUIRED = NO
AQ_WEBSOCKET_ENGINE_REQUIRED = NO
AQ_ENTITY_RESOLUTION_ENGINE_REQUIRED = NO
AQ_SENTIMENT_MODEL_REQUIRED = NO
AQ_RSS_PARSER_REQUIRED = NO
POC_BACKGROUND_PROCESS_COUNT_AFTER_CLOSE = 0
NEW_PRODUCTION_LOC = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEWS_FEATURE_FAMILY_SELECTED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
ORDER_COUNT = 0
BROKER_ACTION_COUNT = 0
CAPITAL_AT_RISK = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-realtime-upstream-streaming-stack-poc-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 72e95f0b6ed4442340a369804bf8d5460fb70e13a47bdbe392214ddd4b81571f
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_ALPACA_ACCESS_AND_MACHINE_READABLE_SIGNAL_DECISION_001
FINAL_CLASSIFICATION = PASS_WITH_ALPACA_LIVE_CREDENTIAL_BLOCKER
```

See [P6 News V1 real-time upstream streaming stack POC 001](p6-news-v1-realtime-upstream-streaming-stack-poc-001.md).

### P6 News V1 real-time access closure and live observation (2026-09-26)

PR #99 was squash-merged at
`c2b9d4ac6a4d1e957cf61c1c31613af40799d01d`. The owner-supplied Alpaca Paper
credential was found in the explicitly approved D-drive root search and used
process-locally through `alpaca-py 0.44.0`. One official `NewsDataStream`
connected, authenticated, subscribed to `*`, remained valid for 5.02 minutes,
and closed cleanly. No message arrived during the bounded window, so no
synthetic evidence or FinBERT result was created.

The three plaintext API files found at the D-drive root were consolidated with
the prior credentials in the existing current-user DPAPI-protected local
secret store. DPAPI round-trip and restricted-ACL checks passed; all three
root plaintext files were then deleted. No secret value, hash, fingerprint,
prefix, or suffix entered evidence, documentation, logs, or Git.

The independent SEC blocker is closed. The existing private `0600`
`EDGAR_IDENTITY` file was injected process-locally into EdgarTools `5.58.0`,
which completed one native `8-K`, page-size-20 current-filings call and returned
20 records. The identity string is absent from evidence and Git. No watcher,
poller, parser, scheduler, or filing NLP was created.

```text
ALPACA_PY_VERSION = 0.44.0
ALPACA_CREDENTIAL_AVAILABLE = YES
ALPACA_STREAM_CONNECTION_STATUS = PASS
ALPACA_STREAM_AUTH_STATUS = PASS
ALPACA_STREAM_SUBSCRIPTION_STATUS = PASS_REQUEST_SENT_ZERO_MESSAGES
ALPACA_REAL_LIVE_STREAM = PASS
LIVE_OBSERVATION_MINUTES = 5.019545533333333
REAL_MESSAGE_COUNT = 0
LIVE_MESSAGES_WITH_SYMBOLS = 0
LIVE_MESSAGES_MATCHING_DEV_UNIVERSE = 0
LIVE_SYMBOLS_NOT_IN_DEV_UNIVERSE = 0
LIVE_SAFE_AVAILABILITY_AUTHORITY = AQ_RECEIVED_AT_UTC
FABRICATED_RECEIVE_TIMESTAMP_COUNT = 0
FINBERT_REAL_MESSAGE_ANALYSIS = NOT_RUN
FINBERT_ANALYZED_MESSAGE_COUNT = 0
D_ROOT_PLAINTEXT_API_FILE_COUNT_AFTER_MIGRATION = 0
DPAPI_SECRET_MIGRATION_STATUS = PASS
SEC_IDENTITY_CONFIGURED = YES
SEC_CURRENT_FILINGS_OWNER = EDGARTOOLS_NATIVE_CURRENT_FILINGS
SEC_CURRENT_FILINGS_POC_STATUS = PASS
SEC_CURRENT_FILINGS_RECORD_COUNT = 20
FED_FEED_ACCESS = PASS
BLS_FEED_ACCESS = PASS
RSS_ATOM_PARSER_OWNER = FEEDPARSER_6_0_12
AQ_NEWS_CRAWLER_REQUIRED = NO
AQ_WEBSOCKET_ENGINE_REQUIRED = NO
AQ_ENTITY_RESOLUTION_ENGINE_REQUIRED = NO
AQ_SENTIMENT_MODEL_REQUIRED = NO
AQ_RSS_PARSER_REQUIRED = NO
NEW_PRODUCTION_LOC = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEWS_FEATURE_FAMILY_SELECTED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
ORDER_COUNT = 0
BROKER_ACTION_COUNT = 0
CAPITAL_AT_RISK = 0
P2_V2_SEALED_OOS_ACCESSED = NO
POC_BACKGROUND_PROCESS_COUNT_AFTER_CLOSE = 0
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-realtime-access-closure-and-live-observation-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = e31fb1f8a0d2e4bc2ed9e6e7883ede5c588296649eb870114aacf989489aeb33
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_MACHINE_READABLE_SIGNAL_SURFACE_DESIGN_001
FINAL_CLASSIFICATION = PASS_P6_NEWS_V1_REALTIME_ACCESS_CLOSURE_AND_LIVE_OBSERVATION
```

See [P6 News V1 real-time access closure and live observation 001](p6-news-v1-realtime-access-closure-and-live-observation-001.md).

### P6 News V1 historical machine-readable data contract and source freeze (2026-09-26)

P6 has returned to its scientific mainline. Macro V1 is closed with no
measurable incremental value; the real-time News upstream path is sufficiently
proven for P6, while productionization and paper execution are deferred to P9.
The current objective is a PIT-safe historical company-news factor that must
eventually face a frozen ablation against `BASE_157`.

The bounded source POC selected 12 P1 episodes before observing news results:
five ordinary continuous, three ticker/name-change, two inactive/acquired or
delisted, and two overlapping shared-CIK/share-class episodes. Two 14-calendar-
day windows per episode produced 24 deterministic windows. Official
`alpaca-py 0.44.0` historical News calls succeeded for all 24 windows and
returned 174 rows representing 173 unique Benzinga article IDs/URLs. Every row
carried provider-native symbols, and the queried historical ticker appeared in
all 174 rows. No current-ticker fallback or article-body retrieval occurred.

Historical PIT admission nevertheless failed closed. Exact string equality was
required between each Alpaca URL and GDELT GKG `V2DOCUMENTIDENTIFIER`. A
deterministically prioritized GKG scan consumed 267,567,105 of the authorized
268,435,456 compressed bytes without retaining ZIPs or requesting source
articles. It found zero exact matches among the 173 unique URLs. Alpaca
`created_at` and `updated_at` remain provenance-only metadata, so zero articles
are PIT-admissible and `NewsEvidenceV1` is not frozen. URL normalization,
redirect following, timestamp substitution, entity resolution, and feature
design remain prohibited.

```text
ACTIVE_PHASE = P6_NEWS_MACRO_SKILLS
ACTIVE_DEVELOPMENT = P6_NEWS_INFORMATION_INTELLIGENCE
P6_MACRO_V1 = CLOSED_NO_MEASURABLE_INCREMENTAL_VALUE
P6_REALTIME_NEWS_UPSTREAM_POC = SUFFICIENT_DEFER_PRODUCTIONIZATION_TO_P9
REALTIME_NEWS_PRODUCTIONIZATION = DEFERRED_TO_P9
CURRENT_P6_OBJECTIVE = NEWS_V1_HISTORICAL_PIT_DATA_AND_FACTOR_ABLATION
EPISODE_SAMPLE_COUNT = 12
EPISODE_WINDOW_COUNT = 24
ALPACA_PY_VERSION = 0.44.0
ALPACA_HISTORICAL_NEWS_STATUS = PASS_REAL_2015_2024_BOUNDED_WINDOWS
ALPACA_SUCCESSFUL_WINDOW_COUNT = 24
ALPACA_FAILED_WINDOW_COUNT = 0
ALPACA_ARTICLE_COUNT = 174
ALPACA_UNIQUE_ARTICLE_COUNT = 173
ALPACA_ARTICLES_WITH_SYMBOLS = 174
ALPACA_REQUESTED_TICKER_PRESENT_COUNT = 174
ALPACA_REQUESTED_TICKER_ABSENT_COUNT = 0
ALPACA_ARTICLE_URL_PRESENT_COUNT = 174
CURRENT_TICKER_BACKFILL_COUNT = 0
GDELT_URL_MATCH_SEMANTICS = EXACT_STRING_EQUALITY_ONLY
GDELT_ADDITIONAL_COMPRESSED_BYTES = 267567105
GDELT_COMPRESSED_BUDGET_BREACH_COUNT = 0
GDELT_EXACT_URL_MATCH_COUNT = 0
GDELT_EXACT_URL_MATCH_RATE = 0.0
PIT_ADMISSIBLE_ARTICLE_COUNT = 0
PIT_ADMISSIBLE_EPISODE_COUNT = 0
PIT_ADMISSIBLE_WINDOW_COUNT = 0
NEWS_EVIDENCE_V1_CONTRACT_FROZEN = NO
GDELT_COMPANY_ENTITY_RESOLUTION_USED = NO
AQ_ENTITY_RESOLUTION_ENGINE_CREATED = NO
AQ_NEWS_CRAWLER_CREATED = NO
AQ_GENERIC_NEWS_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
NEWS_FEATURE_FAMILY_SELECTED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
ORDER_COUNT = 0
BROKER_ACTION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-historical-machine-readable-data-contract-and-source-freeze-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 49856e97c80db6150b1566c25ee72efa12ee30934d4c9b55eb0a97026908f807
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_HISTORICAL_SOURCE_CLOSEOUT_DECISION_001
FINAL_CLASSIFICATION = BLOCKED_HISTORICAL_SAFE_AVAILABILITY_CORROBORATION
```

See [P6 News V1 historical machine-readable data contract and source freeze 001](p6-news-v1-historical-machine-readable-data-contract-and-source-freeze-001.md).

### P6 News V1 whole-upstream owner selection (2026-09-26)

The Alpaca/Benzinga + GDELT + custom corroboration patchwork is retired. Four
and only four whole paths were audited against company identity, native PIT
time, historical/live consistency, symbol history, access/license, and a legal
Qlib handoff.

RavenPack Company News Factors plus News Analytics is the institutional
reference owner: it natively owns point-in-time company identity, sentiment,
relevance, novelty, event taxonomy, news-volume factors, history, and real-time
delivery. LSEG Machine Readable News plus News Analytics is also a technically
valid whole owner. Both remain commercially access-blocked for AQ because
public pricing and a project-compatible license are unavailable without a
sales/entitlement process.

QuantConnect Benzinga and Tiingo are technically coherent historical/live
stacks backed by the US Equity Security Master. They are not selectable for
the required local Qlib handoff: QuantConnect's public download license limits
data to internal LEAN use and prohibits conversion into another format. AQ
will not reinterpret that boundary or rebuild the prior patchwork.

```text
ACTIVE_PHASE = P6_NEWS_MACRO_SKILLS
P6_MACRO_V1 = CLOSED_NO_MEASURABLE_INCREMENTAL_VALUE
P6_COMPANY_NEWS_PATCHWORK_APPROACH = RETIRED
CURRENT_P6_OBJECTIVE = COMPANY_NEWS_V1_CLOSEOUT_DECISION

RAVENPACK_STATUS = VALID_WHOLE_OWNER_BUT_ACCESS_BLOCKED
LSEG_STATUS = VALID_WHOLE_OWNER_BUT_ACCESS_BLOCKED
QUANTCONNECT_BENZINGA_STATUS = REJECTED_LICENSE_OR_EXPORT_INCOMPATIBLE
QUANTCONNECT_TIINGO_STATUS = REJECTED_LICENSE_OR_EXPORT_INCOMPATIBLE

INSTITUTIONAL_REFERENCE_OWNER = RAVENPACK_COMPANY_NEWS_FACTORS_AND_NEWS_ANALYTICS
DEPLOYABLE_COMPANY_NEWS_OWNER = NONE
SELECTED_COMPANY_NEWS_WHOLE_OWNER = NONE
GDELT_COMPANY_NEWS_GLUE_ROLE = RETIRED
ALPACA_DIRECT_ROLE = REALTIME_DIAGNOSTIC_OR_P9_FALLBACK
FINBERT_ROLE_AFTER_SELECTION = CHALLENGER_ONLY_NO_SELECTED_HISTORICAL_OWNER

AQ_NEWS_ENGINE_CREATED = NO
AQ_ENTITY_RESOLUTION_ENGINE_CREATED = NO
AQ_TIMESTAMP_ENGINE_CREATED = NO
AQ_SECURITY_MASTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
NEWS_ARTICLE_DOWNLOAD_COUNT = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
REALTIME_WEBSOCKET_SESSION_COUNT = 0
ORDER_COUNT = 0
BROKER_ACTION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO

PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/news-v1-whole-upstream-owner-selection-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = f273ed8b89512e9f88ba62d57881de59fa80f59cd1fc0737c21ba2e45b60006c
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_COMPANY_NEWS_ACCESS_OR_CLOSEOUT_DECISION_001
FINAL_CLASSIFICATION = PASS_P6_NEWS_V1_WHOLE_UPSTREAM_OWNER_SELECTION
```

See [P6 News V1 whole-upstream owner selection 001](p6-news-v1-whole-upstream-owner-selection-001.md).

### P6 Company News closeout and Global News handoff (2026-09-26)

Company-specific historical News V1 is closed for this P6 cycle as
`DEFERRED_ACCESS_BLOCKED`. RavenPack remains the institutional reference whole
owner and LSEG remains a valid institutional alternative, but neither is an
active dependency because AQ has no established access/license. QuantConnect
Benzinga and Tiingo remain unusable for the required Qlib conversion under the
public local-download terms. No custom Company News implementation or renewed
multi-provider patchwork is authorized.

Alpaca's prior real-time evidence remains available only as a future P9
fallback or challenger. GDELT GKG 2.1 is activated solely for market/global,
geopolitical, and macro-news context. It does not own company identity, CIK,
or ticker resolution. The existing conservative GDELT date/batch authority is
retained: a date-only observation becomes usable on the first XNYS session
strictly after its safe calendar date; no intraday timestamp is fabricated.

```text
P6_MACRO_V1 = CLOSED_NO_MEASURABLE_INCREMENTAL_VALUE
P6_COMPANY_NEWS_V1 = DEFERRED_ACCESS_BLOCKED_NO_CUSTOM_BUILD
P6_COMPANY_NEWS_PATCHWORK = RETIRED
P6_GLOBAL_NEWS_V1 = ACTIVE
CURRENT_P6_OBJECTIVE = GLOBAL_NEWS_V1_MINIMAL_FACTOR_ABLATION

COMPANY_NEWS_V1_HISTORICAL_STATUS = DEFERRED_ACCESS_BLOCKED
INSTITUTIONAL_REFERENCE_OWNER = RAVENPACK_COMPANY_NEWS_FACTORS_AND_NEWS_ANALYTICS
SELECTED_COMPANY_NEWS_WHOLE_OWNER = NONE
AQ_COMPANY_NEWS_ENGINE_REQUIRED = NO
COMPANY_NEWS_CUSTOM_BUILD_AUTHORIZED = NO
REALTIME_COMPANY_NEWS_PRODUCTIONIZATION = DEFERRED_TO_P9
ALPACA_DIRECT_ROLE = P9_REALTIME_NEWS_FALLBACK_OR_CHALLENGER

GDELT_COMPANY_NEWS_GLUE_ROLE = RETIRED
GDELT_GLOBAL_NEWS_ROLE = ACTIVE_P6_CANDIDATE
GDELT_GLOBAL_NEWS_SURFACES = MARKET_LEVEL_NEWS,GLOBAL_NEWS,GEOPOLITICAL_NEWS,MACRO_NEWS_CONTEXT
GDELT_GLOBAL_NEWS_SOURCE = GKG_2_1_WEB_ONLY
GDELT_DATE_ONLY_EFFECTIVE_RULE = FIRST_XNYS_SESSION_STRICTLY_AFTER_SAFE_CALENDAR_DATE
GLOBAL_NEWS_FEATURE_FAMILY_SELECTED = NO

FUTURE_GLOBAL_NEWS_M0 = BASE_157
FUTURE_GLOBAL_NEWS_M1 = BASE_157_PLUS_EXACT_FROZEN_GLOBAL_NEWS_V1_FEATURES
P5_FUNDAMENTALS_INCLUDED = NO
MACRO_V1_INCLUDED = NO

NEW_PRODUCTION_LOC = 0
AQ_NEWS_ENGINE_CREATED = NO
AQ_ENTITY_RESOLUTION_ENGINE_CREATED = NO
AQ_SECURITY_MASTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
REALTIME_WEBSOCKET_SESSION_COUNT = 0
ORDER_COUNT = 0
BROKER_ACTION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO

CURRENT_DEVELOPMENT_NEXT = P6_GLOBAL_NEWS_V1_MINIMAL_FEATURE_SURFACE_DESIGN_001
FINAL_CLASSIFICATION = PASS_P6_COMPANY_NEWS_CLOSEOUT_AND_GLOBAL_NEWS_HANDOFF
```

The frozen sequence is feature-surface design, minimal materialization,
ablation-protocol freeze, first authorized ablation, and closeout. No provider
search is authorized between these stages unless a concrete source defect
blocks execution. See [P6 Company News closeout and Global News handoff 001](p6-news-v1-company-news-closeout-and-global-news-handoff-001.md).

### P6 Global News V1 minimal feature surface (2026-09-26)

Global News V1 is frozen as four session-global fields from GDELT GKG 2.1 WEB
records. The contract uses one unique `GKGRECORDID` as one observation, native
`V1.5TONE` components, DuckDB aggregation, and the existing conservative
date-only availability rule. Canonical storage remains one row per XNYS
session, not one row per security.

Raw document count is replaced, not supplemented, by
`log1p(COUNT(DISTINCT GKGRECORDID))`. The transform has no fitted parameters,
future observations, rolling-window choice, or warm-up state. A bounded set of
previously frozen anchor batches varied from 636 to 2,721 valid WEB rows, a
4.2783x ratio, supporting variance compression without opening a predictive
window-selection search.

The bounded sanity POC reused the prior 2,500-row evidence and one exact
2.6 MB frozen 2022 anchor. Strict parsing retained 636 WEB records, rejected
one known decode-error row, found zero duplicate record IDs, zero selected
tone parse failures, and zero non-finite selected values. The archive matched
its prior byte count and MD5 and was deleted after verification. Its safe date
`2022-01-03` mapped to XNYS session `2022-01-04`.

```text
GLOBAL_NEWS_V1_SOURCE = GDELT_GKG_2_1_WEB
GLOBAL_NEWS_SOURCE_OWNER = GDELT_GKG_2_1
GLOBAL_NEWS_SAFE_AVAILABILITY_OWNER = GDELT_GKG_EXISTING_FROZEN_POLICY
GLOBAL_NEWS_SESSION_OWNER = EXCHANGE_CALENDARS_XNYS
GLOBAL_NEWS_RELATIONAL_COMPOSITION_OWNER = DUCKDB
GLOBAL_NEWS_V1_FEATURE_COUNT = 4
GLOBAL_NEWS_V1_FEATURES = global_news_log1p_volume,global_news_mean_tone,global_news_mean_negative_score,global_news_mean_polarity
GLOBAL_NEWS_VOLUME_TRANSFORM = log1p(COUNT(DISTINCT GKGRECORDID))
GLOBAL_NEWS_EMPTY_SESSION_POLICY = LOG1P_VOLUME_0_EMOTIONAL_FIELDS_NULL_NO_FORWARD_FILL
GLOBAL_NEWS_V1_GCAM_USED = NO
GLOBAL_NEWS_V1_THEMES_USED = NO
GLOBAL_NEWS_V1_EVENT_DATABASE_USED = NO
GLOBAL_NEWS_SOURCE_WEIGHTING_USED = NO
GLOBAL_NEWS_SEMANTIC_DEDUP_USED = NO
OUTCOME_BASED_SELECTION_USED = NO

FUTURE_GLOBAL_NEWS_M0 = BASE_157
FUTURE_GLOBAL_NEWS_M1 = BASE_157_PLUS_EXACT_GLOBAL_NEWS_V1_4
P5_FUNDAMENTALS_INCLUDED = NO
MACRO_V1_INCLUDED = NO
COMPANY_NEWS_INCLUDED = NO

CURRENT_P6_OBJECTIVE = GLOBAL_NEWS_V1_MINIMAL_MATERIALIZATION
CURRENT_DEVELOPMENT_NEXT = P6_GLOBAL_NEWS_V1_MINIMAL_MATERIALIZATION_001
NEW_PRODUCTION_LOC = 0
AQ_NEWS_FEATURE_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/global-news-v1-minimal-feature-surface-design-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 9ca69a381ef78090e59d93f1e140e92481dfcadbf340b3f020c0a1caf1fbe7eb
FINAL_CLASSIFICATION = PASS_P6_GLOBAL_NEWS_V1_MINIMAL_FEATURE_SURFACE_DESIGN
```

GCAM, themes, the separate GDELT Events database, positive score, activity
reference density, and self/group reference density are excluded. See
[P6 Global News V1 minimal feature surface design 001](p6-global-news-v1-minimal-feature-surface-design-001.md).

### P6 Global News V1 streaming backfill (2026-09-26)

Global News V1 is materialized. The owner supplied an authorized BigQuery
Sandbox project after the initial fail-closed access check. The official
partitioned `gdelt-bq.gdeltv2.gkg_partitioned` table then owned server-side
reduction across the frozen 2015-03-25 through 2024-12-31 source range. The
daily query returned 3,569 sufficient-statistics rows and zero raw GKG rows;
its exact scan was 216,430,419,549 bytes. The separate quality-count query used
the same bounded scan, keeping total task scan below the 750 GiB ceiling.

The existing pinned XNYS authority applied first-session-strictly-after
date-only availability, and DuckDB combined sum/count pairs into 2,455 exact
session-global rows from 2015-04-01 through 2024-12-31. The one empty session
retains zero volume and NULL means. No raw news corpus, article content, URL,
theme, GCAM field, or credential entered AQ storage or Git.

```text
P6_GLOBAL_NEWS_V1 = MATERIALIZED
CURRENT_P6_OBJECTIVE = GLOBAL_NEWS_V1_ABLATION_PROTOCOL_FREEZE
HISTORICAL_BACKFILL_MODEL = UPSTREAM_SERVER_SIDE_STREAMING_REDUCTION
GLOBAL_NEWS_STORAGE_MODEL = SESSION_FEATURE_HISTORY_ONLY
RAW_NEWS_RETENTION = NONE

BIGQUERY_AUTH_AVAILABLE = YES
BIGQUERY_PROJECT_AVAILABLE = YES
BIGQUERY_BILLING_STATUS = BIGQUERY_SANDBOX_NO_PAID_BILLING_ENABLED
BIGQUERY_SOURCE_TABLE = gdelt-bq.gdeltv2.gkg_partitioned
BIGQUERY_DRY_RUN = PASS
BIGQUERY_ESTIMATED_BYTES_PROCESSED = 216430419549
BIGQUERY_TOTAL_ESTIMATED_SCAN_BYTES = 432860839098
BIGQUERY_ACTUAL_BYTES_PROCESSED = 216430419549
BIGQUERY_QUERY_SQL_SHA256 = 93ecce9771cc6aa312dea8e557264ca84fe257fc853aaf9e6919e222b03d4375

SOURCE_QUERY_START = 2015-03-25
SOURCE_QUERY_END = 2024-12-31
SOURCE_COLLECTION = WEB_ONLY
SOURCE_RECORD_COUNT = 1618459226
DISTINCT_GKGRECORDID_COUNT = 1345072369
TONE_MALFORMED_COUNT = 0
NEGATIVE_MALFORMED_COUNT = 0
POLARITY_MALFORMED_COUNT = 0
RETURNED_RAW_GKG_ROW_COUNT = 0
RAW_GKG_ROWS_PERSISTED = 0
RAW_NEWS_RECORDS_PERSISTED = 0
RAW_GDELT_ZIP_RETAINED_COUNT = 0
ARTICLE_BODY_RETAINED_COUNT = 0
ARTICLE_HEADLINE_RETAINED_COUNT = 0
DAILY_SUFFICIENT_STATISTICS_ROW_COUNT = 3569
EXPECTED_XNYS_SESSION_COUNT = 2455
MATERIALIZED_SESSION_COUNT = 2455
EMPTY_SESSION_COUNT = 1
RIGHT_EDGE_POST_2024_SESSION_COUNT = 1
RIGHT_EDGE_POST_2024_DOCUMENT_COUNT = 302925
DAILY_SUFFICIENT_STATISTICS_MATERIALIZED = YES
SESSION_FEATURE_HISTORY_MATERIALIZED = YES

GLOBAL_NEWS_V1_FEATURE_COUNT = 4
GLOBAL_NEWS_V1_FEATURES = global_news_log1p_volume,global_news_mean_tone,global_news_mean_negative_score,global_news_mean_polarity
GLOBAL_NEWS_V1_MATERIALIZATION_ID = 293f69052f3184ca798a55ce2183c5c8c4bf179c72b78d1247f58d2282fb4c4f
DAILY_SUFFICIENT_STATISTICS_SHA256 = 5d85aba4f584c08178100638709cc3cda4e7472f1a72da29c677777834b77e9d
SESSION_FEATURE_HISTORY_SHA256 = 3184ab20246300465dc34b1aa2dd7c5f0938e69439581d2bb4b022bc9ce448cb
FUTURE_REALTIME_STATE_MODEL = MUTABLE_LATEST_STATE_PLUS_IMMUTABLE_SESSION_SNAPSHOTS
REALTIME_STATEFUL_STREAM_PROCESSOR_SELECTION = DEFERRED_TO_P9

AQ_NEWS_DATABASE_CREATED = NO
AQ_RAW_NEWS_ARCHIVE_CREATED = NO
AQ_GDELT_DOWNLOADER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
OUTCOME_DATA_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO

PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/global-news-v1-streaming-sufficient-statistics-backfill-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 75e0e85e0448d28abb3df18e0802f1d7574d5c628fb386f2d8fc6574d8e57118
CURRENT_DEVELOPMENT_NEXT = P6_GLOBAL_NEWS_V1_ABLATION_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_P6_GLOBAL_NEWS_V1_STREAMING_SUFFICIENT_STATISTICS_BACKFILL
```

See [P6 Global News V1 streaming sufficient-statistics backfill 001](p6-global-news-v1-streaming-sufficient-statistics-backfill-001.md).

### P6 Global News V1 GKGRECORDID integrity gate (2026-09-26)

The post-materialization integrity gate blocks the Global News V1 ablation.
The official GDELT GKG 2.1 codebook defines `GKGRECORDID` as a globally unique
record identifier and one GKG row as one codified document. The retained
backfill SQL correctly used distinct IDs for volume but computed the three
sentiment sum/count pairs over physical rows.

One additional partition-pruned BigQuery pass remained within its 250 GiB
ceiling and proved that the physical duplicates cannot be collapsed by an
arbitrary row choice. Of 241,297,210 duplicated IDs, 240,643,925 conflict on
Tone, 240,604,624 on Negative Score, and 241,180,404 on Polarity. Date and the
already-filtered WEB source collection had zero conflicts. No corrected
artifact or replacement materialization identity was created.

The missing source date is `2017-08-29`. Its BigQuery partition is absent, so
the affected `2017-08-30` XNYS session is a `SOURCE_COVERAGE_GAP`, not a
genuine zero-news session. All four frozen feature values must be NULL if a
future authoritative materialization resolves the duplicate semantics.

```text
GKGRECORDID_SEMANTICS = GLOBALLY_UNIQUE_LOGICAL_GKG_RECORD
EXISTING_SENTIMENT_DEDUP_SEMANTICS = PHYSICAL_ROWS
DUPLICATE_PHYSICAL_ROW_EXCESS = 273386857
DUPLICATE_PHYSICAL_ROW_RATE = 0.16891797618879278
DUPLICATE_GKGRECORDID_COUNT = 241297210
DUPLICATE_ID_DATE_CONFLICT_COUNT = 0
DUPLICATE_ID_SOURCE_COLLECTION_CONFLICT_COUNT = 0
DUPLICATE_ID_TONE_CONFLICT_COUNT = 240643925
DUPLICATE_ID_NEGATIVE_CONFLICT_COUNT = 240604624
DUPLICATE_ID_POLARITY_CONFLICT_COUNT = 241180404
MISSING_SOURCE_CALENDAR_DATES = 2017-08-29
EMPTY_SESSION = 2017-08-30
EMPTY_SESSION_CLASSIFICATION = SOURCE_COVERAGE_GAP
SOURCE_COVERAGE_GAP_FEATURE_POLICY = ALL_FOUR_FEATURES_NULL
PRIOR_GLOBAL_NEWS_V1_MATERIALIZATION_AUTHORITY = DIAGNOSTIC_ONLY_NOT_SCIENTIFICALLY_AUTHORITATIVE
CORRECTED_GLOBAL_NEWS_V1_MATERIALIZATION_ID = NOT_CREATED_BLOCKED
CURRENT_P6_OBJECTIVE = GLOBAL_NEWS_V1_GKGRECORDID_INTEGRITY_BLOCKER
CURRENT_DEVELOPMENT_NEXT = BLOCKED_GDELT_DUPLICATE_RECORD_SEMANTIC_CONFLICT
FINAL_CLASSIFICATION = BLOCKED_GDELT_DUPLICATE_RECORD_SEMANTIC_CONFLICT
```

### P6 Global News V1 official raw-source authority arbitration (2026-09-26)

The official GDELT raw GKG 2.1 publication stream was tested as the only
authorized replacement candidate for the non-authoritative BigQuery sentiment
materialization. A deterministic 2015–2024 sample used 40 conflicted IDs and 20
non-conflicting controls. Official English/Translingual master-list resolution
reduced the sample to 27 unique archives totaling 246,256,050 compressed bytes;
all 27 byte-count and MD5 checks passed.

Every conflicted ID appeared twice in its canonical raw archive with two
distinct selected semantic tuples, and those raw variant sets exactly matched
the two BigQuery variants in all 40 cases. All 20 controls matched. The defect
therefore exists in the official raw GKG artifacts themselves; neither the
BigQuery mirror nor the raw publication stream is an admissible historical
sentiment owner, and no arbitrary deduplication repair is authorized.

The official master lists contain 175 GKG batches for 2017-08-29, proving that
the absent BigQuery partition is a mirror coverage gap. For 2015-03-25 through
2024-12-31, the master lists contain 669,008 GKG archives totaling
6,230,087,044,164 compressed bytes. This metadata-only cost census did not
start a historical raw backfill.

```text
CONFLICT_SAMPLE_COUNT = 40
CONTROL_UNIQUE_ID_COUNT = 20
RAW_BATCH_ARCHIVE_COUNT_DOWNLOADED = 27
RAW_COMPRESSED_BYTES_DOWNLOADED = 246256050
RAW_ARCHIVE_HASH_VERIFICATION_PASS_COUNT = 27
RAW_ARCHIVE_HASH_VERIFICATION_FAIL_COUNT = 0
RAW_SINGLE_ROW_COUNT = 0
RAW_MULTIPLE_IDENTICAL_COUNT = 0
RAW_MULTIPLE_CONFLICT_COUNT = 40
RAW_MISSING_COUNT = 0
RAW_CONFLICT_VARIANT_SET_EXACT_BIGQUERY_MATCH_COUNT = 40
CONTROL_MATCH_COUNT = 20
CONTROL_MISMATCH_COUNT = 0
CONTROL_MISSING_COUNT = 0
RAW_GKG_BATCH_FILE_COUNT_2017_08_29 = 175
RAW_SOURCE_DATE_PRESENT = YES
BIGQUERY_2017_08_29_GAP = BIGQUERY_MIRROR_COVERAGE_GAP
RAW_ENGLISH_ARCHIVE_COUNT_2015_2024 = 337124
RAW_TRANSLINGUAL_ARCHIVE_COUNT_2015_2024 = 331884
RAW_TOTAL_ARCHIVE_COUNT_2015_2024 = 669008
RAW_ENGLISH_COMPRESSED_BYTES_2015_2024 = 2553726973890
RAW_TRANSLINGUAL_COMPRESSED_BYTES_2015_2024 = 3676360070274
RAW_TOTAL_COMPRESSED_BYTES_2015_2024 = 6230087044164
OFFICIAL_RAW_GKG_AUTHORITY = FAIL_SEMANTIC_CONFLICT
BIGQUERY_GKG_SENTIMENT_ROLE = REJECTED_FOR_HISTORICAL_SENTIMENT_BACKFILL
PRIOR_GLOBAL_NEWS_V1_MATERIALIZATION_AUTHORITY = DIAGNOSTIC_ONLY_NOT_SCIENTIFICALLY_AUTHORITATIVE
RAW_GKG_ZIP_RETAINED_COUNT = 0
RAW_GKG_ROWS_PERSISTED = 0
AQ_GDELT_DOWNLOADER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
OUTCOME_DATA_ACCESSED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/global-news-v1-official-raw-source-authority-arbitration-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 09fd75d89fd7d276ee736de756e98ff1da4f2a811d869dd0727e290dd468d1a9
CURRENT_P6_OBJECTIVE = GLOBAL_NEWS_V1_CLOSEOUT
CURRENT_DEVELOPMENT_NEXT = P6_GLOBAL_NEWS_V1_CLOSEOUT_001
FINAL_CLASSIFICATION = PASS_P6_GLOBAL_NEWS_V1_OFFICIAL_RAW_SOURCE_AUTHORITY_ARBITRATION
```

---

### P6 historical-news mature-upstream reentry audit (2026-09-26)

The five-candidate audit found one bounded research path but no certified
production-PIT historical news owner. FinSen's public US research benchmark and
its documented ProsusAI/FinBERT daily aggregation method may be tested as one
global-market `news_sentiment` challenger with a thin Qlib handoff. Its
date-only timing remains disqualifying for production PIT authority.

FNSPID is blocked by conflicting public license terms; FinRL-DeepSeek,
TradeTheEvent, and FinGPT forecasting remain reference methods only. PR #106
stays open and unmodified as the frozen P6 closeout candidate.

```text
P6_CLOSEOUT_CANDIDATE = PR_106_HELD_PENDING_FINAL_HISTORICAL_NEWS_REENTRY
P6_STATUS = REOPENED_BOUNDED_HISTORICAL_NEWS_RESEARCH
SELECTED_HISTORICAL_NEWS_DATA_OWNER = FINSEN_US_RESEARCH_ONLY_BENCHMARK
SELECTED_NEWS_SIGNAL_METHOD_OWNER = PROSUSAI_FINBERT_VIA_FINSEN_DAILY_AGGREGATION_METHOD
SELECTED_NEWS_PREDICTION_RESEARCH_PATH = FINSEN_GLOBAL_MARKET_DAILY_SENTIMENT_TO_QLIB_INCREMENTAL_ABLATION
STRICT_PRODUCTION_PIT_READY = NO
BOUNDED_RESEARCH_POC_READY = YES
MAX_RETAINED_RAW_NEWS_ROWS = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P6_HISTORICAL_NEWS_SELECTED_UPSTREAM_BOUNDED_FACTOR_POC_001
FINAL_CLASSIFICATION = PASS_P6_HISTORICAL_NEWS_MATURE_UPSTREAM_REENTRY_AUDIT
```

---

### P6 FinSen bounded historical-news factor POC (2026-09-26)

The research-only FinSen path materialized one deterministic global-market
factor, `finsen_finbert_market_sentiment`. It reproduces the published FinBERT
score `P(positive) - P(negative)` and daily arithmetic mean over `Content`, then
uses the first XNYS session strictly after each date. Sessions without source
evidence remain NULL; no forward fill, backfill, zero fill, return access, or
model evaluation occurred.

FinSen remains date-only and research-use constrained. The factor is therefore
a materialized research challenger, not a production-PIT admission. PR #106
remains open and unmerged until the lane reaches a terminal scientific result.

```text
P6_STATUS = REOPENED_BOUNDED_HISTORICAL_NEWS_RESEARCH
P6_CLOSEOUT_CANDIDATE = PR_106_HELD_UNMERGED
FINSEN_RESEARCH_FACTOR_STATUS = MATERIALIZED_RESEARCH_CHALLENGER
RESEARCH_FACTOR_NAME = finsen_finbert_market_sentiment
RESEARCH_FACTOR_COUNT = 1
STRICT_PRODUCTION_PIT_READY = NO
PRODUCTION_ADMISSION_AUTHORIZED = NO
SOURCE_ROW_COUNT = 15534
ELIGIBLE_2015_2023_ROW_COUNT = 14240
XNYS_SESSION_COUNT = 2087
SESSION_WITH_SIGNAL_COUNT = 2003
SESSION_WITHOUT_SIGNAL_COUNT = 84
RESEARCH_SIGNAL_SHA256 = 93bc6a62550accc0a4484e86d6f3af8242c69a6211a51ef40bb34d0c9bc60f48
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 6e56cfd78213eef31b256a4362f70352cfc37afb5e6ba9517b7b4bf73ae5c2f5
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P6_HISTORICAL_NEWS_FINSEN_ABLATION_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_P6_HISTORICAL_NEWS_FINSEN_BOUNDED_FACTOR_POC
```

---

### P6 FinSen historical-news ablation protocol freeze (2026-09-26)

The exact research-only FinSen factor now has one frozen comparison:
`M0 = BASE_157` versus
`M1 = BASE_157 + finsen_finbert_market_sentiment`. The common-support test ends
on `2023-07-17`; the 84 supported-interval NULL sessions remain in both row
populations and are not filled or dropped.

The existing P5/Macro V1 Qlib LightGBM, label, processor, portfolio,
WalkForward, CPCV, SPA, and RealityCheck authorities are reused unchanged. No
training, prediction, backtest, ablation, outcome access, or sealed-OOS access
occurred during this freeze.

```text
FINSEN_ABLATION_PROTOCOL = FROZEN_PRE_EXECUTION
PROTOCOL_SHA256 = 63c69d4eb80a7d98ad4b846484ca14a0bc47e83b2fc5659a261098e7852d79b9
CONTROL_SURFACE = BASE_157
CONTROL_FEATURE_COUNT = 157
CONTROL_FEATURE_MANIFEST_SHA256 = 7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463
CONTROL_DATASET_IDENTITY = P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135
M0_FEATURE_COUNT = 157
M1_FEATURE_COUNT = 158
FINSEN_FACTOR_NAME = finsen_finbert_market_sentiment
FINSEN_FACTOR_SHA256 = 93bc6a62550accc0a4484e86d6f3af8242c69a6211a51ef40bb34d0c9bc60f48
TRAIN_RANGE = 2015-04-01..2019-12-31
VALIDATION_RANGE = 2020-01-01..2021-12-31
HISTORICAL_RESEARCH_TEST_RANGE = 2022-01-03..2023-07-17
MODEL_OWNER = MICROSOFT_QLIB
MODEL_CONFIG_SHA256 = f75355629e7ad6b85f100627dbc055712d7f72d1e1e31783736f1ce4cc10a61a
PRIMARY_METRIC = QLIB_RANK_IC
PROTOCOL_CHANGING_RERUN_AUTHORIZED = NO
STRICT_PRODUCTION_PIT_READY = NO
PRODUCTION_ADMISSION_AUTHORIZED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P6_HISTORICAL_NEWS_FINSEN_FIRST_AUTHORIZED_ABLATION_001
FINAL_CLASSIFICATION = PASS_P6_HISTORICAL_NEWS_FINSEN_ABLATION_PROTOCOL_FROZEN
```

PR #106 remains open, unmerged, and unmodified stale closeout evidence.

---

### P6 FinSen first authorized ablation (2026-09-26)

The single preregistered `M0 = BASE_157` versus
`M1 = BASE_157 + finsen_finbert_market_sentiment` comparison passed every
pre-fit identity, row, label, membership, missingness, broadcast, runtime, and
model-config gate. Exactly two Qlib models were fitted. The 1,011,952-row
surfaces remained identical apart from the one frozen FinSen column, including
all 84 NULL sessions.

The finite Qlib Rank IC evidence is `0.004271356026045012` for M0 and
`0.005851775987652466` for M1, a delta of `0.0015804199616074538`. This does
not support a positive scientific classification because the preregistered
WalkForward procedure is impossible on the frozen common-support test window:
`train_size=504` plus `purged_size=2` requires at least 506 observations, while
the exact test window contains 385 sessions. No WalkForward, CPCV, SPA, or
RealityCheck result was fabricated, and no parameter, date, factor, or model
was changed after outcome access.

The initial composition call also inherited the P2 reference module's longer
2024 test boundary. Those outputs are retained only as invalid diagnostic
evidence. An exact no-refit recovery rebound the same shared Qlib backtest
mechanics to the already-frozen FinSen end date, and the authoritative return
evidence has exactly 385 sessions. Model refit count for that recovery is zero.

```text
FINSEN_ABLATION_RESULT = INCONCLUSIVE
INCONCLUSIVE_REASON = FROZEN_WALKFORWARD_REQUIRES_AT_LEAST_506_OBSERVATIONS_BUT_TEST_HAS_385
PROTOCOL_SHA256 = 63c69d4eb80a7d98ad4b846484ca14a0bc47e83b2fc5659a261098e7852d79b9
M0_ROW_COUNT = 1011952
M1_ROW_COUNT = 1011952
M0_TEST_RANK_IC = 0.004271356026045012
M1_TEST_RANK_IC = 0.005851775987652466
RANK_IC_DELTA = 0.0015804199616074538
MODEL_TRAINING_COUNT = 2
PREDICTION_COUNT = 2
BACKTEST_COUNT = 2
ABLATION_COUNT = 1
PROTOCOL_CHANGING_RERUN_AUTHORIZED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/P6/historical-news-finsen-first-authorized-ablation-001
PRIVATE_EVIDENCE_CHECKSUM_SHA256 = 728cd2ac31eb9e40f1f9682fe6663ac46a68ac17af71f446ee32c31892d2a5d0
PR106_STATE = OPEN
PR106_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P6_HISTORICAL_NEWS_FINSEN_INCONCLUSIVE_CLOSEOUT_OR_EXACT_RECOVERY_001
FINAL_CLASSIFICATION = INCONCLUSIVE_P6_HISTORICAL_NEWS_FINSEN_FROZEN_WALKFORWARD_INSUFFICIENT_OBSERVATIONS
```


---

### P6 FinSen inconclusive and phase closeout (2026-09-26)

The first and only preregistered FinSen ablation remains scientifically
`INCONCLUSIVE`. Its Rank IC delta was positive, but the frozen statistical
protocol cannot complete because the 385-session common-support test window is
shorter than the 506 observations required by the frozen WalkForward
`train_size=504` and `purged_size=2`. No after-the-fact protocol change or
second FinSen experiment is authorized.

All P6 information-intelligence lanes now have terminal dispositions. Macro V1
found no measurable incremental value; Company News V1 remains access-blocked
with no custom AQ substitute; Global News V1 is rejected for official-source
semantic conflict; and FinSen closes inconclusive. No P6 feature family is
admitted, so the post-P6 control remains exact `BASE_157`.

```text
P6_STATUS = COMPLETE
P6_ACTIVE = NO
P6_MACRO_V1 = CLOSED_NO_MEASURABLE_INCREMENTAL_VALUE
P6_COMPANY_NEWS_V1 = DEFERRED_ACCESS_BLOCKED_NO_CUSTOM_BUILD
P6_GLOBAL_NEWS_V1 = REJECTED_SOURCE_SEMANTIC_CONFLICT
P6_FINSEN_HISTORICAL_NEWS = INCONCLUSIVE_PROTOCOL_FEASIBILITY_FAILURE
FINSEN_INCONCLUSIVE_REASON = FROZEN_WALKFORWARD_REQUIRES_AT_LEAST_506_OBSERVATIONS_BUT_TEST_HAS_385
EXACT_NO_PROTOCOL_CHANGE_RECOVERY_AVAILABLE = NO
FINSEN_SECOND_EXPERIMENT_AUTHORIZED = NO
P6_NEW_ADMITTED_FEATURE_FAMILY_COUNT = 0
POST_P6_CONTROL_SURFACE = BASE_157
POST_P6_CONTROL_FEATURE_COLUMN_COUNT = 157
STRICT_PRODUCTION_PIT_READY = NO
PRODUCTION_ADMISSION_AUTHORIZED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P4_REAL_CERTIFIED_ARTIFACT_COUNT = 0
P4_REAL_CHAMPION_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
ACTIVE_DEVELOPMENT = P7_ENTRY_AUDIT
CURRENT_DEVELOPMENT_NEXT = P7_MULTI_ALPHA_ENSEMBLE_ENTRY_AUDIT_001
FINAL_CLASSIFICATION = PASS_P6_FINSEN_INCONCLUSIVE_AND_PHASE_CLOSEOUT_NO_NEW_ADMITTED_FEATURE_FAMILY
```

The FinSen executor is retained as a frozen single-use research executor for
audit/reproduction only; it is not a generic evaluation framework. PR #106 is
closed without merge and superseded by this final P6 closeout.

```text
PR106_STATE = CLOSED_SUPERSEDED
PR106_MERGED = NO
PR106_SUPERSEDED = YES
```

See [P6 Historical News FinSen inconclusive and phase closeout 001](p6-historical-news-finsen-inconclusive-and-phase-closeout-001.md).


---

### P7 multi-alpha ensemble entry audit (2026-09-26)

P7 fails closed at its entry gate because the current project has only one
candidate alpha family: the 17 P3 AlphaGen Candidate V3 objects are all members
of the same `FORMULAIC_ALPHA` family. `BASE_157` remains a control surface,
not a second candidate family. P5 admitted no fundamental increment and P6
admitted no information-intelligence family.

```text
P7_ENTRY_AUDIT = COMPLETE
P7_STATUS = DEFERRED_INSUFFICIENT_INDEPENDENT_ALPHA_FAMILIES
P7_ACTIVE = NO
P7_EXIT_CONDITION_SATISFIED = NO
P7_ENSEMBLE_EXECUTION_AUTHORIZED = NO
P7_MINIMUM_INDEPENDENT_ALPHA_FAMILIES_REQUIRED = 2
P7_CURRENT_INDEPENDENT_CANDIDATE_ALPHA_FAMILIES = 1
P7_ALPHA_FAMILY_1 = P3_FORMULAIC_ALPHA
P7_SECOND_INDEPENDENT_ALPHA_FAMILY = NONE
P7_CONTROL_SURFACE = BASE_157
P7_CONTROL_IS_INDEPENDENT_ALPHA_FAMILY = NO
P3_REAL_CANDIDATE_V3_COUNT = 17
P3_FORMULAIC_ALPHA_FAMILY_COUNT = 1
P5_ADMITTED_INCREMENTAL_ALPHA_FAMILY_COUNT = 0
P6_NEW_ADMITTED_FEATURE_FAMILY_COUNT = 0
MODEL_TRAINING_COUNT = 0
BACKTEST_COUNT = 0
ENSEMBLE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
NEXT_TASK = P8_PORTFOLIO_RISK_ENTRY_AUDIT_001
FINAL_CLASSIFICATION = PASS_P7_ENTRY_AUDIT_DEFERRED_INSUFFICIENT_INDEPENDENT_ALPHA_FAMILIES
```

P7 may be reopened only after at least two genuinely independent admissible
alpha families exist. P2 certification of additional Formulaic candidates does
not by itself create a second family. The P8 next task is entry-audit only and
must not treat P7 as complete.

See [P7 Multi-Alpha Ensemble entry audit 001](p7-multi-alpha-ensemble-entry-audit-001.md).


---

### P8 portfolio / risk entry audit (2026-09-26)

P8 may begin bounded contract and upstream-ownership work, but real portfolio
tournament and risk-overlay execution remain deferred. Qlib and skfolio already
own generic research portfolio/backtest/optimization mechanics, while P0 POC-C
and POC-D proved the synthetic broker-neutral TargetPortfolio boundary.

P7 has no ensemble artifact, P2 sealed OOS remains closed, and P4 has no real
Certified or Champion artifact. P8 therefore may design the minimal
TargetPortfolio and human-risk-envelope contracts, but may not allocate real
candidate capital or duplicate upstream portfolio engines.

```text
P8_ENTRY_AUDIT = COMPLETE
P8_ENTRY_ALLOWED_FOR_CONTRACT_AND_UPSTREAM_DESIGN = YES
P8_REAL_PORTFOLIO_TOURNAMENT_AUTHORIZED = NO
P8_REAL_RISK_OVERLAY_EXECUTION_AUTHORIZED = NO
P8_EXIT_CONDITION_SATISFIED = NO
P8_GENERIC_PORTFOLIO_OPTIMIZER_OWNER = SKFOLIO
P8_RESEARCH_BACKTEST_PORTFOLIO_OWNER = QLIB
P0_TARGETPORTFOLIO_POC = PASS_SYNTHETIC_INTEGRATION_ONLY
P7_ENSEMBLE_ARTIFACT_AVAILABLE = NO
P4_REAL_CERTIFIED_ARTIFACT_COUNT = 0
P4_REAL_CHAMPION_COUNT = 0
P8_REAL_CERTIFIED_STRATEGY_INPUT_COUNT = 0
P8_MODEL_TRAINING_COUNT = 0
P8_BACKTEST_COUNT = 0
P8_REAL_PORTFOLIO_OPTIMIZATION_COUNT = 0
P8_BROKER_ACTION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
NEXT_TASK = P8_PORTFOLIO_UPSTREAM_OWNERSHIP_AND_TARGETPORTFOLIO_CONTRACT_FREEZE_001
FINAL_CLASSIFICATION = PASS_P8_ENTRY_AUDIT_CONTRACT_DESIGN_ALLOWED_REAL_PORTFOLIO_EXECUTION_DEFERRED
```

See [P8 Portfolio / Risk entry audit 001](p8-portfolio-risk-entry-audit-001.md).

---

### P7 Qlib-native ensemble integration and input qualification (2026-09-26)

P7 is reopened for bounded research integration and real-input qualification,
not declared complete. The earlier family-count audit remains correct that all
17 frozen Candidate V3 objects share one Formulaic Alpha producer family, but
the inference that a common producer prevents combination research from even
beginning is superseded. Producer identity, economic signal family and
empirical diversification are different concepts.

The pinned Qlib `AverageEnsemble` public API passes strict synthetic-only
integration and input-boundary tests. Bounded real-input qualification then
opened only allowlisted historical prediction scores. All 17 Candidate V3
artifacts share exactly 377,938 ordered rows over 751 sessions and retain their
recorded hashes, with no missing or non-finite values. Nine satisfy the strict
#114 per-session nonconstant rule; eight contain 385 constant
candidate-session cross-sections in aggregate.

The explicit P2 historical-rehearsal OLS control is bound by recipe, dataset,
recorder and artifact hash. Its method and P2 universe authority are the
intended control, but the existing artifact is a Series rather than the
required one-column DataFrame and its row identity is not exact: 374,591 rows
overlap, 3,347 are candidate-only and 1,006 are control-only. No conversion,
intersection, row drop, component removal or replacement prediction was
performed. The input contract is partial. Synthetic skfolio 1.0.6 checks on
the verified 751-session calendar yielded three complete WalkForward folds and
45 CPCV splits; these parameters remain a feasibility proposal rather than a
frozen protocol. Empirical complementarity remains unevaluated.

```text
P7_CURRENT_STATUS = ACTIVE_RESEARCH_INTEGRATION_AND_INPUT_QUALIFICATION
P7_EXIT_CONDITION_SATISFIED = NO
SIGNAL_COMPLEMENTARITY = NOT_YET_ESTABLISHED
P7_ENSEMBLE_OWNER = MICROSOFT_QLIB
P7_UPSTREAM_CLASS = qlib.model.ens.ensemble.AverageEnsemble
P7_SYNTHETIC_TEST_RESULT = 15_OF_15_PASS
P7_FROZEN_CANDIDATE_ID_COUNT = 17
P7_PREDICTION_ARTIFACT_IDENTITY_VERIFIED_COUNT = 17
P7_REAL_PREDICTION_VALUES_ACCESSED = YES_INPUT_QUALIFICATION_ONLY
P7_COMMON_ORDERED_CANDIDATE_ROW_IDENTITY = PASS_17_OF_17
P7_CANDIDATE_COMMON_ROW_COUNT = 377938
P7_CANDIDATE_COMMON_SESSION_COUNT = 751
P7_STRICT_INPUT_BOUNDARY_PASS_COUNT = 9
P7_STRICT_INPUT_BOUNDARY_FAIL_COUNT = 8
P7_CONSTANT_COMPONENT_SESSION_COUNT = 385
P7_CONTROL_RECIPE_IDENTIFIED = YES
P7_CONTROL_PREDICTION_ARTIFACT_BOUND = YES
P7_CONTROL_PREDICTION_SHA256 = 26c3433faa58a64914393fe13eac169d9ce86dbbe86f16dfb2b24fbd64139dab
P7_CONTROL_REAL_INPUT_COMPATIBILITY = FAIL_SHAPE_AND_ROW_IDENTITY
P7_INPUT_CONTRACT_STATUS = PARTIAL
P7_SYNTHETIC_WALKFORWARD_USABLE_FOLD_COUNT = 3
P7_SYNTHETIC_CPCV_USABLE_SPLIT_COUNT = 45
P7_STATISTICAL_PROTOCOL_FROZEN = NO
P7_REAL_ENSEMBLE_EXECUTION_COUNT = 0
P7_PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
P8_STATUS = EARLY_DESIGN_EVIDENCE_ONLY_NO_IMPLEMENTATION
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P7_REAL_DATA_ENSEMBLE_INPUT_AND_CONTROL_CONTRACT_CLOSEOUT_001
FINAL_CLASSIFICATION = BLOCKED_P7_STRICT_REAL_INPUT_CONTRACT_AND_CONTROL_MATERIALIZATION_REQUIRED
```

See [P7 Qlib-native ensemble integration POC 001](p7-qlib-native-ensemble-integration-poc-001.md),
[P7 real-data ensemble input contract and protocol feasibility 001](p7-real-data-ensemble-input-contract-and-protocol-feasibility-001.md),
the historical [P7 entry audit](p7-multi-alpha-ensemble-entry-audit-001.md),
and the historical [P8 entry audit](p8-portfolio-risk-entry-audit-001.md).

#### P7 real-data input and control contract closeout (2026-09-26)

The preceding partial status is retained as historical evidence and is now
superseded for the input-contract boundary. The selected OLS control was
losslessly adapted from a named Series to a one-column `score` DataFrame. All
4,353 row differences are explained: 1,006 lie after the candidate label-safe
end, 3,316 reflect historical membership/identity exclusions, and 31 reflect
the existing Qlib current-close availability rule. No row remains unexplained.

The final population was derived independently from P2 historical membership,
the Qlib current-close eligibility rule, and the P3 two-session label-safe
interval. It was not defined as the accidental intersection of prediction
files. All 17 candidates and the OLS control cover the exact 374,591-row,
751-session ordered grid. The 17 candidates remain in the master roster;
exactly constant components are inactive only for their current session under
the research policy below. Qlib continues to own standardization and equal
averaging. Qualification found at least eight active components on every
session. No real ensemble was executed.

```text
P7_CURRENT_STATUS = ACTIVE_RESEARCH_INTEGRATION_INPUT_CONTRACT_COMPLETE
P7_EXIT_CONDITION_SATISFIED = NO
SIGNAL_COMPLEMENTARITY = NOT_YET_ESTABLISHED
P7_ENSEMBLE_OWNER = MICROSOFT_QLIB
P7_UPSTREAM_CLASS = qlib.model.ens.ensemble.AverageEnsemble
P7_MASTER_CANDIDATE_COUNT = 17
P7_CONTROL_FORMAT_ADAPTATION = PASS_LOSSLESS_SERIES_TO_SCORE_DATAFRAME
P7_ORIGINAL_ARTIFACT_HASH_CHANGED_COUNT = 0
P7_UNEXPLAINED_ROW_COUNT = 0
P7_FINAL_POPULATION_RULE = P2_HISTORICAL_MEMBERSHIP_AND_QLIB_CURRENT_CLOSE_AVAILABLE_WITHIN_P3_TWO_SESSION_LABEL_SAFE_INTERVAL
P7_FINAL_POPULATION_ROW_COUNT = 374591
P7_FINAL_POPULATION_SESSION_COUNT = 751
P7_FINAL_POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
P7_INPUT_CONTRACT_STATUS = COMPLETE
P7_INPUT_CONTRACT_SHA256 = 92de81d0b8b7b7a29891bf523ae8519af44456f52fea3410ebf0ebd210d0f81f
P7_CONSTANT_SESSION_POLICY = SESSION_LOCAL_NONCONSTANT_COMPONENT_EQUAL_WEIGHT
P7_INACTIVE_CANDIDATE_SESSION_COUNT = 2575
P7_UNIQUE_AFFECTED_SESSION_COUNT = 736
P7_MINIMUM_ACTIVE_COMPONENT_COUNT = 8
P7_SYNTHETIC_TEST_RESULT = 25_OF_25_PASS
P7_NUMERIC_BOUNDARY_GUARD = PASS_FAIL_CLOSED_BEFORE_ENSEMBLE
P7_REAL_INVALID_MEAN_COUNT = 0
P7_REAL_INVALID_STD_COUNT = 0
P7_ACTIVE_MASK_UNCHANGED = YES
P7_INPUT_CONTRACT_IDENTITY_STATUS = UNCHANGED_DATA_CONTRACT_IMPLEMENTATION_GUARD_SEPARATE
P7_SYNTHETIC_WALKFORWARD_USABLE_FOLD_COUNT = 3
P7_SYNTHETIC_CPCV_USABLE_SPLIT_COUNT = 45
P7_STATISTICAL_PROTOCOL_FROZEN = NO
P7_HISTORICAL_PREDICTION_REUSE_READINESS = READY_COMPLETE_INPUT_CONTRACT
P7_PROSPECTIVE_MODEL_READINESS = NOT_READY_MODEL_BYTES_NOT_PERSISTED
P7_REAL_MODEL_TRAINING_COUNT = 0
P7_REAL_PREDICTION_GENERATION_COUNT = 0
P7_REAL_ENSEMBLE_EXECUTION_COUNT = 0
P7_BACKTEST_COUNT = 0
P7_PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
P8_STATUS = EARLY_DESIGN_EVIDENCE_ONLY_NO_IMPLEMENTATION
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P7_FIRST_ENSEMBLE_RESEARCH_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_P7_REAL_DATA_ENSEMBLE_INPUT_AND_CONTROL_CONTRACT_CLOSEOUT
```

---

### P7 variable-roster upstream handoff POC (2026-09-26)

The fixed 17-candidate snapshot remains immutable, but its count is snapshot
metadata rather than a permanent runtime constraint. The proposed fixed-roster
research-protocol task is paused as reference evidence and was not executed.
A focused synthetic POC proves that P7 can consume externally authorized,
immutable, time-effective roster versions without becoming a certification or
model-management owner.

The corrected handoff retains only Candidate and external authorization-evidence
references per member. Candidate V3 remains authoritative for
model/configuration identity; P2/P4 or the applicable research policy owns
authorization; Qlib/MLflow owns runtime lineage and readiness. Qlib online
status is neither roster authorization nor certification evidence.

Roster identity is SHA-256 over RFC 8785 JCS of immutable non-ID fields using
the already-authorized Python `rfc8785==0.1.4` leaf. Frozen Pydantic models
reject extra fields. Daily activation now uses an explicit XNYS
`effective_session`, validated directly by the existing `aq_xnys_calendar`
leaf over `exchange_calendars`, separately
from the timezone-aware UTC evidence cutoff. The validated session-to-members
handoff then delegates to the existing session-local boundary and Qlib
`AverageEnsemble`.

Synthetic `TEST_FIXTURE_NOT_REAL_EVIDENCE` rosters transition from 3 to 5 to 2
members. Tests prove exact boundary activation, no future-member contribution,
distinct identities for same-class models, no fabricated pre-entry
predictions, exact row alignment, fail-closed missing/non-finite values,
unchanged session-local constant handling, minimum-active-component rejection,
deterministic replay and unchanged earlier outputs after later roster versions
exist. No real lifecycle record or Candidate V3 identity was changed.

```text
P7_VARIABLE_ROSTER_HANDOFF_STATUS = PASS_SYNTHETIC_UPSTREAM_HANDOFF
P7_FIXED_17_CANDIDATE_SNAPSHOT_MUTATED = NO
P7_FIXED_ROSTER_PROTOCOL_TASK = PAUSED_REFERENCE_NOT_EXECUTED
P7_SYNTHETIC_ROSTER_SEQUENCE = 3_TO_5_TO_2
P7_ROSTER_EVIDENCE_CLASSIFICATION = TEST_FIXTURE_NOT_REAL_EVIDENCE
P7_EFFECTIVE_TIME_SELECTION = PASS_XNYS_DAILY_SESSION
P7_FUTURE_ROSTER_BACKWARD_REWRITE_COUNT = 0
P7_REPLAY_DETERMINISM = PASS
P7_ROSTER_IDENTITY = SHA256_RFC8785_JCS_IMMUTABLE_NON_ID_FIELDS
P7_AQ_CUSTOM_CANONICALIZER = NO
P7_ROSTER_MEMBER_FIELD_COUNT = 2
P7_ROSTER_MEMBER_FIELDS = candidate_id; authorization_evidence_id
P7_RECORDER_ID_FIELD = REMOVED_REUSE_CANDIDATE_V3
P7_XNYS_DUPLICATION_STATUS = REMOVED
P7_AQ_XNYS_ADAPTER_REUSED = YES
P7_UPSTREAM_ENSEMBLE_OWNER = MICROSOFT_QLIB_AVERAGEENSEMBLE
P7_QLIB_ONLINE_TAG_IS_CERTIFICATION_AUTHORITY = NO
P7_RUNTIME_READINESS_SEPARATED = YES
P7_ONLINE_MANAGER_EXECUTED = NO
P7_ROSTER_RUNTIME_LOC_BEFORE = 242
P7_ROSTER_RUNTIME_LOC_AFTER = 198
P7_REAL_LIFECYCLE_RECORDS_MODIFIED = 0
P7_REAL_MODEL_TRAINING_COUNT = 0
P7_REAL_PREDICTION_GENERATION_COUNT = 0
P7_REAL_ENSEMBLE_EXECUTION_COUNT = 0
P7_BACKTEST_COUNT = 0
P2_V2_COHORT_MODIFIED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P7_EXIT_CONDITION_SATISFIED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
ENVIRONMENT_MUTATED = NO
CURRENT_DEVELOPMENT_NEXT = P7_LIFECYCLE_DECISION_TO_EFFECTIVE_ROSTER_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_P7_ROSTER_UPDATE_POLICY_UPSTREAM_SUBSTITUTION_AUDIT
```

See [P7 variable-roster upstream handoff POC 001](p7-variable-roster-upstream-handoff-poc-001.md).

#### P7 lifecycle decision to effective roster protocol freeze (2026-09-27)

P7 now has one semantically corrected, research-only policy for converting
P2/P4 lifecycle evidence into a prospective daily XNYS roster. P7 research-
roster eligibility is distinct from the P4 Challenger role: `CERTIFIED`,
`SHADOW`, and `CHAMPION` are eligible; `RESEARCH_CANDIDATE`, `DEGRADED`, and
`RETIRED` are ineligible. A Champion's research-roster eligibility grants no
live-capital or production authority.

State reconstruction begins at `CERTIFIED` only with valid P2 evidence and
then applies accepted P4 state-changing decisions in authoritative order.
`NO_CHANGE`, `CHALLENGER_NEEDED`, `RESEARCH_REQUESTED`, and
`REJECT_TRANSITION` retain the prior state; a rejected target never becomes
current. Conflict, broken edges, ambiguous ordering, or missing authority
fails closed.

No existing P2/P4 artifact authorizes a whole P7 roster. The successor
protocol therefore replaces the unsupported whole-roster
`authorization_evidence_id` semantics with non-authoritative
`source_decision_bundle_identity` provenance. Member-level evidence references
remain. PR #116's runtime field is now aligned in PR #117 as
`source_decision_bundle_identity`; its RFC8785 identity projection binds that
provenance-only field, while member authorization semantics remain unchanged.

Updates are event-driven. The first usable session is the first XNYS session
strictly after the New York calendar date containing the verified UTC evidence
cutoff. There is no same-session or intraday activation, no periodic P7
reevaluation engine, and P12 remains scheduling owner. Roster count is
variable; 17 remains immutable historical snapshot metadata only. Fewer than
two authorized members or fewer than two session-active components fails
closed without fabricating or resurrecting members.

```text
P7_ROSTER_PROTOCOL_STATUS = FROZEN_PRE_EXECUTION_SEMANTICALLY_CORRECTED
P7_ROSTER_PROTOCOL_SHA256 = 2f9bd146822e7f85633b604812c779506d87e438a9ffda3f7f961de6a0a91812
P7_ROSTER_PROTOCOL_SUPERSEDED_ALIGNMENT_METADATA_SHA256 = 5034cd1fb5ef6969e7116fa63d5ac40ce22e05f8b16688e0e77f2f72bae97c02
P7_ROSTER_PROTOCOL_SUPERSEDED_PRE_CORRECTION_SHA256 = fa8107fe9bf834f1d088e22fcf2500f3160e94337bc92ff63e494519d0f4171e
P7_NORMATIVE_PROTOCOL_CONTAINS_GIT_PR_TASK_STATE = NO
P7_NORMATIVE_PROTOCOL_CONTAINS_TEMPORARY_IMPLEMENTATION_TODO = NO
P7_RESEARCH_ROSTER_ELIGIBLE_STATES = CERTIFIED; SHADOW; CHAMPION
P7_RESEARCH_ROSTER_INELIGIBLE_STATES = RESEARCH_CANDIDATE; DEGRADED; RETIRED
P7_ELIGIBILITY_AUTHORITY = P7_RESEARCH_ROSTER_PROJECTION_OVER_EXISTING_P2_P4_LIFECYCLE_STATE
P7_P4_CHALLENGER_ROLE_USED_AS_ROSTER_AUTHORITY = NO
P7_CHAMPION_ROSTER_ELIGIBILITY = ELIGIBLE_RESEARCH_ONLY_NO_PRODUCTION_OR_LIVE_CAPITAL_AUTHORITY
P7_WHOLE_ROSTER_AUTHORIZATION_FIELD = REMOVED_FROM_SUCCESSOR_PROTOCOL
P7_SOURCE_DECISION_BUNDLE_IDENTITY = NON_AUTHORITATIVE_PROVENANCE
P7_PR116_RUNTIME_FIELD_ALIGNMENT = PASS_IN_PR117
P7_ROSTER_MEMBER_COUNT_IS_FIXED = NO
P7_EFFECTIVE_SESSION_RULE = FIRST_XNYS_SESSION_STRICTLY_AFTER_CUTOFF_NEW_YORK_DATE
P7_MINIMUM_AUTHORIZED_MEMBER_COUNT = 2
P7_MINIMUM_SESSION_ACTIVE_COMPONENT_COUNT = 2
P7_PERIODIC_REEVALUATION_ENGINE = NONE
P7_ROSTER_PERSISTENCE_OWNER = DVC
P7_SCHEDULER_OWNER = P12
P7_REAL_CANDIDATE_SELECTION_COUNT = 0
P7_REAL_LIFECYCLE_TRANSITION_COUNT = 0
P7_REAL_ROSTER_MUTATION_COUNT = 0
P7_REAL_MODEL_TRAINING_COUNT = 0
P7_REAL_PREDICTION_GENERATION_COUNT = 0
P7_REAL_ENSEMBLE_COUNT = 0
P7_BACKTEST_COUNT = 0
P2_V2_COHORT_MODIFIED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P7_EXIT_CONDITION_SATISFIED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
AQ_NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = MERGE_GATE_PR_117
FINAL_CLASSIFICATION = PASS_P7_EFFECTIVE_ROSTER_SOURCE_BUNDLE_FIELD_ALIGNMENT
```

See [P7 lifecycle decision to effective roster protocol freeze 001](p7-lifecycle-decision-to-effective-roster-protocol-freeze-001.md).

#### P7 Qlib collector / rolling dynamic-pool substitution POC (2026-09-27)

A bounded synthetic POC exercised pinned Qlib Recorder/MLflow artifacts through
`RecorderCollector`, `RollingGroup` / `RollingEnsemble`, `MergeCollector`, the
existing P7 thin authorization and validation boundary, and
`AverageEnsemble`. Seven synthetic Recorders cover C1/C2 R1/R2 overlaps and
the existing 3 -> 5 -> 2 roster fixture. Qlib's later rolling window wins on
duplicate prediction identities, and the native chain exactly matches the
current pre-rolled path in index, values, roster periods and active-component
reports.

`OnlineToolR` is runtime readiness only. It is not Candidate authorization or
certification authority. Source audit confirms `OnlineManager` owns
per-strategy rolling updates, runtime history and signal preparation but not
P2/P4-driven cross-Candidate roster membership. P7 therefore retains only its
project-specific authorization projection plus strict row, numeric,
session-local constant and minimum-component gates.

No current runtime code is safely deletable: the existing 198-LOC handoff does
not duplicate Recorder retrieval, rolling stitching or multi-Candidate
collection. The POC instead prevents those capabilities from being added to
AQ during closeout.

```text
P7_QLIB_COLLECTOR_ROLLING_POC = PASS_PARTIAL_SUBSTITUTION
P7_QLIB_VERSION = 0.9.8.dev26
P7_QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
P7_RECORDER_COLLECTOR_STATUS = PASS
P7_MERGE_COLLECTOR_STATUS = PASS
P7_ROLLING_GROUP_STATUS = PASS
P7_ROLLING_ENSEMBLE_STATUS = PASS_LATEST_WINDOW_WINS
P7_AVERAGE_ENSEMBLE_STATUS = PASS_EXISTING_OWNER
P7_ONLINE_TOOL_R_STATUS = PASS_RUNTIME_READINESS_ONLY
P7_SYNTHETIC_ROSTER_SEQUENCE = 3_TO_5_TO_2
P7_SYNTHETIC_ROLLING_RECORDER_COUNT = 7
P7_CURRENT_PATH_VS_QLIB_NATIVE_PATH = EXACT_MATCH
P7_OUTPUT_INDEX_MATCH = YES
P7_OUTPUT_VALUE_MATCH = YES
P7_ROSTER_PERIOD_MATCH = YES
P7_ACTIVE_COMPONENT_MATCH = YES
P7_QLIB_ONLINE_TAG_IS_CERTIFICATION_AUTHORITY = NO
P7_ONLINE_MANAGER_PER_STRATEGY_ROLLING_OWNER = YES
P7_ONLINE_MANAGER_RUNTIME_HISTORY_OWNER = YES
P7_ONLINE_MANAGER_SIGNAL_PREPARATION_OWNER = YES
P7_ONLINE_MANAGER_DYNAMIC_ROSTER_AUTHORITY = NOT_NATIVE
P7_RUNTIME_LOC_BEFORE = 198
P7_RUNTIME_LOC_AFTER = 198
P7_NET_RUNTIME_LOC_CHANGE = 0
P7_REAL_CANDIDATE_ARTIFACTS_ACCESSED = 0
P7_REAL_MODEL_TRAINING_COUNT = 0
P7_REAL_MODEL_REFIT_COUNT = 0
P7_REAL_PREDICTION_GENERATION_COUNT = 0
P7_REAL_DYNAMIC_ROSTER_EXECUTION_COUNT = 0
P7_REAL_ENSEMBLE_EXECUTION_COUNT = 0
P7_BACKTEST_COUNT = 0
P7_PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_COHORT_MODIFIED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P7_QLIB_RUNTIME_SUBSTITUTION_CLOSEOUT_001
FINAL_CLASSIFICATION = PASS_PARTIAL_SUBSTITUTION
```

See [P7 Qlib collector / rolling dynamic-pool substitution POC 001](p7-qlib-collector-rolling-dynamic-pool-substitution-poc-001.md).

#### P7 Qlib runtime substitution closeout (2026-09-27)

The complete active P7 runtime boundary was audited against pinned Qlib source
and deletion counterfactuals. Qlib remains the sole owner of Recorder
collection, rolling grouping/ensembling, collector merging, per-strategy
online runtime management and `AverageEnsemble` numerical combination. P7
retains only external authorization/effective-roster projection, exact
eligible-row and numeric guards, session-local constant policy and the
minimum-active component rule.

No further runtime deletion is safe. Native Qlib accepts a common row omitted
by every component and emits a shorter result; an extreme finite component can
overflow during standardization and be silently omitted from the mean. These
tests prove the remaining guards prevent scientific population or roster
changes that the upstream runtime does not report.

```text
P7_RUNTIME_SUBSTITUTION_CLOSEOUT = PASS
P7_QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
P7_RUNTIME_SCOPE = time_effective_roster_handoff.py; session_local_router.py; average_ensemble_boundary.py
P7_TIME_EFFECTIVE_ROSTER_HANDOFF_PHYSICAL_LOC = 198
P7_SESSION_LOCAL_ROUTER_PHYSICAL_LOC = 55
P7_AVERAGE_ENSEMBLE_BOUNDARY_PHYSICAL_LOC = 99
P7_RUNTIME_PHYSICAL_LOC_TOTAL = 352
P7_RUNTIME_LOC_BEFORE = 352
P7_RUNTIME_LOC_AFTER = 352
P7_NET_RUNTIME_LOC_CHANGE = 0
P7_UNNECESSARY_DUPLICATION_COUNT = 0
P7_UPSTREAM_DELEGATED_LOC = 14
P7_IRREDUCIBLE_AQ_DOMAIN_POLICY_LOC = 116
P7_IRREDUCIBLE_FAIL_CLOSED_BOUNDARY_LOC = 153
P7_NEUTRAL_SCAFFOLDING_LOC = 69
P7_EXACT_ROW_GUARD_DECISION = RETAIN_IRREDUCIBLE_FAIL_CLOSED_BOUNDARY
P7_FINITE_NUMERIC_GUARD_DECISION = RETAIN_IRREDUCIBLE_FAIL_CLOSED_BOUNDARY
P7_EXTREME_VALUE_GUARD_DECISION = RETAIN_IRREDUCIBLE_FAIL_CLOSED_BOUNDARY
P7_EXACT_CONSTANT_POLICY_DECISION = RETAIN_IRREDUCIBLE_AQ_DOMAIN_POLICY
P7_MINIMUM_ACTIVE_COMPONENT_GATE_DECISION = RETAIN_IRREDUCIBLE_AQ_DOMAIN_POLICY
P7_RUNTIME_READY_GATE_DECISION = RETAIN_IRREDUCIBLE_FAIL_CLOSED_BOUNDARY
P7_ONLINE_MANAGER_DYNAMIC_ROSTER_AUTHORITY = NOT_NATIVE
P7_QLIB_ONLINE_TAG_IS_CERTIFICATION_AUTHORITY = NO
P7_FINAL_RUNTIME_BOUNDARY = EXTERNAL_AUTHORIZED_CANDIDATE_SET_TO_P7_VALIDATION_ROUTING_TO_QLIB_UPSTREAM_RUNTIME_ENSEMBLE
P7_RUNTIME_CLOSEOUT_TEST_RESULT = PASS_45_OF_45
P7_REAL_CANDIDATE_ARTIFACTS_ACCESSED = 0
P7_REAL_MODEL_TRAINING_COUNT = 0
P7_REAL_MODEL_REFIT_COUNT = 0
P7_REAL_PREDICTION_GENERATION_COUNT = 0
P7_REAL_DYNAMIC_ROSTER_EXECUTION_COUNT = 0
P7_REAL_ENSEMBLE_EXECUTION_COUNT = 0
P7_BACKTEST_COUNT = 0
P7_PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_COHORT_MODIFIED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P7_DYNAMIC_RESEARCH_EXECUTION_READINESS_AUDIT_001
FINAL_CLASSIFICATION = PASS_RUNTIME_SUBSTITUTION_CLOSED_NO_FURTHER_SAFE_DELETION
```

See [P7 Qlib runtime substitution closeout 001](p7-qlib-runtime-substitution-closeout-001.md).

#### P7 dynamic research execution readiness audit (2026-09-27)

P7 is mechanically ready at the Qlib runtime and statistical-tooling layers,
but it is not ready for real prospective dynamic-roster research. The real
lifecycle census is zero Certified, zero Shadow, zero Champion, zero Degraded
and zero Retired Candidates; therefore zero Candidates are currently eligible
for the frozen P7 roster and the minimum authorized count of two cannot be
met.

The historical surface is independently intact: all 17 original Formulaic
prediction artifacts, all 17 derived Candidate views, the selected OLS view
and the final eligible grid exist with their frozen hashes. A separately
preregistered research-only static ensemble is mechanically executable. It is
not dynamic-roster evidence, certification evidence or P7 exit evidence.

Prospective inference is a separate blocker. Candidate V3 records model bytes
as `NOT_PERSISTED_BY_UPSTREAM` for 17/17 Candidates, and the real Recorder
artifact directories contain no `params.pkl`, `task` or `dataset`. The OLS
control also has historical prediction bytes but no persisted model artifact.
Using their run configurations would require an unauthorized refit rather than
inference from frozen model state.

```text
P7_DYNAMIC_RESEARCH_EXECUTION_READINESS = NOT_READY_MULTIPLE_BLOCKERS
P7_REAL_CERTIFIED_CANDIDATE_COUNT = 0
P7_REAL_SHADOW_CANDIDATE_COUNT = 0
P7_REAL_CHAMPION_CANDIDATE_COUNT = 0
P7_REAL_DEGRADED_CANDIDATE_COUNT = 0
P7_REAL_RETIRED_CANDIDATE_COUNT = 0
P7_REAL_P2_CERTIFICATION_EVIDENCE_COUNT = 0
P7_REAL_P4_LIFECYCLE_DECISION_EVIDENCE_COUNT = 0
P7_REAL_ELIGIBLE_CANDIDATE_COUNT = 0
P7_MINIMUM_AUTHORIZED_MEMBER_COUNT = 2
P7_REAL_DYNAMIC_ROSTER_CAN_EXIST_NOW = NO
P7_FORMULAIC_17_HISTORICAL_PREDICTION_COUNT = 17
P7_FORMULAIC_17_HISTORICAL_PREDICTION_ARTIFACT_STATUS = PASS_17_EXISTS_AND_SHA256_MATCH
P7_CLOSEOUT_CHECKSUM_STATUS = PASS_28_OF_28
P7_CANDIDATE_V3_MANIFEST_HASH_STATUS = PASS_17_OF_17
P7_FORMULAIC_17_MODEL_BYTES_PERSISTED_COUNT = 0
P7_FORMULAIC_17_PROSPECTIVE_INFERENCE_READY_COUNT = 0
P7_OLS_HISTORICAL_PREDICTION_AVAILABLE = YES
P7_OLS_MODEL_ARTIFACT_AVAILABLE = NO
P7_OLS_PROSPECTIVE_INFERENCE_READY = NO_REQUIRES_REFIT
P7_QLIB_DYNAMIC_RUNTIME_MECHANICS_READY = YES_CONDITIONAL_ON_VALID_AUTHORIZED_MODEL_RECORDERS
P7_FAIREST_PROSPECTIVE_CONTROL = PROSPECTIVE_FIXED_ROSTER_AT_STUDY_START
P7_FAIREST_PROSPECTIVE_CONTROL_READINESS = NO
P7_HISTORICAL_STATIC_ENSEMBLE_EXECUTION_READY = YES_RESEARCH_ONLY_NOT_DYNAMIC_NOT_CERTIFICATION
P7_STATISTICAL_STACK_READY = YES_MECHANICALLY_ONCE_PROSPECTIVE_OBSERVATIONS_EXIST
P7_RETROACTIVE_SYNTHETIC_P2_CERTIFICATION_FOR_VALUE_TEST = PROHIBITED
P7_RETROACTIVE_SYNTHETIC_P4_LIFECYCLE_FOR_VALUE_TEST = PROHIBITED
P7_HISTORICAL_PERFORMANCE_DERIVED_LIFECYCLE_EVENTS = PROHIBITED
P7_REAL_LIFECYCLE_RECORDS_MODIFIED = 0
P7_REAL_ROSTER_MUTATION_COUNT = 0
P7_MODEL_TRAINING_COUNT = 0
P7_MODEL_REFIT_COUNT = 0
P7_PREDICTION_GENERATION_COUNT = 0
P7_REAL_DYNAMIC_ENSEMBLE_EXECUTION_COUNT = 0
P7_REAL_STATIC_ENSEMBLE_EXECUTION_COUNT = 0
P7_BACKTEST_COUNT = 0
P7_PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
ENVIRONMENT_MUTATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P7_PROSPECTIVE_MODEL_PERSISTENCE_UPSTREAM_SUBSTITUTION_AUDIT_001
P7_INDEPENDENT_OPTIONAL_STATIC_ROUTE = P7_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = NOT_READY_MULTIPLE_BLOCKERS
```

See [P7 dynamic research execution readiness audit 001](p7-dynamic-research-execution-readiness-audit-001.md).

---

#### P3 Candidate Qlib Recorder upstream persistence audit (2026-09-27)

The 17 immutable Formulaic Candidate V3 Recorders lack `task`, `params.pkl`
and `dataset` because the P3 producer directly executed `R.start`, manual
`LinearModel.fit`, `SignalRecord` and `SigAnaRecord`; it did not use pinned
Qlib's `TrainerR` / `task_train` path. All 17 Recorders contain predictions,
labels and signal analysis, while all 17 lack the three runtime artifacts.

Pinned Qlib natively persists `task`, `params.pkl` and `dataset` through the
standard task-training path, and `RMDLoader` / `PredUpdater` consume the
persisted model and dataset. RD-Agent's native Qlib workspace already invokes
`qrun`, which delegates to `task_train`. Candidate V3 already supports a real
`PERSISTED` serialized-model identity, so no successor contract, AQ model
store, serializer, Recorder builder or P7 persistence implementation is
required.

```text
CURRENT_17_MISSING_ARTIFACT_ROOT_CAUSE = STANDARD_QLIB_TRAINERR_PATH_NOT_USED
CANDIDATE_MODEL_TRAINING_OWNER = QLIB / P3 PRODUCER PATH
RUNTIME_MODEL_STATE_OWNER = QLIB_RECORDER
RUN_LINEAGE_OWNER = QLIB_MLFLOW
REPRODUCIBILITY_OWNER = DVC
P7_ROLE = DOWNSTREAM_CONSUMER_ONLY
CANDIDATE_V3_SUPPORTS_PERSISTED_MODEL_BINDING = YES
CANDIDATE_SUCCESSOR_CONTRACT_REQUIRED = NO
MLFLOW_MODEL_REGISTRY_ROLE = NOT_REQUIRED
CURRENT_17_MODEL_STATE = HISTORICAL_PREDICTION_ONLY
CURRENT_17_PROSPECTIVE_INFERENCE_READY = NO
AQ_MODEL_STORE_REQUIRED = NO
AQ_MODEL_SERIALIZER_REQUIRED = NO
AQ_RECORDER_BUILDER_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_P3_PRODUCTION_LOC = 0
NEW_P7_PRODUCTION_LOC = 0
CURRENT_DEVELOPMENT_NEXT = P3_FUTURE_CANDIDATE_QLIB_TRAINERR_PATH_ALIGNMENT_001
FINAL_CLASSIFICATION = PASS_STANDARD_QLIB_PERSISTENCE_PATH_WAS_BYPASSED
```

See [P3 Candidate Qlib Recorder upstream persistence audit 001](p3-candidate-qlib-recorder-upstream-persistence-audit-001.md).

---

#### P3 future Candidate Qlib-native handoff POC (2026-09-27)

A bounded non-Candidate fixture proved the complete native future-production
path through pinned Qlib `task_train`. Qlib created `task`, `params.pkl`,
`dataset` and `pred.pkl` without manual Recorder writes. `RMDLoader` reloaded
the model and dataset, and bounded `PredUpdater` replays extended the fixture
while preserving the historical prefix exactly.

RD-Agent already owns the complete `qrun -> task_train` handoff. AlphaGen
supplies expression identity plus materialized factor Parquet; existing Qlib
`StaticDataLoader` and task configuration are sufficient, so no executable
AlphaGen adapter or AQ training runtime is required. Candidate V3's existing
`PERSISTED` union accepts the actual `params.pkl` content identity alongside
the Recorder run identity without a schema change.

```text
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
RD_AGENT_FUTURE_CANDIDATE_HANDOFF = UPSTREAM_WHOLE
ALPHAGEN_OUTPUT_TYPE = EXPRESSION_IDENTITY_PLUS_MATERIALIZED_FACTOR_PARQUET
ALPHAGEN_TO_QLIB_HANDOFF = QLIB_TASK_CONFIG_WITH_STATICDATALOADER_PARQUET
ALPHAGEN_TO_QLIB_RESIDUAL = TASK_CONFIGURATION_ONLY
QLIB_NATIVE_ENTRY_USED = qlib.model.trainer.task_train
SYNTHETIC_RECORDER_TASK_PRESENT = YES
SYNTHETIC_RECORDER_PARAMS_PRESENT = YES
SYNTHETIC_RECORDER_DATASET_PRESENT = YES
SYNTHETIC_RECORDER_PRED_PRESENT = YES
PERSISTED_MODEL_RELOAD = PASS
PERSISTED_DATASET_RELOAD = PASS
BOUNDED_PREDUPDATER = PASS
HISTORICAL_PREFIX_UNCHANGED = PASS
CANDIDATE_V3_PERSISTED_BINDING = PASS_PARAMS_PKL_CONTENT_SHA_PLUS_RECORDER_IDENTITY
CANDIDATE_V3_SCHEMA_CHANGE_REQUIRED = NO
RUNTIME_MODEL_STATE_OWNER = QLIB_RECORDER
RUN_LINEAGE_OWNER = QLIB_MLFLOW
REPRODUCIBILITY_OWNER = DVC
AQ_TRAINING_ENGINE = NO
AQ_MODEL_STORE = NO
AQ_RECORDER_BUILDER = NO
ALPHAGEN_THIN_ADAPTER_REQUIRED = NO
NEW_PRODUCTION_LOC = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_17_REFIT_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P3_FUTURE_CANDIDATE_UPSTREAM_PATH_FREEZE_001
FINAL_CLASSIFICATION = PASS_RD_AGENT_NATIVE_AND_ALPHAGEN_CONFIG_ONLY_HANDOFF
```

See [P3 future Candidate Qlib-native handoff POC 001](p3-future-candidate-qlib-native-handoff-poc-001.md).

---

#### P3 future Candidate upstream path freeze (2026-09-27)

P3 future-Candidate production architecture is closed. RD-Agent uses its
native `qrun -> task_train` path; AlphaGen supplies immutable expression and
materialized factor identities to native Qlib task configuration. Qlib owns
training, Recorder model state and prediction runtime; Qlib/MLflow owns run
lineage and DVC owns reproducibility. Candidate V3 already binds a persisted
`params.pkl` content identity plus its existing Recorder identity, so neither a
schema change nor Candidate V4 is required.

The historical 17 Candidates remain immutable historical-prediction-only
evidence. Their missing runtime model artifacts are not retrofitted, and any
future retraining must create new model, Recorder, and Candidate identities.
P2 certification, P4 lifecycle authority and P7 roster authorization remain
external to Qlib Recorder/runtime state.

```text
RD_AGENT_FUTURE_CANDIDATE_HANDOFF = UPSTREAM_WHOLE_QRUN_TO_QLIB_TASK_TRAIN
ALPHAGEN_FUTURE_CANDIDATE_HANDOFF = EXPRESSION_IDENTITY_PLUS_MATERIALIZED_FACTOR_PARQUET_TO_QLIB_TASK_CONFIG
MODEL_TRAINING_OWNER = QLIB
RUNTIME_MODEL_STATE_OWNER = QLIB_RECORDER
PREDICTION_RUNTIME_OWNER = QLIB
RUN_LINEAGE_OWNER = QLIB_MLFLOW
REPRODUCIBILITY_OWNER = DVC
CANDIDATE_V3_SCHEMA_CHANGE_REQUIRED = NO
CANDIDATE_V4_REQUIRED = NO
MANUAL_MODEL_FIT_FOR_REAL_CANDIDATE = PROHIBITED_BY_DEFAULT
MANUAL_RECORDER_MODEL_PERSISTENCE = PROHIBITED_BY_DEFAULT
MANUAL_PARAMS_PKL_WRITE = PROHIBITED_BY_DEFAULT
AQ_TRAINING_ENGINE = NO
AQ_MODEL_STORE = NO
AQ_MODEL_SERIALIZER = NO
AQ_RECORDER_BUILDER = NO
AQ_MODEL_REGISTRY = NO
AQ_PREDICTION_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
CURRENT_17_REFIT_COUNT = 0
CURRENT_17_RECORDER_MUTATION_COUNT = 0
CURRENT_17_CANDIDATE_IDENTITY_CHANGE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_FUTURE_CANDIDATE_UPSTREAM_PATH_FROZEN
```

See [P3 future Candidate upstream path freeze 001](p3-future-candidate-upstream-path-freeze-001.md).

---

#### P3 RD-Agent native handoff thin Candidate projection POC (2026-09-27)

The existing native `fin_quant -> qrun -> task_train -> Recorder` path remains
unchanged. Repository and private-evidence audit found no reusable RD-Agent
Candidate V3 materializer: the historical private materializer is
Formulaic-specific, while the prior native-handoff POC validated only the
persisted-model union. A 99-line pure projection leaf now validates explicit
RD-Agent/Qlib/AQ identities, hashes existing Recorder artifacts, delegates
canonicalization to `rfc8785==0.1.4`, and validates the unchanged Candidate V3
schema. It owns no training, prediction, Recorder lifecycle, registry, or loop.

The bounded proof reused the existing `TEST_FIXTURE_NOT_REAL_CANDIDATE`
Recorder produced earlier by native Qlib `task_train`; no training was rerun.
Its `task`, `params.pkl`, `dataset`, and `pred.pkl` are present, and the full
RD-Agent Candidate V3 projection passed schema validation and identity
recomputation. The RD-Agent branch inherited from Candidate V1 represents a
persisted model as its required `serialized_model_artifact` content identity
rather than the Formulaic branch's literal `status` union; the POC records the
equivalent `PERSISTED` state without changing the schema.

```text
RDAGENT_PROJECT_PIN_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
RDAGENT_CURRENT_UPSTREAM_SHA = 484776c211e4fbbeef03e0ec00d6bbee7362a4f4
RDAGENT_PIN_BEHIND_BY_COMMITS = 5
FIN_QUANT_RELEVANT_DIFF_COUNT = 0
PIN_UPGRADE_REQUIRED = NO
EXISTING_RDAGENT_CANDIDATE_MATERIALIZER_FOUND = NO
MATERIALIZER_REUSE_CLASSIFICATION = MISSING
THIN_PROJECTION_IMPLEMENTED = YES
THIN_PROJECTION_NEW_LOC = 99
QLIB_NATIVE_TASK_TRAIN_USED_FOR_FIXTURE = YES_REUSED_EXISTING_RECORDER
CANDIDATE_V3_SCHEMA_VALID = YES
CANDIDATE_V3_IDENTITY_VALID = YES
PERSISTED_MODEL_BINDING_VALID = YES
AQ_CUSTOM_CANONICALIZER = NO
AQ_P3_AUTONOMOUS_LOOP_LOC = 0
AQ_P3_TRAINING_ENGINE_LOC = 0
AQ_P3_RECORDER_ENGINE_LOC = 0
AQ_P3_MODEL_STORE_LOC = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
RD_AGENT_LLM_CALL_COUNT = 0
REAL_AUTONOMOUS_LOOP_COUNT = 0
REAL_MODEL_TRAINING_COUNT = 0
REAL_CANDIDATE_CREATED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P3_RDAGENT_FIN_QUANT_AUTONOMOUS_LOOP_REACTIVATION_001
FINAL_CLASSIFICATION = PASS_RDAGENT_NATIVE_HANDOFF_THIN_CANDIDATE_PROJECTION_POC
```

See [P3 RD-Agent native handoff thin Candidate projection POC 001](p3-rdagent-native-handoff-thin-candidate-projection-poc-001.md).

---

#### P7 historical static ensemble research protocol freeze (2026-09-27)

One research-only historical static ensemble protocol is frozen before result
access. It binds the exact 17 Formulaic Candidate V3 snapshot, complete
374,591-row P7 input contract, and preregistered OLS Alpha158 control. Pinned
Qlib `AverageEnsemble` owns session-local standardization and equal averaging;
exact constants are inactive only for their session and at least two active
components remain mandatory.

Daily cross-sectional RankIC delta versus OLS is the sole primary endpoint.
arch SPA owns the one preregistered primary inference, skfolio WalkForward and
CPCV own robustness partitions only, and arch MCS supplies a descriptive
ensemble-plus-17-component family diagnostic. The frozen P2 V2 Top-30/drop-3
configuration is authorized only as a secondary descriptive projection.

```text
STUDY_TYPE = RESEARCH_ONLY_HISTORICAL_STATIC_ENSEMBLE
PRISTINE_OOS = NO
P2_CERTIFICATION_EVIDENCE = NO
P7_DYNAMIC_ROSTER_EVIDENCE = NO
P7_EXIT_CONDITION_EVIDENCE = NO
MASTER_CANDIDATE_COUNT = 17
INDEPENDENT_ALPHA_FAMILY_COUNT = 1
ROW_COUNT = 374591
SESSION_COUNT = 751
INSTRUMENT_COUNT = 547
POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
INPUT_CONTRACT_SHA256 = 92de81d0b8b7b7a29891bf523ae8519af44456f52fea3410ebf0ebd210d0f81f
ENSEMBLE_OWNER = QLIB_AVERAGEENSEMBLE
ENSEMBLE_WEIGHTING = SESSION_LOCAL_NONCONSTANT_COMPONENT_EQUAL_WEIGHT
MINIMUM_ACTIVE_COMPONENT_COUNT = 2
PRIMARY_METRIC = DAILY_CROSS_SECTIONAL_RANK_IC
PRIMARY_COMPARISON = STATIC_17_ENSEMBLE_MINUS_OLS_ALPHA158_CONTROL
PRIMARY_ENDPOINT = MEAN_DAILY_RANK_IC_DELTA_VS_OLS_CONTROL
MULTIPLE_COMPARISON_PROCEDURE = ARCH_8_0_0_MCS_DESCRIPTIVE_18_SIGNAL_FAMILY
TEMPORAL_CV_RESTORES_PRISTINE_OOS = NO
PORTFOLIO_PROJECTION_STATUS = AUTHORIZED_SECONDARY_REUSE_FROZEN_P2_V2_CONFIGURATION
RESULT_CLASSIFICATIONS = STATIC_ENSEMBLE_RESEARCH_SUPPORTIVE; STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE; STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
PROTOCOL_SHA256 = b60078bdba4190fbda2c6f3d3580f0e40a9801c87867095bfaa12885a0fb3ff4
PROTOCOL_STATUS = FROZEN_PRE_EXECUTION
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PORTFOLIO_BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_EXECUTION_001
FINAL_CLASSIFICATION = PASS_P7_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_PROTOCOL_FROZEN
```

See [P7 historical static ensemble research protocol freeze 001](p7-historical-static-ensemble-research-protocol-freeze-001.md).

---

#### P7 historical static ensemble one-shot execution (2026-09-27)

The frozen protocol's Phase A passed all input-identity and synthetic upstream
API checks. Phase B then began exactly once. The attempt stopped fail-closed
before ensemble combination or metric calculation because the frozen label
artifact contained missing or non-finite values after projection to the exact
374,591-row population. The one-shot firewall prohibits repair and retry after
real outcome access, so the sealed result is inconclusive and contains no
evidence for or against the ensemble.

```text
PROTOCOL_SHA256 = b60078bdba4190fbda2c6f3d3580f0e40a9801c87867095bfaa12885a0fb3ff4
REAL_OUTCOME_ACCESS_STARTED = YES
REAL_OUTCOME_EXECUTION_ATTEMPT_COUNT = 1
RESULT_CLASSIFICATION = STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PORTFOLIO_BACKTEST_COUNT = 0
PRISTINE_OOS = NO
P2_CERTIFICATION_EVIDENCE = NO
P7_DYNAMIC_ROSTER_EVIDENCE = NO
P7_EXIT_CONDITION_EVIDENCE = NO
PRODUCTION_AUTHORIZATION = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_HISTORICAL_STATIC_ENSEMBLE_INCONCLUSIVE_RESULT_CLOSEOUT_001
```

See [P7 historical static ensemble research execution 001](p7-historical-static-ensemble-research-execution-001.md).

---

#### P7 historical static ensemble terminal inconclusive closeout (2026-09-27)

P7 V1 is permanently closed as `STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE`;
repair, protocol mutation and rerun are prohibited. A structural-only audit
found that all 374,591 population keys exist in the frozen label artifact, but
114 present rows contain NaN. There are no absent keys or infinite values.
The affected rows span 74 sessions and 57 instruments.

The 114 rows resolve completely to structural availability conditions: 72
membership episodes ended before the complete two-session label horizon and
42 rows coincide with known provider gaps. No unresolved row remains. The
input qualification checked the global calendar horizon but omitted a
row-level finite-label eligibility gate. Qlib remains the label-generation and
label-semantics owner; AQ may add only a thin fail-closed integrity contract in
any independently authorized successor study.

The V1 attempt manifest also did not bind the execution script content SHA or
a pre-outcome commit containing that script. This provenance gap does not
change the terminal classification. Any successor one-shot study must commit
its execution code before outcome access and bind the code SHA in its attempt
manifest. V1 provides no performance evidence for or against the ensemble.

```text
V1_EXECUTION_STATUS = TERMINAL_INCONCLUSIVE
V1_RERUN_ALLOWED = NO
LABEL_POPULATION_ROW_COUNT = 374591
LABEL_KEY_ABSENT_COUNT = 0
LABEL_PRESENT_NAN_COUNT = 114
LABEL_PRESENT_INF_COUNT = 0
LABEL_AFFECTED_SESSION_COUNT = 74
LABEL_AFFECTED_INSTRUMENT_COUNT = 57
LABEL_FAILURE_CAUSE_COUNTS = MEMBERSHIP_EPISODE_ENDED_BEFORE_LABEL_HORIZON:72; KNOWN_PROVIDER_GAP:42
UNRESOLVED_LABEL_FAILURE_ROW_COUNT = 0
CALENDAR_LEVEL_LABEL_HORIZON_CHECK = YES
ROW_LEVEL_LABEL_FINITE_CHECK = NO
INPUT_CONTRACT_GAP = INPUT_CONTRACT_OMITTED_ROW_LEVEL_LABEL_ELIGIBILITY
FUTURE_LABEL_GENERATION_OWNER = QLIB
FUTURE_LABEL_SEMANTICS_OWNER = QLIB
FUTURE_LABEL_INTEGRITY_OWNER = AQ_THIN_FAIL_CLOSED_CONTRACT
PRE_OUTCOME_EXECUTION_SCRIPT_CONTENT_SHA_BOUND = NO
PRE_OUTCOME_EXECUTION_COMMIT_BOUND = NO
FUTURE_ONE_SHOT_EXECUTION_CODE_MUST_BE_COMMITTED_BEFORE_OUTCOME_ACCESS = YES
FUTURE_ATTEMPT_MANIFEST_MUST_BIND_EXECUTION_CODE_SHA256 = YES
V1_PROVIDES_PERFORMANCE_EVIDENCE_FOR_ENSEMBLE = NO
V1_PROVIDES_PERFORMANCE_EVIDENCE_AGAINST_ENSEMBLE = NO
SUCCESSOR_RESEARCH_ADMISSIBILITY = REQUIRES_INDEPENDENT_REVIEW
AQ_LABEL_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_POST_INCONCLUSIVE_SUCCESSOR_RESEARCH_ADMISSIBILITY_AUDIT_001
FINAL_CLASSIFICATION = PASS_P7_STATIC_ENSEMBLE_V1_TERMINAL_INCONCLUSIVE_CLOSEOUT
```

See [P7 historical static ensemble inconclusive result closeout 001](p7-historical-static-ensemble-inconclusive-result-closeout-001.md).

---

#### P7 post-inconclusive successor research admissibility (2026-09-27)

An independent scientific review found that a wholly new successor study is
permissible with explicit post-failure disclosure. V1 remains permanently
`STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE` and is not superseded. No performance,
prediction relationship, or label magnitude was exposed; the post-failure
information is limited to structural label observability.

A successor may use only a preregistered rule requiring a valid prediction and
control population row, present label key, and finite label. This changes the
estimand to one conditional on preregistered label observability. The 72
membership-horizon and 42 provider-gap exclusions are not assumed MCAR and
require explicit structural coverage disclosure without imputation or
performance stratification.

Pinned Qlib remains the label-generation and semantics owner. Qlib natively
stores missing raw labels and `DropnaLabel` removes missing labels only for
learning; AQ may own only the thin fail-closed input-contract gate. A successor
requires new study, protocol, input-contract, population, label-mask, and
execution-attempt identities, plus pre-outcome committed execution code and a
manifest-bound script SHA.

```text
V1_EXECUTION_STATUS = TERMINAL_INCONCLUSIVE
V1_RERUN_ALLOWED = NO
V1_RESULT = STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
V1_IS_SUPERSEDED = NO
PERFORMANCE_INFORMATION_EXPOSED = NO
PREDICTION_PERFORMANCE_RELATIONSHIP_EXPOSED = NO
LABEL_MAGNITUDE_INFORMATION_EXPOSED = NO
PROPOSED_SUCCESSOR_ROW_RULE = PREDICTION_CONTROL_POPULATION_VALID AND LABEL_KEY_PRESENT AND LABEL_FINITE
ROW_RULE_PERFORMANCE_INDEPENDENT = YES
ROW_RULE_LABEL_MAGNITUDE_INDEPENDENT = YES
ROW_RULE_STRUCTURAL_OBSERVABILITY_BASED = YES
MISSINGNESS_ASSUMPTION = NOT_MCAR
ESTIMAND_CHANGED_FROM_V1 = YES
SUCCESSOR_ESTIMAND = CONDITIONAL_ON_PREREGISTERED_LABEL_OBSERVABILITY
POST_FAILURE_INFORMATION_CONTAMINATION = LIMITED_STRUCTURAL_ONLY
STRUCTURAL_MISSINGNESS_DISCLOSURE_REQUIRED = YES
QLIB_SUPPORTS_MISSING_LABEL_STATE = YES
QLIB_NATIVE_LEARNING_DROPS_MISSING_LABELS = YES
FUTURE_ROW_LEVEL_LABEL_GATE_COMPATIBLE_WITH_QLIB = YES
FILL_LABEL_WITH_ZERO = PROHIBITED
FORWARD_FILL_LABEL = PROHIBITED
BACKFILL_LABEL = PROHIBITED
SYNTHETIC_RETURN_IMPUTATION = PROHIBITED
CUSTOM_AQ_LABEL_GENERATION = PROHIBITED
SUCCESSOR_RESEARCH_ADMISSIBILITY = SCIENTIFICALLY_PERMISSIBLE_WITH_POST_FAILURE_DISCLOSURE
AQ_LABEL_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_STATIC_ENSEMBLE_LABEL_OBSERVABLE_INPUT_CONTRACT_FREEZE_001
FINAL_CLASSIFICATION = PASS_P7_SUCCESSOR_RESEARCH_SCIENTIFICALLY_PERMISSIBLE_WITH_POST_FAILURE_DISCLOSURE
```

See [P7 post-inconclusive successor research admissibility audit 001](p7-post-inconclusive-successor-research-admissibility-audit-001.md).

---

#### P7 successor label-observable input contract freeze (2026-09-27)

A wholly new successor input contract is frozen without creating a research
protocol or accessing performance. It retains the exact 17 Candidate V3
identities and source hashes, OLS control, Qlib label, signs, roster, weighting
and primary comparator. V1 remains terminal inconclusive and is not
superseded.

The only new eligibility condition is structural: an otherwise valid V1
prediction/control population row must have a present, finite Qlib label. The
374,591-row Boolean mask excludes exactly the 114 sealed invalid-label rows,
producing a 374,477-row successor grid. All 751 sessions remain, with at least
490 rows per session. Candidate and OLS coverage passes by their previously
sealed complete V1-grid coverage and the strict-subset relationship.

```text
V1_RESULT = STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
V1_IS_SUPERSEDED = NO
SUCCESSOR_ESTIMAND = CONDITIONAL_ON_PREREGISTERED_LABEL_OBSERVABILITY
SUCCESSOR_ROW_RULE = V1_PREDICTION_CONTROL_POPULATION_VALID AND LABEL_KEY_PRESENT AND LABEL_FINITE
LABEL_SHA256 = c14c7c3f1e698126663b85dfcf436cf3258dc4609e8217e95ed188d9be7db35e
LABEL_VALIDITY_MASK_ROW_COUNT = 374591
LABEL_VALIDITY_MASK_SHA256 = 2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf
V1_ROW_COUNT = 374591
SUCCESSOR_ROW_COUNT = 374477
EXCLUDED_ROW_COUNT = 114
MEMBERSHIP_HORIZON_EXCLUSION_COUNT = 72
PROVIDER_GAP_EXCLUSION_COUNT = 42
MISSINGNESS_ASSUMPTION = NOT_MCAR
SUCCESSOR_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
SUCCESSOR_SESSION_COUNT = 751
SUCCESSOR_INSTRUMENT_COUNT = 547
SUCCESSOR_START = 2022-01-03
SUCCESSOR_END = 2024-12-27
SUCCESSOR_MINIMUM_ROWS_PER_SESSION = 490
SUCCESSOR_ALL_SESSIONS_RANKIC_STRUCTURALLY_FEASIBLE = YES
CANDIDATE_17_SUCCESSOR_ROW_COVERAGE = PASS
OLS_SUCCESSOR_ROW_COVERAGE = PASS
SUCCESSOR_INPUT_CONTRACT_SHA256 = b693f43b8dfab0fa04cb12a876fc32928bc5020592a2e137f1c0cbfdde0639ee
LABEL_GENERATION_OWNER = QLIB
LABEL_SEMANTICS_OWNER = QLIB
AQ_LABEL_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_RESEARCH_PROTOCOL_FREEZE_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_LABEL_OBSERVABLE_INPUT_CONTRACT_FROZEN
```

See [P7 successor static-ensemble label-observable input-contract freeze 001](p7-successor-static-ensemble-label-observable-input-contract-freeze-001.md).

---

#### P7 successor historical static-ensemble research protocol freeze (2026-09-27)

A wholly new research-only successor protocol is frozen before successor
outcome access. V1 remains permanently `STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE`,
is not superseded, and may not be rerun. The successor binds the exact
label-observable input contract and preserves every V1 pre-outcome scientific
and statistical choice because V1 exposed no performance information.

The successor estimand is conditional on preregistered label observability.
Its 374,477-row population excludes 114 structurally unavailable labels from
V1: 72 membership-horizon rows and 42 provider-gap rows. Missingness is not
assumed MCAR, and results generalize only to this frozen label-observable
population.

```text
V1_RESULT = STATIC_ENSEMBLE_RESEARCH_INCONCLUSIVE
V1_IS_SUPERSEDED = NO
SUCCESSOR_STUDY_TYPE = NEW_RESEARCH_ONLY_POST_FAILURE_DISCLOSED_HISTORICAL_STATIC_ENSEMBLE
SUCCESSOR_ESTIMAND = CONDITIONAL_ON_PREREGISTERED_LABEL_OBSERVABILITY
SUCCESSOR_INPUT_CONTRACT_SHA256 = b693f43b8dfab0fa04cb12a876fc32928bc5020592a2e137f1c0cbfdde0639ee
SUCCESSOR_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
LABEL_VALIDITY_MASK_SHA256 = 2d0c312c509625ebab0460f7024866b7f629e39e67384b907fef65373aaa59bf
MASTER_CANDIDATE_COUNT = 17
INDEPENDENT_ALPHA_FAMILY_COUNT = 1
ENSEMBLE_OWNER = QLIB_AVERAGEENSEMBLE
ENSEMBLE_WEIGHTING = SESSION_LOCAL_NONCONSTANT_COMPONENT_EQUAL_WEIGHT
PRIMARY_METRIC = DAILY_CROSS_SECTIONAL_RANK_IC
PRIMARY_COMPARISON = STATIC_17_ENSEMBLE_MINUS_OLS_ALPHA158_CONTROL
PRIMARY_ENDPOINT = MEAN_DAILY_RANK_IC_DELTA_VS_OLS_CONTROL
WALKFORWARD_USABLE_FOLD_COUNT = 3
CPCV_USABLE_SPLIT_COUNT = 45
RESULTS_GENERALIZE_ONLY_TO = LABEL_OBSERVABLE_EVALUATION_POPULATION
EXECUTION_CODE_MUST_BE_COMMITTED_PRE_OUTCOME = YES
DIRTY_WORKTREE_ALLOWED = NO
SUCCESSOR_PROTOCOL_SHA256 = a4ca307c3e3a245bb211978d36f03d8a2552c81df28049ddb6b667231689a894
SUCCESSOR_PROTOCOL_STATUS = FROZEN_PRE_EXECUTION_CODE
ENSEMBLE_EXECUTION_COUNT = 0
RANKIC_COMPUTATION_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_CODE_PRECOMMIT_AND_PREFLIGHT_FREEZE_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_PROTOCOL_FROZEN
```

See [P7 successor historical static-ensemble research protocol freeze 001](p7-successor-historical-static-ensemble-research-protocol-freeze-001.md).

---

#### P7 successor signal-construction/evaluation boundary correction (2026-09-27)

A pre-outcome audit found that the first successor protocol applied the
label-observable evaluation population before Qlib `AverageEnsemble`. Because
Qlib standardizes each component cross-sectionally by session before equal
averaging, that ordering would let future label observability alter signal
construction. Corrected authorities now construct the signal on the complete
374,591-row V1 prediction/control population and apply the 374,477-row
label-observable population only afterward for primary evaluation.

Secondary failure semantics are also explicit. Constant-session component
RankIC remains unavailable without imputation. Incomplete MCS, portfolio, or
post-primary lineage evidence is recorded separately and cannot change a
complete six-gate primary classification. V1 remains terminal inconclusive and
is not superseded. The open PR #130 script is not authorizable and must be
rebased/regenerated against these corrected identities and semantics.

```text
SIGNAL_CONSTRUCTION_POPULATION = V1_PREDICTION_CONTROL_POPULATION
SIGNAL_CONSTRUCTION_ROW_COUNT = 374591
SIGNAL_CONSTRUCTION_POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
EVALUATION_POPULATION = SUCCESSOR_LABEL_OBSERVABLE_POPULATION
EVALUATION_ROW_COUNT = 374477
EVALUATION_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
LABEL_OBSERVABILITY_USED_IN_SIGNAL_CONSTRUCTION = NO
PORTFOLIO_SIGNAL_POPULATION = V1_PREDICTION_CONTROL_POPULATION
COMPONENT_CONSTANT_SESSION_RANKIC_POLICY = UNAVAILABLE_NAN_NOT_IMPUTED_NOT_ZERO
MCS_NON_GATING_FAILURE_POLICY = NOT_AVAILABLE_SECONDARY_INCOMPLETE_LOSS_MATRIX_NO_PRIMARY_CLASSIFICATION_EFFECT
PORTFOLIO_NON_GATING_FAILURE_POLICY = RECORD_FAILURE_NO_PRIMARY_CLASSIFICATION_EFFECT
PRIOR_SUCCESSOR_INPUT_CONTRACT_SHA256 = b693f43b8dfab0fa04cb12a876fc32928bc5020592a2e137f1c0cbfdde0639ee
CORRECTED_SUCCESSOR_INPUT_CONTRACT_SHA256 = b9e0c447794c318d7ddc00803e0f2ea5468abc4c77a43752ead2910804b8a7b5
PRIOR_SUCCESSOR_PROTOCOL_SHA256 = a4ca307c3e3a245bb211978d36f03d8a2552c81df28049ddb6b667231689a894
CORRECTED_SUCCESSOR_PROTOCOL_SHA256 = cb61628ed49ca0f9d9798f92567adedbeb533f6854da098ec3c945b38bdbd76a
OLD_PR130_SCRIPT_AUTHORIZABLE = NO
REAL_OUTCOME_ACCESS_STARTED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_CODE_REBASE_AFTER_BOUNDARY_CORRECTION_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_SIGNAL_CONSTRUCTION_EVALUATION_BOUNDARY_CORRECTED_PRE_OUTCOME
```

See [P7 successor signal-construction/evaluation boundary correction 001](p7-successor-signal-construction-evaluation-boundary-correction-001.md).

---

#### P7 successor execution code rebased after boundary correction (2026-09-27)

PR #130 now consumes the PR #131 corrected authorities. Qlib
`AverageEnsemble` runs on the complete 374,591-row signal-construction
population before the 374,477-row label-observable evaluation projection.
Portfolio signals remain on the full construction population. Primary
ensemble/control RankIC and the six-gate SPA/WalkForward/CPCV evidence are
strict; component-summary, MCS, portfolio, and post-primary lineage failures
are secondary and cannot change a locked primary classification.

The future provenance seal must bind separate construction/evaluation
population artifact byte identities and both ordered-index semantic identities.
The old PR #130 script SHA and the first boundary-corrected script SHA
`996a9fe439651ef377337405fac85449bd8abd1d82851b9fc79e69536a03267b`
are retired. The remaining self-reference was removed: the future seal does not
store its own authority commit. HEAD must equal `origin/main`; the seal's
Git-derived last-change commit must equal HEAD; working-tree seal bytes must
equal `HEAD:<seal-path>`; and the sealed execution commit must be an ancestor
whose script blob and current runtime script both match the sealed script hash.
No seal was created and no real outcome was opened.

The resulting execution-script SHA-256 is
`a1a666cba8b8d7162f52cf24c24b9ec58f0463750ea424eaa716c931158d875f`.

```text
SUCCESSOR_INPUT_CONTRACT_SHA256 = b9e0c447794c318d7ddc00803e0f2ea5468abc4c77a43752ead2910804b8a7b5
SUCCESSOR_PROTOCOL_SHA256 = cb61628ed49ca0f9d9798f92567adedbeb533f6854da098ec3c945b38bdbd76a
SIGNAL_CONSTRUCTION_POPULATION_INDEX_SHA256 = 2328b932d853c978383d6e9c36dbb961951dfe597ee898c17f9aaa5edda8342e
EVALUATION_POPULATION_INDEX_SHA256 = 50a94028a8cd816cffd61f5113fc5f799ca84f4af4e504d02b7feb06e5dc10c0
LABEL_OBSERVABILITY_USED_BEFORE_AVERAGEENSEMBLE = NO
PORTFOLIO_SIGNAL_POPULATION = V1_PREDICTION_CONTROL_POPULATION
COMPONENT_CONSTANT_SESSION_RANKIC_POLICY = UNAVAILABLE_NAN_NOT_IMPUTED_NOT_ZERO
MCS_INCOMPLETE_MATRIX_POLICY = NOT_AVAILABLE_SECONDARY_INCOMPLETE_LOSS_MATRIX
PRIMARY_CLASSIFICATION_LOCK_POINT = AFTER_COMPLETE_VALID_SIX_GATE_PRIMARY_AND_ROBUSTNESS_EVIDENCE
REAL_EXECUTION_PROVENANCE_SEAL_PRESENT = NO
REAL_EXECUTION_READY = NO_PENDING_POST_MERGE_PROVENANCE_SEAL
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
CURRENT_HEAD_MUST_EQUAL_ORIGIN_MAIN = YES
SEAL_LAST_CHANGE_COMMIT_MUST_EQUAL_HEAD = YES
WORKTREE_SEAL_MUST_MATCH_HEAD = YES
EXECUTION_COMMIT_SCRIPT_BYTES_VERIFIED = YES
DEPENDENCY_VERSION_SEAL_ENFORCED = YES
REAL_OUTCOME_ACCESS_STARTED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_SEAL_001
FINAL_CLASSIFICATION = PASS_NONRECURSIVE_PROVENANCE_AUTHORITY_FIXED
```

See [P7 successor execution-code rebase after boundary correction 001](p7-successor-one-shot-execution-code-precommit-and-preflight-freeze-001.md).

---

#### P7 successor Git-canonical text-byte identity correction (2026-09-27)

Tracked provenance text now uses `SHA256_OF_RAW_GIT_BLOB_BYTES` as its
canonical byte identity. The Windows checkout hash is diagnostic only and no
longer participates in authorization. Runtime verifies the execution script at
both the sealed execution commit and current `HEAD` using raw Git blob bytes,
then verifies the working-tree script and tracked seal through Git's native
clean/filter-aware blob OIDs.

The correction preserves the nonrecursive authority, clean-worktree,
`HEAD == origin/main`, seal-last-change, execution-commit ancestry, dependency,
Qlib-source, protocol, input, population, and label-mask gates. A realistic
`core.autocrlf=true` regression proves that differing checkout bytes pass when
Git-equivalent, while actual script/seal content mutation and a later unrelated
commit remain rejected. No real seal or outcome was opened.

```text
TRACKED_TEXT_CANONICAL_IDENTITY = SHA256_OF_RAW_GIT_BLOB_BYTES
RAW_WORKTREE_SHA_USED_FOR_AUTHORIZATION = NO
EXECUTION_COMMIT_BLOB_SHA_VERIFIED = YES
CURRENT_HEAD_BLOB_SHA_VERIFIED = YES
WORKTREE_SCRIPT_GIT_EQUIVALENT_TO_HEAD = YES
SEAL_RAW_BYTE_EQUALITY_REQUIRED = NO
WORKTREE_SEAL_GIT_EQUIVALENT_TO_HEAD = YES
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
REAL_PROVENANCE_SEAL_CREATED = NO
REAL_EXECUTE_INVOKED = NO
REAL_OUTCOME_ACCESS_STARTED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_SEAL_001
FINAL_CLASSIFICATION = PASS_GIT_CANONICAL_TEXT_BYTE_IDENTITY_CORRECTED
```

See [P7 successor Git-canonical text-byte identity correction 001](p7-successor-git-canonical-text-byte-identity-correction-001.md).

---

#### P7 successor one-shot execution provenance seal (2026-09-27)

The successor one-shot execution seal is frozen on the Git-canonical execution
script merged at `e7f3a64fb4b0178bd7f21a886b591ef20d2d48db`. It binds the exact
corrected protocol/input/population/mask identities, Qlib source and dependency
versions, the 17 Candidate artifacts, OLS control, Qlib label, and separate
construction/evaluation population artifacts. All 21 artifact hashes passed
raw-byte verification; population verification inspected only ordered
`datetime/instrument` keys.

The seal is nonrecursive and does not store its containing commit SHA. While
its PR remains open it is not real-execution eligible. After merge, the seal's
last-change commit must be the exact `origin/main` tip and **no other main
commit may land before the one-shot execution**. Any later main commit requires
a new seal authority commit.

```text
EXECUTION_CODE_COMMIT_SHA = e7f3a64fb4b0178bd7f21a886b591ef20d2d48db
EXECUTION_SCRIPT_GIT_BLOB_SHA256 = 0f11cba636d2db5849d7caf327c73f1063d0c053dcb35884406287344d714f3a
CANDIDATE_ARTIFACT_COUNT = 17
CANDIDATE_ARTIFACT_HASH_VERIFIED_COUNT = 17
SIGNAL_CONSTRUCTION_POPULATION_ARTIFACT_SHA256 = c2677441b7ce4d4b001f5cb9f51c032fbb85d7a2163e0d80feaaf65e8e160dc6
EVALUATION_POPULATION_ARTIFACT_SHA256 = 5f240cb9d88a318047d597c2ed11c1356eebc60fe0b59ae982d347089dcf4c38
TRACKED_TEXT_CANONICAL_IDENTITY = SHA256_OF_RAW_GIT_BLOB_BYTES
RAW_WORKTREE_SCRIPT_SHA_IN_SEAL = NO
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
REAL_EXECUTION_READY = NO_PENDING_SEAL_PR_MERGE
REAL_EXECUTE_INVOKED = NO
REAL_OUTCOME_ACCESS_STARTED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_ONE_SHOT_EXECUTION_001
FINAL_CLASSIFICATION = PASS_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_SEAL_FROZEN_PRE_MERGE
```

See [P7 successor one-shot execution provenance seal 001](p7-successor-one-shot-execution-provenance-seal-001.md).

---

#### P7 successor cross-Git runtime text equivalence correction (2026-09-27)

The first authorized successor invocation rejected before outcome access with
`WORKTREE_SCRIPT_HEAD_MISMATCH`. Windows Git used `core.autocrlf=true`, while
the WSL runtime had `core.autocrlf` unset. No marker, attempt manifest, output
root, or scientific result was created.

The runner now derives worktree text identity with native Git under explicit
clean-side settings:

```text
git -c core.autocrlf=input -c core.safecrlf=false hash-object --path=<path> <worktree-path>
```

This produces the same canonical blob identity for CRLF and LF checkouts,
without mutating repository or ambient Git configuration. The same rule covers
the tracked runner and seal. Real content mutations still reject. The runner
also requires `Path(__file__).resolve()` to equal the authorized repository
script path, so an external copied runner is rejected even when its bytes are
identical.

The existing real seal is intentionally unchanged and will become ineligible
when this correction is merged. A separate reseal must bind the correction
merge commit and its new raw Git-blob script SHA before any new one-shot
invocation.

```text
PRIOR_AUTHORIZED_MAIN_SHA = 16977fbf8ba62aa3b689cb94a0b56483c4c64739
PRIOR_EXECUTION_REJECTION = WORKTREE_SCRIPT_HEAD_MISMATCH
PRIOR_REAL_OUTCOME_ACCESS_STARTED = NO
PRIOR_OUTCOME_ATTEMPT_CONSUMED = NO
DETERMINISTIC_CLEAN_FILTER_MODE = GIT_CORE_AUTOCRLF_INPUT_SAFECRLF_FALSE
TRACKED_TEXT_CANONICAL_IDENTITY = SHA256_OF_RAW_GIT_BLOB_BYTES
ACTUAL_RUNTIME_SCRIPT_PATH_BOUND = YES
RAW_WORKTREE_SHA_USED_FOR_AUTHORIZATION = NO
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
REAL_SEAL_MODIFIED = NO
REAL_EXECUTE_INVOKED = NO
REAL_OUTCOME_ACCESS_STARTED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_RESEAL_001
FINAL_CLASSIFICATION = PASS_CROSS_GIT_RUNTIME_TEXT_EQUIVALENCE_CORRECTED
```

See [P7 successor cross-Git runtime text equivalence correction 001](p7-successor-cross-git-runtime-text-equivalence-correction-001.md).

---

#### P7 successor one-shot execution provenance reseal (2026-09-27)

The successor execution seal is rebound to the cross-Git-corrected runner
merged at `3c46824c2865a8b8f938e0ff75e840b6de03fa14`. Exactly two seal identities
changed: the execution-code commit and the execution script's canonical raw
Git-blob SHA-256. All scientific, population, dependency, Qlib, Candidate,
control, label, and population-artifact bindings remain unchanged; 21/21
artifact raw-byte hashes passed static verification without deserialization.

```text
EXECUTION_CODE_COMMIT_SHA = 3c46824c2865a8b8f938e0ff75e840b6de03fa14
EXECUTION_SCRIPT_GIT_BLOB_SHA256 = 3349177fbff145111312819082ea2359a6b867e8419006abe6c0dfee2644bb70
TRACKED_TEXT_CANONICAL_IDENTITY = SHA256_OF_RAW_GIT_BLOB_BYTES
DETERMINISTIC_CLEAN_FILTER_MODE = GIT_CORE_AUTOCRLF_INPUT_SAFECRLF_FALSE
ACTUAL_RUNTIME_SCRIPT_PATH_BOUND = YES
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
RAW_WORKTREE_SHA_USED_FOR_AUTHORIZATION = NO
REAL_EXECUTION_READY = NO_PENDING_RESEAL_PR_MERGE
REAL_EXECUTE_INVOKED = NO
REAL_OUTCOME_ACCESS_STARTED = NO
PRIOR_EXECUTION_REJECTION = WORKTREE_SCRIPT_HEAD_MISMATCH
PRIOR_OUTCOME_ATTEMPT_CONSUMED = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_ONE_SHOT_EXECUTION_002
FINAL_CLASSIFICATION = PASS_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_RESEALED_PRE_MERGE
```

After this reseal PR merges, **no other main commit may land before the
one-shot execution**. Any later commit makes the seal's last-change commit
differ from HEAD and requires another reseal.

See [P7 successor one-shot execution provenance reseal 001](p7-successor-one-shot-execution-provenance-reseal-001.md).

---

#### P7 successor cross-Git runtime worktree cleanliness correction (2026-09-27)

Execution 002 rejected before outcome access with
`DIRTY_WORKTREE_FORBIDDEN`. The deterministic blob checks and actual runner
path gate passed, but the runtime cleanliness check still called ambient WSL
`git status`. That command reported 385 false modifications for the Windows
CRLF checkout, while the frozen deterministic Git configuration reported zero.
No output root, marker, attempt manifest, or scientific result was created.

The runner now shares one native-Git clean-side configuration between tracked
text hashing and worktree status:

```text
git -c core.autocrlf=input -c core.safecrlf=false status --porcelain=v1 -z --untracked-files=all
```

Line-ending-only differences are clean. Real tracked content changes, staged
changes, and untracked files remain dirty and reject with
`DIRTY_WORKTREE_FORBIDDEN`. Ambient Git status is no longer authorization
evidence.

```text
PRIOR_EXECUTION_001_REJECTION = WORKTREE_SCRIPT_HEAD_MISMATCH
PRIOR_EXECUTION_002_REJECTION = DIRTY_WORKTREE_FORBIDDEN
PRIOR_REAL_OUTCOME_ACCESS_STARTED = NO
PRIOR_SCIENTIFIC_ATTEMPT_COUNT = 0
AMBIENT_WSL_STATUS_ENTRY_COUNT = 385
DETERMINISTIC_STATUS_ENTRY_COUNT = 0
DETERMINISTIC_GIT_STATUS_CONFIG = CORE_AUTOCRLF_INPUT_SAFECRLF_FALSE_PORCELAIN_V1_Z
DETERMINISTIC_WORKTREE_CLEAN = YES
REAL_SEAL_MODIFIED = NO
REAL_SEAL_GIT_BLOB_SHA = bfa8d0d510c09b4636820b5724cc0861eb9b6a32
REAL_EXECUTE_INVOKED = NO
REAL_OUTCOME_ACCESS_STARTED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_RESEAL_002
FINAL_CLASSIFICATION = PASS_CROSS_GIT_RUNTIME_WORKTREE_CLEANLINESS_CORRECTED
```

See [P7 successor cross-Git runtime worktree cleanliness correction 001](p7-successor-cross-git-runtime-worktree-cleanliness-correction-001.md).

---

#### P7 successor one-shot execution provenance reseal 002 (2026-09-27)

The tracked execution seal is rebound to the deterministic worktree-cleanliness
runner merged by PR #136 at
`27a29c97a34e4da5883f4ff473419c5de30e2cea`. Exactly two seal fields changed:
the execution-code commit and the execution script's canonical raw Git-blob
SHA-256. The protocol, input, population, label-mask, dependency, Qlib,
Candidate, control, label, and population-artifact authorities remain
semantically identical. Raw-byte existence/hash checks matched all 21 artifact
bindings without deserializing predictions or labels.

```text
PRIOR_SEAL_EXECUTION_CODE_COMMIT_SHA = 3c46824c2865a8b8f938e0ff75e840b6de03fa14
NEW_SEAL_EXECUTION_CODE_COMMIT_SHA = 27a29c97a34e4da5883f4ff473419c5de30e2cea
PRIOR_SEAL_EXECUTION_SCRIPT_SHA256 = 3349177fbff145111312819082ea2359a6b867e8419006abe6c0dfee2644bb70
NEW_SEAL_EXECUTION_SCRIPT_SHA256 = 4db387dbfc2d2b800fdfb2e459ad88edb2b682539143f14a631e61117796b870
TRACKED_TEXT_CANONICAL_IDENTITY = SHA256_OF_RAW_GIT_BLOB_BYTES
DETERMINISTIC_GIT_STATUS_CONFIG = CORE_AUTOCRLF_INPUT_SAFECRLF_FALSE_PORCELAIN_V1_Z_UNTRACKED_ALL
ACTUAL_RUNTIME_SCRIPT_PATH_BOUND = YES
AUTHORITY_COMMIT_SHA_STORED_INSIDE_SEAL = NO
RAW_WORKTREE_SHA_USED_FOR_AUTHORIZATION = NO
REAL_EXECUTION_READY = NO_PENDING_RESEAL_PR_MERGE
REAL_EXECUTE_INVOKED = NO
REAL_OUTCOME_ACCESS_STARTED = NO
EXECUTION_001_REJECTION = WORKTREE_SCRIPT_HEAD_MISMATCH
EXECUTION_002_REJECTION = DIRTY_WORKTREE_FORBIDDEN
PRIOR_SCIENTIFIC_ATTEMPT_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P7_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_ONE_SHOT_EXECUTION_003
FINAL_CLASSIFICATION = PASS_SUCCESSOR_ONE_SHOT_EXECUTION_PROVENANCE_RESEALED_002_PRE_MERGE
```

After this reseal merges, no other main commit may land before Execution 003.
Any later main commit invalidates the seal-last-change-equals-HEAD gate and
requires another reseal.

See [P7 successor one-shot execution provenance reseal 002](p7-successor-one-shot-execution-provenance-reseal-002.md).

---

#### P7 successor historical static ensemble execution closeout (2026-09-27)

Execution 003 is the sole scientific outcome attempt for the frozen successor
static-17 equal-weight study. The sealed classification is
`STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE`: its mean daily RankIC delta versus
the frozen OLS Alpha158 control was `-0.006600540893059081`, and zero of six
preregistered gates passed. The result does not support superiority of this
specific 17-Candidate Formulaic Alpha static equal-weight ensemble under the
frozen protocol. It does not support broader claims about ensembles,
individual alphas, AlphaGen, or Qlib AverageEnsemble.

```text
SCIENTIFIC_ATTEMPT_COUNT = 1
RESULT_CLASSIFICATION = STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE
PASSED_GATE_COUNT = 0
FAILED_GATE_COUNT = 6
STATIC_17_EQUAL_WEIGHT_HISTORICAL_STUDY_RERUN_ALLOWED = NO
POST_HOC_RESCUE_ALLOWED = NO
PRISTINE_OOS = NO
P2_CERTIFICATION_EVIDENCE = NO
P7_DYNAMIC_ROSTER_EVIDENCE = NO
P7_EXIT_CONDITION_EVIDENCE = NO
PRODUCTION_AUTHORIZATION = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P2_V2_COHORT_MODIFIED = NO
SUCCESSOR_STATIC_17_EQUAL_WEIGHT_HISTORICAL_STUDY = CLOSED_NOT_SUPPORTIVE
CURRENT_P7_STATUS = INCOMPLETE_REQUIRES_INDEPENDENT_ALPHA_FAMILIES
NEXT_DEVELOPMENT_DIRECTION = P7_INDEPENDENT_ALPHA_FAMILY_ACQUISITION_AND_ADMISSION
FINAL_CLASSIFICATION = PASS_SUCCESSOR_HISTORICAL_STATIC_ENSEMBLE_EXECUTION_CLOSED_NOT_SUPPORTIVE
```

MCS and portfolio outputs are secondary and non-gating. The unavailable MCS
loss matrix and the passing portfolio projection do not change the primary
classification. Execution 001 and 002 remain pre-outcome authority rejections
and consumed no scientific attempts. This exact study cannot be rerun or
rescued post hoc; any future ensemble study requires a new scientific question,
preregistered protocol, identity, and scientifically justified new information.

See [P7 successor historical static ensemble execution closeout 001](p7-successor-historical-static-ensemble-execution-closeout-001.md).

---

#### P7 Static17 scaffold retirement and autonomous factor-factory rebase (2026-09-27)

The terminal Static17 one-shot runners, their dedicated runner test, and the
spent real-execution seal are removed from the active tree. Git history at
`3da8c79d617eca0263f1e6c5dcae61f235d58338` plus the immutable protocol,
contract, result-reference, and closeout records remain the scientific
authority. Deletion from the active tree does not delete scientific history.

The active P7 Python runtime contracts from 2,230 to 352 physical LOC and now
contains only the time-effective authorization handoff, session-local
fail-closed routing, and thin Qlib AverageEnsemble boundary. The reusable
skfolio split-feasibility test remains because it tests public WalkForward and
CombinatorialPurgedCV boundary behavior independently of the retired runners.

Current official-source inspection selects Microsoft RD-Agent(Q) as the
primary autonomous research owner. RD-Agent owns hypothesis generation,
factor/model proposal and coding iteration, experiment feedback, and joint
factor/model orchestration. Qlib continues to own dataset, training,
prediction, Recorder, backtest, signal evaluation, and workflow mechanics.
AlphaGen remains the Formulaic Alpha / RL alpha-pool owner, with its optional
LLM iterative generation surface. AQ retains only PIT data authority,
Candidate normalization and identity, P2 certification, P4 lifecycle, P7
cross-family authorization/ensemble policy, and P8+ capital/risk authority.

```text
SUCCESSOR_STATIC_17_EQUAL_WEIGHT_HISTORICAL_STUDY = CLOSED_NOT_SUPPORTIVE
STATIC_17_RERUN_ALLOWED = NO
PRIMARY_AUTONOMOUS_RD_OWNER = MICROSOFT_RD_AGENT_Q
AUTONOMOUS_RESEARCH_FEEDBACK_SURFACE = TRAIN_VALID_RESEARCH_ONLY
P2_V2_SEALED_OOS_FEEDBACK_TO_AUTONOMOUS_RD = PROHIBITED
AQ_CUSTOM_RESEARCH_LOOP_PRESENT = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_P7_STATUS = INCOMPLETE_REQUIRES_INDEPENDENT_ALPHA_FAMILIES
CURRENT_DEVELOPMENT_NEXT = AUTONOMOUS_QUANT_P3_P7_RDAGENT_FIN_QUANT_THIN_ADAPTER_POC_001
FINAL_CLASSIFICATION = PASS_STATIC17_SCAFFOLD_RETIRED_AUTONOMOUS_RD_DIRECTION_REBASED
```

See [P7 Static17 scaffold retirement 001](p7-static17-scaffold-retirement-001.md).

---

## 27. First Principle

> **Do not build what a mature upstream already solves.**
>
> **Do not trust what has not survived independent out-of-sample certification.**
>
> **Do not let autonomous research directly control unrestricted real capital.**
>
> **Build the smallest runnable system first, while preserving interfaces for the complete tree.**
