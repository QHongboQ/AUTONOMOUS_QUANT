# P3 RD-Agent US Thin Scenario Binding Design 001

Status: **COMPLETE — IMPLEMENTED AND LEVEL-1 VERIFIED**

Design date: 2026-09-14

This document originally defined the minimum project-owned binding that lets the pinned
Microsoft RD-Agent `fin_factor`, `fin_model`, and `fin_quant` applications use
the approved US ragged Qlib configuration family. The design is now implemented
and Level-1 verified. No autonomous loop, training, prediction, backtest,
provider call, or DVC stage was run.

## 1. Authority and decision

```text
RD_AGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
RD_AGENT_VERSION = 0.8.1.dev37
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
PREFERRED_BINDING_STRATEGY = HYPOTHESIS2EXPERIMENT_SUBCLASS_BINDING
PROJECT_BINDING_MODULE_COUNT = 1
PROJECT_TEMPLATE_FILE_COUNT = 5
RUNNER_OVERRIDE_REQUIRED = NO
CODER_OVERRIDE_REQUIRED = NO
RD_LOOP_OVERRIDE_REQUIRED = NO
PROMPT_OVERRIDE_REQUIRED = NO
FACTOR_SOURCE_DATA_PATH = THIN_BINDING_REQUIRED
UPSTREAM_LOGIC_COPIED = NO
THIN_BINDING_DESIGN = READY_FOR_IMPLEMENTATION
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_RDAGENT_US_THIN_SCENARIO_BINDING_IMPLEMENTATION_001
```

The block above is the frozen design decision. Current completion state is:

```text
RD_AGENT_US_THIN_BINDING = PASS
REAL_RDAGENT_US_TEMPLATE_PATH = PROVEN_WITHOUT_AUTONOMOUS_EXECUTION
P3_DVC_STAGE_ACTIVATION = READY_NEXT
CURRENT_NEXT = P3_DVC_STAGE_ACTIVATION_001
```

RD-Agent remains the autonomous research owner. The project binding owns only
the choice of an approved template directory, four official class-setting
values, exact template-file validation, and fail-closed US data-path
preconditions. It does not implement a scenario, runner, coder, loop, data
engine, research engine, registry, recorder, or experiment database.

## 2. Official class-setting seam

Pinned
[`rdagent/app/qlib_rd_loop/conf.py`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/app/qlib_rd_loop/conf.py)
declares these settings and Pydantic prefixes:

| Application path | Field | Exact environment name |
|---|---|---|
| `fin_factor` | `FactorBasePropSetting.hypothesis2experiment` | `QLIB_FACTOR_HYPOTHESIS2EXPERIMENT` |
| `fin_model` | `ModelBasePropSetting.hypothesis2experiment` | `QLIB_MODEL_HYPOTHESIS2EXPERIMENT` |
| `fin_quant` factor branch | `QuantBasePropSetting.factor_hypothesis2experiment` | `QLIB_QUANT_FACTOR_HYPOTHESIS2EXPERIMENT` |
| `fin_quant` model branch | `QuantBasePropSetting.model_hypothesis2experiment` | `QLIB_QUANT_MODEL_HYPOTHESIS2EXPERIMENT` |
| `fin_factor` source-data guard | `FactorBasePropSetting.scen` | `QLIB_FACTOR_SCEN` |
| `fin_quant` source-data guard | `QuantBasePropSetting.scen` | `QLIB_QUANT_SCEN` |

A process-local settings probe at the pinned runtime confirmed all four exact
names. The same settings classes expose runner fields, but runner replacement
is unnecessary because the upstream runners already own correct branch
selection, factor combination, model injection, execution, and result
handling.

Future process-local binding:

```text
PYTHONPATH=/mnt/d/AUTONOMOUS_QUANT/30-research-system/rd-agent/binding:<existing process PYTHONPATH>
QLIB_FACTOR_HYPOTHESIS2EXPERIMENT=aq_rdagent_us_binding.USQlibFactorHypothesis2Experiment
QLIB_MODEL_HYPOTHESIS2EXPERIMENT=aq_rdagent_us_binding.USQlibModelHypothesis2Experiment
QLIB_QUANT_FACTOR_HYPOTHESIS2EXPERIMENT=aq_rdagent_us_binding.USQlibFactorHypothesis2Experiment
QLIB_QUANT_MODEL_HYPOTHESIS2EXPERIMENT=aq_rdagent_us_binding.USQlibModelHypothesis2Experiment
QLIB_FACTOR_SCEN=aq_rdagent_us_binding.USQlibFactorScenario
QLIB_QUANT_SCEN=aq_rdagent_us_binding.USQlibQuantScenario
```

