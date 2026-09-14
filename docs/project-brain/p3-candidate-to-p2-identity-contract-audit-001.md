# P3 Candidate-to-P2 Identity Contract Audit 001

Status: **COMPLETE — THIN STATIC MANIFEST REQUIRED AFTER DVC ACTIVATION**

This is a documentation-only, cross-upstream identity audit. It did not run
an RD-Agent loop, fit a model, create predictions, backtest, access market
data over the network, reproduce a DVC stage, or change any certification
authority.

## 1. Decision

```text
CANDIDATE_TO_P2_CONTRACT = THIN_STATIC_MANIFEST_REQUIRED
CONTRACT_IMPLEMENTATION_ORDER = AFTER_DVC_STAGE
CANDIDATE_ID_STRATEGY = DETERMINISTIC_HASH
CUSTOM_ENGINE_REQUIRED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
CURRENT_NEXT = P3_DVC_STAGE_ACTIVATION_001
```

No single upstream identifier spans the complete Candidate-to-P2 boundary.
RD-Agent owns research structure and content, Qlib Recorder/MLflow own the
executed run, DVC must own artifact and dependency versions, and P2 owns
eligibility and certification. AQ therefore needs only a small immutable
cross-upstream binding manifest after the P3 DVC stage establishes its
artifact identities. A registry, trial ledger, experiment database, packaging
engine, workflow engine, or generic runtime validator is not justified.

Candidate identity is not a performance result:

```text
CANDIDATE_IDENTITY != CERTIFICATION_RESULT
P3_CAN_ISSUE_CERTIFIED = NO
P3_CAN_ACCESS_SEALED_OOS = NO
P3_CAN_EDIT_PROTOCOL_V1 = NO
P3_CAN_PROMOTE_TO_PRODUCTION = NO
```

## 2. Audited authorities and immutable inputs

```text
RD_AGENT_VERSION = 0.8.1.dev37
RD_AGENT_SOURCE_SHA = 32b3d395e73d9db5eee3fe9063d69aec0fdc83bd
RD_AGENT_WHEEL_SHA256 = 6d4b78037016951d21879249152fee21df90e5dca0a752e233026a41afe64395
RD_AGENT_ENV_FREEZE_SHA256 = 1d60835745fad44b917eff46918719f8c1c392fb05747f06fb4dde8cb8c1f67e
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
FACTOR_STATIC_CONFIG_SHA256 = 7a5fa872aedc6820c5c1c8947fab8c2ac433f4d1a5f00eb2fab14656c2813b60
MODEL_STATIC_CONFIG_SHA256 = a7abc5cba54eb2f8bb6b7a5b703cfe63fa43450b22bc732db79f82bf86717296
P2_PROTOCOL_V1_GIT_BLOB_SHA256 = a9aed881c229f9eb7f85fa23b866168a55dc9c00be3c3b178d91a4af20451dfb
P2_PROTOCOL_ACTIVATION_SHA256 = d1ac67558f59d917eb71d666e48967f8f20bafc48bfc1ff616b7c85e262eef54
P2_PROTOCOL_FREEZE_MERGE_SHA = 8cd703b4108d2e377d146de8384b63c0355e93a6
P2_SEALED_OOS_START = 2026-09-14
P2_SEALED_OOS_MINIMUM_SESSIONS = 126
```

The protocol hash above is the canonical Git-blob content hash, avoiding
working-tree line-ending ambiguity.

## 3. RD-Agent native identity inventory

| Native fact | Classification | Candidate use |
|---|---|---|
| session folder and checkpoint path | `NATIVE_PATH_ONLY` | Evidence locator only; never identity |
| `loop_idx`, `step_idx`, trace history index, `idx2loop_id` | `NATIVE_EPHEMERAL` | Order/lineage locator within one session |
| trace `dag_parent` | `NATIVE_EPHEMERAL` relation | Parent relation needs content-bound endpoints |
| hypothesis text fields | `NATIVE_STABLE_CONTENT` | Canonically hash as research content |
| task name/version/description/instructions | `NATIVE_STABLE_CONTENT` | Canonically hash as task content |
| experiment structure and `based_experiments` | `NATIVE_STABLE_CONTENT` | Bind structure and parent content identities |
| workspace path | `NATIVE_PATH_ONLY` | Exclude from Candidate ID |
| workspace `file_dict` and generated code | `NATIVE_STABLE_CONTENT` | Content hash required |
| feedback content | `NATIVE_STABLE_CONTENT` | Lineage evidence, not top-level identity |
| immutable experiment/iteration ID | `NOT_AVAILABLE` | Cannot serve as Candidate ID |

