{{config(materialized='table')}}

WITH source AS (SELECT * FROM {{ ref('stg_lineup_players') }})
SELECT
    fixture_id, team_id, team_name,
    team_colors_player_primary, team_colors_player_number, team_colors_player_border,
    formation, coach_id, coach_name, coach_photo,
    lineup_bucket, player_id, player_name, player_number, player_pos, grid,
    league_id, season
FROM source
