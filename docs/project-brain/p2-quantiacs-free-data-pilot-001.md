# P2 Quantiacs Free Data Pilot 001

Status: **COMPLETE — FAIL_FREE_ROUTE_COVERAGE**

Task: `AUTONOMOUS-QUANT-P2-QUANTIACS-FREE-DATA-PILOT-001`

Date: 2026-09-11

Authoritative base: `f7c599959d9f5c955760941b27481a0e6d4a0bd8`

## 1. Decision

The bounded Quantiacs pilot evaluated all seven required scenario classes. The returned rows were structurally sound, reproducibly captured, aligned to XNYS sessions, and consumable by Qlib. The free route nevertheless fails the required episode-coverage gate:

- the accepted historical Qwest `Q` episode had no provider asset/price coverage in its bounded window;
- the accepted `DISCK` episode was missing its final eligible XNYS session, 2022-04-08; and
- the provider's current `META` asset supplied pre-rename prices but reported `is_liquid = 0` for all 60 tested pre-rename `FB` sessions, so it did not independently corroborate continuous membership.

These are detected, explicit gaps. No row was silently filled, no AQ fact was changed, and no alternative provider was added.

```text
QUANTIACS_FREE_DATA_PILOT = COMPLETE
QUANTIACS_TECHNICAL_VALIDATION = FAIL
FINAL_CLASSIFICATION = FAIL_FREE_ROUTE_COVERAGE
QUANTIACS_CLASSIFICATION = RESEARCH_ONLY_NOT_CERTIFICATION_GRADE
RECOMMENDED_CERTIFICATION_DATA_ROUTE = FREE_ROUTE_BLOCKED
CURRENT_NEXT = P2_CERTIFIED_DATA_PROVIDER_DECISION
```

## 2. Ownership and scope

```text
CAPABILITY = P2_QUANTIACS_FREE_CERTIFICATION_DATA_PROVIDER_PILOT
QUANTIACS = UPSTREAM_WHOLE_DATA_PROVIDER
AQ_PIT = AQ_OWNED_THIN_ACCEPTED_DOMAIN_FACTS
PANDERA_EXCHANGE_CALENDARS_DVC = UPSTREAM_LEAF
QLIB = UPSTREAM_WHOLE_CONSUMER
AQ_IMPLEMENTATION = DISPOSABLE_THIN_PILOT_ADAPTER_AND_EVIDENCE_ONLY
CUSTOM_ENGINE_REQUIRED = NO
```

The pilot made only bounded provider calls and retained evidence privately under `D:\AQ_DATA\P2\quantiacs-free-data-pilot-001`. No data row, response byte, API key, cache, or Parquet file entered Git, DVC, MLflow, or any third party.

No Robinhood, broker, account, order, trading, model-training, Alpha158, prediction, backtest, Recorder, or MLflow operation occurred.

## 3. Credential safety

The owner-supplied plaintext key was moved out of `D:\API.txt`, protected with Windows user-scoped DPAPI, and stored under a restricted user-local secrets directory. The plaintext source was removed after a successful encrypted round trip. The key was decrypted only into the child-process environment and was never printed, hashed, measured, or placed in repository or evidence content.

A byte-level exact-secret scan covered all tracked/untracked repository files and all private pilot artifacts. It passed.

```text
QUANTIACS_API_KEY_PRESENT = YES
CREDENTIAL_LEAK_CHECK = PASS
PLAINTEXT_CREDENTIAL_RETIRED = YES
CREDENTIAL_IN_GIT = NO
CREDENTIAL_IN_PRIVATE_EVIDENCE = NO
```

## 4. Pinned isolated runtime

```text
QUANTIACS_REPO = quantiacs/toolbox
QUANTIACS_REPO_SHA = 9e5274c5ce102a66debc799fd2a2300969fb90f6
QUANTIACS_TOOLBOX_VERSION = 0.0.507
QUANTIACS_SOFTWARE_LICENSE = MIT
UV_VERSION = 0.12.9
PYTHON_VERSION = 3.12.14
ISOLATED_RUNTIME = D:\AQ_ENVS\quantiacs-pilot-001
PACKAGE_CHECK = PASS
```

Exact isolated-runtime package freeze:

```text
Bottleneck==1.6.0
cftime==1.6.5
contourpy==1.4.0
cycler==0.12.1
fonttools==4.65.0
kiwisolver==1.5.1
llvmlite==0.49.0
matplotlib==3.11.2
narwhals==2.26.0
numba==0.67.0
numpy==2.2.6
packaging==26.3
pandas==2.2.3
pillow==12.3.0
plotly==6.9.0
progressbar2==4.6.0
pyparsing==3.3.2
python-dateutil==2.9.0.post0
python-utils==4.0.1
pytz==2026.3.post1
qnt==0.0.507
scipy==1.18.1
six==1.17.0
tabulate==0.10.0
typing_extensions==4.16.0
tzdata==2026.3
xarray==2025.12.0
```

