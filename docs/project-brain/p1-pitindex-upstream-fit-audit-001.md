# P1 pitindex Upstream Fit Audit 001

**Task:** `AUTONOMOUS-QUANT-P1-PITINDEX-UPSTREAM-FIT-AUDIT-001`  
**Date:** 2026-09-10  
**Scope:** bounded, read-only upstream audit and diagnostic set comparison. No production adapter, universe snapshot, model, performance evaluation, backtest, RD-Agent, broker, account, or trading operation was authorized or performed.

## Decision

`arielNacamulli/pitindex` at `2df030e5c9be7c83cf4b28c3d8597d74d274757e` is **REFERENCE_ONLY** for P1. Its public API is small, deterministic against the pinned bundled bytes, and its engineering checks pass. It is not accepted as the authoritative P1 PIT membership source because the pinned S&P 500 data contains unresolved P1-affecting synthetic history and fails exact independent set comparisons.

The decisive failures are:

- the build reconciles an unexplained present-day `VMRK`/`EQR` discrepancy by inserting `VMRK` at the 2004-12-30 start and removing `EQR` at the 2026-09-07 end; these are synthetic boundary placements, not demonstrated historical effective dates;
- all five pinned `fja05680/sp500` sample comparisons contain the same unexplained extra `VMRK` in pitindex;
- the public history uses the successor ticker before the actual transition for `DLPH → APTV`, `KORS → CPRI`, and `Q → IQV`;
- membership is keyed only by ticker and provides no durable security identity, so ticker reuse and price-panel joins remain an AQ responsibility.

The package may be retained as a comparison oracle, change-event lead, and diagnostic input. It must not be the sole or primary authoritative membership provider, and `pitindex.update()` must not become an AQ authority path. The next step is `P1_PIT_DATA_RECOVERY`.

## Pinned provenance and package profile

| Item | Observed result |
|---|---|
| Repository | `arielNacamulli/pitindex` |
| Pinned source SHA | `2df030e5c9be7c83cf4b28c3d8597d74d274757e` |
| Declared package version | `0.2.1` |
| Git description | `v0.2.1-14-g2df030e` (the audited commit is 14 commits after tag `v0.2.1`) |
| Python requirement | `>=3.11`; classifiers name 3.11 and 3.12 |
| Audit runtime | CPython `3.12.14`, isolated at `D:\AQ_ENVS\pitindex-audit` |
| Runtime dependencies | `pandas>=2.0`, `click>=8.1`, `loguru>=0.7` |
| Optional build dependencies | `requests>=2.31`, `lxml>=5.0`, `beautifulsoup4>=4.12` |
| License | MIT; checked-in `LICENSE` SHA-256 `9fa9b46713cc5ea7f96fba870b31eab585f3d0afe8cc3bfbc13f6563d923d51a` |
| Bundled-data attribution | README identifies Wikipedia under CC BY-SA 4.0 and `fja05680/sp500` under MIT; an adopter must preserve the pinned license/attribution record without making a broader legal conclusion |
| Repository maturity | Early-stage Alpha: created 2026-05-04, one published release (`v0.2.0`), zero stars, one fork, small contributor surface, active weekly refresh automation |
| Maintenance evidence | Pushed 2026-09-07; latest weekly refresh succeeded, but the two preceding scheduled refreshes failed; CI last succeeded on 2026-08-17 |
| AQ adapter complexity | Low-to-moderate mechanically, but unacceptable as authority until data defects and security identity are independently resolved |

The pinned source worktree was clean before and after inspection. The `fja05680/sp500` seed was independently pinned to `a2430f2af0c79ddf0748e91de11bdeb1616ab5a7` and remained clean.

## Engineering gates

The exact checked-out source declared the commands and settings used below. No upstream source was patched.

| Gate | Result |
|---|---|
| CI-declared `pytest --tb=short -q --cov=pitindex --cov-report=term-missing --cov-fail-under=80` | **PASS** — 92 passed in 3.38 s; 84.45% coverage |
| `ruff check .` | **PASS** |
| `ruff format --check pitindex scripts tests` | **PASS** — 22 files already formatted |
| `mypy pitindex` | **PASS** — no issues in 6 source files |
| `uv pip check` | **PASS** — 44 packages compatible |

The public API was called against an explicitly empty cache path, with staleness warnings disabled, so all observations below came from the pinned bundled data. Neither `update()` nor any network rebuild was invoked.

## Coverage and public API observations

The package README describes S&P 500 coverage from 2005-01-03, while `pitindex.info()` and `PitIndex.coverage_start` expose the actual seed date as **2004-12-30**. The pinned data covers 2010 through 2024 and every required call returned successfully.

