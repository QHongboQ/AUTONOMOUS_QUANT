# P6 News V1 OpenCorporates/Wikidata Upstream Substitution POC 001

Date: 2026-09-25

## Merge baseline

PR #97 passed its exact documentation-only gate and was squash-merged at
`983c8abb0291b7ea727c14697785d17d92164b64`. This POC starts from that commit
and reuses its deterministic 500-string recovered GKG population unchanged.

## OpenCorporates access and semantic audit

The current official [OpenCorporates API documentation](https://api.opencorporates.com/documentation/API-Reference)
states that an API token is mandatory. The default allowance is 50 requests per
day and 200 per month, which is insufficient for a 500-input same-run POC. The
[Reconciliation API](https://api.opencorporates.com/documentation/Open-Refine-Reconciliation-API)
also requires a token. Open-data access carries Open Database Licence
attribution/share-alike obligations; paid accounts remove those share-alike
restrictions. Compatibility of this private project use with a particular
account plan is therefore not proven without an authorized account.

No OpenCorporates token was present in process, user, or machine environment
variables or the approved private `.env` locations. The task forbids automatic
registration and purchasing, so no OpenCorporates request was sent and no
website HTML was scraped.

The static semantic audit nevertheless passed. Native company search is
case-insensitive, can optionally invoke OpenCorporates name normalization,
searches current and previous names, and company records expose previous and
alternative names with optional dates plus typed external identifiers. The
public API reference documents the generic identifier-system schema but does
not establish the specific `us_sec_cik` system code or its coverage. This is
the right upstream capability class, but the CIK bridge and date validity
cannot be measured without authorized access.

```text
OPENCORPORATES_ACCESS_STATUS = BLOCKED_CREDENTIAL_REQUIRED
OPENCORPORATES_LICENSE_STATUS = ODBL_SHARE_ALIKE_OPEN_DATA_OR_PAID_NON_SHARE_ALIKE; PRIVATE_PLAN_COMPATIBILITY_UNPROVEN
OPENCORPORATES_RECONCILIATION_STATUS = BLOCKED_CREDENTIAL_REQUIRED_STATIC_SEMANTICS_PASS
OPENCORPORATES_INPUT_COUNT = 500_NOT_SENT
OPENCORPORATES_RESOLVED_ENTITY_COUNT = 0_NOT_MEASURED
OPENCORPORATES_US_SEC_CIK_COUNT = 0_NOT_MEASURED
OPENCORPORATES_HISTORICALLY_VALID_NAME_COUNT = 0_NOT_MEASURED
OPENCORPORATES_MULTI_CIK_CONFLICT_COUNT = 0_NOT_MEASURED
OPENCORPORATES_NO_CIK_COUNT = 0_NOT_MEASURED
```

## Wikidata direct bounded POC

The same 500 raw organization strings were sent without AQ preprocessing to
Wikidata's public `wbsearchentities` Action API. The run followed Wikidata's
published access guidance: an identifying User-Agent, sequential requests,
`maxlag`, bounded retries, no dump, and batched entity detail reads of at most
50 items. Wikidata data is CC0.

| Native result | Input count |
|---|---:|
| exactly one item | 80 |
| multiple items | 208 |
| no match | 212 |
| runtime error | 0 |

Four of the 80 unique items contained property `P5531` (Central Index Key):
AbbVie, Berkshire Hathaway, Biogen, and Broadridge Financial Solutions. All
four CIKs exist in the frozen official SEC Submissions snapshot and none
conflicted. The corresponding native Wikidata match was a label or alias, but
none supplied a date-valid name statement covering the GKG safe date. A label
or alias without temporal qualifiers is not historical alias authority.
Consequently the four candidates remain non-admissible and no episode binding
was manufactured.

```text
WIKIDATA_UNIQUE_ITEM_COUNT = 80
WIKIDATA_P5531_CIK_COUNT = 4
WIKIDATA_MULTI_ITEM_COUNT = 208
WIKIDATA_NO_MATCH_COUNT = 212
WIKIDATA_RUNTIME_ERROR_COUNT = 0
SEC_CIK_VALIDATION_PASS_COUNT = 4
SEC_CIK_CONFLICT_COUNT = 0
WIKIDATA_HISTORICAL_ALIAS_AUTHORITY = NO
```

## OpenTapioca audit

[`opentapioca/opentapioca`](https://github.com/opentapioca/opentapioca) was
frozen privately at source commit
`977a4f0409f06b90b9fc34645147ab5d8f460ef1`. Its latest release tag is
`v0.1.2` at `48402c275c684c0aea94117e16a2699022b3f39c`; package metadata reports
version `0.1.2`. The repository `LICENSE` and current README specify
Apache-2.0, although the old `setup.py` metadata still says MIT; this metadata
inconsistency is recorded rather than silently resolved.

The project's public live endpoint has no A or AAAA DNS record from the task
environment. A local production-equivalent run requires its pretrained model
and Solr/Wikidata index; downloading or building that broad index is outside
this bounded POC. OpenTapioca therefore remains a blocked candidate-generation
challenger. Its score cannot be automatic identity authority in any case.

```text
OPENTAPIOCA_VERSION = 0.1.2_PACKAGE_METADATA
OPENTAPIOCA_SOURCE_SHA = 977a4f0409f06b90b9fc34645147ab5d8f460ef1
OPENTAPIOCA_LICENSE = APACHE_2_0_REPOSITORY_AUTHORITY_WITH_STALE_MIT_SETUP_METADATA
OPENTAPIOCA_STATUS = BLOCKED_RUNTIME_CANDIDATE_GENERATION_ONLY
```

## Selection and blocker

No audited stack met the task's mandatory operational gate of at least one
historically valid AQ episode:

- OpenCorporates is the semantically strongest whole-path candidate, but token,
  plan, and rate-limit authority are unavailable.
- Wikidata supplies four exact CIK properties after unique native search, but
  does not supply date-valid name authority for those matches.
- OpenTapioca is unavailable as a live service and would remain candidate
  generation only.
- SEC EDGAR MCP and Datamule from PR #97 remain useful diagnostic evidence but
  are not active production owners because their composition admitted zero
  episodes.

The prior custom resolver is not resumed. The remaining gap is upstream access
to a whole-path entity record with both CIK and historical name dates, not a
reason to create an AQ normalizer or fuzzy matcher.

```text
FINAL_ADMITTED_AQ_EPISODE_COUNT = 0
SELECTED_NEWS_ENTITY_UPSTREAM_STACK = NONE_OPERATIONALLY_SUFFICIENT
SECEDGAR_ACTIVE_ROLE_AFTER_POC = DIAGNOSTIC_CANDIDATE_GENERATION_ONLY_NOT_ACTIVE
DATAMULE_ACTIVE_ROLE_AFTER_POC = DIAGNOSTIC_EXACT_ALIAS_RELATION_ONLY_NOT_ACTIVE
AQ_ENTITY_RESOLUTION_ENGINE_REQUIRED = NO
AQ_NAME_NORMALIZATION_ENGINE_CREATED = NO
AQ_FUZZY_MATCHER_CREATED = NO
AQ_ALIAS_DATABASE_BUILDER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
SKILL_ENTITY_IDENTITY_AUTHORITY = NO
NEWS_FEATURE_FAMILY_SELECTED = NO
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
```

Private evidence is retained at
`D:/AQ_DATA/P6/news-v1-opencorporates-wikidata-upstream-substitution-poc-001`.
Its checksum-manifest SHA-256 is
`cea565c735fe3a2013f851a83b6615858b642496db7f7e5bdbfeac663aae90c5`.

```text
CURRENT_DEVELOPMENT_NEXT = BLOCKED_OPENCORPORATES_CREDENTIAL_US_SEC_CIK_COVERAGE_AND_HISTORICAL_NAME_DATE_AUTHORITY
FINAL_CLASSIFICATION = BLOCKED_OPENCORPORATES_CREDENTIAL_US_SEC_CIK_COVERAGE_AND_HISTORICAL_NAME_DATE_AUTHORITY
```