No existing AQ environment was modified.

## 5. Provider evidence capture

The metadata request returned 857 assets for the requested 2010-01-01 through 2024-12-31 SPX discovery range. Every provider request recorded request type, body hash, dataset, bounded dates, retrieval timestamp, Toolbox version/SHA, and provider/server asset ID where applicable.

The exact provider-returned decompressed response bytes were retained before parsing and SHA-256 hashed. They are not described as raw transport bytes. Fourteen unique response hashes were observed:

```text
3891648e3b613a3e192b0d4b956e44c4c787b548ec344a2c55fd1cb2bfc353ea
470eba6cf9bc4f9987c4ed9f0ce7497b7ab5e93ca08453d5e6430e0561d845e9
64a918f86678f52bcea64faab5ba45555ae6118531963040b24d9a2a6abb182e
6cd3a6326ff2c691c1a6c4f33eac2788d8461e7fb3983695defee4ec55d383b9
846ea08e7f143e767e09b90b48629510acbabee16265e709aa29235fdc73a027
86c47e9fa70c60e02f05c6e92c9e33134fa7e646e6c5315b448f78749b429890
8729ae84f025fd50d6b092930d98176f042ff6bb28c4288fe750f3a68b606673
8e8f5ffdc5921e7da82da9595d8dfa36d0be7ae4c3c95c5eed946537507d3fdf
917c56779dc5013d19bad6972e7ed36046cacc8bc733fc296b28dcc94e2bd331
93b56b9c01c2d73c5204f5c72fc12aad4e694384bcc7ea45278e7a9dd24fb76c
9957cad794c4f3cdc39768a58941010504f45eec680bd4090cada2ce79b326b7
a0cb00986ccef52ded0936769c6ec8e72fa6537883d62298d33c2d2a6799e782
c411c9d2214abc31319cec601204146bf950cdb80bd822b6ccc539a3fcd6d435
f297f8e96de22b1bc51231de15cf1d45020e119e01930ba24a22e929de79e764
```

The private artifact manifest SHA-256 is `4744f1965f1ca51df5f3091b51b2d914f200fad730759e39c8dc1450c7a07199`. Durable DVC freezing was not attempted because retention rights remain unconfirmed.

## 6. Seven-scenario sample

| Scenario | Accepted AQ episode(s) | Provider asset(s) | Bounded request | Result |
|---|---|---|---|---|
| `ACTIVE` | AAPL | `tts-831814` / `NAS:AAPL` | 2024-07-01–2024-12-20 | 122/122 required sessions; mapped |
| `NORMAL_INDEX_REMOVAL` | CPRI | `tts-157814327` / `NYS:CPRI` | 2020-01-02–2020-07-15 | 90/90 eligible sessions; last liquid 2020-05-11; later prices retained but excluded from episode |
| `TICKER_RENAME` | FB, META | `tts-43902240` / `NAS:FB`; `tts-222568848` / `NAS:META` | 2022-03-15–2022-08-05 | FB asset returned no parseable observations; META supplied 100 prices. AQ rename evidence maps 60 pre-boundary prices to FB, but provider `is_liquid` was 0 on all 60; 40 META sessions mapped from 2022-06-09 |
| `ACQUISITION_OR_CORPORATE_SUCCESSION` | DISCK, WBD | `tts-15427298` / `NAS:DISCK`; `tts-245373754` / `NAS:WBD` | 2022-01-18–2022-06-15 | WBD mapped 46/46 eligible sessions from 2022-04-11; DISCK mapped 57/58 and lacked 2022-04-08 |
| `BANKRUPTCY_OR_TERMINAL_DISTRESS` | PCG pre-exit | `tts-820952` / `NYS:PCG` | 2018-10-15–2019-03-15 | 65/65 eligible sessions; last liquid 2019-01-17; prices continued after removal; no terminal value/return field |
| `TICKER_REUSE` | Qwest Q, Quintiles Q, IQV | `tts-376025814` / `NYS:Q`; `tts-130773564` / `NYS:IQV` | 2010-10-01–2011-05-31 and 2017-08-01–2017-12-29 | current Q provider ID belongs to Qnity and returned no old Qwest coverage; IQV ID mapped by accepted dates to separate Quintiles Q and IQV episodes; no collapse |
| `EXIT_REENTRY` | AMD 2010–2013 and AMD 2017–present episodes | `tts-80383707` / `NAS:AMD` | 2013-06-17–2013-11-29 and 2017-01-03–2017-06-30 | same provider ID mapped by date to two separate AQ episodes; 68/68 and 73/73 eligible sessions; membership gap remained unmapped |