The factor/model date settings must remain explicitly aligned with the
approved US YAML segments. In particular, the unchanged quant path reuses the
factor/model runners, and those runners instantiate `FactorBasePropSetting`
and `ModelBasePropSetting`; the launcher must therefore set the corresponding
`QLIB_FACTOR_*` and `QLIB_MODEL_*` dates for `fin_quant` as well. This is
configuration, not a new class override.

## 3. Binding-strategy comparison

| Candidate | Required project ownership | Upstream logic copied | Decision |
|---|---|---:|---|
| `HYPOTHESIS2EXPERIMENT_SUBCLASS_BINDING` | call upstream conversion, then rebind only newly constructed workspaces | no | **selected** |
| `EXPERIMENT_SUBCLASS_BINDING` | make existing converters construct project experiment types, requiring converter replacement or copied `convert_response` construction logic | yes or equivalent reimplementation | rejected |
| `RUNNER_WRAPPER_BINDING` | intercept execution to repair workspace selection, while wrapping a runner that already owns branch selection and execution | avoidable execution-boundary ownership | rejected |

The selected design subclasses only
[`QlibFactorHypothesis2Experiment`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/proposal/factor_proposal.py)
and
[`QlibModelHypothesis2Experiment`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/proposal/model_proposal.py).
Each override calls `super().convert_response(...)`, receives the same
upstream-created experiment object, applies the bounded workspace binding,
and returns that object. No response parsing, task construction, duplicate
factor filtering, trace selection, or experiment construction is copied.

## 4. Exact post-conversion rebinding semantics

### Factor converter

Pinned upstream conversion creates:

1. the current primary `QlibFactorExperiment`;
2. one new empty baseline `QlibFactorExperiment` at
   `based_experiments[0]`; and
3. zero or more accepted prior experiment objects taken directly from
   `trace.hist`.

The project subclass must replace the `experiment_workspace` only on items 1
and 2 with an unchanged upstream `QlibFBWorkspace` initialized from the
project `factor_template` directory. It must not replace a prior trace
experiment workspace or mutate its code, files, result, or artifact identity.

### Model converter

Pinned upstream conversion creates only the current primary
`QlibModelExperiment`; all `based_experiments` are references selected from
`trace.hist`. The project subclass must rebind only the primary workspace and
must not rebind any prior model or factor experiment.

### `fin_quant`

`QuantRDLoop` selects the same configured factor and model converter classes.
The two project subclasses therefore cover both quant branches without a
quant-specific converter, experiment, or runner.

### Fail-closed rules

The binding must validate workspace contents against the exact approved
template inventory/hashes before returning. It must stop if:

- the current primary workspace retains a default-China template;
- the newly constructed factor baseline retains a default-China template;
- an upstream runner-selected filename is absent or outside the approved
  project template directory;
- an unexpected newly constructed current experiment workspace appears; or
- a prior, incomplete (`result is None`) trace experiment could be executed
  but its workspace cannot be proven to contain the approved US family.

A completed prior trace experiment is preserved and not rewritten. These
checks prevent a resumed loop from silently executing an old China workspace
without destroying completed trace artifacts.

## 5. Five-file US template family

Target layout:

```text
30-research-system/rd-agent/templates/p3-us-ragged/
  factor_template/
    conf_baseline.yaml
    conf_combined_factors.yaml
    conf_combined_factors_sota_model.yaml
  model_template/
    conf_baseline_factors_model.yaml
    conf_sota_factors_model.yaml
```

All files retain these approved US substitutions:

```text
provider_uri = /mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data
region = us
market = p2_pit
feature Fillna processor = absent
learn DropnaLabel processor = retained
research dates = within 2015-01-02 through 2024-12-31
MLflow URI = sqlite:////mnt/d/AQ_DATA/P3/rdagent-us-ragged/mlflow.db
benchmark = SPY, structural research placeholder only
```

The existing approved sources are:

```text
FACTOR_BASELINE_SOURCE = 30-research-system/rd-agent/config/p3-us-ragged-factor.yaml
FACTOR_BASELINE_SOURCE_SHA256 = 7a5fa872aedc6820c5c1c8947fab8c2ac433f4d1a5f00eb2fab14656c2813b60
MODEL_BASELINE_SOURCE = 30-research-system/rd-agent/config/p3-us-ragged-model.yaml
MODEL_BASELINE_SOURCE_SHA256 = a7abc5cba54eb2f8bb6b7a5b703cfe63fa43450b22bc732db79f82bf86717296
```

