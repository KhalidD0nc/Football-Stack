{{ config(materialized='table') }}

SELECT
    player_id,
    player_name,
    team_name,
    position,
    league_id,
    season,

    -- Appearances
    COUNT(DISTINCT fixture_id)                                                      as matches_played,
    COALESCE(SUM(CASE WHEN is_substitute = FALSE THEN 1 END), 0)                   as starts,
    COALESCE(SUM(CASE WHEN is_substitute = TRUE THEN 1 END), 0)                    as sub_appearances,
    SUM(minutes_played)                                                             as total_minutes,

    -- Attack
    SUM(goals_total)                                                                as season_goals,
    SUM(assists)                                                                    as season_assists,
    SUM(shots_total)                                                                as season_shots,
    SUM(shots_on_target)                                                            as season_shots_on_target,
    SUM(key_passes)                                                                 as season_key_passes,

    -- Dribbling
    SUM(dribbles_attempted)                                                         as season_dribbles_attempted,
    SUM(dribbles_success)                                                           as season_dribbles_success,

    -- Defending
    SUM(tackles_total)                                                              as season_tackles,
    SUM(interceptions)                                                              as season_interceptions,
    SUM(blocks)                                                                     as season_blocks,
    SUM(duels_total)                                                                as season_duels,
    SUM(duels_won)                                                                  as season_duels_won,

    -- Discipline
    SUM(yellow_cards)                                                               as season_yellows,
    SUM(red_cards)                                                                  as season_reds,
    SUM(fouls_committed)                                                            as season_fouls_committed,
    SUM(fouls_drawn)                                                                as season_fouls_drawn,

    -- Averages and rates
    ROUND(AVG(rating), 2)                                                           as avg_rating,
    ROUND(SUM(goals_total) * 1.0 / NULLIF(SUM(minutes_played), 0) * 90, 3)        as goals_per_90,
    ROUND(SUM(assists) * 1.0 / NULLIF(SUM(minutes_played), 0) * 90, 3)            as assists_per_90,
    ROUND(SUM(duels_won) * 1.0 / NULLIF(SUM(duels_total), 0), 3)                  as duel_win_rate,
    ROUND(SUM(dribbles_success) * 1.0 / NULLIF(SUM(dribbles_attempted), 0), 3)    as dribble_success_rate,
    ROUND(SUM(shots_on_target) * 1.0 / NULLIF(SUM(shots_total), 0), 3)            as shot_accuracy

FROM {{ ref('gold_player_performance_mart') }}
GROUP BY player_id, player_name, team_name, position, league_id, season
ORDER BY season_goals DESC