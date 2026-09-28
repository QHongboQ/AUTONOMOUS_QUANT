# P7 Static17 Scaffold Retirement 001

Date: 2026-09-27

Status: `PASS_STATIC17_SCAFFOLD_RETIRED_AUTONOMOUS_RD_DIRECTION_REBASED`

## Terminal study authority

The frozen static-17 equal-weight historical study is terminal:

```text
RESULT = STATIC_ENSEMBLE_RESEARCH_NOT_SUPPORTIVE
SCIENTIFIC_ATTEMPT_COUNT = 1
RERUN_ALLOWED = NO
POST_HOC_RESCUE_ALLOWED = NO
EVIDENCE_RECOVERY_COMMIT = 3da8c79d617eca0263f1e6c5dcae61f235d58338
```

The closeout at
`docs/project-brain/p7-successor-historical-static-ensemble-execution-closeout-001.md`
remains unchanged. The private sealed output root and checksums remain
unchanged. This task did not reopen outcome values or perform scientific
computation.

## Retired active-tree paths

| Path | Git blob at base | Bytes | Physical LOC | Reason |
|---|---:|---:|---:|---|
| `30-research-system/qlib/p7-native-ensemble/execute_historical_static_research.py` | `6f497c7137106447521f5abe2f8827338437dd90` | 30,563 | 591 | Closed original one-shot historical runner |
| `30-research-system/qlib/p7-native-ensemble/execute_successor_historical_static_research.py` | `f340a4323e4ad0ea279ac8e998e55dff7b48f8bf` | 50,575 | 1,287 | Closed successor one-shot runner; Execution 003 is terminal |
| `30-research-system/qlib/p7-native-ensemble/tests/test_execute_successor_historical_static_research.py` | `7cac61c9daebbe2755b04f9c7df4a43e032fb946` | 30,385 | 681 | Dedicated test for retired successor runner |
| `30-research-system/qlib/p7-native-ensemble/successor-one-shot-execution-provenance-seal.json` | `69cb6ad5f93b240cefc984724e389245ba528119` | 8,434 | 138 | Spent execution seal must not authorize a future run |

Every path is recoverable from
`3da8c79d617eca0263f1e6c5dcae61f235d58338`. The files were deleted rather
than relocated; Git history is the executable archive.

```text
DELETED_FROM_ACTIVE_TREE != SCIENTIFIC_HISTORY_DELETED
RETIRED_EXECUTION_RUNNER_COUNT = 2
RETIRED_DEDICATED_TEST_FILE_COUNT = 1
RETIRED_STALE_SEAL_COUNT = 1
STATIC17_ACTIVE_CODE_BYTES_BEFORE = 81138
STATIC17_ACTIVE_CODE_BYTES_AFTER = 0
STATIC17_ACTIVE_TEST_BYTES_BEFORE = 30385
STATIC17_ACTIVE_TEST_BYTES_AFTER = 0
ACTIVE_P7_RUNTIME_LOC_BEFORE = 2230
ACTIVE_P7_RUNTIME_LOC_AFTER = 352
```

## Preserved scientific evidence and thin runtime

The following immutable scientific evidence remains unchanged:

- `historical-static-ensemble-research-protocol.json`
- `successor-historical-static-ensemble-research-protocol.json`
- `successor-label-observable-input-contract.json`
- `historical-static-ensemble-inconclusive-closeout-result-reference.json`
- `historical-static-ensemble-research-execution-result-reference.json`

The active P7 runtime is limited to:

- `time_effective_roster_handoff.py` — 198 physical LOC;
- `session_local_router.py` — 55 physical LOC;
- `average_ensemble_boundary.py` — 99 physical LOC.

These retain only external P2/P4 authorization handoff, time-effective roster
policy, fail-closed Candidate/session validation, and the Qlib
AverageEnsemble boundary. `test_split_feasibility.py` remains because it
directly validates reusable public skfolio WalkForward and
CombinatorialPurgedCV split behavior rather than either retired runner.

## Reference audit

Before deletion, all exact references were classified:

- runtime/self references in the two runners and the dedicated runner test:
  executable dependencies, deleted together;
- references in provenance-seal and historical Project Brain reports:
  immutable historical evidence, retained in documentation and Git history;