Per-file derivation and retained semantics:

| Project file | Pinned upstream structural source | Approved US source | Required retained structure |
|---|---|---|---|
| `factor_template/conf_baseline.yaml` | `factor_template/conf_baseline.yaml` | factor baseline | `NestedDataLoader`/`Alpha158DL`, Jinja factor expressions/names, `LGBModel`, native records |
| `factor_template/conf_combined_factors.yaml` | `factor_template/conf_combined_factors.yaml` | factor baseline policy | `NestedDataLoader` plus `StaticDataLoader` reading `combined_factors_df.parquet`, feature combination, `LGBModel` |
| `factor_template/conf_combined_factors_sota_model.yaml` | `factor_template/conf_combined_factors_sota_model.yaml` | factor and model baseline policy | static combined factors, injected `model.py`, `GeneralPTNN`, `dataset_cls`, `num_features`, time-series variables |
| `model_template/conf_baseline_factors_model.yaml` | `model_template/conf_baseline_factors_model.yaml` | model baseline | injected `model.py`, `GeneralPTNN`, baseline `Alpha158DL`, dataset/model Jinja variables |
| `model_template/conf_sota_factors_model.yaml` | `model_template/conf_sota_factors_model.yaml` | model baseline policy | `combined_factors_df.parquet` `StaticDataLoader`, injected `model.py`, `GeneralPTNN`, dataset/model Jinja variables |

The two upstream SOTA/combined-model templates are byte-identical at the
pinned SHA, but both filenames must still exist because different unchanged
runners select them. No other pair has been proven semantically identical;
no branch may be reduced by aliasing away its required name.

Qlib owns YAML rendering, datasets, loaders, models, records, and execution.
RD-Agent owns factor combination, `combined_factors_df.parquet`, `model.py`,
runner selection, trace, feedback, and loop behavior.

## 6. Importable component location

The existing `30-research-system/rd-agent/` owner is not itself a valid dotted
Python package name and has no package root suitable for this component. The
minimum location is:

```text
30-research-system/rd-agent/binding/
  aq_rdagent_us_binding/
    __init__.py
```

Only the `binding` parent is added process-locally to `PYTHONPATH`. No editable
install, `pyproject.toml`, wheel, registry, or generic plugin framework is
needed. The two class strings are:

```text
aq_rdagent_us_binding.USQlibFactorHypothesis2Experiment
aq_rdagent_us_binding.USQlibModelHypothesis2Experiment
```

The module derives the adjacent template paths from its own resolved file
location and accepts no arbitrary template routing. It also contains the two
minimal source-data guard Scenario subclasses described in Section 8. Those
classes change no prompt or Scenario description logic.

## 7. CSI300 prompt-context audit

The only CSI300 strings in pinned
[`experiment/prompts.yaml`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/experiment/prompts.yaml)
are in `qlib_factor_experiment_setting` and
`qlib_model_experiment_setting`.

| Occurrence/path | Actual consumer trace | Classification |
|---|---|---|
| factor experiment setting | stored as `QlibFactorScenario._experiment_setting`; read by `experiment_setting` | `UI_ONLY` |
| model experiment setting | stored as `QlibModelScenario._experiment_setting`; read by `experiment_setting` | `UI_ONLY` |
| quant experiment setting | reuses factor experiment-setting text; read by `experiment_setting` | `UI_ONLY` |

Repository-wide use of `experiment_setting` is limited to the logging/UI
storage and rendering path. The real factor/model/quant proposal and feedback
paths pass `Scenario.get_scenario_all_desc(...)`; the pinned factor, model,
and quant implementations of that method do not include
`experiment_setting` or `rich_style_description`. Coding/evaluation context
likewise consumes the scenario description, source-data description,
interface, output, and simulator text—not the CSI300 table.

```text
PROMPT_CSI300_EXECUTION_RELEVANCE = UI_ONLY_NOT_CONSUMED_BY_SELECTED_AUTONOMOUS_EXECUTION_PROMPTS
PROMPT_OVERRIDE_REQUIRED = NO
PROMPT_OVERRIDE_MECHANISM = NONE
```

`RD_AGENT_SETTINGS.app_tpl` is therefore not used. Adding prompt overrides
would create unnecessary ownership and drift.

## 8. Factor source-data path

