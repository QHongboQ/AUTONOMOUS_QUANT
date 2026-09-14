# P3 US Ragged Scenario Configuration Proof 001

Status: **PASS — THIN STATIC CONFIG REQUIRED**

This task tested whether the pinned Microsoft RD-Agent Qlib scenario can
initialize AUTONOMOUS_QUANT's existing US ragged provider through upstream
configuration and public runtime interfaces. It did not execute research,
performance, LLM, or data acquisition work.

## Runtime authority

```text
RD_AGENT_ENV = /home/zhou/AQ_ENVS/rdagent
RD_AGENT_VERSION = 0.8.1.dev37
RD_AGENT_RUNTIME_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
FSSPEC_VERSION = 2026.6.0
RD_AGENT_PIP_CHECK = PASS
QLIB_ENV = rdagent4qlib
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
```

The existing Miniforge executable was visible only to the bounded control
process. A fresh process still did not resolve `conda`; no persistent PATH or
shell-profile change occurred.

## Upstream configuration surface

The inspected factor/model templates, scenario settings, runners, and
`QlibFBWorkspace` establish the following ownership:

| Setting | Upstream representation | Classification |
|---|---|---|
| `provider_uri` | literal under `qlib_init` | `TEMPLATE_VALUE_REPLACEABLE` |
| `region` | literal under `qlib_init` | `TEMPLATE_VALUE_REPLACEABLE` |
| `market` / instruments | YAML anchor passed to `DataHandlerLP` | `TEMPLATE_VALUE_REPLACEABLE` |
| `benchmark` | YAML anchor used only by backtest config | `TEMPLATE_VALUE_REPLACEABLE` |
| train/valid/test intervals | Jinja values supplied by `QLIB_FACTOR_*` or `QLIB_MODEL_*` settings | `CONFIGURABLE_WITH_EXISTING_PUBLIC_CONFIG` |
| handler | `DataHandlerLP` config | `TEMPLATE_VALUE_REPLACEABLE` |
| feature fields | Jinja feature expressions/names and upstream loader config | `CONFIGURABLE_WITH_EXISTING_PUBLIC_CONFIG` |
| label | template expression | `TEMPLATE_VALUE_REPLACEABLE` |
| `Fillna` feature processor | checked-in template default | `TEMPLATE_VALUE_REPLACEABLE`; excluded from the proof to preserve P2 ragged semantics |
| model and backtest execution | present in the full template | `NOT_RELEVANT_TO_P3_PROOF`; neither was instantiated |

`QlibFBWorkspace.execute()` honors the selected YAML but also calls
`prepare()` and `qrun`; this task intentionally used public
`QlibCondaEnv.run()` directly so neither operation occurred.

## Existing US provider

The provider resolved to:

```text
RESEARCH_PROVIDER_PATH = /mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data
CALENDAR_FILE = calendars/day.txt
INSTRUMENT_COLLECTIONS = instruments/all.txt; instruments/p2_pit.txt
FEATURE_STORAGE = features/<security-identity>/{open,high,low,close,volume}.day.bin
RESEARCH_PROVIDER_MIN_SESSION = 2015-01-02
RESEARCH_PROVIDER_MAX_SESSION = 2024-12-31
CALENDAR_SESSIONS = 2516
SECURITY_IDENTITIES = 730
MEMBERSHIP_RANGES = 745
FEATURE_SECURITY_DIRECTORIES = 730
MEMBER_SESSION_ROWS = 1267963
OBSERVED_SAFE_ROWS = 1224788
MASKED_ROWS = 43175
```

The retained P2 evidence is authoritative for member-session accounting. The
filesystem independently confirmed 730 `all` rows, 745 `p2_pit` ranges, 730
feature directories, and the calendar bounds.

## Native US semantics and disposable config

Pinned Qlib defines `REG_US = "us"`. The existing provider exposes the native
instrument collection `p2_pit`. The disposable upstream-template copy used:

```text
provider_uri = /mnt/d/AQ_DATA/P2/qlib-native-ragged-panel-001/qlib_data
region = us
market = p2_pit
benchmark = SPY
train = 2015-01-02 through 2019-12-31
valid = 2020-01-02 through 2021-12-31
test = 2022-01-03 through 2024-12-31
```

`SPY` was retained only because the full upstream template structurally
contains a benchmark. It is a research-only placeholder and grants no P2
certification benchmark authority. No backtest resolved or consumed it.

The static config SHA-256 was
`6c8343164561972b920bc41ae45013181a2814cc88fb100c1515ee311db34175`;
the rendered config SHA-256 was
`b7fc8d6f94f4f32a2396bca9034a47ee1b4713241769aea21cdd79d121a7e928`.

## Qlib initialization and dynamic-universe proof

