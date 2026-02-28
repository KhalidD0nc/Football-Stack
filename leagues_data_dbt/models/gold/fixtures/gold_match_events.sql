{{ config(materialized='table') }}

SELECT
    fixture_id,
    event_sequence,
    event_minute,
    event_extra_minute,
    team_id,
    team_name,
    player_id,
    player_name,
    assist_player_id,
    assist_player_name,
    event_type,
    event_detail,
    event_comments,
    league_id,
    season
FROM {{ ref('stg_match_events') }}
ORDER BY fixture_id, event_sequence
