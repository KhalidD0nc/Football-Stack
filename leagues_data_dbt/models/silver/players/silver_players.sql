{{config(materialized='table')}}
WITH squad AS (
    SELECT * FROM {{ ref('stg_squad_players') }}
),
stats AS (
    SELECT * FROM {{ ref('stg_player_season_stats') }}
)

SELECT
    sq.player_id,
    sq.team_id,
    sq.team_name,
    sq.team_logo,
    sq.league_id,
    sq.season,
    sq.player_name,
    sq.player_age,
    sq.shirt_number,
    sq.position,
    sq.player_photo,

    -- Extended profile from season stats
    s.player_first_name,
    s.player_last_name,
    s.player_birthday,
    s.player_nationality,
    s.player_height,
    s.player_weight,
    s.is_injured,

    -- Season performance
    s.appearances,
    s.lineups,
    s.minutes_played,
    s.rating,
    s.is_captain,
    s.sub_in,
    s.sub_out,
    s.sub_bench,
    s.shots_total,
    s.shots_on,
    s.goals_total,
    s.goals_conceded,
    s.assists_total,
    s.saves,
    s.passes_total,
    s.key_passes,
    s.passes_accuracy,
    s.tackles_total,
    s.tackles_blocks,
    s.interceptions,
    s.duels_total,
    s.duels_won,
    s.dribbles_attempts,
    s.dribbles_success,
    s.dribbles_past,
    s.fouls_drawn,
    s.fouls_committed,
    s.yellow_cards,
    s.yellow_red_cards,
    s.red_cards,
    s.penalties_won,
    s.penalties_committed,
    s.penalties_scored,
    s.penalties_missed,
    s.penalties_saved

FROM squad sq
LEFT JOIN stats s
    ON sq.player_id = s.player_id
    AND sq.team_id = s.team_id
    AND sq.league_id = s.league_id
    AND sq.season = s.season
