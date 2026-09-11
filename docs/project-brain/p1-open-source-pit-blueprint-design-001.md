# P1 Open-Source PIT Blueprint Design 001

**Task:** `AUTONOMOUS-QUANT-P1-OPEN-SOURCE-PIT-BLUEPRINT-DESIGN-001`  
**Date:** 2026-09-10  
**Scope:** architecture and audit only. No PIT runtime, source refresh, price acquisition, model, Alpha158, label, backtest, performance evaluation, RD-Agent, broker, account, PR, or merge operation was performed.

## Decision

The final P1 design is an open-source-assisted, evidence-preserving S&P 500 membership pipeline whose project-owned identity boundary is **`InstrumentEpisodeV1`**, not a permanent Security Master.

Upstreams supply pinned historical snapshots, precise membership-event evidence, rename evidence, and useful failure patterns. AQ supplies a thin canonical ingestion boundary, deterministic episode construction, explicit correction overlays, strict validation, immutable snapshot manifests, and the Qlib handoff. AQ does not rebuild a Wikipedia history parser, maintain a corporate-lineage graph, or decide truth by majority vote.

```text
pinned raw sources
  -> canonical base membership + typed evidence events
  -> ticker-episode overlay
  -> official membership-correction overlay
  -> strict reconciliation gates
  -> resolved InstrumentEpisodeV1 rows
  -> immutable DatasetSnapshot
  -> later market-data episode join
  -> later Qlib handoff
```

This design is complete. Implementation remains not started. `P0 = COMPLETE`, `P1 = NOT_STARTED`, and `CURRENT_NEXT = P1_PIT_DATA_RECOVERY`.

## Audited reference ledger

The following commits are the exact design references observed during this task. Unpinned branch names are not authorities.

