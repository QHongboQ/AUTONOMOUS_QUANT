# P3 Direct Runtime and Post-Run DVC Experiment Authority Freeze 001

Task: `AUTONOMOUS-QUANT-P3-DIRECT-RUNTIME-POSTRUN-DVC-EXPERIMENT-AUTHORITY-FREEZE-001`

Status: `CURRENT AUTHORITY — FROZEN BEFORE THE FIRST DIRECT P3 RUN`

## Ownership and runtime topology

```text
RD_AGENT_OWNER = UPSTREAM_WHOLE_AUTONOMOUS_RESEARCH
QLIB_OWNER = UPSTREAM_WHOLE_QUANT_RUNTIME
QLIB_MLFLOW_OWNER = UPSTREAM_WHOLE_RUN_LINEAGE
DVC_OWNER = UPSTREAM_LEAF_REPRODUCIBILITY_ONLY
AQ_OWNER = THIN_CONFIGURATION_BINDING_CONTRACT_GOVERNANCE_ONLY
```

The only authorized P3 RD-Agent execution topology is:

```text
Windows CurrentUser SecureString/DPAPI secret boundary
        ↓
process-local child environment / WSLENV
        ↓
WSL-native clean AQ checkout
        ↓
official pinned RD-Agent executable
        ↓
rdagent fin_quant --loop-n N
        ↓
official RD-Agent autonomous loop
        ↓
official Qlib / Recorder / MLflow
```

```text
DVC_IS_RUNTIME_LAUNCHER = NO
DVC_IS_RESEARCH_LOOP_OWNER = NO
DVC_IS_RUN_LINEAGE_OWNER = NO
DVC_IS_REPRODUCIBILITY_OWNER = YES
DVC_TEMP_EXECUTOR_FOR_P3_RUNTIME = RETIRED_AS_P3_RUNTIME_LAUNCH_PATH
```

`dvc exp run --temp ... p3_rdagent_us_quant_research` is retired only as a
P3 process-launch path. DVC remains the selected upstream reproducibility
owner; it is not defective and is not removed. The existing stage name
`p3_rdagent_us_quant_research` remains unchanged as the declarative
reproducibility definition.

## Declarative command authority

```text
DVC_DECLARED_COMMAND_ROLE = DECLARATIVE_REPRODUCIBILITY_AUTHORITY
DVC_COMMAND_EXECUTION_AUTHORITY = NO_FOR_P3_RUNTIME
```

The direct command must be semantically equivalent to the declared stage
command for the pinned RD-Agent executable, LiteLLM backend and models,
reasoning effort, token and retry policy, US/PIT binding, factor source,
dates, workspace, trace, pickle cache, MLflow URI, and run namespace. DVC
records that declared contract after the direct run; it does not initiate it.

## One-run post-run registration procedure

For each completed direct RD-Agent run:

1. Choose one unique fresh namespace and use it for the direct run.
2. Require the immutable Qlib/MLflow run and expected run root to be complete.
3. Temporarily project that exact namespace into
   `30-research-system/rd-agent/config/p3-runtime-params.yaml`.
4. Run `dvc commit --force p3_rdagent_us_quant_research`.
5. Run `dvc exp save --name <exact-run-namespace>`.
6. Verify the saved DVC experiment contains the namespace, `dvc.lock`, stage
   lock entry, output identity, and dependency identities.
7. Restore the ordinary source workspace to its committed default namespace
   and verify it is clean.

The saved DVC experiment is an experiment snapshot, not a normal branch
commit. It retains the post-run configuration and lock content needed for
Candidate V3 reproducibility evidence without a normal Git commit per run.

```text
DIRECT_RUNTIME_NAMESPACE = DVC_REGISTERED_NAMESPACE
NO_LATEST_RUN_SELECTION = REQUIRED
NO_RUN_ROOT_REUSE = REQUIRED
```

## Post-run boundary and failure domains

DVC post-run registration owns dependency, dataset, configuration, run-root
output, stage-lock, and reproducibility-snapshot identities. It does not own
secret injection, LLM routing, RD-Agent lifecycle or checkpoints, Qlib or
MLflow execution, hypothesis generation, implementation, or feedback.

```text
DIRECT_RDAGENT_FAILURE = RESEARCH_RUNTIME_FAILURE
DVC_POSTRUN_FAILURE = REPRODUCIBILITY_CANDIDATE_SEALING_FAILURE
```

A DVC post-run failure must not trigger an RD-Agent rerun, Qlib retraining,
factor/model regeneration, or DeepSeek retry. Completed immutable runtime
artifacts remain the source evidence while registration is repaired
separately.

## Candidate and AlphaGen compatibility

RD-Agent Candidate V3 continues to inherit the existing Candidate V1 DVC
artifact identities:

```text
dvc_stage_name = p3_rdagent_us_quant_research
dvc_lock_file_sha256 = REQUIRED
dvc_stage_lock_entry_sha256 = REQUIRED
dvc_run_root_output_identity = REQUIRED
p3_dvc_dependency_identities = REQUIRED
CANDIDATE_V3_SCHEMA_CHANGE_REQUIRED = NO
CANDIDATE_V4_REQUIRED = NO
EXISTING_FORMULAIC_CANDIDATES_MUTATED = NO
```

AlphaGen remains unchanged precedent: AlphaGen research, then Qlib
evaluation, then later DVC reproducibility sealing. No custom AQ runtime,
namespace, experiment-registry, workflow, launcher, adapter, or seal engine
is authorized.

```text
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CUSTOM_AQ_RUNTIME_CODE_REQUIRED = NO
ALPHAGEN_SOURCE_CHANGED = NO
```

## Evidence and next boundary

The DVC 3.67.1 disposable native POC established that manually created
external `cache: false` output can be registered by `dvc commit --force`, then
preserved by `dvc exp save`, without either operation executing the stage.
The lock retains identities, not output-byte storage authority. Official DVC
references are [commit](https://doc.dvc.org/command-reference/commit) and
[exp save](https://doc.dvc.org/command-reference/exp/save). A manual commit
does not itself attest execution; the existing direct-run trace, Qlib/MLflow
recorder, runtime, dataset, and content identities remain required Candidate
evidence.

The next authorized activity is one fresh direct official RD-Agent
`fin_quant` smoke with DVC absent from the runtime critical path. Only after a
successful completed run may native DVC `commit --force` and `exp save`
register the completed artifacts.
