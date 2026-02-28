{{ config(materialized='table') }}

SELECT
    fixture_id,
    league_id,
    season,
    round_name,
    fixture_date,
    status_short,
    status_long,
    status_elapsed,
    referee,
    venue_name,
    venue_city,
    home_team_id,
    home_team_name,
    home_team_logo,
    away_team_id,
    away_team_name,
    away_team_logo,
    home_goals,
    away_goals,
    halftime_home_goals,
    halftime_away_goals,
    fulltime_home_goals,
    fulltime_away_goals,
    penalty_home_goals,
    penalty_away_goals
FROM {{ ref('stg_fixtures') }}
WHERE status_short IN ('FT', 'AET', 'PEN')
ORDER BY fixture_date DESC
