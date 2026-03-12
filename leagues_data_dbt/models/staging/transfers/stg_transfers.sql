{{ config(materialized='table') }}

{% if var('use_curated_parquet', false) %}

{{ curated_source_latest(
    'transfers',
    ['league_id', 'season', 'player_id', 'transfer_date', 'coalesce(from_team_id, -1)', 'coalesce(to_team_id, -1)', "coalesce(transfer_type, 'na')"]
) }}

{% else %}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_transfers') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
player_rows as (
    select
        p.value:player:id::int as player_id,
        p.value:player:name::varchar as player_name,
        p.value:transfers as transfers,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) p
),
flattened as (
    select
        player_id,
        player_name,
        t.value:date::date as transfer_date,
        t.value:type::varchar as transfer_type,
        t.value:teams:in:id::int as to_team_id,
        t.value:teams:in:name::varchar as to_team_name,
        t.value:teams:in:logo::varchar as to_team_logo,
        t.value:teams:out:id::int as from_team_id,
        t.value:teams:out:name::varchar as from_team_name,
        t.value:teams:out:logo::varchar as from_team_logo,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from player_rows,
        lateral flatten(input => player_rows.transfers) t
),
deduped as (
    select
        player_id,
        player_name,
        transfer_date,
        transfer_type,
        to_team_id,
        to_team_name,
        to_team_logo,
        from_team_id,
        from_team_name,
        from_team_logo,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from flattened
    qualify row_number() over (
        partition by
            league_id,
            season,
            player_id,
            transfer_date,
            coalesce(from_team_id, -1),
            coalesce(to_team_id, -1),
            coalesce(transfer_type, 'na')
        order by _loaded_at desc
    ) = 1
)

select
    player_id,
    player_name,
    transfer_date,
    transfer_type,
    to_team_id,
    to_team_name,
    to_team_logo,
    from_team_id,
    from_team_name,
    from_team_logo,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from deduped

{% endif %}