| Reference | Audited provenance | License observation | Accepted role | Explicit limit |
|---|---|---|---|---|
| [arielNacamulli/pitindex](https://github.com/arielNacamulli/pitindex) | `2df030e5c9be7c83cf4b28c3d8597d74d274757e`, package `0.2.1` | MIT; bundled-data README attributes FJA as MIT and Wikipedia as CC BY-SA 4.0 | Design/reference: seed-plus-event reconstruction, curated rename/manual overlays, deterministic bundle, reconciliation reporting, fail-loud threshold pattern | Final output is `REFERENCE_ONLY`: its 5% gate and synthetic boundary corrections are not AQ authority |
| [fja05680/sp500](https://github.com/fja05680/sp500) | `a2430f2af0c79ddf0748e91de11bdeb1616ab5a7` | MIT | Candidate historical snapshot seed and immutable raw input | Snapshot tickers include `-YYYYMM` annotations and known modern/current-ticker backfill; never use directly as permanent identity |
| [shardul0701/SP500-Survivorship-bias-data-2004-2026](https://github.com/shardul0701/SP500-Survivorship-bias-data-2004-2026) | `7920e8e5a9c62d2a39c9df30dea0e133684b43f5` | No repository-level license or GitHub SPDX metadata observed; embedded FJA source has an MIT attribution file | Strong workflow/reference: yearly Jan-1 roster plus effective-date changes, official S&P registry/reconciliation, retained raw evidence, `manual_review_required`, correction mode, validation, review PR | No code or repository curation copied; candidate data must receive separate license/provenance acceptance |
| [shawnlinxl/snp-history](https://github.com/shawnlinxl/snp-history) | `bbf5a18e8c4a5277ecc7a06ebdfc7b547537b8c5` | No license file or GitHub SPDX metadata observed | Evidence/reference for separate announcement date, implemented date, session-boundary text, PIT tickers, and 2000–2016 changes | README says pre-2017 data is unverified and dates may be inaccurate; reference lead, not authority |
| [Quant-Lodge/ticker-reference-data](https://github.com/Quant-Lodge/ticker-reference-data) | `a1124faafe3992f7c2db38d04cfbc760d98f3f87` | No license file or GitHub SPDX metadata observed | Supplemental CIK-backed rename clue and immutable dated-release consumption pattern | Not an S&P membership source; current map is incomplete and may contain unresolved/flat-file-only rows; no code/data adoption without license clearance |
| [quantopian/zipline AssetFinder](https://github.com/quantopian/zipline/blob/014f1fc339dc8b7671d29be2d85ce57d3daec343/zipline/assets/assets.py) | `014f1fc339dc8b7671d29be2d85ce57d3daec343` | Apache-2.0 | Conceptual model: stable asset key, date-bounded symbol ownership, date-required lookup when a symbol has multiple owners, fail on ambiguity | P1 does not adopt Zipline or reproduce its full AssetFinder/database |

License status is part of source eligibility, not a guess. A missing license is recorded as **not granted/unclear for copying**, without making a broader legal conclusion. Such repositories may inform architecture and lead evidence discovery; only separately accepted bytes may enter an authoritative DatasetSnapshot.

## Final P1 identity model: `InstrumentEpisodeV1`

P1 deliberately rejects a full, permanent corporate/security master. One row represents one contiguous interval during which a particular ticker episode is valid and eligible for the index.

| Field | Contract |
|---|---|
| `episode_id` | Deterministic opaque ID, `P1EP-` plus SHA-256 over the canonical episode key and schema version; never derived from ticker alone |
| `source_ticker` | Exact ticker token from the accepted raw membership evidence |
| `normalized_ticker` | Formatting-only canonical token used at the Universe boundary; normalization cannot imply corporate identity |
| `valid_from` | Inclusive first trading-session label on which this ticker episode is valid |
| `valid_to` | Exclusive first trading-session label on which this ticker episode is no longer valid |
| `membership_from` | Inclusive first session for which this episode is S&P 500 eligible |
| `membership_to` | Exclusive first session for which it is no longer eligible |
| `membership_source` | ID of the accepted base snapshot/event/correction that establishes membership |
| `ticker_source` | ID of the accepted rename/reuse evidence that establishes ticker validity |
| `source_event_ids` | Ordered, deduplicated IDs of all source and overlay events contributing to the row |
| `provenance_hash` | SHA-256 of canonical raw-evidence hashes, event rows, policy version, calendar version, and overlay records |
| `resolution_state` | `RESOLVED`, `MANUAL_REVIEW_REQUIRED`, or `REJECTED`; only `RESOLVED` enters a DatasetSnapshot |

Required invariants:

- all intervals are half-open, `[from, to)`;
- `valid_from <= membership_from < membership_to <= valid_to` for every resolved row;
- an `episode_id` has exactly one ticker-validity interval and one contiguous membership interval;
- a membership exit and later re-entry creates a new episode row even if the ticker text is unchanged;
- the same ticker text may identify multiple non-overlapping episodes, including different securities;
- overlapping resolved ownership of the same normalized ticker is forbidden;
- no global `ticker -> security` mapping exists in P1;
- no episode ID asserts that two ticker episodes share one corporate lineage.

### Rename policy

A normal ticker rename closes the old episode at the effective session boundary and opens a new episode at the same boundary. Continuous index membership is represented by adjacent membership intervals; it is **not** encoded as an index removal/addition unless membership evidence independently says so.

Examples: `FB` then `META`; `KORS` then `CPRI`; `RE` then `EG`. P1 does not stitch either pair into a permanent company record. If later research needs economic continuity across episodes, that is a future Asset Master contract outside P1.

### Ticker reuse policy

A reused symbol always creates separate episode IDs. `DLPH` for old Delphi Automotive and later `DLPH` for Delphi Technologies cannot share an episode. `Q` for Qwest and `Q` for the Quintiles/IQVIA lineage cannot share an episode. A query without a date that matches more than one episode must raise `AMBIGUOUS_TICKER_EPISODE`; it must not choose the newest or longest interval.

The Universe module answers only: **which ticker episode is eligible on date t?** It does not answer which episodes belong to the same economic company.

## Typed event separation

Three evidence tables remain structurally separate:

1. `INDEX_MEMBERSHIP_EVENT`: index, action (`ADD`/`REMOVE`), announcement date if known, effective date, session-boundary semantics, ticker as published, source ID, evidence hash.
2. `TICKER_IDENTITY_EVENT`: old ticker, new ticker, announcement date if known, effective date, session boundary, evidence anchors such as CIK when available, source ID, evidence hash, and ambiguity state.
3. `CORPORATE_ACTION_EVENT`: merger, spin-off, acquisition, reorganization, or other action and its source evidence. It is contextual evidence only in P1.

A ticker identity event never manufactures an index membership event. A corporate action never implies membership transfer. Only an explicit index membership source may add or remove membership.

## Deterministic source precedence

Precedence is by provenance and source role, never by source count:

1. **Historical base seed:** a pinned, licensed, mature historical snapshot series (initial candidate: pinned FJA bytes) establishes the provisional roster state.
2. **Precise membership events:** pinned effective-date add/remove evidence updates the base. The Shardul and snp-history datasets are evidence leads/patterns; only accepted licensed rows with retained raw evidence enter authority.
3. **Official conflict resolution:** a retained S&P Global/S&P DJI announcement resolves a membership conflict only for the facts and effective boundary it explicitly states. It does not bless unrelated rows.
4. **Ticker episode overlay:** evidence-backed rename/reuse rows transform ticker labels by date without changing membership. Official issuer/exchange/SEC evidence is preferred; curated open-source and CIK mappings are supporting evidence.
5. **Official membership correction overlay:** a reviewed, content-addressed correction closes an omission or conflict without rewriting the base.
6. **Reference/fallback only:** Qlib `sp500.txt`, pitindex final output, the old AQ experimental reconstruction, and unlicensed/unverified community rows may trigger investigation but cannot resolve a gate.

An ancestry registry records derived-from relationships. Pitindex and Shardul both inherit FJA history; agreement among them is one source lineage, not three votes. Majority voting is prohibited.

## Generic current-ticker-backfill detection and correction

The correction is data-driven and applies to any evidence-backed rename, not a hard-coded symbol list.

### Detection

For every accepted `TICKER_IDENTITY_EVENT(old, new, effective_session)`:

1. scan every base snapshot and membership event for `new` at a session before `effective_session`;
2. scan for `old` at or after the boundary;
3. compare adjacent snapshots to distinguish a label-only change from a real membership add/remove;
4. verify evidence anchors and check whether either ticker was reused by another issuer/episode;
5. emit `FUTURE_TICKER_BEFORE_RENAME`, `STALE_OLD_TICKER_AFTER_RENAME`, or `AMBIGUOUS_REUSE` findings. No row is changed during detection.

### Overlay correction

When evidence proves a label-only rename and no independent membership change exists:

```text
raw membership contains NEW at t < effective_session
  -> preserve raw row and hash
  -> overlay maps NEW observation to OLD episode for t
  -> close OLD episode at effective_session
  -> open NEW episode at effective_session
  -> carry membership continuously across adjacent episodes
```

The overlay references the raw row, rename evidence, effective boundary, and evidence hashes. If the predecessor is missing, multiple predecessors are plausible, CIK/name evidence conflicts, the ticker is reused, or session timing is unclear, the row becomes `MANUAL_REVIEW_REQUIRED` and no resolved universe is emitted.

The mandatory regression examples are `APTV` before 2017-12-05, `CPRI` before 2019-01-02, and `IQV` before 2017-11-15. The algorithm is generic; these symbols are tests, not conditional branches.

## Time semantics

Both `announcement_date` and `effective_date` are retained when available. Announcement date never controls eligibility. A source event also carries its raw timing phrase and a normalized boundary enum:

- `BEFORE_MARKET_OPEN`: active beginning with that date's trading session;
- `AFTER_MARKET_CLOSE`: active beginning with the next session after that date;
- `EFFECTIVE_SESSION`: active beginning with the explicitly named trading session;
- `SOURCE_DEFINED`: transformed only by a pinned, documented source rule;
- `AMBIGUOUS`: fail closed and require manual review.

Calendar conversion records the exchange calendar/version and the derived inclusive session label. Membership removal ends at the same exclusive boundary at which the replacement may begin. Dates that are holidays/weekends cannot be silently treated as sessions.

## Immutable evidence and correction model

```text
base_membership
  + ticker_episode_overlay
  + official_membership_corrections
  = resolved PIT universe
```

Raw evidence is immutable and content-addressed. Its manifest records source URL/repository, source SHA/revision or immutable release, retrieval timestamp, media type, byte length, SHA-256, license/attribution observation, parser/adapter version, and ancestry.

Corrections never edit raw history. Each correction row requires:

- deterministic `correction_id`;
- target source/event/episode IDs and explicit operation;
- reason and conflict classification;
- source URL or repository plus SHA/revision/release;
- announcement date when known, effective date, raw timing phrase, and resolved session boundary;
- evidence SHA-256 where feasible;
- review state and linked regression-test ID.

Manual correction is allowed only for a documented omission or conflict with supporting evidence. No `if symbol == ...` exception is permitted in Python. An unapplied, rejected, or unresolved correction remains visible in the final evidence manifest.

## AQ reconciliation gates

All gates are fail-closed. Counts and ratios are diagnostics only; no tolerance may hide an unexplained membership defect.

| Gate | Required result |
|---|---|
| Year-to-year continuity | Dec-31 resolved state exactly equals the next year's opening state after applying only explicit boundary events |
| Member-count sanity | Every count lies within the versioned expected envelope; every count jump is exactly explained by events |
| Duplicate membership | No duplicate episode/date membership and no duplicate canonical event |
| Duplicate ticker episode | No duplicate episode key; re-entry is explicit rather than collapsed |
| Future ticker detection | No successor ticker appears before its evidence-backed effective session |
| Ticker reuse overlap | No normalized ticker has overlapping resolved episodes; undated lookup is ambiguous when multiple episodes exist |
| Add-present | Zero unexplained additions of an already-active episode |
| Remove-absent | Zero unexplained removals of an inactive episode |
| Terminal roster | Exact set equality against the pinned accepted terminal official roster |
| Historical samples | Exact set equality against pre-registered, independent, evidence-backed samples; every difference classified and resolved |
| Manual correction evidence | Every applied correction has complete source, date, reason, hash, deterministic ID, and regression coverage |
| Provenance ancestry | No shared-descendant sources counted as independent confirmation |
| Snapshot determinism | Same pinned inputs, policy, adapter, and calendar produce byte-identical rows and manifest hash |

Any unexplained set difference blocks DatasetSnapshot publication. A synthetic start/end event is forbidden unless it is an explicit evidence-backed correction with a real effective boundary.

## Data-model and price-handoff boundary

| Module | Sole question | P1 rule |
|---|---|---|
| Universe | Which ticker episode is eligible on date `t`? | Returns resolved `episode_id` plus ticker and membership bounds |
| Market data | Which bars belong to that episode? | Joins only within the episode's valid interval; provider symbol mapping is date-bounded |
| Future Asset Master | Which episodes belong to the same company/security lineage? | Out of P1; no implicit continuity |

After a rename, the new episode does not inherit pre-rename feature history. This conservative loss of history is acceptable for P1. `MIN_HISTORY_REQUIRED` is a required future protocol parameter, expressed in completed trading sessions and recorded in the DatasetSnapshot/pipeline policy. Until the new episode satisfies it, the episode is ineligible for features that need that lookback.

No prices may be stitched across ticker episodes unless a later, explicit, independently validated Asset Master layer authorizes the link. This prevents look-ahead, recycled-ticker contamination, and accidental corporate-lineage assumptions.

## Open-source responsibility matrix

| Function | Upstream owns | AQ owns | Reference/fallback | Not in P1 |
|---|---|---|---|---|
| Historical membership seed | Pinned licensed snapshot producer | Pinning, raw manifest, accepted coverage floor | FJA primary candidate; Shardul representation; pitindex/Qlib comparison | Rebuilding a general web-history archive |
| Membership change events | Evidence publishers with precise effective dates | Canonical event adapter and source-role acceptance | Shardul/snp-history leads; pitindex comparison | Inferring events from prices |
| Ticker rename evidence | Issuer/exchange/SEC and curated upstream evidence | Typed rename table, date/session normalization, ambiguity gate | Quant-Lodge CIK cache and pitindex rename list | Permanent corporate lineage |
| Official conflict resolution | S&P Global/S&P DJI announcement content | Retention, hashing, narrow parser/adapter, reviewed correction overlay | Shardul source registry/workflow pattern | Majority voting |
| Ticker episode construction | None | Generic deterministic `InstrumentEpisodeV1` compiler | Zipline ownership-period semantics | Full AssetFinder/security master |
| Corporate identity | None | Nothing beyond preserving contextual evidence | Corporate-action event may explain a conflict | Company/security lineage graph |
| Price acquisition | Later selected market-data provider | Episode-bounded request/join and snapshot hash | Existing OpenBB handoff design | Cross-episode stitching |
| PIT validation | Upstreams may publish tests/reports | Strict independent gates and regression matrix | pitindex/Shardul validator patterns; Qlib/AQ diagnostics | Percentage-based unexplained acceptance |
| DatasetSnapshot | None | Immutable resolved rows, manifests, policy/calendar/source hashes | None | Mutable latest-cache authority |
| Qlib handoff | Qlib consumes a prepared universe artifact | Deterministic conversion from accepted DatasetSnapshot | Old Qlib file diagnostic only | Qlib reconstructing membership |

## Migration from experimental branch `702116b2`

The old branch remains `DIAGNOSTIC_REFERENCE_ONLY / DO_NOT_EXTEND`. Its components are classified as follows:

| Existing component | Classification | Migration action |
|---|---|---|
| `canonical.py` | **KEEP** | Retain canonical JSON/hash primitives after schema-version tests |
| `parser.py` | **DIAGNOSTIC_ONLY** | Preserve fixtures and the `MMM` fail-closed regression; do not retain a project-owned Wikipedia reconstruction parser in the final path |
| `identity.py` | **REWRITE_USING_UPSTREAM_PATTERN** | Replace hard-coded corporate keys, timelines, and symbol conditionals with `InstrumentEpisodeV1` plus evidence tables |
| `reconstruct.py` | **REWRITE_USING_UPSTREAM_PATTERN** | Replace terminal-state reverse reconstruction and corporate stitching with base snapshot + typed events + generic overlays |
| `validate.py` | **KEEP** | Salvage half-open interval, overlap, duplicate, unresolved, terminal, and diagnostic comparison ideas; adapt to episode/event schemas and stricter gates |
| `cli.py` | **REWRITE_USING_UPSTREAM_PATTERN** | Make a deterministic compiler/validator over pinned manifests; remove direct HTML reconstruction authority |
| `__init__.py` | **DELETE_FROM_FINAL_DESIGN** | Replace exports only when the new module exists; no legacy API compatibility requirement |
| `tests/test_sp500_pit.py` | **REWRITE_USING_UPSTREAM_PATTERN** | Keep valid generic invariants and fixtures; replace identity-continuity assertions with episode-boundary assertions |
| old generated intervals/mappings/reports | **DIAGNOSTIC_ONLY** | Retain outside authority for comparison; never migrate their IDs or truth assertions into the final snapshot |
| old README/CLI contract | **DELETE_FROM_FINAL_DESIGN** | Superseded by this blueprint and a future implementation contract |

Validation is salvaged where it states general invariants. Architecture is not preserved merely because code exists.

## Frozen pre-implementation regression matrix

| ID | Case | Required result |
|---|---|---|
| R01 | `MMM` in a date field | Reject as an unparseable date; never interpret ticker text as a month/date |
| R02 | `FB → META` | Adjacent, different episode IDs at the evidence-backed boundary; no membership gap invented |
| R03 | `CDAY → DAY` | Adjacent episodes; successor absent before boundary |
| R04 | `RE → EG` | Adjacent episodes using the independently accepted effective date |
| R05 | `WLTW → WTW` | Adjacent episodes; announcement date cannot activate the successor early |
| R06 | `KORS → CPRI` | Adjacent episodes at 2019-01-02; no early `CPRI` |
| R07 | `Q → IQV` | Quintiles `Q` episode ends and `IQV` begins at 2017-11-15; Qwest `Q` remains a different episode |
| R08 | old/new `DLPH` | Delphi Automotive and Delphi Technologies receive different episode IDs with no ownership overlap |
| R09 | `DISCK → WBD` | Corporate successor context does not auto-transfer membership; only explicit membership evidence opens `WBD` |
| R10 | APTV historical guard | `APTV` must not appear before 2017-12-05 |
| R11 | CPRI historical guard | `CPRI` must not appear before 2019-01-02 |
| R12 | IQV historical guard | `IQV` must not appear before 2017-11-15 |
| R13 | generic ticker reuse | Reused ticker produces distinct episode IDs; undated lookup fails ambiguous; overlapping ownership blocks snapshot |

Regression case count: **13**. These tests use membership/identity fixtures only and contain no price, model, label, or performance data.

## Implementation plan — not executed

1. Freeze a source manifest: exact commits/releases, license/attribution findings, file hashes, coverage, ancestry, and accepted source roles.
2. Define canonical schemas for raw evidence, the three event types, correction overlays, `InstrumentEpisodeV1`, validation findings, and DatasetSnapshot.
3. Build format adapters only for accepted pinned upstream artifacts; adapters may parse structure but may not infer missing finance events.
4. Implement the generic future-ticker detector and overlay compiler; no symbol-specific Python conditions.
5. Run the 13 frozen regressions and all reconciliation gates against a tiny bounded fixture before touching full data.
6. Recover and review evidence for every unresolved membership/ticker conflict; unresolved rows remain fail-closed.
7. Compile the bounded 2010-01-01 through 2024-12-31 episode table twice and require identical hashes.
8. Publish an immutable DatasetSnapshot only after every authority gate is zero-unexplained.
9. Separately authorize episode-bounded market-data acquisition and define `MIN_HISTORY_REQUIRED`.
10. Separately authorize the Qlib handoff; Qlib receives the accepted snapshot and never reconstructs membership.

Expected implementation complexity is **MODERATE**: the finance-domain custom logic is limited to typed source precedence, session-boundary normalization, generic episode compilation, correction overlays, and strict validation. It excludes HTML-history reconstruction, corporate lineage, price stitching, models, and backtests.

## Authority state

```text
FINAL_P1_IDENTITY_MODEL = InstrumentEpisodeV1
FULL_SECURITY_MASTER_REQUIRED = NO
TICKER_EPISODE_MODEL = REQUIRED
TICKER_REUSE_SAFE_BY_DESIGN = YES
MEMBERSHIP_EVENT_SEPARATED_FROM_RENAME_EVENT = YES
MANUAL_CORRECTIONS_DATA_DRIVEN = YES
RAW_EVIDENCE_IMMUTABLE = YES
AQ_FINANCE_DOMAIN_CUSTOM_LOGIC = MINIMAL_BOUNDED
EXPECTED_IMPLEMENTATION_COMPLEXITY = MODERATE
P0 = COMPLETE
P1 = NOT_STARTED
CURRENT_NEXT = P1_PIT_DATA_RECOVERY
CODE_CHANGED = NO
PR_CREATED = NO
MERGED = NO
```
