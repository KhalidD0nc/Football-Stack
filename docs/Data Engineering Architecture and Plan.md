# Data Engineering Architecture Plan

## Scope
This project scope is **Data Engineering only**.

In-scope:
- Source ingestion
- Data lake storage design
- Data contracts and quality checks
- Curated data marts for downstream consumers

Out-of-scope:
- Model training
- Frontend/dashboard implementation
- Coaching recommendation logic

## Stage Governance
At any point, keep only:
- `Current Stage`: what we are actively executing now
- `Next Stage`: what starts immediately after current is complete

Update rule for every stage transition:
1. Move `Next Stage` into `Current Stage`
2. Define a new `Next Stage`
3. Update this file, `docs/Data Engineering Implementation Checklist.md`, and `README.md` in the same commit

## Architecture (Current + Next)

### Stage 2 - Bronze Expansion for Club + Player Data (Completed)
Goal:
- Capture enough SPL + Al Hilal Bronze data for exploration and downstream model design.

Architecture focus:
- **Source**: API-Football
- **Ingestion**: Python batch job (`scripts/run_daily.py` -> `src/pipeline/ingest.py`)
- **Storage**:
  - Raw payloads under `raw/source=api_football/...`
  - Idempotency markers under `state/source=api_football/...`
- **Reliability**:
  - Retry/backoff for transient API failures
  - Rate limiting
  - Idempotent reruns

Current endpoint coverage:
- League baseline:
  - `/fixtures`, `/teams`, `/standings`, `/fixtures/rounds`
  - `/players` (paginated), `/players/topscorers`, `/players/topassists`, `/players/topyellowcards`, `/players/topredcards`
- Team snapshots (all SPL teams):
  - `/teams/statistics`, `/injuries`, `/transfers`, `/players/squads`
- Team deep details (all finished league fixtures in season):
  - `/fixtures/statistics`, `/fixtures/events`, `/fixtures/lineups`, `/fixtures/players`, `/predictions`

Exit criteria:
- Bronze coverage is sufficient for non-production analytics exploration.
- Run summaries confirm successful endpoint coverage with no critical failures.
- Reruns remain idempotent via state markers.

### Current Stage: Stage 3 - Silver Modeling and Normalization (In Progress)
Goal:
- Transform Bronze payloads into normalized, queryable Silver entities.

Architecture focus:
- Keep Bronze immutable and append-only.
- Build deterministic normalization jobs into shared entities/facts.
- Introduce key quality checks on normalized tables (Schema contracts).

Current Silver entities (Staging):
- Teams:
  - `stg_teams`, `stg_team_standings`, `stg_team_statistics`
- Fixtures:
  - `stg_fixtures`, `stg_rounds`, `stg_match_events`, `stg_match_team_stats`, `stg_match_player_stats`, `stg_lineup_players`, `stg_predictions`
- Players:
  - `stg_player_season_stats`, `stg_player_leaderboards`, `stg_squad_players`
- Transfers/availability:
  - `stg_transfers`, `stg_injuries`

Exit criteria:
- All 15 staging entities load deterministically from Bronze.
- Staging quality checks pass (null keys, uniqueness, accepted values, key relationships).
- Stage 3 evidence pack is published (row counts, duplicate checks, freshness snapshot).

### Next Stage: Stage 4 - Gold Marts and Analytics
Goal:
- Build curated, business-level entities for analytics and downstream applications.

Architecture focus:
- Aggregate Silver facts into performance metrics.
- Implement specialized marts (e.g., Playing Styles, Player Comparison).
- Finalize automated quality and freshness reporting.

Exit criteria:
- Gold models provide stable interfaces for the AI Coaching System.
- Data lineage is fully documented and verifiable.

## Implementation Tracking
Implementation checklists, with explicit `Why` and `Goals` for each stage, are in:
- `docs/Data Engineering Implementation Checklist.md`
