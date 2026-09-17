# P3 AlphaGen US PIT Thin Adapter POC 001

## Result

The bounded POC stopped at the mandatory feature-space gate before adapter
implementation or RL execution.

AlphaGen at frozen upstream commit
`259687e8f316994426416c530a94842a2fe6405e` exposes the intended external
calculation seam. Its factor pools depend on `AlphaCalculator`, and
`TensorAlphaCalculator` provides the generic IC, RankIC, mutual-IC, and pool
combination calculations. The native CN data path is therefore not an inherent
blocker to an external-calculator integration.

```text
ALPHAGEN_NATIVE_CN_DATA_BLOCKER = NON_BLOCKING_FOR_EXTERNAL_CALCULATOR_INTEGRATION
ALPHAGEN_EXTERNAL_CALCULATOR_INTERFACE = PASS
REQUIRED_DATA_SURFACE = data;n_days;n_stocks;max_backtrack_days;max_future_days
```

## Feature-space blocker

AQ's frozen P2 ragged panel authoritatively supplies only `open`, `high`,
`low`, `close`, and `volume`. It explicitly has no true VWAP and prohibits a
fake VWAP. The build report remains
`D:/AQ_DATA/P2/qlib-native-ragged-panel-001/reports/build-report.json` with
SHA-256
`eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142`.

At the frozen AlphaGen commit, `FeatureType` contains `VWAP`, while
`alphagen/rl/env/wrapper.py` defines the RL feature action count as
`len(FeatureType)`, enables the entire feature-action range, and maps those
actions directly through `FeatureType(action)`. The source exposes no public
or configuration-based feature allowlist. Consequently a compliant POC cannot
exclude VWAP without changing or replacing upstream action-space behavior.

The task contract prohibits an upstream edit, enum monkeypatch, fabricated
VWAP, and a project-owned replacement action-space engine. The correct
fail-closed result is therefore:

```text
VWAP_AVAILABLE = NO
FEATURE_SPACE_COMPATIBLE = NO
FEATURE_SPACE_COMPATIBILITY_BLOCKER = YES
UPSTREAM_MODIFICATION_REQUIRED = YES
ALPHAGEN_UPSTREAM_SOURCE_MODIFIED = NO
AQ_ADAPTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Target and safety authority

The target was resolved unambiguously but was not evaluated because the task
stopped earlier:

```text
TARGET_AUTHORITY = P2_CERTIFICATION_PROTOCOL_V1_QLIB_ALPHA158
TARGET_EXPRESSION = Ref($close, -2)/Ref($close, -1) - 1
TARGET_HORIZON_SESSIONS = 2
AUTHORITATIVE_HISTORY = 2015-01-02_THROUGH_2024-12-31
SEALED_OOS_START_SESSION = 2026-09-14
SEALED_OOS_ROWS_ACCESSED = 0
```

No market rows were loaded, no data was downloaded, no AlphaGen RL environment
or PPO learning cycle was started, no expression was evaluated, and no factor
pool or alpha artifact was created.

## Evidence and direction

Private blocker evidence is frozen under:

`D:/AQ_DATA/P3/alphagen-us-pit-thin-adapter-poc-001`

The canonical summary SHA-256 is:

`a8d5d2084c4ca288b7ffdd3ec9076f25f1c8c942b86388489c421a642ecc2d98`

AlphaGen has not been selected as permanent production authority. AlphaForge
and AlphaGPT remain challengers. The local RD-Agent brain search remains
paused and is not a P3 blocker.

```text
RD_AGENT_LOCAL_BRAIN_SEARCH = PAUSED_NOT_P3_BLOCKER
ALPHAGEN_PERMANENT_AUTHORITY_SELECTED = NO
ALPHAFORGE_CHALLENGER_RETAINED = YES
ALPHAGPT_CHALLENGER_RETAINED = YES
AUTONOMOUS_ATTEMPT_004_AUTHORIZED = NO
CURRENT_NEXT = P3_ALPHAGEN_US_PIT_ADAPTER_BLOCKER_AUDIT_001
FINAL_CLASSIFICATION = FEATURE_SPACE_COMPATIBILITY_BLOCKER
```
