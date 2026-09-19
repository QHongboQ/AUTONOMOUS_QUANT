# Selected Upstream Runtime Consolidation and Deployment Wave 001

## Result

```text
TASK = AUTONOMOUS-QUANT-SELECTED-UPSTREAM-RUNTIME-CONSOLIDATION-AND-DEPLOYMENT-WAVE-001
BASE_MAIN = de3c1b8b550a32074b0144b5e24566bca8a6b8d2
UPSTREAM_AUDIT_HEAD = 24971de487add13da0cd6f75086bcc63b4884538
AUDIT_BRANCH_AHEAD_BY = 1
AUDIT_BRANCH_BEHIND_BY = 0
AUDIT_BRANCH_DOCS_ONLY = YES
AUDIT_MERGE_REQUIRED = YES
SELECTED_UPSTREAM_INVENTORY_COMPLETE = YES
SELECTED_UPSTREAM_RUNTIME_COVERAGE = ALL_DEPLOYED_OR_EXPLICIT_BLOCKER
AQ_DUPLICATE_PRODUCTION_OWNER_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
AQ_ADAPTER_IMPLEMENTED = NO
```

The substitution audit remains an unmerged, one-commit, documentation-only
branch. Consequently, this task did not promote its architectural decisions to
main authority. Valuein, Arelle, Alphalens-reloaded, purgedcv, and
RFundamentals were consolidated only as isolated private runtimes with
`TASK_AUTHORIZED_PRIVATE_PENDING_AUDIT_MERGE` authority status. No production
adapter or routing change was made.

## Reused authoritative runtimes

| Upstream | Version or source pin | Runtime | Result |
|---|---|---|---|
| Microsoft Qlib | `0.9.8.dev26`, source `2fb9380b342556ddb50a4b24e4fe8655d548b2b8` | `/home/zhou/miniforge3/envs/rdagent4qlib` | PASS |
| Microsoft RD-Agent | `0.8.1.dev37`, source `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` | `/home/zhou/AQ_ENVS/rdagent` plus pinned source checkout | PASS |
| MLflow | `3.16.0` | Qlib runtime | PASS |
| DVC | `3.67.1` | Windows and WSL isolated runtimes | PASS |
| exchange_calendars | `4.13.2` | retained P2 isolated validation runtime | PASS |
| Pandera | `0.33.1` | retained P2 isolated validation runtime | PASS |
| DuckDB | `1.5.5` | retained P2 isolated validation runtime | PASS |
| pandas / PyArrow | `3.0.5` / `25.0.1` | retained P2 isolated validation runtime | PASS |
| skfolio | `1.0.6` | `D:/AQ_ENVS/skfolio` | PASS |
| arch | `8.0.0` | `D:/AQ_ENVS/arch` | PASS |
| Frouros | `0.9.0` | `/home/zhou/AQ_ENVS/p4-frouros-adwin` | PASS |
| AlphaGen | source `259687e8f316994426416c530a94842a2fe6405e` | existing isolated upstream-guidance runtime | PASS |
| EdgarTools | `5.58.0` | `/home/zhou/AQ_ENVS/p5-fundamental-intelligence` | PASS |
| OpenBB Core / SEC | `1.6.13` / `1.6.7` | same P5 filing runtime | PASS, supplementary only |
| secfsdstools | `2.4.3`, source `af83c24f999109322d01b4980d207eec67bc749e` | `/home/zhou/AQ_ENVS/p5-secfsdstools-bulk` | PASS, candidate catalog only |

The health probes exercised only public imports and bounded local fixtures.
Qlib retained DatasetH/model/Recorder ownership; RD-Agent retained the research
loop; skfolio retained WalkForward/CPCV; arch retained SPA, RealityCheck, StepM,
and MCS; Frouros retained ADWIN; and OpenBB remained
`SUPPLEMENTARY_NON_AUTHORITATIVE` for P5.

The secfsdstools runtime's user-default configuration had `AutoUpdate=True`.
A first import of its configured container path began an unintended update.
That exact process was terminated, and the solely task-generated
`/home/zhou/secfsdstools` tree was removed. Final validation used a private
configuration pointing to the already-retained bounded FSDS evidence with
`AutoUpdate=False`. No downloaded bytes from the accidental attempt were
retained, and no authoritative FSDS evidence was changed.

## Newly consolidated private runtimes

