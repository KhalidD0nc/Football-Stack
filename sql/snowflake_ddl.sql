-- =============================================================================
-- Snowflake DDL — Leagues Data Project
-- Raw landing: S3 JSON -> Snowflake as-is (one table per endpoint)
-- Source: API-Football v3  |  League: SPL (307)
-- =============================================================================

-- ── Database & Schema ───────────────────────────────────────────────────────

CREATE DATABASE IF NOT EXISTS LEAGUES_DATA;
USE DATABASE LEAGUES_DATA;
CREATE SCHEMA IF NOT EXISTS RAW;
USE SCHEMA RAW;

-- ── File Format ─────────────────────────────────────────────────────────────

CREATE FILE FORMAT IF NOT EXISTS json_raw
  TYPE = JSON
  STRIP_OUTER_ARRAY = FALSE
  IGNORE_UTF8_ERRORS = TRUE;

-- ── External Stage ──────────────────────────────────────────────────────────
-- Points at the raw/ prefix in S3.
-- Replace <bucket> and <storage_integration> with your values.

CREATE STAGE IF NOT EXISTS stg_api_football
  URL = 's3://leagues-datalake/raw/source=api_football/'
  STORAGE_INTEGRATION = <storage_integration>
  FILE_FORMAT = json_raw;

-- =============================================================================
-- S3 path layout (from storage.py):
--   raw/source=api_football/league={id}/season={season}/
--     endpoint={ep}/dt={YYYY-MM-DD}/run_id={ts}/part-NNNNN.json
--
-- Each JSON file contains:
--   { "endpoint", "entity_key", "params", "fetched_at", "payload" }
--
-- Every table below stores the full file as a VARIANT column.
-- =============================================================================

-- ── League Baseline ─────────────────────────────────────────────────────────

