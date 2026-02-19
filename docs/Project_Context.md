# Football Intelligence Platform — Project Context

---

## What Is This Project

A **football data intelligence platform** for the Saudi Pro League (SPL). It powers a coaching and competitor analysis AI agent with comprehensive match, player, and team data. Additionally being built as a **public dataset** of the SPL 2025 season.

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

| Layer        | Technology                       | Detail                                      |
|--------------|----------------------------------|---------------------------------------------|
| Data Source  | API-Football v3 (api-sports.io)  | League ID 307, Season 2025                  |
| Extraction   | Python (boto3, requests, tenacity) | scripts/run_daily.py → src/pipeline/ingest.py |
| Storage      | AWS S3                           | Bucket: leagues-datalake / Region: eu-north-1 |
| Warehouse    | Snowflake                        | DB: LEAGUES_DATA / Schema: RAW              |
| Transformation | dbt (dbt-snowflake)            | Project: leagues_data/                      |
| AI Agent     | TBD                              | Will connect to dbt Gold layer marts        |

---

## Current Status

### ✅ DONE — Bronze Layer (Raw Ingestion)

1. **Python ETL** — Extracts 18 endpoints from API-Football, saves to S3
2. **S3 Storage** — Hive-style partitioned paths with idempotency tracking
3. **Snowflake RAW** — 18 tables loaded via COPY INTO, JSON stored as VARIANT
4. **Full Discovery** — All 18 tables explored, JSON structures mapped, data quality issues documented

### 🔄 NEXT — Staging Layer (dbt)

- Build 15 staging models in dbt (flatten JSON → clean typed tables)
- Domain-grouped folder structure: teams/, fixtures/, players/, transfers/
- Full column extraction — public dataset philosophy (keep everything)

### ✅ LATEST IMPLEMENTATION UPDATE (February 18, 2026)

- **Phase 1 (foundation) complete**
  - Added dbt source definitions: `models/sources/raw_sources.yml`
  - Added staging contracts/tests: `models/staging/staging_schema.yml`
- **Phase 2 complete**
  - Implemented: `stg_teams`, `stg_player_leaderboards`
- **Phase 3 implemented**
  - Implemented fixture core: `stg_fixtures`, `stg_rounds`, `stg_match_events`
  - Implemented fixture deep: `stg_match_player_stats`, `stg_predictions`
  - Implemented team/player/availability: `stg_team_standings`, `stg_team_statistics`, `stg_player_season_stats`, `stg_squad_players`, `stg_transfers`, `stg_injuries`
  - Existing implemented models retained: `stg_teams`, `stg_player_leaderboards`, `stg_match_team_stats`, `stg_lineup_players`
  - All staging models use dedup by latest `raw:entity_key` + `_loaded_at`, explicit casts, and lineage columns.
- **Critical fixture key fix applied**
  - For `raw_fixtures_statistics` and `raw_fixtures_lineups`, `fixture_id` is extracted from:
    - `raw:params:fixture::INT`
  - Reason: these endpoint response rows do not reliably include `fixture.id` inside each `payload.response` object.

### ⬜ TODO — Gold Layer (dbt Marts)

- Fact and dimension tables for analytics
- AI agent integration

---

## Data Source: API-Football v3

- **League ID:** 307 (Saudi Pro League)
- **Season:** 2025
- **Base URL:** `https://v3.football.api-sports.io`

### 18 Endpoints Extracted

