# P2 Certified Data Free Route — Quantiacs Audit 001

Status: **COMPLETE — CONDITIONALLY QUALIFIED, FREE ACCESS TEST REQUIRED**

Task: `AUTONOMOUS-QUANT-P2-CERTIFIED-DATA-FREE-ROUTE-QUANTIACS-AUDIT-001`

Date: 2026-09-11

Authoritative base: `5b8eb2fbc3c09bc206ad1889c8d9703eda0abf91`

## 1. Scope and ownership

This was a read-only documentation and pinned-source audit. No Quantiacs account or API key was created, no provider endpoint was called, no market data was downloaded, no package was installed, and no P1 artifact was changed.

```text
CAPABILITY = P2 certification-grade free historical S&P 500 market-data authority
UPSTREAM_OWNER = Quantiacs Toolbox / Quantiacs Data Service + AQ InstrumentEpisodeV1 + DVC + Pandera + exchange_calendars
OWNERSHIP_MODE = MIXED
QUANTIACS_DATA_SERVICE = UPSTREAM_WHOLE
AQ_PIT = AQ_OWNED_THIN_ACCEPTED_MEMBERSHIP_AND_EPISODE_DOMAIN
DVC_PANDERA_EXCHANGE_CALENDARS = UPSTREAM_LEAF
UPSTREAM_ALREADY_DEPLOYED = PARTIAL
AQ_IMPLEMENTATION_ALLOWED = POLICY_CONTRACT_THIN_ADAPTER_EVIDENCE_ONLY
CUSTOM_ENGINE_REQUIRED = NO
```

Quantiacs membership is corroboration and possible provider-side coverage evidence. It does not replace accepted AQ `InstrumentEpisodeV1` membership or episode authority.

## 2. Evidence and upstream pin

Evidence was evaluated in the required order: current official documentation and terms, pinned Toolbox source and tests, then official support statements. Software licensing and market-data rights are separate authorities.

```text
QUANTIACS_REPO = quantiacs/toolbox
QUANTIACS_REPO_SHA = 9e5274c5ce102a66debc799fd2a2300969fb90f6
QUANTIACS_TOOLBOX_VERSION = 0.0.507
QUANTIACS_SOFTWARE_LICENSE = MIT
UPSTREAM_LATEST_COMMIT_DATE = 2025-12-19
REPOSITORY_ARCHIVED = NO
```

Primary evidence:

