# P5 Valuein native PIT whole-path revalidation 001

## Decision

The revalidation passes. Valuein's native point-in-time model materially
replaces the rejected exact-interval-equality interpretation:

```text
P1 InstrumentEpisodeV1
  -> security(symbol, valid_from, valid_to, entity_id)
  -> entity(cik)
  -> index_membership(cik, effective_date, removal_date)
  -> references(security_id, cik, FIGI fields)
  -> EpisodeSecCikBindingV1 projection
```

The Valuein security interval may contain the P1 membership episode. It does
not need to equal it. P1 remains the membership authority; Valuein membership
is an independent upstream oracle and conflict check. No production bindings
were written in this task.

## Frozen upstream evidence

The replay used the previously authenticated Valuein `sp500` plan snapshot
`snapshot_20260918` with SDK 5.2.0. The SDK identifies this plan as the free
Benchmark/S&P 500 tier. The frozen authenticated manifest evidence records
current and former S&P 500 coverage; no credential material is retained.

| Native table | Rows | Relevant historical range |
|---|---:|---|
| `entity` | 968 | current and former filers |
| `security` | 1,263 | 1993-08-13 onward |
| `index_membership` | 25,220 | 1996-01-02 onward |
| `references` | 1,263 | same security SCD2 projection |

The audit verified the native joins `security.entity_id = entity.cik`,
`index_membership.cik = entity.cik`, and the one-for-one `references` security
projection. The replay was offline against immutable cached Parquet bytes;
network requests were zero.

## Full 832-episode replay

| Classification | Episodes |
|---|---:|
| `VALUEIN_NATIVE_EXACT_AGREEMENT` | 1 |
| `VALUEIN_NATIVE_CONTAINING_AGREEMENT` | 708 |
| `VALUEIN_NATIVE_PARTIAL_AGREEMENT` | 1 |
| `VALUEIN_NATIVE_MEMBERSHIP_BOUNDARY_DIFFERENCE` | 0 |
| `VALUEIN_NATIVE_TICKER_BOUNDARY_DIFFERENCE` | 41 |
| `VALUEIN_NATIVE_AMBIGUOUS` | 0 |
| `VALUEIN_NATIVE_CONFLICT` | 2 |
| `VALUEIN_NATIVE_NO_COVERAGE` | 79 |
| **Total** | **832** |

The two conflicts are real overlapping alternative identities and remain
fail-closed. No current-ticker or latest-owner backfill was used.

## Projectable identity boundary

An episode is projectable only when one security and one CIK own the exact
ticker throughout the complete P1 interval, the security interval contains
the P1 interval, Valuein membership does not contradict it, and no overlapping
alternative identity exists. Under that rule:

```text
VALUEIN_NATIVE_PROJECTABLE_BINDING_COUNT = 709
PRIOR_EXACT_ONLY_ADMISSION_COUNT = 1
PRIOR_831_RESIDUAL_RESOLVED_COUNT = 708
VALUEIN_NATIVE_UNRESOLVED_COUNT = 123
```

The native inner join corrected a defect in the earlier diagnostic: KMI and
the 2024 DELL episode had been paired with `RUSSELL1000`/`RUSSELL3000`
`fund_holdings` rows rather than `index_membership.index_name = 'SP500'`.
They are therefore not projectable through the requested Valuein S&P 500
whole path. The historical exact-only FRC admission is unaffected.

## Control cases

All required controls were executed. Seven of twelve episode-level controls
are directly projectable: AAPL, DRE, FRC, new DD, LUMN, new CEG, and META.
Five remain explicitly unresolved: historical BBBY, old CEG, CTL, old DD, and
FB. Rename successors do not backfill predecessors. Old and new DD resolve
differently by date, demonstrating that ticker reuse is fail-closed.

## Ownership result

```text
CAN_VALUEIN_OWN_HISTORICAL_SECURITY_IDENTITY = PARTIAL
CAN_VALUEIN_OWN_SP500_MEMBERSHIP = ORACLE_ONLY
CAN_VALUEIN_REPLACE_AQ_IDENTITY_INFERENCE = PARTIAL
VALUEIN_EXISTING_EXACT_ONLY_ADAPTER_ROLE = REWRITE_THIN_PROJECTION_ONLY
P1_MEMBERSHIP_AUTHORITY = PRESERVED
VALUEIN_FUNDAMENTALS_PRODUCTION_ROLE = NONE
EDGARTOOLS_EXACT_FUNDAMENTALS_AUTHORITY = YES
AQ_MANUAL_IDENTITY_RULE_COUNT = 0
AQ_SECURITY_MASTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
PRODUCTION_LOC_ADDED = 0
```

The next implementation must retire the exact-only behavior and project only
the 709 upstream-native, date-contained identities through the existing
`EpisodeSecCikBindingV1` contract. It must not add a security master, identity
inference engine, provider registry, or manual exception table.

## Evidence

Private evidence root:

```text
D:\AQ_DATA\P5\valuein-native-pit-whole-path-revalidation-001
```

`checksums.json` SHA-256:

```text
1ac91680183225ce04711b72e4861c8e3cb05aa4ee604ad338b7289e325a87d4
```

No historical dataset was built, no factor/model/backtest was run, and P2 V2
sealed OOS was not accessed.

```text
CURRENT_DEVELOPMENT_NEXT = P5_VALUEIN_NATIVE_IDENTITY_THIN_PROJECTION_AND_LEGACY_RETIREMENT_001
```
