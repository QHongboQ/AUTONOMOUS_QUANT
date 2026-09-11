# P1 Qlib-native minimal quant baseline 001

## Status

```text
TASK = AUTONOMOUS-QUANT-P1-QLIB-NATIVE-MINIMAL-QUANT-BASELINE-001
STATUS = COMPLETE
RESULT_CLASSIFICATION = RESEARCH_ONLY_NOT_CERTIFIED
SURVIVORSHIP_BIAS_CONTROL = BEST_EFFORT_NOT_CERTIFIED
```

This is an engineering proof that the accepted Microsoft Qlib runtime can own
one complete, real-data research path. It is not model certification and is
not evidence for production or live-capital use.

## Ownership

```text
CAPABILITY = P1 minimal end-to-end quant research baseline
UPSTREAM_OWNER = Microsoft Qlib
OWNERSHIP_MODE = UPSTREAM_WHOLE
AQ_IMPLEMENTATION = CONFIGURATION_AND_EVIDENCE_ONLY
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

Qlib owns provider access, `DatasetH`, `Alpha158`, `LGBModel`, Recorder,
predictions, `SigAnaRecord`, `TopkDropoutStrategy`, exchange/cost simulation,
backtest, and `PortAnaRecord`. AQ created no substitute data, factor, model,
prediction, portfolio, backtest, or experiment-database engine. The deferred
AQ PIT DatasetSnapshot and Qlib dataset adapter were not on the execution path.

## Accepted runtime and upstream authority

```text
QLIB_ENV = rdagent4qlib
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_SOURCE_WORKTREE_CLEAN = YES
QLIB_RUNTIME_AUTHORITY_MATCH = YES
UPSTREAM_CONFIG = examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
```

Before execution, the accepted environment and source checkout were verified.
Imports passed for Qlib, `DatasetH`, `Alpha158`, `LGBModel`,
`TopkDropoutStrategy`, workflow/Recorder, `SignalRecord`, `SigAnaRecord`, and
`PortAnaRecord`. No environment or package was installed, upgraded, or changed.

## Real-data provider validation

An existing local Qlib-native US daily binary provider was reused; no data was
downloaded during this task.

```text
PROVIDER_URI = /home/zhou/AQ_DATA/P1/qlib-native-baseline-001/qlib_data
REGION = us
DATA_START = 2015-01-02
DATA_END = 2025-12-31
CALENDAR_SESSIONS = 2766
MARKET = sp500
USABLE_INSTRUMENTS = 501
BENCHMARK = SPY
BENCHMARK_AVAILABLE_IN_PROVIDER = YES
```

Qlib public APIs initialized the provider, read its daily calendar and `sp500`
instrument universe, and returned non-empty finite OHLCV observations for a
real AAPL/MSFT/SPY sample. The provider also contains SPY features, so SPY was
selected as the in-provider US broad-market benchmark without fabricated or
cross-provider data.

The available calendar starts in 2015, so it cannot support the upstream
benchmark's 2008 start. Chronological, non-overlapping multi-year windows were
therefore fixed before execution:

```text
TRAIN = 2015-04-01 / 2019-12-31
VALID = 2020-01-01 / 2021-12-31
TEST_AND_BACKTEST = 2022-01-03 / 2025-12-29
```

The initial interval between provider inception and training start permits
Alpha158 lookback. No boundary was selected from performance. All bounded
deviations from the official configuration are documented beside the checked-in
YAML. Model methodology and parameters were retained, except that
`num_threads` was reduced from 20 to 8 for resource safety.

## Native run evidence

The one authorized `qrun` used the checked-in YAML and Qlib's native CLI. An
explicit external SQLite `MLflowExpManager` avoided the unsupported MLflow
filesystem tracking path while remaining Qlib's standard Recorder backend.

```text
CONFIG_SHA256 = c6e6c4882adeb053d58e91b27d7d796fd9886dc1946d1d0540d5d9637f42ccaf
EXPERIMENT = aq_p1_qlib_native_minimal_baseline_001
EXPERIMENT_ID = 1
RECORDER_ID = 16bd043b00914e54bca7458efc5af9e9
RECORDER_STATUS = FINISHED
EXTERNAL_RUN_ROOT = /home/zhou/AQ_DATA/P1/qlib-native-baseline-001/native-run
QRUN_EXIT_CODE = 0
```

The external Recorder contains `pred.pkl`, `label.pkl`, configuration/task
artifacts, signal-analysis artifacts, and Qlib portfolio-analysis reports. No
binary data, model/Recorder artifacts, or MLflow database is stored in Git.

### Predictions and signal analysis

```text
PREDICTION_ROWS = 497062
PREDICTION_NON_NULL = 497062
PREDICTION_INSTRUMENTS = 501
PREDICTION_START = 2022-01-03
PREDICTION_END = 2025-12-29
IC = 0.009376443316672149
ICIR = 0.07344316259370916
RANK_IC = 0.00443446889692092
RANK_ICIR = 0.04557249853299947
```

### Qlib Top-K backtest and portfolio analysis

```text
STRATEGY = TopkDropoutStrategy(topk=50, n_drop=5)
BACKTEST_SESSIONS = 1001
ANNUALIZED_RETURN_WITH_COST = 0.2196360181792855
BENCHMARK_ANNUALIZED_RETURN = 0.1165732741355896
EXCESS_RETURN_WITH_COST_ANNUALIZED = 0.10306273779146044
EXCESS_RETURN_WITH_COST_INFORMATION_RATIO = 0.7710368927486123
EXCESS_RETURN_WITH_COST_MAX_DRAWDOWN = -0.1246120961177218
PORTFOLIO_WITH_COST_MAX_DRAWDOWN = -0.29470629620276534
MEAN_DAILY_TURNOVER = 0.19881074208482732
MEAN_DAILY_TRANSACTION_COST = 0.00019841838168595377
```

The return, benchmark, risk, turnover, and cost values above are outputs from
Qlib's report and Qlib risk-analysis interfaces. They are not an AQ analytics
reimplementation. Their magnitude does not promote or certify the strategy.

## Result and non-authorizations

```text
QLIB_PROVIDER_INIT = PASS
QLIB_DATASET_H = PASS
QLIB_ALPHA158 = PASS
QLIB_LGBMODEL_TRAINING = PASS
QLIB_PREDICTIONS = PASS
QLIB_SIGNAL_ANALYSIS = PASS
QLIB_TOPK_STRATEGY = PASS
QLIB_BACKTEST = PASS
QLIB_PORTANA_RECORD = PASS
PIT_UNIVERSE_CERTIFIED = NO
CERTIFICATION_GATE = NONE
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
```

This provider's static/current-style `sp500` universe is acceptable only for
the stated P1 best-effort research baseline. It does not establish strict
survivorship-free membership or institutional point-in-time price completeness;
those certification responsibilities remain P2 work.

## Repository regression safety

```text
PIT_TESTS = 45/45 PASS
PIT_FROZEN_REGRESSIONS = 13/13 PASS
DATASET_SNAPSHOT_TESTS = 16/16 PASS
QLIB_HANDOFF_TESTS = 17/17 PASS
XNYS_CALENDAR_TESTS = 11/11 PASS
TOTAL_RELEVANT_TESTS = 89/89 PASS
PRODUCTION_PYTHON_COMPILEALL = PASS
```

The frozen-facts tests were executed from an LF-preserving temporary clone to
avoid Windows checkout line-ending translation changing the intentionally
byte-frozen JSON authority. DatasetSnapshot tests ran with the existing
external PIT data and DVC CLI enabled; Qlib handoff tests also exercised the
existing local DatasetSnapshot output. Temporary test clones and generated
Python caches were removed after verification.

## Current state

```text
CLEANUP_PHASE_COMPLETE = YES
P1 = STARTED
P1_MINIMAL_QUANT = IN_PROGRESS
P1_QLIB_NATIVE_BASELINE = COMPLETE
REAL_MARKET_DATA_READY = YES (RESEARCH BASELINE DATASET ONLY)
REAL_ALPHA158_RUN = YES
REAL_MODEL_TRAINING = YES
REAL_PREDICTIONS = YES
REAL_BACKTEST = YES
REAL_PORTFOLIO_ANALYSIS = YES
P1_BASELINE_CLASSIFICATION = RESEARCH_ONLY_NOT_CERTIFIED
PIT_UNIVERSE_CERTIFIED = NO
CURRENT_NEXT = P1_QLIB_NATIVE_MODEL_STRATEGY_COMPARISON
```

The smallest next task supported by this evidence is a bounded Qlib-native
model/strategy comparison. It is not started here and must continue to use
Qlib-owned workflow, evaluation, backtest, and Recorder components.
