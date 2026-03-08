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
**Stage 5 - Agent Integration & Data Observability (Completed/In Progress)**
- Build advanced Platinum-layer models tailored for AI capabilities (Match Intelligence, Player Archetypes, Prediction Accuracy).
- Establish stable interfaces and final documentation for the AI coaching system.
- Implement specialized marts for agent features (e.g., Playing Styles, Event Momentum).
- Finalize automated quality and freshness reporting.

### Stage 3 & 4 Progress (Completed)
- Stage 3 normalized Silver models created (15 staging, 9 silver entities).
- Phase 1 foundations and schema contracts implemented natively in dbt.
- Gold Layer models fully built and executed successfully:
  - **Teams**: `gold_team_performance_summary`, `gold_team_scoring_profile`, `gold_team_discipline_profile`
  - **Players**: `gold_player_performance_mart`, `gold_player_season_summary`
  - **Fixtures**: `gold_match_team_performance`
  - **Availability**: `gold_squad_availability`
- Grain bug resolved via `league_id` and `season` groupings. Null handling fixed via `COALESCE`.

### Stage 5 Progress (Latest)
- Platinum Layer (AI Features) created and verified:
  - **Teams (5 models)**: Attacking Style, Defensive Consistency, Discipline Risk, Form Momentum, Home Fortress.
  - **Players (5 models)**: Duel Dominance, Impact Score, Per-90 Efficiency, Performance Trend, Style Fingerprint.
  - **Fixtures (1 model)**: Match Intelligence.
  - **Predictions (1 model)**: Prediction Accuracy.
- Verified agent-ready correctness, extracted logic for upsets, handling of goalless draws safely, and player styles modeling.

## Next Stage
**Stage 6 - Productionization & CI/CD**
- Build test suites focusing on data freshness and volume anomalies.
- Finalize CI/CD pipeline and automated data lineage tracking.
- Orchestrate end-to-end multi-season backfills incrementally.

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

What this command does:
- Runs API-Football ingestion to S3 (`scripts.run_daily` logic).
- Runs dbt macro `sync_raw_from_s3` to load new S3 files into `LEAGUES_DATA.RAW.*`.
- Runs `dbt build --select staging silver gold` (models + tests).

Season selection note:
- `SEASON` is always read from `.env` (`SEASON=...`), including when `--league-id` is used.

If you want it fully unattended on one machine, schedule it with `cron`:

```bash
15 3 * * * cd /Users/khalidr/Desktop/Leagues_Data_Project && /bin/zsh -lc 'source .venv/bin/activate && python -m scripts.run_pipeline >> logs/pipeline.log 2>&1'
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
