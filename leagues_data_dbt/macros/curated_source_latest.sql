{% macro curated_source_latest(table_name, partition_by, order_by=None) %}
{% set order_by = order_by or ['_loaded_at desc nulls last', 'dt desc nulls last', 'run_id desc nulls last'] %}
with source_rows as (
    select *
    from {{ source('curated', table_name) }}
)
select *
from source_rows
qualify row_number() over (
    partition by {{ partition_by | join(', ') }}
    order by {{ order_by | join(', ') }}
) = 1
{% endmacro %}
