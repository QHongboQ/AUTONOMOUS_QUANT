# P1 Qlib-native model comparison 001

## Status and classification

```text
TASK = AUTONOMOUS-QUANT-P1-QLIB-NATIVE-MODEL-COMPARISON-001
STATUS = COMPLETE
MODEL_COMPARISON_CLASSIFICATION = EXPLORATORY_RESEARCH_ONLY_NOT_CERTIFIED
RESULT_CLASSIFICATION = EXPLORATORY_P1_MODEL_COMPARISON
TEST_SET_IS_PRISTINE_OOS = NO
CERTIFIED_MODEL = NONE
```

The LightGBM test period was already observed before this comparison. Results
are exploratory P1 research evidence, not an independent certification test,
promotion decision, production authorization, or live-capital signal.

## Ownership and frozen boundary

```text
CAPABILITY = P1 Qlib-native bounded model comparison
UPSTREAM_OWNER = Microsoft Qlib
OWNERSHIP_MODE = UPSTREAM_WHOLE
AQ_IMPLEMENTATION = CONFIGURATION_AND_EVIDENCE_ONLY
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```

Qlib owns the provider, `DatasetH`, Alpha158, model implementations, training,
predictions, Recorder, signal analysis, Top-K strategy, backtest, cost model,
and portfolio analysis. AQ created no runner, tournament, model, analytics,
portfolio, backtest, or experiment-database engine.

Both executed candidates use the same fixed comparison boundary:

```text
PROVIDER_URI = /home/zhou/AQ_DATA/P1/qlib-native-baseline-001/qlib_data
REGION = us
MARKET = sp500
USABLE_INSTRUMENTS = 501
BENCHMARK = SPY
TRAIN = 2015-04-01 / 2019-12-31
VALID = 2020-01-01 / 2021-12-31
TEST = 2022-01-03 / 2025-12-29
BACKTEST = 2022-01-03 / 2025-12-29
FACTOR_FAMILY = Alpha158
STRATEGY = TopkDropoutStrategy(topk=50, n_drop=5)
ACCOUNT = 100000000
LIMIT_THRESHOLD = 0.095
DEAL_PRICE = close
OPEN_COST = 0.0005
CLOSE_COST = 0.0015
MIN_COST = 5
```

The provider was neither downloaded, refreshed, nor mutated. Windows,
universe, benchmark, strategy, and exchange/cost assumptions were not changed.

## Runtime and candidate authority

```text
QLIB_ENV = rdagent4qlib
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_SOURCE_WORKTREE_CLEAN = YES
QLIB_RUNTIME_AUTHORITY_MATCH = YES
```

### LightGBM

The completed baseline was reused rather than rerun. Its canonical Git blob
configuration SHA-256 remains
`c6e6c4882adeb053d58e91b27d7d796fd9886dc1946d1d0540d5d9637f42ccaf`,
matching its recorded evidence. Recorder
`16bd043b00914e54bca7458efc5af9e9` remains `FINISHED`; predictions, labels,
signal-analysis artifacts, and portfolio-analysis artifacts are readable.

### Linear OLS

The new candidate uses the pinned upstream configuration
`examples/benchmarks/Linear/workflow_config_linear_Alpha158.yaml` with
`LinearModel(estimator=ols)`. The upstream model-specific processors were
preserved exactly in role: `RobustZScoreNorm` and `Fillna` for inference, and
`DropnaLabel` and `CSRankNorm` for learning. The fixed US provider and windows,
SPY benchmark, external SQLite Recorder, and experiment name are the only
necessary adaptations.

```text
COMPARISON_TYPE = QLIB_UPSTREAM_RECIPE_COMPARISON
LINEAR_CONFIG_SHA256 = b9a92537a9737ce909284e77e583ad20c0a3d2b18f795271d85db6c5ba5eafc1
LINEAR_EXPERIMENT = aq_p1_qlib_model_compare_linear_001
LINEAR_EXPERIMENT_ID = 1
LINEAR_RECORDER_ID = ef143027d1a0486cb876ba8e615496b5
LINEAR_RECORDER_STATUS = FINISHED
LINEAR_QRUN_EXIT_CODE = 0
LINEAR_EXTERNAL_RUN_ROOT = /home/zhou/AQ_DATA/P1/qlib-native-model-comparison-001/linear-run
```

