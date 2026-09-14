# P2 Certification Historical Rehearsal 001

Status: **COMPLETE / REJECTED BY FROZEN STATISTICAL GATES**

The Qlib end-of-frozen-calendar blocker recorded below was subsequently closed
through Qlib's native future-calendar storage contract. The completed rehearsal
did not pass all mandatory Protocol V1 gates and is therefore `REJECTED`. It did
not certify a model or strategy.

This task activated `P2_CERTIFICATION_PROTOCOL_V1`, executed each frozen model
exactly once through Microsoft Qlib, and stopped at a genuine Qlib end-of-
calendar backtest boundary before any strategy report completed. No protocol,
provider, threshold, upstream package, or historical date was changed to make
the run pass.

## Historical initial blocked run

The following sections preserve the first run and its exact blocker as
historical evidence.

### Authority and activation

```text
BASE_MAIN = 8cd703b4108d2e377d146de8384b63c0355e93a6
PROTOCOL_VERSION = P2_CERTIFICATION_PROTOCOL_V1
PROTOCOL_SHA256_CANONICAL_LF = a9aed881c229f9eb7f85fa23b866168a55dc9c00be3c3b178d91a4af20451dfb
PROTOCOL_UNCHANGED = YES
FREEZE_MERGE_SHA = 8cd703b4108d2e377d146de8384b63c0355e93a6
FREEZE_MERGED_AT_UTC = 2026-09-14T02:46:13Z
CALENDAR = exchange_calendars 4.13.2 / XNYS
SEALED_OOS_START_SESSION = 2026-09-14
ACTIVATION_SHA256 = d1ac67558f59d917eb71d666e48967f8f20bafc48bfc1ff616b7c85e262eef54
MINIMUM_SEALED_OOS_SESSIONS = 126
EARLY_RESULT_ACCESS = PROHIBITED
ONE_SHOT_RELEASE = YES
```

`exchange_calendars.get_calendar("XNYS")` showed the 2026-09-14 market open
at 13:30 UTC, strictly after the 02:46:13 UTC merge time, so 2026-09-14 is the
first qualifying session. The activation fact is separate from Protocol V1
and contains only the ten authorized fields.

The Windows checkout uses CRLF worktree conversion for the JSON text. Its
Git/canonical-LF content identity is the frozen SHA above, and the protocol has
no Git diff. This is the repository's established cross-Windows/WSL identity
rule, not a protocol mutation.

### Frozen data and Qlib execution

The existing provider at
`D:\AQ_DATA\P2\qlib-native-ragged-panel-001\qlib_data` was reused without a
rebuild, refresh, or byte mutation.

```text
HISTORY = 2015-01-02 THROUGH 2024-12-31
SECURITY_IDENTITIES = 730
MEMBERSHIP_RANGES = 745
MEMBER_SESSION_ROWS = 1267963
OBSERVED_SAFE_ROWS = 1224788
MASKED_ROWS = 43175

QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
TRAIN = 2015-04-01 THROUGH 2019-12-31
VALID = 2020-01-01 THROUGH 2021-12-31
HISTORICAL_REHEARSAL_TEST = 2022-01-03 THROUGH 2024-12-31
```

Qlib `DatasetH`, `RaggedAlpha158`, `ExpressionDFilter`, `DropnaLabel`, model
classes, `SignalRecord`, `SigAnaRecord`, Recorder, and SQLite-backed
`MLflowExpManager` remained the upstream owners. Both model workloads finished
once; neither will be retrained merely to address the backtest boundary.

| Evidence | LightGBM primary | Linear OLS control |
|---|---:|---:|
| Training | PASS | PASS |
| Prediction rows | 375597 | 375597 |
| Prediction SHA-256 | `7af735fff6b07eb9be4b686776ffd53b496555cb5477bca641dfc9e4f521d7e7` | `26c3433faa58a64914393fe13eac169d9ce86dbbe86f16dfb2b24fbd64139dab` |
| IC | 0.0010258791706427974 | 0.004495286076061295 |
| ICIR | 0.011948140851803103 | 0.033797021966734814 |
| Rank IC | -0.0009483900816399625 | 0.00717181568549117 |
| Rank ICIR | -0.010901812505278316 | 0.05098079239768778 |

```text
PRIMARY_RECORDER_ID = 734ffa5ec01449f6b8a6696880d825bf
CONTROL_RECORDER_ID = d6035e318a0640da876e52d587137e7c
MLFLOW_SQLITE_SHA256 = e7d553c2d50b07e818983cc7f3a8e25f3dd905edfba9a23a0297c59ef1132d10
```

These signal statistics are rehearsal evidence only. They do not certify a
model or authorize strategy selection.

### Exact upstream blocker

The first attempted base strategy was `LGB_50_5`. No complete strategy report
or performance result was persisted.

