# P1 DVC DatasetSnapshot 001

## Result

The research-ready PIT universe now crosses a small immutable
`DatasetSnapshotV1` boundary and is tracked by DVC `3.67.1`. The snapshot has
832 deterministically ordered episode rows. Each JSONL row contains exactly
`episode_id`, `ticker`, `membership_from`, and `membership_to`; adjacent JSON
metadata contains only logical schema/universe identity, coverage, row count,
and `RESEARCH_READY` state.

The data product lives under
`10-data-system/dataset-snapshot/pit-universe`. DVC operations documentation and
the pinned CLI requirement live under
`70-operations-system/reproducibility/dvc`. Root `.dvc/`, `.dvcignore`,
`dvc.yaml`, and `dvc.lock` are upstream-required repository metadata.

This follows DVC's documented model: `dvc.yaml` declares the command,
dependencies, and output; `dvc.lock` records calculated state; `dvc repro`
skips unchanged stages and the local cache restores tracked output. References:
[DVC command reference](https://dvc.org/doc/command-reference/) and
[DVC pipelines](https://dvc.org/doc/user-guide/pipelines/defining-pipelines).

## Responsibility boundary

```text
ResearchReadyUniverse (public PIT contract)
  -> DatasetSnapshot exporter (domain-level output shape)
  -> deterministic episodes.jsonl + snapshot.json
  -> DVC dependency/output/lock/cache tracking
  -> future Qlib adapter
```

The DatasetSnapshot code imports only the public PIT package surface. It does
not import DVC. PIT code does not import DVC. DVC invokes the public exporter
CLI and does not reach into private PIT helpers. DVC owns no membership,
identity, calendar, market-data, model-training, certification, or promotion
semantics.

## DVC verification

- isolated CLI: `D:\AQ_ENVS\dvc`, Python 3.12.14, `dvc==3.67.1`
- dependency check: PASS (99 installed packages compatible)
- real stage declared inputs include the accepted fact JSON, public thin-runtime
  code, pinned FJA CSV, and unresolved-ledger input
- real stage output: `10-data-system/dataset-snapshot/pit-universe/data`
- first reproduction: PASS; `dvc.lock` generated
- identical reproduction: PASS; stage reported unchanged and was skipped
- local cache reproduction: PASS; removed output restored byte-identically
- relevant input mutation: PASS in an isolated fixture; stage reran
- irrelevant file mutation: PASS in an isolated fixture; stage remained skipped
- deterministic snapshot generation: PASS; two exports were byte-identical

No cloud remote was configured. DVC's cache and the generated DatasetSnapshot
payload remain outside Git; the lock and pipeline definitions are in Git.

## Artifact responsibility audit

| Mechanism | Classification | Result |
|---|---|---|
| former manual `build_research_ready_universe.py` file writer | REPLACED_BY_DVC / DELETE_NOW | removed |
| DVC dependency, output, lock, cache, invalidation and rerun state | REPLACED_BY_DVC | upstream-owned |
| deterministic episode and logical dataset IDs | KEEP_DOMAIN | not file-content tracking |
| accepted raw FJA SHA verification | KEEP_DOMAIN | protects domain-accepted input bytes |
| historical generic manifests in oracle-only PIT path | KEEP_ORACLE_TEST_ONLY | inactive in P1 |
| official evidence, terminal authority and promotion records | DEFER_P2 | not reintroduced |

Custom P1 generic artifact/reproducibility LOC is measured as nonblank,
non-comment production Python, excluding tests, docs, DVC metadata/upstream,
and the DatasetSnapshot domain contract/exporter. Before: 32 lines in the
manual file writer. After: 0. Removed: 32. No custom artifact framework or
pipeline engine replaced DVC.

## Validation and state

The prior stack remains 118/118 PASS. Eleven focused DatasetSnapshot/DVC tests
PASS, for 129/129 combined tests. The 11 calendar tests and all 13 frozen PIT
regressions remain PASS. Compileall passes.

```text
P0 = COMPLETE
P1 = STARTED
P1_MINIMAL_QUANT = IN_PROGRESS
P1_PIT_THIN_RUNTIME = COMPLETE
P1_DVC_DATASET_SNAPSHOT = COMPLETE
PIT_UNIVERSE_RESEARCH_READY = YES
PIT_UNIVERSE_CERTIFIED = NO
CURRENT_NEXT = P1_QLIB_DATASET_HANDOFF
QLIB_ADDED = NO
OPENBB_ADDED = NO
ZIPLINE_ADDED = NO
P2_CERTIFICATION_REINTRODUCED = NO
PRODUCTION_TRADING = NOT_AUTHORIZED
```
