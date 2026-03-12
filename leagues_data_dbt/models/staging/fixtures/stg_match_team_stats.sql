{{ config(materialized='table') }}

{% if var('use_curated_parquet', false) %}

{{ curated_source_latest('match_team_stats', ['fixture_id', 'team_id']) }}

{% else %}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_fixtures_statistics') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
stats_long as (
    select
        source_dedup.raw:params:fixture::int as fixture_id,
        team_stats.value:team:id::int as team_id,
        team_stats.value:team:name::varchar as team_name,
        stat.value:type::varchar as stat_type,
        stat.value:value::varchar as stat_value,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) team_stats,
        lateral flatten(input => team_stats.value:statistics) stat
),
pivoted as (
    select
        fixture_id,
        team_id,
        team_name,
        max(case when stat_type = 'Ball Possession' then try_to_double(replace(stat_value, '%', '')) end) as ball_possession_pct,
        max(case when stat_type = 'Passes %' then try_to_double(replace(stat_value, '%', '')) end) as passes_pct,
        max(case when stat_type = 'expected_goals' then try_to_double(stat_value) end) as expected_goals,
        max(case when stat_type = 'goals_prevented' then try_to_double(stat_value) end) as goals_prevented,
        max(case when stat_type = 'Total Shots' then try_to_number(stat_value)::int end) as total_shots,
        max(case when stat_type = 'Shots on Goal' then try_to_number(stat_value)::int end) as shots_on_goal,
        max(case when stat_type = 'Shots off Goal' then try_to_number(stat_value)::int end) as shots_off_goal,
        max(case when stat_type = 'Blocked Shots' then try_to_number(stat_value)::int end) as blocked_shots,
        max(case when stat_type = 'Shots insidebox' then try_to_number(stat_value)::int end) as shots_inside_box,
        max(case when stat_type = 'Shots outsidebox' then try_to_number(stat_value)::int end) as shots_outside_box,
        max(case when stat_type = 'Corner Kicks' then try_to_number(stat_value)::int end) as corner_kicks,
        max(case when stat_type = 'Offsides' then try_to_number(stat_value)::int end) as offsides,
        max(case when stat_type = 'Fouls' then try_to_number(stat_value)::int end) as fouls,
        max(case when stat_type = 'Yellow Cards' then try_to_number(stat_value)::int end) as yellow_cards,
        max(case when stat_type = 'Red Cards' then try_to_number(stat_value)::int end) as red_cards,
        max(case when stat_type = 'Goalkeeper Saves' then try_to_number(stat_value)::int end) as goalkeeper_saves,
        max(case when stat_type = 'Passes accurate' then try_to_number(stat_value)::int end) as passes_accurate,
        max(case when stat_type = 'Total passes' then try_to_number(stat_value)::int end) as total_passes,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from stats_long
    group by
        fixture_id,
        team_id,
        team_name,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
),
final as (
    select
        fixture_id,
        team_id,
        team_name,
        ball_possession_pct,
        passes_pct,
        expected_goals,
        goals_prevented,
        total_shots,
        shots_on_goal,
        shots_off_goal,
        blocked_shots,
        shots_inside_box,
        shots_outside_box,
        corner_kicks,
        offsides,
        fouls,
        yellow_cards,
        red_cards,
        goalkeeper_saves,
        passes_accurate,
        total_passes,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from pivoted
)

select
    fixture_id,
    team_id,
    team_name,
    ball_possession_pct,
    passes_pct,
    expected_goals,
    goals_prevented,
    total_shots,
    shots_on_goal,
    shots_off_goal,
    blocked_shots,
    shots_inside_box,
    shots_outside_box,
    corner_kicks,
    offsides,
    fouls,
    yellow_cards,
    red_cards,
    goalkeeper_saves,
    passes_accurate,
    total_passes,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from final

{% endif %}
