# P3 AlphaGen US PIT Qlib Candidate Evaluation 001

## Result

```text
P3_ALPHAGEN_QLIB_CANDIDATE_EVALUATION = PASS
ALPHAGEN_HISTORICAL_TEST_STATUS = CONSUMED_AS_RESEARCH_EVIDENCE
FROZEN_CANDIDATE_COUNT = 17
QLIB_RECORDERS_FINISHED = 17
PREDICTION_ARTIFACTS_CREATED = 17
P2_CERTIFICATION_EXECUTED = NO
CERTIFIED_FACTOR_COUNT = 0
SEALED_OOS_ROWS_ACCESSED = 0
```

This task independently evaluated the 17 already-frozen AlphaGen cluster
representatives on the historical research TEST partition. It did not rerun
discovery, change the candidate inventory, tune the model, run a portfolio
backtest, certify a factor, or access sealed OOS.

## Frozen authority

The source discovery report remained byte-identical at
`5212564ed15b3fa15bde40f14b9fe9a067b725bc5dd472a6046af0013893523a`.
Before any TEST factor values or metrics were opened, the 17 representatives,
their exact expressions, origin seeds, and TRAIN/VALID IC and RankIC values
were sealed in the private candidate manifest.

```text
FROZEN_CANDIDATE_MANIFEST_SHA256 = de536d7396f6786ea7b27c6a2f5f0970826ce7894b1e17d80361bf11085ff145
HISTORICAL_TEST_AUTHORITY = 2022-01-03 THROUGH 2024-12-31
HISTORICAL_TEST_EFFECTIVE_RANGE = 2022-01-03 THROUGH 2024-12-27
LABEL_LOOKAHEAD_SESSIONS = 2
HISTORICAL_TEST_MEMBER_SESSION_ROWS = 377938
SEALED_OOS_START = 2026-09-14
```

The effective end prevents the two-session label from crossing the historical
TEST authority boundary.

## Upstream ownership and model policy

AlphaGen `259687e8f316994426416c530a94842a2fe6405e` remained the whole expression
engine. The existing AQ US PIT adapter supplied five channels, dynamic ragged
membership, preserved missing values, and prohibited VWAP. Factor values were
materialized with AlphaGen's upstream daily normalization while restoring the
authoritative missingness mask.

