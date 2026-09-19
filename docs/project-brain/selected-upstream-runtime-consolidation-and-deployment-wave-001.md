# Selected Upstream Runtime Consolidation and Deployment Wave 001

## Authority and result

```text
TASK = AUTONOMOUS-QUANT-SELECTED-UPSTREAM-RUNTIME-CONSOLIDATION-AND-DEPLOYMENT-WAVE-001
ORIGINAL_BASE_MAIN = de3c1b8b550a32074b0144b5e24566bca8a6b8d2
ORIGINAL_DEPLOYMENT_HEAD = 6eaef2c6738ea86f4eec682ed73bc85f66422994
UPSTREAM_AUDIT_PR = 55
UPSTREAM_AUDIT_MERGE_SHA = 4f79dddfc747ffb98bdad4bb11d19e4f476b02ca
DEPLOYMENT_REPLAY_BASED_ON_POST_AUDIT_MAIN = YES
SELECTED_UPSTREAM_INVENTORY_COMPLETE = YES
SELECTED_UPSTREAM_RUNTIME_COVERAGE = ALL_DEPLOYED_OR_EXPLICIT_BLOCKER
AQ_DUPLICATE_PRODUCTION_OWNER_COUNT = 0
AQ_NEW_GENERIC_ENGINE_COUNT = 0
AQ_ADAPTER_IMPLEMENTED = NO
```

The substitution and retirement audit is authoritative on main. This report
adds only the independently verified private runtime readiness facts. It does
not expand any tool's audited role or create production routing, bindings, or
adapter code.

## Verified authoritative runtimes

| Upstream | Version or source pin | Runtime | Result and role |
|---|---|---|---|
| Microsoft Qlib | `0.9.8.dev26`, source `2fb9380b342556ddb50a4b24e4fe8655d548b2b8` | `/home/zhou/miniforge3/envs/rdagent4qlib` | PASS; primary research owner |
| Microsoft RD-Agent | `0.8.1.dev37`, source `32b3d395e73d9db5eee3fe9063d69aec0fdc83bd` | `/home/zhou/AQ_ENVS/rdagent` plus pinned source checkout | PASS; research-loop owner |
| MLflow | `3.16.0` | Qlib runtime | PASS; experiment/run identity owner |
| DVC | `3.67.1` | isolated Windows and WSL runtimes | PASS; reproducibility identity owner |
| exchange_calendars | `4.13.2` | retained P2 isolated validation runtime | PASS; XNYS session authority |
| Pandera | `0.33.1` | retained P2 isolated validation runtime | PASS; schema validation owner |
| pandas / PyArrow | `3.0.5` / `25.0.1` | retained P2 isolated validation runtime | PASS |
| DuckDB | `1.5.5` | retained P2 isolated validation runtime | PASS; relational composition owner |
| skfolio | `1.0.6` | `D:/AQ_ENVS/skfolio` | PASS; primary purged/embargo CV and CPCV owner |
| arch | `8.0.0` | `D:/AQ_ENVS/arch` | PASS; primary SPA, RealityCheck, StepM, and MCS owner |
| Frouros | `0.9.0` | `/home/zhou/AQ_ENVS/p4-frouros-adwin` | PASS; ADWIN owner |
| AlphaGen | source `259687e8f316994426416c530a94842a2fe6405e` | isolated upstream-guidance runtime | PASS |
| EdgarTools | `5.58.0` | `/home/zhou/AQ_ENVS/p5-fundamental-intelligence` | PASS; PIT-critical exact historical filing evidence |
| OpenBB Core / SEC | `1.6.13` / `1.6.7` | P5 filing runtime | PASS; supplementary and non-authoritative |
| secfsdstools | `2.4.3`, source `af83c24f999109322d01b4980d207eec67bc749e` | `/home/zhou/AQ_ENVS/p5-secfsdstools-bulk` | PASS; bulk candidate catalog only |

Public imports and bounded local fixtures verified each runtime without factor
creation, model training, prediction, backtesting, historical dataset build,
or sealed-OOS access.

## Isolated partial, fallback, candidate, and oracle runtimes

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

- Valuein SDK `5.2.0` is isolated at
  `/home/zhou/AQ_ENVS/p5-valuein-substitution`. Imports and a bounded,
  authenticated, read-only manifest check passed. Its token remained
  process-private and is absent from Git and the evidence ledger. Its role is
  `MATERIAL_PARTIAL_UPSTREAM`, not sole Episode-to-CIK authority.
