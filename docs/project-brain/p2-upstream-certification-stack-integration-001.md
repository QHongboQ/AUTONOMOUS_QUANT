# P2 Upstream Certification Stack Integration 001

Date: 2026-09-13

Status: **COMPLETE WITH RECORDED BLOCKERS**

Classification: **TECHNICAL INTEGRATION ONLY — NO MODEL OR STRATEGY CERTIFIED**

## Authority and scope

```text
TASK = AUTONOMOUS-QUANT-P2-UPSTREAM-CERTIFICATION-STACK-INTEGRATION-001
BASE_MAIN = a7986b67f2bd0ca7488969ad9ebd3fb931e603fb
BRANCH = agent/p2-upstream-certification-stack-integration-001
UPSTREAM_FIRST = REQUIRED
P2_CERTIFICATION = IN_PROGRESS
CURRENT_NEXT = P2_CERTIFICATION_PROTOCOL_PREREGISTRATION_001
```

This task wired the already-selected certification components through their
public interfaces. It did not create a certification decision, select a model,
run a tournament, change market data, or remediate the provider. Private
runtime evidence is retained under
`D:\AQ_DATA\P2\upstream-certification-stack-integration-001` and is not tracked
by Git.

## Frozen input

```text
QLIB_PROVIDER_PATH = D:\AQ_DATA\P2\qlib-native-ragged-panel-001\qlib_data
HISTORY = 2015-01-02 THROUGH 2024-12-31
SECURITY_IDENTITIES = 730
MEMBERSHIP_RANGES = 745
MEMBER_SESSION_ROWS = 1267963
OBSERVED_SAFE_ROWS = 1224788
MASKED_ROWS = 43175
PROVIDER_BUILD_REPORT_SHA256 = eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142
```

The integration made no market-data network request and did not modify the
provider bytes.

## Upstream integration result

| Owner | Version / pin | Public interface exercised | Result |
|---|---|---|---|
| Microsoft Qlib | `0.9.8.dev26`, source `2fb9380b342556ddb50a4b24e4fe8655d548b2b8` | `qlib.init`, `D.instruments`, `D.list_instruments`, `D.features`, `DatasetH`, `RaggedAlpha158`, `ExpressionDFilter`, `DropnaLabel`, `LGBModel`, prediction, `Exchange`, backtest and `PortAnaRecord` entry surfaces, `Recorder` | PASS |
| MLflow through Qlib | `3.16.0` | `MLflowExpManager`, `R.start`, parameter and artifact logging | PASS |
| skfolio | `1.0.6` | `WalkForward`, `CombinatorialPurgedCV` | PASS |
| arch | `8.0.0` | `SPA`, `RealityCheck`, `StepM`, `MCS` | PASS |
| DVC | `3.67.1` | stage dependencies, output seal, lockfile replay | PASS |
| exchange_calendars | required `4.13.2` | `get_calendar("XNYS")` | BLOCKED_ENVIRONMENT |
| Pandera | required `0.33.1` | `pandera.pandas.DataFrameSchema` | BLOCKED_ENVIRONMENT |

The existing authorized persistent runtimes do not expose
exchange_calendars 4.13.2 or Pandera 0.33.1. The task contract required the
missing environments to be recorded instead of installed, so the retained
validation probe was not executed. This leaves the complete cross-upstream
flow `PARTIAL`; it does not authorize an AQ replacement calendar or schema
engine.

## Qlib and MLflow evidence

The bounded workload selected the first eight stable security-identity
instruments whose accepted ranges span the fixed 2018-01-02 through 2019-06-28
probe interval. Qlib produced 124 daily evidence rows. The handoff SHA-256 is:

```text
2f68240b9895c50570ebc2ce6453e3547754cf6a5bf9820a55674ab8a99a774a
```

The same hash was consumed by skfolio and arch. The Qlib recorder
`dd91ea0afb2c44d4aa5cd140fe5b7e9b` finished successfully in the SQLite-backed
MLflow experiment and logged configuration, provenance, and one bounded
technical artifact.

An initial probe ordering placed `LGBModel.fit` before the explicit Qlib
recorder context, so Qlib opened its default recorder and a later `R.start`
encountered an already-active MLflow run. This exact failure is preserved in
the blocker ledger as non-blocking `PASS_WITH_LIMITATION`. The permitted
same-upstream configuration correction moved model execution and evidence
logging into one public `R.start` context. No upstream source or package was
changed.