RD-Agent's workspace UUID is a location convenience, not an immutable
research identity. Native trace indices are session-local and may move as the
trace evolves. The stable material is the content and relation, so the handoff
must bind canonical content hashes rather than paths or indices alone.

## 4. Qlib Recorder and MLflow identity inventory

Read-only public Recorder inspection of the existing P2 historical rehearsal
confirmed these native fields without creating an experiment or downloading an
artifact:

| Field | Classification | Candidate use |
|---|---|---|
| Qlib experiment ID | `NATIVE_AUTHORITATIVE` | Tracking-store experiment identity |
| MLflow/Qlib recorder run ID | `NATIVE_AUTHORITATIVE` | Executed-run identity |
| run status | `NATIVE_BUT_MUTABLE_METADATA` | Must be terminal `FINISHED` at handoff |
| experiment/recorder names | `NATIVE_BUT_MUTABLE_METADATA` | Display only |
| params and tags | `NATIVE_BUT_MUTABLE_METADATA` | Evidence; not content identity |
| metrics | `NATIVE_BUT_MUTABLE_METADATA` | Performance evidence only |
| artifact URI/path and size | `NATIVE_BUT_MUTABLE_METADATA` | Locator/diagnostic only |
| artifact checksum | `NOT_AVAILABLE` from listing | DVC identity/content hash required |
| task/config artifact | `CONTENT_HASH_REQUIRED` | Bind rendered execution input |
| serialized model artifact | `CONTENT_HASH_REQUIRED` | Required when the Candidate claims a model |
| prediction artifact | `CONTENT_HASH_REQUIRED` | Required for P2 handoff |
| analysis artifacts | `NOT_IDENTITY_CRITICAL` | Referenced by run; excluded from Candidate ID |

The inspected primary rehearsal run demonstrates why both native ID and
artifact identity are necessary: the run and predictions exist, while no
serialized model artifact appears in its public artifact inventory. A future
Candidate that requires a model must fail closed if that artifact is absent.
RD-Agent's Qlib result reader also selects the latest recorder across
experiments; the Candidate handoff must capture the exact run ID rather than
rely on "latest" selection.

The read-only SQLite tracking database remained byte-identical:

```text
MLFLOW_DB_SHA256_BEFORE = 226e6111e4d22e7541162ff61a2940994cf1edac5c01826c76effc7ae0cd3e31
MLFLOW_DB_SHA256_AFTER = 226e6111e4d22e7541162ff61a2940994cf1edac5c01826c76effc7ae0cd3e31
MLFLOW_DB_UNCHANGED = YES
```

## 5. Artifact identity decisions

| Artifact | Classification | Reason |
|---|---|---|
| RD-Agent generated factor/model code | `NEW_CONTENT_HASH_REQUIRED` | Workspace path and trace index are insufficient |
| rendered Qlib task/config | `NEW_CONTENT_HASH_REQUIRED` | Per-run substitutions change the executed task |
| factor/model P3 static configs | `EXISTING_HASH_SUFFICIENT` | Existing exact SHA-256 values bind the overlays |
| serialized model and model parameters | `DVC_IDENTITY_EXPECTED` | Must bind the exact run output without an AQ artifact engine |
| prediction artifact | `DVC_IDENTITY_EXPECTED` | Must bind the predictions presented to P2 |
| dataset/provider content | `DVC_IDENTITY_EXPECTED` plus existing authority tuple | A path alone is not identity |
| PIT membership identity | `EXISTING_HASH_SUFFICIENT` plus DVC dependency | Existing authoritative membership hash remains owner |
| analysis metrics and performance reports | `NOT_IDENTITY_CRITICAL` | They are evidence, not Candidate identity |

