{{ config(materialized='table') }}

{% if var('use_curated_parquet', false) %}

select * from {{ source('curated', 'match_events') }}

{% else %}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_fixtures_events') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
flattened as (
    select
        source_dedup.raw:params:fixture::int as fixture_id,
        e.index::int as event_sequence,
        e.value:time:elapsed::int as event_minute,
        e.value:time:extra::int as event_extra_minute,
        e.value:team:id::int as team_id,
        e.value:team:name::varchar as team_name,
        e.value:player:id::int as player_id,
        e.value:player:name::varchar as player_name,
        e.value:assist:id::int as assist_player_id,
        e.value:assist:name::varchar as assist_player_name,
        e.value:type::varchar as event_type,
        e.value:detail::varchar as event_detail,
        e.value:comments::varchar as event_comments,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) e
)

select
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
    season,
    dt,
    run_id,
    _loaded_at
from flattened

{% endif %}
