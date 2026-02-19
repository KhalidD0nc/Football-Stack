{{ config(materialized='table') }}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_injuries') }}
    qualify row_number() over (
        partition by raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
flattened as (
    select
        i.value:player:id::int as player_id,
        i.value:player:name::varchar as player_name,
        i.value:player:photo::varchar as player_photo,
        i.value:team:id::int as team_id,
        i.value:team:name::varchar as team_name,
        i.value:team:logo::varchar as team_logo,
        i.value:fixture:id::int as fixture_id,
        i.value:fixture:timezone::varchar as fixture_timezone,
        i.value:fixture:date::timestamp_tz as fixture_date,
        i.value:fixture:timestamp::int as fixture_timestamp,
        i.value:league:id::int as injury_league_id,
        i.value:league:name::varchar as injury_league_name,
        i.value:league:country::varchar as injury_league_country,
        i.value:league:logo::varchar as injury_league_logo,
        i.value:league:flag::varchar as injury_league_flag,
        i.value:league:season::int as injury_league_season,
        i.value:type::varchar as injury_type,
        i.value:reason::varchar as injury_reason,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) i
)

select
    player_id,
    player_name,
    player_photo,
    team_id,
    team_name,
    team_logo,
    fixture_id,
    fixture_timezone,
    fixture_date,
    fixture_timestamp,
    injury_league_id,
    injury_league_name,
    injury_league_country,
    injury_league_logo,
    injury_league_flag,
    injury_league_season,
    injury_type,
    injury_reason,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from flattened
