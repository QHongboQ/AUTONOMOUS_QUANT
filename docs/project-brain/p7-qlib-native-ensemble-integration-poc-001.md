# P7 Qlib-Native Ensemble Integration POC 001

## Decision

The smallest research-only integration with Microsoft Qlib's pinned
`AverageEnsemble` passes on deterministic synthetic inputs. This establishes
local API and boundary readiness only. It does not establish empirical signal
complementarity, real-input compatibility, an ensemble artifact, or P7 exit.

```text
BASE_MAIN = 9bec60b41f464d827de0d89b95d7e644bc4e3fe6
P7_CURRENT_STATUS = ACTIVE_RESEARCH_INTEGRATION_AND_INPUT_QUALIFICATION
P7_EXIT_CONDITION_SATISFIED = NO
SIGNAL_COMPLEMENTARITY = NOT_YET_ESTABLISHED
P8_STATUS = EARLY_DESIGN_EVIDENCE_ONLY_NO_IMPLEMENTATION
```

This current authority supersedes only the inference in the historical
[P7 entry audit](p7-multi-alpha-ensemble-entry-audit-001.md) that one common
AlphaGen producer identity prevents combination research from beginning. The
17 candidates remain one `FORMULAIC_ALPHA` producer family; they are not
relabelled as 17 independent economic families. Producer, economic-family and
empirical-diversification identities remain distinct. The historical
[P8 entry audit](p8-portfolio-risk-entry-audit-001.md) remains early design
evidence and does not authorize P8 implementation.

## Ownership and runtime

```text
CAPABILITY = CROSS_SECTIONAL_PREDICTION_STANDARDIZATION_AND_AVERAGING
PRODUCTION_OWNER = MICROSOFT_QLIB
OWNERSHIP_MODE = UPSTREAM_WHOLE
AQ_ALLOWED_SCOPE = STRICT_RESEARCH_INPUT_VALIDATION_AND_OUTPUT_SHAPE_CONVERSION
CUSTOM_ENGINE_REQUIRED = NO
UPSTREAM_CLASS = qlib.model.ens.ensemble.AverageEnsemble
QLIB_VERSION = 0.9.8.dev26
QLIB_SOURCE_SHA = 2fb9380b342556ddb50a4b24e4fe8655d548b2b8
QLIB_IMPORT_PATH = /home/zhou/miniforge3/envs/rdagent4qlib/lib/python3.10/site-packages/qlib/model/ens/ensemble.py
QLIB_PYTHON_VERSION = 3.10.21
QLIB_PANDAS_VERSION = 2.3.3
QLIB_NUMPY_VERSION = 2.2.6
STATISTICS_RUNTIME = /home/zhou/AQ_ENVS/p5-h1-statistics
SKFOLIO_VERSION = 1.0.6
ARCH_VERSION = 8.0.0
EXISTING_RUNTIME_REUSED = YES
ENVIRONMENT_MUTATED = NO
NEW_DEPENDENCY_COUNT = 0
```

The research boundary validates flat, explicitly named, same-index, one-score
inputs before calling the public upstream class directly. It rejects missing,
non-finite, duplicate, mismatched, unsorted, constant or under-populated
cross-sections. Qlib continues to own standardization and averaging. AQ does
not implement either operation.

Pinned Qlib actually returns an unnamed `Series`, despite its `DataFrame`
annotation. It flattens nested dictionaries. For incomplete inputs, native
`concat` plus row-wise `mean` forms a union and can silently skip a missing or
constant component at a row. Those are upstream semantics, not upstream
rejections. The strict AQ research boundary rejects those cases before the
call and converts only the valid unnamed Series to a one-column `score`
DataFrame.

## Metadata-only frozen input inventory

The Candidate V3 materialization manifest is
`511ef7c25e55afc9cded8d6b2f13ed2715d248705c8cbad71918802d5210b8fd`.
All 17 Candidate JSON byte hashes match it. Without deserializing prediction
values, all 17 recorded native prediction paths exist and match their recorded
SHA-256 identities.

Common prediction root:
`D:/AQ_DATA/P3/alphagen-us-pit-qlib-candidate-evaluation-001/mlruns/1/`.
Each relative path below is `<run_id>/artifacts/pred.pkl`.

