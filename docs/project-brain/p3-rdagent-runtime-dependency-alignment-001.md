# P3 RD-Agent Runtime Dependency Alignment 001

Status: **PASS — CURRENT CLOSEOUT / HISTORICAL BLOCKERS PRESERVED**

## Ownership preamble

```text
CAPABILITY = RD-Agent runtime dependency closure
UPSTREAM_OWNER = Microsoft RD-Agent + Python package dependencies declared by upstream
OWNERSHIP_MODE = UPSTREAM_WHOLE
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = NO GENERIC IMPLEMENTATION
AQ_ALLOWED_SCOPE = runtime configuration; dependency alignment; provenance evidence; health verification
CUSTOM_ENGINE_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_TARGET = 0
```

## Authority and scope

```text
TASK = AUTONOMOUS-QUANT-P3-RDAGENT-RUNTIME-DEPENDENCY-ALIGNMENT-001
BASE_MAIN = d6215b19df989b32aa1151d935a4ef6399424c08
BRANCH = agent/p3-upstream-research-stack-integration-001
PRIOR_BRANCH_HEAD = 43cbb1d67c005d70551207f6bb0f2c2af017e7bb
MODE = BOUNDED_UPSTREAM_DEPENDENCY_ALIGNMENT_AND_PROVENANCE_COMPLETION
```

This task evaluated only the missing dependency closure for the audited
Microsoft RD-Agent source. The hard no-upgrade/no-downgrade resolver gate
failed, so no distribution was downloaded into a wheelhouse and no package
was installed, removed, upgraded, or downgraded.

## Upstream requirement authority

The official checkout remained clean at:

```text
ORIGIN = https://github.com/microsoft/RD-Agent.git
SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
SOURCE_WORKTREE_CLEAN = YES
```

At this exact SHA, `requirements.txt` directly declares `tensorboard`,
`datasets`, and `duckduckgo-search`. `pyproject.toml` declares project
dependencies dynamically from `requirements.txt` through
`tool.setuptools.dynamic.dependencies`. The dependency requirement therefore
comes from the audited upstream source, not merely from the earlier failed
`pip check`.

```text
UPSTREAM_MISSING_TOP_LEVEL_DEPENDENCIES = datasets; duckduckgo-search; tensorboard
```

## Pre-mutation snapshot

The control runtime was snapshotted before resolution:

```text
CONTROL_ENV = /home/zhou/AQ_ENVS/rdagent
PYTHON = 3.11.16
PIP = 26.2.1
PRE_ALIGNMENT_RD_AGENT_VERSION = 0.8.0
PRE_ALIGNMENT_PIP_CHECK = PASS
PRE_RDAGENT_PACKAGE_TREE_SHA256 = 01693527f6ba577016d312102c9fd202a10eb65dfca97bc48bd9bdede52285e5
PRE_CONTROL_FREEZE_SHA256 = 28880ae97ecc679435729c775603be09f35121b53dc77611940a5ac0660fbccd
PRE_QLIB_FREEZE_SHA256 = 152a6d6034b7f5a089a790a6bba91ce8ed32e566ff3d0f19fc4adee99ec3ad58
```

The installed RD-Agent package, dist-info directory, and CLI entry point were
copied to a temporary rollback location outside the repository. No rollback
was needed because the task stopped before package mutation; the temporary
copy was retired after final immutability checks.

## Resolver-only dry run

Pip's supported `--dry-run --report` mechanism was run for exactly the three
upstream top-level dependencies with `--upgrade-strategy only-if-needed`.
The machine-readable report SHA-256 was:

```text
RESOLVER_REPORT_SHA256 = 2aecce43917be12129c4ec848e1ca19dd128a0347d15bfcc55f2807669516caf
```

The proposed closure was:

