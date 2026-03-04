{{ config(materialized='table') }}

WITH primary_position AS (
    SELECT player_id, league_id, season, position
    FROM (
        SELECT
            player_id, league_id, season, position,
            SUM(total_minutes) as total_minutes,
            ROW_NUMBER() OVER (
                PARTITION BY player_id, league_id, season
                ORDER BY SUM(total_minutes) DESC
            ) as rn
        FROM {{ ref('gold_player_season_summary') }}
        WHERE position != 'G'
        GROUP BY player_id, league_id, season, position
    ) subq
    WHERE rn = 1
),

base AS (
    SELECT
        s.player_id,
        s.player_name,
        s.team_name,
        p.position,
        s.league_id,
        s.season,
        SUM(s.matches_played)               as matches_played,
        SUM(s.total_minutes)                as total_minutes,
        SUM(s.season_goals)                 as season_goals,
        SUM(s.season_assists)               as season_assists,
        SUM(s.season_key_passes)            as season_key_passes,
        SUM(s.season_tackles)               as season_tackles,
        SUM(s.season_interceptions)         as season_interceptions,
        SUM(s.season_shots)                 as season_shots,
        SUM(s.season_dribbles_success)      as season_dribbles_success,
        AVG(s.avg_rating)                   as avg_rating,
        AVG(s.duel_win_rate)                as duel_win_rate,
        AVG(s.dribble_success_rate)         as dribble_success_rate,
        AVG(s.shot_accuracy)                as shot_accuracy
    FROM {{ ref('gold_player_season_summary') }} s
    JOIN primary_position p
        ON s.player_id = p.player_id
        AND s.league_id = p.league_id
        AND s.season = p.season
    GROUP BY s.player_id, s.player_name, s.team_name, p.position, s.league_id, s.season
    HAVING SUM(s.total_minutes) >= 270
       AND SUM(s.matches_played) >= 3
),

per90 AS (
    SELECT
        player_id,
        player_name,
        team_name,
        position,
        league_id,
        season,
        matches_played,
        total_minutes,
        ROUND(avg_rating, 2)                                            as avg_rating,
        ROUND(season_goals / total_minutes * 90, 3)                    as goals_p90,
        ROUND(season_assists / total_minutes * 90, 3)                  as assists_p90,
        ROUND(season_key_passes / total_minutes * 90, 3)               as key_passes_p90,
        ROUND(season_tackles / total_minutes * 90, 3)                  as tackles_p90,
        ROUND(season_interceptions / total_minutes * 90, 3)            as interceptions_p90,
        ROUND(season_shots / total_minutes * 90, 3)                    as shots_p90,
        ROUND(season_dribbles_success / total_minutes * 90, 3)         as dribbles_p90,
        ROUND(COALESCE(duel_win_rate, 0), 3)                           as duel_win_rate,
        ROUND(COALESCE(dribble_success_rate, 0), 3)                    as dribble_success_rate,
        ROUND(COALESCE(shot_accuracy, 0), 3)                           as shot_accuracy,
        CASE
            WHEN total_minutes < 630  THEN 'Rotation'
            WHEN total_minutes < 1350 THEN 'Regular'
            ELSE 'First Choice'
        END as minutes_bracket,
        CASE
            WHEN position = 'F' THEN
                ROUND(LEAST(GREATEST((
                    (season_goals / total_minutes * 90 * 40) +
                    (season_assists / total_minutes * 90 * 20) +
                    (COALESCE(shot_accuracy, 0) * 15) +
                    (COALESCE(dribble_success_rate, 0) * 10) +
                    ((COALESCE(avg_rating, 6.0) - 6.0) / 2.0 * 15)
                ), 0), 100), 1)
            WHEN position = 'M' THEN
                ROUND(LEAST(GREATEST((
                    (season_goals / total_minutes * 90 * 20) +
                    (season_assists / total_minutes * 90 * 20) +
                    (season_key_passes / total_minutes * 90 * 15) +
                    (COALESCE(duel_win_rate, 0) * 15) +
                    (COALESCE(dribble_success_rate, 0) * 10) +
                    ((COALESCE(avg_rating, 6.0) - 6.0) / 2.0 * 20)
                ), 0), 100), 1)
            WHEN position = 'D' THEN
                ROUND(LEAST(GREATEST((
                    (season_tackles / total_minutes * 90 * 15) +
                    (season_interceptions / total_minutes * 90 * 15) +
                    (COALESCE(duel_win_rate, 0) * 20) +
                    (season_assists / total_minutes * 90 * 10) +
                    ((COALESCE(avg_rating, 6.0) - 6.0) / 2.0 * 20) +
                    (CASE WHEN COALESCE(avg_rating, 0) < 6.5 THEN -10 ELSE 0 END)
                ), 0), 100), 1)
            ELSE 0
        END as efficiency_score
    FROM base
)

SELECT
    player_id,
    player_name,
    team_name,
    position,
    league_id,
    season,
    matches_played,
    total_minutes,
    minutes_bracket,
    avg_rating,
    goals_p90,
    assists_p90,
    key_passes_p90,
    tackles_p90,
    interceptions_p90,
    shots_p90,
    dribbles_p90,
    duel_win_rate,
    dribble_success_rate,
    shot_accuracy,
    efficiency_score,
    RANK() OVER (PARTITION BY league_id, season, position, minutes_bracket ORDER BY efficiency_score DESC) as efficiency_rank
FROM per90