- current Project Brain routing to further Static17 execution: obsolete and
  replaced by the upstream autonomous-RD direction.

After deletion, no active runtime file imports, executes, or names a retired
runner or the spent seal. Historical Project Brain text may continue to name
paths and hashes as evidence.

## Current upstream ownership evidence

Official source was inspected without installation or execution.

Microsoft RD-Agent HEAD
[`484776c211e4fbbeef03e0ec00d6bbee7362a4f4`](https://github.com/microsoft/RD-Agent/tree/484776c211e4fbbeef03e0ec00d6bbee7362a4f4)
contains:

- [`factor.py`](https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/app/qlib_rd_loop/factor.py): `FactorRDLoop`, `step_n`, `loop_n`, session load/resume, factor execution, and feedback;
- [`quant.py`](https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/app/qlib_rd_loop/quant.py): `QuantRDLoop`, factor/model proposal and coding paths, factor/model runners, feedback, `step_n`, `loop_n`, and session load/resume;
- [`conf.py`](https://github.com/microsoft/RD-Agent/blob/484776c211e4fbbeef03e0ec00d6bbee7362a4f4/rdagent/app/qlib_rd_loop/conf.py): Qlib factor, model, and quant scenario integration plus runner/coder/summarizer ownership;
- official CLI commands `rdagent fin_factor` and `rdagent fin_quant`.

AlphaGen HEAD
[`259687e8f316994426416c530a94842a2fe6405e`](https://github.com/ICT-FinD-Lab/AlphaGen/tree/259687e8f316994426416c530a94842a2fe6405e)
contains `alphagen`, `alphagen_qlib`, and `alphagen_llm`; its documented
[`scripts/llm_only.py`](https://github.com/ICT-FinD-Lab/AlphaGen/blob/259687e8f316994426416c530a94842a2fe6405e/scripts/llm_only.py)
provides iterative LLM-only alpha generation.

```text
PRIMARY_AUTONOMOUS_RD_OWNER = MICROSOFT_RD_AGENT_Q
RDAGENT_FIN_FACTOR_VERIFIED = YES
RDAGENT_FIN_QUANT_VERIFIED = YES
RDAGENT_QUANTRDLOOP_VERIFIED = YES
RDAGENT_LOOP_N_VERIFIED = YES
RDAGENT_SESSION_RESUME_VERIFIED = YES
ALPHAGEN_LLM_ITERATIVE_GENERATION_VERIFIED = YES
```

## Ownership and safety boundary

RD-Agent Quant owns hypothesis generation, factor and model proposal, coding
iteration, experiment feedback, and joint factor/model research orchestration.
Qlib owns datasets, training, prediction, Recorder, backtest, signal
evaluation, and workflow mechanics. AlphaGen owns formulaic-alpha mining, RL
alpha-pool research, and optional LLM iterative generation.

AQ owns only PIT data authority, Candidate normalization/identity, the P2
one-way certification boundary, P4 lifecycle authority, P7 cross-family
authorization and ensemble policy, and P8+ capital/risk authority. Multiple
factors from one mechanism or data surface do not automatically constitute
independent families.

Autonomous RD may iterate over train, validation, research backtests, and
research walk-forward evidence. P2 V2 sealed OOS cannot feed back into factor
or model generation:

```text
AUTONOMOUS_RESEARCH_LOOP -> CANDIDATE -> P2_ONE_WAY_CERTIFICATION_BOUNDARY
AQ_CUSTOM_RESEARCH_LOOP_PRESENT = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
STATIC_17_RERUN_ALLOWED = NO
NEXT_TASK = AUTONOMOUS_QUANT_P3_P7_RDAGENT_FIN_QUANT_THIN_ADAPTER_POC_001
```

## Validation

The six retained P7 boundary test files passed 49/49 tests using the existing
pinned environments. Ruff and `git diff --check` passed. No environment was
installed or mutated.

```text
REMAINING_P7_THIN_RUNTIME_TESTS = 49/49 PASS
RUFF = PASS
ACTIVE_RUNTIME_REFERENCES_TO_RETIRED_EXECUTABLES = 0
ENVIRONMENT_MUTATED = NO
```
