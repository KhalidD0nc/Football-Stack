{% macro sync_raw_from_s3(run_date=None, raw_database=None, raw_schema='RAW', stage_name='LEAGUES_STAGE') %}
  {%- set db_name = raw_database if raw_database else target.database -%}
  {%- set dt_pattern = "dt=.*" -%}
  {%- if run_date is not none and (run_date | trim) != "" -%}
    {%- set dt_pattern = "dt=" ~ run_date -%}
  {%- endif -%}

  {%- set endpoints = [
      "fixtures",
      "teams",
      "standings",
      "fixtures_rounds",
      "players",
      "players_topscorers",
      "players_topassists",
      "players_topyellowcards",
      "players_topredcards",
      "teams_statistics",
      "injuries",
      "transfers",
      "players_squads",
      "fixtures_statistics",
      "fixtures_events",
      "fixtures_lineups",
      "fixtures_players",
      "predictions"
  ] -%}

  {% do log("Ensuring RAW objects in " ~ db_name ~ "." ~ raw_schema, info=True) %}
  {% do run_query("create schema if not exists " ~ db_name ~ "." ~ raw_schema) %}
  {% do run_query("create file format if not exists " ~ db_name ~ "." ~ raw_schema ~ ".json_raw type = json strip_outer_array = false ignore_utf8_errors = true") %}

  {% for endpoint in endpoints %}
    {% set table_name = "raw_" ~ endpoint %}
    {% set create_sql %}
      create table if not exists {{ db_name }}.{{ raw_schema }}.{{ table_name }} (
          raw variant not null,
          league_id int,
          season int,
          dt date,
          run_id varchar,
          _file_name varchar,
          _loaded_at timestamp_ntz default current_timestamp()
      )
    {% endset %}
    {% do run_query(create_sql) %}
  {% endfor %}

  {% do log("Starting COPY INTO sync from @" ~ db_name ~ "." ~ raw_schema ~ "." ~ stage_name ~ " using dt filter " ~ dt_pattern, info=True) %}
  {% for endpoint in endpoints %}
    {% set table_name = "raw_" ~ endpoint %}
    {% set file_pattern = '.*endpoint=' ~ endpoint ~ '/' ~ dt_pattern ~ '/run_id=[^/]+/part-.*\\.json' %}
    {% set copy_sql %}
      copy into {{ db_name }}.{{ raw_schema }}.{{ table_name }} (raw, league_id, season, dt, run_id, _file_name)
      from (
          select
              $1,
              regexp_substr(metadata$filename, 'league=([0-9]+)', 1, 1, 'e', 1)::int,
              regexp_substr(metadata$filename, 'season=([0-9]+)', 1, 1, 'e', 1)::int,
              regexp_substr(metadata$filename, 'dt=([0-9-]+)', 1, 1, 'e', 1)::date,
              regexp_substr(metadata$filename, 'run_id=([^/]+)', 1, 1, 'e', 1),
              metadata$filename
          from @{{ db_name }}.{{ raw_schema }}.{{ stage_name }}
      )
      pattern = '{{ file_pattern }}'
      file_format = {{ db_name }}.{{ raw_schema }}.json_raw
      force = false
    {% endset %}

    {% do log("COPY INTO " ~ db_name ~ "." ~ raw_schema ~ "." ~ table_name ~ " with pattern " ~ file_pattern, info=True) %}
    {% set copy_result = run_query(copy_sql) %}
    {% if execute and copy_result is not none and (copy_result.rows | length) > 0 %}
      {% do log("COPY result " ~ table_name ~ ": " ~ (copy_result.rows[0] | string), info=True) %}
    {% endif %}
  {% endfor %}
{% endmacro %}
