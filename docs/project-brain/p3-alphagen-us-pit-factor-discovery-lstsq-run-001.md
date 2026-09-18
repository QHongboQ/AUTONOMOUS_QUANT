# P3 AlphaGen US PIT Factor Discovery LSTSQ Run 001

## Result

The first formal AlphaGen US PIT discovery completed all three frozen seeds
using the qualified official least-squares configuration. Discovery used TRAIN
only; frozen-expression evaluation and redundancy analysis used VALID only.
Historical TEST and sealed OOS were untouched.

```text
ALPHAGEN_FACTOR_DISCOVERY_LSTSQ_RUN_001 = PASS
ALPHAGEN_MSE_LSTSQ_FAST_V1 = FORMAL_DISCOVERY_CONFIG
ALPHAGEN_MSE_L1_REFERENCE_V1 = REFERENCE_RESOURCE_EXPENSIVE_NOT_CURRENT_MAINLINE
FORMAL_SEEDS = 0,1,2
FORMAL_SEEDS_COMPLETED = 3
TIMESTEPS_PER_SEED = 32768
FRESH_PPO_PER_SEED = YES
FRESH_FACTOR_POOL_PER_SEED = YES
WARM_START = NO
```

This is research discovery, not certification. The 17 selected cluster
representatives are classified only as `P3_RESEARCH_ALPHA_CANDIDATE`; the
other 43 unique expressions remain `P3_DISCOVERY_ALPHA_RAW`. No Candidate V2
or P2 certification artifact was created.

## Authority and partitions

The run used clean upstream AlphaGen at
`259687e8f316994426416c530a94842a2fe6405e` and the existing US PIT Qlib
provider whose build-report SHA-256 is
`eda5e8bb8e3f274d2893ea6a09f5764111f59c9cadf40eb32e3fbce199a68142`.
The target remained the frozen P2 authority:
`Ref($close, -2)/Ref($close, -1) - 1`.

```text
TRAIN_AUTHORITY = 2015-04-01 THROUGH 2019-12-31
TRAIN_EFFECTIVE_RANGE = 2015-05-28 THROUGH 2019-12-27
TRAIN_LAST_LABEL_SESSION = 2019-12-31
TRAIN_IDENTITIES = 627
TRAIN_EVALUATION_SESSIONS = 1156
TRAIN_MEMBER_SESSION_ROWS = 583037

VALID_AUTHORITY = 2020-01-01 THROUGH 2021-12-31
VALID_EFFECTIVE_RANGE = 2020-01-02 THROUGH 2021-12-29
VALID_LAST_LABEL_SESSION = 2021-12-31
VALID_IDENTITIES = 546
VALID_EVALUATION_SESSIONS = 503
VALID_MEMBER_SESSION_ROWS = 254017

TARGET_CROSS_PARTITION_ROWS = 0
HISTORICAL_TEST_ROWS_ACCESSED = 0
SEALED_OOS_ROWS_ACCESSED = 0
CURRENT_SURVIVOR_FILTERING = NO
SYNTHETIC_FILL = NO
AUTHORITATIVE_NAN_PRESERVATION = YES
```

## Trial accounting

```text
SEED_0_RUNTIME_SECONDS = 433.34715263498947
SEED_1_RUNTIME_SECONDS = 447.78462965300423
SEED_2_RUNTIME_SECONDS = 379.14288738000323
TOTAL_SEED_RUNTIME_SECONDS = 1260.274669667997

EXPRESSIONS_GENERATED_TOTAL = 7993
EXPRESSIONS_EVALUATED_TOTAL = 2720
POOL_ADMISSIONS_TOTAL = 758
POOL_REPLACEMENTS_TOTAL = 698
RAW_FINAL_POOL_ENTRIES = 60
UNIQUE_EXPRESSIONS = 60
EXACT_DUPLICATES = 0
VALID_EVALUATIONS = 60
VALID_MUTUAL_IC_PAIR_EVALUATIONS = 1770
CORRELATION_CLUSTERS = 17
P3_RESEARCH_ALPHA_CANDIDATES = 17
P3_DISCOVERY_ALPHA_RAW = 43
VWAP_ACTION_SELECTION_COUNT = 0
```

All 60 unique expressions were clustered on VALID using upstream AlphaGen
mutual IC and the frozen `abs(mutual_IC) >= 0.95` rule. Every cluster
representative was selected by highest absolute VALID RankIC with
lexicographic expression text as the tie-break; an independent replay found
zero selection-rule violations.

## Leading research candidates

The leading representatives by absolute VALID RankIC are shown only to make
the research output auditable. Their small magnitudes reinforce that this run
does not establish factor quality or production readiness.

| Cluster | Expression | Seed | TRAIN IC | TRAIN RankIC | VALID IC | VALID RankIC |
|---|---|---:|---:|---:|---:|---:|
| cluster-001 | `Greater(Greater(Div(-30.0,$open),-10.0),-0.5)` | 0 | 0.001628 | 0.003379 | 0.009792 | 0.014471 |
| cluster-005 | `Sub(Abs(Mul(-0.01,Min(Mul(Ref($open,5d),$open),5d))),Less(-1.0,$low))` | 2 | -0.000811 | 0.002599 | 0.002856 | 0.014397 |
| cluster-002 | `EMA(Add(10.0,Add(Abs($low),-0.01)),10d)` | 1 | -0.000558 | 0.002465 | 0.006316 | 0.014220 |
| cluster-006 | `Div(-0.01,Min($volume,1d))` | 0 | 0.002463 | -0.002907 | -0.003756 | -0.014130 |
| cluster-010 | `WMA($volume,20d)` | 2 | 0.009909 | -0.003577 | 0.008801 | -0.013858 |

## Ownership and safety

```text
ALPHAGEN_MSE_POOL = UPSTREAM_WHOLE
ALPHAGEN_LSTSQ_OPTIMIZER = UPSTREAM_WHOLE
AQ_CUSTOM_OPTIMIZER = NO
AQ_EXPRESSION_CACHE = NO
AQ_CUSTOM_FACTOR_POOL = NO
AQ_CUSTOM_RL = NO
AQ_CUSTOM_PPO = NO
MARKET_NETWORK_CALLS = 0
LLM_CALLS = 0
RD_AGENT_EXECUTED = NO
OLLAMA_EXECUTED = NO
BROKER_CALLS = 0
CANDIDATE_V2_CREATED = NO
P2_CERTIFICATION_EXECUTED = NO
```

Private immutable evidence is under:

`D:/AQ_DATA/P3/alphagen-us-pit-factor-discovery-lstsq-run-001/`

The SHA-256 of `discovery_summary.json` is:

`5212564ed15b3fa15bde40f14b9fe9a067b725bc5dd472a6046af0013893523a`

```text
ALPHAFORGE = CHALLENGER_NOT_CURRENT_MAINLINE
ALPHAGPT = CHALLENGER_NOT_CURRENT_MAINLINE
RD_AGENT_LOCAL_BRAIN_SEARCH = PAUSED_NOT_P3_BLOCKER
CURRENT_NEXT = P3_ALPHAGEN_US_PIT_QLIB_CANDIDATE_EVALUATION_001
```
