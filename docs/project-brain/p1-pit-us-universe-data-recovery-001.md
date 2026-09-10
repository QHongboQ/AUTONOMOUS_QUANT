# P1 PIT US universe/data recovery 001

**Task:** `AUTONOMOUS-QUANT-P1-PIT-US-UNIVERSE-DATA-RECOVERY-001`
**Status:** `BLOCKED — QLIB OVERLAP IDENTITY EVIDENCE`
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

That conclusion is preserved as the original fail-closed result, but its causal label is now `ROOT_CAUSE_NOT_YET_PROVEN`. The mismatch mixed membership events with ticker, name, exchange, share-class, spin-off, merger-successor, and ticker-reuse events. It therefore could not prove that the membership-change table itself was incomplete. The original frozen HTML, manifest, blocked report, and 511-versus-503 evidence remain unchanged in `sp500_pit_v1`.

## Date-effective security identity reconciliation

The adapter now uses `SecurityIdentityMapping`. Its project-owned opaque `AQSEC-*` key is separate from source and market-data symbols. Every transition record has effective bounds, transition type, predecessor/successor references, evidence URL/date/hash where frozen, confidence, and resolution state. Provider formatting (`BRK.B -> BRK-B`, `BF.B -> BF-B`) remains separate from corporate identity. Unresolved identities fail closed.

| Extra | Resolution | Effective evidence |
|---|---|---|
| CDAY | `NAME_AND_TICKER_RENAME` to DAY | Dayforce issuer release; 2024-02-01 |
| DISCK | `MERGER_SUCCESSOR`; Discovery Class C ceased and WBD began as a different successor security | WBD issuer release/FAQ; close 2022-04-08, WBD trading 2022-04-11 |
| DLPH | `SPINOFF`; Delphi Automotive continued as APTV while the spun-off, different Delphi Technologies security reused DLPH | Aptiv issuer release; 2017-12-05 |
| JOYG | `EXCHANGE_OR_SYMBOL_CHANGE` to JOY; later actual S&P removal is already row 2015-10-07 | Joy Global SEC 10-K; JOY trading 2011-12-06 |
| KORS | `NAME_AND_TICKER_RENAME` to CPRI | Capri issuer release; 2019-01-02 |
| Q | `NAME_AND_TICKER_RENAME` from QuintilesIMS/Q to IQV; the earlier Qwest/Q security is distinct | IQVIA issuer release; 2017-11-15 |
| RE | `NAME_AND_TICKER_RENAME` to EG | Everest issuer announcement; 2023-07-10 |
| WLTW | `PURE_TICKER_RENAME` to WTW | WTW issuer release; 2022-01-10 |

The five old hard-coded aliases were removed and audited. FB/META is a same-security ticker change (2022-06-09); ANTM/ELV and VIAC/PARA are name-and-ticker changes (2022-06-28 and 2022-02-17); FLT/CPAY is a name-and-ticker change (2024-03-25). HFC/DINO is a new-parent merger successor (2022-03-15), not a timeless alias; HFC's recorded S&P membership ended in 2021 before that successor event.

The DLPH and Q regressions explicitly prove ticker reuse does not collapse different securities. The market mapper returns FB before META's effective date, CDAY before DAY's, RE before EG's, and APTV for the continuing old Delphi Automotive lineage while keeping the later Delphi Technologies/DLPH identity separate.

The reconciled replay now returns exactly 503 frozen-current and 503 terminal logical identities, with empty missing and unexpected sets. This is generated by auditable transitions, including both Discovery share-class predecessors into WBD; no symbol is manually discarded. The final reconciliation artifacts are isolated under `D:\AQ_DATA\P1\universe\sp500_pit_identity_reconciliation_v4`; the original failure evidence is preserved.

## Historical cross-check and transition evidence

The old Qlib PIT file was re-parsed with its inclusive end dates converted to the project's half-open representation and compared by opaque logical identity on the same five dates. Counts `(new / old / intersection / raw symmetric difference)` are `499/503/485/32`, `500/501/487/27`, `504/506/491/28`, `505/506/492/27`, and `505/504/493/23`.

There are 38 unique unresolved logical identities. The validation report records each opaque ID and its source symbol. Recurring examples include apparent current-symbol backfills in Qlib (`AMCR`, `APTV`, `IQV`, `HWM` starting in 1999), corporate transitions (`MYL/VTRS`, `BLL/BALL`, `LB/BBWI`, `FISV/FI`, `COG/CTRA`), share-class handling (`UA/UAA`), and complex successor/reuse cases (`DOW/DD/DWDP`, `IR`). These are investigation leads, not accepted resolutions: first-party membership/identity evidence is not yet complete for every one. Thus `QLIB_OVERLAP_UNEXPLAINED_DIFFERENCES = 38`; no percentage threshold is used.

Because the Qlib gate remains blocked, this task does not assert that zero actual membership events are missing. `ACTUAL_MEMBERSHIP_EVENTS_MISSING_FROM_WIKIPEDIA = NOT_ESTABLISHED` and `PIT_SOURCE_COMPLETENESS = BLOCKED`. The ticker/name transitions above are expressly not counted as missing membership events.

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

The adapter's 36 deterministic offline tests pass. The original 19 remain, adjusted only for opaque identity fields. Added coverage includes all eight reconciliations, DLPH and Q reuse, pre/post rename market symbols, provider-format separation, mapping evidence, fail-closed unresolved identities, exact terminal 503 equality, and post-reconciliation Qlib comparison. The universe remains blocked by the 38-identity first-party evidence audit.