Because the official recipes have different model-appropriate processors,
this is not a claim that model architecture is the sole differing variable.
No hyperparameter, seed, label, factor, window, strategy, or cost search was
performed.

### Optional CatBoost

The accepted environment contains no importable `catboost` package, and Qlib's
`CatBoostModel` therefore raises `ModuleNotFoundError`. The task forbids
installation, so CatBoost was not run and no CatBoost configuration was added.

```text
CATBOOST_STATUS = NOT_RUN_EXISTING_ENV_DEPENDENCY_UNAVAILABLE
CATBOOST_IMPORT = NOT_AVAILABLE
CATBOOST_RUN = NOT_RUN
```

This optional-candidate omission is not a failure of the mandatory LightGBM +
Linear comparison.

## Prediction evidence

Both Recorders contain 497,062 non-null predictions spanning 501 instruments
and the same real test interval:

```text
PREDICTION_ROWS = 497062
PREDICTION_NON_NULL = 497062
PREDICTION_INSTRUMENTS = 501
PREDICTION_START = 2022-01-03
PREDICTION_END = 2025-12-29
BACKTEST_SESSIONS = 1001
```

## Qlib-produced comparison

| Model | Upstream recipe | IC | ICIR | Rank IC | Rank ICIR | Annualized return with cost | Excess return with cost | Excess IR | Portfolio max drawdown | Mean daily turnover | Mean daily transaction cost | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| LightGBM | LightGBM Alpha158 | 0.009376443316672149 | 0.07344316259370916 | 0.00443446889692092 | 0.04557249853299947 | 0.2196360181792855 | 0.10306273779146044 | 0.7710368927486123 | -0.29470629620276534 | 0.19881074208482732 | 0.00019841838168595377 | FINISHED / REUSED |
| Linear OLS | Linear Alpha158 | 0.006651472793385135 | 0.04587821887751571 | 0.008168831235095873 | 0.054177414439987026 | 0.11656782106748978 | -0.0000054593203352934556 | -0.00004932256599191515 | -0.3529348992617742 | 0.2003437981896762 | 0.00019995118457489578 | FINISHED / NEW RUN |
| CatBoost | CatBoost Alpha158 | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | NOT RUN — EXISTING DEPENDENCY UNAVAILABLE |

The common benchmark annualized return was `0.1165732741355896`.
LightGBM's excess-return-with-cost maximum drawdown was
`-0.1246120961177218`; Linear's was `-0.13948903365904505`.

## Interpretation

```text
BEST_OBSERVED_P1_RESEARCH_CANDIDATE = LightGBM
CERTIFIED_MODEL = NONE
```

LightGBM is the stronger observed candidate across IC, ICIR, net annualized
and excess returns, excess information ratio, portfolio drawdown, turnover,
and transaction cost. Linear produces higher Rank IC and Rank ICIR, so the
evidence is not uniformly one-sided. The broader coherent metric pattern makes
LightGBM the useful exploratory reference for the next P1 step, but repeated
exposure to this test set prevents any claim of independent superiority or
formal promotion.

## Safety and current state

All Qlib/MLflow databases, models, predictions, labels, and reports remain
outside Git. No data was downloaded and no accepted environment or package was
changed.

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
P1_QLIB_NATIVE_BASELINE = COMPLETE
P1_QLIB_NATIVE_MODEL_COMPARISON = COMPLETE
MODEL_COMPARISON_CLASSIFICATION = EXPLORATORY_RESEARCH_ONLY_NOT_CERTIFIED
TEST_SET_IS_PRISTINE_OOS = NO
PIT_UNIVERSE_CERTIFIED = NO
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
CURRENT_NEXT = P1_QLIB_NATIVE_STRATEGY_COMPARISON
```
