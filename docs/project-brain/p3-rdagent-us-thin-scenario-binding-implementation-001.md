# P3 RD-Agent US Thin Scenario Binding Implementation 001

Status: **COMPLETE — LEVEL-1 PASS**

Completion date: 2026-09-14

This task implemented the frozen minimum class-seam design for the pinned
Microsoft RD-Agent. The project owns only template selection, fixed template
hashes, workspace rebinding, and the private US factor-source precondition.
RD-Agent continues to own conversion, experiment types, runners, coders,
scenarios, prompts, trace behavior, and loops.

## 1. Pinned authority

```text
RD_AGENT_VERSION = 0.8.1.dev37
RD_AGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
RD_AGENT_SOURCE_WORKTREE_CLEAN = YES
QLIB_SOURCE_WORKTREE_CLEAN = YES
```

## 2. Exact implementation

```text
BINDING_MODULE = 30-research-system/rd-agent/binding/aq_rdagent_us_binding/__init__.py
PROJECT_BINDING_MODULE_COUNT = 1
PROJECT_TEMPLATE_FILE_COUNT = 5
FACTOR_BINDING_CLASS = aq_rdagent_us_binding.USQlibFactorHypothesis2Experiment
MODEL_BINDING_CLASS = aq_rdagent_us_binding.USQlibModelHypothesis2Experiment
FACTOR_SCENARIO_CLASS = aq_rdagent_us_binding.USQlibFactorScenario
QUANT_SCENARIO_CLASS = aq_rdagent_us_binding.USQlibQuantScenario
```

Both converter subclasses call the pinned upstream `convert_response` first
and return the same upstream experiment object. The factor binding changes
only the new current primary and new empty baseline workspaces. The model
binding changes only its new primary workspace. Completed prior experiments,
workspaces, results, tasks, feedback, code, and object identity are preserved.
An incomplete prior experiment fails closed unless its existing workspace
already proves the appropriate approved US template family.

The two Scenario subclasses run the source precondition before upstream
construction and then call `super().__init__()` unchanged. They do not
override any description, prompt, simulator, interface, output, or runtime
environment behavior.

## 3. Frozen template family

```text
factor_template/conf_baseline.yaml = 5b679eaefcf8f552c765fb21f94e4c44f34fe2f680c17f84690473683c5c843d
factor_template/conf_combined_factors.yaml = c2f24f30170eb32e4cfeb916a11eba9fe726143e97c73ca93a6ac70af32cc9c6
factor_template/conf_combined_factors_sota_model.yaml = 0f1b2c8662b5d6619d293c07d91c75df688b5c7ca048f504bbc4e67b38beb7cc
model_template/conf_baseline_factors_model.yaml = 739a2c0b97383241c90ed24f56b106ab24bff9f20466b6411dff3156921a70b9
model_template/conf_sota_factors_model.yaml = a5f7bc6b11900e53514dc93f10d8b393fe9ef0801c4bb0f0f99fa089259b48ec
ACTIVE_CHINA_EXECUTION_DEFAULTS = 0
TEMPLATE_HASH_GUARD = PASS
```

The five files retain the pinned upstream Jinja, `NestedDataLoader`,
`StaticDataLoader`, `combined_factors_df.parquet`, `GeneralPTNN`, `model.py`,
dataset-class, time-series, LightGBM, and record structures required by the
unchanged runners. Project substitutions are limited to the approved US
provider, `region=us`, `market=p2_pit`, 2015-2024 research dates, no feature
`Fillna`, the approved label/cost behavior, SQLite MLflow, and the SPY
research-only structural placeholder.

## 4. Process-local settings and upstream ownership

All six official class settings resolved to the four project classes. Factor,
model, and quant dates resolved to the approved segments. The effective runner,
coder, hypothesis-generator, summarizer, and loop surfaces remain the pinned
RD-Agent implementations.

```text
RUNNER_OVERRIDE_REQUIRED = NO
CODER_OVERRIDE_REQUIRED = NO
RD_LOOP_OVERRIDE_REQUIRED = NO
PROMPT_OVERRIDE_REQUIRED = NO
UPSTREAM_RUNNER_TEMPLATE_SELECTION_COMPATIBLE = PASS
UPSTREAM_LOGIC_COPIED = NO
AQ_CUSTOM_RUNNER_COUNT = 0
AQ_CUSTOM_CODER_COUNT = 0
AQ_CUSTOM_RD_LOOP_COUNT = 0
AQ_CUSTOM_RESEARCH_ENGINE_COUNT = 0
AQ_CUSTOM_DATA_ENGINE_COUNT = 0
AQ_CUSTOM_RECORDER_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## 5. Factor-source guard

The guard accepts no caller-provided path. It verifies the process-selected
native Factor CoSTEER paths resolve exactly to:

```text
FULL = /mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source/full
DEBUG = /mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source/debug
```

It validates the immutable materialization report, exact file hashes, HDF key
`data`, exact six-column schema, `datetime/instrument` index, uniqueness, and
maximum date 2024-12-31. The full/debug source passed. A patched upstream
generator configured to raise was never called while both factor and quant
Scenario constructors and `get_data_folder_intro()` succeeded.

```text
FACTOR_SOURCE_GUARD = PASS
QUANT_SOURCE_GUARD = PASS
RDAGENT_US_FACTOR_SOURCE_DISCOVERY = PASS
CHINA_GENERATOR_EXECUTED = NO
RUNTIME_NETWORK_DATA_PATH = NONE
RUNTIME_FACTOR_REBUILD = NO
SEALED_OOS_ISOLATION = PASS
P2_PROVIDER_MUTATED = NO
```

## 6. Level-1 validation

Focused tests ran against the pinned installed RD-Agent runtime:

```text
LEVEL1_TESTS = 12/12 PASS
FACTOR_PRIMARY_WORKSPACE_BINDING = PASS
FACTOR_BASELINE_WORKSPACE_BINDING = PASS
MODEL_PRIMARY_WORKSPACE_BINDING = PASS
PRIOR_COMPLETED_TRACE_PRESERVED = PASS
INCOMPLETE_UNSAFE_TRACE_FAIL_CLOSED = PASS
```

Tests rendered all five Jinja templates with strict undefined variables,
parsed the rendered YAML, verified all five unchanged runner-selected names,
proved hash tampering and wrong source paths fail closed, and exercised the
real upstream conversion methods without executing a runner.

## 7. Non-actions and next state

```text
RD_AGENT_US_THIN_BINDING = PASS
REAL_RDAGENT_US_TEMPLATE_PATH = PROVEN_WITHOUT_AUTONOMOUS_EXECUTION
P3_DVC_STAGE_ACTIVATION = READY_NEXT
P2_PROVIDER_MUTATED = NO
DVC_CHANGED = NO
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
LLM_CALLS = 0
MODEL_TRAINING = NO
MODEL_FIT_CALLS = 0
NEW_PREDICTIONS = NO
BACKTEST = NO
PERFORMANCE_METRICS_CREATED = NO
MARKET_DATA_NETWORK_CALLS = 0
DATASET_DOWNLOADS = 0
BROKER_CALLS = 0
PAPER_TRADING = NO
LIVE_TRADING = NO
REMAINING_RESIDUAL_GAPS = NONE
CURRENT_NEXT = P3_DVC_STAGE_ACTIVATION_001
```
