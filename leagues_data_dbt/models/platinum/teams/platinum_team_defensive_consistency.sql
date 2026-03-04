{{ config(materialized='table') }}

WITH defense AS (
    SELECT
        team_id,
        team_name,
        league_id,
        season,
        matches_played,
        clean_sheets_total,
        failed_to_score_total,
        home_goals_against,
        away_goals_against,
        home_goals_against + away_goals_against as total_goals_conceded,
        home_win + home_draw + home_lose as home_matches,
        away_win + away_draw + away_lose as away_matches,
        ROUND(clean_sheets_total / NULLIF(matches_played, 0) * 100, 1) as clean_sheet_pct,
        ROUND((home_goals_against + away_goals_against) / NULLIF(matches_played, 0), 2) as goals_conceded_per_match,
        ROUND(home_goals_against / NULLIF(home_win + home_draw + home_lose, 0), 2) as home_goals_conceded_per_match,
        ROUND(away_goals_against / NULLIF(away_win + away_draw + away_lose, 0), 2) as away_goals_conceded_per_match
    FROM {{ ref('gold_team_performance_summary') }}
),

consistency AS (
    SELECT
        team_id,
        team_name,
        league_id,
        season,
        matches_played,
        clean_sheets_total,
        failed_to_score_total,
        total_goals_conceded,
        clean_sheet_pct,
        goals_conceded_per_match,
        home_goals_conceded_per_match,
        away_goals_conceded_per_match,
        ROUND(
            LEAST(
                (
                    (clean_sheet_pct * 0.5) +
                    (GREATEST(3.0 - goals_conceded_per_match, 0) / 3.0 * 30) +
                    (GREATEST(1.0 - ABS(home_goals_conceded_per_match - away_goals_conceded_per_match), 0) * 20)
                ), 100
            ), 1
        ) as defensive_consistency_score,
        CASE
            WHEN clean_sheet_pct >= 40 THEN 'Elite Defense'
            WHEN clean_sheet_pct >= 25 THEN 'Solid Defense'
            WHEN clean_sheet_pct >= 15 THEN 'Average Defense'
            WHEN goals_conceded_per_match >= 2.0 THEN 'Leaky Defense'
            ELSE 'Below Average'
        END as defensive_profile
    FROM defense
)

SELECT
    team_id,
    team_name,
    league_id,
    season,
    matches_played,
    clean_sheets_total,
    failed_to_score_total,
    clean_sheet_pct,
    total_goals_conceded,
    goals_conceded_per_match,
    home_goals_conceded_per_match,
    away_goals_conceded_per_match,
    defensive_consistency_score,
    defensive_profile,
    RANK() OVER (PARTITION BY league_id, season ORDER BY defensive_consistency_score DESC) as defensive_rank
FROM consistency