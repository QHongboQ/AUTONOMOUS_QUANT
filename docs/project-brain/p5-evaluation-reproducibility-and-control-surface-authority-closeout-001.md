# P5 evaluation reproducibility and control-surface authority closeout 001

## Scope and outcome

This closeout starts from main
`8d9d73e6f585639c6d3c91675472c258adbb2637` and branch head
`d009b6d827f259e8bca7efc4ad47af5ee5e1851e`. It closes only the
reproducibility, CONTROL-surface, and P5 phase-exit coverage authorities for
the already-selected Qlib LightGBM evaluation vehicle. It uses pinned source,
repository authority, and two bounded synthetic fits. It does not inspect
performance, read project data, run a project fit or prediction, backtest,
access P2 V2 sealed OOS, contact SEC, or interfere with the independent
historical build.

```text
EVALUATION_MODEL_AUTHORITY = qlib.contrib.model.gbdt.LGBModel
PROCESSOR_SEMANTICS_GATE = PASS
REPRODUCIBILITY_GATE = PASS
CONTROL_SURFACE_GATE = PASS
P5_EXIT_COVERAGE_GATE = PASS_AUTHORITY_FROZEN_EXECUTION_PENDING
LINEAR_OLS_NULL_PRESERVING_COMPATIBLE = NO
```

The Linear OLS rejection remains unchanged.

## LightGBM 4.7.0 reproducibility authority

Official LightGBM 4.7.0 parameter authority states that `deterministic=true`
is a CPU-only reproducibility control and recommends forcing either column-
wise or row-wise histogram construction to avoid numerical instability. It
also establishes that `seed` has lower priority than explicitly supplied
component seeds and that `feature_fraction_seed` owns feature-fraction
sampling. The existing Qlib recipe and model hyperparameters are preserved;
only hidden reproducibility controls become explicit.

```text
device_type = cpu
deterministic = true
force_col_wise = true
force_row_wise = false
num_threads = 8

seed = 20260913
data_random_seed = 1
feature_fraction_seed = 2
bagging_seed = 3
drop_seed = 4
objective_seed = 5
extra_seed = 6

INPUT_ROW_ORDER = datetime ASC, episode_id ASC
INPUT_COLUMN_ORDER = FROZEN_BY_SURFACE_MANIFEST
RUNTIME_IDENTITY = QLIB_0.9.8.dev26_SOURCE_2fb9380..._LIGHTGBM_4.7.0_CPU
```

All other recipe values remain frozen, including:

```text
loss = mse
colsample_bytree = 0.8879
learning_rate = 0.2
subsample = 0.8789
lambda_l1 = 205.6999
lambda_l2 = 580.9768
max_depth = 8
num_leaves = 210
early_stopping_rounds = 50
num_boost_round = 1000
use_missing = true
zero_as_missing = false
bagging_freq = 0
```

### Synthetic repeatability proof

The proof used an in-memory fixture only: 12,000 deterministically ordered
rows, 162 ordered numeric columns, 7% deterministic NaN placement, 9,000
training rows, and 3,000 validation rows. The 162-column width represents the
frozen 157-column CONTROL width plus the largest authorized five-column
filing-feature increment. The same arrays and exact parameter object were
passed to native LightGBM 4.7.0 twice in the same pinned Python 3.10.21
runtime.

```text
SYNTHETIC_FIT_COUNT = 2
PROJECT_MODEL_TRAINING_COUNT = 0
PROJECT_PREDICTION_COUNT = 0
PROJECT_BACKTEST_COUNT = 0

RUN_1_MODEL_STRUCTURE_SHA256 = 2922239ec93cffe7c47d8a9e85cdab4c42647b71abc44b59a2af99e9a1bec18c
RUN_2_MODEL_STRUCTURE_SHA256 = 2922239ec93cffe7c47d8a9e85cdab4c42647b71abc44b59a2af99e9a1bec18c
REPEATED_MODEL_STRUCTURE_HASH_MATCH = YES

RUN_1_PREDICTION_SHA256 = d86ab87280c351cb82d8ea73f4f0647b4238ff09b4a9046f92ba2cee5b98a8ed
RUN_2_PREDICTION_SHA256 = d86ab87280c351cb82d8ea73f4f0647b4238ff09b4a9046f92ba2cee5b98a8ed
REPEATED_PREDICTION_BYTES_MATCH = YES
SYNTHETIC_REPRODUCIBILITY_POC = PASS
```

At eight threads, two validation reductions differed by at most
`1.7763568394002505e-15`; their callback-observed best-iteration counters were
174 and 175. This did not change the serialized model structure or one byte of
the predictions. A diagnostic one-thread run also made the metric trace and
best-iteration counter exact, but changing the frozen recipe to one thread is
not justified by either required repeatability output. The paired evaluation
therefore retains the existing fixed eight-thread resource policy and treats
the serialized model and prediction bytes as the repeatability outputs.

