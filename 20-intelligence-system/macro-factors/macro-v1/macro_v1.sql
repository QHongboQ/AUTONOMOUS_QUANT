CREATE OR REPLACE TEMP TABLE mapped_evidence AS
SELECT e.*, (
    SELECT min(s.session) FROM all_sessions s
    WHERE s.session > CAST(e.known_at AS DATE)
) AS effective_session
FROM evidence_input e;

CREATE OR REPLACE TEMP TABLE state_rows AS
WITH visible_ranked AS (
    SELECT s.session, e.*,
           row_number() OVER (
               PARTITION BY s.session, e.series_id, e.observed_at
               ORDER BY e.known_at DESC, e.evidence_id
           ) AS revision_rank
    FROM target_sessions s
    JOIN mapped_evidence e ON e.effective_session <= s.session
), latest AS (
    SELECT * EXCLUDE (revision_rank) FROM visible_ranked WHERE revision_rank = 1
), windowed AS (
    SELECT *,
           lag(observed_at, 1) OVER w AS d1_observed_at,
           lag(observed_at, 2) OVER w AS d2_observed_at,
           lag(known_at, 1) OVER w AS d1_known_at,
           lag(known_at, 2) OVER w AS d2_known_at,
           lag(effective_session, 1) OVER w AS d1_effective_session,
           lag(effective_session, 2) OVER w AS d2_effective_session,
           lag(value, 1) OVER w AS d1_value,
           lag(value, 2) OVER w AS d2_value,
           lag(evidence_id, 1) OVER w AS d1_evidence_id,
           lag(evidence_id, 2) OVER w AS d2_evidence_id
    FROM latest
    WINDOW w AS (PARTITION BY session, series_id ORDER BY observed_at)
), candidates AS (
    SELECT *,
           CASE
             WHEN series_id = 'CPIAUCSL'
              AND value > 0 AND d1_value > 0 AND d2_value > 0
              AND date_diff('month', d1_observed_at, observed_at) = 1
              AND date_diff('month', d2_observed_at, d1_observed_at) = 1
             THEN ln(value) - 2 * ln(d1_value) + ln(d2_value)
             WHEN series_id = 'UNRATE'
              AND value IS NOT NULL AND d1_value IS NOT NULL
              AND date_diff('month', d1_observed_at, observed_at) = 1
             THEN value - d1_value
           END AS transformed_value,
           CASE WHEN series_id = 'CPIAUCSL'
                THEN greatest(effective_session, d1_effective_session, d2_effective_session)
                ELSE greatest(effective_session, d1_effective_session)
           END AS state_effective_session
    FROM windowed
), ranked AS (
    SELECT *, row_number() OVER (
        PARTITION BY session, series_id ORDER BY observed_at DESC
    ) AS observed_rank
    FROM candidates WHERE transformed_value IS NOT NULL
)
SELECT * EXCLUDE (observed_rank) FROM ranked WHERE observed_rank = 1;

CREATE OR REPLACE TEMP TABLE macro_state AS
SELECT s.session,
       max(CASE WHEN r.series_id = 'CPIAUCSL' THEN r.transformed_value END)
           AS macro_v1_cpiaucsl_d2_log,
       max(CASE WHEN r.series_id = 'UNRATE' THEN r.transformed_value END)
           AS macro_v1_unrate_d1
FROM target_sessions s LEFT JOIN state_rows r USING (session)
GROUP BY s.session ORDER BY s.session;

CREATE OR REPLACE TEMP TABLE provenance AS
WITH signed AS (
    SELECT *, CASE WHEN series_id = 'CPIAUCSL'
                   THEN evidence_id || ':' || d1_evidence_id || ':' || d2_evidence_id
                   ELSE evidence_id || ':' || d1_evidence_id END AS signature
    FROM state_rows
), changed AS (
    SELECT *, lag(signature) OVER (PARTITION BY series_id ORDER BY session) AS prior_signature
    FROM signed
), transitions AS (
    SELECT * FROM changed WHERE prior_signature IS DISTINCT FROM signature
)
SELECT CASE WHEN series_id = 'CPIAUCSL' THEN 'macro_v1_cpiaucsl_d2_log'
            ELSE 'macro_v1_unrate_d1' END AS feature_id,
       state_effective_session,
       series_id AS source_series_id,
       CASE WHEN series_id = 'CPIAUCSL' THEN 6 ELSE 2 END AS transform_code,
       d.dependency_position,
       d.dependency_observed_at,
       d.dependency_known_at,
       d.dependency_effective_session,
       d.dependency_raw_value,
       d.upstream_evidence_identity
FROM transitions,
LATERAL (VALUES
    (0, observed_at, known_at, effective_session, value, evidence_id),
    (1, d1_observed_at, d1_known_at, d1_effective_session, d1_value, d1_evidence_id),
    (2, d2_observed_at, d2_known_at, d2_effective_session, d2_value, d2_evidence_id)
) d(dependency_position, dependency_observed_at, dependency_known_at,
    dependency_effective_session, dependency_raw_value, upstream_evidence_identity)
WHERE series_id = 'CPIAUCSL' OR d.dependency_position < 2
ORDER BY feature_id, state_effective_session, dependency_position;
