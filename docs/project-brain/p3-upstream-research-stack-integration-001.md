# P3 Upstream Research Stack Integration 001

Status: **COMPLETE — RD-AGENT RUNTIME ALIGNMENT PASS**

## Ownership preamble

```text
CAPABILITY = P3 autonomous quantitative research stack
UPSTREAM_OWNER = Microsoft RD-Agent / RD-Agent(Q); Microsoft Qlib; Qlib Recorder / MLflow; DVC
OWNERSHIP_MODE = RD-Agent: UPSTREAM_WHOLE; Qlib: UPSTREAM_WHOLE; MLflow via Qlib: UPSTREAM_WHOLE; DVC: UPSTREAM_LEAF
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = YES, THIN ONLY
AQ_ALLOWED_SCOPE = configuration; adapter; contract; policy; orchestration; health evidence; upgrade evidence
CUSTOM_ENGINE_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_TARGET = 0
```

The repository root contained no `AGENTS.md` at this baseline. The governing
Project Brain and upstream-ownership documents were read in the task-specified
order. This task did not install or upgrade any package and did not modify
RD-Agent or Qlib source.

## Authority and scope

```text
TASK = AUTONOMOUS-QUANT-P3-UPSTREAM-RESEARCH-STACK-INTEGRATION-001
BASE_MAIN = d6215b19df989b32aa1151d935a4ef6399424c08
BRANCH = agent/p3-upstream-research-stack-integration-001
P2 = COMPLETE
P2_CERTIFICATION = COMPLETE
FALSE_ALPHA_CONTROLS_OPERATIONAL = YES
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
SEALED_OOS_AVAILABLE = NO
```

This task inspected and connected only the direct P3 upstream stack. It did
not run an autonomous research loop, train a model, create predictions, run a
backtest, execute P2 Certification, fetch data, call an LLM, or contact a
broker.

## RD-Agent runtime and provenance

| Item | Observed state | Result |
|---|---|---|
| Source checkout | `/home/zhou/AQ_UPSTREAM/rd-agent` | present |
| Checkout SHA | `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` | exact |
| Checkout worktree | clean | PASS |
| Control environment | `/home/zhou/AQ_ENVS/rdagent` | present |
| Python | `3.11.16` | PASS |
| Installed distribution | `rdagent 0.8.0` | import PASS |
| CLI | `rdagent --help`; `fin_factor`, `fin_model`, and `fin_quant` exposed | PASS |
| Dependency health | `pip check`: no broken requirements; `pydantic-ai-slim 1.66.0` | PASS |
| Installed distribution provenance | wheel under the control environment, with no `direct_url.json` | BLOCKED_PROVENANCE |
| Checkout/runtime equality | installed Python tree differs from the clean checkout | NOT_PROVEN_EQUIVALENT |

The checkout SHA is therefore source evidence, not an asserted SHA for the
installed wheel. The installed runtime remains healthy, but activation must
fail closed until the runtime is bound to an auditable source/release identity.

