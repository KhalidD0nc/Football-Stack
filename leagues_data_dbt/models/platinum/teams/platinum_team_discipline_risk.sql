{{ config(materialized='table') }}

WITH card_data AS (
    SELECT
        t.team_id,
        t.team_name,
        t.league_id,
        t.season,
        t.matches_played,
        t.total_cards,
        t.cards_per_match,
        t.yellow_card_rate as yellow_rate,
        t.red_card_rate as red_rate,
        t.stoppage_red_rate,
        t.early_reds,
        t.late_reds,
        t.stoppage_reds,
        t.early_reds + t.late_reds + t.stoppage_reds as total_reds,
        t.late_reds + t.stoppage_reds as late_aggression_reds
    FROM {{ ref('gold_team_discipline_profile') }} t
),

risk AS (
    SELECT
        team_id,
        team_name,
        league_id,
        season,
        matches_played,
        total_cards,
        cards_per_match,
        yellow_rate,
        red_rate,
        stoppage_red_rate,
        total_reds,
        late_aggression_reds,
        ROUND(
            LEAST(
                (
                    (red_rate * 40) +
                    (yellow_rate / 5.0 * 30) +
                    (late_aggression_reds / NULLIF(matches_played, 0) * 20 * 10) +
                    (stoppage_red_rate * 10 * 10)
                ), 100
            ), 1
        ) as discipline_risk_score
    FROM card_data
)

SELECT
    team_id,
    team_name,
    league_id,
    season,
    matches_played,
    total_cards,
    cards_per_match,
    yellow_rate,
    red_rate,
    total_reds,
    late_aggression_reds,
    discipline_risk_score,
    RANK() OVER (PARTITION BY league_id ORDER BY discipline_risk_score DESC) as risk_rank
FROM risk