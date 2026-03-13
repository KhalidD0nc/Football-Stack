
{{ config(materialized='table') }}

SELECT
    fixture_id,
    team_id,
    team_name,
    formation,
    coach_id,
    coach_name,
    team_colors_player_primary,
    team_colors_player_number,
    team_colors_player_border,
    player_id,
    player_name,
    player_number,
    player_pos,
    grid,
    lineup_bucket,
    league_id,
    season
FROM {{ ref('stg_lineup_players') }}
ORDER BY fixture_id, team_id, lineup_bucket, player_number
