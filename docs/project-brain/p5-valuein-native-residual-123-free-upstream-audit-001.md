# P5 Valuein native residual 123 free-upstream audit 001

## Result

The bounded free-upstream audit is complete. It did not reopen the 709
already-admitted Valuein bindings and did not add production code. Twelve of
the 123 residual episodes have sufficient existing free evidence for a future
thin projection; 111 remain explicitly unresolved.

| Residual class | Input | Projectable | Still unresolved |
|---|---:|---:|---:|
| ticker boundary difference | 41 | 9 | 32 |
| no Valuein coverage | 79 | 2 | 77 |
| Valuein conflict | 2 | 0 | 2 |
| Valuein partial agreement | 1 | 1 | 0 |
| **total** | **123** | **12** | **111** |

The complete universe accounting after the audit is therefore 721 potentially
projectable episodes and 111 unresolved episodes. This is evidence only: no
new `EpisodeSecCikBindingV1` row was admitted.

## Valuein boundary evidence

Nine ticker-boundary cases are equivalent under the existing half-open P1
episode semantics because the Valuein security interval ends on a weekend and
there is no weekday before the P1 terminal boundary:

```text
ACS AYE BDK HAR NSM PCL RTN TSS XTO
```

Each case has one exact-symbol security candidate, one CIK, and one containing
SP500 membership row. The other 32 boundary cases contain a weekday/session
gap, a late security start, or otherwise insufficient identity evidence and
remain fail-closed. No automatic stitching was implemented and no ticker name
was hard-coded into production logic.

The audit found no additional case satisfying the stricter adjacent-rename
test of exact CIK, non-overlapping intervals, consistent stable identifiers,
an accepted P1 identity event, and no conflicting owner:

```text
VALUEIN_NATIVE_RENAME_CORROBORATED_COUNT = 0
```

## Partial and conflict cases

The single partial case, BLK, is projectable as two bounded subintervals. The
first native security row ends exactly when the second begins, and the
Valuein SP500 membership row explicitly identifies the second row's CIK as
`successor_cik`. This is an upstream-provided relation, not an AQ successor
guess. Production admission remains deferred.

The DELL and SUN conflicts remain fail-closed. Each has overlapping Valuein
security owners with different CIKs, and the frozen free evidence contains no
higher-authority relation that uniquely resolves the overlap. No majority
vote was used.

## SEC and EdgarTools bounded audit

The audit reused only frozen SEC evidence and the existing accepted binding
ledger. It issued no new SEC request. Frozen SEC material touched 25 residual
tickers, but only two accepted SEC-backed bindings cover their complete
current P1 episode:

```text
CTL -> CIK 0000018926
FB  -> CIK 0001326801
```

The existing BBBY binding starts on 2015-01-02, while its residual P1 episode
starts on 2010-01-04. It is therefore correctly classified as insufficient
for the complete episode rather than silently backfilled.

## Quant-Lodge bounded role

The public `Quant-Lodge/ticker-reference-data` repository was pinned at:

```text
COMMIT = 207d58227bf8a2c4d95066ce654bc8bdb056caa3
FILE = data/ticker_changes.json
SHA256 = c1491370a97a8637765d6dad77fa624c573500109a263a88fe3190ac03fb68c3
BYTES = 1439270
```

It matched 13 residual episodes using only non-null CIK and `old_ticker`
records. Its file does not provide effective-date intervals, so its role is
corroboration only and it independently projected zero episodes. Moving
`main` was not consumed as authority, `flat_file_only` rows were excluded,
and no name match was used.

## Final classifications

| Classification | Count |
|---|---:|
| `FREE_UPSTREAM_PROJECTABLE` | 10 |
| `SEC_EDGAR_CORROBORATED` | 2 |
| `INSUFFICIENT_EVIDENCE` | 33 |
| `NO_FREE_UPSTREAM_COVERAGE` | 76 |
| `CONFLICT_REMAINS_FAIL_CLOSED` | 2 |
| **total** | **123** |

The ten generic free-upstream cases are the nine session-equivalent boundary
cases plus BLK's explicit native successor chain. The SEC total is CTL and FB.

## Reproducibility and ownership

The private audit was replayed twice from frozen inputs and produced the same
checksum ledger hash:

```text
PRIVATE_EVIDENCE_ROOT = D:\AQ_DATA\P5\valuein-native-residual-123-free-upstream-audit-001
CHECKSUMS_SHA256 = 508d560b61915726de49beef36ca4d430eaf478a2da44e93c7687e4abf604d45
OFFLINE_REPLAY = PASS
OUTPUT_HASH_MATCH = YES
```

No paid provider, security master, generic identity engine, manual identity
rule, dataset build, factor, model training, prediction, or backtest was added.
P2 V2 sealed OOS was not accessed.

```text
PAID_DATA_DEPENDENCY_COUNT = 0
AQ_MANUAL_IDENTITY_RULE_COUNT = 0
AQ_SECURITY_MASTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
PRODUCTION_LOC_ADDED = 0
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
```

Because 111 episodes remain without complete free date-valid authority, this
is a meaningful residual, not a thin-projection implementation gate and not a
final small-case adjudication queue. Paid-provider routes are not reopened.

```text
CURRENT_DEVELOPMENT_NEXT = P5_RESIDUAL_IDENTITY_EXPLICIT_UNRESOLVED_CLOSEOUT_001
```
