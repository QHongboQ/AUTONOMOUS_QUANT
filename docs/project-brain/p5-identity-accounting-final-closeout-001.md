# P5 identity accounting final closeout 001

## Result

P5 historical identity accounting is complete without manufacturing CIKs for
episodes that lack authoritative free evidence:

```text
721 authoritative bound episodes
+ 111 explicit exclusion-ledger episodes
= 832 authoritative P1 episodes
```

Accounting completion means every P1 episode has exactly one disposition. It
does not mean every episode has a CIK and it does not remove unbound episodes
from the historical universe.

## Residual audit merge

The documentation-only residual audit was revalidated and squash-merged
through PR #61:

```text
SOURCE_HEAD = c69f5ee325d79891469ca78c419e5d3feb6a94ad
PRE_MERGE_MAIN = 3d56f67fec40927c571e099a2cfdaf4ac7e22605
MERGED_AT_UTC = 2026-09-19T18:29:07Z
MERGE_SHA = 5fb3a48b884753e155ff10b5711b0783e0d9754f
```

## Final binding authority

The existing 709 Valuein projection records were replayed byte-for-byte with
the same output hash. The closeout adds only the 12 episodes proven by the
merged audit:

| Source | Bound episodes | Binding records |
|---|---:|---:|
| preserved Valuein native projection | 709 | 709 |
| zero-XNYS-session-gap boundaries | 9 | 9 |
| explicit Valuein `successor_cik` chain | 1 | 2 |
| existing accepted SEC evidence | 2 | 2 |
| **final** | **721** | **722** |

The session-boundary rule is generic. It admits a provider/P1 boundary
difference only when the supplied authoritative XNYS session set contains no
session outside the Valuein security interval. A focused negative test proves
that a real weekday/XNYS-session gap rejects.

BLK is represented by two adjacent, non-overlapping binding records. The only
continuity input is Valuein's native SP500 membership `successor_cik`; no AQ
corporate-lineage inference was added.

CTL and FB retain their existing accepted binding identities and provenance
unchanged:

```text
CTL -> CIK 0000018926
FB  -> CIK 0001326801
```

Final binding-record classifications are:

```text
PASS_EXACT = 2
PASS_CORROBORATED = 720
```

## Exclusion authority

`EpisodeSecCikExclusionV1` is the thin, immutable no-authority decision
contract. It contains only `episode_id`, classification, reason, evidence
identities, and deterministic `decision_id`; it has no nullable or placeholder
CIK.

The accepted ledger contains exactly:

| Classification | Episodes |
|---|---:|
| `INSUFFICIENT_EVIDENCE` | 33 |
| `NO_FREE_UPSTREAM_COVERAGE` | 76 |
| `CONFLICT_REMAINS_FAIL_CLOSED` | 2 |
| **total** | **111** |

DELL and SUN remain explicitly fail-closed. No current owner, newest owner,
longest interval, majority vote, or ticker/name/price heuristic was used.

## Missingness and universe policy

Exclusion is limited to fundamental identity availability. Every excluded
episode remains an authoritative P1 universe episode and remains in the
episode/session denominator. Fundamental values remain structurally missing.

```text
UNBOUND_EPISODE_REMOVED_FROM_UNIVERSE = NO
UNBOUND_EPISODE_REMOVED_FROM_DENOMINATOR = NO
UNBOUND_EPISODE_PREDECESSOR_CIK_SUBSTITUTION = NO
UNBOUND_EPISODE_SUCCESSOR_CIK_SUBSTITUTION = NO
UNBOUND_EPISODE_CURRENT_CIK_BACKFILL = NO
```

## Full accounting and verification

```text
TOTAL_P1_EPISODES = 832
FINAL_BOUND_EPISODE_COUNT = 721
FINAL_EXCLUSION_EPISODE_COUNT = 111
UNACCOUNTED_EPISODE_COUNT = 0
DUPLICATE_ACCOUNTING_COUNT = 0
EPISODE_IN_BOTH_BINDING_AND_EXCLUSION_COUNT = 0
P5_FULL_UNIVERSE_IDENTITY_ACCOUNTING_COMPLETE = YES
```

Focused tests passed 49/49: 18 Valuein adapter tests, 25 identity
binding/exclusion/ledger tests, and six P1 core contract tests. Ruff and
`git diff --check` passed. Two complete materialization replays produced the
same private checksum ledger hash.

```text
PRIVATE_EVIDENCE_ROOT = D:\AQ_DATA\P5\identity-accounting-final-closeout-001
CHECKSUMS_SHA256 = 32cba10a8f50c2a2a7dc1c9480547272b6f9ef501c49ef4c2a644c711f53dcd5
OFFLINE_REPLAY = PASS
OUTPUT_HASH_MATCH = YES
```

No security master, identity engine, provider framework, generic adapter
framework, manual identity rule, historical dataset build, factor, training,
prediction, or backtest was introduced. P2 V2 sealed OOS was not accessed.

```text
AQ_MANUAL_IDENTITY_RULE_COUNT = 0
AQ_SECURITY_MASTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

Historical identity search is closed. The next development gate is accession
authority and dataset-build readiness, not another provider search.

```text
P5_FULL_BUILD_GATE = IDENTITY_ACCOUNTING_COMPLETE_READY_FOR_ACCESSION_CENSUS
CURRENT_DEVELOPMENT_NEXT = P5_FULL_UNIVERSE_ACCESSION_CENSUS_AND_DATASET_BUILD_GATE_001
```
