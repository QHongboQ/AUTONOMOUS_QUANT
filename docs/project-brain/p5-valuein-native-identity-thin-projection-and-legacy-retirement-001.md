# P5 Valuein native identity thin projection and legacy retirement 001

## Result

The implementation passes. The obsolete exact-interval-only Valuein path was
replaced by one direct, fail-closed projection from native Valuein identity
rows into the existing `EpisodeSecCikBindingV1` contract:

```text
P1 InstrumentEpisodeV1
  + Valuein security
  + Valuein entity / CIK
  + Valuein index_membership(index_name = SP500)
  + Valuein references
  -> EpisodeSecCikBindingV1
```

P1 remains the S&P 500 membership and ticker-episode authority. Valuein owns
partial historical security identity evidence. AQ performs only exact ticker
selection, date containment, conflict rejection, contract projection, and
provenance identity. EdgarTools remains the exact fundamentals authority.

## Revalidation merge

The corrected whole-path revalidation was squash-merged through PR #59:

```text
SOURCE_HEAD = 5a2b81e786a3c450506719912e2f111eb93af099
PRE_MERGE_MAIN = 7c602894f1940ce63bf201fad9ebcc6834fc1f43
MERGED_AT_UTC = 2026-09-19T17:36:49Z
MERGE_SHA = 676a4cd076ff53ab4588986789badc56a6f8457d
```

## Frozen replay

The production projection was replayed offline against the same immutable
Valuein snapshot used by the revalidation. Two consecutive replays produced
identical hashes for every decision artifact.

| Result | Episodes |
|---|---:|
| `PASS_EXACT` | 1 |
| `PASS_CORROBORATED` | 708 |
| admitted bindings | 709 |
| fail-closed unresolved | 123 |
| **total** | **832** |

The 123 unresolved cases remain unchanged: one partial agreement, 41 ticker
boundary differences, two conflicts, and 79 cases without coverage. No
current-ticker backfill, successor substitution, manual mapping, SEC
corroboration, or additional provider was used.

## S&P 500 source gate

Only Valuein `index_membership` records whose `index_name` is exactly `SP500`
can satisfy the membership-evidence precondition. `fund_holdings`, Russell
membership, ETF holdings, and other index rows are excluded.

```text
SP500_MEMBERSHIP_HARD_GATE = PASS
RUSSELL_CONTAMINATION_COUNT = 0
FUND_HOLDINGS_CONTAMINATION_COUNT = 0
```

## Subtraction and ownership

The old `ValueinIdentityDecision`, `IdentityClassification`,
`classify_valuein_identity`, and `admit_exact_valuein_binding` production path
is retired. No parallel exact-only path remains.

The deterministic production LOC rule counts nonblank, non-comment physical
lines in `aq_valuein_adapter/__init__.py`:

```text
OLD_VALUEIN_PRODUCTION_LOC = 205
NEW_VALUEIN_PRODUCTION_LOC = 181
NET_PRODUCTION_LOC_CHANGE = -24
VALUEIN_DUPLICATE_PRODUCTION_PATH_COUNT = 0
AQ_MANUAL_IDENTITY_RULE_COUNT = 0
AQ_SECURITY_MASTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Verification and evidence

The focused Valuein tests passed 14/14, `EpisodeSecCikBindingV1` tests passed
18/18, and the affected P1 contract tests passed 6/6. Ruff and
`git diff --check` passed.

Private evidence root:

```text
D:\AQ_DATA\P5\valuein-native-identity-thin-projection-and-legacy-retirement-001
```

`checksums.json` SHA-256:

```text
b0c3cb1d58fa50838c368c4678bd82e3735d9e977ca1e49483fff97d48f3d239
```

No historical fundamental dataset was built, no factor/model/backtest was
run, and P2 V2 sealed OOS was not accessed.

```text
P5_FULL_UNIVERSE_IDENTITY_ACCOUNTING_COMPLETE = NO
P5_FULL_BUILD_GATE = CLOSED_RESIDUAL_IDENTITY_REQUIRED
CURRENT_DEVELOPMENT_NEXT = P5_VALUEIN_NATIVE_RESIDUAL_123_FREE_UPSTREAM_AUDIT_001
```
