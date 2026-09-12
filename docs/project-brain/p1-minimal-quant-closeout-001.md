# P1 Minimal Quant Closeout 001

## Decision

```text
TASK = AUTONOMOUS-QUANT-P1-MINIMAL-QUANT-CLOSEOUT-001
STATUS = COMPLETE
P1 = COMPLETE
P1_MINIMAL_QUANT = COMPLETE
P1_CLOSEOUT = COMPLETE
RESULT_CLASSIFICATION = RESEARCH_ONLY_NOT_CERTIFIED
```

P1 has met its bounded purpose: a smallest real-data, runnable,
upstream-owned quantitative research path now proves data to factors to model
to predictions to strategy to backtest to portfolio analysis. This closes an
engineering and research-baseline phase only. It does not certify an
investment result or authorize production use.

## Ownership and completed path

Microsoft Qlib remains `UPSTREAM_WHOLE` for the provider interface,
`DatasetH`, Alpha158, model training, predictions, Recorder, signal analysis,
`TopkDropoutStrategy`, exchange/cost simulation, backtest, and
`PortAnaRecord`. AQ added configuration and evidence, not a model, factor,
strategy-search, backtest, portfolio, or experiment-database engine.

```text
UPSTREAM_FIRST = PASS
AQ_GENERIC_RESEARCH_ENGINE = NONE
AQ_EXPERIMENT_DATABASE = NONE
TRIAL_LEDGER_CUSTOM_RUNTIME = RETIRED
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

The retained adjacent ownership remains bounded: the AQ PIT core is an
AQ-owned thin research-domain adapter; Pandera owns structural schemas;
`exchange_calendars` owns XNYS sessions; DatasetSnapshot/DVC and the Qlib PIT
handoff remain inactive P2-deferred boundaries. No material duplicate engine
has reappeared.

## Real-data and baseline evidence

The existing provider was read again through Qlib public APIs without a data
download or refresh.

```text
PROVIDER_URI = /home/zhou/AQ_DATA/P1/qlib-native-baseline-001/qlib_data
REGION = us
MARKET = sp500
DATA_RANGE = 2015-01-02 / 2025-12-31
CALENDAR_SESSIONS = 2766
USABLE_INSTRUMENTS = 501
REAL_MARKET_DATA_READY = YES (RESEARCH BASELINE DATASET ONLY)
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_SOURCE_WORKTREE_CLEAN = YES
```

AAPL, MSFT, and SPY OHLCV samples remained non-empty and finite. Baseline
Recorder `16bd043b00914e54bca7458efc5af9e9` remains `FINISHED` with readable
configuration, dataset, predictions, labels, signal-analysis, and
portfolio-analysis artifacts.

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
PREDICTION_ROWS = 497062
PREDICTION_INSTRUMENTS = 501
PREDICTION_RANGE = 2022-01-03 / 2025-12-29
PREDICTION_SHA256 = 629a8bf6be26ef16b803626db56b8142680eb02b46f6cba359214003eb6d16c1
```

## Bounded comparisons and exploratory reference

The model comparison completed with the accepted LightGBM baseline reused and
one Linear OLS run. Linear Recorder `ef143027d1a0486cb876ba8e615496b5`
remains `FINISHED`. CatBoost remains
`NOT_RUN_EXISTING_ENV_DEPENDENCY_UNAVAILABLE`; it was not installed for
closeout.

The strategy comparison evaluated only the three predeclared Qlib
`TopkDropoutStrategy` settings: 50/5, 30/3, and 100/10. Recorders
`52a61a96342c4f349ed234d988b08be8` and
`64b2d358929f47d28861e760939b41a5` remain `FINISHED`, and both reuse the exact
baseline prediction hash. No additional parameter search occurred.

```text
P1_QLIB_NATIVE_BASELINE = COMPLETE
P1_QLIB_NATIVE_MODEL_COMPARISON = COMPLETE
P1_QLIB_NATIVE_STRATEGY_COMPARISON = COMPLETE
P1_EXPLORATORY_MODEL_REFERENCE = LIGHTGBM_ALPHA158
P1_EXPLORATORY_STRATEGY_REFERENCE = TOPK_30_NDROP_3
```

These are exploratory references, not champions, certified artifacts, or
production-approved choices. The 30/3 strategy had the strongest observed
return and excess information ratio among the bounded candidates, but also a
deeper drawdown than the 50/5 baseline.

## Verification and deferred certification

```text
PIT_TESTS = 45/45 PASS
PIT_FROZEN_REGRESSIONS = 13/13 PASS
DATASET_SNAPSHOT_TESTS = 16/16 PASS
QLIB_HANDOFF_TESTS = 17/17 PASS
XNYS_CALENDAR_TESTS = 11/11 PASS
TOTAL_RELEVANT_TESTS = 89/89 PASS
PRODUCTION_PYTHON_COMPILEALL = PASS
```

Pandera boundary tests are included in the PIT total. The byte-frozen PIT
authority was tested from an LF-preserving temporary clone; existing external
PIT and DatasetSnapshot inputs were reused, and the clone was removed after
verification.

P2 owns strict PIT and price certification, pristine sealed OOS, temporal
certification, purged/walk-forward validation, multiple-testing controls,
robustness and promotion decisions. None was started here.

```text
PIT_UNIVERSE_CERTIFIED = NO
TEST_SET_IS_PRISTINE_OOS = NO
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
P2_CERTIFICATION = NOT STARTED
P3_AUTONOMOUS_RESEARCH = NOT STARTED
```

## Next authority

```text
NEXT_PHASE = P2_CERTIFICATION
CURRENT_NEXT = RESEARCH_WEB_UI_UPSTREAM_ACTIVATION
WEB_UI_IMPLEMENTED = NO
```

The adjacent Web UI candidate owner is MLflow UI / MLflow Tracking Server.
Qlib's accepted `MLflowExpManager` already owns experiment persistence, and
the pinned Qlib Recorder documentation explicitly identifies `mlflow ui` for
visualizing and checking experiment results. Activation is a separate task;
this closeout adds no dashboard, custom frontend, custom Web backend, or
package/environment change.