| Candidate | Candidate V3 identity | Qlib run | Prediction SHA-256 |
| --- | --- | --- | --- |
| candidate-001 | `sha256:de6ecb854a360ffe185ab055df5220d581da8a5e8c14f1a1adf24ef4cc60d577` | `7083335c381f45e08de7c359d9e5cdf4` | `6f94bbd7aa14e5b8abfd810b27cf0f10521d9d1a7f615470776ba5a13bfdd3ce` |
| candidate-002 | `sha256:5f3c9e5f6ce0a1fdf38d87ab6a4609d94f3e170e70008c4289ef3828898e9b5d` | `bc959cd2274a4d4db921682aa6c46f29` | `6cf5f69b5fb3358ec3725219806a55e44ae39cded37e98b45cc409225222e558` |
| candidate-003 | `sha256:e36c1cd6a92ee4b078cdf3e514f839739d74a72940596c0377dcb6bbbeeb3e16` | `71a32ed40e5a4f6bab77b77971c6a323` | `a5f8a0bf419a3cc10be5a2b2135703793649e4f698886a4c02dacdcbb7045bce` |
| candidate-004 | `sha256:5e2c2e5746a020393ced636cbae76d612aaf9334cfa2ea4addd6dd6ba1960d85` | `45d6b869fa2b4149a4f34c0b53391df3` | `6d95d4910386802ec8bc0cd0495e6a4bb89b4703571c16f7c154152a8c24b092` |
| candidate-005 | `sha256:f8409ded53d351c83de386794cf7fbf383813805cf7c60bd112dbb8fae1dc1cc` | `4debf3dad7894515acb87e276bb83d61` | `51952a9d5ea12aae48df6121a6522f42e55ee53af767a1af40eed30e945676a9` |
| candidate-006 | `sha256:aad1eaafe206dfa683dfd47934b17fa0d16df65fcf7b967534f19f518ba3a81b` | `c094bffc18714f139e426264ffb062a7` | `891327baf5c52a6ee8f5c9da043070ac7c54d48bdd6aa62c628909de1395a2b7` |
| candidate-007 | `sha256:80662d497b6e0da7f60f528d56e3048f20fa3531a1f179fc36587784fbe104e7` | `2538173b74c8423b8f7531ce430754d1` | `dd732208e18da7c1ae26cb27872e9befef6eb5abf395230dc1a9c5ab5b2d5012` |
| candidate-008 | `sha256:7353d7a77ffb0883014e81b10457de323d4d300954be304f31c17c2b18230b15` | `0553b185b75849bb8e90cbc37a5dee17` | `86be2394545bb84a092e64153b1ad335969d4776860422b47a65b49f9ab89f76` |
| candidate-009 | `sha256:61ae57c774925c90836ba69ff0fbfdbaa0ef015127f61f3a5b6e6b7f063adb4c` | `4198334b5cb64734a2fb01975f8a7cea` | `2c7bdae6db795d1fc2b1736e7bba09af7dfafc9bba1e51e92b37bda72548b017` |
| candidate-010 | `sha256:89397f82c2361985cde1e73ce740e8da808d4db005bc28885dbd1ad4271c5d5d` | `ba423c10f5ff412c94dabde717dd580a` | `c5c735400f843049a49dc04095f417f0ac25991bf1bf51137140d0beee77039f` |
| candidate-011 | `sha256:99bdafc3e9f0b1c7f895810d50f398eac92a2f8805f33b87c7fa00347f344195` | `7e985ab0e671481aa1433e6caece44de` | `d5a5a506fec62ef76c76757cf574e3c89eb15434b0f77741bc57458067f5f6a4` |
| candidate-012 | `sha256:36ef2725aea4552dcbe35791fc63b4deed4c889197d12afcc272089e19fee33b` | `8629bb4e23794add9f532dd86725fe7a` | `056d2d66cc84e674789939fc4f4f601a85f15ddf9eab82251ac98fc320c57865` |
| candidate-013 | `sha256:c73944e9e3d16055e30d3ad5c3e1935450c32981aa3fc7408e0814662b9a88ec` | `b8c3a60542be485ba5bb794c5c3ca233` | `f86a5906821697852e347fa7f60cd393b2c043d717f8861fc4516d896cc1f41a` |
| candidate-014 | `sha256:644a49049888306381197754c95574f536fd98267766431afebd46ac0f600934` | `9e52d11e9726478b9aed1c71581384ad` | `fe9cbbdfa2c70fd1a497051ee1089e54db61718f6efaea782cb8de362ef6ffd3` |
| candidate-015 | `sha256:c21850f3f1ef47bc22ec70096622118216452ec550013f8c06874a3b6a851086` | `9fb63cb81cce4ffaa0e239342c898743` | `bc3b23a4e44bfacc2686142690303f8a7a4efb15b38fcb054465000dae02b679` |
| candidate-016 | `sha256:20f058b616bed7ce14c4c820e4742c92cafb10b12447a1706b90364137e87f0b` | `9d52ff767d6a4ebd99b2323c13b10834` | `570320e758cd3ea278613189bd89f2a5d28fdf33d697160f446f7aa9cb1fc01c` |
| candidate-017 | `sha256:1a0e410676276ef1a7381d94d7a13feace60969b8207f195e51ea77f23450719` | `52440edc24ef4a4cbc3037b8fe662e86` | `46e12a561f33f4ada8b15069263823e1cc436c65e02bacea7f4748d738793d88` |

