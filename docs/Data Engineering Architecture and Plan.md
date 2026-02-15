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

### Current Stage: Stage 2 - Bronze Expansion for Club + Player Data (Non-Production Complete)
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
- Team deep details (configured team on run date):
  - `/fixtures/statistics` (finished fixtures), `/fixtures/events`, `/fixtures/lineups`, `/fixtures/players`, `/predictions`

Exit criteria:
- Bronze coverage is sufficient for non-production analytics exploration.
- Run summaries confirm successful endpoint coverage with no critical failures.
- Reruns remain idempotent via state markers.

### Next Stage: Stage 3 - Silver Modeling and Normalization
Goal:
- Transform Bronze payloads into normalized, queryable Silver entities.

Architecture focus:
- Keep Bronze immutable and append-only.
- Build deterministic normalization jobs into shared entities/facts.
- Introduce key quality checks on normalized tables.

Next-stage core Silver entities:
- `dim_team`, `dim_player`, `dim_fixture`
- `fact_team_match`, `fact_player_match`
- `fact_match_events`, `fact_lineups`
- `fact_injuries`, `fact_transfers`

Exit criteria:
- Silver entities load deterministically from Bronze.
- Referential integrity and duplicate checks pass.
- Silver outputs support first Gold mart definitions.

## Implementation Tracking
Implementation checklists, with explicit `Why` and `Goals` for each stage, are in:
- `docs/Data Engineering Implementation Checklist.md`
