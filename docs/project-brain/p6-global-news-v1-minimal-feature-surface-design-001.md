# P6 Global News V1 minimal feature surface design 001

## Decision

Global News V1 is frozen as the smallest four-field surface that preserves
document volume, net tone, negative intensity, and emotional charge. It uses
GDELT GKG 2.1 WEB records only and does not reopen Company News identity.

| Ordered feature | Upstream field / aggregation | Meaning |
|---|---|---|
| `global_news_log1p_volume` | `log1p(COUNT(DISTINCT GKGRECORDID))` | Compressed volume of unique qualifying WEB records mapped to the session. |
| `global_news_mean_tone` | `mean(V1.5TONE[0])` | Native average whole-document net tone. |
| `global_news_mean_negative_score` | `mean(V1.5TONE[2])` | Native average negative-word score, retained separately because net tone can cancel. |
| `global_news_mean_polarity` | `mean(V1.5TONE[3])` | Native average lexical emotional charge; not political polarization. |

Positive Score is excluded because GDELT defines Tone as Positive Score minus
Negative Score; with Tone and Negative Score selected, adding Positive Score
would be deterministic redundancy. Activity Reference Density and Self/Group
Reference Density are excluded as farther from the minimal market-information
hypothesis.

The official GKG 2.1 codebook defines `GKGRECORDID` as globally unique,
`V2SOURCECOLLECTIONIDENTIFIER=1` as WEB, and `V1.5TONE` as the native Tone,
Positive Score, Negative Score, Polarity, Activity Reference Density,
Self/Group Reference Density, and Word Count sequence
([GKG 2.1 codebook](https://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf)).

## Volume decision

The frozen source-coverage samples show materially different 15-minute batch
sizes: 636 to 2,721 valid WEB rows across the retained anchors. Raw document
volume is therefore not retained as a model feature. It is replaced by the
fixed monotone transform `log1p(count)`, which compresses scale without fitted
parameters or future/global normalization.

A trailing normalization is not introduced. Selecting a window would add a
new pre-result horizon, warm-up behavior, and rolling state that are not needed
to establish this minimal contract. Raw and transformed volume are not both
kept.

```text
GLOBAL_NEWS_VOLUME_FEATURE = global_news_log1p_volume
VOLUME_TRANSFORM = LOG1P_UNIQUE_GKGRECORDID_SESSION_COUNT
PAST_ONLY_ROLLING_NORMALIZATION_USED = NO
FUTURE_OR_GLOBAL_NORMALIZATION_USED = NO
RAW_VOLUME_RETAINED_AS_SECOND_FEATURE = NO
```

## PIT, grain, missingness, and weighting

The existing conservative GDELT policy remains unchanged: the safe calendar
date becomes effective on the first XNYS session strictly after that date. No
intraday timestamp is fabricated. All qualifying batches whose safe dates map
to a session contribute to that session's aggregate.

Canonical storage has one row per XNYS session and no instrument dimension.
The later Qlib consumer may mechanically broadcast a session-global state, but
the canonical data is not duplicated per security.

One unique GKG record is one equally weighted observation. There is no source,
publisher, geography, word-count, organization, or popularity weighting and
no semantic duplicate detector. For an empty qualifying session,
`global_news_log1p_volume` is `0.0`; Tone, Negative Score, and Polarity are
null. Sentiment is never zero-imputed or forward-filled.

## Bounded source sanity

The POC reused the prior retained 2,500-row sample and retrieved one previously
frozen 2,606,082-byte anchor, `20220103000000.gkg.csv.zip`. Its MD5 matched
`f000306fba39a5a84d9e86de8e1c3521`. Strict UTF-8 parsing rejected the one
previously known decode-error row and retained 636 valid WEB records.

```text
PRIOR_RETAINED_SAMPLE_ROWS = 2500
PRIOR_RETAINED_SAMPLE_WEB_ROWS = 2500
PRIOR_RETAINED_SAMPLE_UNIQUE_GKGRECORDID_COUNT = 2500
BOUNDED_VALID_WEB_TONE_ROWS = 636
BOUNDED_UNIQUE_GKGRECORDID_COUNT = 636
BOUNDED_DUPLICATE_GKGRECORDID_COUNT = 0
DECODE_ERROR_ROW_COUNT = 1
TONE_PARSE_FAILURE_COUNT = 0
NONFINITE_SELECTED_VALUE_COUNT = 0
SAFE_AVAILABLE_DATE = 2022-01-03
EFFECTIVE_XNYS_SESSION = 2022-01-04
RAW_GKG_ZIP_RETAINED = NO
DUCKDB_VERSION = 1.5.5
```

The bounded DuckDB aggregate produced 636 unique documents, log1p volume
`6.456769655572163`, mean Tone `-1.2474769776940404`, mean Negative Score
`3.775258418597025`, and mean Polarity `6.303039859500022`. These values are
source-shape evidence only; no outcome or predictive statistic was read.

## Exclusions and scientific boundary

```text
GLOBAL_NEWS_V1_SOURCE = GDELT_GKG_2_1_WEB
GLOBAL_NEWS_V1_FEATURE_COUNT = 4
GLOBAL_NEWS_V1_FEATURES = global_news_log1p_volume,global_news_mean_tone,global_news_mean_negative_score,global_news_mean_polarity
GLOBAL_NEWS_V1_GCAM_USED = NO
GLOBAL_NEWS_V1_THEMES_USED = NO
GLOBAL_NEWS_V1_EVENT_DATABASE_USED = NO
SOURCE_WEIGHTING_USED = NO
SEMANTIC_DEDUP_USED = NO
OUTCOME_BASED_SELECTION_USED = NO

FUTURE_M0 = BASE_157
FUTURE_M1 = BASE_157_PLUS_EXACT_GLOBAL_NEWS_V1_4
MACRO_V1_INCLUDED = NO
P5_FUNDAMENTALS_INCLUDED = NO
COMPANY_NEWS_INCLUDED = NO

AQ_NEWS_FEATURE_ENGINE_CREATED = NO
AQ_NEW_GENERIC_ENGINE_COUNT = 0
NEW_PRODUCTION_LOC = 0
MODEL_TRAINING_COUNT = 0
PREDICTION_COUNT = 0
BACKTEST_COUNT = 0
ABLATION_COUNT = 0
P2_V2_SEALED_OOS_ACCESSED = NO
CURRENT_P6_OBJECTIVE = GLOBAL_NEWS_V1_MINIMAL_MATERIALIZATION
CURRENT_DEVELOPMENT_NEXT = P6_GLOBAL_NEWS_V1_MINIMAL_MATERIALIZATION_001
```

Private evidence is retained at
`D:/AQ_DATA/P6/global-news-v1-minimal-feature-surface-design-001`. The
deterministic evidence-set SHA-256 is
`9ca69a381ef78090e59d93f1e140e92481dfcadbf340b3f020c0a1caf1fbe7eb`.

The next task is `P6_GLOBAL_NEWS_V1_MINIMAL_MATERIALIZATION_001`. It must
materialize exactly this four-feature contract without reopening providers,
GCAM, themes, event taxonomies, or feature selection.
