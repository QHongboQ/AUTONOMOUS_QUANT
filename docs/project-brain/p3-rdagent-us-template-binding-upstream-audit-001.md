# P3 RD-Agent US Template Binding Upstream Audit 001

Status: **COMPLETE — THIN SCENARIO BINDING REQUIRED**

Audit date: 2026-09-14

This audit determines how the existing project-owned US Qlib configurations
can enter the real Microsoft RD-Agent `fin_factor`, `fin_model`, and
`fin_quant` paths. It does not implement that binding and did not execute an
LLM loop, training, prediction, backtest, or DVC stage.

## 1. Decision

```text
RD_AGENT_US_TEMPLATE_BINDING = THIN_SCENARIO_BINDING_REQUIRED
OFFICIAL_TEMPLATE_OVERRIDE_AVAILABLE = NO
OFFICIAL_UPGRADE_TEMPLATE_OVERRIDE_AVAILABLE = NO
THIN_SCENARIO_BINDING_FEASIBLE = YES
P3_DVC_STAGE_ACTIVATION = DEFERRED_UNTIL_RDAGENT_US_TEMPLATE_BINDING
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_RDAGENT_US_THIN_SCENARIO_BINDING_DESIGN_001
```

The pinned and current official finance scenario has no direct CLI,
environment, settings, or workspace option for a factor template directory,
model template directory, or individual Qlib YAML path. It does expose
importable scenario-component class settings. A project-owned binding-only
component can use those hooks to replace only the `QlibFBWorkspace` template
folder/config selection, while delegating all research, coding, execution,
recording, and feedback behavior to upstream classes.

This is not permission to patch RD-Agent or to create an AQ research engine.

## 2. Exact pinned execution path

Audited source:

```text
RD_AGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
RD_AGENT_VERSION = 0.8.1.dev37
SOURCE_WORKTREE_CLEAN = YES
```

### 2.1 Application and loop construction

The [Typer CLI at the pinned SHA](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/app/cli.py)
routes `fin_factor`, `fin_model`, and `fin_quant` to their finance application
`main()` functions. Their public CLI options cover session path, step/loop
limits, duration, and checkout. No option is a Qlib YAML or template-folder
path. `path` is a saved RD-Agent session/checkpoint path, not a configuration
file.

Each application constructs its RD loop from the corresponding
`FACTOR_PROP_SETTING`, `MODEL_PROP_SETTING`, or `QUANT_PROP_SETTING`.
[`RDLoop.__init__`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/components/workflow/rd_loop.py)
uses importable class names from those settings for the scenario,
hypothesis-to-experiment converter, coder, runner, and summarizer. `QuantRDLoop`
uses separate configurable factor and model converters, coders, runners, and
summarizers.

### 2.2 Experiment and workspace binding

The template folders are selected in experiment constructors, not by the CLI:

| Path | Pinned selection |
|---|---|
| `fin_factor` | [`QlibFactorExperiment`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/experiment/factor_experiment.py) constructs `QlibFBWorkspace(Path(__file__).parent / "factor_template")` |
| `fin_model` | [`QlibModelExperiment`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/experiment/model_experiment.py) constructs `QlibFBWorkspace(Path(__file__).parent / "model_template")` |
| `fin_quant` | its [local factor and model experiment classes](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/experiment/quant_experiment.py) make the same two hard-coded selections |

[`QlibFBWorkspace`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/experiment/workspace.py)
then injects every file from the selected folder into the run-scoped workspace.
Its `execute()` method invokes unchanged `QlibCondaEnv`/`QlibFBWorkspace`
behavior and runs `qrun <selected-name>` inside that workspace.

### 2.3 Runner config-name selection

The file name is selected by the unchanged upstream runners:

