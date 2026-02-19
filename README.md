# Leagues Data Project

## Scope
This repository is for **Data Engineering only**. It focuses on the automated ingestion, storage, and transformation of football data (SPL/API-Football) into a queryable data lake.

## Stage Tracker
We keep only two active stage labels:
- `Current Stage`: the stage being executed now
- `Next Stage`: the immediate follow-up stage

Transition rule (must be followed every stage):
1. Move `Next Stage` into `Current Stage`
2. Define a new `Next Stage`
3. Update both:
   - `README.md`
   - `docs/Data Engineering Architecture and Plan.md`
   - `docs/Data Engineering Implementation Checklist.md`

## Current Stage
**Stage 3 - Silver Modeling and Normalization (In Progress)**
- Transform Bronze payloads into normalized, queryable Silver entities using dbt.
- Standardize keys (team_id, player_id, fixture_id) across all models.
- Implement staging layer for fixtures, teams, players, and statistics.
- Enforce schema contracts and data quality checks (uniqueness, referential integrity).

### Stage 3 Progress (Latest)
- Phase 1 foundations completed:
  - dbt source definitions added in `/Users/khalidr/Desktop/Leagues_Data_Project/leagues_data_dbt/models/sources/raw_sources.yml`
  - staging contracts/tests scaffolded in `/Users/khalidr/Desktop/Leagues_Data_Project/leagues_data_dbt/models/staging/staging_schema.yml`
- Stage 3 model implementation complete (15 staging models):
  - Teams: `stg_teams`, `stg_team_standings`, `stg_team_statistics`
  - Fixtures: `stg_fixtures`, `stg_rounds`, `stg_match_events`, `stg_match_team_stats`, `stg_match_player_stats`, `stg_lineup_players`, `stg_predictions`
  - Players: `stg_player_season_stats`, `stg_player_leaderboards`, `stg_squad_players`
  - Transfers/availability: `stg_transfers`, `stg_injuries`
- Key parsing fix applied for fixture-level endpoints:
  - For `/fixtures/statistics` and `/fixtures/lineups`, `fixture_id` is extracted from `raw:params:fixture` (not from `payload.response`).
- Current focus: Stage 3 hardening (full build stability, quality evidence, and stage-transition docs).

## Next Stage
**Stage 4 - Gold Marts and Analytics**
- Build curated Gold-layer models for downstream consumers (e.g., Team Performance, Player Form).
- Implement advanced business logic and KPI calculations.
- Finalize data freshness and observability dashboards.

## Features

### Ingestion (Bronze Layer)
- **Coverage**: Full league baseline (fixtures, teams, standings, rounds) and deep details (statistics, events, lineups, players, predictions, injuries, transfers).
- **Idempotency**: All ingestion steps use S3 marker files to prevent duplicate API calls and ensure safe re-runs.
- **Resilience**: API client includes exponential backoff retry logic and rate limiting.
- **Paginated Ingestion**: Optimized handling for large datasets like league-wide player lists.

### Transformation (Silver Layer)
- **dbt Integration**: Modern transformation workflow with version-controlled SQL.
- **Schema Contracts**: explicit casts and column documentation for all staging models.
- **Data Quality**: Automated dbt tests for `not_null`, `unique`, and `accepted_values`.
- **Deduplication**: Intelligent handling of raw partition overlaps to ensure a consistent Silver state.

## Environment Setup

1. **Python Environment**: Initialize a virtual environment and install dependencies.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**: Copy the example environment file and fill in your credentials (API-Football key, AWS credentials for S3).
   ```bash
   cp .env.example .env
   ```

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

### dbt Transformations
The dbt project is located in `leagues_data_dbt`.

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
