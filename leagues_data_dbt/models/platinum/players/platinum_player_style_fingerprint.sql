{{ config(materialized='table') }}

WITH base AS (
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
        season_dribbles_attempted,
        season_dribbles_success,
        season_tackles,
        season_interceptions,
        season_blocks,
        season_duels,
        season_duels_won,
        season_shots,
        season_shots_on_target,
        avg_rating,
        goals_per_90,
        assists_per_90,
        duel_win_rate,
        dribble_success_rate,
        shot_accuracy
    FROM {{ ref('gold_player_season_summary') }}
    WHERE matches_played >= 5
      AND total_minutes >= 300
),

fingerprint AS (
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
        season_dribbles_success,
        avg_rating,
        goals_per_90,
        assists_per_90,
        duel_win_rate,
        dribble_success_rate,
        shot_accuracy,
        ROUND(goals_per_90 * 40 + shot_accuracy * 0.3 + season_goals * 0.3, 2)                                                           as poacher_score,
        ROUND(assists_per_90 * 40 + season_key_passes * 0.5 + season_assists * 0.3, 2)                                                   as playmaker_score,
        ROUND(season_tackles * 0.4 + season_interceptions * 0.4 + duel_win_rate * 0.2, 2)                                                as destroyer_score,
        ROUND(dribble_success_rate * 0.5 + season_dribbles_success * 0.5, 2)                                                             as dribbler_score,
        ROUND(goals_per_90 * 15 + assists_per_90 * 15 + season_tackles * 0.2 + season_dribbles_success * 0.2 + avg_rating * 2, 2)       as engine_score,
        ROUND(season_blocks * 0.5 + season_interceptions * 0.3 + season_tackles * 0.2, 2)                                                as guardian_score
    FROM base
),

classified AS (
    SELECT
        *,
        GREATEST(poacher_score, playmaker_score, destroyer_score, dribbler_score, engine_score, guardian_score) as top_score,
        CASE GREATEST(poacher_score, playmaker_score, destroyer_score, dribbler_score, engine_score, guardian_score)
            WHEN poacher_score   THEN 'Poacher'
            WHEN playmaker_score THEN 'Playmaker'
            WHEN destroyer_score THEN 'Destroyer'
            WHEN dribbler_score  THEN 'Dribbler'
            WHEN engine_score    THEN 'Engine'
            WHEN guardian_score  THEN 'Guardian'
        END as player_archetype
    FROM fingerprint
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
    season_dribbles_success,
    avg_rating,
    goals_per_90,
    assists_per_90,
    duel_win_rate,
    dribble_success_rate,
    shot_accuracy,
    poacher_score,
    playmaker_score,
    destroyer_score,
    dribbler_score,
    engine_score,
    guardian_score,
    top_score,
    player_archetype
FROM classified