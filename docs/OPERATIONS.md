# Operations

## Choose a storage backend

| Backend | Settings | Dependency |
| --- | --- | --- |
| Local | `STORAGE_BACKEND=local`, optional `LOCAL_ROOT` | Included |
| S3 | `STORAGE_BACKEND=s3`, `S3_BUCKET`, `AWS_REGION`, AWS credentials | `boto3` is included |
| GCS | `STORAGE_BACKEND=gcs`, `GCS_BUCKET`, optional `GCS_PROJECT`, Google credentials | Install `google-cloud-storage` separately |

Set `DATA_WAREHOUSE=none` for lake-only runs, or `snowflake` with a configured `WAREHOUSE_URI` for direct curated-table loading. Keep credentials in the ignored `.env` file or your runtime's secret configuration.

## Common CLI operations

```bash
# Fixed run date
python -m scripts.run_pipeline --date 2025-03-01 --skip-dbt-build

# Rebuild Parquet from stored JSON without fetching again
python -m scripts.run_pipeline --skip-ingestion --skip-dbt-build

# Refresh league snapshots using only baseline endpoints
python -m scripts.run_pipeline --force-league-snapshot-refresh --baseline-only --skip-dbt-build

# Skip both ingestion and flattening; print the dbt command without executing it
python -m scripts.run_pipeline --skip-ingestion --skip-flatten --dry-run
```

`--dry-run` affects the dbt subprocess only. Ingestion and flattening remain active unless explicitly skipped. Config loading still requires `API_FOOTBALL_KEY`, `LEAGUE_ID`, and `SEASON` when using the environment-based configuration, even in the last example.

`--dev-limit N` limits ingestion work and switches to configured test resources. The default dbt selector covers staging, silver, gold, and platinum, with model enablement controlled separately. Use `--select` to narrow the dbt build.

## Docker

With `.env` configured for the intended storage and warehouse:

```bash
docker compose build pipeline

# Local lake path with direct loading disabled in .env
docker compose run --rm pipeline python -m scripts.run_pipeline --skip-dbt-build
```

The image uses Python 3.12. The default Compose command runs the full pipeline, including dbt, so it requires a configured dbt profile. For warehouse runs, mount your ignored profile into `/app/leagues_data_dbt/profiles.yml` and make any referenced key file available inside the container.

## Optional Airflow

The `airflow` Compose profile adds PostgreSQL, an initialization service, a webserver, and a scheduler. It is separate from the CLI workflow.

```bash
# Set AIRFLOW__CORE__FERNET_KEY and AIRFLOW_ADMIN_PASSWORD in .env first
docker compose --profile airflow up airflow-init

docker compose --profile airflow up -d airflow-webserver airflow-scheduler
```

The webserver is exposed on port 8080 and uses the `admin` user created by the initialization service.

| DAG | Schedule | Role |
| --- | --- | --- |
| `football_daily_ingest` | Daily | Daily ingestion workflow |
| `football_pipeline` | Manual | Ingestion → flattening → dbt with mapped league/season tasks |

The Compose file documents an optional mount for `pipeline_config.json`. dbt profiles, warehouse keys, and any additional storage credentials must also be made available to the Airflow containers when needed. Validate those mounts and connections before scheduling real workloads.

## Warehouse setup boundaries

The Python loader and dbt profile use separate connection settings. `scripts/init_warehouse.py` is an optional helper that creates the fixed `LEAGUES_DATA` or `LEAGUES_DATA_TEST` databases and their `RAW`/`STAGING` schemas; review those fixed names before running it. Warehouse execution is outside offline CI.
