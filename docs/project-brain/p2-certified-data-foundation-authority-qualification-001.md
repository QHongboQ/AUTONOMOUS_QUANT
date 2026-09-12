# P2 Certified Data Foundation — Authority Qualification 001

## Decision record

```text
TASK = AUTONOMOUS-QUANT-P2-CERTIFIED-DATA-FOUNDATION-AUTHORITY-QUALIFICATION-001
STATUS = COMPLETE
P2_CERTIFIED_DATA_FOUNDATION = IN_PROGRESS
P2_DATA_AUTHORITY_QUALIFICATION = COMPLETE
CERTIFICATION_DATA_CONTRACT_V1 = FROZEN
CERTIFICATION_DATA_PROVIDER_DECISION_REQUIRED = YES
CURRENT_NEXT = P2_CERTIFIED_DATA_PROVIDER_DECISION
```

This task qualifies authority surfaces; it does not acquire data or qualify an
actual extraction. P1 remains complete and research-only. No provider account,
subscription, token, package, adapter, download, or provider call was created.

## Ownership boundary

Market-data facts must come from a qualified upstream provider
(`UPSTREAM_WHOLE`). DVC, Pandera, and exchange_calendars retain their bounded
`UPSTREAM_LEAF` roles for snapshot reproducibility, tabular validation, and
session semantics. AQ owns only the certification acceptance policy, the domain
contract, the mapping from provider identity to accepted `InstrumentEpisodeV1`
intervals, and the decision evidence.

The existing AQ PIT domain remains the accepted authority for S&P 500 membership
facts, ticker-episode boundaries, ticker reuse, exit/re-entry, rename boundaries,
and accepted project-specific corrections. It is not a generic security master.
A vendor's current ticker table or historical constituent convenience cannot
silently replace these accepted facts.

## CertificationDataContractV1 — frozen

This is the minimum acceptance boundary for a certification-provider pilot. A
pilot must fail closed on any unsatisfied required item; marketing claims and
ticker-name similarity are not evidence.

### A. Security identity

- Every provider row must carry a stable security-level identifier, or immutable
  evidence sufficient to bind it to exactly one accepted
  `InstrumentEpisodeV1` interval.
- Ticker text alone is insufficient. Reused tickers and non-contiguous
  membership episodes must never collapse.
- The extraction must retain the provider identifier, provider symbol, mapping
  evidence, episode identifier, mapping interval, and mapping decision status.
- Provider identity may corroborate AQ PIT facts; it does not override them
  without a separately accepted correction.

### B. Episode-scoped price coverage

- Every episode required by the registered certification window must have daily
  `session`, `open`, `high`, `low`, `close`, and `volume` rows attributable only
  inside that episode's valid interval.
- Raw/unadjusted OHLCV is preferred and must be retained when offered.
- Adjusted history cannot be the sole authority where later actions can rewrite
  past values. Every adjustment mode and field must be explicit.
- No price row may be joined by undated ticker text or carried across an episode
  boundary.

### C. Delisted and predecessor coverage

- Required coverage includes delisted, acquired, bankrupt, renamed,
  predecessor/successor, index-exited, and later-inactive securities.
- The normalized record must distinguish `LAST_TRADED_PRICE`,
  `DELISTING_VALUE_OR_RETURN`, and explicit `MISSING_DELISTING_VALUE`.
- Provider absence, a missing terminal value, and a zero return are different
  states. None may be silently dropped or substituted.

### D. Corporate actions

- The authority must expose explicit, auditable split, dividend, and ticker-change
  facts and their effective/ex-date semantics.
- Where relevant to a required episode, merger/acquisition distributions,
  spin-offs, cash/stock consideration, and other terminal distributions must be
  available or explicitly unresolved.
- A total-return or adjusted-price field is supplementary; it cannot hide the
  underlying actions needed for temporal certification.

### E. Time and revision semantics

- Price session/date and corporate-action effective/ex-date meanings must be
  explicit.
- Each extraction must record retrieval timestamp, provider product and version
  or snapshot/release identity, query parameters, and applicable calendar.
- Vendor corrections, revisions, and backfills must be represented as such. If
  the provider has no original publication timestamp, the limitation is recorded
  and `first_available_at` must not be invented.

### F. Survivorship completeness

- `current symbols + current S&P 500` is automatic failure.
- Every pilot must measure `REQUIRED_EPISODES`, `MAPPED_EPISODES`,
  `PRICE_COVERED_EPISODES`, `ACTION_COVERED_EPISODES`,
  `DELISTED_COVERED_EPISODES`, and `UNRESOLVED_REQUIRED_EPISODES`.
