{{ config(materialized='table') }}

WITH primary_position AS (
    -- Pick dominant outfield position per player by total minutes
    -- Excludes goalkeepers (position = 'G') as archetype scores are not meaningful for GKs;
    -- consistent with platinum_player_duel_dominance and platinum_player_per90_efficiency
    SELECT player_id, league_id, season, position
    FROM (
        SELECT
            player_id, league_id, season, position,
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
    -- Aggregate-first pattern: sum all fragments per player, then apply threshold
    SELECT
        s.player_id,
        MIN(s.player_name)                  AS player_name,
        p.position,
        s.league_id,
        s.season,
        SUM(s.matches_played)               AS matches_played,
        SUM(s.total_minutes)                AS total_minutes,
        SUM(s.season_goals)                 AS season_goals,
        SUM(s.season_assists)               AS season_assists,
        SUM(s.season_key_passes)            AS season_key_passes,
        SUM(s.season_dribbles_attempted)    AS season_dribbles_attempted,
        SUM(s.season_dribbles_success)      AS season_dribbles_success,
        SUM(s.season_tackles)               AS season_tackles,
        SUM(s.season_interceptions)         AS season_interceptions,
        SUM(s.season_blocks)                AS season_blocks,
        SUM(s.season_duels)                 AS season_duels,
        SUM(s.season_duels_won)             AS season_duels_won,
        SUM(s.season_shots)                 AS season_shots,
        SUM(s.season_shots_on_target)       AS season_shots_on_target,
        AVG(s.avg_rating)                   AS avg_rating,
        -- Recompute per-90 from summed totals (more accurate than averaging rates)
        ROUND(SUM(s.season_goals)   / NULLIF(SUM(s.total_minutes), 0) * 90, 4) AS goals_per_90,
        ROUND(SUM(s.season_assists) / NULLIF(SUM(s.total_minutes), 0) * 90, 4) AS assists_per_90,
        ROUND(SUM(s.season_duels_won) * 1.0 / NULLIF(SUM(s.season_duels), 0), 3) AS duel_win_rate,
        ROUND(SUM(s.season_dribbles_success) * 1.0 / NULLIF(SUM(s.season_dribbles_attempted), 0), 3) AS dribble_success_rate,
        ROUND(SUM(s.season_shots_on_target) * 1.0 / NULLIF(SUM(s.season_shots), 0), 3) AS shot_accuracy
    FROM {{ ref('gold_player_season_summary') }} s
    JOIN primary_position p
        ON  s.player_id = p.player_id
        AND s.league_id = p.league_id
        AND s.season    = p.season
    GROUP BY s.player_id, p.position, s.league_id, s.season
    HAVING SUM(s.matches_played) >= 5
       AND SUM(s.total_minutes)  >= 300
),

raw_scores AS (
    -- Compute raw archetype scores
    SELECT
        *,
        ROUND(goals_per_90 * 40 + COALESCE(shot_accuracy, 0) * 0.3 + season_goals * 0.3, 2)                                              AS poacher_raw,
        ROUND(assists_per_90 * 40 + season_key_passes * 0.5 + season_assists * 0.3, 2)                                                   AS playmaker_raw,
        ROUND(season_tackles * 0.4 + season_interceptions * 0.4 + COALESCE(duel_win_rate, 0) * 0.2, 2)                                   AS destroyer_raw,
        ROUND(COALESCE(dribble_success_rate, 0) * 0.5 + season_dribbles_success * 0.5, 2)                                                AS dribbler_raw,
        ROUND(goals_per_90 * 15 + assists_per_90 * 15 + season_tackles * 0.2 + season_dribbles_success * 0.2 + avg_rating * 2, 2)       AS engine_raw,
        ROUND(season_blocks * 0.5 + season_interceptions * 0.3 + season_tackles * 0.2, 2)                                                AS guardian_raw
    FROM base
),

normalized AS (
    -- Normalize each score to 0-100 using population p75 as the anchor.
    -- This ensures all 6 archetypes compete on equal footing:
    -- a specialist who excels at one dimension beats a generalist
    -- who is mediocre across all dimensions.
    -- p75 anchors are derived from the 2023/2024 season global population baseline.
    -- These are hardcoded intentionally to provide a stable, comparable score
    -- across different seasons and leagues without shifting the distribution bounds:
    --   poacher=7.84  | playmaker=13.11 | destroyer=17.70
    --   dribbler=5.95 | engine=25.70    | guardian=13.40
    SELECT
        *,
        ROUND(LEAST(GREATEST(poacher_raw   / 7.84  * 100, 0), 100), 1) AS poacher_score,
        ROUND(LEAST(GREATEST(playmaker_raw / 13.11 * 100, 0), 100), 1) AS playmaker_score,
        ROUND(LEAST(GREATEST(destroyer_raw / 17.70 * 100, 0), 100), 1) AS destroyer_score,
        ROUND(LEAST(GREATEST(dribbler_raw  / 5.95  * 100, 0), 100), 1) AS dribbler_score,
        ROUND(LEAST(GREATEST(engine_raw    / 25.70 * 100, 0), 100), 1) AS engine_score,
        ROUND(LEAST(GREATEST(guardian_raw  / 13.40 * 100, 0), 100), 1) AS guardian_score
    FROM raw_scores
),

classified AS (
    SELECT
        *,
        GREATEST(poacher_score, playmaker_score, destroyer_score, dribbler_score, engine_score, guardian_score) AS top_score,
        CASE GREATEST(poacher_score, playmaker_score, destroyer_score, dribbler_score, engine_score, guardian_score)
            WHEN poacher_score   THEN 'Poacher'
            WHEN playmaker_score THEN 'Playmaker'
            WHEN destroyer_score THEN 'Destroyer'
            WHEN dribbler_score  THEN 'Dribbler'
            WHEN engine_score    THEN 'Engine'
            WHEN guardian_score  THEN 'Guardian'
        END AS player_archetype
    FROM normalized
)

SELECT
    player_id || '-' || league_id || '-' || season AS fingerprint_id,
    player_id,
    player_name,
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
