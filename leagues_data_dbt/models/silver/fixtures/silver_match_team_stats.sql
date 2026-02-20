{{config(materialized='table')}}

WITH source AS (SELECT * FROM {{ ref('stg_match_team_stats') }})
SELECT
    fixture_id, team_id, team_name,
    ball_possession_pct, passes_pct, expected_goals, goals_prevented,
    total_shots, shots_on_goal, shots_off_goal, blocked_shots,
    shots_inside_box, shots_outside_box, corner_kicks, offsides, fouls,
    yellow_cards, red_cards, goalkeeper_saves, passes_accurate, total_passes,
    league_id, season
FROM source