The real factor and quant scenario constructors call
[`get_data_folder_intro()`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/experiment/utils.py).
At the audited runtime both default directories are absent. If either is
absent, pinned upstream calls `generate_data_folder_from_qlib()`, whose
`factor_data_template/generate.py` initializes
`~/.qlib/qlib_data/cn_data`. That fallback also selects `QTDockerEnv` and is
not an acceptable US autonomous path.

RD-Agent provides the data-folder configuration seam through
`FactorCoSTEERSettings` (`env_prefix="FACTOR_CoSTEER_"`). A process-local
probe confirmed these exact effective environment names:

```text
FACTOR_COSTEER_DATA_FOLDER=/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source/full
FACTOR_COSTEER_DATA_FOLDER_DEBUG=/mnt/d/AQ_DATA/P3/rdagent-us-ragged/factor-source/debug
```

Before any factor/quant Scenario is imported or constructed, a future bounded
implementation task must materialize those private, non-Git directories from
the already approved US Qlib provider using Qlib's public data API. Each must
contain the upstream-native contract:

```text
daily_pv.h5, HDF key = data
README.md
columns = $open, $close, $high, $low, $volume, $factor
index = date-valid US instrument/session observations
```

The full folder covers the approved research range; the debug folder is a
deterministic bounded subset of the same US source. Their source identity,
selection rule, row bounds, and hashes must be recorded privately. This is a
one-time private input materialization and native settings binding, not a
production data adapter.

Native folder configuration alone is not fail-closed: `RDLoop.__init__`
instantiates the configured Scenario before it imports the configured
hypothesis-to-experiment converter, and the upstream Scenario constructor
calls `get_data_folder_intro()`. A converter-side guard would therefore run
too late.

The same single binding module must consequently provide
`USQlibFactorScenario(QlibFactorScenario)` and
`USQlibQuantScenario(QlibQuantScenario)`. Each override performs only the
source-data contract/provenance check and then calls `super().__init__()`.
The official `QLIB_FACTOR_SCEN` and `QLIB_QUANT_SCEN` settings select them.
No Scenario text, prompt, runtime-environment method, or description method is
reimplemented. `fin_model` retains the unmodified upstream model Scenario
because it does not invoke the factor source-data path.

The guard must fail before `super().__init__()` unless both directories and
both files exist, the HDF key/schema/provider provenance validate, and no
China source/default is active. It must never permit the upstream automatic
generator to run. Generated factor code continues to execute through
unchanged `FactorFBWorkspace`, which links these configured folders into its
run-scoped workspace.

```text
FACTOR_SOURCE_DATA_PATH = THIN_BINDING_REQUIRED
CHINA_ONLY_GENERATOR_SELECTED_WITH_CURRENT_DEFAULTS = YES
UPSTREAM_SUPPORTED_ALTERNATIVE = NATIVE_FACTOR_DATA_FOLDER_SETTINGS_PLUS_OFFICIAL_SCEN_CLASS_SEAM_GUARD
DATA_ADAPTER_REQUIRED = NO
```

This closes the design question without authorizing data creation in this
task.

## 9. Frozen validation design

### Level 1 — no LLM and no training

The implementation task must prove:

1. all four converter settings and two Scenario settings import the project
   classes;
2. `super().convert_response(...)` still creates upstream experiment types;
3. factor primary and its newly created empty baseline receive the approved
   factor workspace;
4. model primary receives the approved model workspace;
5. completed prior trace experiments retain object/workspace/artifact
   identity;
6. all five runner-selected names exist and match approved content hashes;
7. an unknown/missing name, wrong folder, wrong hash, or current China
   provider/region/market fails closed;
8. both configured factor source-data folders pass their schema/provenance
   checks before Scenario construction;
9. with a deliberately missing folder, the guard stops before
   `generate_data_folder_from_qlib()` or Docker can be selected; and
10. no LLM, qrun, model fit, prediction, backtest, provider network call, or
    dataset download occurs.

### Level 2 — separately authorized autonomous smoke

Deferred. A later authorization may prove one bounded real RD-Agent loop flows
through the project converter, the US template family, unchanged Qlib
execution, Recorder, and MLflow. This design task does not authorize it.

## 10. Exact implementation budget