There is a second exact mismatch. The installed `rdagent 0.8.0`
`QlibCondaEnv.prepare()` declares Qlib commit
`3e72593b8c985f01979bebcf646658002ac43b00`, while the already accepted
`rdagent4qlib` environment contains Qlib commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`. The clean checkout at
`32b3d395...` declares the latter commit, but it is not the package imported by
the control environment. No upgrade or repair was authorized here.

## RD-Agent native capability matrix

The matrix below is based on the installed runtime package, not inferred from
the newer checkout. Key evidence is in its `app/qlib_rd_loop`,
`components/workflow/rd_loop.py`, `utils/workflow/loop.py`,
`core/experiment.py`, and `utils/env.py` public implementation.

| Capability | Classification | Installed upstream evidence |
|---|---|---|
| Automated hypothesis generation | `NATIVE_AVAILABLE` | `RDLoop._propose`; factor/model/quant hypothesis generators |
| Factor proposal | `NATIVE_AVAILABLE` | `QlibFactorHypothesisGen` and `QlibFactorHypothesis2Experiment` |
| Factor implementation | `NATIVE_AVAILABLE` | factor CoSTEER coder and `QlibFactorRunner` wiring |
| Model proposal | `NATIVE_AVAILABLE` | `QlibModelHypothesisGen` and `QlibModelHypothesis2Experiment` |
| Model implementation | `NATIVE_AVAILABLE` | model CoSTEER coder and `QlibModelRunner` wiring |
| Iterative research loop | `NATIVE_AVAILABLE` | `FactorRDLoop`, `ModelRDLoop`, `QuantRDLoop`, and `LoopBase.run` |
| Experiment feedback loop | `NATIVE_AVAILABLE` | Qlib factor/model summarizers and `RDLoop.feedback` |
| Workspace management | `NATIVE_AVAILABLE` | file-backed workspaces and Qlib workspace execution |
| Iteration state | `NATIVE_AVAILABLE` | loop/step indices, prior outputs, trace history, and workflow tracker |
| Checkpoint and resume/recovery | `NATIVE_AVAILABLE` | per-step `dump`, class `load`, session checkout, workspace checkpoint/recovery |
| Research artifact lineage | `NATIVE_PARTIAL` | trace DAG, experiments, workspaces, and logs exist; no frozen AQ Candidate mapping was found |
| Qlib environment execution | `NATIVE_AVAILABLE` | `QlibCondaEnv` and `QlibFBWorkspace.execute` |
| Research-loop stopping/budget hooks | `NATIVE_PARTIAL` | `step_n`, `loop_n`, `all_duration`, and parallelism limits exist; no AQ budget/permission contract is bound |

The installed CLI and source expose the native research loop. It was not
activated because this task prohibited LLM calls and performance execution.

## RD-Agent to Qlib bridge

A single non-performance smoke used the installed RD-Agent
`QlibCondaEnv.run()` abstraction in `/tmp/aq-p3-bridge-smoke`. The command
inside the selected environment only imported Qlib and printed its version.

```text
COMMAND_CLASS = python -c import_qlib_and_print_version
RETURN_CODE = 0
OBSERVED_QLIB_VERSION = 0.9.8.dev26
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = PASS
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
```

This proves the public runtime bridge; it does not resolve the provenance/pin
mismatch above.

## Qlib runtime and capabilities

| Item | Observed state | Result |
|---|---|---|
| Conda environment | `rdagent4qlib` | present |
| Python | `3.10.21` | PASS |
| Qlib version | `0.9.8.dev26` | PASS |
| Installed source URL | `file:///home/zhou/AQ_WORKSPACES/p0-poc-b-qlib-src` | resolved |
| Source SHA | `2fb9380b342556ddb50a4b24e4fe8655d548b2b8` | exact |
| Source worktree | clean | PASS |
| Import | `import qlib` | PASS |
| CLI | `qrun --help` | PASS |
| Dependency health | `pip check`: no broken requirements | PASS |
| MLflow | `3.16.0` | present |
| LightGBM | `4.7.0` | present |

Public-interface import inspection passed for `Dataset`, `DatasetH`,
`DataHandler`, `DataHandlerLP`, `Alpha158`, `Alpha360`, `Model`, `LGBModel`,
the workflow recorder wrapper, `SignalRecord`, `SigAnaRecord`,
`PortAnaRecord`, `TopkDropoutStrategy`, `SimulatorExecutor`, `Exchange`,
`RollingGen`, and `OnlineManager`.

