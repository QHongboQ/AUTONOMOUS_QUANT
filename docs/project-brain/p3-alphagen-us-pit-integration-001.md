# P3 AlphaGen US PIT Integration 001

## Result

The successful bounded AlphaGen POC is now a modular P3 integration boundary.
AlphaGen remains `UPSTREAM_WHOLE`; its expression engine, RL environment, PPO
construction, factor pool, and IC/RankIC logic were neither copied nor
modified. The pinned upstream source remains clean at
`259687e8f316994426416c530a94842a2fe6405e`.

```text
ALPHAGEN_US_PIT_INTEGRATION = ACTIVE
ALPHAGEN_UPSTREAM_SHA = 259687e8f316994426416c530a94842a2fe6405e
ALPHAGEN_UPSTREAM_MODIFIED = NO
VWAP_FEATURE_SPACE_BLOCKER = CLOSED_RESOLVED_BY_SB3_ACTION_MASKER
P3_RUNTIME_POC_ALPHA = PROOF_ONLY_NOT_RESEARCH_EVIDENCE
```

## Module boundary

Reusable project code is restricted to five real responsibilities:

- `data_view.py` exposes the existing Qlib `p2_pit` provider as AlphaGen's
  OHLCV tensor surface, admits identities with a date-valid membership overlap,
  masks every off-membership observation, preserves provider NaNs, and excludes
  sealed OOS;
- `calculator.py` subclasses upstream `TensorAlphaCalculator` and binds the
  target directly to `P2_CERTIFICATION_PROTOCOL_V1` label-temporal authority;
  upstream `normalize_by_day()` remains the numerical owner and AQ restores
  only the authoritative missingness mask afterward;
- `feature_mask.py` composes upstream `ActionMasker` with AlphaGen's native
  mask and removes only `SIZE_OP + int(FeatureType.VWAP)`;
- `runner.py` only composes upstream `MseAlphaPool`, `AlphaEnv`, `MaskablePPO`,
  and `LSTMSharedNet` from explicit caller parameters;
- `research_config.py` defines the bounded official least-squares research
  configuration and fail-closed research-partition guards without adding a
  custom optimizer, factor pool, RL implementation, or PPO implementation.

The fixed dates, deterministic 32-instrument sample, 2,048-step budget, pool
capacity five, and JSON evidence writing live only in `run_bounded_poc.py`.
Serialization converts numeric values only after the upstream run completes;
it cannot affect AlphaGen runtime or factor values.

```text
AQ_US_PIT_DATA_VIEW = AQ_DOMAIN_SPECIFIC_THIN_ADAPTER
AQ_ALPHAGEN_CALCULATOR = AQ_DOMAIN_SPECIFIC_THIN_ADAPTER
AQ_FEATURE_AVAILABILITY_MASK = AQ_DOMAIN_SPECIFIC_THIN_ADAPTER
AQ_ALPHAGEN_RUNNER = AQ_DOMAIN_SPECIFIC_THIN_COMPOSITION
SERIALIZATION_FIX_SCOPE = EVIDENCE_ONLY
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

There is no circular dependency and no copied AlphaGen implementation.

## Validation

All 18 focused tests pass. They cover OHLCV orientation, frozen target and
two-session alignment, protocol-drift rejection, date-valid PIT membership,
sealed-OOS rejection, expression semantics, VWAP-only mask delta,
deterministic POC sampling, module imports, ragged membership masking, NaN
preservation, partition purging, the historical-TEST guard, the fixed fast
configuration, and the upstream least-squares branch.

One authorized structural-parity run used the same seed, provider, dates,
mask, 32 instruments, and 2,048-step budget as the accepted POC. It initialized
the real upstream RL stack, completed all 2,048 actions, generated nine
expressions, evaluated seven, admitted five, selected VWAP zero times, and
accessed zero sealed-OOS rows. The output is runtime proof only, not factor
quality or certification evidence.

Private evidence is frozen under:

`D:/AQ_DATA/P3/alphagen-us-pit-integration-001/`

The SHA-256 of `integration_summary.json` is:

`28cc750721f7d8a61e44e107cd5ddf12bf6149aec934562c8fc9b9a28204d2a7`

```text
ALPHAFORGE_AND_ALPHAGPT = CHALLENGERS_NOT_CURRENT_MAINLINE
RD_AGENT_LOCAL_BRAIN_SEARCH = PAUSED_NOT_P3_BLOCKER
AUTONOMOUS_ATTEMPT_004_AUTHORIZED = NO
PRIOR_DISCOVERY_RUN_001 = ABORTED_RESOURCE_CALIBRATION_INVALID
ROOT_CAUSE = UPSTREAM_L1_POOL_OPTIMIZATION_NONLINEAR_COST
RAGGED_PIT_CORRECTNESS = PASS
ALPHAGEN_MSE_LSTSQ_FAST_V1 = QUALIFIED
ALPHAGEN_MSE_L1_REFERENCE_V1 = REFERENCE_RESOURCE_EXPENSIVE
ALPHAGEN_FACTOR_DISCOVERY_LSTSQ_RUN_001 = PASS
P3_RESEARCH_ALPHA_CANDIDATE_COUNT = 17
HISTORICAL_TEST_ROWS_ACCESSED = 0
SEALED_OOS_ROWS_ACCESSED = 0
CURRENT_NEXT = P3_ALPHAGEN_US_PIT_QLIB_CANDIDATE_EVALUATION_001
```
