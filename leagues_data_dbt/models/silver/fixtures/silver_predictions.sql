{{config(materialized='table')}}

WITH source AS (SELECT * FROM {{ ref('stg_predictions') }})
SELECT
    fixture_id, predicted_winner_team_id, predicted_winner_team_name,
    predicted_winner_comment, betting_advice,
    home_win_percent, draw_percent, away_win_percent,
    home_win_percent_value, draw_percent_value, away_win_percent_value,
    home_team_id, home_team_name, away_team_id, away_team_name,
    comparison_form_home, comparison_form_away,
    comparison_attack_home, comparison_attack_away,
    comparison_defense_home, comparison_defense_away,
    comparison_poisson_home, comparison_poisson_away,
    comparison_h2h_home, comparison_h2h_away,
    comparison_goals_home, comparison_goals_away,
    comparison_total_home, comparison_total_away,
    league_id, season
FROM source