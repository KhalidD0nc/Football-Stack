{{ config(materialized='table') }}

WITH season_avg AS (
    SELECT
        player_id,
        player_name,
        team_name,
        position,
        league_id,
        season,
        ROUND(AVG(rating), 2)        as season_avg_rating,
        ROUND(AVG(goals_total), 3)   as season_avg_goals,
        ROUND(AVG(assists), 3)       as season_avg_assists,
        ROUND(AVG(key_passes), 3)    as season_avg_key_passes,
        ROUND(AVG(duels_won), 3)     as season_avg_duels_won,
        COUNT(*)                      as total_matches
    FROM {{ ref('gold_player_performance_mart') }}
    WHERE rating IS NOT NULL
    GROUP BY player_id, player_name, team_name, position, league_id, season
),

last_5 AS (
    SELECT
        player_id,
        league_id,
        season,
        ROUND(AVG(rating), 2)        as last5_avg_rating,
        ROUND(AVG(goals_total), 3)   as last5_avg_goals,
        ROUND(AVG(assists), 3)       as last5_avg_assists,
        ROUND(AVG(key_passes), 3)    as last5_avg_key_passes,
        ROUND(AVG(duels_won), 3)     as last5_avg_duels_won,
        COUNT(*)                      as last5_matches
    FROM (
        SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY player_id, league_id, season
                ORDER BY fixture_date DESC
            ) as recency_rank
        FROM {{ ref('gold_player_performance_mart') }}
        WHERE rating IS NOT NULL
    ) subq
    WHERE recency_rank <= 5
    GROUP BY player_id, league_id, season
),

trend AS (
    SELECT
        s.player_id,
        s.player_name,
        s.team_name,
        s.position,
        s.league_id,
        s.season,
        s.total_matches,
        s.season_avg_rating,
        l.last5_avg_rating,
        l.last5_matches,
        s.season_avg_goals,
        l.last5_avg_goals,
        s.season_avg_assists,
        l.last5_avg_assists,
        ROUND(l.last5_avg_rating - s.season_avg_rating, 2) as rating_delta,
        CASE
            WHEN l.last5_avg_rating - s.season_avg_rating >= 0.3  THEN 'Peaking'
            WHEN l.last5_avg_rating - s.season_avg_rating >= 0.1  THEN 'Improving'
            WHEN l.last5_avg_rating - s.season_avg_rating >= -0.1 THEN 'Consistent'
            WHEN l.last5_avg_rating - s.season_avg_rating >= -0.3 THEN 'Declining'
            ELSE 'Poor Form'
        END as form_trend,
        ROUND(
            LEAST(GREATEST(
                50 + (l.last5_avg_rating - s.season_avg_rating) * 50, 0
            ), 100), 1
        ) as trend_score
    FROM season_avg s
    JOIN last_5 l
        ON s.player_id = l.player_id
        AND s.league_id = l.league_id
        AND s.season = l.season
    WHERE s.total_matches >= 5
)

SELECT
    player_id,
    player_name,
    team_name,
    position,
    league_id,
    season,
    total_matches,
    season_avg_rating,
    last5_avg_rating,
    last5_matches,
    rating_delta,
    season_avg_goals,
    last5_avg_goals,
    season_avg_assists,
    last5_avg_assists,
    form_trend,
    trend_score
FROM trend