| Classification | Distribution | Existing version | Proposed version |
|---|---|---:|---:|
| `ADD_NEW_PACKAGE` | `absl-py` | absent | `2.5.0` |
| `ADD_NEW_PACKAGE` | `datasets` | absent | `5.0.1` |
| `ADD_NEW_PACKAGE` | `duckduckgo-search` | absent | `8.1.1` |
| `DOWNGRADE_EXISTING` | `fsspec` | `2026.7.0` | `2026.6.0` |
| `ADD_NEW_PACKAGE` | `grpcio` | absent | `1.84.0` |
| `ADD_NEW_PACKAGE` | `lxml` | absent | `6.1.3` |
| `ADD_NEW_PACKAGE` | `multiprocess` | absent | `0.70.19` |
| `ADD_NEW_PACKAGE` | `primp` | absent | `2.0.1` |
| `ADD_NEW_PACKAGE` | `tensorboard` | absent | `2.21.0` |
| `ADD_NEW_PACKAGE` | `tensorboard-data-server` | absent | `0.7.2` |

The resolver selected `datasets 5.0.1`, whose declared constraint is
`fsspec>=2023.1.0,<=2026.6.0`. The control environment already contains
`fsspec 2026.7.0`; satisfying the selected closure would therefore require an
existing-package downgrade.

```text
DRY_RUN_NEW_PACKAGE_COUNT = 9
DRY_RUN_EXISTING_PACKAGE_UPGRADES = 0
DRY_RUN_EXISTING_PACKAGE_DOWNGRADES = 1
DRY_RUN_EXISTING_PACKAGE_REMOVALS = 0
HARD_GATE = FAIL_EXISTING_FSSPEC_DOWNGRADE_REQUIRED
```

The contract prohibited forcing resolution or manually choosing a different
version merely to pass. Execution stopped at the dry-run gate. No wheelhouse
acquisition, dependency installation, new RD-Agent wheel build, audited-wheel
installation, or bridge smoke occurred.

## Final immutability verification

```text
CONTROL_INVENTORY_UNCHANGED = YES
FINAL_RD_AGENT_VERSION = 0.8.0
FINAL_FSSPEC_VERSION = 2026.7.0
RDAGENT_PACKAGE_TREE_UNCHANGED = YES
FINAL_PIP_CHECK = PASS
EXISTING_PACKAGE_VERSION_CHANGES = 0
NEW_PACKAGE_COUNT = 0
REMOVED_PACKAGES = 0
QLIB_PACKAGE_CHANGED = NO
SELECTED_QLIB_VERSION = 0.9.8.dev26
SELECTED_QLIB_RUNTIME_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
TEMP_ROLLBACK_AND_REPORT_RETIRED = YES
```

## Decision and next gate

```text
DEPENDENCY_ALIGNMENT = BLOCKED
RD_AGENT_WHEEL_SHA256 = NONE
RD_AGENT_RUNTIME_PROVENANCE = BLOCKED
RD_AGENT_RUNTIME_SOURCE_SHA = NONE
RD_AGENT_DECLARED_QLIB_PIN = 3e72593b8c985f01979bebcf646658002ac43b00
RD_AGENT_QLIB_PIN_ALIGNMENT = BLOCKED
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = BLOCKED
```

The next task is a specific upstream dependency-conflict analysis. It may
determine why the environment has `fsspec 2026.7.0` and whether an upstream-
compatible resolution exists, but it must not silently downgrade the package,
pick an arbitrary dependency version, or implement an AQ replacement.

The later residual gaps remain unchanged: US ragged-panel configuration proof,
the thin fail-closed Candidate-to-P2 identity contract, P3 DVC-stage
activation, and autonomous-loop activation.

## Final state and non-actions

```text
P3_AUTONOMOUS_RESEARCH = IN_PROGRESS
P3_UPSTREAM_RESEARCH_STACK_INTEGRATION = COMPLETE_WITH_DOCUMENTED_BLOCKERS
CURRENT_NEXT = P3_RDAGENT_FSSPEC_DEPENDENCY_CONFLICT_ANALYSIS_001

AQ_NEW_GENERIC_ENGINE_COUNT = 0
CODE_CHANGED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
LLM_CALLS = 0
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
DVC_REPRO_EXECUTED = NO
MARKET_DATA_NETWORK_CALLS = 0
NEW_DATA_PROVIDER = NO
BROKER_CALLS = 0
PAPER_TRADING = NO
LIVE_TRADING = NO
```

## Subsequent current-state update

The authorized read-only conflict analysis verified that every installed
reverse dependency accepts `fsspec 2026.6.0` and that an explicit resolver
dry run proposes no other existing-package change. The prior `CURRENT_NEXT`
above is the historical outcome of this dependency-alignment task. Current
authority is:

