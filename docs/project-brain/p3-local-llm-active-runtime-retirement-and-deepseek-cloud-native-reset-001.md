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

## Official single-stock evaluator oracle audit

The raw 0/100 result was not promoted to a DeepSeek capability verdict. A
no-LLM oracle audit reused the intact canary fixture and compared the exact
official alpha053 ground-truth implementation with the same exact implementation
through `FactorImplementEval.eval_case` and its unchanged evaluators.

Both workspaces produced a Series named `result`. Official `_get_df` converted
the ground-truth Series to column `gt_factor` and the source Series to column
`source_factor`. The official `gen_df.sub(gt_df)` then produced two label-aligned
columns containing no non-NaN differences. Consequently the identical oracle
received an equal-value ratio of zero. Each datetime group contained exactly
one instrument, so both Pearson and rank correlation were undefined.

```text
RDAGENT_PIN_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
UPSTREAM_CURRENT_HEAD_CHECKED = 484776c211e4fbbeef03e0ec00d6bbee7362a4f4
UPSTREAM_FIX_AVAILABLE = NO
ORACLE_IMPLEMENTATIONS_IDENTICAL = YES
ORACLE_IMPLEMENTATION_SHA256 = bf790dcc951ec6f5fca41b33cb1626610eadf35eaf7f9363c002d5851a30722d
ORACLE_SINGLE_COLUMN = TRUE
ORACLE_ROW_COUNT_RATIO = 1.0
ORACLE_INDEX_RATIO = 1.0
ORACLE_GT_COLUMNS = gt_factor
ORACLE_SOURCE_COLUMNS = source_factor
ORACLE_SUBTRACTION_RESULT_COLUMNS = gt_factor,source_factor
ORACLE_SUBTRACTION_NON_NAN_COUNT = 0
ORACLE_EQUAL_VALUE_RATIO = 0.0
ORACLE_DISTINCT_DATETIMES = 2516
ORACLE_INSTRUMENTS_PER_DATETIME_MIN_MEDIAN_MAX = 1,1,1
ORACLE_CORRELATION = NAN
ORACLE_PASS = NO
COLUMN_ALIGNMENT_EFFECT_CONFIRMED = YES
SINGLE_STOCK_CORRELATION_UNDEFINED_CONFIRMED = YES
```

Microsoft RD-Agent current upstream HEAD retained byte-identical relevant
evaluator files relative to the project pin, so no existing upstream fix was
available to adopt. No evaluator, factor engine, comparison rule, correlation
rule, or threshold was implemented in AQ.

## Official Factor Coder upstream contract resolution

The official path starts at `rdagent/app/benchmark/factor/eval.py`. It loads
`BenchmarkSettings`, converts RD2Bench JSON entries into `FactorTask` plus
ground-truth `FactorFBWorkspace` objects, constructs the configured Developer
(default `FactorCoSTEER`), and creates `FactorImplementEval`. For every benchmark
round, `develop()` passes a fresh experiment to the Developer; default
FactorCoSTEER performs its native generation and recovery. `eval()` then applies
the deterministic five-evaluator sequence and saves a factor-keyed result
object. `analysis.py` loads that object, calls `summarize_res()`, and aggregates
continuous reporting metrics through `BenchmarkAnalyzer.analyze_data()`.

```text
OFFICIAL_BENCHMARK_ENTRYPOINT = python rdagent/app/benchmark/factor/eval.py
OFFICIAL_ANALYSIS_ENTRYPOINT = python rdagent/app/benchmark/factor/analysis.py <log/path-to.pkl>
FACTOR_IMPLEMENT_EVAL_EVALUATORS = FactorSingleColumnEvaluator,FactorRowCountEvaluator,FactorIndexEvaluator,FactorEqualValueRatioEvaluator,FactorCorrelationEvaluator(hard_check=False)
FACTOR_IMPLEMENT_EVAL_NATIVE_BINARY_PASS_FAIL = NO
FACTOR_VALUE_EVALUATOR_USED_BY_FACTOR_IMPLEMENT_EVAL = NO
FACTOR_VALUE_EVALUATOR_USED_BY_DEFAULT_FACTORCOSTEER_DEVELOP = YES
OFFICIAL_BINARY_ADMISSION_POLICY_FOUND = NO
DEFAULT_BENCH_TEST_ROUND = 10
OFFICIAL_BENCH_ROUND_GENERATES_NEW_IMPLEMENTATION = YES
```

The official Qlib data generator initializes
`~/.qlib/qlib_data/cn_data`, uses `D.instruments()`, and requests `$open`,
`$close`, `$high`, `$low`, `$volume`, and `$factor`. Qlib's initial
instrument-first output is swapped and sorted to a date-first
`(datetime, instrument)` MultiIndex. Full data begins at 2008-12-29 with no
explicit end. Debug data covers 2018-01-01 through 2019-12-31 and retains the
first 100 unique instruments encountered in the sorted full date-major panel.
Both HDF outputs use key `data`.