All 17 share only the following declared metadata; no prediction values were
opened to establish empirical compatibility:

```text
MODEL = qlib.contrib.model.linear.LinearModel(estimator=ols)
FIT_POLICY = TRAIN_ONLY
DECLARED_PREDICTION_INTERVAL = 2022-01-03..2024-12-27
PREDICTION_COLUMN = score
LABEL = Ref($close, -2)/Ref($close, -1) - 1
LABEL_LOOKAHEAD_SESSIONS = 2
INFER_PROCESSORS = RobustZScoreNorm(feature,clip_outlier=True); Fillna(feature)
LEARN_PROCESSORS = DropnaLabel; CSRankNorm(label)
DATASET_INTERVAL = 2015-01-02..2024-12-31
P2_PIT_INSTRUMENTS_SHA256 = e771f73b91664b26584e66c42eb007c4276c492071172e7d6594bc900f01f875
DATASET_SECURITY_IDENTITY_COUNT = 730
MODEL_PERSISTENCE_STATUS = NOT_PERSISTED_BY_UPSTREAM
QLIB_RECORDER_STATUS = FINISHED_17_OF_17
```

The recorded prediction metadata does not carry an exact ordered row-identity
hash. The native artifacts were therefore not opened merely to infer their
keys, completeness, finite values, constancy or mutual common support.

## Potential control identities

`BASE_157` is a feature surface, not a prediction or model identity. Its
feature manifest is
`7d5fbec1e775e8ff7f03b45ab966443c7774a4052b41cbf0a2116e9c96241463`
and its dataset identity is
`P5_CONTROL_DATASET_IDENTITY_V1:08786931dc72b12226d092877fa20c78dff5fb054384a3b1595c1bd1579f8135`.

Two existing controls must not be conflated:

- P2 V2 declares an OLS Alpha158-compatible statistical control with model
  config identity
  `sha256:b9a92537a9737ce909284e77e583ad20c0a3d2b18f795271d85db6c5ba5eafc1`.
  This POC did not bind a prediction artifact to that control.
- P5 Attempt-005 produced a Qlib `LGBModel` `BASE_157` control prediction at
  `D:/AQ_DATA/P5/h1-incremental-fundamental-evaluation-and-closeout-001/attempt-005-final-end-to-end/s0-prediction.pkl`.
  Its existing SHA-256 is
  `52d7f8bbf56ff565f5b77584786f59c3279e31895d54e42bbf0183246a950df6`
  and was reverified without deserializing it. Its surface manifest orders
  rows by `datetime, episode_id`; an exact P7 prediction-key and interval
  contract is not recorded here.

```text
CONTROL_IDENTITY_STATUS = PARTIAL_EXISTING_IDENTITIES_REQUIRE_ONE_EXPLICIT_P7_CONTROL_BINDING
REAL_INPUT_COMPATIBILITY_STATUS = NOT_VERIFIED_METADATA_ONLY
PREDICTION_ARTIFACT_IDENTITY_VERIFIED_COUNT = 17
CONTROL_PREDICTION_ARTIFACT_IDENTITY_VERIFIED_COUNT = 1
```