The two static config hashes bind the selected overlays, but not rendered
per-run substitutions. Therefore:

```text
STATIC_CONFIG_IDENTITY = STATIC_PLUS_RENDERED_CONFIG_HASH_REQUIRED
```

## 6. Dataset and provider identity

A local filesystem path is not a dataset identity. The minimum identity is a
small tuple of existing authoritative facts, completed by the future P3 DVC
dependency identity:

```text
PROVIDER_BUILD_REPORT_SHA256 = eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142
CALENDAR_SHA256 = d4c0c100af851245f6f894e275e5d494d7e1cbd07f82d342c034cbdf7b7bfa4d
ALL_INSTRUMENTS_SHA256 = 24d3a9010b725f8121ae1a999916bd0b6e76923eb9fad85be7e57d8653cc2cbc
P2_PIT_INSTRUMENTS_SHA256 = e771f73b91664b26584e66c42eb007c4276c492071172e7d6594bc900f01f875
DATE_BOUNDS = 2015-01-02..2024-12-31
SECURITY_IDENTITY_COUNT = 730
MEMBERSHIP_RANGE_COUNT = 745
MEMBER_SESSION_ROW_COUNT = 1267963
```

The build report records the shape and policy result, but it is not a content
identity for every provider feature file. The P3 DVC stage must bind the
provider input/dependency state. No new data registry or exhaustive AQ dataset
hashing engine is required.

## 7. Runtime/source identity

| Fact | Classification |
|---|---|
| RD-Agent source SHA and installed wheel hash | `REPRODUCIBILITY_CRITICAL` |
| Qlib source SHA | `REPRODUCIBILITY_CRITICAL` |
| DVC-owned environment/package snapshot identity | `REPRODUCIBILITY_CRITICAL` |
| installed RD-Agent/Qlib version strings | `DIAGNOSTIC_ONLY` when exact source identities exist |
| Python version | `DIAGNOSTIC_ONLY` when the environment snapshot is bound |
| absolute environment/source paths | `NOT_REQUIRED` for identity |

The manifest should reference the DVC-owned environment snapshot rather than
duplicate a complete package freeze.

## 8. P2 certification target identity

The Candidate must identify the exact Protocol V1 content and activation
authority, establish that it belongs to the protocol's eligible candidate
inventory, and attest that P3 did not access the sealed OOS. Protocol V1 fixes
the primary candidate and requires a new protocol version for candidate-set
expansion; a new Candidate cannot silently enter the existing protocol.

P2 alone owns eligibility, sealed-OOS access, acceptance/rejection, and
`CERTIFIED` issuance. Candidate identity neither grants eligibility nor encodes
certification outcome.

## 9. DVC ownership boundary and ordering

DVC must own these facts after activation:

- generated-code output identity;
- rendered Qlib task/config identity;
- serialized model and prediction output identities;
- provider/dataset dependency identity;
- runtime environment snapshot identity;
- reproducible stage dependency/output graph.

The repository currently has no P3 DVC stage. Materializing the Candidate
contract before activation would either contain placeholders or make AQ
duplicate DVC's artifact-version responsibility. Therefore implementation is
ordered `AFTER_DVC_STAGE`.

## 10. Minimum cross-upstream binding matrix

