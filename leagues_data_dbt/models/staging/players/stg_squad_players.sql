{{ config(materialized='table') }}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_players_squads') }}
    qualify row_number() over (
        partition by raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
squad_rows as (
    select
        squad.value:team:id::int as team_id,
        squad.value:team:name::varchar as team_name,
        squad.value:team:logo::varchar as team_logo,
        squad.value:players as players,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) squad
),
flattened as (
    select
        team_id,
        team_name,
        team_logo,
        p.value:id::int as player_id,
        p.value:name::varchar as player_name,
        p.value:age::int as player_age,
        p.value:number::int as shirt_number,
        p.value:position::varchar as position,
        p.value:photo::varchar as player_photo,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from squad_rows,
        lateral flatten(input => squad_rows.players) p
)

select
    team_id,
    team_name,
    team_logo,
    player_id,
    player_name,
    player_age,
    shirt_number,
    position,
    player_photo,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from flattened