## Feature-subsampling compatibility

`colsample_bytree=0.8879` is preserved. Both sides of each directional
hypothesis use the same recipe, ordered feature manifest, and explicit
`feature_fraction_seed=2`. Adding columns is the preregistered treatment: the
native model's response to the larger feature universe is part of the effect
being tested. Forcing `colsample_bytree=1.0` would instead create a P5-specific
recipe change solely to neutralize intended treatment mechanics.

```text
FEATURE_SUBSAMPLING_ABLATION_COMPATIBILITY = PASS
COLSAMPLE_BYTREE_CHANGED = NO
P5_SPECIFIC_LIGHTGBM_RECIPE_CREATED = NO
```

## Exact CONTROL feature surface

The old P1 native-baseline YAML is not the P5 CONTROL identity. Its static
`market: sp500` authority and its 158-column Alpha158 surface include `VWAP0`,
which cannot be requested from the authoritative P2 ragged OHLCV provider.
The current P2-native `RaggedAlpha158` class is the already-approved,
episode-compatible surface. It invokes upstream `Alpha158DL` with K-bar,
`OPEN0`, `HIGH0`, `LOW0`, and rolling OHLCV families while omitting only
`VWAP0`.

```text
CONTROL_FEATURE_FAMILY = P2_RAGGED_ALPHA158_OHLCV_157
CONTROL_FEATURE_COLUMN_COUNT = 157
CONTROL_FEATURE_CONFIG = 30-research-system/qlib/dataset-adapter/aq_qlib_handoff/qlib_config.py
CONTROL_FEATURE_CONFIG_SHA256 = bbec91c3eb8b79e6e01c202310d52a1f1bc5fe5b1e0af13fb9f7dc7fba315b92
OLD_STATIC_ALPHA158_CONTROL_REUSED = NO
OLD_ONLY_FEATURE = VWAP0:$vwap/$close
```

The exact ordered column list is:

```text
KMID,KLEN,KMID2,KUP,KUP2,KLOW,KLOW2,KSFT,KSFT2,OPEN0,HIGH0,LOW0,
ROC5,ROC10,ROC20,ROC30,ROC60,MA5,MA10,MA20,MA30,MA60,
STD5,STD10,STD20,STD30,STD60,BETA5,BETA10,BETA20,BETA30,BETA60,
RSQR5,RSQR10,RSQR20,RSQR30,RSQR60,RESI5,RESI10,RESI20,RESI30,RESI60,
MAX5,MAX10,MAX20,MAX30,MAX60,MIN5,MIN10,MIN20,MIN30,MIN60,
QTLU5,QTLU10,QTLU20,QTLU30,QTLU60,QTLD5,QTLD10,QTLD20,QTLD30,QTLD60,
RANK5,RANK10,RANK20,RANK30,RANK60,RSV5,RSV10,RSV20,RSV30,RSV60,
IMAX5,IMAX10,IMAX20,IMAX30,IMAX60,IMIN5,IMIN10,IMIN20,IMIN30,IMIN60,
IMXD5,IMXD10,IMXD20,IMXD30,IMXD60,CORR5,CORR10,CORR20,CORR30,CORR60,
CORD5,CORD10,CORD20,CORD30,CORD60,CNTP5,CNTP10,CNTP20,CNTP30,CNTP60,
CNTN5,CNTN10,CNTN20,CNTN30,CNTN60,CNTD5,CNTD10,CNTD20,CNTD30,CNTD60,
SUMP5,SUMP10,SUMP20,SUMP30,SUMP60,SUMN5,SUMN10,SUMN20,SUMN30,SUMN60,
SUMD5,SUMD10,SUMD20,SUMD30,SUMD60,VMA5,VMA10,VMA20,VMA30,VMA60,
VSTD5,VSTD10,VSTD20,VSTD30,VSTD60,WVMA5,WVMA10,WVMA20,WVMA30,WVMA60,
VSUMP5,VSUMP10,VSUMP20,VSUMP30,VSUMP60,VSUMN5,VSUMN10,VSUMN20,VSUMN30,VSUMN60,
VSUMD5,VSUMD10,VSUMD20,VSUMD30,VSUMD60
```

`CONTROL_FEATURE_MANIFEST` is the compact, UTF-8, lexicographically
key-sorted JSON object with keys `feature_family` and `columns`. Each column
object contains its one-based `position`, exact `name`, and exact upstream
Qlib `expression` returned by the frozen `RaggedAlpha158.get_feature_config()`.

```text
CONTROL_FEATURE_MANIFEST_SHA256 = 7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463
```

## Exact CONTROL dataset identity

