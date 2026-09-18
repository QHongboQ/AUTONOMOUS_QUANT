# P2 Formulaic Alpha Protocol V2 Activation 001

Status: **COMPLETE — PROTOCOL V2 ACTIVE, SEALED OOS CLOCK STARTED**

Date: 2026-09-18

## Authority result

```text
TASK = P2_FORMULAIC_ALPHA_PROTOCOL_V2_ACTIVATION_001
BASE_MAIN = 9f97c1dc9fd419cadb5bb5a9a304505a5d87411b
MERGE_PR = 47
MERGE_METHOD = SQUASH
PROTOCOL_V2_VERSION = P2_CERTIFICATION_PROTOCOL_V2
PROTOCOL_V2_SHA256 = 18b80277b6529422298e43681bb344e54199a58477cdba20d96fd8220bdc950a
COHORT_MANIFEST_SHA256 = 53920302856592fb43bbffb011423731893ac0a995a04194541c39d69ecfde70
PROTOCOL_V2_ACTIVATION = COMPLETE
CERTIFIED_CANDIDATE_COUNT = 0
```

## Main-side freeze anchor

PR #47 was squash-merged into `main`.

```text
FREEZE_MERGE_SHA =
9f97c1dc9fd419cadb5bb5a9a304505a5d87411b

FREEZE_MERGED_AT_UTC =
2026-09-18T07:50:31Z
```

The merge-anchor interpretation follows the established Protocol V1 precedent:
the authoritative freeze anchor is the first `origin/main` commit proven to
contain the exact frozen protocol content.

Post-merge verification confirmed that the Protocol V2 and Formulaic cohort Git
blobs are byte-identical to the frozen pre-merge blobs. Therefore the frozen
content authorities remain:

```text
PROTOCOL_V2_SHA256 =
18b80277b6529422298e43681bb344e54199a58477cdba20d96fd8220bdc950a

COHORT_MANIFEST_SHA256 =
53920302856592fb43bbffb011423731893ac0a995a04194541c39d69ecfde70
```

No repository merge-policy weakening was used.

## XNYS activation

The frozen calendar authority remains:

```text
CALENDAR = exchange_calendars 4.13.2 / XNYS
```

The merge occurred at 07:50:31 UTC on 2026-09-18. The 2026-09-18 XNYS
session opens later that day, so it is the first qualifying session strictly
after the freeze entered `origin/main`.

```text
SEALED_OOS_START_SESSION = 2026-09-18
MINIMUM_SEALED_OOS_SESSIONS = 126
PRE_ACTIVATION_SESSIONS_COUNT = 0
EARLY_RESULT_ACCESS = PROHIBITED
INTERMEDIATE_PEEK = PROHIBITED
ONE_SHOT_RELEASE = YES
REUSE_FOR_RETUNING = PROHIBITED
```

The activation record is separate from the immutable Protocol V2 and uses the
same bounded ten-field convention established by Protocol V1.

```text
ACTIVATION_FILE =
40-certification-system/protocol/p2-certification-protocol-v2-activation.json

ACTIVATION_SHA256 =
ff3356850e2a6799c1a8827c0c9aa93e1b54e991d54bca10329471f40abcf9ae
```

## Formulaic cohort state

```text
FORMULAIC_COHORT_COUNT = 17
FORMULAIC_CURRENT_ELIGIBILITY = ELIGIBLE_UNDER_P2_CERTIFICATION_PROTOCOL_V2
CERTIFIED_CANDIDATE_COUNT = 0
P2_SELECTS_CHAMPION = NO
P4_REAL_SHADOW_EVIDENCE_COUNT = 0
P4_REAL_CHAMPION_COUNT = 0
```

All 17 candidates remain frozen equal-status members of the cohort. No
candidate may be removed, substituted, re-ranked, or released early before the
one-shot sealed-OOS release.

## V1 independence

```text
PROTOCOL_V1_MODIFIED = NO
V1_ACTIVATION_MODIFIED = NO
V1_SEALED_OOS_START_SESSION = 2026-09-14
V1_CLOCK_RESET = NO
```

Protocol V1 continues independently for its original cohort.

## Non-actions

```text
SEALED_OOS_ACCESSED = NO
HISTORICAL_TEST_PERFORMANCE_ACCESSED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
CERTIFICATION_DECISION_EXECUTED = NO
CERTIFIED_CANDIDATE_COUNT = 0
REAL_SHADOW_CREATED = NO
REAL_CHAMPION_CREATED = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
LIVE_CAPITAL = NOT_AUTHORIZED
```

Activation starts the prospective time boundary. It does not inspect, compute,
or release sealed-OOS results.

## Next

```text
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
```

The Formulaic cohort must accumulate at least 126 XNYS sessions under the
frozen V2 boundary. Early or intermediate result access remains prohibited.
Other project development may be planned separately, but no V2 certification
decision may be made before the one-shot release conditions are satisfied.
