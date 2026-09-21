# P5 filing-feature processor-semantics authority resolution 001

## Scope and decision

This authority resolution starts from main
`8d9d73e6f585639c6d3c91675472c258adbb2637` and branch head
`37369d92fccbc083fbc9ff6beb14e017909fb63a`. It uses only pinned Microsoft
Qlib source inspection and an in-memory synthetic interface proof. It performs
no SEC request, project-data load, model fit, prediction, backtest, P6 action,
or P2 V2 sealed-OOS access. The independent historical build process was only
observed as running and was not modified.

The prior Linear OLS rejection remains authoritative. A different existing
Qlib vehicle, `qlib.contrib.model.gbdt.LGBModel`, passes the frozen sparse
point-event semantics without an AQ processor or missing-value engine.

```text
EVALUATION_MODEL_AUTHORITY = FROZEN
P5_EVALUATION_MODEL = qlib.contrib.model.gbdt.LGBModel
P5_EVALUATION_MODEL_ROLE = FIXED_FEATURE_ABLATION_VEHICLE
P5_MODEL_SELECTION_BASIS = SEMANTIC_COMPATIBILITY_AND_EXISTING_UPSTREAM_AUTHORITY_ONLY
P1_LIGHTGBM_PERFORMANCE_USED_FOR_SELECTION = NO
MODEL_SEARCH = NO
MODEL_COMPARISON = NO
```

## Pinned upstream evidence

The source worktree was clean at the required identity.

```text
UPSTREAM_OWNER = MICROSOFT_QLIB
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_RUNTIME_PYTHON = 3.10.21
LIGHTGBM_VERSION = 4.7.0
MODEL_CLASS = qlib.contrib.model.gbdt.LGBModel
UPSTREAM_CONFIG_PATH = examples/benchmarks/LightGBM/workflow_config_lightgbm_Alpha158.yaml
UPSTREAM_SOURCE_CONFIG_SHA256 = 0cbe1f729f43a2b8cd735759e6244c2e9f8db967555bfe24a7143fce4605d680
ADAPTED_CONFIG_PATH = 30-research-system/qlib/native-baseline/workflow_config_lightgbm_Alpha158_US.yaml
ADAPTED_CONFIG_RAW_SHA256 = 4f5c6fc2b8c56e0d8b201423ae3a2e73cab3e0b2108bcc4edd6033b3d28c1953
ADAPTED_CONFIG_CANONICAL_LF_SHA256 = c6e6c4882adeb053d58e91b27d7d796fd9886dc1946d1d0540d5d9637f42ccaf
```

Pinned source establishes all of the following:

1. `Alpha158` defaults `infer_processors=[]`.
2. Its default learn processors are `DropnaLabel` followed by
   `CSZScoreNorm(fields_group=label)`, so they do not transform feature
   values.
3. `DataHandlerLP.PTYPE_A` is the literal value `append`.
4. `LGBModel._prepare_data()` selects `df["feature"]` and passes `x.values`
   directly to `lightgbm.Dataset(..., free_raw_data=False)`.
5. LightGBM 4.7.0 natively treats NaN as missing with `use_missing=true`,
   while `zero_as_missing=false` keeps legitimate zero distinct from NaN.

## Linear OLS remains rejected

The official Linear recipe applies
`RobustZScoreNorm(fields_group=feature)` and `Fillna(fields_group=feature,
fill_value=0)`. Pinned `Fillna` source performs a feature-group `fillna(0)`.
Pinned `LinearModel.fit()` also performs `df_train.dropna()`.

Removing `Fillna` alone would therefore replace null-to-zero corruption with
row-population divergence. A new imputation, mask, or sparse-linear processor
would change the frozen semantics and is not authorized.

```text
LINEAR_OLS_NULL_PRESERVING_COMPATIBLE = NO
LINEAR_REJECTION_REASON = OFFICIAL_FILLNA_CONVERTS_FEATURE_NULL_TO_ZERO; REMOVING_FILLNA_STILL_DROPS_ROWS_IN_LINEAR_MODEL_FIT; CUSTOM_IMPUTATION_OR_MASK_NOT_AUTHORIZED
```

