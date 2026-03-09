-- =============================================================================
-- BigQuery DDL — Leagues Data Project
-- Raw landing: GCS JSON -> BigQuery External Tables
-- Source: API-Football v3  |  League: SPL (307)
--
-- This script natively connects the GCS data lake directly to BigQuery using
-- External Tables with Hive Partitioning. You do not need a batch load job 
-- (like COPY INTO) because BigQuery can query the GCS JSON files instantly.
-- =============================================================================

-- ── Dataset ─────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS `leagues_data_raw`
OPTIONS(
  location="EU"
);

-- =============================================================================
-- GCS path layout (from storage.py):
--   gs://${GCS_BUCKET}/raw/source=api_football/league={id}/season={season}/
--     endpoint={ep}/dt={YYYY-MM-DD}/run_id={ts}/part-NNNNN.json
--
-- Each JSON file contains:
--   { "endpoint", "entity_key", "params", "fetched_at", "payload" }
--
-- Note: Replace '${GCS_BUCKET}' with the actual name of your GCS bucket.
-- =============================================================================


-- ── League Baseline ─────────────────────────────────────────────────────────

-- /fixtures
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_fixtures` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /teams
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_teams` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /standings
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_standings` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /fixtures/rounds
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_fixtures_rounds` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- ── Players (league-wide) ───────────────────────────────────────────────────

-- /players
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_players` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /players/topscorers
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_players_topscorers` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /players/topassists
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_players_topassists` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /players/topyellowcards
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_players_topyellowcards` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /players/topredcards
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_players_topredcards` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- ── Team-Level Snapshots ────────────────────────────────────────────────────

-- /teams/statistics
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_teams_statistics` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /injuries
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_injuries` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /transfers
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_transfers` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /players/squads
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_players_squads` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- ── Fixture Deep Details ────────────────────────────────────────────────────

-- /fixtures/statistics
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_fixtures_statistics` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /fixtures/events
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_fixtures_events` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /fixtures/lineups
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_fixtures_lineups` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /fixtures/players
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_fixtures_players` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- /predictions
CREATE OR REPLACE EXTERNAL TABLE `leagues_data_raw.ext_raw_predictions` (
    entity_key STRING, params JSON, fetched_at TIMESTAMP, payload JSON
) WITH PARTITION COLUMNS (
    league INT64, season INT64, endpoint STRING, dt DATE, run_id STRING
) OPTIONS (
  format = 'JSON',
  uris = ['gs://${GCS_BUCKET}/raw/source=api_football/*'],
  hive_partition_uri_prefix = 'gs://${GCS_BUCKET}/raw/source=api_football'
);

-- =============================================================================
-- Query examples — External Tables handle nested JSON beautifully with the 
-- JSON functions in BigQuery.
-- =============================================================================

/*
-- All fixture results
SELECT
    league,
    season,
    CAST(JSON_EXTRACT_SCALAR(f, '$.fixture.id') AS INT64) AS fixture_id,
    TIMESTAMP(JSON_EXTRACT_SCALAR(f, '$.fixture.date')) AS fixture_date,
    JSON_EXTRACT_SCALAR(f, '$.teams.home.name') AS home_team,
    JSON_EXTRACT_SCALAR(f, '$.teams.away.name') AS away_team,
    CAST(JSON_EXTRACT_SCALAR(f, '$.goals.home') AS INT64) AS goals_home,
    CAST(JSON_EXTRACT_SCALAR(f, '$.goals.away') AS INT64) AS goals_away
FROM `leagues_data_raw.ext_raw_fixtures`,
  UNNEST(JSON_EXTRACT_ARRAY(payload, '$.response')) AS f
WHERE dt >= '2023-08-01'; -- Partition filter for fast querying!

-- Player stats from a fixture
SELECT
    league,
    dt,
    JSON_EXTRACT_SCALAR(t, '$.team.name') AS team_name,
    CAST(JSON_EXTRACT_SCALAR(p, '$.player.id') AS INT64) AS player_id,
    JSON_EXTRACT_SCALAR(p, '$.player.name') AS player_name,
    CAST(JSON_EXTRACT_SCALAR(p, '$.statistics[0].games.minutes') AS INT64) AS minutes,
    CAST(JSON_EXTRACT_SCALAR(p, '$.statistics[0].goals.total') AS INT64) AS goals,
    CAST(JSON_EXTRACT_SCALAR(p, '$.statistics[0].goals.assists') AS INT64) AS assists
FROM `leagues_data_raw.ext_raw_fixtures_players`,
  UNNEST(JSON_EXTRACT_ARRAY(payload, '$.response')) AS t,
  UNNEST(JSON_EXTRACT_ARRAY(t, '$.players')) AS p
WHERE season = 2023; -- Partition pruning
*/
