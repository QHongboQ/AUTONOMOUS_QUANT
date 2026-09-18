# P2 Formulaic Alpha Certification Protocol Expansion 001

Status: **PASS — V2 FROZEN, NOT ACTIVATED**

Date: 2026-09-18

## Authority result

```text
TASK = AUTONOMOUS-QUANT-P2-FORMULAIC-ALPHA-CERTIFICATION-PROTOCOL-EXPANSION-001
PRIOR_HEAD = e98ad39c1c96f71636f6c6145e1418fed9de5216
ORIGIN_MAIN = d6215b19df989b32aa1151d935a4ef6399424c08
PROTOCOL_V1_MODIFIED = NO
V1_ACTIVATION_MODIFIED = NO
PROTOCOL_V2_CREATED = YES
PROTOCOL_V2_VERSION = P2_CERTIFICATION_PROTOCOL_V2
PROTOCOL_V2_STATUS = FROZEN_PENDING_MAIN_ACTIVATION
PROTOCOL_V2_ACTIVATED = NO
```

Protocol V1 remains the immutable active authority for its original Candidate.
Its activation start is still 2026-09-14, its minimum sealed-OOS window is
still 126 sessions, and its one-shot release and Candidate inventory are
unchanged. Protocol V2 creates a separate Formulaic Alpha cohort and does not
inherit V1's elapsed OOS clock.

## Frozen Formulaic cohort

```text
CANDIDATE_CONTRACT_VERSION = P3_CANDIDATE_TO_P2_CONTRACT_V3
PRODUCER_KIND = FORMULAIC_ALPHA
ENGINE = ALPHAGEN
FORMULAIC_COHORT_COUNT = 17
FORMULAIC_CANDIDATE_ID_UNIQUE_COUNT = 17
COHORT_MANIFEST = 40-certification-system/protocol/p2-formulaic-alpha-v2-candidate-cohort.json
COHORT_MANIFEST_SHA256 = 53920302856592fb43bbffb011423731893ac0a995a04194541c39d69ecfde70
V3_MATERIALIZATION_MANIFEST_SHA256 = 511ef7c25e55afc9cded8d6b2f13ed2715d248705c8cbad71918802d5210b8fd
V3_VALIDATION_REPORT_SHA256 = efbbfd90d5068ddb49a787a08e3f8b5f9da526ae7b22fc326e976adf033473db
FROZEN_DISCOVERY_CANDIDATE_MANIFEST_SHA256 = de536d7396f6786ea7b27c6a2f5f0970826ce7894b1e17d80361bf11085ff145
PERFORMANCE_FIELDS_IN_COHORT_MANIFEST = 0
```

The tracked cohort contains only the 17 lexicographically sorted Candidate V3
IDs and their identity/provenance authorities. Addition, removal, substitution,
post-hoc reduction, and pre-release re-ranking are prohibited. A cohort change
requires Protocol V3 or a later explicit protocol version. Candidate V3's
creation-time `INELIGIBLE_REQUIRES_PROTOCOL_EXPANSION` field remains untouched;
V2 eligibility is an external P2 overlay.

## Multiplicity and consumed historical evidence

```text
ALPHAGEN_SEEDS = 3
EXPRESSIONS_GENERATED_TOTAL = 7993
EXPRESSIONS_EVALUATED_TOTAL = 2720
UNIQUE_FINAL_EXPRESSIONS = 60
CORRELATION_CLUSTERS = 17
FROZEN_CERTIFICATION_COHORT = 17
HIDDEN_TRIAL_REMOVAL = PROHIBITED
HISTORICAL_TEST_STATUS = CONSUMED_AS_RESEARCH_EVIDENCE
HISTORICAL_TEST_EFFECTIVE_RANGE = 2022-01-03 THROUGH 2024-12-27
HISTORICAL_TEST_USED_FOR_V2_SELECTION = NO
HISTORICAL_TEST_ACCESSED_THIS_TASK = NO
HISTORICAL_TEST_PERFORMANCE_ACCESSED = NO
```

Historical TEST is not pristine OOS, is not certification evidence, cannot be
relabeled, and cannot select a V2 subset. All 17 enter the future cohort with
equal preregistered status.

## Frozen model, strategy, and control

```text
MODEL_WRAPPER = MICROSOFT_QLIB LinearModel(estimator=ols)
CANDIDATE_ALPHA_SOURCE = EXACT_CANDIDATE_V3_ALPHAGEN_EXPRESSION_IDENTITY
STRATEGY_WRAPPER = MICROSOFT_QLIB TopkDropoutStrategy(topk=30,n_drop=3)
STATISTICAL_CONTROL = MICROSOFT_QLIB LinearModel(estimator=ols) Alpha158-compatible control
CONTROL_STRATEGY_PROJECTION = COMMON_V2_TOPK30_NDROP3_FOR_CANDIDATE_CONTROL_COMPARABILITY
PARAMETER_ROBUSTNESS_POLICY = V1_P0_THROUGH_P4_INHERITED_FROZEN
COST_STRESS_POLICY = V1_BASE_2X_3X_INHERITED_FROZEN
```

The model family and upstream owners are unchanged from completed Qlib and P2
authority. Every Candidate and the statistical control use the same frozen
strategy projection for comparable net-return evidence. No hyperparameter or
strategy selection used Formulaic TEST performance.

