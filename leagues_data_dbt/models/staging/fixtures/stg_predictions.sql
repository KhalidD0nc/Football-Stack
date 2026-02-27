{{ config(materialized='table') }}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_predictions') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
flattened as (
    select
        source_dedup.raw:params:fixture::int as fixture_id,
        p.value:predictions:winner:id::int as predicted_winner_team_id,
        p.value:predictions:winner:name::varchar as predicted_winner_team_name,
        p.value:predictions:winner:comment::varchar as predicted_winner_comment,
        p.value:predictions:advice::varchar as betting_advice,
        p.value:predictions:percent:home::varchar as home_win_percent,
        p.value:predictions:percent:draw::varchar as draw_percent,
        p.value:predictions:percent:away::varchar as away_win_percent,
        try_to_double(replace(p.value:predictions:percent:home::varchar, '%', '')) as home_win_percent_value,
        try_to_double(replace(p.value:predictions:percent:draw::varchar, '%', '')) as draw_percent_value,
        try_to_double(replace(p.value:predictions:percent:away::varchar, '%', '')) as away_win_percent_value,
        p.value:teams:home:id::int as home_team_id,
        p.value:teams:home:name::varchar as home_team_name,
        p.value:teams:away:id::int as away_team_id,
        p.value:teams:away:name::varchar as away_team_name,
        p.value:comparison:form:home::varchar as comparison_form_home,
        p.value:comparison:form:away::varchar as comparison_form_away,
        p.value:comparison:att:home::varchar as comparison_attack_home,
        p.value:comparison:att:away::varchar as comparison_attack_away,
        p.value:comparison:def:home::varchar as comparison_defense_home,
        p.value:comparison:def:away::varchar as comparison_defense_away,
        p.value:comparison:poisson_distribution:home::varchar as comparison_poisson_home,
        p.value:comparison:poisson_distribution:away::varchar as comparison_poisson_away,
        p.value:comparison:h2h:home::varchar as comparison_h2h_home,
        p.value:comparison:h2h:away::varchar as comparison_h2h_away,
        p.value:comparison:goals:home::varchar as comparison_goals_home,
        p.value:comparison:goals:away::varchar as comparison_goals_away,
        p.value:comparison:total:home::varchar as comparison_total_home,
        p.value:comparison:total:away::varchar as comparison_total_away,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup,
        lateral flatten(input => source_dedup.raw:payload:response) p
)

select
    fixture_id,
    predicted_winner_team_id,
    predicted_winner_team_name,
    predicted_winner_comment,
    betting_advice,
    home_win_percent,
    draw_percent,
    away_win_percent,
    home_win_percent_value,
    draw_percent_value,
    away_win_percent_value,
    home_team_id,
    home_team_name,
    away_team_id,
    away_team_name,
    comparison_form_home,
    comparison_form_away,
    comparison_attack_home,
    comparison_attack_away,
    comparison_defense_home,
    comparison_defense_away,
    comparison_poisson_home,
    comparison_poisson_away,
    comparison_h2h_home,
    comparison_h2h_away,
    comparison_goals_home,
    comparison_goals_away,
    comparison_total_home,
    comparison_total_away,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from flattened
