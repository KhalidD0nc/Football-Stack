{{config(materialized='table')}}

WITH source AS (SELECT * FROM {{ ref('stg_injuries') }})
SELECT
    player_id, player_name, player_photo,
    team_id, team_name, team_logo,
    fixture_id, fixture_timezone, fixture_date, fixture_timestamp,
    injury_league_id, injury_league_name, injury_league_country,
    injury_type, injury_reason,
    league_id, season
FROM source