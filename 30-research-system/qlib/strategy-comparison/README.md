# Qlib-native bounded strategy comparison

This directory records the fixed P1 comparison of three Qlib
`TopkDropoutStrategy` configurations driven by one completed LightGBM
prediction artifact. Microsoft Qlib is the `UPSTREAM_WHOLE` owner of strategy,
portfolio simulation, costs, backtest, Recorder, and portfolio analysis. AQ
adds configuration and evidence only.

## Frozen boundary

- prediction authority: baseline Recorder
  `16bd043b00914e54bca7458efc5af9e9`, artifact `pred.pkl`
- provider: `/home/zhou/AQ_DATA/P1/qlib-native-baseline-001/qlib_data`
- region / market / benchmark: `us` / `sp500` / `SPY`
- backtest: 2022-01-03 through 2025-12-29
- account: 100,000,000
- exchange: limit 0.095, close price, open cost 0.0005, close cost
  0.0015, minimum cost 5
- candidates: baseline 50/5, concentrated 30/3, diversified 100/10

The LightGBM model is not retrained and predictions are not regenerated. The
completed 50/5 baseline is reused. The 30/3 and 100/10 candidates receive the
same loaded prediction object in separate external Qlib Recorders and are
evaluated through Qlib `PortAnaRecord`.

No grid, optimizer, automatic search, custom strategy, custom backtester,
custom portfolio engine, or custom metric engine is introduced. All external
Recorder/MLflow artifacts remain outside Git under
`/home/zhou/AQ_DATA/P1/qlib-native-strategy-comparison-001`.

## Interpretation boundary

This is an `EXPLORATORY_P1_STRATEGY_COMPARISON`. The test set is not pristine
OOS. No candidate can be called certified, promoted, production-ready, or
authorized for live capital from this comparison.

## Observed result

The concentrated 30/3 candidate produced the strongest observed annualized
return, excess return and excess information ratio. It also had the deepest
portfolio drawdown and marginally higher turnover/cost than the 50/5 baseline.
The diversified 100/10 candidate produced the shallowest portfolio drawdown,
but materially lower return and excess information ratio. On the combined
evidence, 30/3 is the `BEST_OBSERVED_P1_STRATEGY_CANDIDATE`, with the drawdown
tradeoff explicitly retained. This label is exploratory only; no strategy is
certified or promoted.