| Future project file | Why it exists | Upstream behavior delegated |
|---|---|---|
| `30-research-system/rd-agent/binding/aq_rdagent_us_binding/__init__.py` | two converter subclasses, two source-data guard Scenario subclasses, and one shared exact-folder/content/source-data preflight helper | upstream conversion, Scenario descriptions, experiments, workspaces, runners, coders, loop |
| `30-research-system/rd-agent/templates/p3-us-ragged/factor_template/conf_baseline.yaml` | US baseline runner branch | Qlib baseline workflow |
| `30-research-system/rd-agent/templates/p3-us-ragged/factor_template/conf_combined_factors.yaml` | US combined-factor runner branch | RD-Agent combination and Qlib static loader |
| `30-research-system/rd-agent/templates/p3-us-ragged/factor_template/conf_combined_factors_sota_model.yaml` | US combined-factor/SOTA-model branch | RD-Agent model injection and Qlib GeneralPTNN |
| `30-research-system/rd-agent/templates/p3-us-ragged/model_template/conf_baseline_factors_model.yaml` | US baseline-factor/model branch | RD-Agent model coding and Qlib GeneralPTNN |
| `30-research-system/rd-agent/templates/p3-us-ragged/model_template/conf_sota_factors_model.yaml` | US SOTA-factor/model branch | RD-Agent factor selection and Qlib static loader/model |
| `30-research-system/rd-agent/binding/tests/test_us_binding.py` | focused no-LLM/no-training seam and fail-closed proofs | no upstream implementation copied |

```text
IMPLEMENTATION_FILE_COUNT = 7
PROJECT_BINDING_MODULE_COUNT = 1
PROJECT_TEMPLATE_FILE_COUNT = 5
PROJECT_TEST_FILE_COUNT = 1
RUNNER_WRAPPER_COUNT = 0
DATA_ENGINE_COUNT = 0
RESEARCH_ENGINE_COUNT = 0
WORKFLOW_ENGINE_COUNT = 0
REGISTRY_COUNT = 0
DATABASE_COUNT = 0
```

Private US factor source-data files and their evidence manifest are runtime
inputs outside Git and are not project implementation modules.

## 11. DVC ordering

```text
DVC = OUTER_DEPENDENCY_AND_ARTIFACT_OWNER
RD_AGENT = AUTONOMOUS_RESEARCH_OWNER
QLIB_AND_MLFLOW = RUN_TRACKING_OWNER
RUN_SCOPED_RDAGENT_WORKSPACE = LIKELY_FUTURE_DVC_OUTPUT_BOUNDARY
SHARED_MLFLOW_DB = NOT_DVC_OUTPUT
US_HISTORICAL_PROVIDER = DVC_DEPENDENCY_ONLY
P3_DVC_STAGE_ACTIVATION = READY_NEXT
```

No DVC file or stage changed.

## 12. Source-data contract proof update

The source-data proof found that the immutable P2 Qlib provider does not expose
`$factor`. The bounded follow-up resolved this without changing that provider:
one thin materializer reads OHLCV through Qlib's public API and joins only
exact, already-selected Quantiacs episode/asset/session observations to frozen
`split_cumprod`. SimFin-only and otherwise unproven factors remain NaN.

The resulting full/debug private `daily_pv.h5` inputs passed the official HDF
schema, pinned native reader, and `get_data_folder_intro()` path. A generator
throw-sentinel proved the China fallback was not selected. The factor-source
precondition is now satisfied; this document's minimum binding design may
proceed unchanged.

```text
QLIB_FACTOR_AVAILABLE_IN_IMMUTABLE_P2_PROVIDER = NO
QLIB_FACTOR_FIELD_PRESERVATION = PASS
CONSTANT_FACTOR_SEMANTICALLY_VALID = NO
SOURCE_DATA_MATERIALIZATION = THIN_CONFIGURED_QLIB_EXPORT
MATERIALIZER_IMPLEMENTATION = ONE_THIN_CONTRACT_MATERIALIZER
FACTOR_SOURCE_DATA_CONTRACT = READY_FOR_THIN_BINDING_IMPLEMENTATION
THIN_BINDING_DESIGN = IMPLEMENTED_LEVEL1_PASS
RD_AGENT_US_THIN_BINDING = PASS
P3_DVC_STAGE_ACTIVATION = READY_NEXT
CURRENT_NEXT = P3_DVC_STAGE_ACTIVATION_001
```

## 13. Design-task non-actions (historical)

```text
CODE_CHANGED = NO
NEW_CONFIG_FILES = 0
DVC_CHANGED = NO
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
LLM_CALLS = 0
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
MARKET_DATA_NETWORK_CALLS = 0
DATASET_DOWNLOADS = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```