-- /fixtures — full season fixture list & scores
CREATE TABLE IF NOT EXISTS raw_fixtures (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /teams — team info + venue
CREATE TABLE IF NOT EXISTS raw_teams (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /standings — league table
CREATE TABLE IF NOT EXISTS raw_standings (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /fixtures/rounds — matchday names
CREATE TABLE IF NOT EXISTS raw_fixtures_rounds (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- ── Players (league-wide) ───────────────────────────────────────────────────

-- /players — paginated player season stats
CREATE TABLE IF NOT EXISTS raw_players (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /players/topscorers
CREATE TABLE IF NOT EXISTS raw_players_topscorers (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /players/topassists
CREATE TABLE IF NOT EXISTS raw_players_topassists (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /players/topyellowcards
CREATE TABLE IF NOT EXISTS raw_players_topyellowcards (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /players/topredcards
CREATE TABLE IF NOT EXISTS raw_players_topredcards (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- ── Team-Level Snapshots (all SPL clubs) ────────────────────────────────────

-- /teams/statistics — aggregated team performance
CREATE TABLE IF NOT EXISTS raw_teams_statistics (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /injuries — player injuries & suspensions
CREATE TABLE IF NOT EXISTS raw_injuries (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /transfers — transfer records
CREATE TABLE IF NOT EXISTS raw_transfers (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /players/squads — current roster
CREATE TABLE IF NOT EXISTS raw_players_squads (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- ── Fixture Deep Details (configured team's match-day data) ─────────────────

-- /fixtures/statistics — match-level team stats
CREATE TABLE IF NOT EXISTS raw_fixtures_statistics (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /fixtures/events — goals, cards, substitutions
CREATE TABLE IF NOT EXISTS raw_fixtures_events (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /fixtures/lineups — formations, starters, bench
CREATE TABLE IF NOT EXISTS raw_fixtures_lineups (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);

-- /fixtures/players — per-player match performance
CREATE TABLE IF NOT EXISTS raw_fixtures_players (
    raw             VARIANT        NOT NULL,
    league_id       INT,
    season          INT,
    dt              DATE,
    run_id          VARCHAR,
    _file_name      VARCHAR,
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);



-- New tables
CREATE TABLE IF NOT EXISTS raw_fixtures_events (
    raw VARIANT NOT NULL, league_id INT, season INT, dt DATE, run_id VARCHAR, _file_name VARCHAR, _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
CREATE TABLE IF NOT EXISTS raw_fixtures_lineups (
    raw VARIANT NOT NULL, league_id INT, season INT, dt DATE, run_id VARCHAR, _file_name VARCHAR, _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
CREATE TABLE IF NOT EXISTS raw_fixtures_players (
    raw VARIANT NOT NULL, league_id INT, season INT, dt DATE, run_id VARCHAR, _file_name VARCHAR, _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
CREATE TABLE IF NOT EXISTS raw_fixtures_statistics (
    raw VARIANT NOT NULL, league_id INT, season INT, dt DATE, run_id VARCHAR, _file_name VARCHAR, _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
CREATE TABLE IF NOT EXISTS raw_predictions (
    raw VARIANT NOT NULL, league_id INT, season INT, dt DATE, run_id VARCHAR, _file_name VARCHAR, _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- COPY INTO examples
-- Each loads from the stage sub-path matching that endpoint.
-- The metadata columns are extracted from the S3 path via METADATA$FILENAME.
-- =============================================================================


-- ============================================================
-- COPY INTO for all 13 endpoints
-- ============================================================

-- 1. fixtures
COPY INTO raw_fixtures (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=fixtures/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 2. teams
COPY INTO raw_teams (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=teams/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 3. standings
COPY INTO raw_standings (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=standings/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 4. fixtures_rounds
COPY INTO raw_fixtures_rounds (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=fixtures_rounds/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 5. players
COPY INTO raw_players (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=players/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 6. players_topscorers
COPY INTO raw_players_topscorers (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=players_topscorers/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 7. players_topassists
COPY INTO raw_players_topassists (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=players_topassists/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 8. players_topyellowcards
COPY INTO raw_players_topyellowcards (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=players_topyellowcards/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 9. players_topredcards
COPY INTO raw_players_topredcards (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=players_topredcards/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 10. teams_statistics
COPY INTO raw_teams_statistics (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=teams_statistics/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 11. injuries
COPY INTO raw_injuries (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=injuries/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 12. transfers
COPY INTO raw_transfers (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=transfers/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- 13. players_squads
COPY INTO raw_players_squads (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
     FROM @LEAGUES_STAGE
)
PATTERN = '.*endpoint=players_squads/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;


-- COPY INTO for new endpoints
COPY INTO raw_fixtures_events (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
    FROM @LEAGUES_STAGE
)
PATTERN = '.*raw/source=api_football/.*endpoint=fixtures_events/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

COPY INTO raw_fixtures_lineups (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
    FROM @LEAGUES_STAGE
)
PATTERN = '.*raw/source=api_football/.*endpoint=fixtures_lineups/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

COPY INTO raw_fixtures_players (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
    FROM @LEAGUES_STAGE
)
PATTERN = '.*raw/source=api_football/.*endpoint=fixtures_players/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

COPY INTO raw_fixtures_statistics (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
    FROM @LEAGUES_STAGE
)
PATTERN = '.*raw/source=api_football/.*endpoint=fixtures_statistics/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

COPY INTO raw_predictions (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
    FROM @LEAGUES_STAGE
)
PATTERN = '.*raw/source=api_football/.*endpoint=predictions/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

/*
-- Example: load raw_fixtures
COPY INTO raw_fixtures (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
    FROM @stg_api_football
)
PATTERN = '.*endpoint=fixtures/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;

-- Example: load raw_fixtures_statistics
COPY INTO raw_fixtures_statistics (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
    FROM @stg_api_football
)
PATTERN = '.*endpoint=fixtures_statistics/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;
*/

-- =============================================================================
-- Query examples — access nested JSON via the raw VARIANT column
-- =============================================================================

/*
-- All fixture results
SELECT
    f.value:fixture:id::INT           AS fixture_id,
    f.value:fixture:date::TIMESTAMP   AS fixture_date,
    f.value:teams:home:name::VARCHAR  AS home_team,
    f.value:teams:away:name::VARCHAR  AS away_team,
    f.value:goals:home::INT           AS goals_home,
    f.value:goals:away::INT           AS goals_away
FROM raw_fixtures,
     LATERAL FLATTEN(input => raw:payload:response) f
WHERE raw:endpoint::VARCHAR = '/fixtures';

-- Player stats from a fixture
SELECT
    t.value:team:name::VARCHAR           AS team_name,
    p.value:player:id::INT               AS player_id,
    p.value:player:name::VARCHAR         AS player_name,
    p.value:statistics[0]:games:minutes::INT AS minutes,
    p.value:statistics[0]:goals:total::INT   AS goals,
    p.value:statistics[0]:goals:assists::INT AS assists
FROM raw_fixtures_players,
     LATERAL FLATTEN(input => raw:payload:response) t,
     LATERAL FLATTEN(input => t.value:players) p;
*/