Microsoft Qlib `0.9.8.dev26` at
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8` owned `DatasetH`, preprocessing,
model fitting, prediction, Recorder/MLflow, and signal analysis. The control
was the already-authorized
`qlib.contrib.model.linear.LinearModel(estimator="ols")` from
`30-research-system/qlib/model-comparison/workflow_config_linear_Alpha158_US.yaml`.
Its upstream `include_valid=False` behavior and existing config establish
`FIT_POLICY = TRAIN_ONLY`; no TRAIN+VALID refit was invented.

All candidates used the same OLS configuration, label, partition boundaries,
`RobustZScoreNorm` and `Fillna` feature processors, and `DropnaLabel` plus
`CSRankNorm` learning processors. Only the single candidate feature changed.

```text
AQ_CUSTOM_MODEL = NO
AQ_CUSTOM_REGRESSION = NO
AQ_CUSTOM_RECORDER = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
```

## Complete historical TEST inventory

The sign flags below are the descriptive rules frozen before TEST access. They
are not certification or magnitude gates.

| Candidate | Cluster | Expression | VALID IC | VALID RankIC | TEST IC | TEST RankIC | IC sign | RankIC sign | Qlib recorder |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| candidate-001 | cluster-000 | `Abs(Abs(Abs(Sub(Mad(Sub(-0.01,Mean(Sub($open,$close),10d)),40d),5.0))))` | -0.004403137 | -0.007875442 | -0.001938306 | 0.001363297 | YES | NO | `7083335c381f45e08de7c359d9e5cdf4` |
| candidate-002 | cluster-001 | `Greater(Greater(Div(-30.0,$open),-10.0),-0.5)` | 0.009791759 | 0.014470517 | -0.002595269 | 0.002446802 | NO | YES | `bc959cd2274a4d4db921682aa6c46f29` |
| candidate-003 | cluster-002 | `EMA(Add(10.0,Add(Abs($low),-0.01)),10d)` | 0.006316433 | 0.014220138 | -0.001451798 | 0.003125021 | NO | YES | `71a32ed40e5a4f6bab77b77971c6a323` |
| candidate-004 | cluster-003 | `Add(-0.5,Less($close,10.0))` | -0.004179429 | 0.000074865 | -0.001128274 | -0.001756798 | YES | NO | `45d6b869fa2b4149a4f34c0b53391df3` |
| candidate-005 | cluster-004 | `Add(Div(-1.0,Less($close,10.0)),5.0)` | -0.003706795 | 0.000074865 | -0.001067479 | -0.001656276 | YES | NO | `4debf3dad7894515acb87e276bb83d61` |
| candidate-006 | cluster-005 | `Sub(Abs(Mul(-0.01,Min(Mul(Ref($open,5d),$open),5d))),Less(-1.0,$low))` | 0.002855845 | 0.014396629 | 0.000298251 | 0.003540357 | YES | YES | `c094bffc18714f139e426264ffb062a7` |
| candidate-007 | cluster-006 | `Div(-0.01,Min($volume,1d))` | -0.003755846 | -0.014129627 | -0.003296659 | -0.000278378 | YES | YES | `2538173b74c8423b8f7531ce430754d1` |
| candidate-008 | cluster-007 | `Div(-5.0,Log(Abs($volume)))` | -0.004194302 | -0.013691834 | -0.005375272 | -0.000258467 | YES | YES | `0553b185b75849bb8e90cbc37a5dee17` |
| candidate-009 | cluster-008 | `Div(1.0,Add(Log($open),-10.0))` | -0.007779497 | -0.013755119 | -0.001711725 | 0.002767504 | YES | NO | `4198334b5cb64734a2fb01975f8a7cea` |
| candidate-010 | cluster-009 | `Div(10.0,Less($close,10.0))` | 0.003706790 | 0.001105534 | -0.001185988 | -0.001756798 | NO | NO | `ba423c10f5ff412c94dabde717dd580a` |
| candidate-011 | cluster-010 | `WMA($volume,20d)` | 0.008800944 | -0.013857829 | -0.006775230 | 0.000022002 | NO | NO | `7e985ab0e671481aa1433e6caece44de` |
| candidate-012 | cluster-011 | `Greater(2.0,Abs(Less($close,5.0)))` | -0.000191141 | 0.001057436 | 0.024253335 | 0.015278635 | NO | YES | `8629bb4e23794add9f532dd86725fe7a` |
| candidate-013 | cluster-012 | `Greater(2.0,Delta(WMA($open,20d),5d))` | 0.002277318 | 0.004792986 | 0.002551465 | 0.000541655 | YES | YES | `b8c3a60542be485ba5bb794c5c3ca233` |
| candidate-014 | cluster-013 | `Less(5.0,EMA(Less($low,$volume),5d))` | 0.001061953 | 0.002326160 | 0.000838522 | -0.000696695 | YES | NO | `9e52d11e9726478b9aed1c71581384ad` |
| candidate-015 | cluster-014 | `Mul(-5.0,Less(Less(Abs($open),10.0),10.0))` | 0.004315125 | 0.000935496 | -0.001204856 | -0.001732568 | NO | NO | `9fb63cb81cce4ffaa0e239342c898743` |
| candidate-016 | cluster-015 | `Mul(Less(30.0,$close),-0.01)` | 0.001401163 | -0.006013634 | 0.004517723 | 0.000323351 | YES | NO | `9d52ff767d6a4ebd99b2323c13b10834` |
| candidate-017 | cluster-016 | `Sub(Less(-10.0,Add($low,-30.0)),0.01)` | -0.004663911 | 0.003112317 | -0.004321154 | -0.004732989 | YES | NO | `52440edc24ef4a4cbc3037b8fe662e86` |

```text
VALID_TEST_IC_SIGN_CONSISTENT_COUNT = 11
VALID_TEST_RANKIC_SIGN_CONSISTENT_COUNT = 7
```

All 17 results remain in the inventory. No candidate was promoted, removed, or
reselected after observing TEST.

## Evidence and contract boundary

Private evidence is under
`D:/AQ_DATA/P3/alphagen-us-pit-qlib-candidate-evaluation-001/`.

```text
FACTOR_MATERIALIZATION_REPORT_SHA256 = 652f19cef41274e1eb5e3fd54c6c3e15fa2aaa0d8591719557ca1220dbfa2821
EVALUATION_SUMMARY_SHA256 = c077196473711ebcbd33e572cb4e3de5a07103dba9e7aa8f88f255a7acf9b6a0
ARTIFACT_MANIFEST_V2_SHA256 = 4da1e39480f84c284a7bd7d01bdc921226b4752e1759aff82dbf2d576214e01f
FINAL_VALIDATION_REPORT_V2_SHA256 = 5b354a168009219417fdc63e40febfcc80b0e974351cf9f7924e4cf95a8c833b
```

The final audit independently rehashed all 17 native MLflow prediction
artifacts, confirmed all 17 SQLite runs are `FINISHED`, and confirmed every
MLflow artifact URI is under the private evidence root. MLflow's download API
initially returned ephemeral `/tmp` paths; the evidence identities were
rebound to the existing durable native artifact paths without changing bytes,
metrics, recorders, or rerunning models.

Candidate V2 was not created. Its required `rdagent_research_identity` and
`llm_execution_identity` cannot truthfully describe these AlphaGen-only runs:

```text
RD_AGENT_EXECUTED = NO
LLM_CALLS = 0
CANDIDATE_V2_CREATED = NO
CANDIDATE_V2_SEMANTIC_COMPATIBILITY = INCOMPATIBLE_REQUIRES_RDAGENT_LLM_IDENTITY
FORMULAIC_ALPHA_HANDOFF_CONTRACT = AUDIT_REQUIRED
CURRENT_NEXT = P3_FORMULAIC_ALPHA_CANDIDATE_HANDOFF_CONTRACT_AUDIT_001
```