| Runner condition | Selected YAML |
|---|---|
| factor baseline without materialized generated factors | `conf_baseline.yaml` |
| factor run with combined generated/base factors | `conf_combined_factors.yaml` |
| factor run with combined factors and retained SOTA model | `conf_combined_factors_sota_model.yaml` |
| model run without retained SOTA factors | `conf_baseline_factors_model.yaml` |
| model run with retained SOTA factors | `conf_sota_factors_model.yaml` |

The selections are literal in the pinned
[`QlibFactorRunner`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/developer/factor_runner.py)
and
[`QlibModelRunner`](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/scenarios/qlib/developer/model_runner.py).
`fin_quant` reuses these same runner classes, so it does not introduce a third
template-selection mechanism.

```text
PINNED_FACTOR_TEMPLATE_BINDING = EXPERIMENT_HARDCODED_FOLDER_PLUS_RUNNER_SELECTED_3_FILE_VARIANTS
PINNED_MODEL_TEMPLATE_BINDING = EXPERIMENT_HARDCODED_FOLDER_PLUS_RUNNER_SELECTED_2_FILE_VARIANTS
PINNED_QUANT_TEMPLATE_BINDING = REUSES_HARDCODED_FACTOR_AND_MODEL_EXPERIMENT_FOLDERS_AND_RUNNERS
```

## 3. Existing official configuration surface

The [finance settings classes](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/rdagent/app/qlib_rd_loop/conf.py)
officially expose importable component-class names and date settings under
`QLIB_FACTOR_`, `QLIB_MODEL_`, and `QLIB_QUANT_` environment prefixes.
This is sufficient to select a thin project component, but no field is a Qlib
template folder or YAML path.

| Surface | What it can configure | Template override result |
|---|---|---|
| CLI arguments | session/checkpoint, loop/step/duration, checkout | none |
| finance settings/environment | scenario, converter, coder, runner, summarizer classes; date segments | indirect class-extension seam only |
| `scen` class setting | prompt/context scenario object | does not select `QlibFBWorkspace` template files |
| `base_features_path` in application `main()` | base factor expressions and code | does not select a Qlib YAML |
| `RD_AGENT_SETTINGS.app_tpl` | lookup precedence for `T(...)` prompt/text templates | does not affect `inject_code_from_folder()` or Qlib YAML folders |
| workspace API | `QlibFBWorkspace(template_folder_path=...)` constructor | usable by a thin component, but not exposed directly by finance CLI/settings |
| data-science custom-data scenario | custom data-science task surface | separate scenario; not a finance Qlib-template override |

