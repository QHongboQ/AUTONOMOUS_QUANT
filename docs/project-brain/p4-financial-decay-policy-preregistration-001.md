# P4 Financial Decay Policy Preregistration 001

## Authority state

```text
TASK = AUTONOMOUS-QUANT-P4-FINANCIAL-DECAY-POLICY-PREREGISTRATION-001
RESULT = PASS
P4_FINANCIAL_DECAY_POLICY_PREREGISTRATION = PASS
P4_PRODUCTION_DECAY_POLICY_STATUS = PREREGISTERED
CURRENT_NEXT = P4_SHADOW_EVIDENCE_PATH_AND_QLIB_ONLINE_INTEGRATION_001
```

This task froze the first production financial-decay interpretation policy
before any prospective Shadow observation was available. It did not certify a
Candidate, observe real Candidate RankIC, access historical TEST or sealed OOS,
or authorize capital or trading.

## Frozen ownership

```text
RANK_IC_COMPUTATION_OWNER = QLIB
CHANGE_DETECTION_OWNER = FROUROS_ADWIN
EXPERIMENT_IDENTITY_OWNER = QLIB_MLFLOW
REPRODUCIBILITY_OWNER = DVC
FINANCIAL_INTERPRETATION_OWNER = AQ_THIN_POLICY
SCHEDULER_OWNER = P12

ADDITIONAL_UPSTREAM_DEPLOYMENT = NO
AQ_METRIC_ENGINE = NO
AQ_DRIFT_ENGINE = NO
AQ_WORKFLOW_ENGINE = NO
AQ_SCHEDULER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

Qlib remains the only RankIC computation authority. Frouros remains the sole
ADWIN mathematics owner with its audited configuration unchanged:

```text
clock = 32
delta = 0.002
m = 5
min_window_size = 5
min_num_instances = 10
FROUROS_CONFIG_MODIFIED = NO
```

## MLflow last-mile decision

Installed MLflow `3.16.0` exposes `MetricThreshold` and
`validate_evaluation_results` as candidate-model validation against a baseline.
`min_absolute_change` requires the candidate to improve in the configured
direction. Expressing “current RankIC deteriorated from the historical
reference” would therefore require semantically inverting candidate and
baseline. The transparent P4 predicate is smaller and faithful to the domain.

```text
MLFLOW_METRIC_THRESHOLD_FOR_DECAY = NOT_SELECTED_SEMANTIC_MISMATCH_FOR_DEGRADATION_DIRECTION
MLFLOW_MODEL_ALIAS = AVAILABLE_FOR_REGISTERED_PERSISTED_MODELS_ONLY
```

This is consistent with the [official MLflow validation source and API](https://mlflow.org/docs/latest/api_reference/_modules/mlflow/models/evaluation/validation.html).

## Source review and numeric limits

[Qlib Recorder documentation](https://github.com/microsoft/qlib/blob/main/docs/component/recorder.rst)
and the [Qlib record-template source](https://github.com/microsoft/qlib/blob/main/qlib/workflow/record_temp.py)
confirm that Qlib owns the prediction/label calculation and persistence of the
per-date RankIC series. [Official Qlib benchmarks](https://github.com/microsoft/qlib/blob/main/examples/benchmarks/README.md)
provide magnitude context only; they do not prescribe a production decay
threshold.

The original [ADWIN paper](https://www.cs.upc.edu/~Gavalda/papers/adwin06.pdf)
supports adaptive statistical change detection, not a financial demotion
meaning. McLean and Pontiff's peer-reviewed evidence documents out-of-sample
and post-publication predictor decay ([Journal of Finance DOI](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365)),
while Harvey, Liu, and Zhu document multiple-testing risk in cross-sectional
return research ([NBER paper and published reference](https://www.nber.org/papers/w20592)).
Neither source supplies a universal RankIC deterioration magnitude, window, or
persistence count for this system.

The numeric choices below are therefore explicitly first-principle,
upstream-constraint, and conservative-governance choices. They are not claimed
as literature optima and were not selected against actual AQ performance.

## Frozen production policy

```text
SUPPORTED_METRIC = RANK_IC_ONLY
PRODUCTION_POLICY_VERSION = FinancialDecayPolicyConfigV2
PRODUCTION_POLICY_ID = sha256:3b95c4671bf75c933437659b971477ae6241f70428c638ae81690c4aa6182854
PRODUCTION_POLICY_SHA256 = 1cb73a05d9f36d8df66a8b044778d37f1812902ad8c2b3c1560b191955053c78
PRODUCTION_POLICY_EFFECTIVE_EPOCH = 2026-10-01

