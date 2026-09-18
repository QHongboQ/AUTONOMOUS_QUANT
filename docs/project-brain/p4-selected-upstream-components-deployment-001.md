# P4 Selected Upstream Components Deployment 001

## Decision

```text
P4_SELECTED_UPSTREAM_COMPONENTS_DEPLOYMENT = PASS
P4_FROUROS_VERSION = 0.9.0
P4_FROUROS_RUNTIME = ISOLATED_PYTHON_3_10_21
P4_FROUROS_ADWIN = DEPLOYED_UPSTREAM_LEAF
P4_FROUROS_OFFSET_INVARIANCE = PASS
P4_FROUROS_SOURCE_MODIFIED = NO
P4_AQ_DRIFT_ENGINE = NO
CURRENT_NEXT = P4_FROUROS_THIN_EVIDENCE_ADAPTER_001
```

This task deployed and validated only the upstream Frouros ADWIN leaf selected
by the residual-capability substitution audit. It did not implement a Qlib
metric adapter, financial-decay policy, lifecycle policy, state machine,
Research Request, identity projection, workflow engine, metric engine, or
state database.

## Runtime

```text
ENVIRONMENT = /home/zhou/AQ_ENVS/p4-frouros-adwin
PYTHON = 3.10.21
FROUROS = 0.9.0
ADWIN_MODULE = frouros.detectors.concept_drift.streaming.window_based.ADWIN
PIP_CHECK = PASS
PACKAGE_DISTRIBUTION_COUNT = 22
ENVIRONMENT_DISK_BYTES = 282889059
```

The environment has independent site-packages and was created with `uv
0.12.12`. Frouros was installed from the official PyPI wheel:

```text
WHEEL = frouros-0.9.0-py3-none-any.whl
WHEEL_SHA256 = 0c88ddeccfe2ac1f105b44efcfc65ba5b879cd8a07e492139c4316677b708980
AUDITED_RELEASE_SOURCE_SHA = 2484916fe0ba50dd2f28bbf1899f2ef3e499df31
AUDITED_REPOSITORY_HEAD = 9fc1f1cd2174f0aaa7eefb7133f2a17b7ba7b970
INSTALLED_ADWIN_MODULE_SHA256 = f3b2c06acf88b6938eac907909ca16b8daa382133eb1247e297a12f299ebd8fd
```

The installed package version and wheel SHA match the audited package
authority. The Git release commit remains release provenance; this task does
not claim that installed wheel bytes are identical to a Git working tree.
Frouros source was neither copied nor modified.

The exact environment freeze is tracked by private evidence and the bounded
lock at
`40-certification-system/champion-challenger/p4-frouros-adwin/requirements.lock`:

```text
FROUROS_RUNTIME_FREEZE_SHA256 = 8c66ad3fde0f116d89aa31c0454a093eba00b16fe6d5946ac973bd5850dfb5d5
PACKAGE_INVENTORY_SHA256 = c079dfacf4481e34dcc163835b6b7538321e74b4ee6bc1715625dc817d72b9d9
```

## Existing environment immutability

Sorted `pip freeze` hashes were captured before and after deployment:

| Environment | Python | Before | After |
| --- | --- | --- | --- |
| `/home/zhou/miniforge3/envs/rdagent4qlib` | 3.10.21 | `dc01037d0ee3d8cd86d891bdaff629ed364c2d574085288ba05d983d51a1ff16` | same |
| `/home/zhou/miniforge3/envs/aq-alphagen-upstream-guidance` | 3.10.21 | `88793e67178d1097b1500107926cb6bc1f72eccf525159e062f5cecf741afb40` | same |
| `/home/zhou/AQ_ENVS/dvc-p3` | 3.12.3 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | same |

```text
AUTHORITATIVE_ENV_MUTATION = NO
```

## Public API and upstream limitation

The deployed environment passed public imports of `ADWIN` and `ADWINConfig`,
construction, default configuration, update, drift status, and `reset()`.
No private method is used. The public API is documented by Frouros at
<https://frouros.readthedocs.io/en/v0.9.0/api_reference/detectors/concept_drift/auto_generated/frouros.detectors.concept_drift.streaming.window_based.ADWIN.html>.