First, the convenience wrapper
`qlib.contrib.evaluate.backtest_daily(..., benchmark=None)` converted `None`
to an empty benchmark configuration. The pinned legacy `PortfolioMetrics`
then applied its `SH000300` default and rejected the absent index. Read-only
source inspection confirmed that Qlib's explicit public Account boundary does
support `benchmark_config={"benchmark": None}`. The run therefore continued
without retraining through Qlib's own `Account`, `Exchange`,
`SimulatorExecutor`, `TopkDropoutStrategy`, and `backtest_loop`; no benchmark
series or custom backtester was introduced.

That public path reached the final frozen session and then failed exactly at:

```text
UPSTREAM = Microsoft Qlib 0.9.8.dev26
INTERFACE = qlib.backtest.backtest_loop
INPUT = LGB_50_5 / BASE / 2022-01-03 THROUGH 2024-12-31 / benchmark None
ERROR = IndexError: index 2516 is out of bounds for axis 0 with size 2516
BOUNDARY = TopkDropoutStrategy.generate_trade_decision
           -> TradeCalendarManager.get_step_time
           -> self._calendar[calendar_index + 1]
BLOCKING_STATUS = P2_HISTORICAL_REHEARSAL_BLOCKING
```

The frozen provider calendar ends on the exact frozen rehearsal end session.
Qlib requests the following calendar element when generating that final
session's decision. The contract forbids all obvious workarounds in this task:
mutating the provider calendar, shortening the rehearsal to 2024-12-30,
fabricating a future session, patching Qlib, or writing a custom backtester.
The full traceback and input are sealed privately in
`D:\AQ_DATA\P2\certification-historical-rehearsal-001\qlib\qlib-rehearsal-blocker.json`
with SHA-256
`932fa50f9f86958965d1ccf04adc66b5ad340fb65ef7e10f351c13e3c07a3d8a`.

### Dependent evidence and reproducibility

Because no Qlib daily portfolio report completed, the following paths were
not executed and remain `BLOCKED`, not failed statistical gates:

- eight base strategy reports;
- skfolio WalkForward and CombinatorialPurgedCV;
- arch SPA, RealityCheck, StepM, and MCS;
- base/2x/3x cost evidence;
- parameter-robustness and regime reductions;
- Pandera performance-table and XNYS-date validation.

The DVC stage `p2_certification_historical_rehearsal` seals Protocol V1,
activation, provider report, both prediction artifacts, the SQLite MLflow
record, blocker record, and fail-closed summary. Its first reproduction passed
and updated the lock; the immediate second reproduction was unchanged.

```text
DVC_REPRO = PASS
SECOND_DVC_REPRO = UNCHANGED
HISTORICAL_REHEARSAL_GATE_PASS = NO
FAILED_MANDATORY_GATES = QLIB_BACKTEST_END_OF_FROZEN_CALENDAR_BLOCKED;
                         ALL_DEPENDENT_CERTIFICATION_EVIDENCE_NOT_EXECUTED
HISTORICAL_REHEARSAL_STATUS = BLOCKED_TECHNICAL
```

### Safety and state at the initial stop

```text
HISTORICAL_DATA_IS_PRISTINE_OOS = NO
HISTORICAL_DATA_CAN_CERTIFY = NO
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
AQ_NEW_GENERIC_ENGINE_COUNT = 0
PROTOCOL_THRESHOLD_CHANGES = 0
NEW_DATA_PROVIDER = NO
MARKET_DATA_NETWORK_CALLS = 0
BROKER_CALLS = 0
LLM_CALLS = 0
SYNTHETIC_ROWS = 0
FORWARD_FILL = NO
PROVIDER_MUTATION = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
LIVE_CAPITAL = NOT_AUTHORIZED
CURRENT_NEXT = P2_CERTIFICATION_HISTORICAL_REHEARSAL_BLOCKER_RESOLUTION_001
```

The next task must decide how to satisfy the frozen end-session semantics using
the same Qlib public runtime without changing Protocol V1 or the provider's
authoritative historical bytes. This task does not authorize that resolution.

## Blocker resolution

