# P1 Qlib-native strategy comparison 001

## Status and classification

```text
TASK = AUTONOMOUS-QUANT-P1-QLIB-NATIVE-STRATEGY-COMPARISON-001
STATUS = COMPLETE
RESULT_CLASSIFICATION = EXPLORATORY_P1_STRATEGY_COMPARISON
STRATEGY_COMPARISON_CLASSIFICATION = EXPLORATORY_RESEARCH_ONLY_NOT_CERTIFIED
TEST_SET_IS_PRISTINE_OOS = NO
CERTIFIED_STRATEGY = NONE
```

This comparison reuses a previously observed test set. It is exploratory P1
research evidence, not independent certification, promotion, production
readiness, or authorization for live capital.

## Ownership

```text
CAPABILITY = P1 Qlib-native bounded strategy comparison
UPSTREAM_OWNER = Microsoft Qlib
OWNERSHIP_MODE = UPSTREAM_WHOLE
AQ_IMPLEMENTATION = CONFIGURATION_AND_EVIDENCE_ONLY
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

Qlib owns `TopkDropoutStrategy`, portfolio simulation, exchange and cost
behavior, backtest, Recorder, and `PortAnaRecord`. AQ implemented no strategy,
backtester, portfolio, parameter-search, comparison, or analytics engine.
Temporary in-memory glue called Qlib public APIs from outside the repository.

## Fixed authority

The accepted runtime was verified before execution:

```text
QLIB_ENV = rdagent4qlib
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_SOURCE_WORKTREE_CLEAN = YES
QLIB_RUNTIME_AUTHORITY_MATCH = YES
TOPK_DROPOUT_STRATEGY_IMPORT = PASS
PORTANA_RECORD_IMPORT = PASS
```

The fixed data and backtest boundary remained:

```text
PROVIDER_URI = /home/zhou/AQ_DATA/P1/qlib-native-baseline-001/qlib_data
REGION = us
MARKET = sp500
BENCHMARK = SPY
BACKTEST = 2022-01-03 / 2025-12-29
ACCOUNT = 100000000
LIMIT_THRESHOLD = 0.095
DEAL_PRICE = close
OPEN_COST = 0.0005
CLOSE_COST = 0.0015
MIN_COST = 5
STRATEGY_CONFIG_SHA256 = b96e88cedb0755f36facc0afbc51e38970217582631c2585c645dcbaf7462588
```

No data was downloaded, refreshed, or modified. The market, benchmark,
calendar bounds, account, exchange rules, and costs were identical for all
candidates.

## Prediction authority

The LightGBM model was not retrained and predictions were not regenerated.
Baseline Recorder `16bd043b00914e54bca7458efc5af9e9` remained `FINISHED`.
Its exact `pred.pkl` was loaded once and supplied unchanged to both new Qlib
Recorders.

```text
PREDICTION_SHA256 = 629a8bf6be26ef16b803626db56b8142680eb02b46f6cba359214003eb6d16c1
PREDICTION_ROWS = 497062
PREDICTION_INSTRUMENTS = 501
PREDICTION_START = 2022-01-03
PREDICTION_END = 2025-12-29
PREDICTION_HASH_MATCH_ALL_CANDIDATES = YES
```

The persisted `pred.pkl` artifact SHA-256 is identical in the baseline, 30/3,
and 100/10 Recorders. Each new Recorder also logs the source Recorder ID and
source hash as parameters.

## Candidate execution

Only the three predeclared candidates were evaluated:

```text
CANDIDATE_A = BASELINE / topk=50 / n_drop=5 / REUSED
CANDIDATE_B = CONCENTRATED / topk=30 / n_drop=3 / EXECUTED
CANDIDATE_C = DIVERSIFIED / topk=100 / n_drop=10 / EXECUTED
CANDIDATE_B_RECORDER = 52a61a96342c4f349ed234d988b08be8 / FINISHED
CANDIDATE_C_RECORDER = 64b2d358929f47d28861e760939b41a5 / FINISHED
BACKTEST_SESSIONS_EACH = 1001
```

No grid search, optimizer, automatic search, retry-driven selection, or
post-result parameter mutation occurred.

## Qlib-produced comparison

| Candidate | topk | n_drop | Annualized return with cost | Benchmark annualized return | Excess return with cost | Excess IR | Excess max drawdown | Portfolio max drawdown | Mean daily turnover | Mean daily transaction cost | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| A — baseline | 50 | 5 | 0.2196360181792855 | 0.1165732741355896 | 0.10306273779146044 | 0.7710368927486123 | -0.1246120961177218 | -0.29470629620276534 | 0.19881074208482732 | 0.00019841838168595377 | FINISHED / REUSED |
| B — concentrated | 30 | 3 | 0.2796432913198966 | 0.1165732741355896 | 0.1630700109320716 | 0.9939941788995332 | -0.14462266762128756 | -0.3411198951762677 | 0.20025748614638225 | 0.00019986307369234654 | FINISHED / NEW PORTANA |
| C — diversified | 100 | 10 | 0.15397879799960634 | 0.1165732741355896 | 0.03740551761178127 | 0.42446769823185987 | -0.09404116477963671 | -0.2654689967215278 | 0.2001078136463369 | 0.00019971337479041029 | FINISHED / NEW PORTANA |

All metrics are directly from Qlib Recorder/`PortAnaRecord` artifacts and
Qlib `risk_analysis`; AQ did not reimplement them.

## Interpretation

```text
BEST_OBSERVED_P1_STRATEGY_CANDIDATE = TOPK_30_NDROP_3
CERTIFIED_STRATEGY = NONE
```

Candidate B has the strongest observed annualized return, excess return, and
excess information ratio. That improvement is coherent across return and
risk-adjusted excess-return measures, while its turnover and transaction cost
are only marginally above the baseline. However, its portfolio and excess
drawdowns are worse than the baseline. Candidate C has the shallowest
portfolio and excess drawdowns, but materially lower return and IR.

The combined tradeoff supports 30/3 only as the current best observed P1
research candidate. The drawdown deterioration and already-observed test set
prevent a certification, promotion, or model-superiority conclusion.

## Repository safety and current state

All predictions, reports, models, MLflow databases, and Recorder artifacts
remain outside Git under
`/home/zhou/AQ_DATA/P1/qlib-native-strategy-comparison-001`. No accepted
environment or package was changed.

Repository regression verification completed without changing production
code:

```text
PIT_TESTS = 45/45 PASS
PIT_FROZEN_REGRESSIONS = 13/13 PASS
DATASET_SNAPSHOT_TESTS = 16/16 PASS
QLIB_HANDOFF_TESTS = 17/17 PASS
XNYS_CALENDAR_TESTS = 11/11 PASS
TOTAL_RELEVANT_TESTS = 89/89 PASS
PRODUCTION_PYTHON_COMPILEALL = PASS
```

The byte-frozen authority tests ran from an LF-preserving temporary clone with
the existing external PIT and DatasetSnapshot data. DVC CLI behavior and the
Qlib public-API compatibility probe were exercised. The temporary clone was
removed after verification.

```text
P1 = STARTED / IN_PROGRESS
P1_MINIMAL_QUANT = IN_PROGRESS
P1_QLIB_NATIVE_BASELINE = COMPLETE
P1_QLIB_NATIVE_MODEL_COMPARISON = COMPLETE
P1_QLIB_NATIVE_STRATEGY_COMPARISON = COMPLETE
STRATEGY_COMPARISON_CLASSIFICATION = EXPLORATORY_RESEARCH_ONLY_NOT_CERTIFIED
TEST_SET_IS_PRISTINE_OOS = NO
CERTIFIED_STRATEGY = NONE
PIT_UNIVERSE_CERTIFIED = NO
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
CURRENT_NEXT = P1_MINIMAL_QUANT_CLOSEOUT
```