- Arelle `2.45.1` is an isolated fallback at
  `/home/zhou/AQ_ENVS/p5-arelle-fallback`. XBRL, dimensions, and Inline XBRL
  transform surfaces are available. EdgarTools remains primary.
- Alphalens-reloaded `0.4.6` is a disconnected, non-duplicative research
  analysis leaf at `/home/zhou/AQ_ENVS/p5-alphalens-audit`. Qlib remains the
  core research and IC owner.
- purgedcv `0.1.6` is a disconnected PSR/DSR candidate at
  `/home/zhou/AQ_ENVS/p5-purgedcv-audit`. Its duplicate CV splitters are not
  adopted over skfolio and no P2 protocol authority changed.
- RFundamentals source `d259b4153358d2683e7078b4a4c220b31a02e45b`
  runs in an isolated user-space R `4.4.3` environment at
  `/home/zhou/AQ_ENVS/p5-rfundamentals-oracle`. The formula/panel smoke passed,
  but the runtime remains `ORACLE_ONLY`; its timing, identity, and price-source
  semantics are not AQ PIT authority.

## secfsdstools operational safety

During the private deployment check, the user-default secfsdstools
configuration had `AutoUpdate=True`; an import began an unintended update.
The exact process was terminated and the solely task-created tree was removed.
No authoritative evidence changed and no bytes from that attempt were retained.
Final validation used the upstream configuration surface with a private,
bounded source and `AutoUpdate=False`.

```text
SECFSDSTOOLS_AUTOUPDATE_DEFAULT_TRUSTED = NO
SECFSDSTOOLS_REQUIRED_RUNTIME_POLICY = EXPLICIT_AUTOUPDATE_FALSE_UNLESS_SEPARATELY_AUTHORIZED
```

An import or smoke test must never silently trigger a historical bulk download.
This is an upstream configuration rule, not authorization for replacement AQ
logic.

## Ownership and non-deployment boundary

AlphaForge and AlphaGPT remain disconnected challengers. LEAN remains an
execution candidate, FinRL-X remains challenger/fallback only, `sec-parser`
remains rejected, and `sec-edgar-downloader` remains a duplicate of the
selected SEC path. Quantiacs and SimFin retain the existing P2 price boundary;
OpenFIGI remains supporting identity evidence only. No alternate security
master, price provider, workflow engine, CV engine, drift engine, or generic
registry was introduced.

The future Valuein task remains fail-closed:

```text
VALUEIN_COMPATIBLE_MATCH_AUTO_ADMISSION = PROHIBITED
VALUEIN_PARTIAL_MATCH_AUTO_ADMISSION = PROHIBITED
VALUEIN_AMBIGUOUS_MATCH_AUTO_ADMISSION = PROHIBITED
VALUEIN_NO_MATCH_BACKFILL = PROHIBITED
VALUEIN_TICKER_ONLY_BACKFILL = PROHIBITED
AQ_SECURITY_MASTER = NO
AQ_PROVIDER_FRAMEWORK = NO
AQ_GENERIC_ADAPTER_FRAMEWORK = NO
AQ_IDENTITY_ENGINE = NO
AQ_FUNDAMENTAL_ENGINE = NO
```

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

The static registry covers 31 selected, retained, candidate, oracle, deferred,
rejected, and duplicate entries. It is evidence, not an AQ software registry.

## Final state

```text
QLIB_RUNTIME_VERIFIED = YES
RDAGENT_RUNTIME_VERIFIED = YES
MLFLOW_RUNTIME_VERIFIED = YES
DVC_RUNTIME_VERIFIED = YES
SKFOlIO_RUNTIME_VERIFIED = YES
ARCH_RUNTIME_VERIFIED = YES
FROUROS_RUNTIME_VERIFIED = YES
EXCHANGE_CALENDARS_RUNTIME_VERIFIED = YES
PANDERA_RUNTIME_VERIFIED = YES
PANDAS_RUNTIME_VERIFIED = YES
PYARROW_RUNTIME_VERIFIED = YES
AQ_ADAPTER_IMPLEMENTED = NO
P5_HISTORICAL_DATASET_BUILT = NO
P5_FACTOR_CREATED = NO
MODEL_TRAINING = NO
P5_BACKTEST = NO
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_DEVELOPMENT_NEXT = P5_VALUEIN_THIN_IDENTITY_AND_FUNDAMENTALS_ADAPTER_001
```