- Certification publication requires `UNRESOLVED_REQUIRED_EPISODES = 0`, unless
  an exclusion was registered by certification policy before the sealed protocol.
  Post-result exclusions are forbidden.

### G. Reproducibility

- DVC remains snapshot authority. An accepted extraction must retain a raw
  manifest, exact request/query manifest, provider/product/version identity,
  retrieval timestamp, byte hashes, normalized snapshot, DVC dependency/output
  hashes, mapping-policy hash, and certification-policy hash.
- A mutable provider cloud response is not a frozen certification dataset.
  Required raw bytes must be legally retainable and frozen content-addressably.
- Re-extraction equivalence is not assumed: vendor-revised bytes create a new
  candidate snapshot and require explicit comparison.

## Current P1 authority gap

The P1 Qlib-native provider proves a complete research pipeline, not strict PIT
data authority. Its local calendar begins in 2015 and its static/current-style
`sp500` path does not prove complete inactive/predecessor episode coverage,
stable security identity, terminal value, or revision time. The prior OpenBB POC
proved a bounded `provider="yfinance"` handoff with explicit
`adjustment="splits_only"` and `include_actions=true`; it did not prove
certification completeness.

Official yfinance documentation describes the library as an unofficial Yahoo
interface intended for research/education and personal use, and its history API
supports repair/adjustment behavior rather than a versioned institutional
snapshot authority ([yfinance documentation](https://ranaroussi.github.io/yfinance/),
[PriceHistory.history](https://ranaroussi.github.io/yfinance/reference/yfinance.price_history.html)).

```text
P1_CURRENT_DATA_CLASSIFICATION = RESEARCH_ONLY_NOT_CERTIFICATION_GRADE
P1_PRICE_AUTHORITY_STRICT_PIT = FAIL
```

It remains valid for exploratory research. It may not be promoted by relabeling
the existing snapshot or its already-observed test interval.

## Provider qualification matrix

`PASS` below means official documentation exposes the capability. `PARTIAL`
means the documented surface does not close the contract without an access test
or AQ mapping evidence. It is not a certification result.

| Provider path | Identity | Delisted | Price history | Corporate actions | Index membership | Time semantics | Reproducible extraction | License / retention | Access / cost | OpenBB integration if any | Qlib handoff feasibility | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Current P1 Qlib/Yahoo + OpenBB/yfinance | `FAIL`: ticker-oriented; no demonstrated immutable security mapping | `FAIL`: complete inactive/predecessor set not demonstrated | `PASS` for bounded research OHLCV | `PARTIAL`: actions/adjustment options exist, but required episode completeness and immutable revision authority do not | `FAIL`: current-style `sp500` is not strict PIT authority | `PARTIAL`: session and action request semantics exist; source publication/revision time does not | `PARTIAL`: AQ froze a research snapshot, not a versioned source authority | Personal-use Yahoo terms; no certification-retention proof | Free access surface; not determinative | Existing yfinance provider route | Already proven for research | `RESEARCH_ONLY_NOT_CERTIFICATION_GRADE` |
| Norgate Data US Stocks Platinum/Diamond | `PASS` on paper: unique unchanging `assetid` | `PASS` on paper: major-exchange delisted set; vendor explicitly does not claim universal completeness | `PASS` on paper: daily OHLCV, unadjusted close and explicit adjustment modes | `PARTIAL/PASS`: dividends and capital-event series cover splits and complex reorganizations; terminal consideration/value needs access validation | `PASS` on paper: S&P 500 constituent series from Mar 1957, described as essentially complete | `PARTIAL`: session and ex-date behavior documented; release/revision snapshot behavior needs validation | `PARTIAL`: local API/export can be hashed, but repeatability and retained raw/version identity require pilot proof | Proprietary subscription; API needs Windows Norgate Data Updater; official terms require source data, snapshots and metadata to be deleted after lapse, so durable evidence requires uninterrupted entitlement | Paid US Stocks Platinum or Diamond | No relied-upon OpenBB route | Straightforward local DataFrame/export normalization, then frozen Qlib provider build while entitlement remains active | `CONDITIONALLY_QUALIFIED_NEEDS_ACCESS_TEST` |
| EODHD | `PARTIAL`: ISIN/search and ID-mapping surfaces exist, but immutable historical security binding is not established | `PARTIAL`: delisted symbols and EOD history exist; pre-2018 non-price coverage is explicitly limited | `PASS` on paper for daily OHLCV | `PARTIAL`: dividends, splits and symbol changes exist, but the required early delisted action/terminal-value surface is incomplete | `PARTIAL`: S&P 500 reconstruction is reliable only from Apr 2012 and documented as incomplete earlier, with some 2012–2015 short coverage; this is corroboration only, not the rejection basis | `PARTIAL`: dates/effective dates exist; immutable snapshot/revision/first-published authority is not demonstrated | `PARTIAL`: API payloads can be hashed but no official immutable release identity was established | Commercial API terms and retention rights require plan review | Paid API needed beyond limited free history | No relied-upon OpenBB route | Feasible JSON/CSV normalization, but required early delisted action/final-value, immutable identity and snapshot-authority gaps remain | `REJECTED_FOR_REQUIRED_SCOPE` |
| CRSP US Stock Database | `PASS` on paper: permanent `PERMNO` security identifier and name history | `PASS` on paper: delisting codes, dates, prices/amounts, returns and successor links | `PASS` on paper: daily/monthly stock data including inactive securities | `PASS` on paper: distributions and delisting/final-return semantics | `PARTIAL`: CRSP index products are useful corroboration, while AQ retains accepted S&P episode authority | `PASS` on paper for dated observations and monthly product releases; exact vintage must be frozen | `PASS` in principle through dated licensed releases and retained files, subject to entitlement | Institutional proprietary license; permitted retention and derivative-output terms must be confirmed | Paid institutional access; price not publicly qualified here | No relied-upon OpenBB route | Feasible flat-file/SAS extraction into a frozen normalized Qlib provider; non-trivial mapping pilot | `CONDITIONALLY_QUALIFIED_NEEDS_ACCESS_TEST` |

### Official documentation authority

The following official material was reviewed on 2026-09-11. Historical index
membership is evaluated as corroboration only; it is not used as a substitute
for AQ's accepted episode facts or as the sole provider-selection criterion.

Norgate's official content table states that delisted securities require
Platinum/Diamond, describes its delisted-set boundary, and explicitly disclaims
complete early coverage ([US Delisted](https://norgatedata.com/data-content-tables.php#us-delisted)).
The same table documents S&P 500 constituents from March 1957 and calls the
history essentially complete to the stated start date
([US Historical Index Constituents](https://norgatedata.com/data-content-tables.php#us-historical-index-constituents)).
Its published Python interface documents an unchanging `assetid`, explicit
price-adjustment selection, unadjusted close, dividends, capital events, and the
Windows-only running Updater/subscription prerequisite
([norgatedata Python package](https://pypi.org/project/norgatedata/)). The official
package comparison identifies Platinum/Diamond as the levels carrying historical
constituents and delisted coverage
([Norgate Stock Market Packages](https://norgatedata.com/stockmarketpackages.php)).
Norgate's official licensing FAQ says the local database becomes inaccessible
and extracted data, normalized rows, snapshots, events, backups, and metadata
must be deleted after a subscription lapses; uninterrupted entitlement is
therefore a hard provenance-retention condition
([Norgate Subscription & Licensing FAQ](https://norgatedata.com/faq.php)).

EODHD officially documents delisted-list access, EOD coverage limitations before
2018, and symbol-change effective dates
([Delisted Companies Data](https://eodhd.com/financial-apis/delisted-stock-companies-data-2),
[Symbol Change History](https://eodhd.com/financial-apis-blog/symbol-change-history-api)).
Its fundamentals documentation exposes `HistoricalTickerComponents`, while its
own S&P 500 history notes reliable reconstruction only from April 2012 and
omissions before that date
([Fundamental Data Feed](https://eodhd.com/financial-apis/stock-etfs-fundamental-data-feeds),
[S&P 500 Historical Constituents](https://eodhd.com/financial-apis-blog/sp-500-historical-constituents-data)).
Its supported SDK describes OHLCV and identifier mapping, but that does not by
itself prove immutable episode mapping or terminal-return coverage
([EODHD SDK](https://eodhd.com/financial-apis/node-js-typescript-sdk-for-eodhd-financial-apis)).

CRSP's official US Stock guide documents permanent security identifiers, prices,
distributions and delisting information
([CRSP 10-Year US Stock Database Guide](https://www.crsp.org/wp-content/uploads/guides/CRSP10_Year_US_Stock_Database_Guide.pdf)).
Its field guide exposes `PERMNO`, delisting date/code, new security/company links,
delisting price/date/amount, and delisting returns
([CRSP US Stock and Indexes Database Guide](https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-guide-flat-file-format-1-0/)).
Current release notes identify dated database products and delivery formats,
which a future licensed extraction must pin
([CRSP Release Notes](https://www.crsp.org/wp-content/uploads/mdaz_202603.pdf)).

These are official capability statements, not observations from paid data.

## Exact unresolved questions

### Norgate Data

1. Will the owner authorize uninterrupted entitlement for every period in which
   AQ must retain the raw certification snapshot? Official lapse terms require
   deletion of source-derived data and metadata, so a lapsed subscription cannot
   satisfy the durable snapshot contract.
2. Can Platinum/Diamond export every AQ-required 2010–present episode by
   `assetid`, including reused tickers, without a symbol-resolution ambiguity?
3. For every acquired/bankrupt/delisted episode, which fields distinguish last
   trade from cash/stock consideration or other terminal value, and where is
   absence explicit?
4. Can the Updater/database release identity and vendor corrections be frozen in
   a request manifest, and will repeated extraction against one local release be
   byte- or content-stable?
5. Does the selected tier permit the planned personal research use, and can the
   certification governance accept the continuing-subscription retention
   dependency? No installation or purchase occurs before written acceptance.

### CRSP

1. Is an affordable lawful entitlement available to this personal project, and
   what retention/derived-data rights survive loss of access?
2. Which exact CRSP product/vintage contains every required daily episode and
   distribution/delisting field, and can that licensed vintage be frozen by DVC?
3. What deterministic mapping evidence joins `PERMNO`/name history to each AQ
   `InstrumentEpisodeV1` without inferring corporate continuity?
4. Does the selected delivery expose all required terminal distributions and
   explicit missing states at daily resolution?

### EODHD (rejection boundary)

1. Can EODHD provide an immutable security identity across symbol reuse rather
   than only identifier lookup around a ticker?
2. Can it provide auditable corporate-action and terminal-value evidence for
   every required pre-2018 delisted episode?
3. Is there a versioned/revision-addressable extraction and contractually
   retainable raw snapshot?

Positive answers could justify a future re-audit; they are not assumed here.

## Provider decision gate and shortlist

No candidate is fully qualified without licensed-access validation. Weakening
`CertificationDataContractV1` to preserve a free path is forbidden.

```text
QUALIFIED_PROVIDER_COUNT = 0
CONDITIONALLY_QUALIFIED_PROVIDER_COUNT = 2
BEST_PERSONAL_PROJECT_OPTION = NORGATE_DATA_US_STOCKS_PLATINUM_OR_DIAMOND
BEST_INSTITUTIONAL_REFERENCE = CRSP_US_STOCK_DATABASE
CERTIFICATION_DATA_PROVIDER_DECISION_REQUIRED = YES
PAID_ACCESS_REQUIRED_FOR_RECOMMENDED_PATH = YES
```

Norgate is the smallest personal-project pilot because the documented Windows
Python surface combines an unchanging asset identifier, unadjusted/adjustable
prices, actions, delisted securities, and historical S&P membership in one local
product. Its remaining blockers are commercial authorization, retention terms,
the required uninterrupted entitlement, terminal-value semantics, and observed
coverage/mapping.

CRSP is the institutional reference because its security identifier, name
history, distributions, and explicit delisting-return/final-value fields most
closely match the contract. Its blockers are entitlement, licensing/retention,
product selection, and an observed episode mapping/extraction.

No additional provider was added: the mandatory candidates already establish
the smallest meaningful personal/institutional decision pair.

## Next execution step

The owner must choose and authorize one paid/licensed path before any pilot. A
later, separately authorized `P2_CERTIFIED_DATA_PROVIDER_PILOT` must use a small
predeclared episode sample that includes an active security, rename, acquisition,
delisting/bankruptcy, ticker reuse, and exit/re-entry. It must test identity
mapping, raw OHLCV, actions, terminal states, revision metadata, license-compliant
snapshot retention, completeness counters, Pandera validation, exchange calendar
alignment, DVC freezing, and Qlib handoff. It must not train or certify a model.

```text
P2_CERTIFIED_DATA_FOUNDATION = IN_PROGRESS
P2_DATA_AUTHORITY_QUALIFICATION = COMPLETE
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PIT_UNIVERSE_CERTIFIED = NO
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
AQ_CUSTOM_DATA_ENGINE = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
CURRENT_NEXT = P2_CERTIFIED_DATA_PROVIDER_DECISION
```
