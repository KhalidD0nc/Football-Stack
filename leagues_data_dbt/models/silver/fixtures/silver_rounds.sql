{{config(materialized='table')}}

WITH source AS (SELECT * FROM {{ ref('stg_rounds') }})
SELECT round_name, round_number, league_id, season
FROM source
