{{ config(materialized='table') }}

WITH home_away_split AS (
    SELECT
        team_id,
        team_name,
        league_id,
        season,
        COUNT(CASE WHEN home_away = 'Home' THEN 1 END) as home_matches,
        SUM(CASE WHEN home_away = 'Home' THEN goals_scored ELSE 0 END) as home_goals_scored,
        SUM(CASE WHEN home_away = 'Home' THEN away_goals ELSE 0 END) as home_goals_conceded,
        SUM(CASE WHEN home_away = 'Home' AND goals_scored > away_goals THEN 1 ELSE 0 END) as home_wins,
        SUM(CASE WHEN home_away = 'Home' AND goals_scored = away_goals THEN 1 ELSE 0 END) as home_draws,
        SUM(CASE WHEN home_away = 'Home' AND goals_scored < away_goals THEN 1 ELSE 0 END) as home_losses,
        COUNT(CASE WHEN home_away = 'Away' THEN 1 END) as away_matches,
        SUM(CASE WHEN home_away = 'Away' THEN goals_scored ELSE 0 END) as away_goals_scored,
        SUM(CASE WHEN home_away = 'Away' THEN home_goals ELSE 0 END) as away_goals_conceded,
        SUM(CASE WHEN home_away = 'Away' AND goals_scored > home_goals THEN 1 ELSE 0 END) as away_wins,
        SUM(CASE WHEN home_away = 'Away' AND goals_scored = home_goals THEN 1 ELSE 0 END) as away_draws,
        SUM(CASE WHEN home_away = 'Away' AND goals_scored < home_goals THEN 1 ELSE 0 END) as away_losses
    FROM {{ ref('gold_match_team_performance') }}
    GROUP BY team_id, team_name, league_id, season
),

fortress AS (
    SELECT
        team_id,
        team_name,
        league_id,
        season,
        home_matches,
        home_wins,
        home_draws,
        home_losses,
        home_goals_scored,
        home_goals_conceded,
        away_matches,
        away_wins,
        away_draws,
        away_losses,
        away_goals_scored,
        away_goals_conceded,
        ROUND(home_wins / NULLIF(home_matches, 0) * 100, 1) as home_win_pct,
        ROUND(away_wins / NULLIF(away_matches, 0) * 100, 1) as away_win_pct,
        ROUND((home_wins / NULLIF(home_matches, 0)) - (away_wins / NULLIF(away_matches, 0)), 3) as win_rate_diff,
        ROUND(home_goals_scored / NULLIF(home_matches, 0), 2) as home_goals_per_match,
        ROUND(away_goals_scored / NULLIF(away_matches, 0), 2) as away_goals_per_match,
        ROUND(
            LEAST(GREATEST(
                (
                    ((home_wins / NULLIF(home_matches, 0)) - (away_wins / NULLIF(away_matches, 0))) * 0.6 +
                    ((home_goals_scored / NULLIF(home_matches, 0)) - (away_goals_scored / NULLIF(away_matches, 0))) * 0.2 +
                    ((away_goals_conceded / NULLIF(away_matches, 0)) - (home_goals_conceded / NULLIF(home_matches, 0))) * 0.2
                ) * 100, 0), 100
            ), 1
        ) as fortress_score
    FROM home_away_split
)

SELECT
    team_id,
    team_name,
    league_id,
    season,
    home_matches,
    home_wins,
    home_draws,
    home_losses,
    home_goals_scored,
    home_goals_conceded,
    away_matches,
    away_wins,
    away_draws,
    away_losses,
    away_goals_scored,
    away_goals_conceded,
    home_win_pct,
    away_win_pct,
    win_rate_diff,
    home_goals_per_match,
    away_goals_per_match,
    fortress_score,
    RANK() OVER (PARTITION BY league_id ORDER BY fortress_score DESC) as fortress_rank
FROM fortress