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
        SUM(s.matches_played)           as matches_played,
        SUM(s.total_minutes)            as total_minutes,
        SUM(s.season_duels)             as season_duels,
        SUM(s.season_duels_won)         as season_duels_won,
        SUM(s.season_tackles)           as season_tackles,
        SUM(s.season_interceptions)     as season_interceptions,
        SUM(s.season_fouls_drawn)       as season_fouls_drawn,
        SUM(s.season_fouls_committed)   as season_fouls_committed,
        AVG(s.avg_rating)               as avg_rating,
        AVG(s.duel_win_rate)            as duel_win_rate
    FROM {{ ref('gold_player_season_summary') }} s
    JOIN primary_position p
        ON s.player_id = p.player_id
        AND s.league_id = p.league_id
        AND s.season = p.season
    GROUP BY s.player_id, s.player_name, s.team_name, p.position, s.league_id, s.season
    HAVING SUM(s.total_minutes) >= 270
       AND SUM(s.matches_played) >= 3
),

dominance AS (
    SELECT
        player_id,
        player_name,
        team_name,
        position,
        league_id,
        season,
        matches_played,
        total_minutes,
        season_duels,
        season_duels_won,
        season_tackles,
        season_interceptions,
        season_fouls_drawn,
        season_fouls_committed,
        ROUND(avg_rating, 2)                                                as avg_rating,
        ROUND(COALESCE(duel_win_rate, 0), 3)                                as duel_win_rate,
        ROUND(season_duels / NULLIF(total_minutes, 0) * 90, 2)             as duels_p90,
        ROUND(season_duels_won / NULLIF(total_minutes, 0) * 90, 2)         as duels_won_p90,
        ROUND(season_tackles / NULLIF(total_minutes, 0) * 90, 2)           as tackles_p90,
        ROUND(season_interceptions / NULLIF(total_minutes, 0) * 90, 2)     as interceptions_p90,
        ROUND(season_fouls_drawn / NULLIF(total_minutes, 0) * 90, 2)       as fouls_drawn_p90,
        ROUND(
            LEAST(GREATEST((
                (COALESCE(duel_win_rate, 0) * 40) +
                (season_duels_won / NULLIF(total_minutes, 0) * 90 * 5) +
                ((season_tackles + season_interceptions) / NULLIF(total_minutes, 0) * 90 * 5) +
                (season_fouls_drawn / NULLIF(total_minutes, 0) * 90 * 5)
            ), 0), 100), 1
        ) as duel_dominance_score,
        CASE
            WHEN COALESCE(duel_win_rate, 0) >= 0.65 THEN 'Dominant'
            WHEN COALESCE(duel_win_rate, 0) >= 0.55 THEN 'Strong'
            WHEN COALESCE(duel_win_rate, 0) >= 0.45 THEN 'Competitive'
            WHEN COALESCE(duel_win_rate, 0) >= 0.35 THEN 'Struggling'
            ELSE 'Weak'
        END as dominance_label
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
    avg_rating,
    season_duels,
    season_duels_won,
    duel_win_rate,
    duels_p90,
    duels_won_p90,
    tackles_p90,
    interceptions_p90,
    fouls_drawn_p90,
    duel_dominance_score,
    dominance_label,
    RANK() OVER (PARTITION BY league_id, season ORDER BY duel_dominance_score DESC) as dominance_rank
FROM dominance
WHERE season_duels >= 20