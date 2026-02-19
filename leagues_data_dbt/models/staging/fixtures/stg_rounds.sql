{{ config(materialized='table') }}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_fixtures_rounds') }}
    qualify row_number() over (
        partition by raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
flattened as (
    select
        round_name.value::varchar as round_name,
        regexp_substr(round_name.value::varchar, '[0-9]+')::int as round_number,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) round_name
)

select
    round_name,
    round_number,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from flattened