```text
RESOLUTION_CLASS = SAFE_BOUNDED_FSSPEC_DOWNGRADE
CURRENT_NEXT = P3_RDAGENT_FSSPEC_BOUNDED_DOWNGRADE_AND_PROVENANCE_ALIGNMENT_001
```

## Bounded downgrade and provenance alignment attempt

Status: **BLOCKED / MANDATORY BRIDGE SMOKE FAILED / FULL ROLLBACK COMPLETE**

The separately authorized bounded task began from the clean branch head
`efabc669d91bae99012c91b378c09f82e9f0d686`. The official RD-Agent checkout
was clean at `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd`; the selected Qlib source was
clean at `2fb9380b342556ddb50a4b24e4fe8655d548b2b8`; and `rdagent4qlib` reported
Qlib `0.9.8.dev26`.

The pre-mutation control environment was Python `3.11.16`, pip `26.2.1`,
`rdagent 0.8.0`, and `fsspec 2026.7.0`, with `pip check` passing. Its sorted
freeze SHA-256 was
`28880ae97ecc679435729c775603be09f35121b53dc77611940a5ac0660fbccd`.
The selected Qlib environment freeze SHA-256 was
`152a6d6034b7f5a089a790a6bba91ce8ed32e566ff3d0f19fc4adee99ec3ad58`.
A repository-external byte-preserving rollback snapshot was created before
mutation.

### Exact resolver and released artifacts

The repeated `--dry-run --report --upgrade-strategy only-if-needed` resolver
gate proposed exactly:

```text
ADD absl-py==2.5.0
ADD datasets==5.0.1
ADD duckduckgo-search==8.1.1
ADD grpcio==1.84.0
ADD lxml==6.1.3
ADD multiprocess==0.70.19
ADD primp==2.0.1
ADD tensorboard==2.21.0
ADD tensorboard-data-server==0.7.2
CHANGE fsspec 2026.7.0 -> 2026.6.0
OTHER_EXISTING_PACKAGE_UPGRADES = 0
OTHER_EXISTING_PACKAGE_DOWNGRADES = 0
EXISTING_PACKAGE_REMOVALS = 0
RESOLVER_REPORT_SHA256 = 4b7fbe7d4341f659b38edf10c3890bb349e8535f60565fdb770c9b8cb9cc4398
```

The ten exact released wheels were acquired into the temporary wheelhouse.
Their SHA-256 values were:

| Distribution | SHA-256 |
|---|---|
| `absl-py 2.5.0` | `0f17b89f2a4eaaedc4f28c622998aa690564b3012a396a4ffad0821007fe03ba` |
| `datasets 5.0.1` | `9fbf73688f8c18f7529b4fe592abd04015f81d1e58001e4bac73ffb2b39d7cc4` |
| `duckduckgo-search 8.1.1` | `f48adbb06626ee05918f7e0cef3a45639e9939805c4fc179e68c48a12f1b5062` |
| `fsspec 2026.6.0` | `02e0b71817df9b2169dc30a16832045764def1191b43dcff5bb85bdee212d2a1` |
| `grpcio 1.84.0` | `bd8ea8eb3817b226057cc1c0e7ec4b378dcda52043b972b6ff12b1152178967d` |
| `lxml 6.1.3` | `527195c188d7d0af748cd48d220ab8cdc5cb99be3d49ac4d9be7324d8abf9bc0` |
| `multiprocess 0.70.19` | `928851ae7973aea4ce0eaf330bbdafb2e01398a91518d5c8818802845564f45c` |
| `primp 2.0.1` | `9a7be373adfded677a9092ae2743873d5c8a9573148d617a189d26715f7d8ea5` |
| `tensorboard 2.21.0` | `7279316dcb6bd5bc391d623dea841531299cde1887310e8133bc34a996d32255` |
| `tensorboard-data-server 0.7.2` | `ef687163c24185ae9754ed5650eb5bc4d84ff257aabdc33f0cc6f74d8ba54530` |

Installed from the wheelhouse with `--no-index`, the temporary aligned state
passed `pip check`, the exact package-version assertions, the full inventory
diff, and import-only smoke for `fsspec`, `datasets`, `tensorboard`,
`duckduckgo_search`, `prefect`, and `huggingface_hub`. No search or dataset
request was issued.