The selected universe comprises 12 required AQ episodes. Eleven have an evidence-bounded provider mapping. Ten have complete price coverage for every required session inside the selected window. The two blocking coverage cases are:

| Episode | Gap |
|---|---|
| `P1EP-4b01343670d58f2834ac593a0475d2a4afa98e731111ef2d29d1db8107874f0b` (Qwest Q) | 0/126 required sessions; provider's current `NYS:Q` identifies a different security |
| `P1EP-fa652ff66a8d91355865906c7b3bcf1c267fcca7e15007a29c34fddbee3b3442` (DISCK) | 57/58 required sessions; 2022-04-08 absent |

```text
PILOT_REQUIRED_SCENARIOS = 7
PILOT_SCENARIOS_EVALUATED = 7
PILOT_REQUIRED_EPISODES = 12
PILOT_MAPPED_EPISODES = 11
PILOT_PRICE_COVERED_EPISODES = 10
PILOT_ACTION_COVERED_EPISODES = 10
PILOT_DELISTED_OR_INACTIVE_EPISODES = 8
PILOT_UNRESOLVED_EPISODES = 2
TICKER_REUSE_COLLAPSE = NO
```

## 7. Identity and membership

Mappings used provider ID, provider metadata, date, accepted AQ episode intervals, and accepted identity evidence. Ticker text alone never authorized a join. The Qwest, Quintiles/IQVIA, and Qnity uses of `Q` remained distinct. The same AMD provider ID was permitted to map to two non-contiguous AQ membership episodes only by date.

Returned provider membership exactly matched AQ episode membership for every tested mapped row except the 60 pre-rename FB rows reconstructed from the current META provider asset. Those price rows were captured and date-mapped with limitation; their provider membership flag remained unchanged at 0 and the mismatch remained visible.

```text
IDENTITY_MAPPING = PARTIAL
AQ_VS_PROVIDER_MEMBERSHIP = PARTIAL
MEMBERSHIP_MISMATCH_ROW_COUNT = 60
UNDATED_TICKER_MAPPING_USED = NO
AQ_FACTS_MODIFIED = NO
```

## 8. Price, action, session, and Pandera validation

The provider returned 916 bounded rows. After accepted episode mapping, 707 rows entered the validated private table and 209 out-of-membership rows remained diagnostic only. No unresolved or out-of-episode row entered the Qlib artifact.

Pandera `0.33.1` validated the required provider ID, episode ID, session, OHLCV, dividend, split cumulative product, membership flag, and mapping-state columns. `exchange_calendars 4.13.2` provided XNYS session authority.

```text
RETURNED_ROW_COUNT = 916
VALIDATED_MAPPED_ROW_COUNT = 707
DIAGNOSTIC_UNMAPPED_ROW_COUNT = 209
DUPLICATE_PROVIDER_ASSET_SESSION = 0
INVALID_XNYS_SESSION = 0
MISSING_INTERNAL_PROVIDER_SESSION = 0
OUT_OF_EPISODE_JOIN = 0
NONFINITE_REQUIRED_PRICE = 0
NEGATIVE_VOLUME = 0
SILENT_FORWARD_FILL = NO
SYNTHETIC_SESSION = NO
PANDERA_VALIDATION = PASS_FOR_MAPPED_ROWS
OHLCV_VALIDATION = PARTIAL_DUE_TO_REQUIRED_EPISODE_COVERAGE_GAPS
```

Two nonzero dividend observations occurred in the active AAPL sample. No sampled window contained a `split_cumprod` transition. On a disposable copy, `provider returned -> restore origin -> reapply split adjustment` had maximum absolute and relative error 0, but this is not evidence for behavior across an actual split event.

```text
DIVIDEND_VALIDATION = PARTIAL
DIVIDEND_EVENT_COUNT = 2
SPLIT_TRANSITION_COUNT = 0
SPLIT_ROUNDTRIP = NOT_OBSERVED
ARITHMETIC_ROUNDTRIP_MAX_ABSOLUTE_ERROR = 0
ARITHMETIC_ROUNDTRIP_MAX_RELATIVE_ERROR = 0
RECONSTRUCTED_PRICE_CLASSIFICATION = DETERMINISTICALLY_RECONSTRUCTED
```