```text
OFFICIAL_FACTOR_BENCHMARK_EXPECTS_MULTI_INSTRUMENT_PANEL = YES
OFFICIAL_INDEX_NAMES = datetime,instrument
OFFICIAL_INDEX_ORDER = DATETIME_THEN_INSTRUMENT_ASCENDING
OFFICIAL_DEBUG_INSTRUMENT_SELECTION_METHOD = FIRST_100_UNIQUE_INSTRUMENTS_FROM_FULL_DATE_MAJOR_PANEL
OFFICIAL_DEBUG_TARGET_INSTRUMENT_COUNT = 100
OFFICIAL_HDF_KEY = data
```

The generated-code prompt requires a one-column pandas DataFrame whose column
name is the factor name. The official alpha053 ground truth instead emits a
Series named `result`; the benchmark evaluator accepts either pandas shape and
normalizes Series internally. This label asymmetry explains why equal-value
accuracy is not a viable single-stock oracle, while the intended multi-stock
panel supplies the cross-section required by the official correlation metric.

`analysis.py` semantics are descriptive rather than admission rules:

```text
AVG_RUN_SR = FRACTION_WITHOUT_RUN_LEVEL_CODERERROR
AVG_FORMAT_SR = MEAN_OF_ROW_COUNT_RATIO_AND_INDEX_JACCARD_ACROSS_ROUNDS
AVG_CORRELATION = MEAN_CROSS_SECTIONAL_PEARSON_CORRELATION_ACROSS_ROUNDS_WITH_MISSING_AS_ZERO
MAX_CORRELATION = MAXIMUM_OF_THAT_CORRELATION_ACROSS_ROUNDS
MAX_ACCURACY = MAXIMUM_EQUAL_VALUE_RATIO_ACROSS_ROUNDS
AVG_ACCURACY = MEAN_FORMAT_WEIGHTED_EQUAL_VALUE_RATIO_ACROSS_ROUNDS
```

Current Microsoft RD-Agent HEAD
`484776c211e4fbbeef03e0ec00d6bbee7362a4f4` is five commits ahead of the
project pin, but none of the 16 relevant benchmark, evaluator, generator,
prompt, loader, configuration, or documentation files changed. Targeted search
found no matching Microsoft issue or PR. An upstream upgrade would therefore
not alter this contract.

```text
RELEVANT_FILE_DIFF_COUNT = 0
RELEVANT_BEHAVIOR_CHANGED = NO
UPSTREAM_FIX_AVAILABLE = NO
AQ_INTEGRATION_CLASSIFICATION = THIN_DATA_ADAPTER_ONLY
```

The next valid capability benchmark should use the official runner, official
RD2Bench alpha053, intended multi-instrument panel, unchanged
`FactorImplementEval`, and `BenchmarkAnalyzer`. It should preserve the official
default ten rounds, each of which invokes FactorCoSTEER development again. This
task did not run that benchmark.

## Evidence and safety

Private evidence is retained at:

```text
D:/AQ_DATA/P3/deepseek-alpha053-one-code-100-single-stock-benchmark-001
D:/AQ_DATA/P3/official-single-stock-evaluator-oracle-sanity-audit-001
D:/AQ_DATA/P3/official-factor-coder-evaluation-contract-upstream-resolution-001
```

```text
SUMMARY_SHA256 = ca73efc3c9c310101079dd9eccb9b5273b3dd5de1bef086e3df1426826308fc3
CHECKSUMS_SHA256 = 53ca90c1a0ac06ad07998fd16c621e38a7d3a8ab52c3f27b9939d77aa590a584
ORACLE_SUMMARY_SHA256 = 12a3a557bd649a60124acc393e7a0824920c74c2f2b86af5e9f295f5a86d6ecc
ORACLE_CHECKSUMS_SHA256 = 9624c86cceab6e97807466b72710713d69b4d6313a1de30989453a2b033ab3cb
UPSTREAM_CONTRACT_SHA256 = a5814b661fd9eaed8dc0f5e0fc1079406d73ce1c8ce33c4125761169b5669a14
UPSTREAM_CONTRACT_CHECKSUMS_SHA256 = 36efe16e5494745f5f601b8752fd2e0d5fe8da2ebef30489ef9fee9cc710c935
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

The raw benchmark result neither admits nor rejects DeepSeek Flash for
autonomous Factor Coder use. The upstream contract is now resolved, but
DeepSeek capability remains unresolved until the official multi-instrument,
multi-round path is executed. No superseded single-stock, Qlib-replacement,
73-stock blocker, or independent-generation path is reactivated.

```text
RAW_100_STOCK_RESULT = 0/100
PRIOR_0_OF_100_DEEPSEEK_CAPABILITY_VERDICT_VALID = NO
DEEPSEEK_FACTOR_CODER_CAPABILITY = UNRESOLVED
FIN_QUANT_NEXT_TASK_AUTHORIZED = NO
CURRENT_DEVELOPMENT_NEXT = P3_DEEPSEEK_OFFICIAL_MULTI_INSTRUMENT_RD2BENCH_10_ROUND_BENCHMARK_001
FINAL_CLASSIFICATION = PASS_OFFICIAL_FACTOR_CODER_UPSTREAM_CONTRACT_RESOLVED
```
