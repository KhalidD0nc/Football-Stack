# Football Intelligence Platform — Project Context

---

## What Is This Project

A **football data intelligence platform** for the Saudi Pro League (SPL). It powers a coaching/competitor analysis AI agent with comprehensive match, player, and team data.

**Goal:** Enable coaches to ask natural language questions like:
- "How does Al Hilal's attack compare to Al Ittihad's defense?"
- "Which midfielder had the best pass accuracy this season?"
- "Show me Al Nassr's formation trends and win rates"
- "What's the predicted outcome for the next Al Ahli match?"

---

## Architecture

```
API-Football (v3) → Python ETL → S3 (raw JSON) → Snowflake (COPY INTO) → dbt → AI Agent
```

### Tech Stack
| Layer          | Technology                              |
|----------------|----------------------------------------|
| Data Source     | API-Football v3 (api-sports.io)        |
| Extraction      | Python (boto3, requests)               |
| Storage         | AWS S3 (`leagues-datalake` bucket)     |
| Warehouse       | Snowflake                              |
| Transformation  | dbt (dbt-snowflake)                    |
| AI Agent        | TBD                                    |
| AWS Region      | eu-north-1 (Stockholm)                 |

---

## Current Status

### ✅ DONE — Bronze Layer (Raw Ingestion)

1. **Python ETL** — Extracts 18 endpoints from API-Football, saves to S3
2. **S3 Storage** — Hive-style partitioned paths with idempotency tracking
3. **Snowflake RAW** — 18 tables loaded via COPY INTO, JSON stored as VARIANT

### 🔄 IN PROGRESS — Silver Layer (dbt Staging)

- dbt project needs to be initialized
- Staging models need to be written (flatten JSON → clean tables)

### ⬜ TODO — Gold Layer (dbt Marts)

- Fact and dimension tables for analytics
- AI agent integration

---

## Data Source: API-Football v3

- **League ID:** 307 (Saudi Pro League)
- **Season:** 2025
- **Base URL:** `https://v3.football.api-sports.io`

### 18 Endpoints Extracted

| # | Endpoint | Scope | Files Per Run | Description |
|---|----------|-------|---------------|-------------|
| 1 | `/fixtures` | League | 1 | All 306 season fixtures & scores |
| 2 | `/teams` | League | 1 | 18 SPL team profiles & venues |
| 3 | `/standings` | League | 1 | League table (18 teams nested) |
| 4 | `/fixtures/rounds` | League | 1 | Matchday/round names |
| 5 | `/players` | League | ~34 | Paginated player season stats (20/page) |
| 6 | `/players/topscorers` | League | 1 | Top goal scorers |
| 7 | `/players/topassists` | League | 1 | Top assist providers |
| 8 | `/players/topyellowcards` | League | 1 | Most yellow cards |
| 9 | `/players/topredcards` | League | 1 | Most red cards |
| 10 | `/teams/statistics` | Per team | 18 | Aggregated team season stats |
| 11 | `/injuries` | Per team | 18 | Player injuries & suspensions |
| 12 | `/transfers` | Per team | 18 | Transfer records |
| 13 | `/players/squads` | Per team | 18 | Current roster per team |
| 14 | `/fixtures/statistics` | Per fixture | ~58* | Match stats (possession, shots, etc.) |
| 15 | `/fixtures/events` | Per fixture | ~58* | Goals, cards, substitutions |
| 16 | `/fixtures/lineups` | Per fixture | ~58* | Formations, starters, bench |
| 17 | `/fixtures/players` | Per fixture | ~58* | Per-player match performance |
| 18 | `/predictions` | Per fixture | ~58* | Pre-match win predictions & comparison |

*58 = number of finished fixtures as of 2026-02-15. Grows as season progresses.

---

## S3 Structure

**Bucket:** `leagues-datalake`
**Region:** eu-north-1

### Path Format (Hive-style partitions)
```
raw/source=api_football/league={id}/season={year}/
  endpoint={name}/dt={YYYY-MM-DD}/run_id={timestamp}/part-{NNNNN}.json
```

### Example
```
raw/source=api_football/league=307/season=2025/
  endpoint=fixtures/dt=2026-02-15/run_id=20260215T075848Z/part-00001.json
```

### JSON File Structure
Every file contains:
```json
{
  "endpoint": "/fixtures",
  "entity_key": "league_snapshot",
  "params": {"league": 307, "season": 2025},
  "fetched_at": "2026-02-15T07:58:52Z",
  "payload": { ... API response ... }
}
```