## Synthetic integration and split feasibility

The focused suite passed 15/15 tests. Eight successful synthetic calls reached
the upstream ensemble: one hand calculation, three repeatability/order calls,
one return-type call, one incomplete-input characterization and two
flat/nested calls. Boundary-failure cases were rejected before Qlib.

```text
SYNTHETIC_ENSEMBLE_CALL_COUNT = 8
SYNTHETIC_TEST_PASS_COUNT = 15
SYNTHETIC_TEST_FAIL_COUNT = 0
HAND_CALCULATION = PASS
INDEX_PRESERVATION = PASS
REPEATABILITY = PASS
COMPONENT_ORDER_INVARIANCE = PASS
INPUT_IMMUTABILITY = PASS
FAIL_CLOSED_BOUNDARIES = PASS
NATIVE_INCOMPLETE_INPUT_BEHAVIOR = UNION_AND_SKIPNA_CHARACTERIZED_NOT_ADMITTED
NATIVE_NESTED_DICTIONARY_BEHAVIOR = FLATTENED_CHARACTERIZED_NOT_USED_BY_BOUNDARY
```

In skfolio 1.0.6, synthetic WalkForward with `train_size=504`,
`purged_size=2`, `test_size=63`, `reduce_test=False` yields three complete
504/63 folds from 700 observations. At 568 observations the upstream minimum
guard does not raise but yields zero folds; the POC treats that as infeasible.
At 385 observations it raises before yielding a fold, confirming the prior
FinSen negative example without reopening or rerunning FinSen. Synthetic CPCV
with 100 observations, 10 folds, two test folds, purge 2 and embargo 2 yields
45 splits, each with two nonempty ten-observation test folds and at least 68
training observations.

```text
SYNTHETIC_SPLIT_FEASIBILITY_RESULT = PASS_MECHANICS_PROVEN_PARAMETERS_NOT_FROZEN_FOR_P7
WALKFORWARD_SYNTHETIC_OBSERVATIONS = 700
WALKFORWARD_YIELDED_FOLD_COUNT = 3
WALKFORWARD_ZERO_FOLD_BOUNDARY_OBSERVATIONS = 568
HISTORICAL_385_NEGATIVE_TEST = PASS_REJECTED
CPCV_SYNTHETIC_OBSERVATIONS = 100
CPCV_YIELDED_SPLIT_COUNT = 45
TEMPORAL_ROBUSTNESS_VS_ROLLING_REFIT = DISTINCT_NOT_INTERCHANGEABLE
P7_STATISTICAL_PROTOCOL_FROZEN = NO
```

These splitters partition an existing observation/return series. They do not
perform rolling model fitting or generate out-of-sample predictions.

## Remaining blockers and immutable boundaries

Before any real ensemble execution, a separate authority must bind one control
identity; establish exact ordered row-key/common-support metadata across every
admitted component; test real completeness, finiteness and nonconstancy
without outcome-based selection; freeze component/weight/statistical policy;
and create a new ensemble identity with explicit certification authority.
Signal complementarity remains unmeasured. The missing upstream model bytes
must not be invented. A future ensemble is not added to the frozen P2 V2
17-member cohort and does not inherit its sealed-OOS clock.

```text
REAL_MODEL_TRAINING_COUNT = 0
REAL_PREDICTION_GENERATION_COUNT = 0
REAL_ENSEMBLE_EXECUTION_COUNT = 0
BACKTEST_COUNT = 0
PERFORMANCE_METRICS_COMPUTED = 0
P2_SEALED_OOS_ACCESSED = NO
P2_COHORT_MODIFIED = NO
BROKER_ACTION_COUNT = 0
PRODUCTION_ACTIVATION_AUTHORIZED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
NEXT_TASK = P7_REAL_DATA_ENSEMBLE_INPUT_CONTRACT_AND_PROTOCOL_FEASIBILITY_001
FINAL_CLASSIFICATION = PASS_P7_QLIB_NATIVE_ENSEMBLE_INTEGRATION_POC_REAL_INPUT_QUALIFICATION_PENDING
```
