{{ config(materialized='table') }}

WITH spl_teams AS (
    SELECT DISTINCT team_id
    FROM {{ ref('silver_teams') }}
),

latest_transfers AS (
    SELECT
        t.player_id,
        t.player_name,
        t.to_team_id                                                as team_id,
        t.to_team_name                                              as current_team,
        t.from_team_id,
        t.from_team_name                                            as previous_team,
        t.transfer_date,
        t.transfer_type,
        CASE
            WHEN t.to_team_id   IN (SELECT team_id FROM spl_teams) THEN 'Transfer In'
            WHEN t.from_team_id IN (SELECT team_id FROM spl_teams) THEN 'Transfer Out'
        END                                                         as transfer_direction,
        t.league_id,
        t.season
    FROM {{ ref('silver_transfers') }} t
    WHERE t.to_team_id   IN (SELECT team_id FROM spl_teams)
       OR t.from_team_id IN (SELECT team_id FROM spl_teams)
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY t.player_id
        ORDER BY t.transfer_date DESC
    ) = 1
)

SELECT
    lt.player_id,
    lt.player_name,
    lt.team_id,
    lt.current_team,
    lt.previous_team,
    lt.transfer_date,
    lt.transfer_type,
    lt.transfer_direction,
    -- Is player currently available at an SPL club?
    CASE 
        WHEN lt.transfer_direction = 'Transfer In' THEN TRUE
        ELSE FALSE
    END                                                             as is_active_spl_player,
    lt.league_id,
    lt.season

FROM latest_transfers lt
ORDER BY lt.transfer_date DESC