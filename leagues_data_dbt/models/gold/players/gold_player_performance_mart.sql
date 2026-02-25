{{ config(materialized='table') }}



WITH player_stats AS (
    SELECT
        s.player_id,
        s.player_name,
        s.fixture_id,
        s.team_id,
        s.team_name,
        s.position,
        s.is_substitute,
        s.rating,
        s.minutes_played,
        COALESCE(s.shots_total, 0)        as shots_total,
        COALESCE(s.shots_on_target, 0)    as shots_on_target,
        COALESCE(s.goals_total, 0)        as goals_total,
        COALESCE(s.assists, 0)            as assists,
        COALESCE(s.passes_total, 0)       as passes_total,
        s.passes_accuracy,
        COALESCE(s.key_passes, 0)         as key_passes,
        COALESCE(s.dribbles_attempted, 0) as dribbles_attempted,
        COALESCE(s.dribbles_success, 0)   as dribbles_success,
        COALESCE(s.duels_total, 0)        as duels_total,
        COALESCE(s.duels_won, 0)          as duels_won,
        COALESCE(s.tackles_total, 0)      as tackles_total,
        COALESCE(s.interceptions, 0)      as interceptions,
        COALESCE(s.blocks, 0)             as blocks,
        COALESCE(s.fouls_committed, 0)    as fouls_committed,
        COALESCE(s.fouls_drawn, 0)        as fouls_drawn,
        COALESCE(s.yellow_cards, 0)       as yellow_cards,
        COALESCE(s.red_cards, 0)          as red_cards,
        COALESCE(s.penalties_won, 0)      as penalties_won,
        COALESCE(s.penalties_scored, 0)   as penalties_scored,
        s.league_id,
        s.season
    FROM {{ ref('silver_match_player_stats') }} s
),

lineup_context AS (
    SELECT
        player_id,
        fixture_id,
        formation,
        grid
    FROM {{ ref('silver_lineup_players') }}
),

fixture_context AS (
    SELECT
        fixture_id,
        fixture_date,
        round_name,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        home_goals,
        away_goals
    FROM {{ ref('silver_fixture') }}
)

SELECT
    p.player_id,
    p.player_name,
    p.fixture_id,
    p.team_id,
    p.team_name,
    p.position,
    p.is_substitute,
    l.formation,
    l.grid,
    f.fixture_date,
    f.round_name,
    f.home_team_name,
    f.away_team_name,
    -- Derived context
    CASE WHEN p.team_id = f.home_team_id THEN 'Home' ELSE 'Away' END       as home_away,
    CASE 
        WHEN p.team_id = f.home_team_id THEN f.away_team_name 
        ELSE f.home_team_name 
    END                                                                      as opponent_name,
    CASE 
        WHEN p.team_id = f.home_team_id AND f.home_goals > f.away_goals THEN 'Win'
        WHEN p.team_id = f.away_team_id AND f.away_goals > f.home_goals THEN 'Win'
        WHEN f.home_goals = f.away_goals                                THEN 'Draw'
        ELSE 'Loss'
    END                                                                      as match_result,
    -- Stats
    p.rating,
    p.minutes_played,
    p.shots_total,
    p.shots_on_target,
    p.goals_total,
    p.assists,
    p.passes_total,
    p.passes_accuracy,
    p.key_passes,
    p.dribbles_attempted,
    p.dribbles_success,
    p.duels_total,
    p.duels_won,
    p.tackles_total,
    p.interceptions,
    p.blocks,
    p.fouls_committed,
    p.fouls_drawn,
    p.yellow_cards,
    p.red_cards,
    p.penalties_won,
    p.penalties_scored,
    p.league_id,
    p.season

FROM player_stats p
LEFT JOIN lineup_context l ON p.player_id = l.player_id AND p.fixture_id = l.fixture_id
LEFT JOIN fixture_context f ON p.fixture_id = f.fixture_id