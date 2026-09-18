# P4 Upstream Components Integration and Ownership Reaudit 001

## Decision

```text
P4_UPSTREAM_COMPONENTS_INTEGRATION_AND_OWNERSHIP_REAUDIT = PASS_UPSTREAM_INTEGRATION_CLEAN
P4_UPSTREAM_STACK = QLIB_MLFLOW_DVC_FROUROS_INTEGRATED
P4_ADDITIONAL_UPSTREAM_DEPLOYMENT_REQUIRED = NO
P4_GENERIC_AQ_ENGINE_COUNT = 0
P4_RESIDUAL_AQ_SCOPE = EXPLICIT_AND_DOMAIN_SPECIFIC_ONLY
CURRENT_NEXT = P4_RESIDUAL_THIN_POLICY_IMPLEMENTATION_001
```

The implemented stack remains correctly partitioned. Qlib owns metric and
Recorder mechanics, MLflow owns experiment/run/artifact identity, Frouros owns
ADWIN mathematics, and DVC owns reproducibility and dependency/output
identity. AQ contains only closed evidence contracts, fixed domain validation,
one audited RankIC translation, and cross-upstream identity checks.

No bounded cleanup or additional upstream deployment is required before the
remaining domain-specific policy slice.

## Implementation inventory

The deterministic counting rule is physical UTF-8 source lines. Runtime means
tracked non-test Python under
`40-certification-system/champion-challenger/p4-frouros-adwin/`.

```text
RUNTIME_IMPLEMENTATION_FILES = 3
RUNTIME_IMPLEMENTATION_LOC = 738
TEST_FILES = 4
TEST_LOC = 631
SCHEMA_COUNT = 3
SCHEMA_LOC = 159
CLI_ENTRY_POINTS = 3
TOP_LEVEL_FUNCTIONS = 23
TOP_LEVEL_CLASSES = 2
PUBLIC_FUNCTIONS = 20
PUBLIC_CLASSES = 2
```

The runtime files are the RankIC exporter, the Frouros runner, and the identity
projection validator/seal producer. The contracts remain distinct:

- `MetricObservationStreamV1` carries neutral ordered RankIC observations and
  the source artifact identity;
- `DetectorEvidenceV1` carries detector configuration, translation provenance,
  replay authority, and statistical change evidence;
- `UpstreamIdentityProjectionV1` binds Qlib, MLflow, Frouros, and the first two
  exact-byte contracts.

Merging them would collapse replacement boundaries rather than remove a
redundant wrapper.

## Function ownership audit

Every one of the 25 top-level runtime functions/classes was classified:

```text
UPSTREAM_CALL = 1
AQ_DOMAIN_VALIDATION = 6
AQ_BOUNDED_GLUE = 5
AQ_IDENTITY_BINDING = 4
AQ_CONTRACT_SERIALIZATION = 9
GENERIC_REIMPLEMENTATION_SUSPECT = 0
UNNECESSARY = 0
```

The sole `UPSTREAM_CALL` is the bounded `run_adwin` path. It constructs public
Frouros `ADWINConfig` and `ADWIN`, feeds the fixed translated stream, and
records evidence. No AQ code implements adaptive windows, variance,
cut-point search, thresholds, window compression, CUSUM, Page-Hinkley, or any
change-point mathematics.

The short SHA-256 and deterministic-JSON helpers are standard-library exact
byte operations tied to closed contracts. They are not a canonicalization or
serialization framework. Their limited repetition keeps the Qlib, isolated
Frouros, and DVC environments independent.

## Deep audits

### Qlib exporter

```text
QLIB_EXPORTER_CLASSIFICATION = RANK_IC_ONLY_THIN_BOUNDED_EXPORTER
AQ_METRIC_ENGINE = NO
AQ_QLIB_RECORDER_REIMPLEMENTATION = NO
```

It loads only an explicitly supplied `ric.pkl`, validates one pandas Series,
and writes the closed neutral stream. It does not calculate RankIC, reconstruct
labels, compute rolling metrics, discover a latest Recorder, normalize
arbitrary metrics, or implement a metric registry.

### Frouros runner

```text
FROUROS_RUNNER_CLASSIFICATION = THIN_BOUNDED_ADAPTER
ADWIN_MATH_OWNER = FROUROS
AQ_ADWIN_IMPLEMENTATION = NO
AQ_CHANGE_POINT_MATH = NO
AQ_DRIFT_ENGINE = NO
```

The runner validates one fixed contract, records the audited constant `+1.0`
RankIC translation, calls only public Frouros APIs, and serializes bounded
detector evidence. It contains no detector abstraction, plugin system, generic
transform pipeline, state manager, or runtime-launch framework.

### Identity projection

```text
IDENTITY_PROJECTION_CLASSIFICATION = PROJECT_SPECIFIC_BOUNDED_VALIDATION
AQ_GENERIC_IDENTITY_ENGINE = NO
AQ_DVC_ENGINE = NO
```

Its responsibilities are necessary and finite: exact-byte hashes,
Qlib/MLflow equality checks, artifact/evidence/runtime bindings,
interpretation-source bindings, closed projection validation, and one small
DVC seal. DVC still owns the graph, invalidation, cache, output hash, lock, and
reproduction. Qlib, MLflow, Frouros, and DVC do not individually own the
project-specific equality assertions across their identity surfaces.

Replacing the manual checks with Pydantic in the DVC runtime would add a
transitive-runtime coupling without removing the cross-field checks.
`jsonschema` and RFC 8785 are absent from the isolated Frouros/DVC boundary
where relevant. No dependency change is justified.