- [Quantiacs S&P 500 stock data documentation](https://quantiacs.com/documentation/en/data/stocks.html)
- [Quantiacs S&P 500 quick start](https://quantiacs.com/documentation/en/examples/q22_quick_start_s_p500.html)
- [Quantiacs stock data fields and metadata](https://quantiacs.com/documentation/en/user_guide/data_stocks.html)
- [Quantiacs local development](https://quantiacs.com/documentation/en/user_guide/local_development.html)
- [Quantiacs FAQ](https://quantiacs.com/faq)
- [Quantiacs Terms of Use](https://quantiacs.com/termsofuse)
- [Official Quantiacs support: historical S&P 500 membership](https://quantiacs.com/community/topic/781/how-to-get-stocks-in-sp500-index-at-a-given-time)
- [Pinned `qnt/data/stocks.py`](https://github.com/quantiacs/toolbox/blob/9e5274c5ce102a66debc799fd2a2300969fb90f6/qnt/data/stocks.py)
- [Pinned `qnt/data/id_translation.py`](https://github.com/quantiacs/toolbox/blob/9e5274c5ce102a66debc799fd2a2300969fb90f6/qnt/data/id_translation.py)
- [Pinned `qnt/data/common.py`](https://github.com/quantiacs/toolbox/blob/9e5274c5ce102a66debc799fd2a2300969fb90f6/qnt/data/common.py)
- [Pinned SPX/cache tests](https://github.com/quantiacs/toolbox/tree/9e5274c5ce102a66debc799fd2a2300969fb90f6/qnt/tests)

The pinned live SPX test expects 808 historical assets. Current official documentation says more than 750 stocks that were constituents at some point since 2006. An official support observation dated 2026-02-24 reported 842 historical assets, of which 658 still had active OHLC coverage. These are time-layered facts, not a single immutable count; the service-side dataset can evolve.

## 3. S&P 500 universe coverage

```text
SPX_HISTORY_START = 2006-01-01
SPX_HISTORICAL_ASSET_COUNT = >750_DOCUMENTED; 808_PINNED_TEST_EXPECTATION; 842_OFFICIAL_SUPPORT_OBSERVATION_2026-02-24
DELISTED_SECURITIES_INCLUDED = YES_ON_PAPER
DYNAMIC_SPX_MEMBERSHIP_AVAILABLE = YES_ON_PAPER
```

For the SPX dataset, official Quantiacs documentation and support define `is_liquid == 1` as inclusion in the S&P 500 at the observed date. This meaning is dataset-specific; the generic stocks dataset instead defines liquidity using prior-month traded dollar volume. SPX membership is represented as a date/session-dependent field across the historical asset panel.

Removed and delisted constituents are represented, and aliases such as `ALTR~1` demonstrate separate observations with reused display tickers. Official support also acknowledges that historical constituent completeness degrades further back in time, with the early history reportedly below 500 members. A pilot must therefore measure date-by-date coverage and must not promote the provider's membership flag over accepted AQ PIT facts.

## 4. Security identity

The provider returns an opaque server asset ID. `id_translation.py` maps it to a preferred `exchange:symbol`, stores that mapping in `id-translation.csv`, and appends `~1`, `~2`, and so on when the preferred display ID collides. A previously seen server ID reuses its stored mapping. This proves deterministic client mapping for an observed server ID, but official material does not establish that the opaque ID is a permanent security-level rather than listing-level identifier.

Official stock-list metadata exposes FIGI and CIK. It does not expose ISIN in the documented response. Official support uses ISIN to explain that the old SNDK acquired in 2016 and the new SNDK issued after a 2025 spin-off are different securities, but that statement does not make ISIN an exposed provider field.

```text
STABLE_PROVIDER_SECURITY_ID = CONDITIONAL
PROVIDER_ID_LEVEL = UNKNOWN_SECURITY_OR_LISTING
FIGI_AVAILABLE = YES
CIK_AVAILABLE = YES
ISIN_AVAILABLE = NO
IDENTIFIER_TEMPORAL_SEMANTICS = UNKNOWN_NEEDS_PILOT
TICKER_REUSE_DISTINGUISHED = CONDITIONAL
CAN_PROVIDER_ID_MAP_DETERMINISTICALLY_TO_INSTRUMENTEPISODEV1 = CONDITIONAL
```

The future pilot must freeze the server ID, translated ID, metadata, and the AQ episode match. Ticker text alone is never sufficient. Reused ticker episodes must remain distinct and undated ambiguity must fail closed.

## 5. Price authority and transformations

Pinned `stocks.py` exposes these SPX fields:

```text
open low high close vol divs split_cumprod is_liquid
```

The standalone `split` field is excluded in SPX mode. Split events are derivable from changes or ratios in `split_cumprod`.

For generic stocks, `load_data()` applies `adjust_by_splits()` client-side; the SPX route does not apply that function because it consumes the SPX service representation. Official SPX documentation describes the delivered price history as split-adjusted. `restore_origin_data()` can deterministically reverse the arithmetic using `split_cumprod`: divide OHLC and dividends by the factor and multiply volume by it. The result is `DETERMINISTICALLY_RECONSTRUCTED`, not raw provider bytes. A pilot must quantify precision and rounding before claiming information preservation.

Dividends are a separate explicit field and do not themselves rewrite historical OHLC in the inspected transformation functions.

```text
OHLCV_AVAILABLE = YES
DIVIDENDS_AVAILABLE = YES
SPLIT_EVENT_AVAILABLE = DERIVABLE
LOADED_SPX_PRICE_SEMANTICS = PROVIDER_RETURNED_SPLIT_ADJUSTED
UNADJUSTED_PRICE_RECOVERABLE = CONDITIONAL
UNADJUSTED_PRICE_SEMANTICS = DETERMINISTICALLY_RECONSTRUCTED
VOLUME_RECONSTRUCTION = DETERMINISTIC_SUBJECT_TO_PRECISION_VALIDATION
```

## 6. Corporate-action authority

| Event | Authority classification | Audit conclusion |
|---|---|---|
| Dividends | `EXPLICIT_PROVIDER_FIELD` | `divs` is returned. Pilot must validate timing and units. |
| Splits | `DERIVABLE_FROM_PROVIDER_FIELD` | Derive from `split_cumprod`; no standalone SPX `split` field. |
| Ticker changes | `AQ_PIT_EVIDENCE_AVAILABLE` | Use accepted AQ evidence where present; otherwise require external official evidence. |
| Merger/acquisition consideration | `EXTERNAL_OFFICIAL_EVIDENCE_REQUIRED` | Never infer cash or stock consideration from the final price. |
| Spin-offs | `EXTERNAL_OFFICIAL_EVIDENCE_REQUIRED` | Provider price/membership fields do not prove allocation terms. |
| Bankruptcy/terminal state | `EXTERNAL_OFFICIAL_EVIDENCE_REQUIRED` | Price disappearance is not a zero-return observation. |
| Delisting value | `UNAVAILABLE` | No inspected SPX field supplies it. |
| Delisting return | `UNAVAILABLE` | No inspected SPX field supplies it. |

```text
DELISTING_RETURN_AVAILABLE = NO
DELISTING_VALUE_AVAILABLE = NO
TERMINAL_STATE_GAP = MATERIAL
```

The contract's explicit `MISSING_DELISTING_VALUE` state can represent absence; it does not make the economic consequence known. Certification policy must later specify an evidence-backed liquidation convention, and a provider pilot must establish whether usable prices/actions exist through the required exit session. Until both conditions are satisfied, unresolved terminal state remains material and blocks affected episodes.

## 7. Membership exit and liquidation timing

`is_liquid` is a dated SPX membership observation on paper. The reviewed evidence does not prove for every removal that it turns false at AQ's authoritative effective session, that a usable price exists on the last eligible session, or that acquisitions and bankruptcies always permit a clean tradable exit. Membership exit cannot be assumed to make terminal semantics irrelevant.

The bounded pilot must include exactly these scenario classes:

1. `ACTIVE`
2. `NORMAL_INDEX_REMOVAL`
3. `TICKER_RENAME`
4. `ACQUISITION`
5. `BANKRUPTCY`
6. `TICKER_REUSE`
7. `EXIT_REENTRY`

For each sample, compare provider identity and `is_liquid` timing to accepted AQ episode/membership evidence; inspect price/action availability at the last eligible and first ineligible sessions; and preserve unresolved terminal states rather than filling them heuristically.

## 8. Time and revision semantics

Pinned `common.py` implements `set_max_datetime()` by rewriting the data base URL to include `/last/<timestamp>/`. This is source behavior, not an official documented guarantee that the response is an immutable vendor vintage. No inspected evidence supplies a release/version ID or promises that corrections and backfills cannot rewrite past responses.

```text
AS_OF_REQUEST_IMPLEMENTATION = PRESENT_IN_PINNED_SOURCE
AS_OF_REQUEST_PUBLICLY_DOCUMENTED = NO_EVIDENCE_FOUND
IMMUTABLE_VENDOR_VINTAGE = NOT_PROVEN
RELEASE_VERSION_ID = NONE_OBSERVED
HISTORICAL_REWRITE_BEHAVIOR = UNKNOWN
REVISION_SEMANTICS = UNKNOWN_NEEDS_PILOT_OR_PROVIDER_CONFIRMATION
```

## 9. Cache, exact evidence, and DVC handoff

Pinned cache behavior:

```text
CACHE_DIR_DEFAULT = data-cache
CACHE_RETENTION_DEFAULT = 7_DAYS
CACHE_KEY = SHA1_OF_PICKLED_REQUEST_ARGUMENTS
CACHE_REQUEST_ARGUMENTS_RETAINED = YES
CACHE_RESPONSE = DECOMPRESSED_PROVIDER_RESPONSE_BODY_BYTES
RAW_TRANSPORT_BYTES_RETAINED = NO
```

The cache stores request arguments and the decompressed provider response body before xarray parsing. Those exact provider-returned body bytes can technically be copied before expiry and SHA-256 hashed; they must be described as `PROVIDER_RETURNED_DECOMPRESSED_RESPONSE_BYTES`, not raw transport/compressed bytes.

A separately authorized pilot can technically perform:

```text
Quantiacs provider-returned response bytes
  -> retained evidence bytes + request manifest + SHA-256
  -> normalized episode-scoped snapshot
  -> Pandera validation
  -> exchange_calendars validation
  -> private DVC freeze, only if data-rights confirmation permits
  -> Qlib handoff
```

DVC remains reproducibility owner. The Toolbox cache is temporary transport evidence, not the certified snapshot authority.

```text
RAW_RESPONSE_HASHABLE = YES
REPRODUCIBLE_VENDOR_VINTAGE = NOT_PROVEN
```

## 10. Free access

Official FAQ/documentation describe strategy development and data access as free. Local development requires a free Quantiacs account and an API key obtained from the profile. No payment-method requirement, time-limited trial, or documented rate limit was found in the reviewed material.

```text
QUANTIACS_DATA_ACCESS_COST = FREE
QUANTIACS_ACCOUNT_REQUIRED = YES
QUANTIACS_API_KEY_REQUIRED_FOR_LOCAL = YES
PAYMENT_METHOD_REQUIRED = UNKNOWN_NOT_DOCUMENTED
TRIAL_LIMIT = NONE_DOCUMENTED
RATE_LIMIT = UNKNOWN_NOT_DOCUMENTED
```

No account or key was created in this audit.

## 11. Data terms and retention gate

The MIT license applies to Toolbox software only. It does not license the market data.

The current Terms of Use grant limited, non-transferable service access for personal purposes or business only in furtherance of collaboration with Quantiacs. They prohibit transferring/providing market data or a synopsis/analysis to third parties and prohibit public reproduction, redistribution, and resale of Quantiacs content. The terms also disclaim data accuracy, completeness, and timeliness. The reviewed terms do not explicitly grant long-term retention after account termination, private content-addressed archival, or backup rights.

Local development and cache documentation show that local caching is technically intended during use. They do not settle long-term data rights. Therefore:

```text
TOOLBOX_CODE_LICENSE = MIT
MARKET_DATA_USE_RIGHTS = QUANTIACS_TERMS_OF_USE
LOCAL_DOWNLOAD_CACHE = TECHNICALLY_SUPPORTED; RIGHTS_LIMITED_BY_TERMS
LONG_TERM_PRIVATE_RETENTION = UNKNOWN_REQUIRES_PROVIDER_CONFIRMATION
PRIVATE_DVC_RETENTION_ALLOWED = UNKNOWN
PERSONAL_RESEARCH_SYSTEM_USE = CONDITIONAL_ON_TERMS_AND_PROVIDER_CONFIRMATION
PERSONAL_LIVE_TRADING_RESEARCH_USE = UNKNOWN_REQUIRES_PROVIDER_CONFIRMATION
BACKUP_COPIES = UNKNOWN_REQUIRES_PROVIDER_CONFIRMATION
THIRD_PARTY_TRANSFER_ALLOWED = NO
PUBLIC_GIT_DATA_STORAGE_ALLOWED = NO
PUBLIC_DVC_REMOTE_ALLOWED = NO
PUBLIC_REDISTRIBUTION_ALLOWED = NO
COMMERCIAL_RESALE_ALLOWED = NO
DATA_RETENTION_AFTER_ACCOUNT_TERMINATION = UNKNOWN_REQUIRES_PROVIDER_CONFIRMATION
```

This is a conservative contract qualification, not a legal conclusion. Before a DVC-backed certification pilot retains provider bytes, the owner must obtain written provider confirmation for private long-term retention, private content-addressed snapshots/backups, intended personal research use, and post-termination handling.

## 12. Source quality and maintenance

The repository is active rather than archived at the audited pin. Release `0.0.507` is declared in pinned package metadata. Relevant tests cover data initialization/cache behavior and a live SPX asset-count expectation of 808. Because that SPX test depends on the provider, it was inspected but not executed. Official documentation, the pinned test, and a newer official support count do not describe an immutable release; the discrepancy reinforces the need to freeze each pilot response and its request manifest.

## 13. WIKI/PRICES cross-check

```text
CAN_WIKI_PRICES_BE_A_USEFUL_READ_ONLY_CROSSCHECK_FOR_PRE_2018_ROWS = YES
```

Nasdaq Data Link's WIKI/PRICES data is stale/discontinued after 2018. It may provide a read-only diagnostic comparison for pre-2018 price, dividend, or split rows. It must not become live/current authority and cannot establish AQ identity episodes from ticker strings alone. It was not downloaded in this audit.

## 14. CertificationDataContractV1 matrix

| Contract section | Result | Evidence-bounded reason |
|---|---|---|
| A. Security identity | `PARTIAL` | Stable server IDs and collision aliases exist, with FIGI/CIK metadata, but identifier level and temporal semantics are not authoritative. |
| B. Episode-scoped price coverage | `UNKNOWN_NEEDS_PILOT` | Historical OHLCV exists, but complete deterministic coverage for accepted AQ episodes has not been measured. |
| C. Delisted/predecessor coverage | `PARTIAL` | Former/delisted constituents are represented, but early coverage is incomplete and terminal value/return is absent. |
| D. Corporate actions | `PARTIAL` | Dividends are explicit and splits derivable; terminal, consideration, spin-off, and some identity events require external evidence. |
| E. Time and revision semantics | `UNKNOWN_NEEDS_PILOT` | `/last/<timestamp>` exists in code, but immutable-vintage and historical rewrite semantics are undocumented. |
| F. Survivorship completeness | `UNKNOWN_NEEDS_PILOT` | Dynamic historical membership and former members exist, but official support acknowledges early incompleteness. |
| G. Reproducibility | `PARTIAL` | Exact decompressed response bytes are hashable; immutable revision semantics and lawful long-term private retention remain unresolved. |

The frozen contract was not weakened. No section is promoted to `PASS_ON_PAPER` where an actual provider observation or provider confirmation is still required.

## 15. Composite free route evaluation

```text
ARCHITECTURE = AQ InstrumentEpisodeV1
             + Quantiacs SPX historical data and provider identity
             + Quantiacs dividend/split evidence
             + official evidence for terminal/corporate-action gaps
             + Pandera + exchange_calendars + DVC
             -> certification-candidate Dataset -> Qlib

COMPLEXITY = MODERATE_THIN_MAPPING_AND_VALIDATION
IDENTITY_SAFETY = CONDITIONAL
SURVIVORSHIP_CONTROL = PARTIAL_NEEDS_PILOT
TERMINAL_GAP = MATERIAL
REPRODUCIBILITY = CONDITIONAL
LEGAL_RETENTION = UNKNOWN_REQUIRES_PROVIDER_CONFIRMATION
QLIB_HANDOFF = FEASIBLE_AFTER_FROZEN_VALIDATED_SNAPSHOT
```

No additional generic provider is justified by this paper audit. External official evidence is permitted only for concrete terminal and corporate-action gaps.

## 16. Decision and bounded next step

```text
QUANTIACS_CLASSIFICATION = CONDITIONALLY_QUALIFIED_NEEDS_FREE_ACCESS_TEST
FREE_ROUTE_PILOT_JUSTIFIED = YES
RECOMMENDED_CERTIFICATION_DATA_ROUTE = QUANTIACS_FREE_PROVIDER_PILOT
CURRENT_NEXT = P2_QUANTIACS_FREE_DATA_PILOT_OWNER_AUTHORIZATION
FINAL_CLASSIFICATION = PASS_WITH_PROVIDER_CONFIRMATION_REQUIRED
```

This classification means only that a small, bounded free provider pilot is justified. It does not mean the data is certification-grade. The pilot requires separate owner authorization because the owner must create/use a free account and local API key. Before durable private DVC retention, written provider confirmation is required for the unresolved data-rights questions.

The pilot must fail closed unless it can:

- freeze exact request arguments and provider-returned decompressed response bytes with SHA-256;
- reconcile server IDs and metadata to accepted AQ episodes without ticker-only identity;
- verify date-by-date SPX membership and coverage for all seven required scenarios;
- measure missing sessions, duplicated keys, action timing, and terminal gaps;
- determine whether `/last/<timestamp>` provides a reproducible view or merely a request boundary;
- keep all data and credentials outside Git and any public DVC remote; and
- retain data only within confirmed provider rights.

## 17. Preserved project state and non-actions

```text
P2_CERTIFICATION = STARTED / IN_PROGRESS
P2_CERTIFIED_DATA_FOUNDATION = IN_PROGRESS
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PIT_UNIVERSE_CERTIFIED = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
LIVE_CAPITAL = NOT_AUTHORIZED

ACCOUNT_CREATED = NO
API_KEY_CREATED = NO
PROVIDER_CALLED = NO
DATA_DOWNLOADED = NO
PACKAGE_CHANGED = NO
P1_ARTIFACTS_CHANGED = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
```
