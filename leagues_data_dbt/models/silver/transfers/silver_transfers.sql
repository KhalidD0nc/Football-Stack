{{config(materialized='table')}}

WITH source AS (SELECT * FROM {{ ref('stg_transfers') }})
SELECT
    player_id, player_name, transfer_date, transfer_type,
    to_team_id, to_team_name, to_team_logo,
    from_team_id, from_team_name, from_team_logo,
    league_id, season
FROM source