| As-of date | Constituents |
|---|---:|
| 2010-01-04 | 500 |
| 2012-06-29 | 498 |
| 2014-06-30 | 499 |
| 2016-06-30 | 506 |
| 2018-06-29 | 507 |
| 2020-06-30 | 506 |
| 2021-06-30 | 506 |
| 2022-06-30 | 504 |
| 2023-06-30 | 504 |
| 2024-06-28 | 504 |
| 2024-12-31 | 504 |

All eleven frames had zero duplicate tickers, zero null tickers, and zero duplicate logical rows. Each exposed `as_of` and `build_timestamp_utc` metadata, and `info()` exposed sources, build time, sizes, event count, and reconciliation fields.

The API is an in-memory event walk: bundled seed roster plus ordered add/remove events, keyed by ticker. Weekend/holiday queries use the last event state. The returned frame exposes `as_of` and build timestamp attributes but does not expose row-level event provenance, a logical security ID, or a price identity join key. User cache files override package data when present; therefore any future diagnostic use must pin source SHA, bundled-data hash, cache policy, and exact requested date.

## Bundled-data reproducibility

The pinned bundle authority was restricted to these four Git-tracked files: `sp500_seed.csv`, `sp500_changes.csv`, `sp500_current.csv`, and `build_metadata.json`.

| File | SHA-256 |
|---|---|
| `sp500_seed.csv` | `1a444b80576333455e6a77d24ac12b5eb1095fbdf2d208e1db07396592e3f8aa` |
| `sp500_changes.csv` | `4d5757c55bb1c113fbd5bb15ae4196000e2a87a34271e680435b3b838e8e1456` |
| `sp500_current.csv` | `f3beb7103bb7e65b0097f909b10cfafdae8b5a17d3e1560d170800026afdc392` |
| `build_metadata.json` | `6e15a4fb95152c20376dd4339c4d000dc6cbf6dfa8da88c1a573975efca2a3f4` |
| Canonical filename-plus-bytes bundle hash | `88a44f471ffe79b4438e5992dc9b6a1f40c00074bfce8454ea18897bd753e408` |

These bytes are reproducible from the pinned clean Git commit. This proves byte reproducibility only; it does not validate the historical truth of the contents.

## Build design and unresolved reconciliation events

The upstream design derives the S&P 500 seed and pre-2019 event differences from `fja05680/sp500`, then uses Wikipedia current/changes data and curated rename/manual-event CSVs. It walks the event log to the current roster and permits a reconciliation difference up to 5%. Remaining current-roster differences are closed with synthetic events at the start or end boundary.

For the pinned S&P 500 build:

- current-build diff ratio: `0.007952286282306162` (0.80%);
- synthetic events: **2**;
- synthetic start add: `VMRK` on 2004-12-30 because it is present in the current roster but absent from the event walk;
- synthetic end remove: `EQR` on 2026-09-07 because it is absent from the current roster but present after the event walk;
- invalid removals: `LEHMQ` on 2008-09-15 and 2008-09-17;
- the curated path converts `LEHMQ → LEH` at the seed boundary and removes `LEH` on 2008-09-15, so the public result uses the period-correct `LEH`; the two invalid `LEHMQ` removals remain explicit build anomalies.

Both synthetic events are unresolved and P1-affecting. Placing a current ticker at the coverage start and a removal at the build end creates historical membership assertions that were not independently established. A sub-5% terminal reconciliation threshold is not an acceptable substitute for exact PIT provenance in the P1 universe authority.

## Independent pinned fja05680 comparison

The comparison normalized only the seed's documented `-YYYYMM` future-removal suffix and selected the most recent pinned snapshot on or before each requested date. No fuzzy or identity mapping was used.

| Requested date | Seed effective date | pitindex | fja | Exact difference |
|---|---|---:|---:|---|
| 2010-06-30 | 2010-06-29 | 500 | 499 | pitindex-only `VMRK` |
| 2012-06-29 | 2012-06-29 | 498 | 497 | pitindex-only `VMRK` |
| 2014-06-30 | 2014-06-24 | 499 | 498 | pitindex-only `VMRK` |
| 2016-06-30 | 2016-06-27 | 506 | 505 | pitindex-only `VMRK` |
| 2018-06-29 | 2018-06-26 | 507 | 506 | pitindex-only `VMRK` |

Result: **5 samples, 5 unexplained exact-set failures**. This is consistent with the build log's synthetic start event and fails the task's strict authority gate.

## Known ticker-transition checks

Each check queried immediately before and on/after the transition encoded by the public event history. PASS requires old present/new absent before and old absent/new present after.