## Schema and serialization

```text
SCHEMA_VALIDATION_DUPLICATION = NECESSARY_CROSS_RUNTIME_FAIL_CLOSED_CHECK
SERIALIZATION_IDENTITY_CLASSIFICATION = BOUNDED_DETERMINISTIC_EXACT_BYTE_SERIALIZATION
AQ_CUSTOM_CANONICALIZER = NO
CROSS_RUNTIME_BOUNDARY = IMMUTABLE_FILE_CONTRACT
GENERIC_RPC_FRAMEWORK = NO
```

Pydantic validates the Qlib-side object model, JSON Schema is the portable
contract, and small manual checks protect the dependency-minimal Frouros and
DVC consumers. This is deliberate boundary validation, not a replacement
schema engine. Sorted compact JSON plus one newline defines exact artifact
bytes and explicitly makes no RFC 8785 semantic-canonicalization claim.

## Ownership and persistence

| Owner | Mode | Retained responsibility |
| --- | --- | --- |
| Qlib | `UPSTREAM_WHOLE` | RankIC, SigAnaRecord, Recorder, rolling/online mechanics |
| MLflow | `UPSTREAM_LEAF` | experiment, run, status, artifact identity |
| Frouros | `UPSTREAM_LEAF` | ADWIN change-detection mathematics |
| DVC | `UPSTREAM_LEAF` | dependency/output identity, invalidation, reproduction, lock |
| RFC 8785 | `UPSTREAM_LEAF` when needed | semantic canonicalization only |
| AQ | thin domain/integration | bounded validation, identity consistency, translation provenance, future policy |
| P2 | sole authority | certification |
| P12 | sole authority | operational scheduling |

```text
AQ_EXPERIMENT_REGISTRY = NO
AQ_MODEL_REGISTRY = NO
AQ_ARTIFACT_STORE = NO
AQ_STATE_DATABASE = NO
AQ_IDENTITY_DATABASE = NO
AQ_DECISION_DATABASE = NO
AQ_EVENT_STORE = NO
DETECTOR_DURABLE_AUTHORITY = REPLAY_FROM_IMMUTABLE_OBSERVATIONS
MODULE_REPLACEABILITY = PASS
```

The file contracts preserve module replacement: detector implementation can
change without changing Qlib metric production; the Qlib source can evolve
without absorbing detector math; MLflow remains behind the Qlib identity
boundary; DVC can remain or later be replaced as a reproducibility leaf without
changing detector or lifecycle semantics.

## Tests, hygiene, and environment immutability

```text
IDENTITY_PROJECTION_TESTS = 14/14 PASS
QLIB_EXPORTER_TESTS = 11/11 PASS
FROUROS_RUNNER_TESTS = 8/8 PASS
FULL_CROSS_RUNTIME_TESTS = 1/1 PASS
DVC_STAGE_PARSE_DAG_STATUS = PASS
TRACKED_PRIVATE_EVIDENCE_LEAK = NO
FROUROS_SOURCE_COPIED = NO
AUTHORITATIVE_ENV_MUTATION = NO
HISTORICAL_TEST_ACCESSED = NO
SEALED_OOS_ACCESSED = NO
```

The tests are behavioral and fail closed on malformed contracts, identity
mismatches, altered bytes, runtime drift, and unsupported metrics. The full
adapter parity test invokes the real isolated Frouros public API over synthetic
fixtures. It does not mock detector mathematics or read historical research
evidence. The prior DVC integration retains a successful first reproduction
and immediate unchanged second reproduction.

No private MLflow database, `ric.pkl`, generated evidence, virtual environment,
wheel, package cache, or Frouros source is tracked. Package inventories for
`rdagent4qlib`, `aq-alphagen-upstream-guidance`, `p4-frouros-adwin`, and
`dvc-p3` remained unchanged during this audit.

## Residual AQ scope

The remaining P4 work is explicit and domain-specific only:

```text
RESIDUAL_AQ_DOMAIN_FACTS = lifecycle meanings and allowed transitions; challenger role semantics; financial degradation meanings; human authority boundaries
RESIDUAL_AQ_CONTRACTS = shadow completeness/admission; producer-neutral ResearchRequestV1; lifecycle decision evidence
RESIDUAL_AQ_GLUE = consume Qlib/MLflow/DVC/Frouros evidence identities without persistence or orchestration
RESIDUAL_AQ_EXECUTABLE_POLICY = small pure degradation, promotion, demotion, retirement, and request-construction predicates
ADDITIONAL_UPSTREAM_DEPLOYMENT_REQUIRED = NO
```

Prior substitution evidence established that FSM, rule/policy, persistence,
and serving/orchestration upstreams would add more generic machinery than these
fixed project meanings require. No generic mechanism remains in the residual
list.

P2 Protocol was not modified and the real Certified artifact count remains
zero. Formulaic candidates are still
`INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION`. That blocks the eventual real
Candidate → Certified → Shadow → Champion exit proof, but not implementation
of the residual pure P4 policy.

## Private evidence

```text
PRIVATE_REPORT = D:/AQ_DATA/P4/upstream-components-integration-and-ownership-reaudit-001/reaudit_summary.json
PRIVATE_REPORT_SHA256 = abe2d366c672cea0b9235e6f6db87bbd88826e06af64eb0d3011d522b8661992
```

## Next

```text
CURRENT_NEXT = P4_RESIDUAL_THIN_POLICY_IMPLEMENTATION_001
```

This audit does not begin that implementation.