CONTROL is a date-valid left projection onto the complete P1/P5
episode-session grid. `episode_id` is the logical instrument key; rows are
ordered by `(datetime ASC, episode_id ASC)`. The 111 frozen identity
exclusions remain in the denominator with structurally missing P5
fundamentals. No current-ticker, static-universe, successor-price, or
pre-observation forward-fill shortcut is permitted.

The canonical `P5_CONTROL_DATASET_IDENTITY_V1` bundle fixes:

| Component | Frozen identity |
|---|---|
| P1 universe | 832 episodes; DVC snapshot `177a98ec2e94e460e4dff3166b991fac.dir`; accepted-facts SHA-256 `c1745a22c17c3a8a35bf56f504c1d96398c787492dce54a60ac85801799a9f62` |
| P5 identity | 721 bound, 111 exclusions; evidence checksum SHA-256 `32cba10a8f50c2a2a7dc1c9480547272b6f9ef501c49ef4c2a644c711f53dcd5`; replay SHA-256 `faab5726a5792b3d15cb1150f409845614a1b9bf8e2664e668ab46a5b2fbfb65` |
| P2 price surface | `D:/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data`; DVC dependency `fcd742578d6d89a5673bc1a618fc676b.dir`; build-report SHA-256 `eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142` |
| Provider authority | 12-fact SHA-256 `3cd9b13a1424609120a4e069ac2cf9f9b9aa61e2df919aa48cf51eeac616bc69`; Quantiacs primary plus bounded SimFin secondary |
| P2 counts | 730 security instruments; 745 membership ranges; 1,267,963 member-session rows |
| Feature surface | 157 columns; manifest SHA-256 `7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463` |

The canonical bundle uses compact sorted-key JSON and hashes to:

```text
CONTROL_DATASET_IDENTITY = P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135
```

Future materialization must additionally seal the produced dataset bytes in
DVC before either hypothesis may execute. This authority freezes the exact
inputs and projection semantics; it does not claim that the not-yet-built P5
evaluation surface already has a final artifact hash.

## Eleven fundamentals and P5 phase-exit coverage

No prior authority placed the eleven frozen structured fundamentals in
CONTROL. Option B is therefore rejected. Option A is frozen without adding
ratios, derived factors, subsets, or model search.

The ordered fundamental increment is exactly:

```text
Revenue
NetIncome
Assets
Liabilities
CommonEquity
NetCashFromOperatingActivities
CashAndCashEquivalents
CurrentAssetsTotal
CurrentLiabilitiesTotal
ShortTermDebt
LongTermDebt
```

The complete surface family is:

```text
BASE = exact 157-column CONTROL
BASE_PLUS_FUNDAMENTALS = BASE + exact 11 columns above
BASE_PLUS_FUNDAMENTALS_PLUS_FILING = BASE_PLUS_FUNDAMENTALS + exact 5 frozen filing columns
```

Only two directional hypotheses are authorized:

```text
H1 = BASE vs BASE_PLUS_FUNDAMENTALS
H2 = BASE_PLUS_FUNDAMENTALS vs BASE_PLUS_FUNDAMENTALS_PLUS_FILING
P5_INCREMENTAL_COMPARISON_COUNT = 2
```

H1 and H2 form one fixed, preregistered two-hypothesis family under the
existing `arch 8.0.0` multiple-testing authority. No subset, leave-one-out,
ratio, model, or hyperparameter search is permitted. The existing frozen
stationary-bootstrap and SPA/RealityCheck policy applies when the trials are
later authorized; this task executes neither comparison.

```text
STRUCTURED_FUNDAMENTAL_FEATURE_COUNT = 11
STRUCTURED_FUNDAMENTALS_INCLUDED_IN_CONTROL = NO
FILING_FEATURE_COUNT = 5
DOES_CURRENT_TWO_TRIAL_FILING_ABLATION_ALONE_SATISFY_P5_EXIT_CONDITION = NO
```

## Ownership and next authority

```text
AQ_FEATURE_ENGINE = NO
AQ_MODEL_ENGINE = NO
AQ_ABLATION_ENGINE = NO
AQ_STATISTICS_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0

HISTORICAL_BUILD_STATUS = RUNNING_WAITING_FOR_COMPLETION
HISTORICAL_BUILD_INTERFERENCE = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P6_ACTIVE = NO

TEST_RESULT = 18/18 PASS; 17 focused Qlib-adapter unit tests plus 1 pinned-runtime public-API probe
DIFF_CHECK = PASS

CURRENT_DEVELOPMENT_NEXT = P5_FILING_FEATURE_HISTORICAL_MATERIALIZATION_001
CURRENT_DEVELOPMENT_NEXT_GATE = WAITING_FOR_P5_HISTORICAL_FUNDAMENTALS_BUILD_TERMINAL_CLOSEOUT
FINAL_CLASSIFICATION = PASS_EVALUATION_REPRODUCIBILITY_CONTROL_SURFACE_AND_EXIT_COVERAGE_AUTHORITY_FROZEN
```