Native `QlibCondaConf()` discovered `rdagent4qlib` with no manual
`bin_path`. A diagnostic-only `QlibCondaEnv.run()` returned zero and Qlib
initialized the configured local provider with caches disabled.

Public Qlib data interfaces resolved:

```text
INSTRUMENT_QUERY = {market: p2_pit, filter_pipe: []}
2015-01-02_ACTIVE_SECURITIES = 499
2024-12-31_ACTIVE_SECURITIES = 503
EARLY_ONLY_SECURITIES = 176
LATE_ONLY_SECURITIES = 180
DATE_DEPENDENT_MEMBERSHIP = YES
STATIC_CURRENT_UNIVERSE_SUBSTITUTION = NO
```

The instrument collection therefore retained its date-valid ranges; AQ did
not recreate or mutate PIT membership logic.

## Raggedness proof

A deterministic, bounded sample selected the first provider interval starting
on the first calendar session and ending before the final calendar session:

```text
SAMPLE_INSTRUMENT = P2SEC00A2606527FADDDA12E3E76CDEA395D253F930C87F0E430726CA4C16E027FBB7
MEMBERSHIP_INTERVAL = 2015-01-02 through 2016-01-04
SAMPLE_WINDOW = 2015-12-29 through 2016-01-07
REQUESTED_SESSIONS = 7
RETURNED_OBSERVED_CLOSE_ROWS = 4
RETURNED_NAN_CLOSE_ROWS = 0
MISSING_BY_ABSENCE = 3
```

Qlib represented the post-interval sessions by omitting unavailable rows. The
initial disposable assertion expected explicit NaNs; it was corrected to
recognize both explicit NaN and absent-row ragged representations. No search
for a more convenient missing-data example was performed.

```text
ZERO_FILL = NO
FORWARD_FILL = NO
BACK_FILL = NO
INTERPOLATION = NO
SUCCESSOR_PRICE_SUBSTITUTION = NO
RAGGED_PANEL_SEMANTICS_PRESERVED = YES
AQ_MISSING_DATA_ENGINE = NONE
```

## Immutability and sealed OOS

Provider state before and after the passing proof was identical:

```text
PROVIDER_FILE_COUNT = 3653
PROVIDER_TOTAL_BYTES = 25537236
CALENDAR_SHA256 = d4c0c100af851245f6f894e275e5d494d7e1cbd07f82d342c034cbdf7b7bfa4d
ALL_INSTRUMENTS_SHA256 = 24d3a9010b725f8121ae1a999916bd0b6e76923eb9fad85be7e57d8653cc2cbc
P2_PIT_INSTRUMENTS_SHA256 = e771f73b91664b26584e66c42eb007c4276c492071172e7d6594bc900f01f875
PIT_MEMBERSHIP_AUTHORITY_CHANGED = NO
```

The provider maximum session `2024-12-31` is strictly earlier than sealed OOS
start `2026-09-14`. No sealed/future path or result was supplied or queried.

```text
P3_CAN_ACCESS_SEALED_OOS = NO
SEALED_OOS_ISOLATION = PASS
```

## China-default inventory

All China occurrences on or adjacent to the inspected scenario were
accounted for:

1. Five factor/model YAML templates each contain `cn_data`, `region: cn`,
   `csi300`, and `SH000300`: `TEMPLATE_DEFAULT_ONLY` and replaceable by a
   static config.
2. Two `CSI300` occurrences in `experiment/prompts.yaml` are
   `PROMPT_TEXT_ONLY`; no prompt or LLM loop ran.
3. `factor_data_template/generate.py` contains an executable `cn_data`
   initializer. It is `NOT_ON_SELECTED_PATH` for this Qlib configuration
   proof, but a future factor scenario must preconfigure US factor source-data
   folders and must not invoke that generator.
4. No China-only calendar assumption was found in `QlibFBWorkspace` or the
   diagnostic execution path; Qlib's public `region=us` configuration owns US
   semantics.

```text
UNACCOUNTED_EXECUTION_HARDCODES = 0
```

## Decision

The upstream public configuration and runtime interfaces are sufficient, but
the checked-in template does not expose provider, region, market, benchmark,
or missing-data choices through the existing date environment variables. A
small project-owned static YAML/config overlay is therefore necessary. No
runtime adapter, generic universe engine, data engine, research engine, or
Qlib runner is required.

```text
QLIB_INIT_FROM_RDAGENT_US_CONFIG = PASS
US_INSTRUMENT_UNIVERSE_RESOLVED = PASS
P3_US_SCENARIO_CONFIGURATION = THIN_STATIC_CONFIG_REQUIRED
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

1. Bounded US ragged static-config materialization.
2. Candidate-to-P2 thin fail-closed identity contract.
3. P3 DVC-stage activation.
4. Autonomous-loop activation.

```text
CURRENT_NEXT = P3_US_RAGGED_STATIC_CONFIG_MATERIALIZATION_001
```