## Frozen static-data handoff

The Alpha158 handler does not own the external P5 columns. The exact handoff
authority is:

```text
combined baseline + P5 DataFrame
  -> qlib.data.dataset.loader.StaticDataLoader
  -> qlib.data.dataset.handler.DataHandlerLP
  -> qlib.data.dataset.DatasetH
  -> qlib.contrib.model.gbdt.LGBModel
```

The minimum handler configuration is frozen as:

```text
STATIC_DATA_LOADER = qlib.data.dataset.loader.StaticDataLoader
DATA_HANDLER = qlib.data.dataset.handler.DataHandlerLP
FEATURE_SHARED_PROCESSORS = []
FEATURE_INFER_PROCESSORS = []
LEARN_PROCESSORS = DropnaLabel(fields_group=label) -> CSZScoreNorm(fields_group=label)
PROCESS_TYPE = append
NULL_PRESERVATION = REQUIRED
```

`DropnaLabel` is allowed to remove rows whose label is null. No feature-null
row may be removed solely because a P5 feature is null.

## Synthetic null-semantics proof

The in-memory fixture contained three synthetic instruments, six dates
spanning train/valid/test-shaped intervals, two baseline numeric features,
and all five frozen P5 columns. The fixture included legitimate zero, one,
positive counts, non-event NaN, explicit-missing NaN, and one null label.

The proof constructed only upstream `StaticDataLoader`, `DataHandlerLP`,
`DatasetH`, `LGBModel`, and native LightGBM `Dataset` objects. It wrote no
fixture or model artifact and called no model fit.

```text
SYNTHETIC_INSTRUMENT_COUNT = 3
SYNTHETIC_INPUT_ROW_COUNT = 18
INFER_ROW_COUNT = 18
LEARN_ROW_COUNT = 17
LABEL_NULL_ROW_DROP_COUNT = 1
DATASET_SEGMENT_ROWS = train:6; valid:5; test:6

NULL_INPUT_COUNT = 19
NULL_HANDLER_OUTPUT_COUNT = 19
ZERO_INPUT_COUNT = 38
ZERO_HANDLER_OUTPUT_COUNT = 38
NONZERO_INPUT_COUNT = 33
NONZERO_HANDLER_OUTPUT_COUNT = 33

LABEL_FILTERED_NULL_COUNT = 18
LABEL_FILTERED_ZERO_COUNT = 36
LABEL_FILTERED_NONZERO_COUNT = 31
LABEL_FILTERED_FEATURES_EQUAL_INPUT_SUBSET = YES

NONZERO_INPUT_VALUES_UNCHANGED = YES
NO_FORWARD_FILL = YES
NO_BACKWARD_FILL = YES
NO_NULL_TO_ZERO = YES
NO_ROW_DROP_DUE_TO_P5_FEATURE_NULL = YES
SYNTHETIC_NULL_SEMANTICS_POC = PASS
```

The difference between inference and learning counts is exactly the single
allowed null-label row. Rows containing P5 feature nulls remained present in
the learning surface when their labels were valid.

For the Qlib-created native LightGBM inputs, `Dataset.construct()` succeeded
with no fit:

```text
LIGHTGBM_NATIVE_TRAIN = rows:6; columns:7; nulls:6; zeros:13
LIGHTGBM_NATIVE_VALID = rows:5; columns:7; nulls:6; zeros:10
LIGHTGBM_NATIVE_DATASET_CONSTRUCTION = PASS
LIGHTGBM_NULL_PRESERVING_COMPATIBLE = YES
MODEL_TRAINING_COUNT = 0
```

The construction-level output returned by `Dataset.get_data()` was exactly
equal, including each NaN position and zero, to the corresponding
`DatasetH.prepare(..., data_key=DK_L)` feature matrix.

## Frozen model configuration and reproducibility boundary

The existing AQ-adapted Qlib LightGBM recipe is reused without performance
selection or tuning. Hidden Qlib defaults and missing-value/stochastic
defaults are made explicit as authority. The pinned upstream example uses 20
threads; the already-exercised AQ US adaptation fixes 8, so this authority
retains 8 rather than selecting a new value:

