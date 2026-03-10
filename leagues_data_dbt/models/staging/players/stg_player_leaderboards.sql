{{ config(materialized='table') }}

{% if var('use_curated_parquet', false) %}

select * from {{ source('curated', 'player_leaderboards') }}

{% else %}

with top_scorers_source as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_players_topscorers') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
top_scorers as (
    select
        'top_scorers'::varchar as ranking_type,
        player.value:player:id::int as player_id,
        player.value:player:name::varchar as player_name,
        player.value:player:firstname::varchar as player_first_name,
        player.value:player:lastname::varchar as player_last_name,
        player.value:player:age::int as player_age,
        player.value:player:nationality::varchar as player_nationality,
        player.value:player:photo::varchar as player_photo_url,
        player.value:statistics[0]:team:id::int as team_id,
        player.value:statistics[0]:team:name::varchar as team_name,
        player.value:statistics[0]:league:id::int as stats_league_id,
        player.value:statistics[0]:league:season::int as stats_season,
        player.value:statistics[0]:games:appearences::int as appearances,
        player.value:statistics[0]:games:minutes::int as minutes_played,
        player.value:statistics[0]:games:position::varchar as position,
        player.value:statistics[0]:games:rating::float as rating,
        player.value:statistics[0]:goals:total::int as goals_total,
        player.value:statistics[0]:goals:assists::int as assists_total,
        player.value:statistics[0]:cards:yellow::int as yellow_cards,
        player.value:statistics[0]:cards:red::int as red_cards,
        player.index + 1 as rank,
        top_scorers_source.league_id,
        top_scorers_source.season,
        top_scorers_source.dt,
        top_scorers_source.run_id,
        top_scorers_source._loaded_at
    from top_scorers_source,
        lateral flatten(input => top_scorers_source.raw:payload:response) player
),
top_assists_source as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_players_topassists') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
top_assists as (
    select
        'top_assists'::varchar as ranking_type,
        player.value:player:id::int as player_id,
        player.value:player:name::varchar as player_name,
        player.value:player:firstname::varchar as player_first_name,
        player.value:player:lastname::varchar as player_last_name,
        player.value:player:age::int as player_age,
        player.value:player:nationality::varchar as player_nationality,
        player.value:player:photo::varchar as player_photo_url,
        player.value:statistics[0]:team:id::int as team_id,
        player.value:statistics[0]:team:name::varchar as team_name,
        player.value:statistics[0]:league:id::int as stats_league_id,
        player.value:statistics[0]:league:season::int as stats_season,
        player.value:statistics[0]:games:appearences::int as appearances,
        player.value:statistics[0]:games:minutes::int as minutes_played,
        player.value:statistics[0]:games:position::varchar as position,
        player.value:statistics[0]:games:rating::float as rating,
        player.value:statistics[0]:goals:total::int as goals_total,
        player.value:statistics[0]:goals:assists::int as assists_total,
        player.value:statistics[0]:cards:yellow::int as yellow_cards,
        player.value:statistics[0]:cards:red::int as red_cards,
        player.index + 1 as rank,
        top_assists_source.league_id,
        top_assists_source.season,
        top_assists_source.dt,
        top_assists_source.run_id,
        top_assists_source._loaded_at
    from top_assists_source,
        lateral flatten(input => top_assists_source.raw:payload:response) player
),
top_yellow_cards_source as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_players_topyellowcards') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
top_yellow_cards as (
    select
        'top_yellow_cards'::varchar as ranking_type,
        player.value:player:id::int as player_id,
        player.value:player:name::varchar as player_name,
        player.value:player:firstname::varchar as player_first_name,
        player.value:player:lastname::varchar as player_last_name,
        player.value:player:age::int as player_age,
        player.value:player:nationality::varchar as player_nationality,
        player.value:player:photo::varchar as player_photo_url,
        player.value:statistics[0]:team:id::int as team_id,
        player.value:statistics[0]:team:name::varchar as team_name,
        player.value:statistics[0]:league:id::int as stats_league_id,
        player.value:statistics[0]:league:season::int as stats_season,
        player.value:statistics[0]:games:appearences::int as appearances,
        player.value:statistics[0]:games:minutes::int as minutes_played,
        player.value:statistics[0]:games:position::varchar as position,
        player.value:statistics[0]:games:rating::float as rating,
        player.value:statistics[0]:goals:total::int as goals_total,
        player.value:statistics[0]:goals:assists::int as assists_total,
        player.value:statistics[0]:cards:yellow::int as yellow_cards,
        player.value:statistics[0]:cards:red::int as red_cards,
        player.index + 1 as rank,
        top_yellow_cards_source.league_id,
        top_yellow_cards_source.season,
        top_yellow_cards_source.dt,
        top_yellow_cards_source.run_id,
        top_yellow_cards_source._loaded_at
    from top_yellow_cards_source,
        lateral flatten(input => top_yellow_cards_source.raw:payload:response) player
),
top_red_cards_source as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_players_topredcards') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
top_red_cards as (
    select
        'top_red_cards'::varchar as ranking_type,
        player.value:player:id::int as player_id,
        player.value:player:name::varchar as player_name,
        player.value:player:firstname::varchar as player_first_name,
        player.value:player:lastname::varchar as player_last_name,
        player.value:player:age::int as player_age,
        player.value:player:nationality::varchar as player_nationality,
        player.value:player:photo::varchar as player_photo_url,
        player.value:statistics[0]:team:id::int as team_id,
        player.value:statistics[0]:team:name::varchar as team_name,
        player.value:statistics[0]:league:id::int as stats_league_id,
        player.value:statistics[0]:league:season::int as stats_season,
        player.value:statistics[0]:games:appearences::int as appearances,
        player.value:statistics[0]:games:minutes::int as minutes_played,
        player.value:statistics[0]:games:position::varchar as position,
        player.value:statistics[0]:games:rating::float as rating,
        player.value:statistics[0]:goals:total::int as goals_total,
        player.value:statistics[0]:goals:assists::int as assists_total,
        player.value:statistics[0]:cards:yellow::int as yellow_cards,
        player.value:statistics[0]:cards:red::int as red_cards,
        player.index + 1 as rank,
        top_red_cards_source.league_id,
        top_red_cards_source.season,
        top_red_cards_source.dt,
        top_red_cards_source.run_id,
        top_red_cards_source._loaded_at
    from top_red_cards_source,
        lateral flatten(input => top_red_cards_source.raw:payload:response) player
),
final as (
    select * from top_scorers
    union all
    select * from top_assists
    union all
    select * from top_yellow_cards
    union all
    select * from top_red_cards
)

select
    ranking_type,
    player_id,
    player_name,
    player_first_name,
    player_last_name,
    player_age,
    player_nationality,
    player_photo_url,
    team_id,
    team_name,
    stats_league_id,
    stats_season,
    appearances,
    minutes_played,
    position,
    rating,
    goals_total,
    assists_total,
    yellow_cards,
    red_cards,
    rank,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from final

{% endif %}