| P3 research capability | Classification | Upstream interface |
|---|---|---|
| Dataset / DatasetH | `NATIVE_AVAILABLE` | `qlib.data.dataset` |
| Handlers and Alpha158-compatible features | `NATIVE_AVAILABLE` | `qlib.data.dataset.handler`, `qlib.contrib.data.handler` |
| Model training | `NATIVE_AVAILABLE` | `qlib.model.base.Model`, `LGBModel` |
| Workflow and experiment recording | `NATIVE_AVAILABLE` | `qlib.workflow.R`, record templates |
| Prediction generation and ranking | `NATIVE_AVAILABLE` | `SignalRecord`, signal analysis, signal strategy |
| Research backtest and transaction costs | `NATIVE_AVAILABLE` | simulator executor, Exchange, Qlib backtest interfaces |
| Portfolio analysis | `NATIVE_AVAILABLE` | `PortAnaRecord` |
| Rolling / online research | `NATIVE_AVAILABLE` | `RollingGen`, `OnlineManager` |

Optional CatBoost, XGBoost, and PyTorch model packages are absent. They are not
part of the selected direct LightGBM path and were not installed.

## Qlib Recorder and MLflow

The existing SQLite-backed P0 recorder was queried through Qlib's public
`MLflowExpManager` and recorder interfaces with creation disabled.

```text
TRACKING_URI = sqlite:////home/zhou/AQ_WORKSPACES/p0-poc-b-qlib-rdagent/mlflow.db
DATABASE_SHA256_BEFORE = 6aee6f24ee845c6f5b259e0c87ff3e62770622a42a5d28d8164e412f89da6016
DATABASE_SHA256_AFTER = 6aee6f24ee845c6f5b259e0c87ff3e62770622a42a5d28d8164e412f89da6016
EXPERIMENT = poc_b_synthetic
EXPERIMENT_ID = 1
RECORDER_ID = b563ff37fda84161b835f9c19774eac6
RECORDER_STATUS = FINISHED
PARAMETERS_VISIBLE = 24
METRICS_VISIBLE = 2
ARTIFACTS_VISIBLE = config; dataset; label.pkl; params.pkl; pred.pkl; task
QLIB_RECORDER = PASS
MLFLOW_TRACKING = PASS
EXPERIMENT_LINEAGE_OWNER = QLIB_MLFLOW
AQ_EXPERIMENT_DATABASE = NONE
AQ_CUSTOM_RECORDER = NONE
AQ_CUSTOM_TRIAL_LEDGER_RUNTIME = NONE
```

No new experiment or performance artifact was created.

## DVC

The isolated DVC environment at `D:\AQ_ENVS\dvc` uses Python `3.12.14` and
DVC `3.67.1`. `uv pip check` reported all 99 installed packages compatible.
The existing `p2_upstream_certification_stack_integration` stage was parsed by
`dvc status` without running `dvc repro`; DVC reported changed dependencies
and its private seal output relative to the historical lock. That drift was
not repaired because this task forbids reproduction and frozen-P2 changes.

```text
DVC_RUNTIME = PASS
DVC_REPRO_EXECUTED = NO
AQ_CUSTOM_ARTIFACT_ENGINE = NONE
AQ_CUSTOM_REPRO_ENGINE = NONE
P3_DVC_STAGE = UPSTREAM_AVAILABLE_NOT_ACTIVATED
```

## P3 research data boundary

The existing historical Qlib provider is identifiable at
`D:\AQ_DATA\P2\qlib-native-ragged-panel-001\qlib_data`. Its retained build
report SHA-256 is
`eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142`
and records:

```text
HISTORY = 2015-01-02 THROUGH 2024-12-31
SECURITY_IDENTITIES = 730
INSTRUMENT_EPISODES = 745
MEMBER_SESSION_ROWS = 1267963
OBSERVED_SAFE_ROWS = 1224788
MASKED_ROWS = 43175
P3_RESEARCH_DATA_INTERFACE = PASS
```

The provider ends before the sealed-OOS start and was not opened by the bridge
smoke. RD-Agent received only the temporary smoke directory. No sealed result
path or query was provided.

