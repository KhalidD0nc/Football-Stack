{{ config(materialized='table') }}

WITH predictions AS (
    SELECT
        fixture_id,
        league_id,
        season,
        predicted_winner_team_id,
        predicted_winner_team_name,
        predicted_winner_comment,
        betting_advice,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        -- Normalize probability values (API returns as % strings, silver casts to numeric)
        home_win_percent_value,
        draw_percent_value,
        away_win_percent_value,
        -- Comparison scores from API model
        comparison_form_home,
        comparison_form_away,
        comparison_attack_home,
        comparison_attack_away,
        comparison_defense_home,
        comparison_defense_away,
        comparison_total_home,
        comparison_total_away
    FROM {{ ref('silver_predictions') }}
),

actuals AS (
    SELECT
        fixture_id,
        home_goals,
        away_goals,
        home_team_id,
        away_team_id,
        CASE
            WHEN home_goals > away_goals THEN home_team_id
            WHEN away_goals > home_goals THEN away_team_id
            ELSE NULL  -- draw has no winner team_id
        END                                             AS actual_winner_team_id,
        CASE
            WHEN home_goals > away_goals THEN 'Home'
            WHEN away_goals > home_goals THEN 'Away'
            ELSE 'Draw'
        END                                             AS actual_result
    FROM {{ ref('gold_match_summary') }}
    WHERE status_short IN ('FT', 'AET', 'PEN')
),

joined AS (
    SELECT
        p.fixture_id,
        p.league_id,
        p.season,
        p.home_team_id,
        p.home_team_name,
        p.away_team_id,
        p.away_team_name,
        p.predicted_winner_team_id,
        p.predicted_winner_team_name,
        p.predicted_winner_comment,
        p.betting_advice,
        p.home_win_percent_value,
        p.draw_percent_value,
        p.away_win_percent_value,
        p.comparison_form_home,
        p.comparison_form_away,
        p.comparison_attack_home,
        p.comparison_attack_away,
        p.comparison_defense_home,
        p.comparison_defense_away,
        p.comparison_total_home,
        p.comparison_total_away,
        a.home_goals,
        a.away_goals,
        a.actual_result,
        a.actual_winner_team_id,
        -- Was the prediction directionally correct?
        CASE
            WHEN a.actual_result IS NULL                                THEN NULL  -- match not played
            WHEN a.actual_result = 'Draw'
             AND p.predicted_winner_team_id IS NULL                     THEN TRUE
            WHEN p.predicted_winner_team_id = a.actual_winner_team_id  THEN TRUE
            ELSE FALSE
        END                                                             AS prediction_correct,
        -- Confidence: probability assigned to the predicted outcome
        CASE
            WHEN p.predicted_winner_team_id = p.home_team_id THEN p.home_win_percent_value
            WHEN p.predicted_winner_team_id = p.away_team_id THEN p.away_win_percent_value
            ELSE p.draw_percent_value
        END                                                             AS prediction_confidence,
        -- Unexpected result: high-confidence prediction that failed
        CASE
            WHEN a.actual_result IS NULL THEN NULL
            WHEN p.predicted_winner_team_id != a.actual_winner_team_id
             AND CASE
                    WHEN p.predicted_winner_team_id = p.home_team_id THEN p.home_win_percent_value
                    WHEN p.predicted_winner_team_id = p.away_team_id THEN p.away_win_percent_value
                    ELSE p.draw_percent_value
                 END >= 50                                              THEN TRUE
            ELSE FALSE
        END                                                             AS was_upset,
        CASE
            WHEN a.actual_result IS NULL THEN NULL
            WHEN p.predicted_winner_team_id = a.actual_winner_team_id
             AND CASE
                    WHEN p.predicted_winner_team_id = p.home_team_id THEN p.home_win_percent_value
                    WHEN p.predicted_winner_team_id = p.away_team_id THEN p.away_win_percent_value
                    ELSE p.draw_percent_value
                 END < 50                                               THEN TRUE
            ELSE FALSE
        END                                                             AS low_confidence_correct
    FROM predictions p
    INNER JOIN actuals a ON p.fixture_id = a.fixture_id
),

scored AS (
    SELECT
        *,
        -- Prediction outcome label for AI agent
        CASE
            WHEN prediction_correct IS NULL     THEN 'Pending'
            WHEN prediction_correct = TRUE
             AND prediction_confidence >= 60    THEN 'Confident & Correct'
            WHEN low_confidence_correct = TRUE   THEN 'Low Confidence Correct'
            WHEN prediction_correct = TRUE
             AND prediction_confidence < 60     THEN 'Correct'
            WHEN was_upset = TRUE               THEN 'High Confidence Wrong'
            WHEN actual_result = 'Draw'         THEN 'Draw Surprise'
            ELSE 'Incorrect'
        END                                                             AS prediction_outcome,
        -- Margin of victory vs predicted margin
        ABS(home_goals - away_goals)                                    AS actual_goal_margin,
        -- Score the model: 1 if correct, 0 if wrong (for accuracy aggregation)
        CASE WHEN prediction_correct = TRUE THEN 1.0 ELSE 0.0 END      AS accuracy_score
    FROM joined
)

SELECT
    fixture_id,
    league_id,
    season,
    home_team_id,
    home_team_name,
    away_team_id,
    away_team_name,
    home_goals,
    away_goals,
    actual_result,
    actual_goal_margin,
    predicted_winner_team_id,
    predicted_winner_team_name,
    predicted_winner_comment,
    betting_advice,
    home_win_percent_value,
    draw_percent_value,
    away_win_percent_value,
    prediction_confidence,
    prediction_correct,
    was_upset,
    low_confidence_correct,
    prediction_outcome,
    accuracy_score,
    comparison_form_home,
    comparison_form_away,
    comparison_attack_home,
    comparison_attack_away,
    comparison_defense_home,
    comparison_defense_away,
    comparison_total_home,
    comparison_total_away
FROM scored
