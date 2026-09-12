# Qlib-native bounded model comparison

This directory holds configuration and provenance for the P1 exploratory
comparison between the completed LightGBM baseline and Qlib's official
`LinearModel(estimator=ols)` Alpha158 recipe. Microsoft Qlib remains the
`UPSTREAM_WHOLE` owner of data handling, factors, training, prediction,
Recorder, signal analysis, Top-K strategy, backtest, costs, and portfolio
analysis. AQ adds no runner, tournament engine, model engine, or analytics
engine.

## Fixed comparison boundary

- provider: `/home/zhou/AQ_DATA/P1/qlib-native-baseline-001/qlib_data`
- region / market / benchmark: `us` / `sp500` / `SPY`
- train: 2015-04-01 through 2019-12-31
- validation: 2020-01-01 through 2021-12-31
- test and backtest: 2022-01-03 through 2025-12-29
- factor family: Qlib Alpha158
- strategy: `TopkDropoutStrategy(topk=50, n_drop=5)`
- account: 100,000,000
- exchange: limit 0.095, close price, open cost 0.0005, close cost
  0.0015, minimum cost 5

The merged LightGBM run is reused without modification or rerun. The Linear
candidate uses pinned upstream authority
`examples/benchmarks/Linear/workflow_config_linear_Alpha158.yaml`, including
its model-appropriate `RobustZScoreNorm`, `Fillna`, `DropnaLabel`, and
`CSRankNorm` processors. Consequently this is a
`QLIB_UPSTREAM_RECIPE_COMPARISON`, not a laboratory claim that model class is
the only varying input.

Adaptations are limited to the same US provider, market, benchmark and fixed
data-supported windows used by the baseline, plus an identifiable experiment
and external SQLite Recorder location. No model, factor, window, Top-K, or cost
parameter is tuned.

## Candidate boundary

- LightGBM: reused completed baseline Recorder.
- Linear OLS: mandatory new Qlib-native run.
- CatBoost: not run because `catboost` is absent from the accepted environment
  and the task forbids installation. No CatBoost configuration is added.

All Qlib/MLflow artifacts remain under
`/home/zhou/AQ_DATA/P1/qlib-native-model-comparison-001`, outside Git.

## Interpretation

This is an `EXPLORATORY_P1_MODEL_COMPARISON`. The test set was already
observed during the LightGBM baseline, so `TEST_SET_IS_PRISTINE_OOS = NO`.
No result is certified, promoted, authorized for production, or evidence for
live-capital use. Metric differences must not be described as independent
proof of model superiority.

## Observed result

The Linear Recorder finished successfully with 497,062 non-null predictions
over the same 501 instruments and 2022-01-03 through 2025-12-29 test period.
LightGBM was the stronger observed P1 research candidate across IC, ICIR,
net annualized/excess return, information ratio, drawdown, turnover, and cost;
Linear had the higher Rank IC and Rank ICIR. This mixed exploratory evidence
does not certify either model. Exact Qlib-produced metrics and Recorder
provenance are retained in the corresponding Project Brain evidence document.
