# P2 Free Upstream Identity Authority Implementation 001

Status: COMPLETE

Base main: `80ff39808b57572ec6f549a77d9ac396d0ddb498`

## Ownership and scope

```text
CAPABILITY = P2_PROVIDER_BINDING_AUTHORITY
TREE_OWNER = MARKET_DATA_P2_BINDING
OWNERSHIP_MODE = AQ_OWNED_BOUNDED_DOMAIN_FACTS
P2_PROVIDER_BINDING_AUTHORITY_FACTS = 12
P1_UNIVERSE_AUTHORITY_UNCHANGED = YES
CUSTOM_GENERIC_ENGINE_REQUIRED = NO
```

The market-data `p2-binding` leaf now owns exactly 12 accepted declarative
provider-binding facts reconstructed from the approved private authority
closeout. They do not migrate, copy, or change P1 membership or
InstrumentEpisode authority. The P1 accepted reconciliation fact artifact is
unchanged.

## Frozen provenance

```text
AUTHORITY_CLOSEOUT_REPORT_SHA256 = 710361d36c000310aa9771bb6e6ba4b13b0f7c7d4c3a7b843ed62239a8c2cad5
PROPOSED_AUTHORITY_FACTS_SHA256 = aaa2693823abdba72c0d4b564214217cc49bd28e6c0eb3ac1a659f3b4bef81c2
ACCEPTED_PROVIDER_BINDING_FACTS_SHA256 = 3cd9b13a1424609120a4e069ac2cf9f9b9aa61e2df919aa48cf51eeac616bc69
AUTHORITY_SCOPE = PROVIDER_BINDING_ONLY
```

The production loader freezes the accepted artifact by exact SHA-256 and
fails closed on a changed hash, schema, fact count, duplicate episode/provider
binding, invalid interval or evidence hash, unsupported scope, or any enabled
unsafe inference/substitution field.

## Runtime semantics

Python validates only the narrow authority artifact and public relation
boundaries. DuckDB owns the exact episode/provider/provider-asset/date match,
uniqueness, conflicts, interval joins, coverage joins, and missing-session
inventory. No provider registry, router, ticker resolver, identity engine,
security master, or ticker-specific branch was added.

Authority changes identity eligibility only. It never supplies observations
or changes coverage. The accepted ARNC/HWM relation therefore remains:

```text
REQUIRED_SESSIONS = 1323
OBSERVED_SESSIONS = 868
MISSING_SESSIONS = 455
COVERAGE_STATE = PARTIAL_PROVIDER_COVERAGE
```

## Verification and non-actions

Focused tests cover exact accepted assets, same-ticker wrong assets,
out-of-interval episodes, duplicate facts, altered authority bytes, the exact
12-fact count, coverage orthogonality, and the ARNC/HWM 455-session gap. The
existing DD, ANTM/ELV, STI, FB/META, DISCK, zero-session, partial-session,
out-of-episode, cardinality, and coverage regressions remain in the same test
suite.

```text
P1_UNIVERSE_AUTHORITY_CHANGED = NO
FROZEN_CERTIFICATION_DATASET_CONTRACT_CHANGED = NO
DATASET_BUILT = NO
MODEL_TRAINING = NO
BACKTEST = NO
NEW_PRICE_PROVIDER_ADDED = NO
PR_CREATED = NO
MERGED = NO
CURRENT_NEXT = P2_FREE_UPSTREAM_IDENTITY_AUTHORITY_IMPLEMENTATION_CLOSEOUT_001
```
