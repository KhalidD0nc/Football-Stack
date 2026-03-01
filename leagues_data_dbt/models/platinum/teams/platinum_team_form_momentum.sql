{{ config(materialized='table') }}

WITH match_results AS (
    SELECT
        e.team_id,
        e.team_name,
        e.league_id,
        e.season,
        e.fixture_id,
        e.fixture_date,
        e.goals_scored,
        CASE 
            WHEN e.home_away = 'Home' THEN e.away_goals
            ELSE e.home_goals
        END as goals_conceded,
        CASE 
            WHEN e.goals_scored > CASE WHEN e.home_away = 'Home' THEN e.away_goals ELSE e.home_goals END THEN 'W'
            WHEN e.goals_scored = CASE WHEN e.home_away = 'Home' THEN e.away_goals ELSE e.home_goals END THEN 'D'
            ELSE 'L'
        END as result,
        ROW_NUMBER() OVER (
            PARTITION BY e.team_id, e.league_id 
            ORDER BY e.fixture_date DESC
        ) as match_recency
    FROM {{ ref('gold_match_team_performance') }} e
),

weighted AS (
    SELECT
        team_id,
        team_name,
        league_id,
        season,
        SUM(CASE 
            WHEN result = 'W' THEN (6 - match_recency) * 3
            WHEN result = 'D' THEN (6 - match_recency) * 1
            ELSE 0
        END) as weighted_points,
        COUNT(*) as matches_included,
        LISTAGG(result, '') WITHIN GROUP (ORDER BY match_recency DESC) as recent_form_string,
        SUM(CASE WHEN result = 'W' THEN 1 ELSE 0 END) as recent_wins,
        SUM(CASE WHEN result = 'D' THEN 1 ELSE 0 END) as recent_draws,
        SUM(CASE WHEN result = 'L' THEN 1 ELSE 0 END) as recent_losses,
        SUM(goals_scored) as recent_goals_scored,
        SUM(goals_conceded) as recent_goals_conceded
    FROM match_results
    WHERE match_recency <= 5
    GROUP BY team_id, team_name, league_id, season
)

SELECT
    team_id,
    team_name,
    league_id,
    season,
    matches_included,
    recent_form_string,
    recent_wins,
    recent_draws,
    recent_losses,
    recent_goals_scored,
    recent_goals_conceded,
    weighted_points,
    ROUND((weighted_points / 45.0) * 100, 1) as momentum_index,
    RANK() OVER (PARTITION BY league_id ORDER BY weighted_points DESC) as momentum_rank
FROM weighted