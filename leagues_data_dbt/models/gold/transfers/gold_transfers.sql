{{ config(materialized='table') }}

SELECT
    player_id,
    player_name,
    transfer_date,
    transfer_type,
    from_team_id,
    from_team_name,
    from_team_logo,
    to_team_id,
    to_team_name,
    to_team_logo,
    league_id,
    season
FROM {{ ref('silver_transfers') }}
ORDER BY transfer_date DESC