{{ config(materialized='table') }}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_teams') }}
    qualify row_number() over (
        partition by raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
flattened as (
    select
        team.value:team:id::int as team_id,
        team.value:team:name::varchar as team_name,
        team.value:team:code::varchar as team_code,
        team.value:team:country::varchar as country,
        team.value:team:founded::int as founded,
        team.value:team:national::boolean as is_national_team,
        team.value:team:logo::varchar as team_logo_url,
        team.value:venue:id::int as venue_id,
        team.value:venue:name::varchar as venue_name,
        team.value:venue:address::varchar as venue_address,
        team.value:venue:city::varchar as venue_city,
        team.value:venue:capacity::int as venue_capacity,
        team.value:venue:surface::varchar as venue_surface,
        team.value:venue:image::varchar as venue_image_url,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) team
),
final as (
    select
        team_id,
        team_name,
        team_code,
        country,
        founded,
        is_national_team,
        team_logo_url,
        venue_id,
        venue_name,
        venue_address,
        venue_city,
        venue_capacity,
        venue_surface,
        venue_image_url,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from flattened
)

select * from final
