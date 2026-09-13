CREATE OR REPLACE TEMP VIEW binding_interval_observations AS
SELECT
    e.case_id,
    c.provider_asset_identifier,
    o.session_date,
    o.close
FROM binding_episodes e
JOIN binding_candidates c USING (case_id)
JOIN binding_observations o USING (provider_asset_identifier)
WHERE o.session_date >= e.valid_from
  AND o.session_date < e.valid_to;

CREATE OR REPLACE TEMP VIEW binding_candidate_summary AS
SELECT
    e.case_id,
    count(c.provider_asset_identifier) AS candidate_count,
    count(c.provider_asset_identifier) FILTER (
        WHERE c.provider_identity_supported AND c.sec_identity_supported
    ) AS eligible_count
FROM binding_episodes e
LEFT JOIN binding_candidates c USING (case_id)
GROUP BY e.case_id;

CREATE OR REPLACE TEMP VIEW binding_unique_candidates AS
SELECT case_id, min(provider_asset_identifier) AS provider_asset_identifier
FROM binding_candidates
WHERE provider_identity_supported AND sec_identity_supported
GROUP BY case_id
HAVING count(*) = 1;

CREATE OR REPLACE TEMP VIEW binding_conflicts AS
SELECT *
FROM binding_candidate_summary
WHERE candidate_count > 1 AND eligible_count != 1;

CREATE OR REPLACE TEMP VIEW binding_duplicates AS
SELECT 'binding_candidates' AS relation_name, case_id,
       provider_asset_identifier AS duplicate_key, count(*) AS duplicate_count
FROM binding_candidates
GROUP BY case_id, provider_asset_identifier
HAVING count(*) > 1
UNION ALL
SELECT 'binding_sessions', case_id, cast(session_date AS varchar), count(*)
FROM binding_sessions
GROUP BY case_id, session_date
HAVING count(*) > 1
UNION ALL
SELECT 'binding_observations', c.case_id,
       o.provider_asset_identifier || '|' || cast(o.session_date AS varchar), count(*)
FROM binding_observations o
JOIN (
    SELECT DISTINCT case_id, provider_asset_identifier FROM binding_candidates
) c USING (provider_asset_identifier)
GROUP BY c.case_id, o.provider_asset_identifier, o.session_date
HAVING count(*) > 1;

CREATE OR REPLACE TEMP VIEW binding_session_summary AS
SELECT case_id, count(*) AS actual_session_count
FROM binding_sessions
GROUP BY case_id;

CREATE OR REPLACE TEMP VIEW binding_session_validity AS
SELECT
    e.case_id,
    count(s.session_date) FILTER (
        WHERE s.session_date < e.valid_from OR s.session_date >= e.valid_to
    ) AS out_of_episode_session_count
FROM binding_episodes e
LEFT JOIN binding_sessions s USING (case_id)
GROUP BY e.case_id;

CREATE OR REPLACE TEMP VIEW binding_required_observations AS
SELECT
    u.case_id,
    u.provider_asset_identifier,
    s.session_date,
    i.close
FROM binding_unique_candidates u
JOIN binding_sessions s USING (case_id)
JOIN binding_interval_observations i
  ON i.case_id = u.case_id
 AND i.provider_asset_identifier = u.provider_asset_identifier
 AND i.session_date = s.session_date;

CREATE OR REPLACE TEMP VIEW binding_coverage AS
SELECT
    u.case_id,
    count(o.session_date) AS observation_count
FROM binding_unique_candidates u
LEFT JOIN binding_required_observations o
  ON o.case_id = u.case_id
 AND o.provider_asset_identifier = u.provider_asset_identifier
GROUP BY u.case_id;

CREATE OR REPLACE TEMP VIEW binding_missing_sessions AS
SELECT e.case_id, s.session_date
FROM binding_episodes e
JOIN binding_sessions s USING (case_id)
JOIN binding_unique_candidates u USING (case_id)
ANTI JOIN binding_interval_observations o
  ON o.case_id = e.case_id
 AND o.provider_asset_identifier = u.provider_asset_identifier
 AND o.session_date = s.session_date;

