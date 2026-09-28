# P3 Local Runtime Retirement and DeepSeek One-Code Benchmark 001

Task date: 2026-09-28

## Current authority

The local Ollama generative route is retired. P3 uses the upstream-native
`rdagent.oai.backend.LiteLLMAPIBackend` and LiteLLM DeepSeek provider route with
`deepseek/deepseek-flash`, thinking enabled, `reasoning_effort=high`, and a
65,536-token output ceiling. The separately owned local embedding slot remains.
No AQ cloud client, parser, retry system, or generic benchmark engine was added.

```text
LOCAL_GENERATIVE_LLM_ACTIVE = NO
LOCAL_EMBEDDING_ACTIVE = YES_SEPARATE_CAPABILITY
AQ_CUSTOM_LLM_BACKEND_COUNT = 0
AQ_CUSTOM_EVALUATOR = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

PR #141 remains superseded and closed. PR #142 was returned to clean architecture
head `973e4962e6536d8f447e715792a44b32eb8f2563` before this benchmark; the confused
unmerged head `457e3d35b86e5825bbbf4dbddf03ed30f6bfabb6` has no authority.

## Valid cloud preflight

The official model list, native LiteLLM chat, high-reasoning mapping, JSON
output, and RD-Agent native parsing passed. The earlier 4,096-token screen is
only an invalid inherited local-runtime-budget diagnostic.

```text
DEEPSEEK_AUTH = PASS
DEEPSEEK_MODEL_DISCOVERY = PASS
LITELLM_CHAT_COMPLETION = PASS
DEEPSEEK_REASONING_HIGH = PASS
DEEPSEEK_JSON_OUTPUT = PASS
RDAGENT_NATIVE_PARSE = PASS
EFFECTIVE_MODEL = deepseek/deepseek-flash
EFFECTIVE_REASONING_EFFORT = high
EFFECTIVE_THINKING = enabled
EFFECTIVE_MAX_TOKENS = 65536
DEEPSEEK_4096_SCREEN = INVALID_LEGACY_LOCAL_RUNTIME_CONFIGURATION_DIAGNOSTIC
```

The previous multi-instrument alpha053 result, including its `0.404742...`
correlation, is now only `SUPERSEDED_MULTI_INSTRUMENT_BENCHMARK_DIAGNOSTIC`.
It is neither a DeepSeek capability PASS nor FAIL and is not current authority.

## One-code / 100-single-stock official benchmark

The immutable full source was verified before use:

```text
SOURCE = D:/AQ_DATA/P3/rdagent-us-ragged/factor-source/full/daily_pv.h5
SOURCE_SHA256 = deacd04bad8f5321bd49cc63cf9be37d38e4ae7b33b5c223021c80dedad98b21
DISTINCT_INSTRUMENT_COUNT = 730
ELIGIBLE_INSTRUMENT_COUNT = 726
SELECTED_INSTRUMENT_COUNT = 100
SELECTION = LEXICOGRAPHIC_FIRST_100_WITH_ROW_COUNT_AT_LEAST_10
CANARY_INSTRUMENT = P2SEC00087FD1DC9463C008A58ABC120BDBA4F9FF2F67952DD09DC6D729B71BD66F09
```

Each fixture contains only the selected stock and preserves every original row,
value, missing value, column, index name, and HDF key. One official alpha053
FactorCoSTEER screen ran on the canary. Its final code was frozen and no further
successful LLM calls occurred during the 100-stock stage.

```text
DEEPSEEK_GENERATION_SCREEN_COUNT = 1
GENERATED_IMPLEMENTATION_SHA256 = d4832e0bf8479a0e4368fcabc317367e5601a25a73fee4eb8dfdc17ecd7a82de
TOTAL_DEEPSEEK_LLM_CALLS = 4
TOTAL_INPUT_TOKENS = 8423
TOTAL_OUTPUT_TOKENS = 400
TOTAL_ESTIMATED_COST_USD = 0.0030069
SAME_IMPLEMENTATION_USED_FOR_ALL_100 = YES
OFFICIAL_ALPHA053_UNCHANGED = YES
OFFICIAL_GT_CODE_UNCHANGED = YES
OFFICIAL_EVALUATOR_UNCHANGED = YES
```

All 100 independent fixture executions completed. Every output passed the
single-column, row-count, and index checks, while every official equal-value
comparison failed. The generated DataFrame retained the `alpha053` column name
while the official evaluator names the ground-truth Series `gt_factor`; its
unchanged column-aligned subtraction therefore produced no equal values. The
generated implementation also replaces infinities with missing values while the
official ground truth does not. The exam and evaluator were not changed.

```text
STOCK_EVALUATION_COUNT = 100
SINGLE_COLUMN_PASS_COUNT = 100
ROW_COUNT_RATIO_ONE_COUNT = 100
INDEX_RATIO_ONE_COUNT = 100
EQUAL_VALUE_RATIO_ONE_COUNT = 0
PASS_COUNT = 0
FAIL_COUNT = 100
PASS_RATE = 0.0
FAILURE_TAXONOMY = OFFICIAL_VALUE_COMPARISON_FAILURE:100
MIN_CORRELATION = UNDEFINED_ALL_OFFICIAL_SINGLE_STOCK_CORRELATIONS_NAN
MEDIAN_CORRELATION = UNDEFINED_ALL_OFFICIAL_SINGLE_STOCK_CORRELATIONS_NAN
MEAN_CORRELATION = UNDEFINED_ALL_OFFICIAL_SINGLE_STOCK_CORRELATIONS_NAN
MAX_CORRELATION = UNDEFINED_ALL_OFFICIAL_SINGLE_STOCK_CORRELATIONS_NAN
```

The official correlation statistic groups by datetime; a single-stock fixture
has one observation in each group, so all official per-date correlations are
undefined. This does not replace or relax the official value gate.

## Evidence and safety

Private evidence is retained at:

```text
D:/AQ_DATA/P3/deepseek-alpha053-one-code-100-single-stock-benchmark-001
```

```text
SUMMARY_SHA256 = ca73efc3c9c310101079dd9eccb9b5273b3dd5de1bef086e3df1426826308fc3
CHECKSUMS_SHA256 = 53ca90c1a0ac06ad07998fd16c621e38a7d3a8ab52c3f27b9939d77aa590a584
NEW_PRODUCTION_LOC = 0
FIN_QUANT_EXECUTED = NO
REAL_CANDIDATE_CREATED = 0
MODEL_TRAINING = NO
NEW_RESEARCH_PREDICTION = NO
BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
P4_MODIFIED = NO
P7_MODIFIED = NO
```

## Decision

The benchmark result does not admit DeepSeek Flash to autonomous Factor Coder
use. It also does not reactivate any superseded semantic-audit, Qlib-replacement,
73-stock blocker, or 100-independent-generation task.

```text
DEEPSEEK_GENERATIVE_RUNTIME = NOT_ADMITTED_BY_ONE_CODE_100_SINGLE_STOCK_BENCHMARK
FIN_QUANT_NEXT_TASK_AUTHORIZED = NO
CURRENT_DEVELOPMENT_NEXT = P3_DEEPSEEK_FACTOR_CODER_ROUTE_DECISION_001
FINAL_CLASSIFICATION = FAIL_DEEPSEEK_ONE_CODE_100_SINGLE_STOCK_OFFICIAL_BENCHMARK_0_OF_100
```