The prior negative-input limitation was reproduced without patching upstream:

```text
SIGNED_STREAM_NATIVE_SUPPORT = NO
INPUT = -0.05 from a fresh detector
RESULT = ValueError: total value must be greater or equal than 0.0.
SIGNED_STREAM_LIMITATION_REPRODUCED = YES
```

## Constant-offset invariance

The five frozen synthetic financial-style streams were processed with constant
offsets `+1.0` and `+2.0`. Both offsets keep the upstream running total valid.
For every case, the complete per-observation drift-flag sequence and first
detection index were identical:

```text
OFFSET_TEST_CASES_PASS = 5/5
ADWIN_CHANGE_DECISION_CONSTANT_OFFSET_INVARIANT = PASS
```

This demonstrates that a later explicit translation is an input-domain seam,
not AQ-owned detector math. No adapter was created in this task.

## Prior POC replay and determinism

The exact prior seed, stream generation, and case order were replayed without
historical TEST or sealed OOS:

| Frozen case | Deployed result |
| --- | ---: |
| positive RankIC → near zero | first drift 1247 |
| positive RankIC → sign reversal | first drift 1119 |
| stable noise | no drift |
| gradual deterioration | first drift 1823 |
| temporary shock/recovery | no drift |

```text
PRIOR_POC_REPLAY = PASS
DETERMINISTIC_REPLAY = PASS
RESET_REPLAY = PASS
STATE_RESTORE = PASS_PYTHON_PICKLE_PRESERVED_POC_PATH_NOT_A_STABLE_CROSS_VERSION_FORMAT
```

The pickle result proves parity with the preserved POC path. It is not a
promise of a stable cross-version serialization format and does not add AQ
state logic.

## Dependency boundary

The isolated environment contains only the 22 frozen distributions needed by
the seeded environment and Frouros resolution. None of the rejected/deferred
P4 candidates is installed:

```text
UNAUTHORIZED_P4_PACKAGE_ADDITIONS = 0
RIVER_INSTALLED = NO
TRANSITIONS_INSTALLED = NO
RULE_ENGINE_INSTALLED = NO
CLOUDEVENTS_INSTALLED = NO
```

## Ownership and non-actions

```text
FROUROS_ADWIN_OWNER = UPSTREAM_LEAF
FROUROS_SOURCE_MODIFIED = NO
FROUROS_SOURCE_COPIED = NO
AQ_FROUROS_ADAPTER_CREATED = NO
AQ_FINANCIAL_DECAY_POLICY_CREATED = NO
AQ_DRIFT_ENGINE = NO
AQ_METRIC_ENGINE = NO
AQ_WORKFLOW_ENGINE = NO
AQ_STATE_DATABASE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
ALPHAGEN_EXECUTED = NO
RD_AGENT_EXECUTED = NO
QLIB_TRAINING_EXECUTED = NO
QLIB_PREDICTION_EXECUTED = NO
HISTORICAL_TEST_ACCESSED = NO
SEALED_OOS_ACCESSED = NO
P2_CERTIFICATION_EXECUTED = NO
REAL_LIFECYCLE_TRANSITIONS_EXECUTED = NO
```

## Private evidence

```text
PRIVATE_REPORT = D:/AQ_DATA/P4/selected-upstream-components-deployment-001/deployment_summary.json
PRIVATE_REPORT_SHA256 = 0e5534ff3f17f203e4085fec44e3e598dad173ef3449a81f32d17f24c17a242d
```

The private evidence root contains the authority snapshot, environment
creation evidence, full runtime freeze, package inventory, distribution and
installed-file provenance, public API check, offset proof, exact POC replay,
determinism/state evidence, and resource baseline.

## Next

```text
CURRENT_NEXT = P4_FROUROS_THIN_EVIDENCE_ADAPTER_001
```

The next task may implement only:

```text
validated Qlib metric observation
→ explicit constant-translation provenance
→ public Frouros ADWIN call
→ immutable detector evidence
```

Detector math and lifecycle/financial decision policy remain prohibited.
