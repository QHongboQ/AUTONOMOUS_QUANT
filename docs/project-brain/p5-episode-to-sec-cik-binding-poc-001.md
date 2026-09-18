# P5 Episode to SEC CIK Binding POC 001

## Outcome

```text
TASK = AUTONOMOUS-QUANT-P5-EPISODE-TO-SEC-CIK-BINDING-POC-001
EPISODE_TO_SEC_CIK_BINDING = PARTIAL
PARTIAL_CLASSIFICATION = TRACTABLE_FAIL_CLOSED
SAMPLE_EPISODE_COUNT = 8
PASS_EXACT_COUNT = 3
PASS_CORROBORATED_COUNT = 3
PASS_COUNT = 6
AMBIGUOUS_COUNT = 1
NO_SEC_FILER_COUNT = 0
MISSING_AUTHORITY_COUNT = 1
CURRENT_DEVELOPMENT_NEXT = P5_FUNDAMENTAL_HISTORICAL_DATASET_DESIGN_001
FINAL_CLASSIFICATION = PASS_TRACTABLE_PARTIAL
```

The POC proves that historical `InstrumentEpisodeV1` rows can be bound to SEC
filer CIKs only through date-bounded evidence composition. It does not authorize
a scaled fundamental dataset build. The operational P2 authority remains
unchanged:

```text
CURRENT_NEXT = P2_FORMULAIC_ALPHA_SEALED_OOS_ACCUMULATION_001
P2_FORMULAIC_ALPHA_V2 = ACTIVE_SEALED_OOS_ACCUMULATION
P2_V2_SEALED_OOS_ACCESSED = NO
```

## Binding authority

SEC CIK is the stable filer identifier. The SEC's periodically updated
`company_tickers.json` association is discovery/corroboration only: the SEC
does not guarantee its accuracy or scope, and it is not a historical
ticker-interval authority. EdgarTools 5.58.0 correctly supports direct CIK
construction and SEC retrieval/parsing, but its ticker constructor resolves
through bundled or live current SEC ticker data. It therefore does not convert
a current ticker lookup into historical authority.

