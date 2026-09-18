# P3 AlphaGen US PIT VWAP Action Mask POC 001

## Result

The prior feature-space blocker is resolved without modifying AlphaGen.
`sb3-contrib==2.0.0` owns the outer `ActionMasker`; the AQ-specific function
copies AlphaGen's native mask and sets only the unavailable VWAP action to
false. `MaskablePPO` then consumes the composed mask through its public
interface.

```text
ALPHAGEN_SHA = 259687e8f316994426416c530a94842a2fe6405e
ALPHAGEN_UPSTREAM_SOURCE_MODIFIED = NO
SB3_CONTRIB_VERSION = 2.0.0
ACTION_MASKER_USED = YES
VWAP_ACTION_INDEX = SIZE_OP + int(FeatureType.VWAP) = 27
MASK_LENGTH = 48
MASK_DIFF_COUNT_MAX = 1
VWAP_ACTION_ALWAYS_FALSE = YES
OTHER_ACTION_SEMANTICS_UNCHANGED = YES
```

Across the successful 2,048-action PPO run, no VWAP action was selected and no
VWAP expression was produced.

```text
VWAP_ACTION_SELECTION_COUNT = 0
VWAP_EXPRESSION_COUNT = 0
VWAP_FEATURE_SPACE_BLOCKER = RESOLVED_BY_UPSTREAM_SB3_ACTION_MASKER
```

## Data and target boundary

The POC reads the existing immutable `RaggedPanelBuildV1` Qlib provider. The
build report SHA-256 remains
`eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142`.
No sixth channel was created.

The selection rule is independent of returns: take the lexicographically first
32 security identities in the intersection of `p2_pit` membership on
2024-01-02 and 2024-03-28. Forty historical sessions and two future sessions
were loaded only as the expression/target buffers. The evaluated interval has
61 sessions and 1,952 member-session rows; the complete buffered view has
3,296 rows. All five channels were observed for this deterministic cohort.

```text
DATA_FEATURES = OPEN,CLOSE,HIGH,LOW,VOLUME
VWAP_AVAILABLE = NO
DATA_EVALUATION_RANGE = 2024-01-02_THROUGH_2024-03-28
DATA_INSTRUMENT_COUNT = 32
DATA_EVALUATION_ROWS = 1952
MISSINGNESS_POLICY = PRESERVE_AUTHORITATIVE_NAN_NO_FILL_NO_SYNTHETIC_VALUES
TARGET_AUTHORITY = P2_CERTIFICATION_PROTOCOL_V1_QLIB_ALPHA158
TARGET_EXPRESSION = Ref($close, -2)/Ref($close, -1) - 1
TARGET_HORIZON_SESSIONS = 2
SEALED_OOS_ROWS_ACCESSED = 0
```

The data view holds the AlphaGen-required tensor orientation
`buffered_days × feature_index × stocks`. Exact channel, target alignment, and
`Ref($close,5d)` fixture tests passed.

## Bounded runtime proof

The run used the frozen upstream construction: `MseAlphaPool`, `AlphaEnv`,
`MaskablePPO`, `MlpPolicy`, and `LSTMSharedNet`. It used seed 0, CUDA device 0,
`n_steps=2048`, `total_timesteps=2048`, and batch size 128. This is a runtime
POC only and is not research-quality or certification evidence.

```text
RL_ENV_INITIALIZED = YES
PPO_LEARNING_EXECUTED = YES
EXPRESSIONS_GENERATED = 9
EXPRESSIONS_EVALUATED = 7
POOL_ADMISSION_COUNT = 5
RUNTIME_SECONDS = 20.919754761998774
P3_RUNTIME_POC_ALPHA_PRODUCED = YES
P3_RUNTIME_POC_ALPHA_EXPRESSION = Div(Sub(30.0,$close),30.0)
P3_RUNTIME_POC_ALPHA_IC = 0.02986137755215168
P3_RUNTIME_POC_ALPHA_RANK_IC = 0.025259578600525856
P3_RUNTIME_POC_ALPHA_WEIGHT = 0.037002231410402535
ALPHA_CLASSIFICATION = P3_RUNTIME_POC_ALPHA
```

One first bounded execution completed learning but failed while serializing a
NumPy integer in the post-run evidence writer. No result from that execution
was retained. The writer was narrowed to native JSON scalar types and the same
fixed 2,048-step POC was run once more. No budget, data, seed, mask, or model
selection changed.

```text
BOUNDED_PPO_EXECUTION_COUNT = 2
FIRST_EXECUTION_DISPOSITION = POST_LEARNING_EVIDENCE_SERIALIZATION_FAILURE_NO_RESULT_RETAINED
```

## Ownership and evidence

AlphaGen owns its expression engine, RL environment, PPO construction, factor
pool, and IC logic. `sb3-contrib` owns action masking. AQ owns only the bounded
US PIT tensor view, target binding, unavailable-feature mask, and calculator
bridge. Adapter LOC is 117, counted as the physical source lines returned by
`inspect.getsourcelines` for those six adapter symbols; the bounded runner and
tests are excluded.

```text
AQ_US_PIT_VIEW = AQ_DOMAIN_SPECIFIC_THIN_ADAPTER
AQ_VWAP_MASK = AQ_DOMAIN_SPECIFIC_THIN_ADAPTER
AQ_ALPHA_CALCULATOR = AQ_DOMAIN_SPECIFIC_THIN_ADAPTER
AQ_CUSTOM_RL = NO
AQ_CUSTOM_PPO = NO
AQ_CUSTOM_EXPRESSION_ENGINE = NO
AQ_CUSTOM_FACTOR_POOL = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

Private evidence is frozen under:

`D:/AQ_DATA/P3/alphagen-us-pit-vwap-action-mask-poc-001`

The final `poc_summary.json` SHA-256 is:

`8acde157d3dfed66e70891de7d639ba9fa246e7dd01924fddc86be9cd19db4c0`

```text
RD_AGENT_LOCAL_BRAIN_SEARCH = PAUSED_NOT_P3_BLOCKER
AUTONOMOUS_ATTEMPT_004_AUTHORIZED = NO
CURRENT_NEXT = P3_ALPHAGEN_US_PIT_INTEGRATION_001
FINAL_CLASSIFICATION = PASS
```
