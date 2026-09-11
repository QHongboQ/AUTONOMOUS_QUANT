# Qlib-native minimal quant baseline

This directory contains configuration and provenance notes for the first P1
end-to-end Qlib-native real-data research baseline. Microsoft Qlib owns the
provider, `DatasetH`, `Alpha158`, `LGBModel`, Recorder, signal analysis,
`TopkDropoutStrategy`, backtest, cost simulation, and portfolio analysis.
AQ supplies configuration and evidence only; it does not implement a parallel
engine.

## Authority and execution

- Qlib version: `0.9.8.dev26`
- pinned upstream source: `2fb9380b342556ddb50a4b24e4fe8655d548b2b8`
- upstream authority: `examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml`
- environment: `rdagent4qlib` under WSL Ubuntu 24.04
- provider: `/home/zhou/AQ_DATA/P1/qlib-native-baseline-001/qlib_data`
- external run root: `/home/zhou/AQ_DATA/P1/qlib-native-baseline-001/native-run`
- experiment: `aq_p1_qlib_native_minimal_baseline_001`

The provider and all Qlib/MLflow outputs are external to the Git repository.
The run uses Qlib's CLI and Recorder directly, with an explicit SQLite-backed
`MLflowExpManager`; there is no AQ experiment database or wrapper.

## Bounded configuration deviations

The model methodology and LightGBM hyperparameters are unchanged from the
pinned upstream benchmark except `num_threads`, reduced from 20 to 8 solely
for resource safety. The following data-specific substitutions are necessary:

- region changes from China to US;
- market changes from `csi300` to the provider's Qlib-native `sp500` universe;
- benchmark changes from `SH000300` to verified in-provider `SPY`;
- provider coverage begins on 2015-01-02, so the original 2008-2020 windows
  are replaced by chronological, non-overlapping multi-year windows:
  train 2015-04-01 through 2019-12-31, validation 2020-01-01 through
  2021-12-31, and test/backtest 2022-01-03 through 2025-12-29;
- handler fit begins on 2015-04-01 to leave an initial Alpha158 lookback
  interval after provider inception;
- external SQLite tracking and an explicit experiment name make the run
  identifiable and avoid the unsupported MLflow filesystem backend.

No boundary or parameter was selected from model performance. The provider's
`sp500` membership is a best-effort research universe rather than an
institutionally complete point-in-time universe.

## Classification

This configuration is `RESEARCH_ONLY_NOT_CERTIFIED` with survivorship-bias
control `BEST_EFFORT_NOT_CERTIFIED`. It provides no certification gate,
production authorization, live-capital implication, or trading authority.
The deferred AQ DatasetSnapshot/PIT-universe and Qlib dataset-adapter paths are
not dependencies of this native P1 baseline.