## Temporal CV and multiple-testing interfaces

skfolio returned nine `WalkForward` splits with train size 30, test size 10,
and purge size 2, and ten `CombinatorialPurgedCV` splits with five folds, two
test folds, purge size 2, and embargo size 2. The probe only verified upstream
split construction and train/test disjointness; certification policy retains
split authority.

arch executed `SPA`, `RealityCheck`, `StepM`, and `MCS` on the two-column
Qlib-derived loss evidence. Each interface completed twice with its explicit
seed and reproduced the same result. These are statistical interface results,
not profitability or promotion evidence.

## DVC evidence ownership

The `p2_upstream_certification_stack_integration` DVC stage records external
dependency identities for the accepted provider report and private Qlib,
skfolio, and arch reports, plus the repository blocker ledger. The generated
seal is ignored by Git. A first `dvc repro` generated the seal and updated
`dvc.lock`; an immediate second replay reported the stage unchanged and all
data and pipelines up to date.

```text
QLIB_REPORT_SHA256 = 67e910e73b860939195b9142cde134c04528d14e554d8379f2563079e7f7c0eb
SKFOLIO_REPORT_SHA256 = 0d1d5a9984bc419367d612a04ad778b5b4fbc63be5ee8cf2fce0090f6831fa1b
ARCH_REPORT_SHA256 = 5d00e5b41c81660c6a1490822469cc7afa09ffc1bce4e4b1c0ec9d088c2b254b
BLOCKER_LEDGER_SHA256 = 8648d03746c77fd283e2a2a67818a0a370f86e685ec6f6605ad05ac2d620e913
DVC = PASS
```

## Blockers

The authoritative machine-readable ledger is
`40-certification-system/upstream-stack-integration/blockers.json`.

```text
RECORDED_ISSUE_COUNT = 3
P2_BLOCKING_BLOCKER_COUNT = 2
EXCHANGE_CALENDARS = BLOCKED_ENVIRONMENT
PANDERA = BLOCKED_ENVIRONMENT
```

The two P2-blocking items require separately authorized pinned runtimes before
their retained public-interface validation probe can run. They do not create
an automatic repair task.

The existing Qlib dataset-adapter regression suite passed 25 of 25 tests from
its expected Windows launcher, including its public Qlib API compatibility
probe. All five new bounded probe/seal scripts parsed successfully, and the
blocker-ledger field/status contract passed its static check.

## Architecture and non-actions

```text
AQ_NEW_GENERIC_ENGINE_COUNT = 0
AQ_CUSTOM_CV_ENGINE = NO
AQ_CUSTOM_STATISTICS_ENGINE = NO
AQ_CUSTOM_BACKTESTER = NO
AQ_CUSTOM_EXPERIMENT_DB = NO
AQ_CUSTOM_DATA_ENGINE = NO
AQ_CUSTOM_OPTIMIZER = NO
AQ_CUSTOM_BOOTSTRAP_ENGINE = NO
NEW_DATA_PROVIDER = NO
MARKET_DATA_NETWORK_CALLS = 0
BROKER_CALLS = 0
LLM_CALLS = 0
RD_AGENT_EXECUTED = NO
P2_DATA_PROVIDER_REMEDIATION = CLOSED
RESEARCH_RUNTIME_EXTERNAL_API_COUNT = 0
PR_CREATED = NO
MERGED = NO
```

## Final state

```text
QLIB = PASS
MLFLOW_VIA_QLIB = PASS
EXCHANGE_CALENDARS = BLOCKED
PANDERA = BLOCKED
SKFOLIO_WALKFORWARD = PASS
SKFOLIO_CPCV = PASS
ARCH_SPA = PASS
ARCH_REALITY_CHECK = PASS
ARCH_STEPM = PASS
ARCH_MCS = PASS
DVC = PASS
FULL_CROSS_UPSTREAM_FLOW = PARTIAL
FINAL_CLASSIFICATION = PASS_WITH_RECORDED_BLOCKERS
CURRENT_NEXT = P2_CERTIFICATION_PROTOCOL_PREREGISTRATION_001
```
