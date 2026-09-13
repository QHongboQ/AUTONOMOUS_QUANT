# P2 Free Upstream Identity Binding Minimization Cleanup 001

Status: HISTORICAL MINIMIZATION CLEANUP — SUPERSEDED BY FAIL-CLOSED HARDENING 001

```text
BASE_MAIN = d550ad55c287e81083ddd92adb5446c2a8fac033
PRIOR_HEAD = 569c1641cace9a07f60edf50bd2e8e47400af494
TREE_OWNERSHIP = CORRECT
PROVIDER_BINDING_LOCATION = 10-data-system/market-data/p2-binding
UNIVERSE_OWNS_PROVIDER_BINDING = NO
MARKET_DATA_OWNS_PROVIDER_BINDING = YES
CUSTOM_ENGINE_REQUIRED = NO
```

## Ownership correction

The first implementation placed provider compatibility and binding inside the
S&P 500 PIT universe package. The implementation now lives under the
market-data tree. The universe leaf owns PIT membership, identity, and
InstrumentEpisode facts. The market-data leaf consumes a thin public episode
relation and owns provider observations, compatibility, provenance,
provider-to-episode binding, and price coverage. It neither imports a sibling's
private implementation nor duplicates InstrumentEpisode facts.

Certification acceptance remains an AQ policy boundary. Generic execution is
upstream-owned: OpenBB Core provides the Fetcher API and EquityHistorical
Standard Model; DuckDB executes relations; Pandera validates relation shapes;
edgartools retrieves/parses SEC filings; OpenFIGI is supporting identity
evidence only. Quantiacs and SimFin retain their native transport boundaries.

## Exact call-graph and ownership inventory

Searches covered all non-test production Python and all imports/calls of the
first `aq_pit.provider_binding` implementation. Its only importer was its
focused test. No production caller existed, so moving the boundary and its
tests was safe.

| Production capability | Classification | Cleanup result |
|---|---|---|
| `aq_pit.domain`, accepted facts, research-ready gate | `REQUIRED_AQ_DOMAIN_FACT` / `REQUIRED_AQ_POLICY` | retained |
| FJA membership-source adapter | `REQUIRED_AQ_DOMAIN_FACT` | retained; not a price-provider adapter |
| PIT Pandera boundary | `REPLACED_BY_PANDERA` | retained thin schema leaf |
| XNYS calendar adapter | `NOT_DUPLICATIVE` | retained upstream leaf |
| DatasetSnapshot/DVC export | `NOT_DUPLICATIVE` | retained snapshot contract; not provider routing |
| Qlib dataset handoff | `NOT_DUPLICATIVE` | retained downstream adapter |
| provider routing/registry | no implementation | none created |
| provider normalization | first implementation only | moved into two OpenBB Fetchers |
| provider/security matching and generic temporal composition | first implementation only | DuckDB remains execution owner |
| coverage, conflicts, duplicate and unique-candidate queries | first implementation only | DuckDB SQL remains execution owner |
| SEC retrieval/parsing | no implementation | edgartools remains owner |
| generic identity lookup | no implementation | OpenFIGI remains supporting evidence only |

```text
DUPLICATE_GENERIC_CAPABILITIES = NONE
RETIRED_GENERIC_MODULES = NONE
MOVED_MISOWNED_MODULE = aq_pit/provider_binding.py
```

No working P1 research authority was deleted to reduce LOC.

## Cleaned structure

```text
10-data-system/market-data/p2-binding/
  README.md
  requirements.txt
  aq_market_data_binding/
    __init__.py
    providers.py
    binding.py
    binding.sql
  tests/
    test_binding.py
```

`providers.py` contains exactly two thin Fetchers. They accept only
provider-specific query/provenance fields, invoke the supplied native upstream
surface, map native rows to OpenBB `EquityHistoricalData`, and return an
`AnnotatedResult`. They contain no downloader manager, router, cache, retry,
security resolver, or certification engine.

The sidecar metadata preserves exactly the future reconstruction boundary:

```text
provider
provider_asset_identifier
provider_symbol
adjustment_semantics
source_observation_sha256
```

This avoids forking OpenBB's Standard Model. It does not claim that the final
certification dataset has been built.

`binding.py` retains only the project evidence port, Pandera boundary, and
four-state fail-closed AQ policy. `binding.sql` leaves interval and anti joins,
duplicates, conflicts, uniqueness, coverage, and unresolved inventory in
DuckDB. Identity ambiguity remains distinct from a known zero-observation
provider gap.

## Deterministic minimization metrics

The unchanged rule enumerates all non-test repository `*.py` files, excluding
`tests`, `test_*`, and `.venv`; LOC counts nonblank physical lines whose
trimmed form does not begin with `#`.

```text
ORIGINAL_MAIN_MODULE_COUNT = 28
ORIGINAL_MAIN_LOC = 1547
FIRST_IMPLEMENTATION_MODULE_COUNT = 29
FIRST_IMPLEMENTATION_LOC = 1686
CLEANED_IMPLEMENTATION_MODULE_COUNT = 31
CLEANED_IMPLEMENTATION_LOC = 1727
NET_LOC_VS_BASELINE = +180
```

The cleaned structure adds two physical modules for explicit ownership
separation and 41 lines for the public package boundary plus the five required
provenance fields. Every line above the baseline belongs to the two thin
OpenBB translations, the evidence/policy boundary, or Pandera-to-DuckDB glue.
No replaceable generic duplicate remains. No deletion was manufactured to hit
a numeric target.

## Regression and safety evidence

The 15 synthetic binding tests and all 13 frozen PIT behavioral regressions
pass. Verified behavior includes both OpenBB translations, DuckDB interval and
anti joins, duplicate/conflict/unique-candidate queries, OpenFIGI and
edgartools boundaries, DD fail-closed ambiguity, ANTM/ELV authorization, STI
known coverage gap, FB/META non-backmap, and DISCK non-substitution. Ruff and
package dependency checks pass; compileall passes using an external bytecode
cache.

```text
GENERIC_RUNTIME_TICKER_BRANCHES = 0
NEW_ACCEPTED_MANUAL_EPISODE_FACTS = 0
FROZEN_CERTIFICATION_DATASET_CONTRACT_V1 = FROZEN
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
SOURCE_PRECEDENCE = QUANTIACS_PRIMARY_SIMFIN_BOUNDED_SECONDARY
PROVIDER_PAYLOADS_IN_GIT = NO
PRIVATE_MARKET_DATA_IN_GIT = NO
CREDENTIALS_IN_GIT = NO
DATASET_BUILT = NO
MODEL_TRAINING = NO
BACKTEST = NO
SEALED_OOS_DATES_SELECTED = NO
```

No provider was queried, no data was downloaded, and no dataset/DVC action was
performed.

## Current state

```text
P2_FREE_UPSTREAM_IDENTITY_BINDING_IMPLEMENTATION = COMPLETE
P2_FREE_UPSTREAM_IDENTITY_BINDING_MINIMIZATION_CLEANUP = COMPLETE
CURRENT_NEXT = P2_FREE_UPSTREAM_IDENTITY_BINDING_IMPLEMENTATION_CLOSEOUT_001
```
