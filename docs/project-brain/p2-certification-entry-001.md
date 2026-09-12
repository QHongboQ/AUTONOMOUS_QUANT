# P2 Certification Entry 001

## Entry decision

```text
TASK = AUTONOMOUS-QUANT-P2-CERTIFICATION-ENTRY-001
STATUS = COMPLETE
P1 = COMPLETE
P1_MINIMAL_QUANT = COMPLETE
P2_CERTIFICATION_ENTRY = COMPLETE
P2_CERTIFICATION = STARTED / IN_PROGRESS
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PIT_UNIVERSE_CERTIFIED = NO
```

P2 is entered as an architecture, ownership, and dependency phase. No
certification engine or certification run was created. The logical tree is a
responsibility map: mature upstreams produce evidence, while AQ owns only
project-specific certification policy, contracts, thresholds, and promotion
authority.

The P1 exploratory references remain inputs for future P2 protocols only:

```text
P1_EXPLORATORY_MODEL_REFERENCE = LIGHTGBM_ALPHA158
P1_EXPLORATORY_STRATEGY_REFERENCE = TOPK_30_NDROP_3
P1_RESULT_CLASSIFICATION = RESEARCH_ONLY_NOT_CERTIFIED
TEST_SET_IS_PRISTINE_OOS = NO
```

They are not promoted, certified, or authorized for production.

## Upstream-first ownership map

Verified deployed authorities are Qlib `0.9.8.dev26` at source SHA
`2fb9380b342556ddb50a4b24e4fe8655d548b2b8`, skfolio `1.0.6`, arch `8.0.0`,
DVC `3.67.1`, exchange_calendars `4.13.2`, and Pandera `0.33.1`.

| Capability | Upstream owner | Mode | Deployed | Public interface | AQ allowed scope | Custom engine required |
|---|---|---|---|---|---|---|
| temporal-integrity | exchange_calendars + Pandera + Qlib; AQ owns policy | `UPSTREAM_LEAF` + `UPSTREAM_WHOLE` + `AQ_OWNED` policy | yes | `get_calendar`; `DataFrameSchema`; `DatasetH(segments=...)` | partition, leakage, purge/embargo and acceptance policy; thin contracts | no |
| walk-forward | skfolio | `UPSTREAM_LEAF` | yes | `skfolio.model_selection.WalkForward` | declare windows, hashes and acceptance thresholds | no |
| purged-cv | skfolio | `UPSTREAM_LEAF` | yes | `CombinatorialPurgedCV(n_folds, n_test_folds, purged_size, embargo_size)` | choose and preregister policy values; interpret evidence | no |
| multiple-testing-control | arch | `UPSTREAM_LEAF` | yes | `SPA`, `RealityCheck`, `StepM`, `MCS` and seeded bootstrap classes | define loss matrix, benchmark, trial inventory, seed and thresholds | no |
| benchmark-suite | Qlib | `UPSTREAM_WHOLE` | yes | Qlib backtest, Recorder and `PortAnaRecord` | select and freeze benchmark families and comparison policy | no |
| cost-slippage-stress | Qlib | `UPSTREAM_WHOLE` | yes | `backtest`; `Exchange` cost, volume-threshold and impact-cost inputs; `PortAnaRecord` | declare scenarios, limits and rejection thresholds | no |
| regime-stress | Qlib for bounded segmented reruns; optional ruptures remains deferred | `UPSTREAM_WHOLE` + `AQ_OWNED` policy | Qlib yes; ruptures no | `DatasetH` segments, backtest, Recorder and portfolio analysis | preregister regimes and acceptance policy; compose evidence | no |
| shadow-trading | LEAN only if later adopted | conditional `UPSTREAM_WHOLE` | no: source/evidence only; runtime prerequisites unresolved | LEAN paper/shadow execution interfaces after a separate adoption audit | permissions, TargetPortfolio boundary, observation and stop policy | no |
| champion-challenger | AQ | `AQ_OWNED` | not implemented | future project-specific `CertificationDecision` / promotion contract | thresholds, decision state, human permission and audit | no generic engine |
| strict point-in-time correctness | AQ PIT facts + exchange_calendars + Pandera + a certified data authority | mixed | partial | `build_research_ready_universe`, XNYS adapter, Pandera boundaries | accepted facts, source precedence, fail-closed policy and contracts | no |
| survivorship-bias control | certified data authority not yet selected; AQ owns acceptance policy | mixed / unresolved upstream | no | episode-scoped membership and price coverage contract | define completeness and rejection rules | no |
| sealed independent OOS | AQ policy + DVC | `AQ_OWNED` policy + `UPSTREAM_LEAF` freeze | partial | DVC dependencies, lock and content-addressed output | preregistration, access boundary, one-shot evaluation and release decision | no |
| parameter perturbation | Qlib + MLflow Recorder | `UPSTREAM_WHOLE` | yes | Qlib configuration/workflow, Recorder and MLflow tracking | preregister bounded perturbations and interpretation | no |
| liquidity constraints | Qlib plus certified price/volume authority | `UPSTREAM_WHOLE` + unresolved data input | partial | Qlib `Exchange(volume_threshold=..., impact_cost=...)` | thresholds, stress grid and rejection policy | no |
| reproducibility | DVC + Qlib Recorder / MLflow | `UPSTREAM_LEAF` + `UPSTREAM_WHOLE` | yes | `dvc.yaml` / `dvc.lock`; Recorder and `MLflowExpManager` | immutable dependency declarations and cross-upstream evidence contract | no |
| promotion policy | AQ | `AQ_OWNED` | not implemented | future project-specific decision contract | exclusive certification, promotion and human authorization authority | no generic engine |

