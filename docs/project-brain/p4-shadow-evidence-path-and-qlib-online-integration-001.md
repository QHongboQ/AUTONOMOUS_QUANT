# P4 Shadow Evidence Path and Qlib Online Integration 001

Status: **PASS — TEST FIXTURE MECHANISM ONLY**

Date: 2026-09-17

## Classification and authority

```text
TASK = AUTONOMOUS-QUANT-P4-SHADOW-EVIDENCE-PATH-AND-QLIB-ONLINE-INTEGRATION-001
BASE_HEAD = f5520103a2b4656ad864351e3797e8eec9b871bd
FIXTURE_CLASSIFICATION = TEST_FIXTURE_NOT_REAL_SHADOW
FIXTURE_SHADOW_STATUS = INCOMPLETE
REAL_SHADOW_EVIDENCE_CREATED = NO
REAL_LIFECYCLE_TRANSITION_EXECUTED = NO
P2_PROTOCOL_MODIFIED = NO
```

The run proves the Shadow evidence mechanism and nothing more. It is not a
Candidate, Certified artifact, prospective Shadow, Champion, production
monitor, or trading result. The synthetic certification identity is explicitly
`TEST_FIXTURE_NOT_REAL_EVIDENCE`, and no result from the 17 Formulaic Alpha
Candidates was read.

## Upstream ownership and real execution