## Family-aware multiple testing

```text
MULTIPLE_TESTING_OWNER = ARCH_8.0.0
REQUIRED_PROCEDURES = SPA; RealityCheck; StepM; MCS
FAMILY_GATES = SPA; RealityCheck
CANDIDATE_WISE_GATES = StepM superior-set membership; MCS 95% set membership
CERTIFICATION_MULTIPLICITY = ZERO_ONE_OR_MULTIPLE_CANDIDATES_MAY_BE_CERTIFIED
P2_SELECTS_CHAMPION = NO
```

The full 17-member family is evaluated against one preregistered control.
Family-aware gates are applied before Candidate-wise status. P2 may eventually
issue zero, one, or multiple `CERTIFIED` results; P4 owns later Shadow and
Champion decisions.

## Independent V2 sealed OOS boundary

```text
V2_SEALED_OOS_START_RULE = THE_FIRST_XNYS_SESSION_STRICTLY_AFTER_THE_PROTOCOL_V2_FREEZE_COMMIT_BECOMES_PART_OF_ORIGIN_MAIN
V2_SEALED_OOS_START_SESSION = UNRESOLVED_PENDING_MAIN_ACTIVATION
PRE_ACTIVATION_SESSIONS_COUNT = 0
MINIMUM_SEALED_OOS_SESSIONS = 126
ONE_SHOT_RELEASE = YES
EARLY_RESULT_ACCESS = PROHIBITED
INTERMEDIATE_PEEK = PROHIBITED
CANDIDATE_BY_CANDIDATE_EARLY_RELEASE = PROHIBITED
REUSE_FOR_RETUNING = PROHIBITED
```

The pending activation record contains no fabricated merge SHA or date. A
later merge-gate task must prove the exact freeze commit is in `origin/main`,
then resolve the first XNYS session strictly after that merge. Sessions before
activation do not count retroactively.

## DVC reproducibility

```text
DVC_VERSION = 3.67.1
DVC_STAGE_NAME = p2_formulaic_alpha_protocol_v2_freeze
DVC_REPRO_1 = PASS
DVC_REPRO_2 = UNCHANGED_DATA_AND_PIPELINES_UP_TO_DATE
DVC_YAML_SHA256 = 901e3d1a0b306b6a5769debee7a5561f4898318ea1b7391dd9ecf25fb2f49754
DVC_LOCK_SHA256 = 8e6b4354167516a465c4b4531fd44618b048c784e2ab4df053563b425fd7fcc0
DVC_STAGE_LOCK_ENTRY_IDENTITY = sha256:afe7d04397b7b69998e43c2b60c1d7174a537663e5ad16eac18d67fa92ee35e4
DVC_SEAL_OUTPUT_SHA256 = 135b7728ce73875a353ba7ddf833b3bc166420b2b15ddf571214a4cb4118cd98
DVC_OUTPUT_HASH = md5:9568a446316a91deed7b961bd5d3d628
```

The bounded seal verifies exact Protocol V2, cohort, pending activation,
Candidate V3 contract/materialization/validation, Formulaic DVC seal, provider
authority, Qlib model/control configuration, and strategy configuration. It is
an identity seal, not a protocol engine or certification executor.

## Safety and non-actions

```text
SEALED_OOS_ACCESSED = NO
V1_SEALED_OOS_ACCESSED = NO
V2_SEALED_OOS_ACCESSED = NO
FUTURE_MARKET_DATA_ACCESSED = NO
MODEL_TRAINING = NO
NEW_PREDICTIONS = NO
BACKTEST = NO
WALKFORWARD_EXECUTED = NO
CPCV_EXECUTED = NO
SPA_EXECUTED = NO
REALITYCHECK_EXECUTED = NO
STEPM_EXECUTED = NO
MCS_EXECUTED = NO
CERTIFICATION_DECISION_EXECUTED = NO
CERTIFIED_CANDIDATE_COUNT = 0
AQ_PROTOCOL_ENGINE = NO
AQ_STATISTICS_ENGINE = NO
AQ_MODEL_ENGINE = NO
AQ_BACKTEST_ENGINE = NO
AQ_EXPERIMENT_REGISTRY = NO
AQ_STATE_DATABASE = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

P4 contracts and policies were not modified. No Candidate, Certified, Shadow,
Champion, degradation, retirement, trading, or capital evidence was created.

## Identities and next

```text
PROTOCOL_V2_SHA256 = 18b80277b6529422298e43681bb344e54199a58477cdba20d96fd8220bdc950a
PRIVATE_REPORT = D:/AQ_DATA/P2/formulaic-alpha-certification-protocol-expansion-001/expansion_summary.json
PRIVATE_REPORT_SHA256 = 1694ec0360f610be0e7d37cfdadbc273618a94c059743ef4f788ab08f6a1ad94
FORMULAIC_V3_P2_ELIGIBILITY = ELIGIBLE_PENDING_PROTOCOL_V2_ACTIVATION
ACTIVATION_BLOCKED_PENDING_MAIN_MERGE = YES
CURRENT_NEXT = P2_FORMULAIC_ALPHA_PROTOCOL_V2_ACTIVATION_MERGE_GATE_001
```

This task does not execute the merge gate or activate Protocol V2.
