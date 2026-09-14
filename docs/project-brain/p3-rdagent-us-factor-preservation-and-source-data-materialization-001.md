# P3 RD-Agent US Factor Preservation and Source-Data Materialization 001

Status: **COMPLETE — READY FOR THIN BINDING IMPLEMENTATION**

Completion date: 2026-09-14

This task resolved the only remaining RD-Agent US factor source-data blocker.
It created a private RD-Agent-native derivative from existing frozen P2
evidence without changing the P2 Qlib provider, provider authority, PIT
membership, ragged policy, sealed OOS, RD-Agent, Qlib, or DVC.

## 1. Authority and result

```text
RD_AGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_FACTOR_AUTHORITY = QUANTIACS_SPLIT_CUMPROD
QLIB_FACTOR_FIELD_PRESERVATION = PASS
RDAGENT_US_FACTOR_SOURCE_DATA = PASS
FACTOR_SOURCE_DATA_CONTRACT = READY_FOR_THIN_BINDING_IMPLEMENTATION
MATERIALIZER_IMPLEMENTATION = ONE_THIN_CONTRACT_MATERIALIZER
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_RDAGENT_US_THIN_SCENARIO_BINDING_IMPLEMENTATION_001
```

## 2. Frozen source and identity chain

The retained source was located from physical evidence rather than chat
history:

```text
FROZEN_QUANTIACS_SOURCE = D:/AQ_DATA/P2/frozen-certification-dataset-build-001/source/quantiacs
SOURCE_MANIFEST_SHA256 = 80f42e07b80dbc2fbe211d9b44ab4b6a0e5e9db3943098effb3976b92a49e73b
FULL_UNIVERSE_INVENTORY = D:/AQ_DATA/P2/certification-coverage-frontier-audit-001/full_universe_inventory.json
FULL_UNIVERSE_INVENTORY_SHA256 = 3c73a9ec0260a3187529a557b271fe5c34ba332427ae41ed713f5459a28395c2
AVAILABILITY_SHA256 = f69f31fb85ed9034fe34f4ec7633e75b58648f39f67bbea5aa1067429e46cf97
EPISODE_MAP_SHA256 = 31eb307bd31937c97a24fb4076d641d0ebe0e9d0f0c9dc23c02162ba8d5f31f6
INSTRUMENT_IDENTITY_SHA256 = 4b99d072199dc595e068dd2dd9517b1fa1d1493afaa1a069316adc646be4957a
FROZEN_QUANTIACS_SOURCE_FOUND = YES
FROZEN_SPLIT_CUMPROD_FOUND = YES
```

The materializer requires all source-manifest artifact hashes to match. For
each row it verifies the exact frozen chain:

```text
Qlib datetime/instrument row
-> availability episode_id and provider-selection reason
-> accepted inventory provider_asset_identifier for that episode
-> exact frozen Quantiacs asset and session coordinate
-> split_cumprod observation
```

Historical ticker is validation metadata only and never a join key.

```text
IDENTITY_JOIN_PROOF = PASS
TICKER_ONLY_IDENTITY_JOIN = NO
```

Bounded evidence covered:

- normal active case `HUM`, 2015-01-02, episode-specific `NYS:HUM`;
- the FB/META rename chain, with one security identity but distinct accepted
  episodes and exact `NAS:FB` and `NAS:META` provider assets on their
  date-valid sides of the boundary; and
- AAPL's retained split boundary, using exact `NAS:AAPL` session observations.

## 3. P2 provider non-mutation

The provider was hashed before the Qlib read and again after all output and
HDF validation:

```text
P2_PROVIDER_FILE_COUNT_BEFORE = 3653
P2_PROVIDER_FILE_COUNT_AFTER = 3653
P2_PROVIDER_BYTES_BEFORE = 25537236
P2_PROVIDER_BYTES_AFTER = 25537236
P2_PROVIDER_TREE_SHA256_BEFORE = 83ff6acb15e2c3d33e84ca447306e2a7bfd12a03008c72ca0d9dea76634e4f21
P2_PROVIDER_TREE_SHA256_AFTER = 83ff6acb15e2c3d33e84ca447306e2a7bfd12a03008c72ca0d9dea76634e4f21
P2_PROVIDER_CALENDAR_SHA256 = d4c0c100af851245f6f894e275e5d494d7e1cbd07f82d342c034cbdf7b7bfa4d
P2_PROVIDER_P2_PIT_SHA256 = e771f73b91664b26584e66c42eb007c4276c492071172e7d6594bc900f01f875
FACTOR_DAY_BIN_ADDED_TO_P2 = NO
P2_PROVIDER_MUTATED = NO
```

## 4. Private derivative

```text
P3_FACTOR_SOURCE_ROOT = D:/AQ_DATA/P3/rdagent-us-ragged/factor-source
FULL_DAILY_PV = D:/AQ_DATA/P3/rdagent-us-ragged/factor-source/full/daily_pv.h5
FULL_DAILY_PV_SHA256 = deacd04bad8f5321bd49cc63cf9be37d38e4ae7b33b5c223021c80dedad98b21
DEBUG_DAILY_PV = D:/AQ_DATA/P3/rdagent-us-ragged/factor-source/debug/daily_pv.h5
DEBUG_DAILY_PV_SHA256 = 5fe7263630a9b7c3a796f35e0d943e62aed44ec4d22b20cbf42a4ec846016ebc
MATERIALIZATION_REPORT_SHA256 = 7d067e6f93409228125e7e5b6d2590242d60a5bc664f5f8aa9848e5d4a0e3033
```

