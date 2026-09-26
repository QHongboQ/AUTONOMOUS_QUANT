# P6 News V1 Entity Resolution Upstream Deployment POC 001

Date: 2026-09-25

## Decision

The bounded POC replaces AQ-owned organization-name resolution mechanics with
two upstream leaves while retaining only fail-closed project admission policy:

- [`cyanheads/secedgar-mcp-server`](https://github.com/cyanheads/secedgar-mcp-server)
  `v0.15.1` / `e356eb4db3c5027862e5e78afdd88d05c1867652`
  (`Apache-2.0`) is selected as a **candidate-generation leaf**.
- [`john-friedman/datamule-data`](https://github.com/john-friedman/datamule-data)
  `a68aa57c641db777ffd860a0c8befbe740048c58` (`MIT`) is selected as the
  **historical exact-alias relation owner**.
- SEC Submissions remains source authority. The frozen source hash is
  `702fbcd8b4335bc649e9e4eab3a202f3effc314b43421664bfecb59365767165`.
- The existing `EpisodeSecCikBindingV1` ledger remains the only CIK-to-P1
  episode authority.

No AQ name normalizer, fuzzy matcher, alias database, entity resolver, or
generic identity engine was created.

## Recovered input and bounded population

The POC reused the retained GKG organization evidence whose checksum-manifest
SHA-256 is
`4d5651b76d5e5941cf1f837c579c35c9288cb4ecda0b7b59c0faf4139578816e`.
It did not redownload GKG or fetch article URLs. From the 3,499 exact
`V1ORGANIZATIONS` strings, it retained the earliest occurrence by safe date and
GKG record ID, sorted the raw strings lexicographically, and selected the first
500. Inputs were not rewritten before upstream resolution.

## SEC EDGAR MCP safety gate

The isolated runtime is Node `v24.19.0`, npm `11.17.0`, with exact package
`@cyanheads/secedgar-mcp-server@0.15.1`; its package-lock SHA-256 is
`bdfeaafb883ec92991d1101c53a048fd4c17c2e2c737f6b2e13b65c5ffe23e76`.
The local stdio server started and exposed its native tools, but the live SEC
registry request was rejected by SEC's request-rate threshold. The project's
public hosted MCP endpoint then completed all 500 native
`secedgar_company_search` calls without a runtime error.

Source inspection established that name resolution tries exact, prefix, then
substring matches over current and former names and deduplicates by CIK. The
public result does not expose which match class produced the result. Automatic
AQ admission therefore cannot treat any returned CIK as exact authority. This
is materially important: for example, raw `aaron` returned a unique unrelated
current profile, showing why unique output alone is insufficient.

| Native outcome | Inputs |
|---|---:|
| no match | 459 |
| unique CIK | 34 |
| multiple CIKs | 7 |
| exact-classifiable | 0 |
| non-exact or unknown match class | 41 |
| runtime error | 0 |

## Datamule exact relation

The audited data snapshot is the current repository commit above. Its four
filer metadata/name files have canonical combined identity
`82ab4b7b7ce45108ca0f69324c414c2d2b3c18dc393c5c67f359e5ae21df77d4`.
The native relation files are `listed_filer_names.csv.gz` and
`unlisted_filer_names.csv.gz`, with `name`, `start_date`, `end_date`, and `cik`.
The project documents SEC `submissions.zip` as the generation source. It also
documents a blank end date for current names and a first-submission start date
when no recorded name change exists; it does not document boundary inclusion.

DuckDB performed only raw, case-sensitive exact equality. No case folding,
punctuation rewriting, suffix removal, or other AQ normalization was applied.
The lower-case GKG strings therefore produced zero exact Datamule matches:

| Exact-relation outcome | Inputs |
|---|---:|
| any exact alias row | 0 |
| unique CIK | 0 |
| ambiguous CIK | 0 |
| no match | 500 |

This is a valid fail-closed result, not permission to add AQ normalization.
Current-name rows would remain non-admissible unless an upstream relation proves
historical start. Undocumented interval boundaries use strict interior
`start_date < safe_available_date < end_date`; equality and inverted intervals
fail closed.

## Cross-upstream and episode result

The frozen official SEC snapshot was read only for bounded validation of the 50
candidate CIKs returned by the upstreams; all 50 were present. It was not used
to build a new AQ alias table.

| Cross-upstream classification | Inputs |
|---|---:|
| `AGREE_UNIQUE_CIK` | 0 |
| `SECEDGAR_ONLY` | 34 |
| `DATAMULE_ONLY` | 0 |
| `CONFLICT` | 0 |
| `AMBIGUOUS` | 7 |
| `UNMATCHED` | 459 |

Because the MCP response has no match-class metadata and Datamule supplied no
raw-exact date-valid alias, the 34 unique candidates are
`CURRENT_NAME_HISTORICAL_START_UNPROVEN`; seven multi-CIK results are identity
conflicts. No result reached the existing episode ledger admission gate.

```text
HISTORICALLY_VALID_UNIQUE_CIK_COUNT = 0
VALID_NON_AQ_ENTITY_COUNT = 0
NO_DATE_VALID_AQ_EPISODE_COUNT = 0
IDENTITY_CONFLICT_COUNT = 7
FINAL_ADMITTED_AQ_EPISODE_COUNT = 0
```

Zero admissions are acceptable for this ownership POC: recall is not improved
by inventing project-owned identity mechanics. The selected leaves own native
candidate generation and exact historical relation; AQ owns only the predicate
“one CIK, date-valid alias, no SEC conflict, one existing episode, else reject.”
The bounded predicate is estimated at 26 LOC and is not implemented here.

## Frozen authority

```text
SECEDGAR_STATUS = SELECTED_CANDIDATE_GENERATION_LEAF
DATAMULE_STATUS = SELECTED_HISTORICAL_ALIAS_RELATION_OWNER
SELECTED_ENTITY_RESOLUTION_MECHANICS_OWNER = SECEDGAR_MCP_SERVER_0_15_1_CANDIDATE_GENERATION_ONLY
SELECTED_HISTORICAL_ALIAS_RELATION_OWNER = DATAMULE_DATA_A68AA57_EXACT_RAW_RELATION
AQ_ENTITY_RESOLUTION_ENGINE_REQUIRED = NO
AQ_HISTORICAL_ALIAS_POLICY_LOC_ESTIMATE = 26
AQ_NEWS_ENTITY_RESOLVER_CREATED = NO
AQ_NAME_NORMALIZATION_ENGINE_CREATED = NO
AQ_FUZZY_MATCHER_CREATED = NO
AQ_ALIAS_DATABASE_BUILDER_CREATED = NO
AQ_GENERIC_IDENTITY_ENGINE_CREATED = NO
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

Private POC evidence is retained at
`D:/AQ_DATA/P6/news-v1-entity-resolution-upstream-deployment-poc-001`; its
checksum-manifest SHA-256 is
`b204820eb43f2baabce073fa10d06824ed6ccfd02440d817b320f830f3b830c2`.

## Next

```text
CURRENT_DEVELOPMENT_NEXT = P6_NEWS_V1_ENTITY_BINDING_POLICY_FREEZE_001
FINAL_CLASSIFICATION = PASS_P6_NEWS_V1_ENTITY_RESOLUTION_UPSTREAM_DEPLOYMENT_POC
```
