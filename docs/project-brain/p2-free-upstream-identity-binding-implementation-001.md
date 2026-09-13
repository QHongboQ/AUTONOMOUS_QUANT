# P2 Free Upstream Identity Binding Implementation 001

Status: HISTORICAL FIRST IMPLEMENTATION — SUPERSEDED BY MINIMIZATION CLEANUP 001

Base main: `d550ad55c287e81083ddd92adb5446c2a8fac033`

## Ownership preamble

```text
CAPABILITY = FREE_UPSTREAM_PROVIDER_IDENTITY_BINDING
UPSTREAM_OWNER = OPENBB_CORE; QUANTIACS; SIMFIN; OPENFIGI; EDGARTOOLS; DUCKDB; PANDERA; EXCHANGE_CALENDARS
OWNERSHIP_MODE = UPSTREAM_WHOLE_AND_UPSTREAM_LEAF_WITH_AQ_POLICY_BOUNDARY
UPSTREAM_ALREADY_DEPLOYED = YES
AQ_IMPLEMENTATION_ALLOWED = YES
AQ_ALLOWED_SCOPE = ADAPTER; CONTRACT; POLICY; DOMAIN_FACTS
CUSTOM_ENGINE_REQUIRED = NO
```

OpenBB Core owns provider compatibility and the EquityHistorical Standard
Model. Quantiacs and SimFin own their native transport/access surfaces.
OpenFIGI supplies supporting identifier evidence only. edgartools owns SEC
retrieval and parsing. DuckDB owns generic relational composition. Pandera
owns table-boundary validation, `exchange_calendars` owns XNYS sessions, DVC
owns future snapshots, and Qlib remains the future research consumer.

AQ owns only PIT membership and InstrumentEpisode facts, source precedence,
fail-closed acceptance policy, terminal-gap policy, and exceptional
declarative authority facts. No AQ generic engine was required or created.

## Delete-first inventory

The production inventory at the task base found no existing AQ provider
registry, provider router, generic provider normalizer, provider/security
binding engine, price coverage engine, generic identity lookup, SEC
retrieval/parser, or generic relational engine. Consequently there was no
equivalent competing implementation that could safely be retired.

| Existing capability | Classification | Result |
|---|---|---|
| PIT membership and InstrumentEpisode domain | `KEEP_PROJECT_POLICY` / `KEEP_DOMAIN_FACT` | retained |
| accepted reconciliation facts | `KEEP_DOMAIN_FACT` | retained unchanged |
| Pandera PIT boundary | `REPLACE_WITH_UPSTREAM` already complete | reused |
| XNYS calendar adapter | `REPLACE_WITH_UPSTREAM` already complete | retained unchanged |
| DVC snapshot and Qlib handoff leaves | `RETIRE_NOT_ACTIVE_IN_P2` for this execution | not invoked or changed |
| generic provider/identity/SEC/relational machinery | no pre-existing implementation | no duplicate to delete |

The final architecture therefore contains one thin boundary, not two
competing implementations.

## Deterministic production LOC measurement

Counting rule: enumerate every non-test `*.py` file in the repository; exclude
any path component named `tests`, filenames beginning `test_`, and `.venv`;
count physical lines whose trimmed value is non-empty and does not begin with
`#`.

```text
BASELINE_CUSTOM_MODULE_COUNT = 28
BASELINE_CUSTOM_LOC = 1547
FINAL_CUSTOM_MODULE_COUNT = 29
FINAL_CUSTOM_LOC = 1686
NET_CUSTOM_LOC_CHANGE = +139
```

The 139-line increase is the bounded project adapter/evidence/policy boundary.
All generic relational work is SQL executed by DuckDB. No equivalent generic
AQ code existed to retire, so the count is reported without claiming a net
repository reduction. The 518-line POC was not copied into production.

## Production implementation

Exactly two OpenBB `Fetcher` integrations exist:

1. `QuantiacsEquityHistoricalFetcher`
2. `SimFinEquityHistoricalFetcher`

