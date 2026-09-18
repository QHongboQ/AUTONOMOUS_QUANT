# P3 RD-Agent Conda Discovery Path Configuration Resolution 001

Status: **PASS**

This record closes the RD-Agent Conda discovery, dependency, runtime
provenance, Qlib-pin, and native bridge gaps. It preserves prior failed
attempts in their original historical documents.

## Authority and configuration

Microsoft RD-Agent source
`32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` establishes that
`QlibCondaConf` selects `rdagent4qlib` and that the inherited validator invokes
an unqualified `conda run -n <environment> --no-capture-output env`, assigning
the returned PATH to `bin_path`.

Filesystem and Conda metadata resolved exactly one intended environment:

```text
CONDA_BASE = /home/zhou/miniforge3
CONDA_EXECUTABLE = /home/zhou/miniforge3/bin/conda
CONDA_VERSION = 26.7.2
SELECTED_QLIB_PREFIX = /home/zhou/miniforge3/envs/rdagent4qlib
SELECTED_QLIB_BIN_PATH = /home/zhou/miniforge3/envs/rdagent4qlib/bin
```

Only the bounded process PATH was prefixed with the Conda base bin. A fresh
process after validation could not resolve `conda`, proving no persistent PATH
or profile mutation.

## Native bridge proofs

`QlibCondaConf()` was instantiated without a manual `bin_path`. Its native
validator produced a PATH beginning with:

```text
/home/zhou/miniforge3/envs/rdagent4qlib/bin:
/home/zhou/miniforge3/condabin:
/home/zhou/miniforge3/bin:
<original process PATH>
```

Exactly one pre-alignment and one post-alignment `QlibCondaEnv.run()` call
were made. Each executed only an import/version/interpreter proof; both
returned zero with:

```text
SYS_EXECUTABLE = /home/zhou/miniforge3/envs/rdagent4qlib/bin/python
OBSERVED_QLIB_VERSION = 0.9.8.dev26
```

No `prepare()` call, model training, prediction, backtest, dataset download,
market-data request, broker call, or LLM loop occurred.

## Audited environment alignment

The resolver dry-run report SHA-256 was
`4b7fbe7d4341f659b38edf10c3890bb349e8535f60565fdb770c9b8cb9cc4398`.
It proposed only the authorized dependency closure. The final environment
diff was:

```text
CHANGED_EXISTING = fsspec 2026.7.0 -> 2026.6.0
CHANGED_RUNTIME = rdagent 0.8.0 -> 0.8.1.dev37
ADDED = absl-py 2.5.0; datasets 5.0.1; duckduckgo-search 8.1.1;
        grpcio 1.84.0; lxml 6.1.3; multiprocess 0.70.19; primp 2.0.1;
        tensorboard 2.21.0; tensorboard-data-server 0.7.2
REMOVED = NONE
UNAUTHORIZED_EXISTING_PACKAGE_VERSION_CHANGES = 0
FINAL_FREEZE_SHA256 = 1d60835745fad44b917eff46918719f8c1c392fb05747f06fb4dde8cb8c1f67e
```

The clean official source built
`rdagent-0.8.1.dev37-py3-none-any.whl`, SHA-256
`6d4b78037016951d21879249152fee21df90e5dca0a752e233026a41afe64395`.
The wheel was installed with `--no-deps --no-index`. Import, CLI help,
dependency health, direct provenance, and the declared Qlib pin passed.

```text
RD_AGENT_RUNTIME_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
RD_AGENT_DECLARED_QLIB_PIN = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
SELECTED_QLIB_RUNTIME_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
RD_AGENT_QLIB_PIN_ALIGNMENT = PASS
```

## Immutability and state

The Qlib environment freeze and both upstream source worktrees were unchanged.
The independent DVC environment retained 99 packages and the same deterministic
freeze SHA-256
`4c4c5cbb2d1ae319ed26642065464081ea1a35560e880e71e4e3468e7a19b699`.
Task rollback/build/wheelhouse directories were removed after validation.

```text
CONDA_DISCOVERY_PATH_CONFIGURATION_PROOF = PASS
PRE_ALIGNMENT_NATIVE_BRIDGE = PASS
FSSPEC_ALIGNMENT = PASS
RD_AGENT_DEPENDENCY_ALIGNMENT = PASS
RD_AGENT_RUNTIME_PROVENANCE = PASS
RD_AGENT_QLIB_PIN_ALIGNMENT = PASS
RD_AGENT_TO_QLIB_RUNTIME_BRIDGE = PASS
PERSISTENT_OS_PATH_CHANGED = NO
SHELL_PROFILE_CHANGED = NO
QLIB_PACKAGE_CHANGED = NO
DVC_ENV_CHANGED = NO
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

Remaining finite gaps:

1. US ragged-panel scenario configuration proof.
2. Candidate-to-P2 thin fail-closed identity contract.
3. P3 DVC-stage activation.
4. Autonomous-loop activation.

```text
CURRENT_NEXT = P3_US_RAGGED_SCENARIO_CONFIGURATION_PROOF_001
```
