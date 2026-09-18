# P3 US Ragged Static Config Materialization 001

Status: **PASS — THIN STATIC CONFIG MATERIALIZED**

This task materialized the minimum project-owned configuration needed for the
pinned Microsoft RD-Agent factor and model research paths to initialize the
existing US ragged Qlib provider. It introduced no executable AQ adapter,
runner, data engine, universe engine, missing-data engine, or research engine.

## Authority and scope

```text
TASK = AUTONOMOUS-QUANT-P3-US-RAGGED-STATIC-CONFIG-MATERIALIZATION-001
BASE_MAIN = d6215b19df989b32aa1151d935a4ef6399424c08
PRIOR_BRANCH_HEAD = 8e3292f2d9d2f63453f33df16cbe69326d954c0e
RD_AGENT_VERSION = 0.8.1.dev37
RD_AGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
```

## Minimum config decision

Two configs are the minimum selected boundary:

| Static config | Pinned upstream template | Upstream SHA-256 | Purpose |
|---|---|---|---|
| `30-research-system/rd-agent/config/p3-us-ragged-factor.yaml` | `rdagent/scenarios/qlib/experiment/factor_template/conf_baseline.yaml` | `b6253e3d9c7512f7066088ae27f5440e4a95cb409292ab9529ecb68847ea8385` | Baseline factor-research Qlib task used by the RD-Agent factor path |
| `30-research-system/rd-agent/config/p3-us-ragged-model.yaml` | `rdagent/scenarios/qlib/experiment/model_template/conf_baseline_factors_model.yaml` | `bd3e9338789f8bf4fd72e6f38032fd6a642799d0b38dc83a0ea6f043eff4248c` | Baseline model-research Qlib task used by the RD-Agent model path |

The factor and model runners have distinct baseline task shapes, so one config
cannot represent both without creating a generator or wrapper. `fin_quant`
composes these upstream capabilities; it does not justify pre-copying the
combined-factor or selected-SOTA variants before those states are activated.
No unused upstream template was copied.

```text
MINIMUM_REQUIRED_CONFIG_COUNT = 2
```

## Bounded project substitutions

The upstream model classes, feature/label interface, dataset class, strategy,
record templates, and research parameters remain intact. Only project-specific
runtime values were changed:

```text
PROVIDER_URI = /mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data
REGION = us
MARKET = p2_pit
TRAIN = 2015-01-02 THROUGH 2019-12-31
VALID = 2020-01-02 THROUGH 2021-12-31
TEST = 2022-01-03 THROUGH 2024-12-31
TRACKING_URI = sqlite:////mnt/d/AQ_DATA/P3/rdagent-us-ragged/mlflow.db
```

The explicit SQLite URI preserves the already-validated Qlib/MLflow
database-backed path rather than relying on MLflow's rejected filesystem-store compatibility
path. No database was opened or created in this task.

The full upstream workflow structure requires a benchmark field, so both
configs retain `SPY` only as a research-only structural placeholder.
`SPY_IS_P2_CERTIFICATION_BENCHMARK = NO`; no backtest consumed it.

The upstream feature `Fillna` processor was omitted. No replacement processor
or AQ missing-data implementation was introduced. The US exchange limit value
was disabled with the supported static `null` setting.

```text
ZERO_FILL = NO
FORWARD_FILL = NO
BACK_FILL = NO
INTERPOLATION = NO
SUCCESSOR_PRICE_SUBSTITUTION = NO
AQ_CUSTOM_MISSING_DATA_ENGINE = NONE
ACTIVE_CHINA_EXECUTION_DEFAULTS = 0
```

## Config identity

Both repository files are deterministic UTF-8 text without BOM, use LF line
endings, and contain no timestamp, secret, or credential.

