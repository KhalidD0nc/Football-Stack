# Data Engineering Implementation Checklist

## Scope
This checklist is for **Data Engineering execution only**.

## Stage Governance
Keep only:
- `Current Stage`
- `Next Stage`

On each stage transition:
1. Move `Next Stage` to `Current Stage`
2. Define a new `Next Stage`
3. Update:
- `docs/Data Engineering Architecture and Plan.md`
- `docs/Data Engineering Implementation Checklist.md`
- `README.md`

## Stage 2 - Bronze Expansion for Club + Player Data (Completed)
### Why
- Stage 2 is required to support FBref-like outputs and AI coaching data needs.
- Thin-slice endpoints alone are not enough for club intelligence and player intelligence coverage.

### Goals
- Expand Bronze endpoint coverage for club-side and player-side datasets.
- Add pagination-safe player ingestion.
- Add endpoint-level visibility in run outputs.

### Checklist
- [x] Add club-side endpoint ingestion family (`/standings`, `/teams`, `/teams/statistics`, `/fixtures/rounds`, `/injuries`, `/transfers`).
- [x] Add player-side endpoint ingestion family (`/players`, `/players/squads`, `/players/topscorers`, `/players/topassists`, `/players/topyellowcards`, `/players/topredcards`).
- [x] Add `/fixtures/lineups` to match-detail ingestion.
- [x] Add `/predictions` to match-detail ingestion.
- [x] Expand match-detail ingestion scope to all finished fixtures in the league season.
- [x] Implement and verify deterministic pagination for `/players`.
- [x] Define and apply snapshot cadence for non-production exploration runs.
- [x] Add per-endpoint run counters and failure visibility to run summary.
- [x] Validate partition consistency and idempotent marker behavior in non-production runs.

### Run Evidence (Non-Production)
- Example run: `python -m scripts.run_daily` on `2026-02-15`
- Summary:
  - `fixtures_total=306`
  - `teams_total=18`
  - `players_pages_fetched=34`
  - `api_calls=114`
  - `api_failures=0`
  - `endpoint_failures=0`
  - `raw_files=114`
  - `skipped_idempotent=0`

## Current Stage: Stage 3 - Silver Modeling and Normalization (In Progress)
### Why
- Bronze data is now sufficient for exploration, but not convenient for analytics or website serving.
- Silver creates stable, normalized entities and facts for consistent downstream use.

### Goals
- Build deterministic normalization from Bronze to Silver.
- Standardize keys and types across team/player/fixture entities.
- Add Silver-level quality checks.

### Checklist
- [x] Define Silver schema contracts (`stg_teams`, `stg_player_leaderboards`, `stg_match_team_stats`, `stg_lineup_players`).
- [x] Implement Bronze-to-Silver normalization transforms (Staging models).
- [x] Enforce primary/business key uniqueness and dedup logic (dbt tests).
- [ ] Implement core dimension tables (`dim_team`, `dim_player`, `dim_fixture`).
- [ ] Implement core fact tables (`fact_team_match`, `fact_player_match`).
- [ ] Validate referential integrity across fixture/team/player keys.
- [ ] Add freshness and null-key checks for all Silver outputs.
- [ ] Publish initial Silver run summary and sample row counts.

## Next Stage: Stage 4 - Gold Marts and Analytics
### Why
- Silver entities are normalized but require complex joins for business questions.
- Gold marts provide user-ready data for the AI Coaching System and front-end displays.

### Goals
- Aggregate Silver facts into performance-oriented marts.
- Implement business-focused KPIs (e.g., xG contribution, player form trends).
- Ensure data is optimized for high-performance retrieval.

### Checklist
- [ ] Define Gold schema for Team Performance Mart.
- [ ] Define Gold schema for Player Scouting Mart.
- [ ] Implement aggregation logic for seasonal and rolling stats.
- [ ] Add business-logic validation tests.
- [ ] Create documentation for downstream consumers.