| # | Endpoint | Scope | Raw Rows | Nested Records | Description |
|---|----------|-------|----------|----------------|-------------|
| 1 | `/fixtures` | League | 1 | 306 | All season fixtures & scores |
| 2 | `/teams` | League | 1 | 18 | SPL team profiles & venues |
| 3 | `/standings` | League | 1 | 18 | League table (18 teams nested) |
| 4 | `/fixtures/rounds` | League | 1 | 34 | Matchday/round names |
| 5 | `/players` | League | 34 | 666 | Paginated player season stats (20/page) |
| 6 | `/players/topscorers` | League | 1 | 20 | Top goal scorers |
| 7 | `/players/topassists` | League | 1 | 20 | Top assist providers |
| 8 | `/players/topyellowcards` | League | 1 | 20 | Most yellow cards |
| 9 | `/players/topredcards` | League | 1 | 20 | Most red cards |
| 10 | `/teams/statistics` | Per team | 18 | 18 (1:1) | Aggregated team season stats |
| 11 | `/injuries` | Per team | 18 | 2 total | Player injuries & suspensions |
| 12 | `/transfers` | Per team | 18 | 2,573 | Transfer records |
| 13 | `/players/squads` | Per team | 18 | 558 | Current roster per team |
| 14 | `/fixtures/statistics` | Per fixture | 189 | 376 | Match stats — long format (18 stat types × 2 teams) |
| 15 | `/fixtures/events` | Per fixture | 189 | 3,090 | Goals, cards, substitutions |
| 16 | `/fixtures/lineups` | Per fixture | 190* | 7,514 | Formations, starters, bench |
| 17 | `/fixtures/players` | Per fixture | 189 | 7,476 | Per-player match performance |
| 18 | `/predictions` | Per fixture | 189 | 189 (1:1) | Pre-match win predictions |

*190 rows due to 1 accidental duplicate from a double pipeline run — handled via dedup in staging.

**Total staging rows (estimated): ~23,000+**

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

| Setting     | Value                |
|-------------|----------------------|
| Database    | `LEAGUES_DATA`       |
| Schema      | `RAW`                |
| Warehouse   | (user-specific)      |
| Stage       | `LEAGUES_STAGE`      |
| File Format | `json_raw`           |
| Auth        | Access keys (no IAM role) |

### Stage Configuration
```sql
-- Stage points to bucket root, uses credentials (no IAM role)
CREATE STAGE LEAGUES_STAGE
  URL = 's3://leagues-datalake/'
  CREDENTIALS = (AWS_KEY_ID = '...' AWS_SECRET_KEY = '...')
  FILE_FORMAT = json_raw;
```

### 18 RAW Tables — Shared Schema
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

---

## Discovery Findings

Full data discovery was completed on all 18 RAW tables before building the staging layer.

### Data Quality Issues Found

| Issue | Table | Detail | Action |
|-------|-------|--------|--------|
| Wrong country | `raw_teams` | Al Khaleej Saihat → country = "United-Arab-Emirates" (should be Saudi-Arabia) | Pass through in staging. Fix in Gold. |
| Duplicate row | `raw_fixtures_lineups` | fixture=1435971 appears twice (two pipeline runs 10 min apart on same day) | Dedup via QUALIFY in staging |
| Round out of order | `raw_fixtures_rounds` | Round 10 appears after round 23 in array | Extract round number with REGEXP_SUBSTR for numeric sort |
| String-typed stats | `raw_fixtures_statistics` | All stat values stored as VARCHAR (e.g. "66%", "12") — sorts alphabetically not numerically | Cast to INT/FLOAT in staging |

### Duplication Check Results

| Table | Total Rows | Unique Fixtures | Duplicates |
|-------|-----------|-----------------|------------|
| raw_fixtures_events | 189 | 189 | 0 ✅ |
| raw_fixtures_lineups | 190 | 189 | 1 ⚠️ |
| raw_fixtures_players | 189 | 189 | 0 ✅ |
| raw_fixtures_statistics | 189 | 189 | 0 ✅ |
| raw_predictions | 189 | 189 | 0 ✅ |

### Referential Integrity Check
Cross-join between raw_fixtures (team IDs) and raw_teams → **zero orphan records**. All teams in fixtures exist in teams table. All teams have played at least one match. ✅

### Fixture Statistics — 18 Stat Types (Long Format)

`raw_fixtures_statistics` stores one row per stat per team per fixture (long format). All 18 types appear exactly 376 times (189 fixtures × 2 teams):

| Stat Type | Format | Cast Strategy |
|-----------|--------|---------------|
| Ball Possession | String with % | `REPLACE('%','')::FLOAT` |
| Passes % | String with % | `REPLACE('%','')::FLOAT` |
| expected_goals | Decimal string | `::FLOAT` |
| goals_prevented | Decimal (can be negative) | `::FLOAT` |
| Total Shots, Shots on Goal, Shots off Goal | Integer string | `::INT` |
| Blocked Shots, Shots insidebox, Shots outsidebox | Integer string | `::INT` |
| Corner Kicks, Offsides, Fouls | Integer string | `::INT` |
| Yellow Cards, Red Cards | Integer string | `::INT` |
| Goalkeeper Saves, Passes accurate, Total passes | Integer string | `::INT` |

