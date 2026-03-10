{{ config(materialized='table') }}

{% if var('use_curated_parquet', false) %}

select * from {{ source('curated', 'fixtures') }}

{% else %}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_fixtures') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
flattened as (
    select
        f.value:fixture:id::int as fixture_id,
        f.value:fixture:referee::varchar as referee,
        f.value:fixture:timezone::varchar as fixture_timezone,
        f.value:fixture:date::timestamp_tz as fixture_date,
        f.value:fixture:timestamp::int as fixture_timestamp,
        f.value:fixture:periods:first::int as period_first,
        f.value:fixture:periods:second::int as period_second,
        f.value:fixture:venue:id::int as venue_id,
        f.value:fixture:venue:name::varchar as venue_name,
        f.value:fixture:venue:city::varchar as venue_city,
        f.value:fixture:status:long::varchar as status_long,
        f.value:fixture:status:short::varchar as status_short,
        f.value:fixture:status:elapsed::int as status_elapsed,
        f.value:league:id::int as fixture_league_id,
        f.value:league:name::varchar as fixture_league_name,
        f.value:league:country::varchar as fixture_league_country,
        f.value:league:logo::varchar as fixture_league_logo,
        f.value:league:flag::varchar as fixture_league_flag,
        f.value:league:season::int as fixture_league_season,
        f.value:league:round::varchar as round_name,
        f.value:teams:home:id::int as home_team_id,
        f.value:teams:home:name::varchar as home_team_name,
        f.value:teams:home:logo::varchar as home_team_logo,
        f.value:teams:home:winner::boolean as home_team_winner,
        f.value:teams:away:id::int as away_team_id,
        f.value:teams:away:name::varchar as away_team_name,
        f.value:teams:away:logo::varchar as away_team_logo,
        f.value:teams:away:winner::boolean as away_team_winner,
        f.value:goals:home::int as home_goals,
        f.value:goals:away::int as away_goals,
        f.value:score:halftime:home::int as halftime_home_goals,
        f.value:score:halftime:away::int as halftime_away_goals,
        f.value:score:fulltime:home::int as fulltime_home_goals,
        f.value:score:fulltime:away::int as fulltime_away_goals,
        f.value:score:extratime:home::int as extratime_home_goals,
        f.value:score:extratime:away::int as extratime_away_goals,
        f.value:score:penalty:home::int as penalty_home_goals,
        f.value:score:penalty:away::int as penalty_away_goals,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) f
)

select
    fixture_id,
    referee,
    fixture_timezone,
    fixture_date,
    fixture_timestamp,
    period_first,
    period_second,
    venue_id,
    venue_name,
    venue_city,
    status_long,
    status_short,
    status_elapsed,
    fixture_league_id,
    fixture_league_name,
    fixture_league_country,
    fixture_league_logo,
    fixture_league_flag,
    fixture_league_season,
    round_name,
    home_team_id,
    home_team_name,
    home_team_logo,
    home_team_winner,
    away_team_id,
    away_team_name,
    away_team_logo,
    away_team_winner,
    home_goals,
    away_goals,
    halftime_home_goals,
    halftime_away_goals,
    fulltime_home_goals,
    fulltime_away_goals,
    extratime_home_goals,
    extratime_away_goals,
    penalty_home_goals,
    penalty_away_goals,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from flattened

{% endif %}
