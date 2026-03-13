{{ config(materialized='table') }}

SELECT
    fixture_id,
    league_id,
    season,
    round_name,
    fixture_date,
    fixture_timestamp,
    status_short,
    status_long,
    status_elapsed,
    referee,
    venue_id,
    venue_name,
    venue_city,
    fixture_timezone,

    -- Home team
    home_team_id,
    home_team_name,
    home_team_logo,

    -- Away team
    away_team_id,
    away_team_name,
    away_team_logo,

    -- Live scores (null for NS, populated for live matches)
    home_goals,
    away_goals,
    halftime_home_goals,
    halftime_away_goals

FROM {{ ref('stg_fixtures') }}
WHERE status_short IN ('NS', '1H', '2H', 'HT', 'ET', 'BT', 'P', 'SUSP', 'INT')
ORDER BY fixture_date ASC
