{{ config(materialized='table') }}

WITH goal_events AS (
    SELECT
        e.team_id,
        e.team_name,
        e.event_detail,
        e.event_minute,
        e.event_extra_minute,
        e.league_id,
        e.season
    FROM {{ ref('silver_match_events') }} e
    WHERE e.event_type = 'Goal'
),

team_info AS (
    SELECT
        t.team_id,
        t.league_id,
        t.season,
        t.all_played as matches_played,
        r.country
    FROM {{ ref('silver_teams') }} t
    LEFT JOIN {{ source('gold', 'ref_leagues') }} r ON t.league_id = r.league_id
)

SELECT
    g.team_id,
    g.team_name,
    t.league_id,
    t.season,
    t.country,
    t.matches_played,

    -- Goal types
    COUNT(*)                                                                 as goals_scored,
    COUNT(CASE WHEN g.event_detail = 'Normal Goal' THEN 1 END)              as open_play_goals,
    COUNT(CASE WHEN g.event_detail = 'Penalty'     THEN 1 END)              as penalty_goals,
    COUNT(CASE WHEN g.event_detail = 'Own Goal'    THEN 1 END)              as own_goals_scored,

    -- Goal timing
    COUNT(CASE WHEN g.event_minute <= 30 THEN 1 END)                        as early_goals,
    COUNT(CASE WHEN g.event_minute > 30 AND g.event_minute <= 60 THEN 1 END) as mid_goals,
    COUNT(CASE WHEN g.event_minute > 60 AND g.event_minute <= 90 THEN 1 END) as late_goals,
    COUNT(CASE WHEN g.event_extra_minute IS NOT NULL THEN 1 END)             as stoppage_goals,

    -- Rates
    ROUND(COUNT(*) * 1.0 / t.matches_played, 3)                             as goals_per_match,
    ROUND(COUNT(CASE WHEN g.event_detail = 'Penalty' THEN 1 END) * 1.0 /
          NULLIF(COUNT(*), 0), 3)                                            as penalty_goal_ratio

FROM goal_events g
JOIN team_info t ON g.team_id = t.team_id AND g.league_id = t.league_id AND g.season = t.season
GROUP BY g.team_id, g.team_name, t.league_id, t.season, t.country, t.matches_played
ORDER BY goals_per_match DESC