```text
loss = mse
colsample_bytree = 0.8879
learning_rate = 0.2
subsample = 0.8789
lambda_l1 = 205.6999
lambda_l2 = 580.9768
max_depth = 8
num_leaves = 210
num_threads = 8
early_stopping_rounds = 50
num_boost_round = 1000
use_missing = true
zero_as_missing = false
bagging_freq = 0
resolved_internal_objective = mse
resolved_internal_verbosity = -1
```

`subsample=0.8789` is retained from the recipe, but LightGBM's native
`bagging_freq=0` means row bagging remains disabled. Feature subsampling is
active through `colsample_bytree=0.8879`.

Every relevant native seed is explicit. A subsequent bounded reproducibility
closeout also enables LightGBM's CPU deterministic mode and forces column-wise
histogram construction. These are execution controls, not performance tuning:

```text
seed = 20260913; lower priority than explicit component seeds
data_random_seed = 1
feature_fraction_seed = 2
bagging_seed = 3
drop_seed = 4
objective_seed = 5
extra_seed = 6
deterministic = true
force_col_wise = true
force_row_wise = false
device_type = cpu
boosting = gbdt
extra_trees = false
```

Reproducibility authority is bounded to the pinned Qlib source, LightGBM
4.7.0 CPU runtime/build, fixed `num_threads=8`, fixed input row/column ordering,
and the explicit component seeds above. Two identical in-memory synthetic
fits produced identical serialized model SHA-256 and byte-identical
predictions. See [P5 Evaluation Reproducibility and Control-Surface Authority
Closeout 001](p5-evaluation-reproducibility-and-control-surface-authority-closeout-001.md).

`colsample_bytree=0.8879` remains unchanged. Feature subsampling is part of the
frozen model recipe, and the model's response to a preregistered added feature
set is part of the treatment. The same ordered surface, seed, and recipe apply
to both sides of each paired comparison.

## Two-trial and split authority

```text
P5_INCREMENTAL_COMPARISON_COUNT = 2
H1 = EXACT_157_COLUMN_P2_RAGGED_ALPHA158_OHLCV_CONTROL vs SAME_PLUS_EXACT_11_FUNDAMENTALS
H2 = BASE_PLUS_EXACT_11_FUNDAMENTALS vs SAME_PLUS_EXACT_5_FILING_FEATURES
TRAIN = 2015-04-01 through 2019-12-31
VALID = 2020-01-01 through 2021-12-31
HISTORICAL_RESEARCH_TEST = 2022-01-03 through 2024-12-31
```

Model, kwargs, handler, label, processors, segments, component seeds,
runtime, strategy, and cost assumptions must be identical. There is no
feature-subset search, leave-one-out run, alternate model, or model search.
None of these windows is executed by this task.

## Safety, ownership, and next authority

The historical fundamentals process remained live under its existing PID and
was not signalled, read for research output, restarted, or modified.

```text
HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
HISTORICAL_BUILD_INTERFERENCE = NO
AQ_FEATURE_PROCESSOR = NO
AQ_MISSING_VALUE_ENGINE = NO
AQ_MODEL_ENGINE = NO
AQ_TRAINING_ENGINE = NO
AQ_BACKTEST_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
SEC_DATA_REQUEST_COUNT = 0
PROJECT_MODEL_TRAINING_COUNT = 0
PROJECT_PREDICTION_COUNT = 0
PROJECT_BACKTEST_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P6_ACTIVE = NO
PROCESSOR_SEMANTICS_GATE = PASS
CURRENT_DEVELOPMENT_NEXT = P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_001
CURRENT_DEVELOPMENT_NEXT_GATE = WAITING_FOR_P5_HISTORICAL_FUNDAMENTALS_BUILD_TERMINAL_CLOSEOUT
FINAL_CLASSIFICATION = PASS_PROCESSOR_SEMANTICS_RESOLVED_LIGHTGBM_AUTHORITY_FROZEN
```
