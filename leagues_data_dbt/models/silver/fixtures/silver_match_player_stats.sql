{{config(materialized='table')}}

WITH source AS (SELECT * FROM {{ ref('stg_match_player_stats') }})
SELECT
    fixture_id, team_id, team_name, team_logo,
    player_id, player_name, player_photo, shirt_number, position,
    rating, minutes_played, is_captain, is_substitute, offsides,
    shots_total, shots_on_target, goals_total, goals_conceded, assists,
    saves, passes_total, key_passes, passes_accuracy,
    tackles_total, blocks, interceptions, duels_total, duels_won,
    dribbles_attempted, dribbles_success, dribbled_past,
    fouls_drawn, fouls_committed, yellow_cards, red_cards,
    penalties_won, penalties_committed, penalties_scored,
    penalties_missed, penalties_saved,
    league_id, season
FROM source