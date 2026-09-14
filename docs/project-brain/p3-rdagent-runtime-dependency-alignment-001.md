# P3 RD-Agent Runtime Dependency Alignment 001

Status: **BLOCKED BY EXISTING-PACKAGE DOWNGRADE / NO ENVIRONMENT MUTATION**

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