- [SEC EDGAR data access and ticker/CIK association caveat](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data)
- [SEC submissions API and current/former-name metadata](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [EdgarTools direct CIK and ticker lookup guidance](https://edgartools.readthedocs.io/en/latest/guides/finding-companies/)

```text
TICKER_ONLY_BINDING = PROHIBITED
CURRENT_TICKER_TO_CIK_BACKFILL = PROHIBITED
CURRENT_SP500_SURVIVOR_LIST = PROHIBITED
CURRENT_TICKER_MAPPING_USED_AS_SOLE_AUTHORITY = NO
```

Quantiacs provider metadata contributes a provider asset and sometimes a CIK,
but the CIK field is incomplete and becomes date-safe only when composed with
an accepted episode/provider relation or independent SEC authority. SimFin's
current SimFin ID and ISIN can corroborate a security relation; its current
ticker backfill is not historical episode authority. A further current-ticker
mapping project would not close the remaining cases and was not introduced.

## Episode snapshot rule

The authoritative full P1 episode file and the later P2 2015-window episode map
do not produce identical episode IDs. For example, full-history `CTL` is
`P1EP-522d...`, while the P2 window uses `P1EP-48fa...`. The POC therefore
enforces:

```text
P1_FULL_EPISODE_IDS_EQUAL_P2_2015_WINDOW_EPISODE_IDS = NO
IMPLICIT_EPISODE_ID_CROSSWALK = PROHIBITED
P2_PROVIDER_BINDING_FACTS_REKEYED_TO_FULL_P1 = NO
```

Every proposed binding names the exact full-P1 episode ID. Existing P2 facts
and frozen SEC documents may corroborate a decision, but they are never
silently renamed into a different episode authority. A binding may cover a
strict subinterval of an episode when that is all the retained evidence proves;
the BBBY sample deliberately demonstrates this bounded behavior.

## Deterministic test matrix

| Case | Episode / ticker | Result | CIK | Date-safe decision |
|---|---|---|---|---|
| Unchanged ticker and issuer | `P1EP-d8a26f...` / AAPL | `PASS_CORROBORATED` | `0000320193` | P1 provenance, Quantiacs CIK, and accession-bound 2009/2021 SEC filings agree; ticker is not sole authority. |
| Genuine ticker rename | `P1EP-522dbc...` / CTL→LUMN | `PASS_EXACT` | `0000018926` | SEC filing fixes the same-registrant rename at 2020-09-18; P2 binding corroborates. |
| Ticker reuse | `P1EP-7ef556...` / BBBY | `PASS_CORROBORATED` | `0000886158` | Accepted NAS:BBBY evidence covers 2015-01-02 through 2017-07-26 and rejects unrelated NYS:BBBY CIK `0001130713`; pre-2015 is not claimed. |
| Merger/succession | `P1EP-4e4d03...` / DRE | `PASS_EXACT` | `0000783280` | Frozen 8-K establishes the 2022-10-03 merger boundary; PLD is not substituted. |
| Current-symbol backfill | `P1EP-82fdce...` / old DD | `AMBIGUOUS_FAIL_CLOSED` | — | Historical NYS:DD lacks CIK; current NYS:DD~1 CIK `0001666700` belongs to the post-2019 security. |
| Exit/re-entry | `P1EP-3d55f0...` / new DD | `PASS_EXACT` | `0001666700` | Frozen SEC corporate-action evidence and NYS:DD~1 agree from the 2019 episode boundary; old DD remains separate. |
| Missing historical provider CIK | `P1EP-036bcd...` / FB→META | `PASS_CORROBORATED` | `0001326801` | P1 rename fact, issuer-filed unchanged CUSIP, SimFin ISIN, and shared P2 security identity compose the relation; current META lookup is not sole authority. |
| Missing historical CIK | `P1EP-7a59c7...` / old CEG | `MISSING_AUTHORITY` | — | Historical NYS:CEG lacks CIK; current NAS:CEG CIK `0001868275` belongs to a distinct 2022 re-entry episode and is not backfilled. |

The matrix contains no `NO_SEC_FILER` sample; the count is explicitly zero
rather than inferred. The two unresolved outcomes remain first-class and are
not coerced into a mapping.

## Thin contract decision

The POC designs, but does not implement, `EpisodeSecCikBindingV1`. Its complete
field inventory is:

```text
episode_id
cik
valid_from
valid_to
binding_classification
evidence_source_identities
binding_id
```

`binding_id` is SHA-256 over deterministic compact UTF-8 JSON of the six
non-ID fields, with lexicographically sorted object keys and preserved evidence
list order. Six sample bindings recomputed exactly. No broader entity, ticker,
or corporate-lineage model was introduced.

```text
EPISODE_SEC_CIK_BINDING_CONTRACT_IMPLEMENTED = NO
AQ_SECURITY_MASTER = NO
AQ_TICKER_RESOLVER = NO
AQ_CORPORATE_LINEAGE_DATABASE = NO
AQ_SEC_HTTP_CLIENT = NO
AQ_SEC_CRAWLER = NO
AQ_GENERIC_IDENTITY_ENGINE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Inputs and replay

The POC reused the full P1 episode file, accepted P1 ticker-identity events,
P2 episode map and provider authority, frozen Quantiacs metadata, bounded SimFin
identity metadata, frozen SEC decision ledgers, and the accession-bound P5 SEC
source identity report. The private output validates all JSON, reconciles
`6 + 1 + 0 + 1 = 8`, and recomputes all six binding IDs.

```text
PRIVATE_BINDINGS = D:/AQ_DATA/P5/episode-to-sec-cik-binding-poc-001/binding_samples.json
PRIVATE_BINDINGS_SHA256 = 283260cc054577678815a124ff235f687e2fbe7d2d3f045ae9d5f0ac0546d971
PRIVATE_REPORT = D:/AQ_DATA/P5/episode-to-sec-cik-binding-poc-001/poc_summary.json
PRIVATE_REPORT_SHA256 = aa4eb177174fb42419e2e407458baf4aab1f6b7e3413347ea364b23316380945
```

## Non-actions and next step

```text
P2_V2_SEALED_OOS_ACCESSED = NO
P5_FACTOR_CREATED = NO
P5_BACKTEST = NO
P5_HISTORICAL_DATASET_BUILT = NO
```

The partial result is tractable because the thin contract represents both
bounded admission and explicit fail-closed gaps. Historical dataset design may
now specify coverage/accounting rules around this contract; it may not fill
old DD or old CEG from current symbols and may not start a scaled build.
