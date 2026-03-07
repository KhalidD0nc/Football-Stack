{{ config(materialized='table') }}

WITH fixture_base AS (
    -- One row per fixture from gold_match_summary
    SELECT
        fixture_id,
        league_id,
        season,
        round_name,
        fixture_date,
        status_short,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        home_goals,
        away_goals,
        halftime_home_goals,
        halftime_away_goals,
        fulltime_home_goals,
        fulltime_away_goals,
        ABS(home_goals - away_goals)                         AS goal_margin,
        home_goals + away_goals                              AS total_goals,
        CASE
            WHEN home_goals > away_goals THEN home_team_name
            WHEN away_goals > home_goals THEN away_team_name
            ELSE 'Draw'
        END                                                  AS actual_winner
    FROM {{ ref('gold_match_summary') }}
    WHERE status_short IN ('FT', 'AET', 'PEN')
),

team_stats AS (
    -- Pivot gold_match_team_performance from 2-rows-per-fixture to 1-row-per-fixture
    SELECT
        fixture_id,
        MAX(CASE WHEN home_away = 'Home' THEN ball_possession_pct END)  AS home_possession,
        MAX(CASE WHEN home_away = 'Away' THEN ball_possession_pct END)  AS away_possession,
        MAX(CASE WHEN home_away = 'Home' THEN total_shots END)          AS home_shots,
        MAX(CASE WHEN home_away = 'Away' THEN total_shots END)          AS away_shots,
        MAX(CASE WHEN home_away = 'Home' THEN shots_on_goal END)        AS home_shots_on_target,
        MAX(CASE WHEN home_away = 'Away' THEN shots_on_goal END)        AS away_shots_on_target,
        MAX(CASE WHEN home_away = 'Home' THEN expected_goals END)       AS home_xg,
        MAX(CASE WHEN home_away = 'Away' THEN expected_goals END)       AS away_xg,
        MAX(CASE WHEN home_away = 'Home' THEN passes_pct END)           AS home_pass_accuracy,
        MAX(CASE WHEN home_away = 'Away' THEN passes_pct END)           AS away_pass_accuracy,
        SUM(fouls)                                                       AS total_fouls,
        SUM(yellow_cards)                                                AS total_yellows,
        SUM(red_cards)                                                   AS total_reds,
        SUM(corner_kicks)                                                AS total_corners
    FROM {{ ref('gold_match_team_performance') }}
    GROUP BY fixture_id
),

combined AS (
    SELECT
        f.fixture_id,
        f.league_id,
        f.season,
        f.round_name,
        f.fixture_date,
        f.home_team_id,
        f.home_team_name,
        f.away_team_id,
        f.away_team_name,
        f.home_goals,
        f.away_goals,
        f.halftime_home_goals,
        f.halftime_away_goals,
        f.total_goals,
        f.goal_margin,
        f.actual_winner,
        -- Halftime swing: did the match result change after HT?
        CASE
            WHEN f.halftime_home_goals > f.halftime_away_goals AND f.home_goals > f.away_goals THEN 'Home Led & Won'
            WHEN f.halftime_away_goals > f.halftime_home_goals AND f.away_goals > f.home_goals THEN 'Away Led & Won'
            WHEN f.halftime_home_goals > f.halftime_away_goals AND f.away_goals > f.home_goals THEN 'Away Comeback'
            WHEN f.halftime_away_goals > f.halftime_home_goals AND f.home_goals > f.away_goals THEN 'Home Comeback'
            WHEN f.halftime_home_goals = f.halftime_away_goals AND f.home_goals > f.away_goals THEN 'Home Won From Level'
            WHEN f.halftime_home_goals = f.halftime_away_goals AND f.away_goals > f.home_goals THEN 'Away Won From Level'
            ELSE 'Level Throughout'
        END                                                             AS match_narrative,
        -- Team performance metrics (nullable when stats unavailable)
        t.home_possession,
        t.away_possession,
        t.home_shots,
        t.away_shots,
        t.home_shots_on_target,
        t.away_shots_on_target,
        t.home_xg,
        t.away_xg,
        t.home_pass_accuracy,
        t.away_pass_accuracy,
        t.total_fouls,
        t.total_yellows,
        t.total_reds,
        t.total_corners,
        -- Dominance: did the stats-dominant team win?
        CASE
            WHEN t.home_possession IS NULL THEN NULL
            WHEN t.home_shots > t.away_shots AND f.home_goals > f.away_goals THEN TRUE
            WHEN t.away_shots > t.home_shots AND f.away_goals > f.home_goals THEN TRUE
            ELSE FALSE
        END                                                             AS dominant_team_won,
        -- xG vs actual: over or under performance
        ROUND(f.home_goals - COALESCE(t.home_xg, 0), 2)               AS home_xg_overperformance,
        ROUND(f.away_goals - COALESCE(t.away_xg, 0), 2)               AS away_xg_overperformance
    FROM fixture_base f
    LEFT JOIN team_stats t ON f.fixture_id = t.fixture_id
),

classified AS (
    SELECT
        *,
        -- Match profile label for AI agent context
        CASE
            WHEN total_goals >= 5                                   THEN 'Thriller'
            WHEN total_goals = 0                                    THEN 'Goalless'
            WHEN goal_margin >= 3                                   THEN 'One-Sided'
            WHEN match_narrative ILIKE '%Comeback%'                 THEN 'Comeback'
            WHEN total_goals >= 3 AND goal_margin <= 1              THEN 'High Scoring'
            WHEN COALESCE(total_fouls, 0) >= 30
              OR COALESCE(total_yellows, 0) >= 6                    THEN 'High Intensity'
            ELSE 'Competitive'
        END                                                         AS match_profile
    FROM combined
)

SELECT
    fixture_id,
    league_id,
    season,
    round_name,
    fixture_date,
    home_team_id,
    home_team_name,
    away_team_id,
    away_team_name,
    home_goals,
    away_goals,
    halftime_home_goals,
    halftime_away_goals,
    total_goals,
    goal_margin,
    actual_winner,
    match_narrative,
    match_profile,
    home_possession,
    away_possession,
    home_shots,
    away_shots,
    home_shots_on_target,
    away_shots_on_target,
    home_xg,
    away_xg,
    home_xg_overperformance,
    away_xg_overperformance,
    home_pass_accuracy,
    away_pass_accuracy,
    total_fouls,
    total_yellows,
    total_reds,
    total_corners,
    dominant_team_won
FROM classified