```text
QLIB_VERSION = 0.9.8.dev26
MLFLOW_VERSION = 3.16.0
DVC_VERSION = 3.67.1
QLIB_ONLINE_MANAGER = INTEGRATED_UPSTREAM
QLIB_ROLLING_STRATEGY = INTEGRATED_UPSTREAM
QLIB_ROLLING_GEN = INTEGRATED_UPSTREAM
QLIB_TRAINER_R = INTEGRATED_UPSTREAM
QLIB_ONLINE_TOOL_R = INTEGRATED_UPSTREAM
QLIB_RECORDER_SIGANA = INTEGRATED_UPSTREAM
AQ_ONLINE_MODEL_ENGINE = NO
AQ_ROLLING_ENGINE = NO
AQ_TRAINER = NO
AQ_METRIC_ENGINE = NO
AQ_STATE_DATABASE = NO
AQ_WORKFLOW_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

The private fixture invoked the public upstream classes directly:

- `qlib.workflow.online.manager.OnlineManager`
- `qlib.workflow.online.strategy.RollingStrategy`
- `qlib.workflow.task.gen.RollingGen(step=21)`
- `qlib.model.trainer.TrainerR`
- `qlib.workflow.online.utils.OnlineToolR`
- Qlib Recorder/MLflow, `SignalRecord`, and `SigAnaRecord`

AQ did not subclass or reproduce those components. The only new executable
repository code is one bounded identity seal; it neither trains nor schedules
models and does not calculate RankIC.

## Data firewall and fixture shape

```text
MODEL = qlib.contrib.model.linear.LinearModel(estimator=ols)
DATASET = DatasetH + RaggedAlpha158/Alpha158DL
TRAIN = 2019-01-02 through 2020-06-30
VALID = 2020-07-01 through 2020-12-31
ONLINE = 2021-01-04 through 2021-03-04
ROLLING_STEP = 21_XNYS_SESSIONS
INSTRUMENT_COUNT = 12
UNIVERSE_SELECTION = LEXICOGRAPHIC_SECURITY_IDENTITY_FROM_PIT_MEMBERS_ACTIVE_2019_01_02
UNIVERSE_CLASSIFICATION = MECHANISM_TEST_ONLY
MAX_PREDICTION_DATE = 2021-03-04
MAX_LABEL_DATE = 2021-03-04
HISTORICAL_TEST_ROWS_ACCESSED = 0
SEALED_OOS_ROWS_ACCESSED = 0
REAL_ALPHAGEN_CANDIDATE_ARTIFACTS_ACCESSED = 0
```

The subset is identity/order bounded only. It uses no return, RankIC,
liquidity, future-membership, or Candidate-performance selection. The provider
contains later history, but all configured market/label intervals and emitted
prediction/label indices end before the historical TEST start of 2022-01-03.
The manager was placed in the upstream simulation status for the bounded
fixture, preventing its unbounded live `update_online_pred()` path from reading
the provider's latest date.

## Online history, tags, and signal evidence

```text
QLIB_ONLINE_HISTORY_TIMEPOINTS = 2
QLIB_RECORDER_COUNT = 2
QLIB_ONLINE_RECORDER_COUNT = 1
QLIB_OFFLINE_RECORDER_COUNT = 1
QLIB_ONLINE_TAG_IS_P4_SHADOW_AUTHORITY = NO
QLIB_EXPERIMENT_ID = 1
QLIB_SELECTED_RECORDER_ID = 344e70a13c14478e80f61500a4412081
MLFLOW_EXPERIMENT_ID = 1
MLFLOW_SELECTED_RUN_ID = 344e70a13c14478e80f61500a4412081
PREDICTION_SHA256 = 8d3b8910fa131b2c0639cb4682dfb49739e02703c58f6f43184ac00b0ac3caaa
SIGANA_RIC_SHA256 = a7a387a1fa8ecc3b417ba34cf4dfb1d2a73f70df54a3e89d8643e38439cb4ff5
AQ_RANKIC_COMPUTATION = NO
```

`OnlineManager.history` records 2021-01-04 and 2021-02-03. On replacement,
the older Recorder is tagged `offline` and the selected Recorder is tagged
`online` by `OnlineToolR`. Those tags describe Qlib runtime status only; they
carry no P4 lifecycle authority. Qlib `SigAnaRecord` performed prediction-label
alignment and persisted `sig_analysis/ric.pkl` in the MLflow artifact tree.

## Shadow contract and epoch firewall

`ShadowEvidenceV1` is preserved for historical synthetic fixtures. New
`ShadowEvidenceV2` adds the explicit classifications
`TEST_FIXTURE_NOT_REAL_SHADOW` and `PROSPECTIVE_ZERO_CAPITAL_SHADOW`.
`COMPLETE_PASS` and `COMPLETE_FAIL` both require an outcome/evaluation
identity. Real P2 evidence cannot bind V1, and real promotion requires a
prospective V2 `COMPLETE_PASS` with outcome identity and consistent
Qlib/MLflow/P2 identities.

```text
SHADOW_CONTRACT_VERSION = ShadowEvidenceV2
SHADOW_CONTRACT_FAIL_CLOSED = PASS
REAL_COMPLETE_PASS_WITHOUT_OUTCOME_EVIDENCE = STRUCTURALLY_IMPOSSIBLE
PRE_EPOCH_PRODUCTION_DECAY_EVALUATION = REJECTED
PRODUCTION_POLICY_EFFECTIVE_EPOCH = 2026-10-01
P4_PRE_EPOCH_PRODUCTION_EVIDENCE = INELIGIBLE
```

The fixture remains `INCOMPLETE` because it has no real P2 certification, is
not prospective after the production policy epoch, and is explicitly a test
fixture. Calling the existing V2 degradation policy with its 2021 current
window returns `REJECT_TRANSITION / DECAY_POLICY_NOT_PREREGISTERED`. No real
Frouros policy loop or lifecycle decision was emitted.

## Zero-capital and DVC evidence

```text
ZERO_CAPITAL_SHADOW = YES
BROKER_CALLS = 0
ORDER_COUNT = 0
CAPITAL_ALLOCATED = 0
BACKTEST_EXECUTED = NO
PORTFOLIO_STRATEGY_EXECUTED = NO
DVC_STAGE_NAME = p4_shadow_evidence_path_fixture_seal
FIRST_DVC_REPRO = PASS
SECOND_DVC_REPRO = UNCHANGED_DATA_AND_PIPELINES_UP_TO_DATE
DVC_YAML_SHA256 = 60800afcb2e20109dc0cb3d3a633d1a18da55cfacd997bcbc0d38d64695aefe0
DVC_LOCK_SHA256 = 7eace5345b21be674c69c8d84e44172ee8a40da186b3a997ce50eaa40dfcee2a
DVC_STAGE_LOCK_ENTRY_IDENTITY = sha256:0b249a23159b91889b0b97a32f109b73b7b6a1896efb9d889046b7367b48837d
DVC_SEAL_OUTPUT_SHA256 = ea59eb9291bf9ea8fd729c10e90efd5f2bccbbd789e3d61a19ef50f0def8b6bc
```

DVC binds the fixed task configuration, Qlib/MLflow identities, online
history, tags, prediction and RankIC artifacts, Shadow fixture, zero-capital
attestation, pre-epoch rejection, and policy sources. It owns reproducibility,
not Shadow meaning. No database, registry, scheduler, event store, or artifact
store was introduced by AQ.

## Verification and private evidence

```text
RESIDUAL_POLICY_TESTS = 52/52 PASS
SHADOW_ONLINE_AND_SEAL_TESTS = 9/9 PASS
FROUROS_RUNNER_TESTS = 8/8 PASS
FROUROS_FULL_ADAPTER_TESTS = 1/1 PASS
QLIB_EXPORTER_AND_IDENTITY_PROJECTION_TESTS = 25/25 PASS
TOTAL_TEST_RESULT = 95/95 PASS
NEW_DEPENDENCY_COUNT = 0
QLIB_ENV_PACKAGE_MUTATION = NO
FROUROS_ENV_PACKAGE_MUTATION = NO
DVC_ENV_PACKAGE_MUTATION = NO
```

```text
PRIVATE_ROOT = D:/AQ_DATA/P4/shadow-evidence-path-and-qlib-online-integration-001
SHADOW_FIXTURE_SHA256 = 5f1eb7dd740e810d870bdd0850f2ee14f316fd5c9d120f20cd51707158dcc5fb
PRIVATE_REPORT = D:/AQ_DATA/P4/shadow-evidence-path-and-qlib-online-integration-001/integration_summary.json
PRIVATE_REPORT_SHA256 = 19e3cd11612ff98da65e9660a6e74a99829bfc241ae1e8d02cc1ad25420cb073
```

## Result and next

```text
P4_SHADOW_EVIDENCE_PATH_AND_QLIB_ONLINE_INTEGRATION = PASS
P4_SHADOW_MECHANISM = PASS_TEST_FIXTURE_ONLY
P4_REAL_CERTIFIED_ARTIFACTS_CREATED = 0
P4_REAL_SHADOW_ARTIFACTS_CREATED = 0
P4_REAL_CHAMPIONS_CREATED = 0
P4_REAL_DEGRADED_ARTIFACTS_CREATED = 0
P4_REAL_RETIRED_ARTIFACTS_CREATED = 0
P4_REAL_RESEARCH_REQUESTS_CREATED = 0
FORMULAIC_ALPHA_P2_PROTOCOL_EXPANSION = STILL_REQUIRED
CURRENT_NEXT = P2_FORMULAIC_ALPHA_CERTIFICATION_PROTOCOL_EXPANSION_001
```

This task does not begin that P2 work.
