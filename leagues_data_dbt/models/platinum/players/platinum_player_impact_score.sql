{{ config(materialized='table') }}

WITH position_dedup AS (
    SELECT
        player_id,
        league_id,
        season,
        position
    FROM (
        SELECT
            player_id,
            league_id,
            season,
            position,
            ROW_NUMBER() OVER (
                PARTITION BY player_id, league_id, season
                ORDER BY total_minutes DESC
            ) as rn
        FROM {{ ref('gold_player_season_summary') }}
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
        SUM(s.season_goals)             as season_goals,
        SUM(s.season_assists)           as season_assists,
        SUM(s.season_key_passes)        as season_key_passes,
        SUM(s.season_tackles)           as season_tackles,
        SUM(s.season_interceptions)     as season_interceptions,
        SUM(s.season_duels_won)         as season_duels_won,
        AVG(s.avg_rating)               as avg_rating,
        AVG(s.goals_per_90)             as goals_per_90,
        AVG(s.assists_per_90)           as assists_per_90,
        AVG(s.duel_win_rate)            as duel_win_rate
    FROM {{ ref('gold_player_season_summary') }} s
    JOIN position_dedup p
        ON s.player_id = p.player_id
        AND s.league_id = p.league_id
        AND s.season = p.season
    WHERE p.position != 'G'
    GROUP BY s.player_id, s.player_name, s.team_name, p.position, s.league_id, s.season
    HAVING SUM(s.matches_played) >= 5
       AND SUM(s.total_minutes) >= 300
),

impact AS (
    SELECT
        player_id,
        player_name,
        team_name,
        position,
        league_id,
        season,
        matches_played,
        total_minutes,
        season_goals,
        season_assists,
        season_key_passes,
        season_tackles,
        season_interceptions,
        season_duels_won,
        avg_rating,
        goals_per_90,
        assists_per_90,
        ROUND(goals_per_90 * 30 + assists_per_90 * 20, 2)                         as attacking_impact,
        ROUND(season_key_passes / NULLIF(matches_played, 0) * 15, 2)              as creative_impact,
        ROUND(
            (season_tackles / NULLIF(matches_played, 0)) * 8 +
            (season_interceptions / NULLIF(matches_played, 0)) * 7 +
            duel_win_rate * 10, 2
        )                                                                           as defensive_impact,
        ROUND((avg_rating - 6.0) / 2.0 * 25, 2)                                  as consistency_impact
    FROM base
),

scored AS (
    SELECT
        *,
        ROUND(
            LEAST(GREATEST(
                attacking_impact + creative_impact + defensive_impact + consistency_impact
            , 0), 100), 1
        ) as impact_score
    FROM impact
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
    season_goals,
    season_assists,
    season_key_passes,
    season_tackles,
    season_interceptions,
    season_duels_won,
    avg_rating,
    goals_per_90,
    assists_per_90,
    attacking_impact,
    creative_impact,
    defensive_impact,
    consistency_impact,
    impact_score,
    RANK() OVER (PARTITION BY league_id, season ORDER BY impact_score DESC) as impact_rank
FROM scored