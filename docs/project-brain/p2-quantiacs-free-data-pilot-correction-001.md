# P2 Quantiacs Free-Data Pilot Correction 001

Task: `AUTONOMOUS-QUANT-P2-QUANTIACS-FREE-DATA-PILOT-CORRECTION-001`

Status: `COMPLETE`

## Authority and scope

```text
CAPABILITY = P2_QUANTIACS_PILOT_CORRECTION_AND_COVERAGE_ADJUDICATION
UPSTREAM_OWNER = QUANTIACS_DATA_SERVICE + AQ_INSTRUMENTEPISODEV1 + PANDERA + EXCHANGE_CALENDARS + QLIB
OWNERSHIP_MODE = QUANTIACS_UPSTREAM_WHOLE; AQ_PIT_AQ_OWNED_THIN_DOMAIN; PANDERA_EXCHANGE_CALENDARS_UPSTREAM_LEAF; QLIB_UPSTREAM_WHOLE
UPSTREAM_ALREADY_DEPLOYED = YES_PARTIAL
AQ_IMPLEMENTATION_ALLOWED = YES
AQ_ALLOWED_SCOPE = PILOT_CORRECTION_IDENTITY_RECONCILIATION_BOUNDED_PROVIDER_QUERIES_COVERAGE_ADJUDICATION_VALIDATION_THIN_EVIDENCE_COMPOSITION
CUSTOM_ENGINE_REQUIRED = NO
```

This correction is based on pilot commit
`2834a484ad0c4fb3bab5a3cccd7d201a612ae8d1`, not directly on `main`.
It changes no production code and creates no generic provider-composition
engine.

```text
ORIGINAL_PILOT_SHA = 2834a484ad0c4fb3bab5a3cccd7d201a612ae8d1
ORIGINAL_PILOT_RESULT = FAIL_FREE_ROUTE_COVERAGE
ORIGINAL_PILOT_EVIDENCE = PRESERVED
ORIGINAL_PILOT_DOCUMENT_SHA256 = dd8c5cbd827d5b0cf1b47d13ba96d3788d5a969cfe181a5aeda61527464ccb91
ORIGINAL_ADJUDICATION = SUPERSEDED_BY_CORRECTION_001
```

The original provider observations remain historical facts. The superseded
part is the cross-episode FB/META mapping and the resulting route-wide
adjudication.

## Identity correction

The pilot defect is confirmed. It assigned 60 pre-2022-06-09 rows returned by
provider asset `tts-222568848` (`NAS:META`) to the distinct AQ FB episode.
Economic-company continuity does not authorize a provider price row to cross
an `InstrumentEpisodeV1` ticker boundary. The correction applies only:

```text
FB_AQ_EPISODE -> tts-43902240 / NAS:FB
META_AQ_EPISODE -> tts-222568848 / NAS:META
ORIGINAL_META_BACKMAP_ROW_COUNT = 60
CORRECTED_META_BACKMAP_ROW_COUNT = 0
```

Meta's SEC-filed issuer announcement establishes that FB was replaced by META
before market open on 2022-06-09 while the listing and CUSIP remained
unchanged. That identity evidence fixes the ticker boundary; it does not allow
META provider rows to masquerade as FB rows:

- https://www.sec.gov/Archives/edgar/data/1326801/000132680122000070/may312022-exhibit991.htm

## Bounded provider-view evidence

Both views were queried with exact provider IDs for identical bounded dates.
The Quantiacs generic `is_liquid` field was not interpreted as S&P 500
membership. AQ PIT remains membership authority.

| Identity | Dates | SPX rows | Generic rows | Result |
|---|---:|---:|---:|---|
| `tts-43902240` / `NAS:FB` | 2022-03-15–2022-08-05 | 0 | 0 | confirmed Quantiacs price gap |
| `tts-222568848` / `NAS:META` | 2022-03-15–2022-08-05 | 100 | 100 | rows exist, but only 40 at/after the META boundary are episode-eligible |
| `tts-15427298` / `NAS:DISCK` | 2022-04-07–2022-04-11 | 1 | 1 | only 2022-04-07; 2022-04-08 absent |

The generic-view metadata query independently returned the exact identities
`tts-43902240`/FB, `tts-222568848`/META, and `tts-15427298`/DISCK. Generic META
and DISCK raw response payloads parse as xarray data with respectively 100 and
1 populated sessions. The public toolbox `load_origin_data` wrapper raises a
`KeyError` afterward because it expects a generic `split` field that these
responses omit; this wrapper behavior does not erase the directly parsed
provider rows. SPX and generic payload hashes are identical for META and for
DISCK, so no generic-only row exists to compose.