### Idempotency
- `state/` folder contains marker files to prevent duplicate API calls
- Pipeline checks markers before each fetch — safe to re-run
- Marker path: `state/source=api_football/league={id}/season={year}/endpoint={name}/dt={date}/idempotency_key={hash}.json`

---

## Snowflake Setup

### Connection Details
| Setting    | Value                |
|------------|---------------------|
| Database   | `LEAGUES_DATA`       |
| Schema     | `RAW`                |
| Warehouse  | (user-specific)      |
| Stage      | `LEAGUES_STAGE`      |
| File Format| `json_raw`           |

### Stage Configuration
```sql
-- Stage points to bucket root, uses credentials (no IAM role)
CREATE STAGE LEAGUES_STAGE
  URL = 's3://leagues-datalake/'
  CREDENTIALS = (AWS_KEY_ID = '...' AWS_SECRET_KEY = '...')
  FILE_FORMAT = json_raw;
```

### 18 RAW Tables

All tables share the same schema:
```sql
CREATE TABLE raw_{endpoint} (
    raw             VARIANT        NOT NULL,   -- full JSON blob
    league_id       INT,                       -- extracted from S3 path
    season          INT,                       -- extracted from S3 path
    dt              DATE,                      -- run date
    run_id          VARCHAR,                   -- run timestamp
    _file_name      VARCHAR,                   -- S3 file path
    _loaded_at      TIMESTAMP_NTZ  DEFAULT CURRENT_TIMESTAMP()
);
```

**Tables:**
```
raw_fixtures              raw_players_topscorers     raw_teams_statistics
raw_teams                 raw_players_topassists     raw_injuries
raw_standings             raw_players_topyellowcards raw_transfers
raw_fixtures_rounds       raw_players_topredcards    raw_players_squads
raw_players               raw_fixtures_statistics    raw_predictions
raw_fixtures_events       raw_fixtures_lineups       raw_fixtures_players
```

### COPY INTO Pattern
```sql
COPY INTO raw_{endpoint} (raw, league_id, season, dt, run_id, _file_name)
FROM (
    SELECT
        $1,
        REGEXP_SUBSTR(METADATA$FILENAME, 'league=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'season=([0-9]+)', 1, 1, 'e')::INT,
        REGEXP_SUBSTR(METADATA$FILENAME, 'dt=([0-9-]+)',    1, 1, 'e')::DATE,
        REGEXP_SUBSTR(METADATA$FILENAME, 'run_id=([^/]+)',  1, 1, 'e'),
        METADATA$FILENAME
    FROM @LEAGUES_STAGE
)
PATTERN = '.*raw/source=api_football/.*endpoint={endpoint_name}/dt=.*/part-.*\\.json'
FILE_FORMAT = json_raw;
```

- COPY INTO is idempotent — Snowflake skips already-loaded files
- Re-run same statements after each pipeline run to load new data

### Data Volumes (as of 2026-02-15)

| Endpoint | Raw Rows | Nested Records (after FLATTEN) |
|----------|----------|-------------------------------|
| transfers | 18 | 2,573 |
| players | 34 | 666 |
| fixtures | 1 | 306 |
| teams_statistics | 18 | 198 |
| teams | 1 | 18 |
| players_squads | 18 | 18 |
| injuries | 18 | 2 |
| standings | 1 | 1 (contains 18 teams nested) |
| fixtures_events | ~58 | TBD |
| fixtures_lineups | ~58 | TBD |
| fixtures_players | ~58 | TBD |
| fixtures_statistics | ~58 | TBD |
| predictions | ~58 | TBD |

---

## Pipeline Code Structure

```
src/pipeline/
├── api_client.py    — HTTP client for API-Football
├── config.py        — PipelineConfig (league_id, season, keys, etc.)
├── ingest.py        — Main ingestion logic (6 steps)
├── storage.py       — S3Writer (put_raw, put_marker, idempotency)
└── run_daily.py     — CLI entrypoint: python run_daily.py --date 2026-02-15
```

### Ingestion Steps (ingest.py)
1. Fetch all fixtures → identify finished fixture IDs
2. Fetch all teams → extract team IDs
3. League-level baselines (standings, rounds, top scorers/assists/cards)
4. Paginated player stats (all league players)
5. Team-level endpoints for all 18 teams (stats, injuries, transfers, squads)
6. Deep fixture details for all finished matches (statistics, events, lineups, players, predictions)

### Key Design Decisions
- **One file per API response** — not merged, enables granular tracking
- **Global part counter** — part numbers are sequential across all endpoints in a run
- **Idempotency via S3 markers** — safe to re-run, skips already-fetched data
- **Finished fixtures only** for detail endpoints (status: FT, AET, PEN)

