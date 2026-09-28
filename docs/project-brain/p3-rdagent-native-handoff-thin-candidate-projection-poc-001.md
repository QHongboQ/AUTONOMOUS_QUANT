# P3 RD-Agent Native Handoff Thin Candidate Projection POC 001

Date: 2026-09-27

Status: `PASS_RDAGENT_NATIVE_HANDOFF_THIN_CANDIDATE_PROJECTION_POC`

## Baseline and upstream audit

PR #139 is merged at main `b3e1f061cefd8b03acfd7b563e8459b1cc6c26eb`;
the four retired Static17 execution/seal paths remain absent. The authorized
RD-Agent checkout is unchanged and clean at
`32b3d395e73d9db5eee3fe9063d69aec0fdc83bd`.

GitHub's exact comparison to current upstream
`484776c211e4fbbeef03e0ec00d6bbee7362a4f4` reports five commits and zero
changed files under `rdagent/app/qlib_rd_loop`, `rdagent/scenarios/qlib`, or
the Qlib/CoSTEER quant paths. The observed changes are release metadata, CI,
UI/log-server security, and unrelated data-science debugging. The project pin
therefore remains authoritative.

The existing US/PIT binding and both static configs are reused unchanged. The
existing DVC stage still invokes native
`/home/zhou/AQ_ENVS/rdagent/bin/rdagent fin_quant --loop-n 1`; AQ has no custom
RD loop, runner, or coder.

## Materializer audit and minimum leaf

The complete tracked repository contains no RD-Agent-to-Candidate-V3
materializer. The private historical `materialize_candidate_v3.py` is tightly
bound to the 17 Formulaic candidates, and the prior native Qlib handoff POC
only proved the Candidate V3 persisted-model shape. Classification:
`MISSING`.

`project_rdagent_candidate_v3.py` is the resulting pure 99-line leaf. It:

- accepts the seven explicit non-ID Candidate V3 fields;
- requires the RD_AGENT producer branch and frozen RD-Agent source SHA;
- requires a FINISHED Recorder and `task`, `params.pkl`, `dataset`, `pred.pkl`;
- hashes only the persisted model and prediction bytes needed by the existing
  RD-Agent artifact contract;
- computes Candidate ID with upstream `rfc8785==0.1.4`; and
- validates against the unchanged Candidate V1/V2/V3 schemas.

It cannot train, predict, backtest, rank, select, retry research, call an LLM,
manage Recorder lifecycle, or store registry state.

## Bounded native-Recorder proof

The POC reused Recorder `experiment_id=1`,
`run_id=49c5419261db4e0989943a13e2a61d3f`, previously created through pinned
Qlib `task_train`. It was not executed again. The projection is marked
`TEST_FIXTURE_NOT_REAL_CANDIDATE` in private evidence and was not submitted to
P2, P4, or P7.

```text
QLIB_RECORDER_FINISHED = YES
QLIB_TASK_PRESENT = YES
QLIB_PARAMS_PKL_PRESENT = YES
QLIB_DATASET_PRESENT = YES
QLIB_PRED_PRESENT = YES
PARAMS_PKL_SHA256 = 0ffb9976b713f739157a44205d4e24de095413ba7eb007570d16157f757b913d
CANDIDATE_ID = sha256:a03b044a72834cc1b77663e2fdeae10217ac119f417ab1e694355351f5f6dc51
CANDIDATE_V3_SCHEMA_VALID = YES
CANDIDATE_V3_IDENTITY_VALID = YES
PERSISTED_MODEL_BINDING_VALID = YES
```

Candidate V3's RD-Agent branch inherits V1's required
`serialized_model_artifact`, so persistence is represented directly by its
content/DVC identity. The literal `status=PERSISTED` union belongs to the
Formulaic branch. The private summary records the equivalent persisted state;
no schema or identity model was changed.

The fixed Candidate V3 dataset bundle continues to bind provider report,
calendar, all-instrument and PIT-instrument identities, date bounds, counts,
and DVC dependencies. Recorder `dataset` remains upstream runtime state and is
not copied into an AQ dataset store.

Private evidence:
`D:/AQ_DATA/P3/rdagent-native-handoff-thin-candidate-projection-poc-001/`.
`checksums.json` SHA-256 is
`902cb499d180f46886934d3d30feb52924c4414e697d7bff5e55992553710da6`.

## Verification and boundaries

Candidate V3 plus focused projection tests passed 12/12. RD-Agent US binding
tests passed 28/28. The focused suite rejects unfinished Recorders, absent
`params.pkl`, `dataset`, or `pred.pkl`, incorrect RD-Agent source identity,
wrong producer branch, and Candidate ID mismatch.

```text
EXISTING_US_BINDING_REUSED = YES
EXISTING_DVC_STAGE_REUSED = YES
EXISTING_CANDIDATE_V3_REUSED = YES
AQ_CUSTOM_CANONICALIZER = NO
AQ_DATASET_STORE = NO
AQ_P3_AUTONOMOUS_LOOP_LOC = 0
AQ_P3_TRAINING_ENGINE_LOC = 0
AQ_P3_RECORDER_ENGINE_LOC = 0
AQ_P3_MODEL_STORE_LOC = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
RD_AGENT_LLM_CALL_COUNT = 0
REAL_AUTONOMOUS_LOOP_COUNT = 0
REAL_MODEL_TRAINING_COUNT = 0
REAL_CANDIDATE_CREATED = 0
P2_V2_SEALED_OOS_ACCESSED = NO
P3_FIN_QUANT_003_MUTATED_OR_RETRIED = NO
CURRENT_DEVELOPMENT_NEXT = P3_RDAGENT_FIN_QUANT_AUTONOMOUS_LOOP_REACTIVATION_001
FINAL_CLASSIFICATION = PASS_RDAGENT_NATIVE_HANDOFF_THIN_CANDIDATE_PROJECTION_POC
```
