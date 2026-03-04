{{ config(materialized='table') }}

WITH scoring AS (
    SELECT
        team_id,
        team_name,
        league_id,
        season,
        goals_scored,
        open_play_goals,
        penalty_goals,
        goals_per_match,
        early_goals,
        mid_goals,
        late_goals,
        stoppage_goals,
        ROUND(early_goals / NULLIF(goals_scored, 0) * 100, 1) as early_goal_pct,
        ROUND(mid_goals / NULLIF(goals_scored, 0) * 100, 1) as mid_goal_pct,
        ROUND(late_goals / NULLIF(goals_scored, 0) * 100, 1) as late_goal_pct,
        ROUND(stoppage_goals / NULLIF(goals_scored, 0) * 100, 1) as stoppage_goal_pct,
        ROUND(penalty_goals / NULLIF(goals_scored, 0) * 100, 1) as penalty_goal_pct,
        ROUND(open_play_goals / NULLIF(goals_scored, 0) * 100, 1) as open_play_goal_pct
    FROM {{ ref('gold_team_scoring_profile') }}
),

classified AS (
    SELECT
        team_id,
        team_name,
        league_id,
        season,
        goals_scored,
        goals_per_match,
        open_play_goals,
        penalty_goals,
        early_goals,
        mid_goals,
        late_goals,
        stoppage_goals,
        early_goal_pct,
        mid_goal_pct,
        late_goal_pct,
        stoppage_goal_pct,
        penalty_goal_pct,
        open_play_goal_pct,
        CASE
            WHEN penalty_goal_pct >= 25 THEN 'Penalty Reliant'
            WHEN early_goal_pct >= 35 THEN 'Early Finisher'
            WHEN (late_goal_pct + stoppage_goal_pct) >= 35 THEN 'Late Bloomer'
            WHEN mid_goal_pct >= 40 THEN 'Mid-Game Dominant'
            WHEN goals_per_match >= 2.5 THEN 'Clinical'
            WHEN goals_per_match <= 1.0 THEN 'Struggling'
            ELSE 'Balanced'
        END as attacking_style,
        CASE
            WHEN open_play_goal_pct >= 85 THEN 'Open Play Specialist'
            WHEN penalty_goal_pct >= 20 THEN 'Set Piece Dependent'
            WHEN (late_goal_pct + stoppage_goal_pct) >= 30 THEN 'Second Half Threat'
            WHEN early_goal_pct >= 30 THEN 'Fast Starter'
            ELSE 'Consistent'
        END as secondary_trait
    FROM scoring
)

SELECT
    team_id,
    team_name,
    league_id,
    season,
    goals_scored,
    goals_per_match,
    early_goal_pct,
    mid_goal_pct,
    late_goal_pct,
    stoppage_goal_pct,
    penalty_goal_pct,
    open_play_goal_pct,
    attacking_style,
    secondary_trait
FROM classified