# P5 SEC bulk acceptance and upstream period parity POC 001

Status: **GAP CLOSEOUT FAIL_CLOSED; production migration not authorized**. Original POC base main `010a97135b181db43fce6597a9859a4755e225a0`; bounded gap-closeout base main `f17cfeb5bd960e1385150fa5bf3c261743a2d53c`. Neither task inspected PID 403 or its build root, trained, predicted, backtested, read P2 sealed OOS, or modified P5 production code. `AGENTS.md` is not present in this checkout.

## Frozen sources and runtime

| Source | Bytes | SHA-256 |
| --- | ---: | --- |
| [SEC companyfacts.zip](https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip) | 1,409,212,553 | `ee099c7394a357f1996c728b7362f25158613b34f2ab1ad270cffc1befb917b6` |
| [SEC submissions.zip](https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip) | 1,564,656,199 | `702fbcd8b4335bc649e9e4eab3a202f3effc314b43421664bfecb59365767165` |
| SEC FSDS 2009q4 (preserved earlier POC) | 4,050,938 | `ad23b114ecb430c3a05ee2f2be799e966a67591ef098c44311b2f1f632d3ea82` |
| SEC FSDS 2010q1 (preserved earlier POC) | 5,311,282 | `2a4db2340ab1662d5135d7e17be1a58352c5959017350f0ef2174135f9996125` |
| SEC FSDS 2021q1 (preserved earlier POC) | 97,900,752 | `6a776a9fa3d974476101efa9a4bfc531b7cdc2763abd45a6f70dd240a223843b` |

The SEC bulk pair was downloaded once each into a separate private POC root; no per-accession mass acquisition was attempted. The SEC describes these ZIPs as nightly snapshots of the official [CompanyFacts and Submissions APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), not historical nightly vintages. The 9 public parity accessions were frozen before comparing libraries (`fixture-manifest.json` SHA-256 `32204d3a71abce8af35135744aa76bcf722b9c2c64a5eef2abdbd71f3678e476`). The separate Python 3.11.16 runtime pinned EdgarTools 5.58.0 and secfsdstools 2.4.3; the latter used `AutoUpdate=False` for the controlled comparison. No project lockfile changed.

An initial secfsdstools import unexpectedly invoked its package-level automatic updater **before** a per-call configuration could apply. It began downloading quarterly ZIPs via the existing user default config. The isolated POC process was stopped immediately. Nine exact task-generated ZIP paths (783,490,105 bytes, including one zero-byte partial) were inventoried and removed; no other cache path was deleted. This is a POC execution-discipline incident, not a valid controlled data source. The controlled parity run then set `SECFSDSTOOLS_CFG` before import and used the preserved three-quarter upstream index without further FSDS downloads. SEC network contention from the brief unexpected download cannot be ruled out; direct process/worktree/checkpoint interference with PID 403 did not occur. The incident is sealed privately, not hidden.

## Gate A — accession and exact acceptance

The existing final identity ledger provided 721 bound episodes, 711 unique CIKs and 111 explicit exclusions; no current-ticker CIK lookup was used. Seven of the 711 CIKs lack a CompanyFacts member. Across the other CIKs, the frozen ZIP contains 16,623,494 candidate fact observations and 53,218 unique `(CIK, accession)` pairs. All 1,096 older-history files referenced by those CIKs were present in the official Submissions ZIP and inspected alongside recent arrays.

| Classification | Unique accessions |
| --- | ---: |
| Exact SEC Submissions acceptance with matching form | 53,169 |
| CompanyFacts accession missing from same-CIK Submissions | 2 |
| CompanyFacts form conflicts with Submissions form | 47 |
| Total | 53,218 |

The 47 form conflicts are 20 `10-K→10-K/A`, 18 `10-Q→10-Q/A`, five `2.01 SD→SD`, two `8-K→8-K/A`, one `10-K→10-KT`, and one `10-Q→10-QT`. One accession appears identically at a recent/older split boundary; it was counted as one unique metadata record while the duplicate physical row is retained in audit accounting. No CIK header conflicts were observed in either ZIP for the bound CIKs. A valid acceptance field was required to have an explicit UTC `Z` timestamp; `filed`, report date and period end were never substituted.