skfolio is an algorithm provider, not temporal-policy owner. Arch emits
multiple-comparison evidence and cannot promote a candidate. The previously
accepted DSR/PBO gap may permit separately authorized pure verified evidence
functions only if P2 policy requires them; it does not authorize a generic AQ
statistics or certification engine. LEAN is relevant only to the later shadow
leaf and is not adopted by this entry.

## Data-authority audit

| Requirement | Current result | Evidence boundary |
|---|---|---|
| universe membership PIT authority | research-ready, not certified | accepted AQ facts cover bounded S&P 500 membership/identity behavior, but the gate remains `PIT_UNIVERSE_CERTIFIED = NO` |
| ticker identity and reuse authority | bounded research-ready | 20 accepted identity events and episode/re-entry firewalls do not constitute a permanent security master or complete institutional authority |
| delisted and predecessor prices | not ready | current Qlib/Yahoo-derived provider has no demonstrated complete episode-scoped coverage |
| price-history survivorship completeness | not ready | the provider's `sp500` path is explicitly best-effort and not certified |
| corporate-action treatment | not ready | no certification evidence proves split/dividend/rename treatment across every required episode |
| timestamp / first-available semantics | not ready | price availability and revision timestamps are not carried as certification authority |
| immutable dataset snapshots | capability ready | DVC `3.67.1` owns dependencies, lock, hash/cache and reproduction; existing snapshot is research-ready only |
| sealed certification dataset | possible after input closure | DVC can freeze it only after certified universe, prices, actions, timestamps and policy are fixed |
| genuinely untouched OOS now | no | the P1 2022-01-03 through 2025-12-29 test period has already been observed |

The smallest blocking fact is therefore:

```text
P2_FIRST_BLOCKER = CERTIFICATION_DATA_AUTHORITY_INCOMPLETE
BLOCKER_DETAIL = NO_STRICT_SURVIVORSHIP_COMPLETE_POINT_IN_TIME_PRICE_AUTHORITY_FOR_DELISTED_AND_PREDECESSOR_SECURITY_EPISODES
STRICT_PIT_DATA_READY = NO
SURVIVORSHIP_FREE_PRICE_AUTHORITY_READY = NO
```

P1 data may be reused for exploratory development and dry-run plumbing, but
not as certified evidence. No paid data was purchased, no provider was added,
and no data was downloaded in this entry task.

## Sealed-OOS policy

The observed P1 test period can never be relabeled as the final sealed OOS.
A future window becomes sealed only after all of the following are recorded
before evaluation:

1. certified universe, episode-scoped price/action and availability authority;
2. immutable dataset and policy hashes;
3. candidate, feature, label, cost, liquidity, benchmark and metric definitions;
4. train/validation boundary, CV/purge/embargo policy and complete trial inventory;
5. an access rule preventing research selection from seeing sealed results;
6. a one-shot evaluation procedure, release event and fail-closed audit trail.

The final dates must follow the certified data and preregistration policy, not
be chosen from observed performance or convenience. New future observations
may become eligible only after these conditions are established.

## Dependency order

```text
certified membership / identity / price / action / timestamp authority
  -> temporal integrity and strict PIT validation
  -> reproducible frozen certification dataset
  -> preregistered train / validation / sealed-OOS protocol
  -> skfolio WalkForward / CombinatorialPurgedCV
  -> arch multiple-testing + bounded perturbation / robustness evidence
  -> Qlib benchmark / cost / slippage / liquidity / regime stress
  -> LEAN shadow observation if separately adopted and required
  -> AQ CertificationDecision and champion/challenger promotion policy
```

Downstream statistical evidence cannot repair an uncertified data input, and
no leaf may independently promote a model or strategy.

## First execution task and non-authorizations

```text
P2_FIRST_EXECUTION_TASK = P2_CERTIFIED_DATA_FOUNDATION
CURRENT_NEXT = P2_CERTIFIED_DATA_FOUNDATION
```

That independently auditable task must close the earliest data dependency:
select and pin acceptable universe/price/action/timestamp authorities, define
episode-scoped coverage and fail-closed completeness rules, and produce a
reproducibly frozen certification-candidate data boundary. It must not train,
certify, promote, paper trade, or trade live merely to complete the data leaf.

```text
AQ_CUSTOM_CERTIFICATION_ENGINE = NO
AQ_CUSTOM_CV_ENGINE = NO
AQ_CUSTOM_STATISTICS_ENGINE = NO
AQ_CUSTOM_BACKTESTER = NO
AQ_CUSTOM_EXPERIMENT_DATABASE = NO
NEW_AQ_PRODUCTION_PYTHON_LOC = 0
CERTIFIED_MODEL = NONE
CERTIFIED_STRATEGY = NONE
PRODUCTION_TRADING = NOT AUTHORIZED
LIVE_CAPITAL = NOT AUTHORIZED
P3_AUTONOMOUS_RESEARCH = NOT STARTED
```

The existing research Web UI remains owned and implemented by upstream
MLflow. This task neither modified it nor created a certification dashboard.