### Exact RD-Agent wheel and mandatory bridge result

An offline local wheel was built from a clean local build clone of the official
source SHA. Neither the official source nor the build clone was modified.

```text
RD_AGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
SOURCE_VERSION = 0.8.1.dev37
WHEEL_FILENAME = rdagent-0.8.1.dev37-py3-none-any.whl
WHEEL_SHA256 = ad330119e1d5a6986a963934a39e26a2dc0f79aa0b69c4590fd7c3f063acec37
WHEEL_DECLARED_QLIB_PIN = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
```

The wheel was installed with `--no-index --no-deps --force-reinstall`.
`rdagent 0.8.1.dev37` imported, `rdagent --help` passed, `pip check` passed,
the installed code declared the exact selected Qlib pin, and its
`direct_url.json` recorded the same wheel SHA-256.

Exactly one public `QlibCondaEnv.run()` smoke then requested only `import qlib`
and printing the version and interpreter identity. `QlibCondaEnv.prepare()`
was never called. Although `QlibCondaConf.conda_env_name` defaults to
`rdagent4qlib`, its inherited `bin_path` defaults to empty. The smoke emitted
PATH `/bin/:/usr/bin/:`, so it failed before Qlib import:

```text
BRIDGE_RETURN_CODE = 127
BRIDGE_STDOUT = timeout: failed to run command 'python': No such file or directory
OBSERVED_QLIB_VERSION = NOT_OBSERVED_IN_ALIGNED_SMOKE
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = BLOCKED
```

RD-Agent logged local LLM-backend configuration initialization while reporting
the failed run, but no LLM loop or external LLM request occurred. The contract
permitted only one bridge smoke, so there was no repair or retry. A future
separately authorized retry must configure the selected Qlib environment bin
path while continuing to prohibit `prepare()`.

### Rollback and authoritative current state

The failed mandatory check triggered full rollback. All nine new packages were
removed, `fsspec 2026.7.0`, `rdagent 0.8.0`, and the original CLI entry point
were restored, and the sorted freeze matched the pre-task file byte-for-byte.
`pip check`, RD-Agent import, and CLI help passed after rollback. Qlib and DVC
were unchanged; the DVC freeze SHA-256 remained
`4c4c5cbb2d1ae319ed26642065464081ea1a35560e880e71e4e3468e7a19b699`
for all 99 distributions.

```text
POST_RD_AGENT_VERSION = 0.8.0
POST_FSSPEC_VERSION = 2026.7.0
ROLLBACK_CONTROL_FREEZE_SHA256 = 28880ae97ecc679435729c775603be09f35121b53dc77611940a5ac0660fbccd
ROLLBACK_FREEZE_IDENTITY = PASS
QLIB_FREEZE_IDENTITY = PASS
DVC_ENV_CHANGED = NO
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
QLIB_PACKAGE_CHANGED = NO
FSSPEC_ALIGNMENT = BLOCKED_FULL_ROLLBACK_AFTER_BRIDGE_FAILURE
RD_AGENT_DEPENDENCY_ALIGNMENT = BLOCKED_FULL_ROLLBACK_AFTER_BRIDGE_FAILURE
RD_AGENT_RUNTIME_PROVENANCE = BLOCKED_ORIGINAL_0_8_0_RESTORED
RD_AGENT_RUNTIME_SOURCE_SHA = NONE
RD_AGENT_DECLARED_QLIB_PIN = 3e72593b8c985f01979bebcf646658002ac43b00
SELECTED_QLIB_RUNTIME_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
RD_AGENT_QLIB_PIN_ALIGNMENT = BLOCKED
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = BLOCKED_ALIGNED_RUNTIME_PATH_NOT_BOUND
RETRY_REQUIRED = YES
CURRENT_NEXT = P3_RDAGENT_FSSPEC_BOUNDED_DOWNGRADE_AND_PROVENANCE_ALIGNMENT_001

AQ_NEW_GENERIC_ENGINE_COUNT = 0
CODE_CHANGED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
LLM_CALLS = 0
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
DATASET_DOWNLOADS = 0
MARKET_DATA_NETWORK_CALLS = 0
DVC_REPRO_EXECUTED = NO
BROKER_CALLS = 0
PAPER_TRADING = NO
LIVE_TRADING = NO
```

