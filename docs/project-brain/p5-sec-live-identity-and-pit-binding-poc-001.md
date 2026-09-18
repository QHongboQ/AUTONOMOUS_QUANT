# P5 SEC Live Identity and PIT Binding POC 001

## Outcome

```text
TASK = AUTONOMOUS-QUANT-P5-SEC-LIVE-IDENTITY-AND-PIT-BINDING-POC-001
EDGAR_IDENTITY_CONFIGURED = YES_LOCAL_PRIVATE
EDGARTOOLS_LIVE_SEC = PASS
EDGARTOOLS_SKILL_LIVE_ROUTING = PASS
OPENBB_SEC_LIVE = BLOCKED_UPSTREAM_SAFE_IDENTITY_AND_HISTORICAL_SCOPE
THREE_WAY_PIT_BINDING = BLOCKED
FINAL_CLASSIFICATION = BOUNDED_PARTIAL_OPENBB_SAFE_LIVE_BOUNDARY_BLOCKED
CURRENT_DEVELOPMENT_NEXT = P5_OPENBB_SEC_SAFE_IDENTITY_AND_HISTORICAL_SCOPE_RESOLUTION_001
```

The operational P2 authority remains unchanged:

```text
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
P2_V2_SEALED_OOS_ACCESSED = NO
```

This task created a private host-local SEC identity file outside the repository
with restrictive directory/file modes `700/600`. The identity value is not
stored in Git, Project Brain, DVC, private JSON evidence, logs, or this report.

## Bounded historical network scope

EdgarTools was configured process-locally at no more than two requests per
second, sequentially and without concurrency. The POC used only historical SEC
quarterly indexes, one historical submissions page, and five exact full
submissions whose acceptance times precede the cutoff.

```text
HISTORICAL_POC_CUTOFF = 2021-12-31T23:59:59Z
CONSERVATIVE_LOGICAL_SEC_REQUEST_ACTIONS = 13
CURRENT_OR_POST_CUTOFF_FILING_SELECTED = NO
SEC_MIRROR_CREATED = NO
```

The conservative count includes four actions from a bounded first execution
that stopped before producing a sample result because the upstream downloader
returned decoded text rather than bytes. The rerun accepted the upstream text
shape; no sample-selection or authority rule changed.

## SEC and EdgarTools authority

The selected samples are deterministic by fixed CIK/form/calendar quarter,
then latest filing date and accession:

| Sample | Accession | Report period | First available at (UTC) |
|---|---|---|---|
| 10-K | `0000320193-21-000105` | `2021-09-25` | `2021-10-28T22:04:28Z` |
| 10-Q | `0000320193-21-000065` | `2021-06-26` | `2021-07-27T22:03:42Z` |
| 8-K | `0001193125-21-328151` | `2021-11-09` | `2021-11-12T21:31:14Z` |
| 10-K/A | `0001193125-10-012091` | `2009-09-26` | `2010-01-25T21:25:58Z` |

Each time comes from the raw SEC full-submission acceptance header, interpreted
in the SEC's Eastern time basis and converted to UTC. Filing date and report
period are never used as availability authority.

EdgarTools `5.58.0` proved the live historical index and filing route, full
submission SGML, attachments, HTML/text, 10-K/10-Q/8-K report objects, sections,
XBRL, financial statements, and `to_context` without an AQ parser or client.

The selected 2021 10-K preserved this accession-bound XBRL fact:

```text
CONCEPT = us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax
LABEL = Net sales
VALUE = 365817000000
UNIT = USD
PERIOD = 2020-09-27..2021-09-25
ACCESSION = 0000320193-21-000105
FIRST_AVAILABLE_AT = 2021-10-28T22:04:28Z
```

The upstream EdgarTools Skill and its relative reports, financials, and XBRL
guidance were consulted without modification. The bounded Skill answer retained
the exact form, report period, accession, net-sales fact, Item 1A section fact,
and source-submission hash. No investment recommendation was produced.

## Amendment vintage proof

The fixed issuer order found Apple first. For the `2009-09-26` report period:

| Vintage | Accession | First available at | `us-gaap:SalesRevenueNet` |
|---|---|---|---:|
| Original 10-K | `0001193125-09-214859` | `2009-10-27T20:18:29Z` | `36537000000` |
| 10-K/A | `0001193125-10-012091` | `2010-01-25T21:25:58Z` | `42905000000` |

The amendment is a separate later vintage and is never projected backward.

```text
RESTATEMENT_HANDLING = FAIL_CLOSED_AND_EXPLICIT
AMENDMENT_PROJECTED_BACKWARD = NO
```

## OpenBB fail-closed boundary

No OpenBB live request was issued. Source inspection of the exact installed
`openbb-sec 1.6.7` distribution found two independent blockers:

1. SEC request headers contain a hard-coded example User-Agent. The installed
   package has no `EDGAR_IDENTITY` reference or documented public path for
   supplying the authorized local identity. Monkeypatching that constant would
   not prove an upstream-supported boundary.
2. The income statement, balance sheet, cash-flow, and growth routes retrieve
   the current complete SEC Company Facts payload before statement resolution.
   That transport cannot be bounded to pre-2022 filings, so invoking it would
   violate this POC's historical-only contract even if returned rows were later
   filtered.

```text
OPENBB_SEC_LIVE = BLOCKED
OPENBB_PIT_MODE = PARTIAL
OPENBB_PIT_MODE_BEHAVIOR_OBSERVED = NO
OPENBB_PACKAGE_MODIFIED = NO
OPENBB_MONKEYPATCH_USED = NO
```

This is an upstream runtime/configuration boundary, not a factor result and not
permission to create an AQ HTTP client. The exact next task must resolve whether
an official upstream configuration/version can satisfy both the identity and
historical transport boundaries.

## Three-way binding decision

SEC source authority to EdgarTools filing/accession is proven. The OpenBB leg
was not executed because doing so would violate the two safety gates above.

```text
SEC_TO_EDGARTOOLS = PASS
EDGARTOOLS_TO_OPENBB = NOT_EXECUTED_FAIL_CLOSED
THREE_WAY_PIT_BINDING = BLOCKED
AQ_THIN_BINDER_REQUIRED = YES_AFTER_UPSTREAM_SAFE_LIVE_BOUNDARY
```

Any future binder remains limited to the SEC accession/acceptance evidence to
OpenBB structured-value identity join. It may not own HTTP, SEC download, XBRL,
filing parsing, statements, generic storage/ETL, or restatement logic.

## No implementation or research creep

```text
AQ_SEC_FETCHER = NO
AQ_SEC_HTTP_CLIENT = NO
AQ_XBRL_PARSER = NO
AQ_FILING_PARSER = NO
AQ_RAG_ENGINE = NO
AQ_VECTOR_DB = NO
AQ_FUNDAMENTAL_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_BACKTEST = NO
```

Private evidence is stored under
`D:/AQ_DATA/P5/sec-live-identity-and-pit-binding-poc-001/`.

```text
PRIVATE_REPORT = D:/AQ_DATA/P5/sec-live-identity-and-pit-binding-poc-001/poc_summary.json
PRIVATE_REPORT_SHA256 = c15db43defa31dc1194eed0fe4afae4d26c9d4803e8f138069ceef28bbad7fae
```
