# Architecture and data contracts

## Pipeline stages

| Stage | Code | Contract |
| --- | --- | --- |
| Configure | `src/pipeline/config.py` | One or more league/season targets with explicit storage and warehouse selection |
| Fetch | `api_client.py`, `fetch.py`, `steps.py` | API-Football responses plus attempt/failure accounting and fetch markers |
| Persist raw | `storage.py` | Original JSON payloads partitioned by source, league, season, endpoint, date, and run |
| Flatten | `flatten.py`, `schemas.py` | Typed rows with source/entity deduplication and schema-backed Parquet output |
| Load | `flatten.py` | Optional Snowflake curated-table synchronization |
| Transform | `leagues_data_dbt/` | Staging → silver → optional gold → optional platinum models |
| Orchestrate | `scripts/run_pipeline.py`, `airflow/dags/` | CLI execution or optional Airflow tasks |

## Storage layout

```text
data_lake/
├── raw/source=api_football/league=…/season=…/endpoint=…/dt=…/run_id=…/
├── curated/source=api_football/league=…/season=…/endpoint=…/dt=…/run_id=…/
└── … fetch markers used by ingestion
```

The same logical keys are used by local, S3, and GCS writers. Raw objects contain JSON; curated objects contain Parquet. Marker checks reduce duplicate fetches, while deduplication resolves overlapping source rows. Refresh flags deliberately bypass selected marker checks.

## Warehouse boundary

The direct-load path supports `snowflake` and `none`. In Snowflake mode, the Python flatten stage loads the curated tables used by dbt's `curated` source. A failed warehouse synchronization raises `WarehouseSyncError`; orchestration stops before dbt.

`use_curated_parquet` is enabled in `dbt_project.yml`: its name refers to the curated data path, but the SQL reads warehouse tables rather than Parquet files directly. Legacy raw JSON branches remain in the staging SQL. Gold and platinum use Snowflake-specific SQL and are disabled by default.

GCS is an implemented lake backend. `scripts/init_bigquery.py` refers to `sql/bigquery_ddl.sql`, which is not included on this branch; that helper is not a complete, runnable BigQuery setup path.

## Environment separation

Storage, Python warehouse loading, and dbt each have configuration boundaries. Keep them aligned:

- Set `STORAGE_BACKEND` explicitly; otherwise configured bucket variables can influence backend inference.
- Limited runs can select `S3_BUCKET_TEST`, `GCP_BUCKET_TEST`, `WAREHOUSE_URI_TEST`, and dbt's `test` target.
- dbt's schema macro uses explicit model schema names without prefixing `target.schema`. Use separate databases or accounts for environment isolation; changing the target schema alone does not isolate every layer.
- `pipeline_config.json` can override environment defaults for multi-target runs.

## Verification

The offline suite uses local files, fixtures, and mocks. dbt parsing checks project configuration and the dependency graph; it does not validate SQL execution against Snowflake. Live ingestion, warehouse transformations, and Airflow scheduling require their own configured integration verification.

The existing [pipeline illustration](../resources/pipeline_diagram.png) is retained as a project resource; the current source and module contracts above define the active execution path.