```text
SEALED_OOS_START_SESSION = 2026-09-14
SEALED_OOS_AVAILABLE = NO
P3_CAN_ACCESS_SEALED_OOS = NO
EARLY_SEALED_RESULT_ACCESS = PROHIBITED
INTERMEDIATE_PEEK = PROHIBITED
SEALED_OOS_ISOLATION = PASS
```

## P3 Candidate to P2 handoff inspection

| Required identity/evidence | Availability |
|---|---|
| Research iteration identity | native loop index/session path available |
| Hypothesis/factor identity | hypothesis, task, experiment, trace history available |
| Factor/code artifact | file-backed workspace and code dictionary available |
| Model class/config | Qlib task/config and recorder parameters available |
| Dataset identity | Qlib dataset configuration and DVC dependency identity available |
| Qlib Recorder identity | native recorder/run ID available |
| Prediction artifact identity | native recorder artifact available; AQ content-hash binding not unified |
| Research metrics | Qlib recorder metrics and analysis artifacts available |
| Trial/experiment lineage | RD-Agent trace and Qlib/MLflow lineage each exist; cross-upstream binding is not frozen |

The upstreams expose the ingredients but no existing repository contract binds
one RD-Agent iteration, its workspace/code identity, Qlib recorder/prediction,
dataset identity, and P2 Candidate identity into a fail-closed package.

```text
P3_TO_P2_HANDOFF = THIN_CONTRACT_REQUIRED
GENERIC_CANDIDATE_PACKAGING_ENGINE = NOT_AUTHORIZED
```

## P2 boundary preservation

```text
P3_CAN_ISSUE_CERTIFIED = NO
P3_CAN_EDIT_PROTOCOL_V1 = NO
P3_CAN_ACCESS_SEALED_OOS = NO
P3_CAN_PROMOTE_TO_PRODUCTION = NO
P3_CAN_TRADE_LIVE = NO
CANDIDATE_LIFECYCLE = RD_AGENT_QLIB_RESEARCH -> CANDIDATE -> P2_CERTIFICATION_GATE -> REJECTED_OR_NOT_ELIGIBLE_OR_FUTURE_CERTIFIED
```

No P2 protocol, threshold, authority, provider state, frozen data, or result
was changed.

## Finite residual-gap register

| Capability | Classification | Exact residual action |
|---|---|---|
| RD-Agent installed-runtime source identity | `UPSTREAM_BLOCKED` | bind the control runtime to an exact auditable release/SHA; do not infer the checkout SHA |
| RD-Agent declared Qlib pin versus selected Qlib runtime | `UPSTREAM_BLOCKED` | reverse dependencies and explicit resolver prove a bounded `fsspec 2026.7.0` to `2026.6.0` downgrade changes no other existing package; execute only under the next bounded authorization |
| AQ US ragged-panel scenario configuration | `THIN_AQ_CONTRACT_MAY_BE_REQUIRED` | installed templates are fixed to `~/.qlib/qlib_data/cn_data`, `region: cn`, and `csi300`; prove a configuration/adapter-only US path |
| Autonomous LLM research loop | `UPSTREAM_AVAILABLE_NOT_ACTIVATED` | activate only after provenance/config gates and separate LLM-budget authorization |
| P3 Candidate to P2 mapping | `THIN_AQ_CONTRACT_MAY_BE_REQUIRED` | define a project-specific fail-closed identity contract; do not build a workflow engine |
| P3 DVC dependency stage | `UPSTREAM_AVAILABLE_NOT_ACTIVATED` | configure only after the P3 artifact boundary is frozen; do not duplicate DVC |
| Sealed-OOS release | `DEFERRED_TO_LATER_PHASE` | remain inaccessible until the one-shot P2 authority permits release |
| Additional research/provider/broker projects | `NOT_REQUIRED` | remain inactive for this direct integration |

