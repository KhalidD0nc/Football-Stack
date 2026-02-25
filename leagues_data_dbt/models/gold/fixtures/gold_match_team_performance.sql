{{ config(materialized='table') }}

WITH match_events_agg AS (
    SELECT
        fixture_id,
        team_id,
        COUNT(CASE WHEN event_type = 'Goal'                                    THEN 1 END) as goals_scored,
        COUNT(CASE WHEN event_type = 'Goal' AND event_detail = 'Penalty'       THEN 1 END) as penalty_goals,
        COUNT(CASE WHEN event_type = 'Goal' AND event_detail = 'Own Goal'      THEN 1 END) as own_goals,
        COUNT(CASE WHEN event_type = 'subst'                                   THEN 1 END) as substitutions_made,
        COUNT(CASE WHEN event_type = 'Var'                                     THEN 1 END) as var_incidents
    FROM {{ ref('silver_match_events') }}
    GROUP BY fixture_id, team_id
),

fixture_context AS (
    SELECT
        fixture_id,
        fixture_date,
        round_name,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        home_goals,
        away_goals,
        CASE
            WHEN home_goals > away_goals THEN home_team_name
            WHEN away_goals > home_goals THEN away_team_name
            ELSE 'Draw'
        END as winner
    FROM {{ ref('silver_fixture') }}
    WHERE status_short = 'FT'
)

SELECT
    f.fixture_id,
    f.fixture_date,
    f.round_name,
    f.home_team_name,
    f.away_team_name,
    f.home_goals,
    f.away_goals,
    f.winner,

    -- Team context
    s.team_id,
    s.team_name,
    CASE WHEN s.team_id = f.home_team_id THEN 'Home' ELSE 'Away' END as home_away,

    -- Team stats
    s.ball_possession_pct,
    s.total_shots,
    s.shots_on_goal,
    s.expected_goals,
    s.corner_kicks,
    s.fouls,
    s.yellow_cards,
    s.red_cards,
    s.passes_accurate,
    s.total_passes,
    s.passes_pct,
    s.goalkeeper_saves,

    -- Events
    COALESCE(e.goals_scored, 0)       as goals_scored,
    COALESCE(e.penalty_goals, 0)      as penalty_goals,
    COALESCE(e.own_goals, 0)          as own_goals,
    COALESCE(e.substitutions_made, 0) as substitutions_made,
    COALESCE(e.var_incidents, 0)      as var_incidents,

    s.league_id,
    s.season

FROM fixture_context f
JOIN {{ ref('silver_match_team_stats') }} s ON f.fixture_id = s.fixture_id
LEFT JOIN match_events_agg e ON f.fixture_id = e.fixture_id AND s.team_id = e.team_id
ORDER BY f.fixture_date DESC