# P3 AlphaGen Official LSTSQ Fastpath Closeout 001

## Result

The aborted first discovery attempt is closed without retaining its invalid
linear runtime projection. The proven ragged-PIT and missing-data corrections
remain, and AlphaGen's official least-squares pool optimizer is qualified as a
resource-feasible, nondefault configuration for the next formal run.

```text
PRIOR_DISCOVERY_RUN_001 = ABORTED_RESOURCE_CALIBRATION_INVALID
ROOT_CAUSE = UPSTREAM_L1_POOL_OPTIMIZATION_NONLINEAR_COST
RAGGED_PIT_CORRECTNESS = PASS
NAN_PRESERVATION = PASS
CURRENT_SURVIVOR_FILTERING = NO
SYNTHETIC_FILL = NO
VWAP_FABRICATION = NO
```

## Upstream authority and ownership

The pinned AlphaGen source is the clean current official master at
`259687e8f316994426416c530a94842a2fe6405e`. Its commit
`d4b5f4be7b9b082e7ad3c146d80d6e6ee31748a6`, titled
`Optional least-squares optimization`, introduced the official branch used
here. With `l1_alpha = 0.0`, `MseAlphaPool.optimize()` delegates to
`_optimize_lstsq()` and then `numpy.linalg.lstsq`. A deterministic fixture
observed that branch, observed no Adam entry, and matched the direct NumPy
solution.

```text
FAST_CONFIG_ID = ALPHAGEN_MSE_LSTSQ_FAST_V1
FAST_CONFIG_CLASSIFICATION = UPSTREAM_SUPPORTED_NONDEFAULT_CONFIGURATION
SELECTION_BASIS = RESOURCE_FEASIBILITY_ONLY
POOL_CAPACITY = 20
L1_ALPHA = 0.0
N_STEPS = 2048
BATCH_SIZE = 128
GAMMA = 1.0
ENTROPY_COEFFICIENT = 0.01
LSTM_LAYERS = 2
LSTM_MODEL_DIM = 128
LSTM_DROPOUT = 0.1
ALPHAGEN_MSE_POOL = UPSTREAM_WHOLE
ALPHAGEN_LSTSQ_OPTIMIZER = UPSTREAM_WHOLE
ALPHAGEN_L1_ADAM_OPTIMIZER = UPSTREAM_WHOLE
AQ_CUSTOM_OPTIMIZER = NO
AQ_EXPRESSION_CACHE = NO
AQ_CUSTOM_FACTOR_POOL = NO
AQ_CUSTOM_RL = NO
AQ_CUSTOM_PPO = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

`ALPHAGEN_MSE_L1_REFERENCE_V1` remains supported with `l1_alpha = 0.005`, but
is classified `UPSTREAM_REFERENCE_RESOURCE_EXPENSIVE_NOT_CURRENT_MAINLINE`.
No factor-quality comparison was performed, and least squares is not claimed
to be equivalent or superior to L1 Adam.

## Candidate-ineligible resource calibration

One seed-999 calibration used the full authoritative TRAIN dynamic PIT view:
627 identities and 583,037 member-session rows. It ran 8,192 timesteps and is
not eligible as a factor candidate. Historical TEST and sealed OOS rows
accessed were both zero.

```text
CALIBRATION_RUNTIME_SECONDS = 66.9645478859893
Q1_SECONDS = 15.950375190994237
Q2_SECONDS = 15.934579758992186
Q3_SECONDS = 17.584157066012267
Q4_SECONDS = 17.493673660996137
EARLY_SECONDS_PER_1000 = 7.788269136227655
LATE_SECONDS_PER_1000 = 8.54183284228327
MATURITY_SLOWDOWN_RATIO = 1.0967562487729607
FINAL_POOL_SIZE = 20
EXPRESSIONS_GENERATED = 113
EXPRESSIONS_EVALUATED = 61
ADMISSIONS = 42
REPLACEMENTS = 22
GPU_UTILIZATION_PERCENT_MIN_MEDIAN_MAX = 7 / 9 / 77
GPU_MEMORY_MIB_MIN_MEDIAN_MAX = 237 / 883 / 1115
CPU_UTILIZATION_PERCENT_MIN_MEDIAN_MAX = 94.5 / 97.35 / 99.0
RSS_BYTES_MIN_MEDIAN_MAX = 3212619776 / 3372892160 / 3372892160
NO_OOM = YES
STABLE_MEMORY = YES
RUNTIME_ERRORS = 0
```

The frozen budget formula is
`Q4_SECONDS / 2048 * candidate_steps * 3 * 1.5`. It projects 314.886 seconds
for 8,192 steps, 629.772 seconds for 16,384 steps, and 1,259.545 seconds for
32,768 steps across three seeds including the safety factor. The largest
candidate under the 7,200-second resource ceiling is therefore 32,768 steps
per seed. This decision uses no IC, RankIC, expression content, pool objective,
or validation result.

## Evidence and next state

All seven required immutable JSON artifacts are stored privately under:

`D:/AQ_DATA/P3/alphagen-official-lstsq-fastpath-closeout-001/`

The SHA-256 of `summary.json` is:

`d807aa503f082f6c526bd67606dc6e3a142426ef2ded2d85ce5dcd4c7a3d83af`

```text
CORRECTNESS_TESTS = 18/18_PASS
ABORTED_LINEAR_CALIBRATION_REMOVED = YES
ALPHAGEN_MSE_LSTSQ_FAST_V1 = QUALIFIED
SELECTED_FORMAL_TIMESTEPS_PER_SEED = 32768
PROJECTED_THREE_SEED_RUNTIME_WITH_SAFETY_SECONDS = 1259.5445035917219
FORMAL_FACTOR_DISCOVERY_EXECUTED = NO
CURRENT_NEXT = P3_ALPHAGEN_US_PIT_FACTOR_DISCOVERY_LSTSQ_RUN_001
```