A blocker is not authorization for custom implementation. The bounded
provenance-alignment attempt is recorded in
`p3-rdagent-runtime-provenance-alignment-001.md`: the exact source wheel built
offline, but its mandatory dependency metadata made `pip check` fail, so the
original healthy runtime was restored. The subsequent dependency-alignment
dry run is recorded in `p3-rdagent-runtime-dependency-alignment-001.md` and
failed closed because it proposed an existing `fsspec` downgrade. The
subsequent read-only conflict analysis found the exact bounded downgrade safe
against every installed requirement and proposed no other existing-package
change. Its separately authorized execution is now the first gate; the US
configuration and Candidate contract remain finite follow-on gaps.

## Final state and non-actions

```text
P3_AUTONOMOUS_RESEARCH = IN_PROGRESS
RD_AGENT_RUNTIME = PASS
RD_AGENT_NATIVE_RESEARCH_LOOP = NATIVE_AVAILABLE
RD_AGENT_CHECKPOINT_RESUME = NATIVE_AVAILABLE
QLIB_RUNTIME = PASS
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = PASS_PRE_ALIGNMENT_RUNTIME_ONLY
QLIB_RESEARCH_CAPABILITIES = PASS
QLIB_RECORDER = PASS
MLFLOW_TRACKING = PASS
DVC_RUNTIME = PASS
P3_RESEARCH_DATA_INTERFACE = PASS
P3_TO_P2_HANDOFF = THIN_CONTRACT_REQUIRED
SEALED_OOS_ISOLATION = PASS
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P3_UPSTREAM_RESEARCH_STACK_INTEGRATION = COMPLETE_WITH_DOCUMENTED_BLOCKERS
CURRENT_NEXT = P3_RDAGENT_FSSPEC_BOUNDED_DOWNGRADE_AND_PROVENANCE_ALIGNMENT_001

RD_AGENT_LLM_LOOP_EXECUTED = NO
LLM_CALLS = 0
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
SKFOLIO_EXECUTED = NO
ARCH_EXECUTED = NO
DVC_REPRO_EXECUTED = NO
MARKET_DATA_NETWORK_CALLS = 0
NEW_DATA_PROVIDER = NO
BROKER_CALLS = 0
LIVE_TRADING = NO
PAPER_TRADING = NO
```

## Subsequent bounded-alignment attempt

The authorized fsspec/dependency/provenance execution confirmed the audited
resolver closure and temporarily passed RD-Agent dependency, import, CLI,
wheel-provenance, and Qlib-pin checks. The single mandatory aligned-runtime
`QlibCondaEnv.run()` smoke returned 127 because the default configuration did
not bind the selected Conda environment's bin path. No retry was permitted.
The original `rdagent 0.8.0` and `fsspec 2026.7.0` environment was restored
with an identical complete freeze.

```text
RD_AGENT_RUNTIME = PASS_ORIGINAL_0_8_0_RESTORED
FSSPEC_ALIGNMENT = BLOCKED_FULL_ROLLBACK_AFTER_BRIDGE_FAILURE
RD_AGENT_DEPENDENCY_ALIGNMENT = BLOCKED_FULL_ROLLBACK_AFTER_BRIDGE_FAILURE
RD_AGENT_RUNTIME_PROVENANCE = BLOCKED
RD_AGENT_QLIB_PIN_ALIGNMENT = BLOCKED
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = BLOCKED_ALIGNED_RUNTIME_PATH_NOT_BOUND
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_RDAGENT_FSSPEC_BOUNDED_DOWNGRADE_AND_PROVENANCE_ALIGNMENT_001
```

## Subsequent explicit-bin-path retry

The zero-mutation prerequisite retry resolved the actual `rdagent4qlib`
prefix from Conda metadata and passed its bin directory explicitly to the
restored RD-Agent 0.8.0 public configuration. The installed 0.8.0
`CondaConf` validator nevertheless overwrote that value after its unqualified
`conda` subprocess could not be found. The single proof returned 127 and the
task stopped before all package operations.