---

## Accessing the Data

### JSON Navigation (Snowflake VARIANT)
```sql
-- Access nested fields
raw:endpoint::VARCHAR                          -- "/fixtures"
raw:payload:response                           -- API response array
raw:payload:response[0]:league:name::VARCHAR   -- "Pro League"
raw:fetched_at::TIMESTAMP                      -- when data was pulled

-- Flatten nested arrays
SELECT f.value:fixture:id::INT AS fixture_id
FROM raw_fixtures,
     LATERAL FLATTEN(input => raw:payload:response) f;
```

### Example Queries

**Standings:**
```sql
SELECT
    s.value:rank::INT AS rank,
    s.value:team:name::VARCHAR AS team,
    s.value:points::INT AS points,
    s.value:all:played::INT AS played,
    s.value:all:win::INT AS wins
FROM raw_standings,
     LATERAL FLATTEN(input => raw:payload:response[0]:league:standings[0]) s
ORDER BY rank;
```

**Al Hilal Players:**
```sql
SELECT
    p.value:player:name::VARCHAR AS player_name,
    s.value:games:appearences::INT AS appearances,
    s.value:games:rating::FLOAT AS rating,
    s.value:goals:total::INT AS goals,
    s.value:goals:assists::INT AS assists
FROM raw_players,
     LATERAL FLATTEN(input => raw:payload:response) p,
     LATERAL FLATTEN(input => p.value:statistics) s
WHERE s.value:team:name::VARCHAR ILIKE '%hilal%'
ORDER BY goals DESC NULLS LAST;
```

**Match Events (Goals):**
```sql
SELECT
    e.value:team:name::VARCHAR AS team,
    e.value:player:name::VARCHAR AS player,
    e.value:type::VARCHAR AS event_type,
    e.value:time:elapsed::INT AS minute
FROM raw_fixtures_events,
     LATERAL FLATTEN(input => raw:payload:response) e
WHERE e.value:type::VARCHAR = 'Goal';
```

**Predictions:**
```sql
SELECT
    raw:payload:response[0]:predictions:winner:name::VARCHAR AS predicted_winner,
    raw:payload:response[0]:predictions:advice::VARCHAR AS advice,
    raw:payload:response[0]:predictions:percent:home::VARCHAR AS home_win_pct,
    raw:payload:response[0]:predictions:percent:away::VARCHAR AS away_win_pct
FROM raw_predictions;
```

---

## What Needs To Be Done Next

### 1. Initialize dbt Project
```bash
pip install dbt-snowflake
dbt init leagues_data
```

### 2. Define Sources (sources.yml)
Point dbt at the 18 RAW tables.

### 3. Build Staging Models (Silver Layer)
Flatten each RAW table into clean, typed tables:
```
raw_fixtures         → stg_fixtures, stg_fixture_scores
raw_players          → stg_players, stg_player_stats
raw_teams            → stg_teams, stg_venues
raw_standings        → stg_standings
raw_transfers        → stg_transfers
raw_fixtures_events  → stg_fixture_events
raw_fixtures_players → stg_fixture_player_stats
raw_predictions      → stg_predictions
... etc (expect ~25-30 staging tables)
```

### 4. Build Marts (Gold Layer)
Business-ready tables:
```
fct_matches          — match results with stats
fct_player_performance — player ratings over time
fct_transfers        — transfer analysis
dim_teams            — team dimension
dim_players          — player dimension
dim_standings_history — standings progression
```

### 5. AI Coaching Agent
Connect to Snowflake marts and enable natural language queries.

---

## Multi-League Support

The architecture supports multiple leagues with zero schema changes:
- Add a league to the Python config → pipeline fetches it
- Same COPY INTO statements load all leagues
- Filter by `league_id` in queries:
```sql
WHERE league_id = 307  -- Saudi Pro League
WHERE league_id = 39   -- Premier League
```

---

## Daily Operations

### Run Pipeline
```bash
python run_daily.py --date 2026-02-15
```

### Load New Data into Snowflake
Re-run the same COPY INTO statements — Snowflake auto-skips already-loaded files.

### Transform with dbt
```bash
cd leagues_data
dbt run
```

---

## Important Notes

- S3 credentials are used for Snowflake access (no IAM role)
- The `state/` folder in S3 is for pipeline idempotency only, not loaded into Snowflake
- Part numbers in filenames are a global counter per run, not per endpoint
- Standings has 1 raw row but 18 teams nested inside
- Season 2025 has 306 total fixtures, 58 finished as of Feb 15, 2026