REFERENCE_SAMPLE_SESSIONS = 252
CURRENT_SAMPLE_SESSIONS = 63
POLICY_EVALUATION_CADENCE = 21_XNYS_SESSIONS
MINIMUM_DETERIORATION = 0.03_ABSOLUTE_RANK_IC
MINIMUM_REFERENCE_SAMPLE_COUNT = 252
MINIMUM_CURRENT_SAMPLE_COUNT = 63
REQUIRED_CHANGE_EVENTS = 1
REQUIRED_PERSISTENCE_EVIDENCE_COUNT = 3
CORROBORATION_REQUIRED = YES
```

The 252-session reference is frozen for the monitored Champion. The current
window is the trailing 63 XNYS sessions ending at the explicit evidence
cutoff. Evaluations occur every 21 XNYS sessions. Three consecutive eligible
evaluations must each meet the financial materiality and sample requirements.
A Frouros alert never demotes by itself.

The reference ends before the current window begins. Every prospective current
window must begin on or after `2026-10-01`. Pre-epoch observations may establish
the frozen reference but are not counted as prospective validation evidence.
Scheduling remains a P12 responsibility; P4 receives immutable upstream
summaries and does not implement a rolling or scheduling engine.

The selected `0.03` absolute deterioration is a deliberately material
conservative-governance hurdle. It is not a fitted estimate. The general
directional rule is sufficient for sign reversal:

```text
current_rank_ic < reference_rank_ic
AND
reference_rank_ic - current_rank_ic >= 0.03
```

No sign-specific branch exists.

## Versioning and immutability

V1 remains unchanged with only `UNSET_REQUIRES_PREREGISTRATION` and
`TEST_ONLY_POLICY_CONFIG`. V2 adds the minimum fields required for a real
production policy: policy identity, effective epoch, window/cadence semantics,
and the frozen thresholds. The JSON policy is validated by Pydantic and the V2
JSON Schema. Its semantic identity is SHA-256 over RFC 8785 bytes of all
non-ID fields. The exact policy-file bytes have their own SHA-256.

```text
RETROACTIVE_THRESHOLD_REWRITE = PROHIBITED
FUTURE_THRESHOLD_CHANGE_REQUIRES = NEW_VERSION; NEW_POLICY_ID; EXPLICIT_RATIONALE; NEW_EFFECTIVE_EPOCH
RETROACTIVE_SHADOW_RELABELING = PROHIBITED
AQ_POLICY_REGISTRY = NO
```

## Synthetic sanity check

The eight-scenario matrix was frozen before analysis. Only deterministic
synthetic RankIC streams were used.

```text
STABLE_HEALTHY = NO_CHANGE
NOISY_HEALTHY = NO_CHANGE
SMALL_TEMPORARY_DROP = NO_CHANGE
TEMPORARY_SHOCK_RECOVERY = NO_CHANGE
PERSISTENT_SMALL_DETERIORATION = NO_CHANGE
PERSISTENT_MATERIAL_DETERIORATION = MARK_DEGRADED
SIGN_REVERSAL = MARK_DEGRADED
GRADUAL_DECAY = MARK_DEGRADED

SYNTHETIC_SCENARIO_COUNT = 8
SENSITIVITY_SANITY_CHECK = PASS_8_OF_8_PREREGISTERED_SCENARIOS
```

Sensitivity variants at `0.02` and `0.04` materiality and two/four
confirmations were recorded only to expose obvious pathologies. They did not
select or optimize the already-declared policy.

## Validation and firewalls

```text
V2_FOCUSED_TESTS = 16/16_PASS
RESIDUAL_POLICY_TESTS = 47/47_PASS
QLIB_EXPORTER_AND_FULL_ADAPTER_TESTS = 12/12_PASS
FROUROS_RUNNER_TESTS = 8/8_PASS
IDENTITY_PROJECTION_TESTS = 14/14_PASS
TEST_RESULT = 81/81_PASS

ALPHAGEN_HISTORICAL_TEST_METRICS_ACCESSED = NO
REAL_CANDIDATE_RANKIC_ACCESSED = NO
SEALED_OOS_ACCESSED = NO
REAL_SHADOW_EVIDENCE_ACCESSED = NO
QLIB_REAL_CANDIDATE_RECORDER_ACCESSED = NO
REAL_DATA_USED_FOR_THRESHOLD_SELECTION = NO

P2_PROTOCOL_MODIFIED = NO
REAL_CERTIFIED_ARTIFACT_COUNT = 0
FORMULAIC_ALPHA_P2_PROTOCOL_EXPANSION = STILL_REQUIRED

NEW_DEPENDENCY_COUNT = 0
AQ_THRESHOLD_ENGINE = NO
AQ_METRIC_ENGINE = NO
AQ_DRIFT_ENGINE = NO
AQ_POLICY_REGISTRY = NO
AQ_STATE_DATABASE = NO
AQ_SCHEDULER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Private evidence

```text
PRIVATE_REPORT = D:/AQ_DATA/P4/financial-decay-policy-preregistration-001/preregistration_summary.json
PRIVATE_REPORT_SHA256 = c5d852de5873c87ae5fff68d29f3ad07da2d05be7a026e074506523545616f82
PRODUCTION_POLICY_SHA256 = 1cb73a05d9f36d8df66a8b044778d37f1812902ad8c2b3c1560b191955053c78
```

The private directory contains exactly the required authority, source,
semantics, preregistered scenario, sensitivity, rationale, policy, identity,
negative-test, and summary artifacts. It contains no real Candidate metrics.

## Next

```text
CURRENT_NEXT = P4_SHADOW_EVIDENCE_PATH_AND_QLIB_ONLINE_INTEGRATION_001
```

The next task may connect prospective Qlib OnlineManager/Recorder evidence and
zero-capital Shadow observations. It may not change these thresholds based on
those observations.