```text
p3-us-ragged-factor.yaml SHA256 = 7a5fa872aedc6820c5c1c8947fab8c2ac433f4d1a5f00eb2fab14656c2813b60
p3-us-ragged-model.yaml SHA256 = a7abc5cba54eb2f8bb6b7a5b703cfe63fa43450b22bc732db79f82bf86717296
```

## Read-only runtime validation

A disposable diagnostic outside the repository invoked the installed
RD-Agent `QlibCondaEnv` with process-local Conda discovery. Inside the selected
`rdagent4qlib` environment, Qlib's public `render_template` path rendered each
config with minimal diagnostic feature/model variables, the upstream safe YAML
loader parsed both, and `qlib.init` initialized the local provider. Neither
`prepare()` nor `qrun` was invoked.

```text
STATIC_CONFIG_PARSE = PASS
QLIB_INIT = PASS
CALENDAR = 2015-01-02 THROUGH 2024-12-31; 2516 SESSIONS
MARKET = p2_pit
EARLY_ACTIVE_SECURITIES = 499
LATE_ACTIVE_SECURITIES = 503
MARKET_RESOLUTION = PASS
```

The same deterministic boundary sample used by the prior proof returned:

```text
REQUESTED_SESSIONS = 7
RETURNED_OBSERVED_CLOSE_ROWS = 4
RETURNED_NAN_CLOSE_ROWS = 0
MISSING_BY_ABSENCE = 3
RAGGED_PANEL_SEMANTICS_PRESERVED = YES
```

Provider state was unchanged:

```text
PROVIDER_FILE_COUNT_BEFORE = 3653
PROVIDER_FILE_COUNT_AFTER = 3653
PROVIDER_TOTAL_BYTES_BEFORE = 25537236
PROVIDER_TOTAL_BYTES_AFTER = 25537236
CALENDAR_SHA256 = d4c0c100af851245f6f894e275e5d494d7e1cbd07f82d342c034cbdf7b7bfa4d
ALL_INSTRUMENTS_SHA256 = 24d3a9010b725f8121ae1a999916bd0b6e76923eb9fad85be7e57d8653cc2cbc
P2_PIT_INSTRUMENTS_SHA256 = e771f73b91664b26584e66c42eb007c4276c492071172e7d6594bc900f01f875
```

The provider maximum session remains `2024-12-31`, strictly before sealed OOS
start `2026-09-14`.

```text
P3_CAN_ACCESS_SEALED_OOS = NO
SEALED_OOS_ISOLATION = PASS
```

## Decision and non-actions

Static upstream configuration is sufficient. The disposable diagnostic and
task-created logs/caches were removed after validation; no runtime artifact
remains in the repository.

```text
P3_US_RAGGED_STATIC_CONFIG = COMPLETE
P3_US_SCENARIO_CONFIGURATION = THIN_STATIC_CONFIG_MATERIALIZED
AQ_US_SCENARIO_ADAPTER = NONE
AQ_CUSTOM_QLIB_RUNNER = NONE
AQ_CUSTOM_UNIVERSE_ENGINE = NONE
AQ_CUSTOM_DATA_ENGINE = NONE
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CODE_CHANGED = NO

RD_AGENT_LLM_LOOP_EXECUTED = NO
LLM_CALLS = 0
MODEL_TRAINING = NO
MODEL_FIT_CALLS = 0
NEW_PREDICTIONS = NO
BACKTEST = NO
PERFORMANCE_METRICS_CREATED = NO
MARKET_DATA_NETWORK_CALLS = 0
DATASET_DOWNLOADS = 0
NEW_DATA_PROVIDER = NO
DVC_REPRO_EXECUTED = NO
BROKER_CALLS = 0
PAPER_TRADING = NO
LIVE_TRADING = NO
```

Remaining finite gaps:

1. Candidate-to-P2 thin fail-closed identity contract audit.
2. P3 DVC-stage activation.
3. Autonomous-loop activation.

```text
CURRENT_NEXT = P3_CANDIDATE_TO_P2_IDENTITY_CONTRACT_AUDIT_001
```