The later residual gaps remain unchanged: US ragged-panel scenario
configuration proof, the Candidate-to-P2 thin fail-closed identity contract,
P3 DVC-stage activation, and autonomous-loop activation. The project does not
advance to them while the bounded alignment remains rolled back.

## Explicit Qlib bin-path alignment retry

Status: **BLOCKED BEFORE PACKAGE MUTATION**

The bounded retry started from the exact rolled-back environment:

```text
TASK = AUTONOMOUS-QUANT-P3-RDAGENT-EXPLICIT-QLIB-BINPATH-ALIGNMENT-RETRY-001
PRIOR_BRANCH_HEAD = de5d6f457d65dc51483c05096caabc398c4c9f95
RD_AGENT_VERSION = 0.8.0
FSSPEC_VERSION = 2026.7.0
PIP_CHECK = PASS
```

Actual Conda metadata resolved exactly one `rdagent4qlib` environment:

```text
SELECTED_QLIB_PREFIX = /home/zhou/miniforge3/envs/rdagent4qlib
SELECTED_QLIB_BIN_PATH = /home/zhou/miniforge3/envs/rdagent4qlib/bin
SELECTED_PYTHON = /home/zhou/miniforge3/envs/rdagent4qlib/bin/python
SELECTED_QLIB_VERSION = 0.9.8.dev26
SELECTED_QLIB_RUNTIME_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
```

The official checkout at
`32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` confirmed the public inheritance
chain `QlibCondaConf -> CondaConf -> LocalConf`; `QlibCondaConf` selects
`rdagent4qlib`; and `LocalConf.bin_path` defaults to empty. Official test
source also demonstrates public construction with `LocalConf(bin_path=...)`.

Exactly one zero-package-mutation proof instantiated the restored installed
runtime with:

```text
QlibCondaConf(bin_path=/home/zhou/miniforge3/envs/rdagent4qlib/bin)
```

and invoked `QlibCondaEnv.run()` with a payload limited to printing
`sys.executable`, `qlib.__version__`, and PATH. It returned 127 before Python
could start:

```text
RETURN_CODE = 127
EFFECTIVE_RUN_PATH = /bin/:/usr/bin/:
STDOUT = timeout: failed to run command 'python': No such file or directory
EXPLICIT_BINPATH_CONFIGURATION_PROOF = BLOCKED
```

Read-only inspection then established the exact reason. Installed RD-Agent
0.8.0 defines an after-model-validator on `CondaConf` that always runs:

```text
conda run -n rdagent4qlib --no-capture-output env | grep '^PATH='
```

and always replaces `self.bin_path` with either the command result or an empty
string. The `conda` executable is not discoverable on the control process PATH,
so the validator returned a nonzero status and overwrote the explicitly passed
value with `''`. A separate configuration instantiation confirmed:

```text
EFFECTIVE_BIN_PATH = ''
CONDA_ENV_NAME = rdagent4qlib
```

The task contract required an immediate stop if this pre-mutation proof failed.
Therefore no rollback snapshot, resolver dry run, wheel download, dependency
installation, RD-Agent build, or final bridge smoke was started. The direct
selected-Qlib check remains valid, but it is not misreported as a successful
RD-Agent bridge.

```text
PACKAGE_CHANGES = 0
ENVIRONMENT_CHANGES = 0
POST_RD_AGENT_VERSION = 0.8.0
POST_FSSPEC_VERSION = 2026.7.0
DEPENDENCY_IMPORT_SMOKE = NOT_EXECUTED_STEP_2_STOP
RD_AGENT_WHEEL_SHA256 = NONE
RD_AGENT_RUNTIME_PROVENANCE = BLOCKED
RD_AGENT_RUNTIME_SOURCE_SHA = NONE
RD_AGENT_DECLARED_QLIB_PIN = 3e72593b8c985f01979bebcf646658002ac43b00
RD_AGENT_QLIB_PIN_ALIGNMENT = BLOCKED
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = BLOCKED
UNAUTHORIZED_EXISTING_PACKAGE_VERSION_CHANGES = 0
QLIB_PACKAGE_CHANGED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
RD_AGENT_LLM_LOOP_EXECUTED = NO
LLM_CALLS = 0
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
DATASET_DOWNLOADS = 0
MARKET_DATA_NETWORK_CALLS = 0
CURRENT_NEXT = P3_RDAGENT_CONDA_DISCOVERY_PATH_CONFIGURATION_RESOLUTION_001
```