```text
VALUEIN_RUNTIME_READY = YES
EDGARTOOLS_RUNTIME_READY = YES
SECFSDSTOOLS_RUNTIME_READY = YES
OPENBB_RUNTIME_READY = YES
ARELLE_FALLBACK_RUNTIME_READY = YES
ALPHALENS_LEAF_RUNTIME_READY = YES
PURGEDCV_CANDIDATE_RUNTIME_READY = YES
RFUNDAMENTALS_RUNTIME_STATUS = RUNTIME_READY_ORACLE_ONLY
```

- Valuein SDK `5.2.0` was promoted in place at
  `/home/zhou/AQ_ENVS/p5-valuein-substitution`. Imports and one authenticated,
  read-only manifest call passed. The token remained process-private and is not
  present in evidence or Git. No binding was created.
- Arelle `2.45.1` remains an isolated fallback at
  `/home/zhou/AQ_ENVS/p5-arelle-fallback`. XBRL, dimensions, and Inline XBRL
  transform surfaces are present. EdgarTools remains primary.
- Alphalens-reloaded `0.4.6` remains a disconnected research-analysis leaf at
  `/home/zhou/AQ_ENVS/p5-alphalens-audit`; Qlib remains the IC/core research
  owner.
- purgedcv `0.1.6` remains a disconnected PSR/DSR candidate at
  `/home/zhou/AQ_ENVS/p5-purgedcv-audit`. Its CV splitters were not adopted over
  skfolio, and P2 protocol authority was unchanged.
- A new user-space-only R `4.4.3` environment was created at
  `/home/zhou/AQ_ENVS/p5-rfundamentals-oracle`. It loaded the required R/Arrow
  dependencies and the pinned RFundamentals source
  `d259b4153358d2683e7078b4a4c220b31a02e45b`; its offline smoke found the
  130-formula catalog. It remains `ORACLE_SOURCE_ONLY` because its timing,
  identity, and price-source semantics are not AQ PIT authority.

## Non-deployments and ownership preservation

AlphaForge and AlphaGPT remain disconnected challengers. LEAN remains an
execution candidate, FinRL-X remains challenger/fallback only, `sec-parser`
remains rejected, and `sec-edgar-downloader` remains a duplicate of the
selected SEC path. No alternate security master, price provider, workflow
engine, CV engine, drift engine, or generic registry was introduced.

The static registry also records the existing Quantiacs/SimFin P2 price-input
boundary and OpenFIGI's supporting-identity-only role. These are evidence of
current ownership, not new deployments.

## Private evidence

```text
PRIVATE_EVIDENCE_ROOT = D:/AQ_DATA/UPSTREAMS/selected-upstream-runtime-consolidation-and-deployment-wave-001
UPSTREAM_DEPLOYMENT_REGISTRY_SHA256 = ddf36ddb5444a44a547c794402703ecd9b04543a1ee0ed5f488a8324d94696e7
DEPENDENCY_FREEZES_SHA256 = e2203a7e33e860f37d8f1f542180611965d0e120173f205f6b4b01dd88567283
RUNTIME_HEALTH_RESULTS_SHA256 = bfdfb3e9c52885a72af2130a0fcaa28b941c9716717c22d22068d4cca13ebc13
DUPLICATE_OWNER_CHECK_SHA256 = 4aa2df9256fc7eb29651afe4be6aa63a7e32a81a620d7641a47edad6e12de0b5
CREDENTIALS_IN_PRIVATE_EVIDENCE = NO
PRIVATE_EVIDENCE_IN_GIT = NO
```

The registry is static evidence, not an AQ software registry. It records exact
runtime paths, package freezes, source pins, health, ownership, deployment
classification, authority status, duplicate-owner counts, and upgrade
boundaries.

## Safety and next step

```text
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
EXCHANGE_CALENDARS_RUNTIME_VERIFIED = YES
PANDERA_RUNTIME_VERIFIED = YES
PANDAS_RUNTIME_VERIFIED = YES
PYARROW_RUNTIME_VERIFIED = YES
CURRENT_DEVELOPMENT_NEXT = P5_UPSTREAM_DEPLOYMENT_SUBSTITUTION_AUDIT_PR_AND_MERGE_001
```

Because the substitution audit is not merged, the normal Valuein adapter task
is not yet authorized by main. The next step is its bounded PR/merge closeout
or formal adjudication; only afterward may
`P5_VALUEIN_THIN_IDENTITY_AND_FUNDAMENTALS_ADAPTER_001` begin.