CREATE OR REPLACE TEMP VIEW binding_missing_summary AS
SELECT case_id, count(*) AS missing_session_count
FROM binding_missing_sessions
GROUP BY case_id;

CREATE OR REPLACE TEMP VIEW binding_identity_states AS
SELECT
    e.case_id,
    CASE
      WHEN s.candidate_count = 0 THEN 'PROVIDER_BINDING_NOT_AVAILABLE'
      WHEN coalesce(d.has_duplicate, false) THEN 'PROVIDER_BINDING_AMBIGUOUS'
      WHEN coalesce(ss.actual_session_count, 0) != e.required_sessions
        THEN 'PROVIDER_BINDING_AMBIGUOUS'
      WHEN coalesce(sv.out_of_episode_session_count, 0) != 0
        THEN 'PROVIDER_BINDING_AMBIGUOUS'
      WHEN s.eligible_count != 1 THEN 'PROVIDER_BINDING_AMBIGUOUS'
      ELSE 'PROVIDER_BINDING_AUTHORIZED'
    END AS identity_state,
    u.provider_asset_identifier,
    s.candidate_count,
    s.eligible_count,
    e.required_sessions,
    coalesce(c.observation_count, 0) AS observation_count,
    coalesce(m.missing_session_count, 0) AS missing_session_count
FROM binding_episodes e
JOIN binding_candidate_summary s USING (case_id)
LEFT JOIN binding_session_summary ss USING (case_id)
LEFT JOIN binding_session_validity sv USING (case_id)
LEFT JOIN binding_unique_candidates u USING (case_id)
LEFT JOIN binding_coverage c USING (case_id)
LEFT JOIN binding_missing_summary m USING (case_id)
LEFT JOIN (
    SELECT DISTINCT case_id, true AS has_duplicate FROM binding_duplicates
) d USING (case_id);

CREATE OR REPLACE TEMP VIEW binding_coverage_states AS
SELECT
    *,
    CASE
      WHEN identity_state != 'PROVIDER_BINDING_AUTHORIZED'
        THEN 'COVERAGE_NOT_EVALUATED'
      WHEN missing_session_count = 0
        THEN 'COMPLETE_PROVIDER_COVERAGE'
      WHEN missing_session_count = required_sessions
        THEN 'ZERO_PROVIDER_COVERAGE'
      WHEN missing_session_count > 0
       AND missing_session_count < required_sessions
        THEN 'PARTIAL_PROVIDER_COVERAGE'
      ELSE 'COVERAGE_NOT_EVALUATED'
    END AS coverage_state
FROM binding_identity_states;

CREATE OR REPLACE TEMP VIEW binding_decisions AS
SELECT
    *,
    CASE
      WHEN identity_state = 'PROVIDER_BINDING_AMBIGUOUS'
        THEN 'PROVIDER_BINDING_AMBIGUOUS'
      WHEN identity_state = 'PROVIDER_BINDING_NOT_AVAILABLE'
        THEN 'PROVIDER_BINDING_NOT_AVAILABLE'
      WHEN coverage_state = 'COMPLETE_PROVIDER_COVERAGE'
        THEN 'PROVIDER_BINDING_AUTHORIZED'
      WHEN coverage_state = 'ZERO_PROVIDER_COVERAGE'
        THEN 'KNOWN_PROVIDER_GAP_CANDIDATE'
      WHEN coverage_state = 'PARTIAL_PROVIDER_COVERAGE'
        THEN 'PARTIAL_PROVIDER_COVERAGE'
      ELSE 'PROVIDER_BINDING_AMBIGUOUS'
    END AS decision_state,
    decision_state AS binding_state
FROM binding_coverage_states;
