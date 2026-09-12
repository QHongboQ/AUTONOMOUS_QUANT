# P2 Free Data Gap-Fill Authority Audit 001

**Task:** `AUTONOMOUS-QUANT-P2-FREE-DATA-GAP-FILL-AUTHORITY-AUDIT-001`
**Base:** `97be7667c62f60abf1eac452406e329dcaf6c987`
**Result:** `PASS_WITH_UNRESOLVED_AUTHORITY`

## Scope and ownership

This bounded audit tested whether the already deployed OpenBB/yfinance path
could provide certification-usable evidence for the three explicit gaps left
by the corrected Quantiacs pilot. OpenBB remains the provider gateway and
yfinance remains the Yahoo acquisition implementation (`UPSTREAM_WHOLE`). No
AQ downloader, provider client, registry, retry layer, cache, storage engine,
normalizer, ticker resolver, corporate-action parser, calendar, schema, or
generic provenance framework was created.

The existing isolated runtime was reused without package changes:

| Component | Observed version |
|---|---:|
| Python | `3.12.14` |
| OpenBB | `4.7.2` |
| `openbb-yfinance` | `1.6.3` |
| yfinance | `1.7.0` |
| pyarrow | `25.0.1` |

OpenBB ran with the established isolated home at
`D:\AQ_CACHE\openbb-home`. The calls explicitly selected
`provider="yfinance"`; historical calls used `interval="1d"`,
`adjustment="splits_only"`, and `include_actions=true`, followed by
`to_df(index=None)`. There were exactly four provider calls and no manual or
automatic retry: one Q profile request and one bounded historical request each
for FB, META, and DISCK.

## Bounded observations

OpenBB/yfinance treats `end_date` as an exclusive bound in these requests.
Accordingly, the submitted end dates below are one day after the final date
requested by policy.

| Request | Submitted range | Result | Returned identity/sessions | OHLCV/actions |
|---|---|---|---|---|
| `FB` historical | 2022-03-15 to 2022-06-09 | `EmptyDataError`; 0 rows | no returned symbol; no sessions | unavailable |
| `META` historical | 2022-06-09 to 2022-06-18 | 7 rows | requested META; 2022-06-09 through 2022-06-17 | OHLCV present; no action fields returned in this window |
| `DISCK` historical | 2022-04-07 to 2022-04-12 | yfinance reported possibly delisted/no timezone; OpenBB raised `EmptyDataError`; 0 rows | no returned symbol; no sessions, including no 2022-04-08 | unavailable |
| `Q` profile | current identity inspection | 1 profile | `Q`, Qnity Electronics, Inc., exchange `NYQ`; incorporated 2024 and formerly Novus SpinCo 1, Inc. | price call forbidden by identity gate |

The successful META frame's deterministic canonical-record SHA-256 was
`336a132fa14afa909e83957ee80bac5c8ebb785321cb3c64bb08daad43e67c4c`.
No market-data rows or provider response bytes were retained, placed in Git,
or promoted to DVC. The two empty historical results had no response payload
to hash. No durable Yahoo cache or general data store was created by AQ.

The META result corroborates only the successor episode. It was not mapped to
FB. Therefore:

```text
FB_YAHOO_EXACT_EPISODE_PRICE = ABSENT
META_YAHOO_EXACT_EPISODE_PRICE = PRESENT
FB_META_CROSS_EPISODE_MAPPING = 0
DISCK_2022_04_08_YAHOO = ABSENT
QWEST_Q_YAHOO_IDENTITY = WRONG_SECURITY
QWEST_Q_PRICE_COVERAGE = NOT_TESTABLE_DUE_IDENTITY
SYNTHETIC_PRICE_ROWS = 0
```

## Identity and event authority

The provider observations were adjudicated against issuer and SEC evidence,
not against name similarity or price continuity:

- Meta's SEC-filed issuer announcement says FB was replaced by META before
  market open on 2022-06-09, with the listing and CUSIP otherwise continuing.
  The seven META rows therefore cannot fill the separate pre-boundary FB
  episode. [Meta issuer exhibit filed with the SEC](https://www.sec.gov/Archives/edgar/data/1326801/000132680122000070/may312022-exhibit991.htm)
- Warner Bros. Discovery's SEC filing says the Discovery classes were
  suspended before the opening on 2022-04-11 and WBD started trading that day;
  issuer evidence identifies DISCK as one of the pre-transaction classes. It
  establishes the boundary but does not manufacture the missing 2022-04-08
  OHLCV row. [WBD Form 8-K](https://www.sec.gov/Archives/edgar/data/1437107/000119312522103051/d328161d8k.htm)
- Qwest's SEC filing says its NYSE `Q` common stock ceased to be listed after
  the merger completed on 2011-04-01. The current provider profile instead
  identifies Q as Qnity Electronics, an unrelated issuer incorporated in
  2024. The hard identity gate therefore stopped before any current-Q price
  request. [Qwest Form 8-K](https://www.sec.gov/Archives/edgar/data/1037949/000110465911018718/a11-9685_18k.htm)

SEC/issuer evidence is used only for identity and event boundaries, never as a
price source.

## Provider-authority audit

| Authority dimension | Finding |
|---|---|
| Price coverage | META post-boundary only; FB and DISCK absent; historical Qwest not tested because Q is now a different security |
| Identity precision | Correct for current Q profile, but reuse of the bare ticker makes it unsafe for historical Qwest; single-symbol historical frames did not expose a returned-symbol field |
| Corporate-action visibility | The interface was called with actions enabled, but no action fields were returned in the only successful bounded frame; no action evidence exists for either missing row |
| Adjustment semantics | Installed OpenBB provider source explicitly maps `splits_only` to the non-dividend-adjusted yfinance path and passes the action flag |
| Revision addressability | `FAIL`: request/result metadata exposes no vendor revision, vintage, as-of snapshot, or immutable data release identifier |
| Provider versioning | OpenBB, provider-extension, and yfinance code versions are pin-able; the live Yahoo dataset itself is not version-addressable |
| Data-retention rights | `UNRESOLVED`: yfinance describes the tool as research/education use and the Yahoo API as personal-use only, directing users to Yahoo terms; no explicit durable certification-retention grant was established |
| Reproducibility | Request parameters and the successful returned frame can be hashed, but a later live response cannot be proven to represent the same vendor revision |
| Free access | Available without a provider credential for this bounded research audit; that does not establish certification retention or redistribution authority |

OpenBB documents the historical endpoint, provider selection, OHLCV schema,
and adjustment choices. [OpenBB historical-price reference](https://docs.openbb.co/odp/python/reference/equity/price/historical)
yfinance expressly describes its Yahoo access as intended for research and
education and says users must consult Yahoo's terms for rights in downloaded
data. [yfinance documentation](https://ranaroussi.github.io/yfinance/)
Yahoo's current general terms do not provide the explicit durable-use grant
needed here; this audit makes no broader legal conclusion.
[Yahoo terms](https://legal.yahoo.com/ca/en/yahoo/terms/otos/)

## Decision matrix

| AQ episode | Primary Quantiacs status | Yahoo identity status | Yahoo price status | Yahoo action status | Revision status | Retention status | Certification gap-fill decision | Reason |
|---|---|---|---|---|---|---|---|---|
| FB, through 2022-06-08 | provider coverage gap | exact requested episode not evidenced; no redirect observed | absent | unavailable | fail | unresolved | `REJECT` | no FB rows were returned; META rows remain a separate episode |
| DISCK, required 2022-04-08 | terminal gap | exact request produced no identity-bearing result | absent | unavailable | fail | unresolved | `REJECT` | no 2022-04-08 DISCK row was returned and no terminal value may be manufactured |
| Qwest Communications International Inc., CIK 0001037949, historical NYSE Q | historical-scope/provider gap | wrong security | not testable due identity | unavailable | fail | unresolved | `REJECT` | current Q is Qnity; price presence would be irrelevant and unsafe |

No Yahoo candidate survives the technical identity/coverage gates, before the
separate revision and retention gates are considered. Therefore:

```text
FREE_ROUTE_DECISION = D — FREE_ROUTE_CURRENTLY_BLOCKED
NEXT_FREE_CANDIDATE_REQUIRED = YES
RECOMMENDED_NEXT_MATURE_PROVIDER_GATEWAY_PATH = OpenBB -> alpha_vantage
ALPHA_VANTAGE_STATUS = DEFERRED_PENDING_EXISTING_AUTHORIZED_KEY_AND_SEPARATE_AUTHORITY_AUDIT
CURRENT_NEXT = P2_CERTIFICATION_DATA_ROUTE_DECISION
```

OpenBB documents Alpha Vantage as a mature historical-price provider extension
requiring `alpha_vantage_api_key`; no key/account was present or authorized for
this task, so it was neither installed nor called.
[OpenBB provider list](https://docs.openbb.co/odp/python/extensions/providers)
The current free route is blocked; this is not evidence that every paid or
future authorized provider route is rejected.

## Safety and final state

```text
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
PACKAGES_CHANGED = NO
PROVIDER_CALLS = 4
MARKET_DATA_RETAINED = NO
MARKET_DATA_IN_GIT = NO
DVC_PROMOTION = NO
MODEL_TRAINING = NO
BACKTEST = NO
RDAGENT_EXECUTED = NO
MLFLOW_EXPERIMENT = NO
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
P2_CERTIFICATION = STARTED / IN_PROGRESS
P2_CERTIFIED_DATA_FOUNDATION = IN_PROGRESS
P2_FREE_DATA_GAP_FILL_AUTHORITY_AUDIT = COMPLETE
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
CURRENT_NEXT = P2_CERTIFICATION_DATA_ROUTE_DECISION
```