```text
FB_SPX_RESPONSE_SHA256 = 8729ae84f025fd50d6b092930d98176f042ff6bb28c4288fe750f3a68b606673
FB_GENERIC_RESPONSE_SHA256 = e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
META_SPX_RESPONSE_SHA256 = 470eba6cf9bc4f9987c4ed9f0ce7497b7ab5e93ca08453d5e6430e0561d845e9
META_GENERIC_RESPONSE_SHA256 = 470eba6cf9bc4f9987c4ed9f0ce7497b7ab5e93ca08453d5e6430e0561d845e9
DISCK_SPX_RESPONSE_SHA256 = 8ce611092985d5bf94a22acb936212317998ed2cc1c391de044698f371de4724
DISCK_GENERIC_RESPONSE_SHA256 = 8ce611092985d5bf94a22acb936212317998ed2cc1c391de044698f371de4724
FB_QUANTIACS_PRICE_GAP = CONFIRMED
FB_SPX_VIEW_GAP = YES
```

Each correction evidence row records `provider_view`. No row from one view
silently overwrites another.

## Qwest scope adjudication

The accepted Qwest episode is Qwest Communications International Inc., CIK
`0001037949`, whose common stock traded as NYSE `Q`. Qwest's SEC-filed 2011
Form 8-K states that the merger closed on 2011-04-01 and that this `Q` common
stock ceased to be NYSE-listed. It is not the current Quantiacs `NYS:Q`
security:

- https://www.sec.gov/Archives/edgar/data/1037949/000110465911018718/a11-9685_18k.htm

The original result therefore stands: Quantiacs provided 0/126 mapped Qwest
price sessions and no later `Q` identity was substituted. Project Brain does
not yet preregister a final P2 Certification dataset start date. Existing P2
authority says the sealed dates are selected only after data and policy hashes
exist; the 2015 P1 research-provider boundary is descriptive, not a final P2
Certification boundary.

```text
QWEST_PROVIDER_GAP = YES
P2_CERTIFICATION_WINDOW_STATUS = NOT_YET_PREREGISTERED
QWEST_SCOPE_STATUS = HISTORICAL_REGRESSION_COVERAGE_GAP_SCOPE_NOT_YET_DECIDED
QUANTIACS_EARLY_HISTORY_INCOMPLETE = YES
```

Qwest alone therefore cannot establish that every feasible free route is
blocked. No Certification date was invented or performance-selected.

## DISCK direct recheck

Both exact-ID views returned 2022-04-07 and omitted the required 2022-04-08
session. The SEC-filed WBD 8-K establishes that DISCK ceased trading after the
close on 2022-04-08 and WBD started on 2022-04-11. A separate SEC-filed Form 4
records the one-for-one conversion of DISCK on 2022-04-08. These sources prove
identity and the corporate-action/trading boundary, not missing OHLCV:

- https://www.sec.gov/Archives/edgar/data/1437107/000119312522103051/d328161d8k.htm
- https://www.sec.gov/Archives/edgar/data/937797/000143710722000093/xslF345X03/wf-form4_164979993298213.xml

```text
DISCK_2022_04_08_SPX = ABSENT
DISCK_2022_04_08_GENERIC = ABSENT
DISCK_GAP = QUANTIACS_PROVIDER_PRICE_GAP_CONFIRMED
```

No price was manufactured from event evidence and no additional provider was
queried.

## Corrected metrics and unresolved classification

The corrected mapped dataset is an exact row subset of the immutable pilot
dataset: only the 60 invalid META-to-FB rows were removed. It has 647 rows.

```text
CORRECTED_REQUIRED_EPISODES = 12
CORRECTED_MAPPED_EPISODES = 10
CORRECTED_PRICE_COVERED_EPISODES = 9
CORRECTED_ACTION_COVERED_EPISODES = 9
CORRECTED_UNRESOLVED_EPISODES = 3
```

| Unresolved episode | Exclusive classification | Meaning |
|---|---|---|
| FB | `PROVIDER_COVERAGE_GAP` | neither Quantiacs view returned FB prices |
| Qwest Q | `HISTORICAL_SCOPE_NOT_YET_DECIDED` | early-history gap is real; final P2 window is not preregistered |
| DISCK | `TERMINAL_GAP` | final eligible session price and terminal-value semantics remain absent |