## 9. Terminal-state result

- PCG had a clean observable provider price through AQ's final eligible session and continuing prices after index exit. This permits a clean index-exit observation in the pilot; it does not establish bankruptcy recovery or terminal value.
- CPRI also had a clean price through its final eligible session and later prices.
- DISCK lacked 2022-04-08, AQ's last eligible XNYS session before the 2022-04-11 WBD succession boundary. The provider alone therefore cannot prove a clean tradable exit at the required boundary.
- No Quantiacs field supplied delisting return/value, acquisition cash/stock consideration, bankruptcy recovery, or terminal value.

```text
PCG = CLEAN_TRADABLE_EXIT_BEFORE_TERMINAL_EVENT
CPRI = CLEAN_TRADABLE_EXIT_BEFORE_TERMINAL_EVENT
DISCK_WBD = TERMINAL_OFFICIAL_EVIDENCE_REQUIRED
TERMINAL_STATE = MATERIAL_GAP
```

## 10. Revision/as-of observation

The pinned Toolbox `/last/<timestamp>/` implementation accepted the fixed `2024-12-31T23` boundary. Two uncached requests for the same AAPL window returned the same SHA-256:

```text
ASOF_RESPONSE_HASH_1 = 86c47e9fa70c60e02f05c6e92c9e33134fa7e646e6c5315b448f78749b429890
ASOF_RESPONSE_HASH_2 = 86c47e9fa70c60e02f05c6e92c9e33134fa7e646e6c5315b448f78749b429890
REVISION_SEMANTICS = OBSERVED_REPEATABLE_NOT_VENDOR_VERSIONED
```

This proves only pilot-time repeatability. It does not prove immutable historical vendor vintages or prohibit later corrections/backfills.

## 11. Private artifacts and Qlib handoff

The mapped private Parquet SHA-256 is `23f33d8c80d13e2a92aaba59fcae8c9e8efaa77efcccc1ee3ac79525c640b0b4`. The Qlib-compatible copy uses `(datetime, instrument=episode_id)` and `$open/$high/$low/$close/$volume`; its SHA-256 is `08ea31c510830b64f96c27c675340fd377e05dd146ba06e9abe51e326bac6cdf`.

The accepted WSL Qlib `0.9.8.dev26` environment loaded all 707 rows through public `StaticDataLoader(config=<private parquet>).load()`. Direct and loaded index, columns, dtypes, and values were equal. Qlib did not train, predict, backtest, record, or start MLflow.

```text
QLIB_PILOT_INGESTION = PASS
QLIB_SOURCE_MODIFIED = NO
QLIB_ENVIRONMENT_MODIFIED = NO
MODEL_TRAINING = NO
BACKTEST = NO
RECORDER = NO
MLFLOW = NO
```

## 12. Rights and retention

```text
PRIVATE_DVC_RETENTION = NOT_ATTEMPTED_PENDING_PROVIDER_CONFIRMATION
PUBLIC_DVC = NONE
PUBLIC_UPLOAD = NONE
```

The private pilot evidence is temporary validation evidence only. If the route is ever reconsidered, written provider confirmation remains necessary for:

1. long-term private local retention;
2. private content-addressed/DVC snapshots;
3. private backups;
4. personal quantitative research use;
5. personal live-trading research use; and
6. data/file/hash/metadata retention after account closure.

Because the route already fails required technical coverage, rights confirmation is deferred rather than treated as the immediate next task.

## 13. Final gate and preserved authority

Valid returned rows and a successful Qlib handoff cannot compensate for missing required security episodes or final eligible sessions. `CertificationDataContractV1` remains frozen, the PIT universe remains uncertified, and no provider is promoted.

```text
P2_CERTIFICATION = STARTED / IN_PROGRESS
P2_CERTIFIED_DATA_FOUNDATION = IN_PROGRESS
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PIT_UNIVERSE_CERTIFIED = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
LIVE_CAPITAL = NOT_AUTHORIZED

PROVIDER_CALLED = YES
DATA_DOWNLOADED = YES_BOUNDED_PRIVATE_PILOT_ONLY
MARKET_DATA_IN_GIT = NO
PACKAGE_CHANGED_OUTSIDE_ISOLATED_RUNTIME = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
NO_PRODUCTION_CODE_CHANGED = YES
PUSHED = NO
PR_CREATED = NO
MERGED = NO

FINAL_CLASSIFICATION = FAIL_FREE_ROUTE_COVERAGE
CURRENT_NEXT = P2_CERTIFIED_DATA_PROVIDER_DECISION
```
