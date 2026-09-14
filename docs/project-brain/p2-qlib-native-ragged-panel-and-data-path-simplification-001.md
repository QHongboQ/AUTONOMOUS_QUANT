# P2 Qlib Native Ragged Panel and Data-Path Simplification 001

Status: COMPLETE

```text
CAPABILITY = P2_QLIB_NATIVE_RESEARCH_DATA
UPSTREAM_OWNER = MICROSOFT_QLIB
OWNERSHIP_MODE = UPSTREAM_WHOLE
UPSTREAM_DEPLOYED = YES
AQ_IMPLEMENTATION = PIT_MEMBERSHIP + SECURITY_IDENTITY + DECLARATIVE_PROVIDER_BINDING_FACTS + THIN_QLIB_HANDOFF_ONLY
CUSTOM_GENERIC_ENGINE_REQUIRED = NO
```

## Authority and scope

The accepted runtime remains Qlib `0.9.8.dev26` from pinned source commit
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` in the existing WSL Ubuntu 24.04
`rdagent4qlib` environment. Qlib owns local-provider storage, DatasetH,
DataHandlerLP, Alpha158/Alpha158DL operators, ExpressionDFilter, DropnaLabel,
LGBModel, Recorder, prediction, Exchange, backtest, transaction costs, and
portfolio analysis.

AQ supplies only accepted PIT membership ranges, permanent security identity,
12 declarative date-bounded provider-binding facts, and a thin frozen-input
staging/configuration handoff. No AQ provider registry, router, generic
normalizer, identity engine, security master, binary writer, feature engine,
label processor, model engine, or tradability engine was added.

## Frozen inputs and private output

```text
SOURCE_PRECEDENCE = QUANTIACS_PRIMARY_SIMFIN_BOUNDED_SECONDARY
QUANTIACS_SOURCE_MANIFEST_SHA256 = 80f42e07b80dbc2fbe211d9b44ab4b6a0e5e9db3943098effb3976b92a49e73b
SIMFIN_SOURCE_SHA256 = 3a7c21afefc044a9c28f5a1f1069840fe092d7f44b937c7d9b489bcc5c9fd2a9
PRIVATE_OUTPUT = D:\AQ_DATA\P2\qlib-native-ragged-panel-001
NETWORK_REQUESTS_EXECUTED = 0
```

The panel covers every accepted XNYS member session from 2015-01-02 through
2024-12-31. Qlib instrument IDs are deterministic encodings of
`security_identity`; ticker text is metadata only. Re-entry ranges remain
non-contiguous and ticker reuse cannot collapse distinct securities.

## Full-panel accounting

```text
UNIQUE_SECURITY_IDENTITIES = 730
INSTRUMENT_EPISODES = 745
TOTAL_MEMBER_SESSION_ROWS = 1267963
OBSERVED_SAFE_ROWS = 1224788
MASKED_ROWS = 43175
MASKED_ROW_PERCENT = 3.405068
QUANTIACS_SELECTED_ROWS = 1224658
SIMFIN_SELECTED_ROWS = 130