Both folders contain only the native `daily_pv.h5` plus the pinned RD-Agent
README structure with a bounded project note. The HDF key is `data`, index is
`datetime, instrument`, and columns are exactly `$open`, `$close`, `$high`,
`$low`, `$volume`, `$factor`.

The materializer first publishes to a unique sibling temporary directory. It
promotes the validated directory atomically and removes temporary pickle/audit
transport used between the existing pinned-Qlib runtime and the existing
PyTables-capable RD-Agent venv. No package was installed or changed.

## 5. Exact row and factor accounting

```text
TOTAL_DAILY_PV_ROWS = 1267963
QUANTIACS_BACKED_ROWS = 1224658
SIMFIN_ONLY_ROWS = 130
FACTOR_NON_NULL_ROWS = 1224658
FACTOR_NAN_ROWS = 43305
FACTOR_UNIQUE_COUNT = 72
FACTOR_NONCONSTANT_COUNT = 140098
FAKE_FACTOR_ROWS = 0
CONSTANT_ONE_FALLBACK_ROWS = 0
```

Every `OBSERVED_PRIMARY` row received its exact positive finite frozen
`split_cumprod`. All 130 `OBSERVED_SECONDARY` SimFin rows retained factor NaN.
All masked rows also retained factor NaN. There was no fill, interpolation,
factor recomputation, or successor/current-ticker substitution.

## 6. Split semantic proof

The frozen AAPL observations demonstrate a real nonconstant boundary:

| Session | Adjusted close | `split_cumprod` / HDF `$factor` | Restored close (`adjusted / factor`) |
|---|---:|---:|---:|
| 2020-08-28 | 124.80750274658203 | 0.25 | 499.2300109863281 |
| 2020-08-31 | 129.0399932861328 | 1.0 | 129.0399932861328 |

The HDF factor exactly equals the frozen source coordinate in both rows.

```text
FACTOR_IS_NOT_GLOBALLY_FORCED_TO_ONE = YES
```

## 7. Deterministic debug materialization

The pinned upstream generator intends a fixed 2018-2019 debug period and a
100-instrument subset. The P3 rule removes upstream enumeration-order
dependence:

```text
DEBUG_SELECTION = FIRST_100_INSTRUMENT_IDS_IN_LEXICOGRAPHIC_SECURITY_IDENTITY_ORDER
DEBUG_START = 2018-01-01
DEBUG_END = 2019-12-31
DEBUG_INSTRUMENT_COUNT = 100
DEBUG_ROW_COUNT = 34541
RANDOMNESS = NONE
CURRENT_TICKER_DEPENDENCE = NONE
CURRENT_DATE_DEPENDENCE = NONE
```

The debug data is selected from the completed full derivative and therefore
cannot re-query or diverge from its factor/missingness semantics.

## 8. Retained implementation and tests

No existing thin tool exported the RD-Agent HDF while joining the frozen
factor authority, so one task-specific materializer was required:

```text
MATERIALIZER_FILE = 30-research-system/rd-agent/binding/aq_rdagent_us_binding/materialize_factor_source.py
FOCUSED_TEST_FILE = 30-research-system/rd-agent/binding/tests/test_materialize_factor_source.py
FOCUSED_TESTS = 5/5 PASS
```

It has one fixed responsibility: existing Qlib public OHLCV plus exact frozen
episode/provider/session factor evidence to the RD-Agent HDF contract. It has
no provider fetch/router, identity resolver, PIT builder, corporate-action
inference, price-adjustment calculation, imputation, refresh, or generic
engine abstraction.

## 9. RD-Agent native discovery proof

Both HDF files passed `pandas.read_hdf(..., key="data")`, index/schema checks,
and the pinned `get_file_desc()` path. Process-local native folder settings
then pointed to the new private folders. `get_data_folder_intro()` read the
debug HDF and README successfully while a replacement generator function was
configured to throw immediately if selected.

```text
RDAGENT_NATIVE_HDF_CONTRACT = PASS
RDAGENT_GET_FILE_DESC = PASS
RDAGENT_US_FACTOR_SOURCE_DISCOVERY = PASS
CHINA_GENERATOR_EXECUTED = NO
CHINA_FALLBACK_SELECTED = NO
```

## 10. Authority preservation and non-actions

```text
MAX_MATERIALIZED_SESSION = 2024-12-31
SEALED_OOS_START = 2026-09-14
SEALED_OOS_ISOLATION = PASS
PIT_MEMBERSHIP_AUTHORITY_CHANGED = NO
RAGGED_POLICY_CHANGED = NO
DVC_CHANGED = NO
RD_AGENT_SOURCE_CHANGED = NO
QLIB_SOURCE_CHANGED = NO
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
BROKER_CALLS = 0
PAPER_TRADING = NO
LIVE_TRADING = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
REMAINING_RESIDUAL_GAPS = NONE
```
