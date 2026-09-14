# P3 RD-Agent Runtime Provenance Alignment 001

Status: **BLOCKED / ORIGINAL RUNTIME RESTORED**

## Ownership preamble

```text
CAPABILITY = RD-Agent P3 control-runtime provenance
UPSTREAM_OWNER = Microsoft RD-Agent
OWNERSHIP_MODE = UPSTREAM_WHOLE
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = YES, THIN ONLY
AQ_ALLOWED_SCOPE = configuration; runtime selection; provenance evidence; health evidence; orchestration
CUSTOM_ENGINE_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_TARGET = 0
```

## Authority and bounded objective

```text
TASK = AUTONOMOUS-QUANT-P3-RDAGENT-RUNTIME-PROVENANCE-ALIGNMENT-001
BASE_MAIN = d6215b19df989b32aa1151d935a4ef6399424c08
BRANCH = agent/p3-upstream-research-stack-integration-001
PRIOR_BRANCH_HEAD = 20e28cf1013fdb64c889fc0a5897520c59ad86b7
MODE = BOUNDED_UPSTREAM_RUNTIME_PROVENANCE_ALIGNMENT_ONLY
```

This task attempted only to bind the existing RD-Agent control runtime to an
immutable wheel built from the audited Microsoft source checkout and to align
the runtime-declared Qlib pin. It did not address the US ragged-panel scenario,
the Candidate-to-P2 contract, a P3 DVC stage, or autonomous-loop activation.

## Official source authority

| Item | Verified value | Result |
|---|---|---|
| Origin | `https://github.com/microsoft/RD-Agent.git` | official Microsoft repository |
| Source checkout | `/home/zhou/AQ_UPSTREAM/rd-agent` | present |
| Source SHA | `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` | exact |
| Git description | `v0.8.0-37-g32b3d395` | observed |
| Source worktree | clean before and after | PASS |
| Declared Qlib commit | `2fb9380b342556ddb50a4b24e4fe8655d548b2b8` | exact |

No source file was modified.

## Pre-alignment runtime and rollback snapshot

The isolated control environment was `/home/zhou/AQ_ENVS/rdagent` with Python
`3.11.16`. Its imported package and distribution metadata were:

```text
PRE_ALIGNMENT_RD_AGENT_VERSION = 0.8.0
IMPORT_PATH = /home/zhou/AQ_ENVS/rdagent/lib/python3.11/site-packages/rdagent
DIST_INFO = /home/zhou/AQ_ENVS/rdagent/lib/python3.11/site-packages/rdagent-0.8.0.dist-info
ENTRY_POINT = rdagent=rdagent.app.cli:app
DIRECT_URL = ABSENT
PRE_ALIGNMENT_DECLARED_QLIB_PIN = 3e72593b8c985f01979bebcf646658002ac43b00
PRE_RDAGENT_PACKAGE_TREE_SHA256 = 01693527f6ba577016d312102c9fd202a10eb65dfca97bc48bd9bdede52285e5
PRE_CONTROL_FREEZE_SHA256 = 28880ae97ecc679435729c775603be09f35121b53dc77611940a5ac0660fbccd
PRE_QLIB_FREEZE_SHA256 = 152a6d6034b7f5a089a790a6bba91ce8ed32e566ff3d0f19fc4adee99ec3ad58
PRE_ALIGNMENT_PIP_CHECK = PASS
```

Before mutation, the installed `rdagent` package, its dist-info directory, and
the CLI entry point were copied to a task-specific location outside the
repository. This provided a byte-preserving rollback path.

## Exact offline wheel build

The existing environment already contained `setuptools 84.0.0`,
`setuptools-scm 10.2.3`, `wheel 0.48.0`, and `pip 26.2.1`. The separate
`build` frontend was absent, so the wheel was built with the existing pip and
PEP 517 backend using `--no-build-isolation`, `--no-deps`, `--no-index`, and
`PIP_NO_INDEX=1`.

```text
SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
SOURCE_VERSION = 0.8.1.dev37
WHEEL_FILENAME = rdagent-0.8.1.dev37-py3-none-any.whl
WHEEL_SHA256 = fb78207ec83ea94ca839bff191a619dd952ba840409877e001da11beaf0e26de
WHEEL_DECLARED_QLIB_PIN = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
BUILD_DEPENDENCY_CHANGES = 0
PACKAGE_NETWORK_DOWNLOADS = 0
SOURCE_WORKTREE_CLEAN_AFTER_BUILD = YES
```

The wheel therefore supplied the requested SHA-to-wheel evidence chain. The
wheel and temporary source clone were not retained after the rollback.

## Fail-closed validation and rollback

Only the `rdagent` distribution was replaced, using the local wheel with
`--no-index --no-deps --force-reinstall`. The new package imported as
`rdagent 0.8.1.dev37`, but the mandatory immediate `pip check` failed:

```text
rdagent 0.8.1.dev37 requires datasets, which is not installed.
rdagent 0.8.1.dev37 requires duckduckgo-search, which is not installed.
rdagent 0.8.1.dev37 requires tensorboard, which is not installed.
```

Installing these missing packages was outside this task's authority. The
aligned-runtime bridge smoke was therefore not executed. The original
`rdagent 0.8.0` package, dist-info metadata, and CLI entry point were restored
from the snapshot.

Post-rollback verification established:

```text
POST_ALIGNMENT_RD_AGENT_VERSION = 0.8.0
CONTROL_INVENTORY_RESTORED = YES
RDAGENT_PACKAGE_TREE_RESTORED = YES
RDAGENT_IMPORT = PASS
RDAGENT_CLI_HELP = PASS
PIP_CHECK = PASS
RD_AGENT_DECLARED_QLIB_PIN = 3e72593b8c985f01979bebcf646658002ac43b00
DEPENDENCY_VERSION_CHANGES = 0
QLIB_PACKAGE_CHANGED = NO
SELECTED_QLIB_VERSION = 0.9.8.dev26
SELECTED_QLIB_RUNTIME_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
TEMP_ROLLBACK_AND_BUILD_COPY_RETIRED = YES
```

The failed candidate runtime was not left installed. The selected Qlib
runtime remained unchanged.

## Decision and remaining gaps

```text
RD_AGENT_RUNTIME = PASS
RD_AGENT_RUNTIME_PROVENANCE = BLOCKED
RD_AGENT_RUNTIME_SOURCE_SHA = NONE
RD_AGENT_QLIB_PIN_ALIGNMENT = BLOCKED
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = BLOCKED
ALIGNMENT = BLOCKED
```

The first two residual gaps remain unresolved, now with a concrete upstream
dependency blocker:

1. authorize and resolve only the audited source wheel's missing runtime
   dependencies without changing the selected Qlib runtime;
2. install and validate the exact audited wheel, then bind its wheel hash and
   source SHA to the control runtime;
3. prove the US ragged-panel scenario configuration path;
4. define the thin fail-closed Candidate-to-P2 identity contract;
5. activate the P3 DVC stage after its artifact boundary is frozen;
6. activate the autonomous loop only under separate LLM/budget authority.

The next task is deliberately an upstream runtime dependency-alignment task,
not an AQ replacement implementation.

## Final state and non-actions

```text
P3_AUTONOMOUS_RESEARCH = IN_PROGRESS
P3_UPSTREAM_RESEARCH_STACK_INTEGRATION = COMPLETE_WITH_DOCUMENTED_BLOCKERS
CURRENT_NEXT = P3_RDAGENT_RUNTIME_DEPENDENCY_ALIGNMENT_001

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
PACKAGE_NETWORK_DOWNLOADS = 0
```
