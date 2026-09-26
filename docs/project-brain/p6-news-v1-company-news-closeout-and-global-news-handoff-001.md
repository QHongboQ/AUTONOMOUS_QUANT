# P6 Company News closeout and Global News handoff 001

## Authority decision

PR #102 was squash-merged as
`a8325d2f00ee12fe5c0837ddbbd5f97e206a4690`. Its four-candidate whole-owner
audit remains the evidence basis for this closeout.

Company-specific historical News V1 is deferred because the institution-grade
whole owners are not currently accessible under an established AQ license.
RavenPack Company News Factors plus News Analytics remains the institutional
reference; LSEG Machine Readable News plus News Analytics remains a valid
alternative. Neither becomes an active dependency. QuantConnect Benzinga and
Tiingo remain incompatible with the required local Qlib conversion under the
public download terms. Direct Alpaca plus external PIT corroboration is not
reopened.

```text
COMPANY_NEWS_V1_HISTORICAL_STATUS = DEFERRED_ACCESS_BLOCKED
INSTITUTIONAL_REFERENCE_OWNER = RAVENPACK_COMPANY_NEWS_FACTORS_AND_NEWS_ANALYTICS
SELECTED_COMPANY_NEWS_WHOLE_OWNER = NONE
AQ_COMPANY_NEWS_ENGINE_REQUIRED = NO
COMPANY_NEWS_CUSTOM_BUILD_AUTHORIZED = NO
REALTIME_COMPANY_NEWS_PRODUCTIONIZATION = DEFERRED_TO_P9
ALPACA_DIRECT_ROLE = P9_REALTIME_NEWS_FALLBACK_OR_CHALLENGER
```

No sales contact, trial signup, purchase, provider search, or custom Company
News implementation occurred. Historical evidence is preserved rather than
rewritten.

## Global News handoff

The already-proven GDELT GKG 2.1 historical path is activated only for
session-global information state: market-level, global, geopolitical, and
macro-news context. GDELT is not Company News identity glue and does not own
company identity, CIK resolution, or ticker resolution.

The retained source and availability authority is:

```text
GDELT_GLOBAL_NEWS_SOURCE = GKG_2_1_WEB_ONLY
GDELT_SAFE_AVAILABILITY = CONSERVATIVE_BATCH_AND_DATE_EVIDENCE
GDELT_DATE_ONLY_EFFECTIVE_RULE = FIRST_XNYS_SESSION_STRICTLY_AFTER_SAFE_CALENDAR_DATE
GDELT_FABRICATED_INTRADAY_TIMESTAMP = NO
GDELT_COMPANY_NEWS_GLUE_ROLE = RETIRED
GDELT_GLOBAL_NEWS_ROLE = ACTIVE_P6_CANDIDATE
```

No feature family is selected here. The next design must choose the smallest
upstream-native surface, approximately three to six session-global features,
without yet freezing tone formulas, themes, GCAM columns, aggregation windows,
decay, or normalization.

## Frozen future scientific boundary

The future comparison is `M0 = BASE_157` against
`M1 = BASE_157 + exact frozen GLOBAL_NEWS_V1 features`. `BASE_157` is unchanged.
P5 fundamentals and the closed Macro V1 surface remain excluded.

The authorized sequence is:

1. `P6_GLOBAL_NEWS_V1_MINIMAL_FEATURE_SURFACE_DESIGN_001`
2. `P6_GLOBAL_NEWS_V1_MINIMAL_MATERIALIZATION_001`
3. `P6_GLOBAL_NEWS_V1_ABLATION_PROTOCOL_FREEZE_001`
4. `P6_GLOBAL_NEWS_V1_FIRST_AUTHORIZED_ABLATION_001`
5. `P6_GLOBAL_NEWS_V1_CLOSEOUT_001`

No provider search occurs between these stages unless a concrete source defect
blocks execution.

## Current state and non-actions

```text
P6_MACRO_V1 = CLOSED_NO_MEASURABLE_INCREMENTAL_VALUE
P6_COMPANY_NEWS_V1 = DEFERRED_ACCESS_BLOCKED_NO_CUSTOM_BUILD
P6_COMPANY_NEWS_PATCHWORK = RETIRED
P6_GLOBAL_NEWS_V1 = ACTIVE
CURRENT_P6_OBJECTIVE = GLOBAL_NEWS_V1_MINIMAL_FACTOR_ABLATION
GLOBAL_NEWS_FEATURE_FAMILY_SELECTED = NO

NEW_PRODUCTION_LOC = 0
AQ_NEWS_ENGINE_CREATED = NO
AQ_ENTITY_RESOLUTION_ENGINE_CREATED = NO
AQ_SECURITY_MASTER_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
REALTIME_WEBSOCKET_SESSION_COUNT = 0
ORDER_COUNT = 0
BROKER_ACTION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO

CURRENT_DEVELOPMENT_NEXT = P6_GLOBAL_NEWS_V1_MINIMAL_FEATURE_SURFACE_DESIGN_001
FINAL_CLASSIFICATION = PASS_P6_COMPANY_NEWS_CLOSEOUT_AND_GLOBAL_NEWS_HANDOFF
```