Staging will **PIVOT** this long format into wide format (1 row per team per fixture, 18 columns).

### Leaderboard Tables — Identical Structure
All 4 leaderboard tables (topscorers, topassists, topyellowcards, topredcards) share identical JSON structure. Will be combined into **one staging table** `stg_player_leaderboards` with a `ranking_type` column.

---

## Staging Layer Design

### Philosophy
- **Full fidelity** — extract every available column from source JSON
- **No business logic** — pass values exactly as API returned them
- **No value corrections** — known issues passed through, fixed in Gold
- **Typed columns** — proper INT, FLOAT, VARCHAR, TIMESTAMP, BOOLEAN casts
- **One row per logical entity** — one fixture, one player, one event per row
- **Deduplicated** — always take latest `_loaded_at` for duplicate entity_keys
- **Public dataset** — designed for external consumers, not just the AI agent

### Deduplication Pattern (applied to ALL staging models)
```sql
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY raw:entity_key::VARCHAR
    ORDER BY _loaded_at DESC
) = 1
```

### 15 Staging Tables

| Staging Table | Source RAW Table(s) | Est. Rows | Transform Pattern |
|---------------|---------------------|-----------|-------------------|
| `stg_teams` | raw_teams | 18 | Simple FLATTEN |
| `stg_team_standings` | raw_standings | 18 | Simple FLATTEN |
| `stg_team_statistics` | raw_teams_statistics | 18 | Deep JSON nav (no FLATTEN) |
| `stg_fixtures` | raw_fixtures | 306 | Simple FLATTEN |
| `stg_rounds` | raw_fixtures_rounds | 34 | Array FLATTEN + round number extract |
| `stg_match_events` | raw_fixtures_events | 3,090 | FLATTEN + dedup |
| `stg_match_team_stats` | raw_fixtures_statistics | 376 | FLATTEN + PIVOT to wide + dedup |
| `stg_match_player_stats` | raw_fixtures_players | 7,476 | Double FLATTEN + dedup |
| `stg_lineup_players` | raw_fixtures_lineups | 7,514 | Double FLATTEN (startXI + subs) + dedup |
| `stg_predictions` | raw_predictions | 189 | Deep JSON nav (no FLATTEN) |
| `stg_player_season_stats` | raw_players | 666 | Double FLATTEN |
| `stg_player_leaderboards` | raw_players_top* (4 tables) | 80 | FLATTEN + UNION ALL + ranking_type |
| `stg_squad_players` | raw_players_squads | 558 | Double FLATTEN |
| `stg_transfers` | raw_transfers | 2,573 | Simple FLATTEN |
| `stg_injuries` | raw_injuries | 2 | Simple FLATTEN |

### dbt Folder Structure (Domain-Grouped)
```
leagues_data/models/staging/
├── teams/
│   ├── stg_teams.sql
│   ├── stg_team_standings.sql
│   └── stg_team_statistics.sql
├── fixtures/
│   ├── stg_fixtures.sql
│   ├── stg_rounds.sql
│   ├── stg_match_events.sql
│   ├── stg_match_team_stats.sql
│   ├── stg_match_player_stats.sql
│   ├── stg_lineup_players.sql
│   └── stg_predictions.sql
├── players/
│   ├── stg_player_season_stats.sql
│   ├── stg_player_leaderboards.sql
│   └── stg_squad_players.sql
└── transfers/
    ├── stg_transfers.sql
    └── stg_injuries.sql
```

### Key SQL Patterns

**Pattern 1: Simple FLATTEN**
```sql
WITH source AS (
    SELECT raw:payload:response AS arr, _loaded_at
    FROM {{ source('raw', 'raw_teams') }}
    QUALIFY ROW_NUMBER() OVER (PARTITION BY raw:entity_key::VARCHAR ORDER BY _loaded_at DESC) = 1
),
flattened AS (
    SELECT t.value:team:id::INT AS team_id, ...
    FROM source, LATERAL FLATTEN(input => arr) t
)
SELECT * FROM flattened
```

