# Leagues Data Project

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![dbt](https://img.shields.io/badge/dbt-compatible-orange.svg)

**Are you looking to build a data-driven football product, train Machine Learning models, or power AI agents with high-quality sports analytics?**

**Leagues Data Project** is your starting point. It is an end-to-end data engineering pipeline that automates the ingestion, storage, and transformation of football (soccer) league data via [API-Football](https://www.api-football.com/). 

💡 **Cost-Efficient & High Performance:** We built this architecture with a relentless focus on minimizing operational costs while maximizing performance. By utilizing intelligent idempotency (to eliminate redundant and costly API calls), local-first development options, and optimized data processing, we drastically lowered the cost of running a large-scale sports data pipeline.

It is designed to be fully extensible, supporting any league globally without hardcoded defaults, and orchestrates data from raw API payloads all the way to agent-ready AI features.

<div align="center">
  <img src="resources/pipeline_diagram.png" alt="Leagues Data Project Pipeline Diagram" />
</div>

## Features

### Ingestion (Bronze Layer)
- **Coverage**: Full league baseline (fixtures, teams, standings, rounds) and deep details (statistics, events, lineups, players, predictions, injuries, transfers).
- **Multi-Provider Storage**: Pluggable storage backends — **local filesystem** (default, zero cloud deps), **AWS S3**, or **Google Cloud Storage**. Controlled via `STORAGE_BACKEND` env var or config file.
- **Idempotency**: All ingestion steps use marker files to prevent duplicate API calls and ensure safe re-runs.
- **Resilience**: API client includes exponential backoff retry logic and rate limiting.
- **Paginated Ingestion**: Optimized handling for large datasets like league-wide player lists.

### Transformation (Silver Layer)
- **dbt Integration**: Modern transformation workflow with version-controlled SQL.
- **Schema Contracts**: explicit casts and column documentation for all staging models.
- **Data Quality**: Automated dbt tests for `not_null`, `unique`, and `accepted_values`.
- **Deduplication**: Intelligent handling of raw partition overlaps to ensure a consistent Silver state.

### Transformation (Platinum Layer - AI Features)
- **Agent-Ready Marts**: 12 highly enriched models optimized specifically for LLM-based coaching agents.
- **Player Archetypes**: Standardized 0-100 scores across 6 distinct profiles via `platinum_player_style_fingerprint`.
- **Match Narratives**: Halftime swing, goal margins, and expected goals dominance via `platinum_match_intelligence`.
- **Prediction Scoring**: Accurate confidence tracking and upset detection via `platinum_prediction_accuracy`.

## Environment Setup

1. **Python Environment**: Initialize a virtual environment and install dependencies.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**: Copy the example environment file and fill in your credentials.
   ```bash
   cp .env.example .env
   ```
   At minimum you need `API_FOOTBALL_KEY`, `LEAGUE_ID`, and `SEASON`. Storage defaults to local filesystem (`data_lake/` directory) — no cloud credentials required to get started.

3. **Multi-League Config** (optional): For multi-league, multi-season runs, copy and edit the JSON config:
   ```bash
   cp pipeline_config.json.example pipeline_config.json
   ```

### Storage Backends

| Backend | `STORAGE_BACKEND` | Required vars | Extra dependency |
|---|---|---|---|
| Local filesystem (default) | `local` | `LOCAL_ROOT` (default `data_lake`) | None |
| AWS S3 | `s3` | `S3_BUCKET`, `AWS_REGION`, AWS credentials | `boto3` |
| Google Cloud Storage | `gcs` | `GCS_BUCKET`, optionally `GCS_PROJECT` | `google-cloud-storage` |

Backward compat: if `STORAGE_BACKEND` is unset but `S3_BUCKET` is set, the backend is inferred as `s3`.

## Quick Start

### Python Ingestion
To run the daily ingestion script:

```bash
python -m scripts.run_daily
```

By default, this will run for the current date. You can also specify a specific date:

```bash
python -m scripts.run_daily --date 2026-02-15
```

Run a specific league id (single-league run):

```bash
python -m scripts.run_daily --league-id 39
python -m scripts.run_daily --league-id 307
```

### End-to-End Automated Pipeline (Recommended)
Run ingestion + Snowflake RAW sync (`COPY INTO`) + dbt build in one command:

```bash
python -m scripts.run_pipeline
```

Optional date override:

```bash
python -m scripts.run_pipeline --date 2026-02-15
```

Run a specific league id (single-league run):

```bash
python -m scripts.run_pipeline --league-id 39
python -m scripts.run_pipeline --league-id 307
```

Multi-league run from a JSON config file:

```bash
python -m scripts.run_pipeline --config pipeline_config.json
```

**Ingestion-only mode** (local storage users, skip Snowflake/dbt):

```bash
python -m scripts.run_pipeline --skip-raw-sync --skip-dbt-build
```

If you need to resync pending RAW files across all dates (no `dt` filter):

```bash
python -m scripts.run_pipeline --skip-ingestion --raw-sync-all-dates
```

If late-night fixtures finished after your first run on the same date, force-refresh league snapshots:

```bash
python -m scripts.run_pipeline --force-league-snapshot-refresh
```

For a low-cost same-day refresh (baseline endpoints only):

```bash
python -m scripts.run_pipeline --force-league-snapshot-refresh --baseline-only
```

What the full pipeline does:
- Runs API-Football ingestion to the configured storage backend.
- Runs dbt macro `sync_raw_from_s3` to load S3 files into `LEAGUES_DATA.RAW.*` (S3 backend only).
- Runs `dbt build --select staging silver gold platinum` (models + tests). **Note:** Gold and Platinum models are disabled by default.

To enable the advanced analytical layers (Gold) and AI features (Platinum), use the respective flags. (**Note:** Enabling Platinum automatically enables the Gold layer it depends on):
```bash
python -m scripts.run_pipeline --enable-gold --enable-platinum
```

Season selection note:
- `SEASON` is always read from `.env` (`SEASON=...`), including when `--league-id` is used.

If you want it fully unattended on one machine, schedule it with `cron`:

```bash
15 3 * * * cd /path/to/Leagues_Data_Project && /bin/zsh -lc 'source .venv/bin/activate && python -m scripts.run_pipeline >> logs/pipeline.log 2>&1'
```

### dbt Transformations
The dbt project is located in `leagues_data_dbt`.

Note: The orchestration script expects `dbt` CLI to be installed and available on `PATH`.

```bash
cd leagues_data_dbt
dbt deps      # Install dependencies
dbt build     # Run models and tests
```

Targeted builds used for current staging rollout:
```bash
dbt build -s stg_teams stg_player_leaderboards
dbt build -s stg_match_team_stats stg_lineup_players
dbt build -s stg_fixtures stg_rounds stg_match_events
dbt build -s stg_match_player_stats stg_predictions
dbt build -s stg_team_standings stg_team_statistics stg_player_season_stats stg_squad_players stg_transfers stg_injuries
dbt build -s staging
dbt build -s silver
dbt run -s gold --full-refresh
```

To view documentation:
```bash
dbt docs generate
dbt docs serve
```

## Project Structure
- `src/pipeline/`: Core ingestion logic (API client, storage, orchestration).
- `leagues_data_dbt/`: dbt project for SQL transformations.
- `scripts/`: Operational scripts and entry points.
- `docs/`: Strategic architecture and implementation tracking.
- `tests/`: Unit and integration tests for the Python pipeline.

## Primary Documents
Architecture plan:
- `docs/Data Engineering Architecture and Plan.md`
Implementation checklist:
- `docs/Data Engineering Implementation Checklist.md`
Project Context:
- `docs/Project_Context.md`

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

Please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on how to set up the project and submit your pull requests.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