| Transition | Membership result | Upstream mechanism and direct observation |
|---|---|---|
| `FB → META` | RESOLVED / PASS | `ticker_renames.csv`; boundary 2022-06-09 behaves correctly |
| `CDAY → DAY` | RESOLVED / PASS | precise source event; public boundary 2024-02-01 behaves correctly (the later curated rename is a no-op) |
| `RE → EG` | RESOLVED / PASS | `ticker_renames.csv`; boundary 2023-03-09 behaves correctly |
| `KORS → CPRI` | **NOT RESOLVED / FAIL** | on 2018-12-31 `CPRI` is already present and `KORS` absent; seed-derived history adds `CPRI` in 2016 and removes `KORS` in 2018 |
| `WLTW → WTW` | RESOLVED / PASS | precise source event; public boundary 2022-01-10 behaves correctly (the later curated rename is a no-op) |
| `DLPH → APTV` | **NOT RESOLVED / FAIL** | on 2017-12-04 `APTV` is already present and `DLPH` absent; seed-derived history adds `APTV` in 2012 |
| `Q → IQV` | **NOT RESOLVED / FAIL** | on 2017-11-05 `IQV` is already present and `Q` absent; seed-derived history adds `IQV` in August 2017 |
| `DISCK → WBD` | RESOLVED / PASS | precise source event; boundary 2022-04-11 behaves correctly |

These failures are consistent with the seed's use of future/current ticker labels in historical snapshots. The API has no durable entity/security identity layer to distinguish a rename, merger successor, spin-off, or later reuse of the same ticker. `PIT_MEMBERSHIP_TICKER_REUSE_AMBIGUITY = YES`; `PRICE_SECURITY_IDENTITY_STILL_REQUIRED = YES`.

## AQ diagnostic comparison

The old AQ self-built PIT branch and its preserved output were used only as diagnostics. It was not promoted, repaired, or treated as authority. Raw source-symbol sets differed on all six required dates:

| Date | pitindex count | AQ count | pitindex-only / AQ-only |
|---|---:|---:|---:|
| 2020-06-30 | 506 | 503 | 18 / 15 |
| 2021-06-30 | 506 | 503 | 16 / 13 |
| 2022-06-30 | 504 | 502 | 13 / 11 |
| 2023-06-30 | 504 | 502 | 12 / 10 |
| 2024-06-28 | 504 | 502 | 12 / 10 |
| 2024-12-31 | 504 | 502 | 10 / 8 |

The pattern is dominated by temporal ticker-label policy differences (`FB/META`, `DLPH/APTV`, `Q/IQV`, `WLTW/WTW`, and others), plus `VMRK`. It confirms that exact membership and security identity must be resolved from first-party evidence rather than selecting either diagnostic output by overlap percentage.

## Old Qlib diagnostic comparison

The preserved Qlib `sp500.txt` was also diagnostic only. Raw sets differed on all five required dates:

| Date | pitindex count | Qlib count | pitindex-only / Qlib-only |
|---|---:|---:|---:|
| 2012-06-29 | 498 | 503 | 27 / 32 |
| 2014-06-30 | 499 | 502 | 21 / 24 |
| 2016-06-30 | 506 | 507 | 18 / 19 |
| 2018-06-29 | 507 | 507 | 16 / 16 |
| 2020-06-30 | 506 | 505 | 3 / 2 |

The differences are primarily historical ticker backfill/identity representation, with possible membership differences mixed in; the files do not provide enough first-party evidence to classify every row. This old Qlib instrument file is not an independent authority and cannot cure pitindex's provenance or identity defects.

## Ownership boundary and next step

If retained, pitindex may provide only versioned membership-candidate evidence. AQ must own:

- accepted source hierarchy and exact PIT effective-date policy;
- security master, durable security identifiers, symbol intervals, and price-identity joins;
- first-party exception evidence and rejection/acceptance authority;
- immutable snapshot manifests with source SHA, data hashes, query date, and adapter version;
- explicit prohibition on an unpinned user-cache or `update()` result becoming authoritative.

No adapter or snapshot is implemented by this task. Because the strict authority gate fails, no universe snapshot is authorized. P1 itself remains not started.

```text
PITINDEX_DECISION = REFERENCE_ONLY
PITINDEX_SHA = 2df030e5c9be7c83cf4b28c3d8597d74d274757e
FJA_SEED_SHA = a2430f2af0c79ddf0748e91de11bdeb1616ab5a7
PINNED_DATA_HASH = 88a44f471ffe79b4438e5992dc9b6a1f40c00074bfce8454ea18897bd753e408
PINNED_DATA_REPRODUCIBLE = YES
CURRENT_BUILD_SYNTHETIC_EVENTS = 2
P1_AFFECTING_SYNTHETIC_EVENTS_UNRESOLVED = YES
PIT_MEMBERSHIP_TICKER_REUSE_AMBIGUITY = YES
PRICE_SECURITY_IDENTITY_STILL_REQUIRED = YES
P0 = COMPLETE
P1 = NOT_STARTED
CURRENT_NEXT = P1_PIT_DATA_RECOVERY
MODEL_TRAINED = NO
PERFORMANCE_EVALUATED = NO
BACKTEST_RUN = NO
RDAGENT_EXECUTED = NO
PR_CREATED = NO
MERGED = NO
```