KNOWN_PROVIDER_GAP_ROWS = 7581
KNOWN_TERMINAL_SESSION_PROVIDER_GAP_ROWS = 1
PARTIAL_PROVIDER_COVERAGE_ROWS = 455
NO_PROVIDER_ASSET_ROWS = 30025
IDENTITY_AMBIGUOUS_ROWS = 2456
TERMINAL_POLICY_UNRESOLVED_ROWS = 2657
UNRESOLVED_ERROR_ROWS = 0
```

| Year | Member rows | Observed safe | Masked | Usable percent |
|---:|---:|---:|---:|---:|
| 2015 | 126147 | 117296 | 8851 | 92.983583 |
| 2016 | 127104 | 119479 | 7625 | 94.000976 |
| 2017 | 126744 | 120526 | 6218 | 95.094048 |
| 2018 | 126737 | 121386 | 5351 | 95.777871 |
| 2019 | 127260 | 122629 | 4631 | 96.360993 |
| 2020 | 127767 | 123862 | 3905 | 96.943655 |
| 2021 | 127260 | 124013 | 3247 | 97.448531 |
| 2022 | 126437 | 124004 | 2433 | 98.075722 |
| 2023 | 125750 | 125064 | 686 | 99.454473 |
| 2024 | 126757 | 126529 | 228 | 99.820128 |

Every unavailable required observation remains a membership row with NaN
OHLCV. The private availability sidecar retains the reason. No whole year is
rejected because of isolated missing sessions.

## Qlib-native integration evidence

Pinned upstream `scripts/dump_bin.py` created the local provider: 2,516 daily
calendar sessions, 745 instrument ranges, and 730 feature directories. The
bounded real-data probe verified:

```text
qlib.init = PASS
D.instruments = PASS
D.list_instruments = PASS
D.features_observed = PASS
D.features_missing_returns_nan = PASS
DatasetH = PASS
Alpha158DL_OHLCV_FEATURES = PASS (157 features; no VWAP)
ExpressionDFilter_CURRENT_CLOSE = PASS
DropnaLabel = PASS
SMOKE_TRAINABLE_LABEL_ROWS = 20671
MASKED_ROWS_IN_SMOKE_TRAINING_INPUT = 455
MASKED_UNUSABLE_ROWS_IN_INFERENCE = 0
MASKED_UNUSABLE_ROWS_IN_TRAINING = 0
FEATURE_NAN_COUNT = 4305
FEATURE_TOTAL_VALUES = 3245347
LGBModel_BOUNDED_SMOKE = PASS
PREDICTION_SMOKE = PASS (2688 rows)
Exchange_NAN_SUSPENSION = PASS
NAN_CLOSE_BUY_ALLOWED = NO
NAN_CLOSE_SELL_ALLOWED = NO
AQ_CUSTOM_LABEL_EXPRESSION = NONE
AQ_CUSTOM_FILTER_CLASS = NONE
```

Real controls covered ARNC/HWM, BBBY, DOW, DISCK, ANTM/ELV, ABC/COR,
COG/CTRA, and UTX/RTX. ARNC retains exactly 868 observed and 455 masked required
sessions. DOW's two security identities remain separate. DISCK retains its one
known terminal-session provider gap.

## Prohibited transformations and runtime boundary

```text
SYNTHETIC_PRICE_ROWS = 0
FORWARD_FILL = NO
BACKWARD_FILL = NO
LINEAR_INTERPOLATION = NO
SUCCESSOR_PRICE_SUBSTITUTION = NO
CURRENT_TICKER_BACKFILL = NO
FAKE_VWAP = NO
FAKE_FACTOR = NO
RESEARCH_RUNTIME_EXTERNAL_API_COUNT = 0
DATA_REFRESH_PRICE_PROVIDER_COUNT = 2
IDENTITY_EVIDENCE_NETWORK_CALLS_DURING_RUNTIME = 0
```

This proves the research-data path only. It does not certify the full PIT
dataset, select sealed OOS dates, or make any model-performance claim.

## Legacy runtime retirement

After the real Qlib integration passed, repository import/reference checks
showed the former `10-data-system/market-data/p2-binding` executable leaf had no
live downstream dependency. The specifically authorized provider fetchers,
AQ/DuckDB binding runtime, executable tests, requirements, and package entry
point were retired. No replacement provider wrapper or generic engine was
created.

The accepted facts were moved byte-for-byte to
`10-data-system/market-data/provider-binding-authority/accepted_provider_binding_facts.json`.

```text
AUTHORITY_FACT_COUNT = 12
AUTHORITY_CONTENT_CHANGED = NO
AUTHORITY_SHA256 = 3cd9b13a1424609120a4e069ac2cf9f9b9aa61e2df919aa48cf51eeac616bc69
OPENBB_RUNTIME_REQUIRED = NO
OPENFIGI_RUNTIME_REQUIRED = NO
EDGARTOOLS_RUNTIME_REQUIRED = NO
VALUEIN_RUNTIME = NO
PROVIDER_ROUTER = NONE
GENERIC_AQ_DATA_ENGINE = NONE
LEGACY_P2_BINDING_EXECUTABLE = REMOVED
```

Historical audit documents remain evidence and are not current runtime
dependencies.

## Current state

```text
QLIB = RESEARCH_RUNTIME_OWNER
AQ = PIT_MEMBERSHIP + SECURITY_IDENTITY + DECLARATIVE_PROVIDER_BINDING_FACTS + THIN_QLIB_HANDOFF_ONLY
MISSING_SESSION_POLICY = PRESERVE_MEMBERSHIP_AND_MASK_SESSION
MISSING_SESSION_CAUSES_WHOLE_YEAR_REJECTION = NO
RESEARCH_RUNTIME_EXTERNAL_API_COUNT = 0
DATA_PROVIDER_REMEDIATION = CLOSED
P2 = STARTED / IN_PROGRESS
CURRENT_NEXT = P2_QLIB_NATIVE_RAGGED_PANEL_PR_CLOSEOUT_001
```