The [official finance documentation](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/docs/scens/quant_agent_fin.rst)
describes the YAMLs inside the package template directories and documents
their fields. The
[installation/configuration guide](https://github.com/microsoft/RD-Agent/blob/32b3d395e73d9db5eee3fe9063d69aec0fdc83bd/docs/installation_and_configuration.rst)
documents date-segment environment variables. Neither documents an external
template-directory or individual-YAML override.

Important distinction:

```text
PROMPT_TEMPLATE_OVERRIDE != QLIB_WORKSPACE_TEMPLATE_OVERRIDE
SESSION_PATH != QLIB_CONFIG_PATH
BASE_FEATURES_PATH != QLIB_CONFIG_PATH
```

## 4. Current official upstream and history

At audit time, official `microsoft/RD-Agent` `main` resolves to the same SHA as
the pinned source:

```text
OFFICIAL_CURRENT_MAIN = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
PINNED_SOURCE_EQUALS_OFFICIAL_CURRENT_MAIN = YES
LATEST_OFFICIAL_RELEASE = v0.8.0
LATEST_RELEASE_IS_NEWER_THAN_PINNED_SOURCE = NO
```

The current official experiment constructors and runner selections remain the
same hard-coded paths/names described above. The latest formal release predates
the pinned/current main and therefore cannot supply a newer hook.

The strongest public issue evidence is
[`microsoft/RD-Agent#1283`](https://github.com/microsoft/RD-Agent/issues/1283).
The open question asks how to specify custom Qlib data/factors; a repository
contributor states that there is currently no finance-scenario
dataset interface and that different market/region/universe behavior requires
updating the corresponding YAML. That advice confirms the missing public hook;
it does not turn in-package YAML modification into an acceptable AQ ownership
model.

No merged or open official PR found by the targeted searches adds an external
finance template-folder or individual-Qlib-config option. Closed, unmerged
[`PR #1400`](https://github.com/microsoft/RD-Agent/pull/1400) directly changed
package runner code and in-package Qlib YAMLs; it is evidence of a source-patch
approach, not an official supported override.

```text
OFFICIAL_TEMPLATE_OVERRIDE_AVAILABLE = NO
OFFICIAL_UPGRADE_TEMPLATE_OVERRIDE_AVAILABLE = NO
```

## 5. Community evidence

| Evidence | Scope | Observed approach | Classification | Fitness for AQ |
|---|---|---|---|---|
| [`microsoft/RD-Agent#1224`](https://github.com/microsoft/RD-Agent/issues/1224) | US/custom Qlib data attempt | Uses the default Qlib config location and finance command; reports a `fin_quant` failure and does not prove external template selection | `OFFICIAL_CONFIGURATION_ONLY` | Diagnostic only; not a binding solution |
| [`franxyang/RD-Agent-ETF`](https://github.com/franxyang/RD-Agent-ETF) | ETF/custom provider/custom market | Carries a full RD-Agent tree and edits in-package `factor_template/*.yaml`, including a hard-coded provider path/market | `FORKED_RUNTIME` | Reject; duplicates/forks upstream and embeds machine-specific paths |
| [`microsoft/RD-Agent#1400`](https://github.com/microsoft/RD-Agent/pull/1400) | custom baseline/provider/market changes | Changes RD-Agent runners, utilities, and packaged factor/model YAMLs; PR closed without merge | `UPSTREAM_SOURCE_PATCH` | Reject; unmerged and broader than template binding |
| [`delon-xie/QuantByQlib`](https://github.com/delon-xie/QuantByQlib) | US/CN/HK/crypto and RD-Agent factors | Adds its own Docker/session manager, output parser, factor validation/persistence, injection, Qlib strategy, and data layer | `CUSTOM_RESEARCH_ENGINE` | Reject; replaces/duplicates the ownership this project assigns upstream |

No inspected community implementation demonstrated an
`OFFICIAL_CONFIGURATION_ONLY` external finance-template override. The evidence
supports a small project extension through existing component-class hooks,
not a fork, source patch, or new research engine.

## 6. Qlib boundary remains solved

The prior bounded proof already established that, when supplied the correct
US YAML, unchanged Qlib resolves the existing provider and date-valid market:

```text
QLIB_REGION = us
QLIB_MARKET = p2_pit
RAGGED_PANEL_SEMANTICS_PRESERVED = YES
SEALED_OOS_ISOLATION = PASS
QLIB_CUSTOM_RUNNER_REQUIRED = NO
QLIB_CUSTOM_DATA_ENGINE_REQUIRED = NO
```

The unresolved boundary is entirely RD-Agent's workspace-template selection.
No Qlib source, runner, data engine, or provider change is needed.

## 7. Thin scenario-binding feasibility

The official finance settings provide the import-class seam needed for a
binding-only project component:

- factor/model `hypothesis2experiment` classes can be selected through their
  prefixed settings;
- `fin_quant` separately exposes factor and model
  `hypothesis2experiment` class settings;
- a thin subclass can delegate conversion to `super()`, then replace only the
  experiment workspace with unchanged `QlibFBWorkspace` pointed at a
  project-owned template folder;
- the same binding must cover the returned experiment and any newly created
  baseline/based experiments;
- unchanged upstream coders and runners then keep selecting the five official
  config names and invoking unchanged `QlibFBWorkspace.execute()` and
  `QlibCondaEnv`.

A similarly thin runner wrapper is technically possible through the `runner`
class settings, but it is not preferred because the existing runner already
owns branch selection and execution. The design should leave that owner
unchanged and bind the workspace before runner execution.

This component would own only:

1. the project template-folder reference;
2. the explicit mapping from the two approved US baseline config sources to
   the upstream-required template family;
3. fail-closed checks that all runner-selected files are present and remain
   within the approved project folder.

It would not own hypothesis generation, coding, factor assembly, model
selection, training, Qlib execution, Recorder/MLflow, feedback, trace, or
loop control.

```text
THIN_SCENARIO_BINDING_FEASIBLE = YES
UPSTREAM_FEATURE_DUPLICATED = NO
RD_LOOP_REUSED = YES
HYPOTHESIS_GENERATION_REUSED = YES
CODER_REUSED = YES
FACTOR_MODEL_RUNNERS_REUSED = YES
QLIB_FB_WORKSPACE_REUSED = YES
QLIB_CONDA_ENV_REUSED = YES
QLIB_RECORDER_MLFLOW_REUSED = YES
```

## 8. Five-name completeness constraint

The existing approved files remain authoritative configuration sources:

```text
FACTOR_CONFIG = 30-research-system/rd-agent/config/p3-us-ragged-factor.yaml
FACTOR_CONFIG_SHA256 = 7a5fa872aedc6820c5c1c8947fab8c2ac433f4d1a5f00eb2fab14656c2813b60
MODEL_CONFIG = 30-research-system/rd-agent/config/p3-us-ragged-model.yaml
MODEL_CONFIG_SHA256 = a7abc5cba54eb2f8bb6b7a5b703cfe63fa43450b22bc732db79f82bf86717296
```

They prove the US baseline Qlib semantics, but their current filenames do not
match the five names selected by the real runners. More importantly, simple
file aliasing is not sufficient for every branch:

- the two combined-factor branches require upstream `StaticDataLoader`
  consumption of `combined_factors_df.parquet`;
- the SOTA-model branch requires the injected `model.py`/`GeneralPTNN` path;
- the baseline factor branch retains LGBM;
- the model branches retain baseline-versus-SOTA-factor distinctions.

The next design must therefore define a complete project-owned five-name
template family derived from the two approved US baselines and the structural
differences in the pinned upstream variants. It must not copy China provider,
market, fill, or date defaults. It must also fail closed if a runner requests
an unbound filename.

This is bounded configuration materialization, not a second runner or data
engine.

## 9. Future DVC architecture and ordering

```text
DVC = OUTER_PIPELINE_AND_ARTIFACT_DEPENDENCY_OWNER
RD_AGENT = AUTONOMOUS_RESEARCH_OWNER
QLIB_RECORDER_PLUS_MLFLOW = RUN_TRACKING_OWNER
RUN_SCOPED_WORKSPACE_DIRECTORY = FUTURE_DVC_OUTPUT_BOUNDARY
SHARED_MLFLOW_TRACKING_DB = NOT_A_DVC_OUTPUT
HISTORICAL_US_PROVIDER = DVC_DEPENDENCY_NEVER_P3_OUTPUT
P3_DVC_STAGE_ACTIVATION = DEFERRED_UNTIL_RDAGENT_US_TEMPLATE_BINDING
```

DVC activation must wait until the real loop has one unambiguous US template
binding. Otherwise DVC would freeze a path that the loop does not actually
consume.

## 10. Non-actions

```text
CODE_CHANGED = NO
DVC_CHANGED = NO
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
LLM_CALLS = 0
MODEL_TRAINING = NO
MODEL_FIT_CALLS = 0
NEW_PREDICTIONS = NO
BACKTEST = NO
MARKET_DATA_NETWORK_CALLS = 0
DATASET_DOWNLOADS = 0
BROKER_CALLS = 0
PAPER_TRADING = NO
LIVE_TRADING = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```
