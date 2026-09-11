# DVC reproducibility operations

DVC `3.67.1` is the pinned CLI owner for pipeline dependencies, outputs,
content cache, invalidation, no-change skips, lock state, and local-cache
restoration. The repository-level `.dvc/`, `.dvcignore`, `dvc.yaml`, and
`dvc.lock` are upstream-required metadata, not a new AQ domain framework.

The current single stage publishes the PIT DatasetSnapshot. DVC does not own
PIT semantics, membership or identity truth, market-data meaning,
certification, model training, or production promotion. No DVC Python API is
imported into AQ code and no cloud remote is configured.

`D:/AQ_DATA/P1/pit` is an explicit `HOST_LOCAL_BINDING` for the authoritative
machine. It remains a literal external dependency so DVC can hash and invalidate
the pinned raw FJA input correctly. The historical unresolved-findings ledger is
archive/reference evidence only and is no longer an active stage dependency.
This pipeline does not claim checkout-location independence.

The isolated CLI environment is `D:\AQ_ENVS\dvc`. Run from repository root:

```text
D:\AQ_ENVS\dvc\Scripts\dvc.exe repro pit_universe_snapshot
```