**Pattern 2: Double FLATTEN (lineups — startXI + substitutes)**
```sql
LATERAL FLATTEN(input => raw:payload:response) team,
LATERAL FLATTEN(input => ARRAY_CAT(team.value:startXI, team.value:substitutes)) player
```

**Pattern 2a: Fixture ID extraction for fixture-level endpoints**
```sql
raw:params:fixture::INT AS fixture_id
```
Use this for `/fixtures/statistics` and `/fixtures/lineups` staging models.

**Pattern 3: PIVOT (match_team_stats — long → wide)**
```sql
SELECT
    fixture_id, team_id, team_name,
    MAX(CASE WHEN stat_type = 'Ball Possession'  THEN REPLACE(stat_value,'%','')::FLOAT END) AS ball_possession_pct,
    MAX(CASE WHEN stat_type = 'Total Shots'      THEN stat_value::INT END) AS total_shots,
    MAX(CASE WHEN stat_type = 'expected_goals'   THEN stat_value::FLOAT END) AS expected_goals,
    -- ... 15 more stat columns
GROUP BY fixture_id, team_id, team_name
```

**Pattern 4: UNION ALL (leaderboards — 4 tables → 1)**
```sql
(SELECT 'top_scorers'     AS ranking_type, ... FROM raw_players_topscorers ...)
UNION ALL
(SELECT 'top_assists'     AS ranking_type, ... FROM raw_players_topassists ...)
UNION ALL
(SELECT 'top_yellow_cards' AS ranking_type, ... FROM raw_players_topyellowcards ...)
UNION ALL
(SELECT 'top_red_cards'   AS ranking_type, ... FROM raw_players_topredcards ...)
```

---

## Pipeline Code Structure

```
src/pipeline/
├── api_client.py    — HTTP client for API-Football (retry, rate limiting)
├── config.py        — PipelineConfig (league_id, season, keys, etc.)
├── ingest.py        — Main ingestion logic (6 steps)
├── storage.py       — S3Writer (put_raw, put_marker, idempotency)
└── run_daily.py     — CLI entrypoint
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

## Next Steps — Stage 3 Execution Plan

| Step | Action | Priority |
|------|--------|----------|
| 1 | Run full staging build and tests: `dbt build -s staging` | HIGH |
| 2 | Resolve any remaining model-level data quality failures (null keys, uniqueness, accepted values) | HIGH |
| 3 | Capture Stage 3 evidence pack (row counts, duplicate checks, freshness snapshot) | HIGH |
| 4 | Validate schema target configuration in dbt profile/macro (`DEV`, `staging`, `DEV_STAGING`) | MEDIUM |
| 5 | Update governance docs and move Stage 4 to Current Stage once Stage 3 evidence is complete | MEDIUM |

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
python -m scripts.run_daily --date 2026-02-15
```

### Load New Data into Snowflake
Re-run the same COPY INTO statements — Snowflake auto-skips already-loaded files.

### Transform with dbt
```bash
cd leagues_data
dbt run
```

---

## Important Notes & Gotchas

- S3 credentials are used for Snowflake access — no IAM role configured
- The `state/` folder in S3 is for pipeline idempotency markers only — NOT loaded into Snowflake
- Part numbers in S3 filenames are a GLOBAL counter per run, not per endpoint
- `raw_standings` has 1 raw row but 18 teams nested inside — always FLATTEN before querying
- Season 2025 has 306 total fixtures — 189 finished as of Feb 15, 2026. Grows as season progresses
- All 4 leaderboard tables are identical in structure — combined into one staging table
- Stat values in `raw_fixtures_statistics` are VARCHAR strings — must cast explicitly
- **Snowflake QUALIFY + GROUP BY** — QUALIFY cannot be used in same SELECT as GROUP BY. Use subquery pattern instead
- **Snowflake UNION ALL** — requires parentheses around each SELECT block when using ORDER BY + LIMIT per block
- `raw_fixtures_lineups` has one extra row (190 vs 189) — accidental duplicate from double pipeline run, handled by dedup pattern
