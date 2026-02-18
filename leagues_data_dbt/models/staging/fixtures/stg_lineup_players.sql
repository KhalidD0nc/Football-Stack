{{ config(materialized='table') }}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_fixtures_lineups') }}
    qualify row_number() over (
        partition by raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
lineups_flat as (
    select
        source_dedup.raw:params:fixture::int as fixture_id,
        lineup.value:team:id::int as team_id,
        lineup.value:team:name::varchar as team_name,
        lineup.value:team:colors:player:primary::varchar as team_colors_player_primary,
        lineup.value:team:colors:player:number::varchar as team_colors_player_number,
        lineup.value:team:colors:player:border::varchar as team_colors_player_border,
        lineup.value:formation::varchar as formation,
        lineup.value:coach:id::int as coach_id,
        lineup.value:coach:name::varchar as coach_name,
        lineup.value:coach:photo::varchar as coach_photo,
        lineup.value:startXI as start_xi,
        lineup.value:substitutes as substitutes,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) lineup
),
start_xi_players as (
    select
        fixture_id,
        team_id,
        team_name,
        team_colors_player_primary,
        team_colors_player_number,
        team_colors_player_border,
        formation,
        coach_id,
        coach_name,
        coach_photo,
        'start_xi'::varchar as lineup_bucket,
        player.value:player:id::int as player_id,
        player.value:player:name::varchar as player_name,
        player.value:player:number::int as player_number,
        player.value:player:pos::varchar as player_pos,
        player.value:player:grid::varchar as grid,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from lineups_flat,
        lateral flatten(input => lineups_flat.start_xi) player
),
sub_players as (
    select
        fixture_id,
        team_id,
        team_name,
        team_colors_player_primary,
        team_colors_player_number,
        team_colors_player_border,
        formation,
        coach_id,
        coach_name,
        coach_photo,
        'substitutes'::varchar as lineup_bucket,
        player.value:player:id::int as player_id,
        player.value:player:name::varchar as player_name,
        player.value:player:number::int as player_number,
        player.value:player:pos::varchar as player_pos,
        player.value:player:grid::varchar as grid,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from lineups_flat,
        lateral flatten(input => lineups_flat.substitutes) player
),
final as (
    select
        fixture_id,
        team_id,
        team_name,
        team_colors_player_primary,
        team_colors_player_number,
        team_colors_player_border,
        formation,
        coach_id,
        coach_name,
        coach_photo,
        lineup_bucket,
        player_id,
        player_name,
        player_number,
        player_pos,
        grid,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from start_xi_players

    union all

    select
        fixture_id,
        team_id,
        team_name,
        team_colors_player_primary,
        team_colors_player_number,
        team_colors_player_border,
        formation,
        coach_id,
        coach_name,
        coach_photo,
        lineup_bucket,
        player_id,
        player_name,
        player_number,
        player_pos,
        grid,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from sub_players
)

select
    fixture_id,
    team_id,
    team_name,
    team_colors_player_primary,
    team_colors_player_number,
    team_colors_player_border,
    formation,
    coach_id,
    coach_name,
    coach_photo,
    lineup_bucket,
    player_id,
    player_name,
    player_number,
    player_pos,
    grid,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from final