Read-only inspection of pinned Qlib source
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` confirmed that
`TradeCalendarManager.reset()` requests `Cal.calendar(..., future=True)`, the
final step requires `self._calendar[calendar_index + 1]`, and local
`FileCalendarStorage` resolves that request through `calendars/day_future.txt`.
The pinned `CollectorFutureCalendarUS` is not implemented.

A private calendar-only runtime root was created outside Git at
`D:\AQ_DATA\P2\certification-historical-rehearsal-001\qlib-calendar-runtime`.
It uses Qlib's public `LocalCalendarProvider` and `FileCalendarStorage`; it is
not an AQ calendar engine and does not contain market observations.

```text
QLIB_NATIVE_FUTURE_CALENDAR_REQUIRED = YES
QLIB_NATIVE_FUTURE_CALENDAR_STORAGE = calendars/day_future.txt
QLIB_PINNED_US_FUTURE_COLLECTOR = NOT_IMPLEMENTED
CALENDAR_AUTHORITY = exchange_calendars 4.13.2 / XNYS
RUNTIME_DAY_CALENDAR_ROWS = 2516
RUNTIME_DAY_CALENDAR_LAST = 2024-12-31
RUNTIME_DAY_CALENDAR_SHA256 = d4c0c100af851245f6f894e275e5d494d7e1cbd07f82d342c034cbdf7b7bfa4d
RUNTIME_FUTURE_CALENDAR_ROWS = 2517
RUNTIME_FUTURE_CALENDAR_SHA256 = 3225eab67ebddcd53022bec56d2d8fa99745a2d7990722c36eee57185566937d
FUTURE_CALENDAR_EXTRA_SESSION = 2025-01-02
FUTURE_CALENDAR_EXTRA_SESSION_COUNT = 1
TRADE_CALENDAR_FINAL_STEP_BOUNDARY_RESOLVES = YES
```

The extra session was resolved from XNYS rather than hard-coded. It is only
the calendar boundary Qlib needs to express the final closed interval.

```text
FROZEN_PROVIDER_MUTATED = NO
PRICE_DATA_MUTATED = NO
INSTRUMENT_DATA_MUTATED = NO
MEMBERSHIP_MUTATED = NO
OHLCV_ROWS_ADDED = 0
SYNTHETIC_PRICE_ROWS = 0
AQ_CUSTOM_CALENDAR_ENGINE = NO
AQ_CUSTOM_BACKTESTER = NO
```

The frozen provider remained 3,653 files and 25,537,236 bytes, and its
`calendars/day.txt` retained the SHA-256 shown above.

## Resumed rehearsal result

Both persisted prediction artifacts and original Recorder IDs were verified
and reused. Neither model was retrained and no new predictions were generated.
Qlib completed eight base runs and four cost-stress runs, each across all 753
XNYS sessions from 2022-01-03 through 2024-12-31.

```text
PRIMARY_PREDICTION_ROWS = 375597
PRIMARY_PREDICTION_SHA256 = 7af735fff6b07eb9be4b686776ffd53b496555cb5477bca641dfc9e4f521d7e7
PRIMARY_RECORDER_ID = 734ffa5ec01449f6b8a6696880d825bf
CONTROL_PREDICTION_ROWS = 375597
CONTROL_PREDICTION_SHA256 = 26c3433faa58a64914393fe13eac169d9ce86dbbe86f16dfb2b24fbd64139dab
CONTROL_RECORDER_ID = d6035e318a0640da876e52d587137e7c
PRIMARY_MODEL_RETRAINED = NO
CONTROL_MODEL_RETRAINED = NO
BASE_STRATEGY_RUNS = 8
COST_STRESS_ADDITIONAL_RUNS = 4
```

The preregistered reductions produced:

| Frozen gate/evidence | Result | Value |
|---|---|---:|
| WalkForward | PASS | 3 splits; positive fraction 1.0; median active return 0.0084314423431755 |
| CPCV | PASS | 45 splits; positive fraction 0.8; median active return 0.04940262646246085 |
| SPA | FAIL | consistent p-value 0.091 |
| RealityCheck | FAIL | consistent p-value 0.091 |
| StepM | FAIL | primary not in superior set |
| MCS | PASS | primary in 95% included set |
| Base cost | PASS | WalkForward median active return 0.0084314423431755 |
| 2x cost | PASS | WalkForward median active return 0.008385281193044714 |
| 3x cost | EVIDENCE ONLY / PASS | WalkForward median active return 0.008340581641408384 |
| Parameter robustness | PASS | 3 positive neighbors; median 0.16648788929475467 |
| Regime evidence | PARTIAL | 2023-2024 available; 2021-2022 partial; earlier blocks unavailable |
| Pandera 0.33.1 | PASS | strict required performance evidence validation |
| exchange_calendars 4.13.2 / XNYS | PASS | aligned dates are XNYS sessions |

The `arch` results are an intended fail-closed statistical outcome, not a
technical blocker. Thresholds, candidates, dates, and inputs were not changed.
The DVC stage seals both the historical blocker and completed downstream
evidence; its first reproduction passed and its immediate second reproduction
was unchanged.

```text
DVC_REPRO = PASS
SECOND_DVC_REPRO = UNCHANGED
FAILED_MANDATORY_GATES = SPA; REALITY_CHECK; STEPM
NEW_DISTINCT_TECHNICAL_BLOCKER = NONE
HISTORICAL_REHEARSAL_GATE_PASS = NO
HISTORICAL_REHEARSAL_STATUS = REJECTED
HISTORICAL_DATA_CAN_CERTIFY = NO
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
AQ_NEW_GENERIC_ENGINE_COUNT = 0
PROTOCOL_THRESHOLD_CHANGES = 0
NEW_DATA_PROVIDER = NO
MARKET_DATA_NETWORK_CALLS = 0
BROKER_CALLS = 0
LLM_CALLS = 0
RD_AGENT_EXECUTED = NO
SEALED_OOS_START_SESSION = 2026-09-14
ACTIVATION_SHA256 = d1ac67558f59d917eb71d666e48967f8f20bafc48bfc1ff616b7c85e262eef54
CURRENT_NEXT = P2_CERTIFICATION_HISTORICAL_REHEARSAL_CLOSEOUT_001
```