```text
RD_AGENT_RUNTIME = PASS_ORIGINAL_0_8_0_UNCHANGED
EXPLICIT_BINPATH_CONFIGURATION_PROOF = BLOCKED_CONDA_DISCOVERY_PATH
PACKAGE_CHANGES = 0
FSSPEC_VERSION = 2026.7.0
QLIB_PACKAGE_CHANGED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_RDAGENT_CONDA_DISCOVERY_PATH_CONFIGURATION_RESOLUTION_001
```

## Current RD-Agent runtime integration closeout

The native discovery path is now proven. With
`/home/zhou/miniforge3/bin` prepended only to the bounded process PATH,
unmodified `QlibCondaConf()` discovered the unique `rdagent4qlib` environment.
One pre-alignment and one post-alignment non-performance
`QlibCondaEnv.run()` proof each returned zero from the selected Qlib Python.

The audited source-derived RD-Agent `0.8.1.dev37` runtime and its exact Qlib
pin now align with the selected Qlib commit. The dependency closure passes,
Qlib and DVC inventories are unchanged, and no AQ runner or generic engine was
introduced.

```text
CONDA_DISCOVERY_PATH_CONFIGURATION_PROOF = PASS
PRE_ALIGNMENT_NATIVE_BRIDGE = PASS
FSSPEC_ALIGNMENT = PASS
RD_AGENT_DEPENDENCY_ALIGNMENT = PASS
RD_AGENT_RUNTIME_PROVENANCE = PASS
RD_AGENT_QLIB_PIN_ALIGNMENT = PASS
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = PASS
QLIB_PACKAGE_CHANGED = NO
DVC_ENV_CHANGED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_US_RAGGED_SCENARIO_CONFIGURATION_PROOF_001
```

## Current US ragged scenario configuration proof

The pinned RD-Agent factor and model templates expose Qlib initialization and
workflow settings as YAML, but their checked-in defaults are China-specific.
A disposable copy changed only configuration values, removed the default
feature `Fillna` processor to preserve the established P2 ragged policy, and
was executed through native `QlibCondaEnv.run()` without `prepare()`.

Qlib initialized the existing immutable US provider with `region=us` and
`market=p2_pit`. Public Qlib instrument resolution returned different active
sets at the provider's first and last sessions. A seven-session boundary
sample returned four observed rows and left three unavailable sessions absent;
no row or price was synthesized or filled. Provider file counts, byte counts,
and key hashes were unchanged.

The provider, region, market, benchmark, and missing-data choices are literal
template values rather than runtime environment settings. A bounded static
US config is therefore required; no executable adapter or AQ engine is
required.

```text
QLIB_INIT_FROM_RDAGENT_US_CONFIG = PASS
QLIB_US_REGION_CONFIG = us
QLIB_US_MARKET_CONFIG = p2_pit
US_INSTRUMENT_UNIVERSE_RESOLVED = PASS
STATIC_CURRENT_UNIVERSE_SUBSTITUTION = NO
RAGGED_PANEL_SEMANTICS_PRESERVED = YES
PIT_MEMBERSHIP_AUTHORITY_CHANGED = NO
SEALED_OOS_ISOLATION = PASS
P3_US_SCENARIO_CONFIGURATION = THIN_STATIC_CONFIG_REQUIRED
UNACCOUNTED_EXECUTION_HARDCODES = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_US_RAGGED_STATIC_CONFIG_MATERIALIZATION_001
```

## Current US ragged static-config materialization

The minimum selected configuration set is now materialized under the existing
RD-Agent owner: one pinned-template overlay for factor research and one for
model research. The overlays bind the immutable US provider, `region=us`, and
the date-valid `p2_pit` market; omit upstream feature filling; and keep all
research dates within 2015-01-02 through 2024-12-31. SPY remains only a
structurally required research placeholder and is not a P2 certification
benchmark.