| Field | Semantic purpose | Authoritative owner | Native source | Immutable or mutable | Required for P2 handoff | AQ must own | Rationale |
|---|---|---|---|---|---|---|---|
| `candidate_contract_version` | Interpret the binding document | AQ boundary | static manifest spec | immutable | yes | yes | No upstream owns the cross-upstream schema version |
| `candidate_id` | Stable identity of the complete binding | AQ boundary | deterministic hash of the canonical tuple below | immutable | yes | yes | No upstream ID spans all authorities |
| `rdagent_research_identity` | Bind hypothesis, task, generated code and parent lineage | RD-Agent content; AQ binds reference | trace/experiment/workspace content hashes | immutable when hashed | yes | binding only | RD-Agent has content but no sufficient immutable experiment ID |
| `qlib_recorder_identity` | Bind the exact completed execution | Qlib Recorder/MLflow | experiment ID, run ID, terminal status | IDs stable; status mutable until terminal | yes | binding only | Prevents "latest run" ambiguity |
| `artifact_identity_bundle` | Bind static/rendered configs, code, model and prediction | DVC and source files | hashes plus DVC output references | immutable | yes | binding only | Prevents artifact replacement and missing-output handoff |
| `dataset_identity_bundle` | Bind provider, calendar and PIT membership inputs | P2 data authorities and DVC | existing hashes/counts/bounds plus DVC dependency | immutable | yes | binding only | Paths and display names are insufficient |
| `runtime_identity_bundle` | Bind reproducing RD-Agent/Qlib environments | source authorities and DVC | source/wheel hashes plus environment snapshot reference | immutable | yes | binding only | Avoids version-string-only provenance |
| `p2_target_and_eligibility_boundary` | Bind protocol, activation, inventory eligibility and sealed-OOS isolation | P2 Certification | protocol/activation identities and access attestation | immutable for one handoff | yes | binding only | P3 cannot issue certification or expand Protocol V1 |

```text
AQ_REQUIRED_IDENTITY_FIELD_COUNT = 8
```

AQ owns the eight top-level binding fields, not the underlying upstream facts.
The bundle boundaries prevent redundant top-level fields while preserving
explicit owner attribution and fail-closed completeness.

## 11. Deterministic Candidate ID tuple

`candidate_id` should be a deterministic hash over the canonical, explicitly
versioned representations of:

1. `candidate_contract_version`;
2. `rdagent_research_identity`;
3. `qlib_recorder_identity`;
4. `artifact_identity_bundle`;
5. `dataset_identity_bundle`;
6. `runtime_identity_bundle`;
7. `p2_target_and_eligibility_boundary`.

The computed `candidate_id` itself is not included recursively. Timestamps,
hostnames, absolute paths, temporary directories, display names, metrics,
returns, Sharpe, IC, win rate, and statistical gate outcomes are excluded.
No opaque UUID or mutable Candidate registry is needed.

## 12. Fail-closed boundary rules

P2 must reject the handoff before certification execution when any of these is
true:

- a required top-level field or owned subfield is absent;
- the Qlib experiment/run identity is absent, non-unique, or not `FINISHED`;
- required generated code, rendered config, model, or prediction is absent;
- any content hash, DVC dependency/output identity, or DVC lock state differs;
- static and rendered config identities do not reconcile;
- the provider/calendar/PIT membership identity tuple differs;
- RD-Agent source/wheel, Qlib source, or environment identity differs;
- RD-Agent parent/artifact lineage is incomplete or cannot be content-bound;
- the P2 protocol version/hash/activation identity differs;
- the Candidate is outside the frozen protocol inventory;
- sealed-OOS access or contamination is indicated;
- a mutable path, name, timestamp, metric, or performance result is used as
  the sole authority for identity.

These are static contract checks over upstream-owned evidence. This audit does
not establish a need for a new AQ runtime validation engine.

## 13. Residual implementation gaps

The finite remaining work is:

1. activate the P3 DVC stage so DVC owns exact dependencies and outputs;
2. materialize the eight-field thin static Candidate-to-P2 manifest against
   those DVC identities;
3. integrate Candidate production into the autonomous research loop only
   after the static boundary is independently reviewed.

No unresolved identity-design blocker remains.

## 14. Non-actions

```text
CODE_CHANGED = NO
SCHEMA_IMPLEMENTED = NO
MANIFEST_IMPLEMENTED = NO
DVC_STAGE_CHANGED = NO
RD_AGENT_LLM_LOOP_EXECUTED = NO
LLM_CALLS = 0
MODEL_TRAINING = NO
MODEL_FIT_CALLS = 0
NEW_PREDICTIONS = NO
BACKTEST = NO
PERFORMANCE_METRICS_CREATED = NO
DVC_REPRO_EXECUTED = NO
MARKET_DATA_NETWORK_CALLS = 0
DATASET_DOWNLOADS = 0
BROKER_CALLS = 0
PAPER_TRADING = NO
LIVE_TRADING = NO
```