The next bounded configuration task must establish how the upstream 0.8.0
validator can discover the existing Miniforge `conda` executable without
source modification or package mutation. It must not retry the alignment or
advance to later P3 work until that configuration proof passes.

## Current closeout — native Conda discovery and audited alignment pass

The historical blocked attempts above remain evidence of the failure modes
that preceded this closeout. The bounded configuration resolution exposed the
existing Miniforge executable to the RD-Agent control process only. Native
`QlibCondaConf()` then ran its own validator, discovered the selected
`rdagent4qlib` path, and retained it without a manually supplied `bin_path`.

```text
CONDA_BASE = /home/zhou/miniforge3
CONDA_EXECUTABLE = /home/zhou/miniforge3/bin/conda
CONDA_VERSION = 26.7.2
CONDA_ENV_NAME = rdagent4qlib
SELECTED_QLIB_PREFIX = /home/zhou/miniforge3/envs/rdagent4qlib
SELECTED_QLIB_BIN_PATH = /home/zhou/miniforge3/envs/rdagent4qlib/bin
CONDA_DISCOVERY_PATH_CONFIGURATION_PROOF = PASS
PERSISTENT_OS_PATH_CHANGED = NO
SHELL_PROFILE_CHANGED = NO
```

Before package mutation, exactly one native `QlibCondaEnv.run()` call executed
only `import sys, qlib` and printed the interpreter and Qlib version. It
returned zero from the selected environment:

```text
PRE_ALIGNMENT_NATIVE_BRIDGE = PASS
SYS_EXECUTABLE = /home/zhou/miniforge3/envs/rdagent4qlib/bin/python
OBSERVED_QLIB_VERSION = 0.9.8.dev26
PRE_RD_AGENT_VERSION = 0.8.0
PRE_FSSPEC_VERSION = 2026.7.0
```

The resolver dry run proposed exactly the previously audited closure and no
other existing-package version change or removal. Exact released artifacts
were installed for:

```text
fsspec = 2026.6.0
absl-py = 2.5.0
datasets = 5.0.1
duckduckgo-search = 8.1.1
grpcio = 1.84.0
lxml = 6.1.3
multiprocess = 0.70.19
primp = 2.0.1
tensorboard = 2.21.0
tensorboard-data-server = 0.7.2
```

The official clean Microsoft source at
`32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` produced
`rdagent-0.8.1.dev37-py3-none-any.whl` with SHA-256
`6d4b78037016951d21879249152fee21df90e5dca0a752e233026a41afe64395`.
The wheel was installed with `--no-deps --no-index`; installed provenance,
imports, CLI help, and `pip check` passed.

The installed RD-Agent declares Qlib commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`, exactly matching the selected
Qlib source/runtime. Exactly one post-alignment native
`QlibCondaEnv.run()` repeated the non-performance import proof and returned
zero from the same selected interpreter. `QlibCondaEnv.prepare()` was never
called.

```text
POST_RD_AGENT_VERSION = 0.8.1.dev37
POST_FSSPEC_VERSION = 2026.6.0
RD_AGENT_DEPENDENCY_ALIGNMENT = PASS
RD_AGENT_RUNTIME_PROVENANCE = PASS
RD_AGENT_RUNTIME_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
RD_AGENT_DECLARED_QLIB_PIN = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
SELECTED_QLIB_RUNTIME_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
RD_AGENT_QLIB_PIN_ALIGNMENT = PASS
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = PASS
UNAUTHORIZED_EXISTING_PACKAGE_VERSION_CHANGES = 0
REMOVED_PREEXISTING_PACKAGES = 0
QLIB_PACKAGE_CHANGED = NO
DVC_ENV_CHANGED = NO
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
RD_AGENT_LLM_LOOP_EXECUTED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
DATASET_DOWNLOADS = 0
MARKET_DATA_NETWORK_CALLS = 0
CURRENT_NEXT = P3_US_RAGGED_SCENARIO_CONFIGURATION_PROOF_001
```