Both configs rendered and parsed through Qlib's public config path inside the
native RD-Agent `QlibCondaEnv`. Qlib initialization, market resolution, and a
bounded ragged sample passed without training, predictions, backtest, LLM,
network, or provider mutation. No executable AQ adapter or generic engine is
required.

```text
P3_US_RAGGED_STATIC_CONFIG = COMPLETE
P3_US_SCENARIO_CONFIGURATION = THIN_STATIC_CONFIG_MATERIALIZED
MINIMUM_REQUIRED_CONFIG_COUNT = 2
ACTIVE_CHINA_EXECUTION_DEFAULTS = 0
RAGGED_PANEL_SEMANTICS_PRESERVED = YES
SEALED_OOS_ISOLATION = PASS
AQ_US_SCENARIO_ADAPTER = NONE
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_CANDIDATE_TO_P2_IDENTITY_CONTRACT_AUDIT_001
```

## Current Candidate-to-P2 identity contract audit

The cross-upstream identity boundary is now defined without implementing a
new AQ engine. RD-Agent owns research content and lineage, Qlib
Recorder/MLflow own the exact completed run, DVC must own dependency and
artifact versions, and P2 Certification owns protocol eligibility, sealed-OOS
isolation, and certification decisions.

No native upstream ID spans all four authorities. After the P3 DVC stage is
activated, the minimum project-owned boundary is an eight-field thin static
manifest with a deterministic Candidate ID. It binds upstream identities; it
does not replace their registries, recorders, artifact stores, or validators.

```text
P3_CANDIDATE_TO_P2_IDENTITY_CONTRACT_AUDIT = COMPLETE
CANDIDATE_TO_P2_CONTRACT = THIN_STATIC_MANIFEST_REQUIRED
CANDIDATE_ID_STRATEGY = DETERMINISTIC_HASH
AQ_REQUIRED_IDENTITY_FIELD_COUNT = 8
CONTRACT_IMPLEMENTATION_ORDER = AFTER_DVC_STAGE
CANDIDATE_IDENTITY_IS_CERTIFICATION_RESULT = NO
P3_CAN_ACCESS_SEALED_OOS = NO
P3_CAN_ISSUE_CERTIFIED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_DVC_STAGE_ACTIVATION_001
```

## Current RD-Agent US template-binding upstream audit

The pinned RD-Agent source and official current `main` are the same commit.
Both hard-code the finance workspace template folders in the factor/model
Experiment constructors and the five Qlib YAML names in the unchanged
factor/model runners. The CLI, finance environment settings, `app_tpl`, and
custom-data surfaces do not directly expose an external Qlib template folder
or individual YAML path. No newer official release or current upstream hook
closes this gap.

The existing importable component-class settings do provide a safe upstream
extension seam. A binding-only hypothesis-to-experiment component can delegate
to upstream conversion, replace only the experiment's `QlibFBWorkspace`
template folder, and leave RDLoop, proposal, coder, runner, Qlib execution,
Recorder/MLflow, feedback, and trace behavior unchanged.

The next design must preserve all five upstream runner branches. The two
approved US baseline YAMLs cannot simply be aliased over branches that require
combined-factor `StaticDataLoader` or SOTA model semantics.

```text
P3_RDAGENT_US_TEMPLATE_BINDING_UPSTREAM_AUDIT = COMPLETE
OFFICIAL_TEMPLATE_OVERRIDE_AVAILABLE = NO
OFFICIAL_UPGRADE_TEMPLATE_OVERRIDE_AVAILABLE = NO
THIN_SCENARIO_BINDING_FEASIBLE = YES
RD_AGENT_US_TEMPLATE_BINDING = THIN_SCENARIO_BINDING_REQUIRED
P3_DVC_STAGE_ACTIVATION = DEFERRED_UNTIL_RDAGENT_US_TEMPLATE_BINDING
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_RDAGENT_US_THIN_SCENARIO_BINDING_DESIGN_001
```
