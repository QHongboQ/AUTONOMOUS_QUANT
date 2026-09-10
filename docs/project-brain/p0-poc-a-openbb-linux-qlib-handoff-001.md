# P0 POC-A OpenBB/Linux Qlib handoff 001

**Task:** `AUTONOMOUS-QUANT-P0-POC-A-OPENBB-LINUX-QLIB-HANDOFF-001`
**Result:** `POC_A = BLOCKED` before any provider request.

## Scope and preflight

The task branch was created from authoritative `origin/main` commit `7a4dc680a42406bb8c411ae50d7138a803809819`. POC-B runtime and artifacts were not modified.

The installed Windows OpenBB runtime was verified without a provider call:

| Item | Observed value |
|---|---|
| OpenBB environment | `D:\AQ_ENVS\openbb` |
| OpenBB | `4.7.2` |
| `openbb-yfinance` | `1.6.3` |
| Historical route | `obb.equity.price.historical` |
| Supported provider | explicit `provider="yfinance"` |
| Supported historical parameters | `symbol`, `start_date`, `end_date`, `interval`, `adjustment`, `include_actions` |
| Adjustment options | `splits_only`, `splits_and_dividends` |

Installed yfinance source confirms `adjustment="splits_only"` maps to the non-dividend-adjusted path and `include_actions=true` is passed as the provider action flag. No provider request was made because the required artifact serialization precondition did not pass.

## Isolated OpenBB home

OpenBB 4.7.2 derives `OPENBB_DIRECTORY` from Python `Path.home()` as `<home>/.openbb_platform`. The task pre-created `D:\AQ_CACHE\openbb-home` and launched the inspected OpenBB process with the Windows `USERPROFILE`/`HOMEDRIVE`/`HOMEPATH` environment set to that root. Direct runtime output verified:

```text
Path.home() = D:\AQ_CACHE\openbb-home
OPENBB_DIRECTORY = D:\AQ_CACHE\openbb-home\.openbb_platform
USER_SETTINGS_PATH = D:\AQ_CACHE\openbb-home\.openbb_platform\user_settings.json
SYSTEM_SETTINGS_PATH = D:\AQ_CACHE\openbb-home\.openbb_platform\system_settings.json
```

Only the isolated OpenBB settings files were created (104 bytes across two files). The standard Windows user profile was not used for OpenBB settings or cache artifacts.

## Fail-closed Parquet serialization blocker

The required primary artifact is `D:\AQ_DATA\poc\poc-a-openbb-qlib\market_data.parquet`, produced by the Windows OpenBB side of the selected topology. Before making a network request, the installed Windows OpenBB environment was checked for existing Parquet writers:

```text
pyarrow = absent
fastparquet = absent
polars = absent
duckdb = absent
```

Without an installed Windows-side Parquet engine, pandas cannot safely write the required artifact. Linux Qlib has `pyarrow`, but moving serialization to that runtime would change the specified Windows OpenBB → normalized pandas/Parquet handoff and would not prove the final data boundary. Installing a writer is prohibited by this task. Therefore the provider call was not made, no raw yfinance fallback was used, and no market data was downloaded.

The POC output directory `D:\AQ_DATA\poc\poc-a-openbb-qlib\` was not created. Incremental market-data artifact use was therefore `0` bytes, within the 25 MiB cap.

## Linux consumer preflight

The established Linux consumer authority was inspected read-only:

| Item | Observed value |
|---|---|
| Runtime | `/home/zhou/miniforge3/envs/rdagent4qlib` |
| Python | `3.10.21` |
| Qlib | `0.9.8.dev26` |
| Pinned Qlib source SHA | `2fb9380b342556ddb50a4b24e4fe8655d548b2b8` |
| `StaticDataLoader` constructor | `StaticDataLoader(config: Union[dict, str, pandas.DataFrame], join="outer")` |
| `StaticDataLoader.load` | accepts instruments/start/end filters and returns a pandas `DataFrame` |

The Linux runtime is ready to consume a valid Parquet or pandas-compatible normalized artifact, but ingestion was not attempted because no compliant Windows artifact exists.

## Final state

```text
OPENBB_PROVIDER_CALL_COUNT = 0
MARKET_DATA_DOWNLOADED = NO
WINDOWS_ARTIFACT = NOT_CREATED
LINUX_ARTIFACT = NOT_CREATED
CROSS_RUNTIME_HASH_MATCH = NOT_APPLICABLE
QLIB_INGESTION = NOT_ATTEMPTED
PACKAGES_CHANGED = NO
SOURCE_CHANGED = NO
LLM_CALLS = NONE
OPENBB_CALLED = NO
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
POC_A = BLOCKED (missing Windows-side Parquet writer)
P0_POC_A_OPENBB_LINUX_QLIB_HANDOFF = BLOCKED
CURRENT_NEXT = P0_POC_A_BLOCKER_RESOLUTION
P0 = IN_PROGRESS
P1 = NOT_STARTED
```