They map only provider-specific query/provenance fields, invoke an injected
native upstream loader, and transform rows into OpenBB
`EquityHistoricalData`. They do not implement a provider registry, router,
generic query abstraction, generic normalizer, HTTP layer, retry system, or
cache.

`OpenFigiEvidence` rejects `tts-*` and requires a standard 12-character FIGI.
OpenFIGI evidence is supporting only and cannot independently authorize an
historical PIT episode. `SecEvidence.from_edgartools` accepts an edgartools
`Filing` and retains only CIK, accession, filing/effective dates, content hash,
and decision role; AQ contains no SEC scraper or parser.

Pandera validates the episode, candidate, observation, and session relations.
DuckDB SQL owns the interval join, anti join, unique-candidate query, conflict
query, coverage, missing-session inventory, and final unresolved relation. AQ
supplies the four-state fail-closed policy:

```text
PROVIDER_BINDING_AUTHORIZED
PROVIDER_BINDING_AMBIGUOUS
PROVIDER_BINDING_NOT_AVAILABLE
KNOWN_PROVIDER_GAP_CANDIDATE
```

## Dependency authority

The POC-demonstrated leaf dependencies are pinned exactly:

```text
duckdb==1.5.5
edgartools==5.58.0
exchange-calendars==4.13.2
openbb-core==1.6.13
pandera[pandas]==0.33.1
```

No OpenBB meta-package or provider framework was installed into a project
runtime by this task. Validation reused the isolated private POC environment.

## Acceptance evidence

Fifteen synthetic focused tests pass:

- OpenBB Standard Model and both provider transforms;
- DuckDB interval join, anti join, duplicate query, conflict query, unique
  candidate, coverage, and all four distinct output states;
- OpenFIGI and edgartools evidence boundaries;
- DD fails closed as ambiguous;
- ANTM/ELV is uniquely authorized;
- STI is a known provider coverage gap rather than identity failure;
- FB/META is not cross-episode backmapped from OpenFIGI alone;
- DISCK remains unavailable and does not substitute WBD observations;
- no ticker-specific production branch or generic AQ engine class exists.

All 13 frozen PIT regressions continue to pass. Ruff passes with no cache.
`compileall` passes using an external bytecode cache. The full discovery run
reported 49 passes, 9 expected real-data skips, and 2 pre-existing structure
test errors because the Windows checkout's CRLF bytes do not match the frozen
raw-file hash (`core.autocrlf=true`). The focused implementation suite and all
13 frozen behavioral regressions pass independently. The facts, frozen hash
authority, and Git line-ending policy were not weakened or changed in this
task.

## Frozen authority and non-actions

```text
FROZEN_CERTIFICATION_DATASET_CONTRACT_V1 = FROZEN
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
SOURCE_PRECEDENCE = QUANTIACS_PRIMARY_SIMFIN_BOUNDED_SECONDARY
NEW_ACCEPTED_MANUAL_EPISODE_FACTS = 0
GENERIC_RUNTIME_TICKER_BRANCHES = 0
CERTIFICATION_DATASET_ROWS_IN_GIT = NO
PROVIDER_PAYLOADS_IN_GIT = NO
PRIVATE_MARKET_DATA_IN_GIT = NO
LICENSED_MARKET_DATA_IN_GIT = NO
DVC_DATA_ARTIFACTS_IN_GIT = NO
CREDENTIALS_IN_GIT = NO
PRIVATE_EVIDENCE_IN_GIT = NO
DATASET_BUILT = NO
MODEL_TRAINING = NO
BACKTEST = NO
SEALED_OOS_DATES_SELECTED = NO
```

No provider was called, no real price data was downloaded, and the 49
unresolved episodes were not bulk-mapped. The accepted reconciliation facts
and frozen certification contract are unchanged.

## Current state

```text
P2_FREE_UPSTREAM_IDENTITY_BINDING_IMPLEMENTATION = COMPLETE
CURRENT_NEXT = P2_FREE_UPSTREAM_IDENTITY_BINDING_IMPLEMENTATION_CLOSEOUT_001
```

The closeout must independently inspect architecture, custom LOC, upstream
ownership, focused regressions, and dependency footprint before any frozen
dataset build resumes.
