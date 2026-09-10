# P1 PIT US universe/data recovery 001

**Task:** `AUTONOMOUS-QUANT-P1-PIT-US-UNIVERSE-DATA-RECOVERY-001`
**Status:** `BLOCKED — PIT_UNIVERSE`
**Scope:** data infrastructure only; no model, prediction, IC, return, backtest, Sharpe, or P1 protocol work.

## Original blocker and recovery decision

The previous P1 data-protocol attempt failed closed: the Qlib US package ended on 2020-11-10, its bundled `sp500.txt` had no changes after 2020-10-09, and the pinned Qlib index collector interpreted the current page's `MMM` ticker as a date. The old package remains **REFERENCE_BASELINE_ONLY**.

This task created a compact project-owned adapter at `10-data-system/universe/sp500-pit/`. It uses the same Wikipedia source family as Qlib's US index collector but does not patch or otherwise alter the pinned Qlib source. The adapter detects tables by normalized semantic headers rather than column position, expands merged/MultiIndex headers, and fails closed when a required field is missing or ambiguous. In particular, the change date is strictly parsed from the semantic `Date` column; a ticker such as `MMM` cannot be interpreted as a date.

## Frozen evidence and schema

The current page retrieved on 2026-09-10 did not include the required history table. A pre-2025 revision of the same page was therefore frozen as the 2024-cutoff source:

```text
REVISION_ID = 1265285344
REVISION_TIMESTAMP = 2024-12-26T04:36:28Z
SOURCE_URL = https://en.wikipedia.org/w/index.php?oldid=1265285344
HTML_SHA256 = 01002d09e51ba29c81796e2f3bb8e019a36301aecca7c8e14b9d103fb55027fd
PARSER_VERSION = SP500_PIT_PARSER_V1
```

The parser found one current table with `Symbol`, `Security`, and `Date added`, and one history table with `Date`, `Added/Ticker`, `Added/Security`, `Removed/Ticker`, and `Removed/Security`. It recorded their semantic-header fingerprints in the durable source manifest. The frozen source root is `D:\AQ_DATA\P1\universe\sp500_pit_v1`; absolute Windows or WSL paths are excluded from every logical hash.

## Reconstruction contract and result

The adapter uses half-open membership intervals: `[membership_start, membership_end)`. A session is active exactly when the source-reported effective date is at or after the start and before the end. It reconstructs backward from the frozen terminal constituent table, then replays transitions forward. Symbol mapping is a separately versioned structure. It explicitly covers `BRK.B -> BRK-B`, `BF.B -> BF-B`, and detects ticker reuse/share-class cases such as Under Armour and Ingersoll Rand instead of assuming a ticker is a permanent security identity.

The adapter's required terminal-state invariant failed:

```text
FROZEN_CURRENT_CONSTITUENTS = 503
RECONSTRUCTED_TERMINAL_CONSTITUENTS = 511
UNEXPECTED_TERMINAL_IDENTITIES =
  CDAY, DISCK, DLPH, JOYG, KORS, Q, RE, WLTW
PIT_UNIVERSE = BLOCKED
```

The historical page labels its data as selected changes. Its change rows do not fully encode all ticker renames, share-class/corporate transitions, and deletions required to reconstruct the terminal table. The required policy is exact terminal-set equality; the eight extra identities are therefore not silently mapped, dropped, or accepted. Candidate interval and mapping files from the failed reconstruction were removed. Frozen source HTML, the source manifest, and the blocked validation report remain as recoverable evidence.

## Historical cross-check and transition evidence

The old Qlib PIT file was compared as an independent historical reference on 2012-06-29, 2014-06-30, 2016-06-30, 2018-06-29, and 2020-06-30. The candidate replay versus old-Qlib intersections were respectively 485, 485, 488, 489, and 491; the candidate/old active counts were 506/502, 507/501, 511/505, 512/506, and 512/505. These material differences are retained in `validation_report.json` and are not treated as format-only differences.

Eight post-2020 source transitions were independently checked against four official S&P Dow Jones announcement PDFs: two 2021 transitions (SBNY/LEG and SEDG/HBI), two 2022 transitions (FSLR/FBHS and MBC), two 2023 transitions (UBER/SEE and JBL/ALK), and two 2024 transitions (PLTR/AAL and DELL/ETSY). Their effective dates matched the frozen change table:

```text
POST_2020_TRANSITION_CHECKS = 8 PASS
```

The publisher returned HTTP 403 when asked to archive those PDFs directly. The compact transition manifest records each official URL, the observed source check, and that no local PDF/hash is asserted. This transparency does not resolve the separate terminal-state failure.

The retained bounded evidence inventory is five files / 1,915,354 bytes. Its frozen revision HTML hash is the source hash above; the current-page diagnostic HTML hash is `c64fb5da53cd9f48c8c3ee288f6589fb4f65114c0e19928d3ee6122ba56ecd10`; and the blocked validation report hash is `bedfd9766129af082235186ac06a829da4cbfa0dbba1f33c02093471f78bc611`.

## Non-actions and next state

No Yahoo full-union download was started because a final PIT universe is a hard prerequisite. Consequently no final DatasetSnapshot, Alpha158 schema work, labels, market-data coverage, model, prediction, performance measure, backtest, RD-Agent action, OpenBB call, Robinhood action, or trading action occurred. The pinned Qlib worktree remains at `2fb9380b342556ddb50a4b24e4fe8655d548b2b8` and was not modified.

```text
P0 = COMPLETE
P1 = NOT_STARTED
CURRENT_NEXT = P1_PIT_DATA_RECOVERY
DATASET_SNAPSHOT_CREATED = NO
```

The adapter's 19 deterministic offline tests passed. They cover semantic schema parsing, schema drift, the `MMM` regression, backward reconstruction, effective-date/no-future rules, interval validation, mapping/versioning, dot/dash handling, legacy-Qlib comparison, deterministic and path-free hashes, post-2024 exclusion, coverage arithmetic, and terminal-state fail-closed validation.
