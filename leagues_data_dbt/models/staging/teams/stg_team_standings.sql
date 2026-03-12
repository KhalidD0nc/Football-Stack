{{ config(materialized='table') }}

{% if var('use_curated_parquet', false) %}

{{ curated_source_latest('team_standings', ['team_id', 'league_id', 'season']) }}

{% else %}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_standings') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
flattened as (
    select
        s.value:rank::int as standing_rank,
        s.value:team:id::int as team_id,
        s.value:team:name::varchar as team_name,
        s.value:team:logo::varchar as team_logo,
        s.value:group::varchar as standing_group,
        s.value:form::varchar as recent_form,
        s.value:status::varchar as standing_status,
        s.value:description::varchar as standing_description,
        s.value:all:played::int as all_played,
        s.value:all:win::int as all_win,
        s.value:all:draw::int as all_draw,
        s.value:all:lose::int as all_lose,
        s.value:all:goals:for::int as all_goals_for,
        s.value:all:goals:against::int as all_goals_against,
        s.value:home:played::int as home_played,
        s.value:home:win::int as home_win,
        s.value:home:draw::int as home_draw,
        s.value:home:lose::int as home_lose,
        s.value:home:goals:for::int as home_goals_for,
        s.value:home:goals:against::int as home_goals_against,
        s.value:away:played::int as away_played,
        s.value:away:win::int as away_win,
        s.value:away:draw::int as away_draw,
        s.value:away:lose::int as away_lose,
        s.value:away:goals:for::int as away_goals_for,
        s.value:away:goals:against::int as away_goals_against,
        s.value:goalsDiff::int as goals_diff,
        s.value:points::int as points,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response[0]:league:standings[0]) s
)

select
    standing_rank,
    team_id,
    team_name,
    team_logo,
    standing_group,
    recent_form,
    standing_status,
    standing_description,
    all_played,
    all_win,
    all_draw,
    all_lose,
    all_goals_for,
    all_goals_against,
    home_played,
    home_win,
    home_draw,
    home_lose,
    home_goals_for,
    home_goals_against,
    away_played,
    away_win,
    away_draw,
    away_lose,
    away_goals_for,
    away_goals_against,
    goals_diff,
    points,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from flattened

{% endif %}