There is no remaining `IDENTITY_CONFLICT`; deterministic provider/episode
identity is fail-closed.

## Validation and Qlib handoff

Pandera `0.33.1` and exchange_calendars `4.13.2` validated the corrected
dataset. The validation runtime was uv-isolated and changed no established AQ
environment.

```text
DUPLICATE_PROVIDER_ASSET_SESSION = 0
OUT_OF_EPISODE_JOINS = 0
INVALID_XNYS_SESSIONS = 0
NEGATIVE_VOLUME = 0
NONFINITE_REQUIRED_OHLC = 0
SILENT_FORWARD_FILL = NO
SYNTHETIC_PRICE_ROW = NO
SOURCE_ROW_SUBSET_EXACT = YES
PARQUET_ROUNDTRIP_EXACT = YES
CORRECTED_PARQUET_SHA256 = 0622f86ee6e69ab2baa60b9333d87beb2acab7c0df88325eb1c0f56afaf94892
CORRECTED_QLIB_INPUT_SHA256 = 667eb678a50ccf384a75a1be2936b4fc6070aeb485512b49826e8705145566f8
```

Because 647 corrected rows differ from the original 707-row handoff, Qlib
`0.9.8.dev26` `StaticDataLoader(config=<private correction parquet>).load()`
was rerun in the accepted Linux environment. It returned 647 rows with exact
index, column, dtype, and value equality. No model, feature handler,
prediction, backtest, Recorder, or MLflow operation ran.

```text
CORRECTED_QLIB_INGESTION = PASS
```

## Revision, retention, and terminal boundary

```text
REVISION_SEMANTICS = OBSERVED_REPEATABLE_NOT_VENDOR_VERSIONED
PRIVATE_DVC_RETENTION = BLOCKED_PENDING_PROVIDER_CONFIRMATION
TERMINAL_STATE = MATERIAL_GAP
```

Improved identity adjudication does not create delisting returns, delisting
values, acquisition consideration, or bankruptcy recovery. Price coverage and
terminal-value semantics remain separate gates. No durable DVC freeze was
performed.

## Technical adjudication

The FB and DISCK gaps are narrow, explicit post-2015 price gaps; identity is
sound, and 9 of 12 sampled episodes have complete price/action coverage. Qwest
is a real early-history limitation whose final Certification scope is not yet
decided. This supports a bounded free gap-fill authority audit, but does not
authorize heuristic filling or certify the route.

```text
IDENTITY_MAPPING = PASS
AQ_VS_PROVIDER_MEMBERSHIP = PASS
CORRECTED_OHLCV_VALIDATION = PASS
FINAL_TECHNICAL_ADJUDICATION = PASS_TECHNICAL_PILOT_FREE_GAP_FILL_REQUIRED
QUANTIACS_FREE_DATA_PILOT_CORRECTION = COMPLETE
QUANTIACS_TECHNICAL_VALIDATION = PASS_WITH_EXPLICIT_PRICE_GAPS
RECOMMENDED_CERTIFICATION_DATA_ROUTE = QUANTIACS_PRIMARY_PLUS_FREE_GAP_FILL_AUDIT
CURRENT_NEXT = P2_FREE_DATA_GAP_FILL_AUTHORITY_AUDIT
```

This is a technical pilot result, not data-source certification. A future task
must audit bounded free gap-fill authority and separately close provider
rights, revision-addressability, retention, and terminal-value policy.

## Safety and non-actions

```text
P2_CERTIFICATION = STARTED / IN_PROGRESS
P2_CERTIFIED_DATA_FOUNDATION = IN_PROGRESS
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PIT_UNIVERSE_CERTIFIED = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
LIVE_CAPITAL = NOT_AUTHORIZED
CREDENTIAL_LEAK_CHECK = PASS
ROBINHOOD_TOOLS_INVOKED = NONE
ACCOUNT_DATA_ACCESSED = NO
TRADING_ACTIONS = NONE
MODEL_TRAINING = NO
BACKTEST = NO
PAPER_TRADING = NO
LIVE_TRADING = NO
NEW_PAID_PROVIDER = NO
PAYMENT = NO
NEW_MARKET_DATA_ACCOUNT = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
PUSHED = NO
PR_CREATED = NO
MERGED = NO
```

Private correction evidence is retained only under
`D:\AQ_DATA\P2\quantiacs-free-data-pilot-correction-001`. No response,
Parquet, credential, or private artifact is committed to Git.
