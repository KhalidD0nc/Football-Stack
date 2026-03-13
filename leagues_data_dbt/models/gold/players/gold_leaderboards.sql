{{ config(materialized='table') }}

WITH source AS (
    SELECT
        ranking_type,
        rank,
        player_id,
        player_name,
        player_first_name,
        player_last_name,
        player_age,
        player_nationality,
        player_photo_url,
        team_id,
        team_name,
        league_id,
        season,
        appearances,
        minutes_played,
        position,
        rating,
        goals_total,
        assists_total,
        yellow_cards,
        red_cards
    FROM {{ ref('stg_player_leaderboards') }}
)

SELECT
    ranking_type,
    rank,
    player_id,
    player_name,
    player_first_name,
    player_last_name,
    player_age,
    player_nationality,
    player_photo_url,
    team_id,
    team_name,
    league_id,
    season,
    appearances,
    minutes_played,
    position,
    rating,
    goals_total,
    assists_total,
    yellow_cards,
    red_cards
FROM source
ORDER BY league_id, ranking_type, rank