Three bounded official accession-specific metadata probes for the two missing joins recovered **zero** timestamps (HTTP 404, 503, 404). Thus 49 accession admissions remain unresolved, exact fallback count is zero, and `SEC_BULK_ACCEPTANCE_CLASSIFICATION = PARTIAL_FAIL_CLOSED`. The form conflicts have timestamps in Submissions but cannot be admitted as matching-form evidence until reconciled. Year/form breakdown and the exact missing ledger are retained privately. In the bound population, CompanyFacts has no fact with `filed` before 2009; pre-XBRL filings are not implied to have structured fact coverage. `20-F`, `20-F/A` and `6-K` occur in the form breakdown. Historical issuer domicile is not inferred from current filer metadata; foreign-form observations are distinguished from a proven full issuer-country time series.

## Gate B — native statement and period behavior

The private matrix records all 11 frozen P5 concepts for each of 9 preselected real accessions. EdgarTools 5.58.0 parsed the frozen SEC CompanyFacts members through its installed EntityFacts parser/query and retained exact accession, raw value, taxonomy/tag, unit, start/end, form, filed date and period. secfsdstools 2.4.3 read the pre-existing upstream FSDS SUB/NUM/PRE index through `SingleReportCollector.get_report_by_adsh`, with `MainCoregRawFilter`, `OfficialTagsOnlyRawFilter`, `ReportPeriodRawFilter` and, only on applicable domestic fixtures, `USDOnlyRawFilter`; its native BS/IS/CF standardizers were executed. The FSDS source remains upstream-owned. [SEC FSDS documentation](https://www.sec.gov/dera/data/fsds.pdf) specifies its `adsh`, `ddate`, `qtrs`, `uom` and coreg grain and includes transition/foreign forms.

| Case | Frozen public accession(s) | Observed native result |
| --- | --- | --- |
| Annual flow + instant | Apple `0001193125-09-214859` | Annual revenue 36.537B, net income 5.704B; assets 53.851B (`qtrs=4/0`) agree between accession raw and FSDS standardizer. |
| Direct quarter | Apple `0001193125-10-012085` | Accession raw duration and FSDS `qtrs=1` exist. EdgarTools accession-isolated high-level quarterly statement is empty: convenience view is not raw-fact parity. |
| Six-month YTD | Microsoft `0001193125-10-015598` | `qtrs=1` and `qtrs=2` coexist; six-month revenue 31.942B remains a separate horizon. |
| Nine-month YTD | Walmart `0001193125-09-248603` | `qtrs=1` and `qtrs=3` coexist; nine-month revenue 294.563B remains separate. |
| Original and amendment | Apple original above + `0001193125-10-012091` | Distinct accessions and values: annual revenue 36.537B→42.905B, net income 5.704B→8.235B. No backwards vintage collapse. |
| Transition | Myriad `0000899923-21-000021` (`10-KT`) | FSDS retains a two-quarter transition flow; do not relabel it annual merely because the form begins `10-K`. |
| Foreign IFRS | ASML `0000937966-21-000007` (`20-F`) | Both raw and FSDS statement paths yielded values; no forced USD-only filter. |
| Structured foreign 6-K | CNR `0000016868-21-000012` | Both paths yielded structured data; not evidence that all 6-K filings are structured. |
| Missing concept | Apple original/amendment | No short-/long-term debt in tested raw synonyms; missing is retained, not zero-filled. |

secfsdstools standardized output has corresponding columns for **9/11** frozen concepts; `ShortTermDebt` and `LongTermDebt` are absent even where its raw NUM rows contain debt tags. EdgarTools EntityFacts raw retains accession-specific debt where present, but its high-level quarterly statement was empty for some older 10-Q fixtures. Neither convenience layer alone proves full 11-concept PIT equivalence. Native standardizers may derive or map values; their output cannot replace raw decimal/source identity, exact SEC acceptance or amendment-vintage admission. The 2009 Apple amendment proves why separate accessions are mandatory. AQ's current period policy was a comparison guard only; no period engine was added.

## Conditional owner and retirement decision

| Capability | Primary upstream candidate, subject to fail-closed gaps |
| --- | --- |
| Raw standard whole-entity facts | SEC CompanyFacts bulk |
| Exact filing metadata | SEC Submissions bulk, with exact accession fallback only |
| Comparable statement columns | secfsdstools 2.4.3, only for supported columns |
| Native duration/instant evidence | SEC FSDS `qtrs` through secfsdstools |
| Original/amendment raw vintage | EdgarTools 5.58.0 EntityFacts accession view |
| Tested structured foreign statements | secfsdstools 2.4.3, without inappropriate USD filtering |

These are owner candidates, **not production admission**. The 49 unresolved accession/form cases and two absent standardized debt columns prevent atomically replacing the current path. Future retirement action is `DELETE_AFTER_MIGRATION` for `run_full_universe_preflight.py`, `REWRITE_THIN` for `aq_edgartools_full_build`, `REWRITE_THIN` while preserving AQ PIT policy for `aq_hybrid_fundamentals`, and `KEEP` the thin `materialize.py` evidence projection. No deletion or production LOC change occurred; retirement/retention LOC cannot yet be certified. Do not invent an acceptance resolver, period engine, SEC client or AQ statement engine.

Next: `P5_SEC_BULK_ACCEPTANCE_AND_PERIOD_GAP_CLOSEOUT_001` — close the exact 2 missing joins, 47 form conflicts, debt-column and older quarterly statement gaps using upstream evidence before any migration. No PID 403 status check or build-root read was made; its eventual output remains an independent later oracle.

## Gap Closeout

This bounded follow-up reused the SHA-frozen SEC CompanyFacts and Submissions ZIPs; neither bulk file was redownloaded. It used the exact 49-row ledger, not another 53,218-accession scan, and froze seven real debt fixtures (six positive issuers across 2009–2021 plus a missing-debt control) before reading native parity results. New evidence and its checksum manifest are under the existing private `D:/AQ_DATA/P5/upstream-parity-poc-001` root. Original PR #77 evidence was not overwritten. No secfsdstools import or auto-update occurred.

The 49 anomalies split into 42 P5-relevant exact-11-concept historical financial accessions and seven outside the authorized form/history scope. Fifty-two bounded accession-specific SEC requests (49 exact index headers, three necessary SGML-header fallbacks) returned 23,902,175 response bytes, as recorded in `owner-closeout.json`. Of 47 form conflicts, 44 received exact official filing form, accession, CIK and acceptance metadata; three remain unresolved because the official header does not independently establish the same target CIK. The two same-CIK Submissions omissions remain unresolved: both exact index and full-submission URLs returned 404. Thus five **P5-relevant** acceptance cases remain unadmitted. CompanyFacts' conflicting raw `form` field was not rewritten. The full 49-row decision ledger, official response hashes, request count and byte count are private.

EdgarTools 5.58.0 native EntityFacts and synonym groups cover both debt groups on real accession-bound instant facts; no synthetic values, duration substitution or segmented summation was used. However its `MappingStore` labels `LongTermDebtCurrent` as `Current Portion of Long-Term Debt`, while the same native synonym group assigns that tag to `short_term_debt`; four fixture facts expose mapper-versus-group label divergence. No AQ debt-specific reconciliation rule is authorized, so exact ShortTermDebt standardized parity and the combined 11-concept semantic gate remain **fail-closed**. LongTermDebt mapped on the tested positive facts. The frozen nine-fixture raw EntityFacts replay plus upstream `edgar.xbrl.core.classify_duration` exposed native instant, quarterly, semi-annual, nine-month and annual classes, retaining amendment, transition and tested foreign facts as distinct observations. The older empty 10-Q high-level convenience statement is not itself needed by the accession-bound raw-fact path; it is a non-blocking convenience API limit, not a reason to patch upstream.

Owner selection is therefore **not finalized for production**. SEC CompanyFacts remains the raw-fact candidate, exact SEC filing metadata remains incomplete for five relevant accessions, EdgarTools native standardization requires the identified debt-label semantic resolution, and secfsdstools remains an independent parity oracle rather than an automatically adopted production dependency. `P5_UPSTREAM_MIGRATION_GATE = FAIL_CLOSED`; production retirement LOC/actions are not authorized for recalculation or execution. The next state is `BLOCKED_UPSTREAM_GAPS_REMAIN`. No production Python LOC, Project Brain document, dataset, model, prediction, backtest, or generic AQ engine was added. The old PID 403 build root and its 392 failures were not read or retried.

The subsequent owner-authorized P5 V1 scope contraction is a **new pre-evaluation authority**, not a reinterpretation of this POC's result. It excludes the five exact-authority gaps as missing observations and retires `ShortTermDebt`; this historical eleven-feature fail-closed finding remains intact. The ordered ten-feature authority and source hashes are frozen in `10-data-system/fundamentals/historical-dataset/p5-minimal-upstream-v1.json`. The migration branch must still build and validate the complete frozen bulk input before claiming a passing production gate.
