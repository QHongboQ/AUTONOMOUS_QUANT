# P2 Free Upstream Identity Binding Fail-Closed Hardening 001

Status: COMPLETE — AWAITING INDEPENDENT CLOSEOUT

```text
PRIOR_HEAD = e15bce2d719192b82d071d407fa8b3017821ceb1
TREE_OWNERSHIP = CORRECT
PROVIDER_BINDING_LOCATION = 10-data-system/market-data/p2-binding
DUCKDB_RELATIONAL_OWNER = YES
```

## Bounded defect and correction

Independent review found that `binding_decisions` used an inner join to
`binding_session_summary`. An episode with no supplied session rows therefore
had no summary row and could disappear from the final relation.

The final relation now left-joins the session summary and treats a missing
count as zero. A required episode with zero or partial session input survives
and resolves to `PROVIDER_BINDING_AMBIGUOUS`. DuckDB also calculates an
out-of-episode session count against each half-open episode interval. A
supplied session outside `valid_from <= session_date < valid_to` fails closed
even when the raw supplied-row count equals `required_sessions`.

No success state, provider, authority fact, or Python relational loop was
added.

## Cardinality and regression evidence

Four focused regressions were added:

1. an episode with zero session rows remains present and fails closed;
2. two supplied rows for three required sessions fail closed;
3. three supplied rows with one outside the episode interval fail closed;
4. N unique episodes produce exactly N decisions and one decision per case.

The complete synthetic binding suite passes 19/19. All 13 frozen PIT
behavioral regressions remain PASS. Ruff, dependency validation, and
compileall pass.

```text
ZERO_SESSION_EPISODE_PRESERVED = PASS
ZERO_SESSION_FAIL_CLOSED = PASS
PARTIAL_SESSION_FAIL_CLOSED = PASS
OUT_OF_EPISODE_SESSION_FAIL_CLOSED = PASS
DECISION_ROW_COUNT_EQUALS_EPISODE_COUNT = PASS
ONE_DECISION_PER_CASE = PASS
DD_FAIL_CLOSED = PASS
ANTM_ELV_BINDING = PASS
STI_COVERAGE_GAP = PASS
FB_META_REGRESSION = PASS
DISCK_REGRESSION = PASS
DUPLICATE_FAIL_CLOSED = PASS
GENERIC_RUNTIME_TICKER_BRANCHES = 0
```

## Preserved authority and non-actions

```text
AQ_PROVIDER_REGISTRY = NONE
AQ_PROVIDER_ROUTER = NONE
AQ_GENERIC_NORMALIZER = NONE
AQ_SECURITY_MASTER = NONE
AQ_RELATIONAL_ENGINE = NONE
FROZEN_CERTIFICATION_DATASET_CONTRACT_V1 = FROZEN
ACTIVE_PRICE_PROVIDER_SET = QUANTIACS_PLUS_SIMFIN_ONLY
SOURCE_PRECEDENCE = QUANTIACS_PRIMARY_SIMFIN_BOUNDED_SECONDARY
NEW_ACCEPTED_MANUAL_EPISODE_FACTS = 0
DATASET_BUILT = NO
PROVIDER_CALLS = NONE
MODEL_TRAINING = NO
BACKTEST = NO
SEALED_OOS_DATES_SELECTED = NO
```

The existing branch remains the implementation authority. Current next is
unchanged:

```text
CURRENT_NEXT = P2_FREE_UPSTREAM_IDENTITY_BINDING_IMPLEMENTATION_CLOSEOUT_001
```
