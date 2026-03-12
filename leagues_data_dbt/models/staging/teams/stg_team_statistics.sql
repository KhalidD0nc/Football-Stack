{{ config(materialized='table') }}

{% if var('use_curated_parquet', false) %}

{{ curated_source_latest('team_statistics', ['team_id', 'league_id', 'season']) }}

{% else %}

with source_dedup as (
    select
        raw,
        league_id,
        season,
        dt,
        run_id,
        _loaded_at
    from {{ source('raw', 'raw_teams_statistics') }}
    qualify row_number() over (
        partition by league_id, season, raw:entity_key::varchar
        order by _loaded_at desc
    ) = 1
),
extracted as (
    select
        raw:payload:response:team:id::int as team_id,
        raw:payload:response:team:name::varchar as team_name,
        raw:payload:response:team:logo::varchar as team_logo,
        raw:payload:response:league:id::int as stats_league_id,
        raw:payload:response:league:name::varchar as stats_league_name,
        raw:payload:response:league:season::int as stats_season,
        raw:payload:response:form::varchar as recent_form,
        raw:payload:response:fixtures:played:home::int as fixtures_played_home,
        raw:payload:response:fixtures:played:away::int as fixtures_played_away,
        raw:payload:response:fixtures:played:total::int as fixtures_played_total,
        raw:payload:response:fixtures:wins:home::int as fixtures_wins_home,
        raw:payload:response:fixtures:wins:away::int as fixtures_wins_away,
        raw:payload:response:fixtures:wins:total::int as fixtures_wins_total,
        raw:payload:response:fixtures:draws:home::int as fixtures_draws_home,
        raw:payload:response:fixtures:draws:away::int as fixtures_draws_away,
        raw:payload:response:fixtures:draws:total::int as fixtures_draws_total,
        raw:payload:response:fixtures:loses:home::int as fixtures_loses_home,
        raw:payload:response:fixtures:loses:away::int as fixtures_loses_away,
        raw:payload:response:fixtures:loses:total::int as fixtures_loses_total,
        raw:payload:response:goals:for:total:home::int as goals_for_home,
        raw:payload:response:goals:for:total:away::int as goals_for_away,
        raw:payload:response:goals:for:total:total::int as goals_for_total,
        try_to_double(raw:payload:response:goals:for:average:home::varchar) as goals_for_avg_home,
        try_to_double(raw:payload:response:goals:for:average:away::varchar) as goals_for_avg_away,
        try_to_double(raw:payload:response:goals:for:average:total::varchar) as goals_for_avg_total,
        raw:payload:response:goals:against:total:home::int as goals_against_home,
        raw:payload:response:goals:against:total:away::int as goals_against_away,
        raw:payload:response:goals:against:total:total::int as goals_against_total,
        try_to_double(raw:payload:response:goals:against:average:home::varchar) as goals_against_avg_home,
        try_to_double(raw:payload:response:goals:against:average:away::varchar) as goals_against_avg_away,
        try_to_double(raw:payload:response:goals:against:average:total::varchar) as goals_against_avg_total,
        raw:payload:response:clean_sheet:home::int as clean_sheets_home,
        raw:payload:response:clean_sheet:away::int as clean_sheets_away,
        raw:payload:response:clean_sheet:total::int as clean_sheets_total,
        raw:payload:response:failed_to_score:home::int as failed_to_score_home,
        raw:payload:response:failed_to_score:away::int as failed_to_score_away,
        raw:payload:response:failed_to_score:total::int as failed_to_score_total,
        raw:payload:response:biggest:streak:wins::int as biggest_streak_wins,
        raw:payload:response:biggest:streak:draws::int as biggest_streak_draws,
        raw:payload:response:biggest:streak:loses::int as biggest_streak_loses,
        raw:payload:response:biggest:wins:home::varchar as biggest_win_home,
        raw:payload:response:biggest:wins:away::varchar as biggest_win_away,
        raw:payload:response:biggest:loses:home::varchar as biggest_loss_home,
        raw:payload:response:biggest:loses:away::varchar as biggest_loss_away,
        raw:payload:response:biggest:goals:for:home::int as biggest_goals_for_home,
        raw:payload:response:biggest:goals:for:away::int as biggest_goals_for_away,
        raw:payload:response:biggest:goals:against:home::int as biggest_goals_against_home,
        raw:payload:response:biggest:goals:against:away::int as biggest_goals_against_away,
        source_dedup.league_id,
        source_dedup.season,
        source_dedup.dt,
        source_dedup.run_id,
        source_dedup._loaded_at
    from source_dedup
)

select
    team_id,
    team_name,
    team_logo,
    stats_league_id,
    stats_league_name,
    stats_season,
    recent_form,
    fixtures_played_home,
    fixtures_played_away,
    fixtures_played_total,
    fixtures_wins_home,
    fixtures_wins_away,
    fixtures_wins_total,
    fixtures_draws_home,
    fixtures_draws_away,
    fixtures_draws_total,
    fixtures_loses_home,
    fixtures_loses_away,
    fixtures_loses_total,
    goals_for_home,
    goals_for_away,
    goals_for_total,
    goals_for_avg_home,
    goals_for_avg_away,
    goals_for_avg_total,
    goals_against_home,
    goals_against_away,
    goals_against_total,
    goals_against_avg_home,
    goals_against_avg_away,
    goals_against_avg_total,
    clean_sheets_home,
    clean_sheets_away,
    clean_sheets_total,
    failed_to_score_home,
    failed_to_score_away,
    failed_to_score_total,
    biggest_streak_wins,
    biggest_streak_draws,
    biggest_streak_loses,
    biggest_win_home,
    biggest_win_away,
    biggest_loss_home,
    biggest_loss_away,
    biggest_goals_for_home,
    biggest_goals_for_away,
    biggest_goals_against_home,
    biggest_goals_against_away,
    league_id,
    season,
    dt,
    run_id,
    _loaded_at
from extracted

{% endif %}
