{% macro sync_curated_from_s3(run_date=None, curated_database=None, curated_schema='CURATED', stage_name='LEAGUES_STAGE') %}
  {%- set db_name = curated_database if curated_database else target.database -%}
  {%- set dt_pattern = "dt=.*" -%}
  {%- if run_date is not none and (run_date | trim) != "" -%}
    {%- set dt_pattern = "dt=" ~ run_date -%}
  {%- endif -%}

  {%- set curated_tables = [
      "teams",
      "fixtures",
      "rounds",
      "match_events",
      "match_team_stats",
      "match_player_stats",
      "lineup_players",
      "predictions",
      "player_season_stats",
      "player_leaderboards",
      "squad_players",
      "team_standings",
      "team_statistics",
      "transfers",
      "injuries"
  ] -%}

  {% do log("Ensuring CURATED objects in " ~ db_name ~ "." ~ curated_schema, info=True) %}
  {% do run_query("create schema if not exists " ~ db_name ~ "." ~ curated_schema) %}
  {% do run_query("create file format if not exists " ~ db_name ~ "." ~ curated_schema ~ ".parquet_curated type = parquet") %}

  {% do log("Starting COPY INTO sync from @" ~ db_name ~ "." ~ curated_schema ~ "." ~ stage_name ~ "/curated/ using dt filter " ~ dt_pattern, info=True) %}

  {% for table_name in curated_tables %}
    {%- set file_pattern = '.*endpoint=' ~ table_name ~ '/' ~ dt_pattern ~ '/run_id=[^/]+/data\\.parquet' -%}

    {#- Step 1: Create table from Parquet schema if it does not exist.
        Uses INFER_SCHEMA to auto-detect column names and types from Parquet files.
        This requires at least one Parquet file to exist in the stage for this endpoint. -#}
    {% set create_sql %}
      create table if not exists {{ db_name }}.{{ curated_schema }}.{{ table_name }}
        using template (
          select array_agg(object_construct(*))
          from table(
            infer_schema(
              location => '@{{ db_name }}.{{ curated_schema }}.{{ stage_name }}/curated/'
              , file_format => '{{ db_name }}.{{ curated_schema }}.parquet_curated'
              , files => 'source=api_football/'
            )
          )
        )
    {% endset %}

    {#- Step 2: COPY INTO with MATCH_BY_COLUMN_NAME maps Parquet columns to table columns. -#}
    {% set copy_sql %}
      copy into {{ db_name }}.{{ curated_schema }}.{{ table_name }}
      from @{{ db_name }}.{{ curated_schema }}.{{ stage_name }}/curated/
      pattern = '{{ file_pattern }}'
      file_format = {{ db_name }}.{{ curated_schema }}.parquet_curated
      match_by_column_name = case_insensitive
      force = false
    {% endset %}

    {% do log("COPY INTO " ~ db_name ~ "." ~ curated_schema ~ "." ~ table_name ~ " with pattern " ~ file_pattern, info=True) %}

    {% if execute %}
      {#- Attempt schema-inferred table creation; log warning if no files exist yet -#}
      {% set ns = namespace(table_ready=true) %}
      {% do run_query(create_sql) %}

      {% set copy_result = run_query(copy_sql) %}
      {% if copy_result is not none and (copy_result.rows | length) > 0 %}
        {% do log("COPY result " ~ table_name ~ ": " ~ (copy_result.rows[0] | string), info=True) %}
      {% endif %}
    {% endif %}
  {% endfor %}
{% endmacro %}
