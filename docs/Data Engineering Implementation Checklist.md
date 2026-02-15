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

## Current Stage: Stage 2 - Bronze Expansion for Club + Player Data (Non-Production Complete)
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

## Next Stage: Stage 3 - Silver Modeling and Normalization
### Why
- Bronze data is now sufficient for exploration, but not convenient for analytics or website serving.
- Silver creates stable, normalized entities and facts for consistent downstream use.

### Goals
- Build deterministic normalization from Bronze to Silver.
- Standardize keys and types across team/player/fixture entities.
- Add Silver-level quality checks.

### Checklist
- [ ] Define Silver schema contracts (`dim_team`, `dim_player`, `dim_fixture`, `fact_*` tables).
- [ ] Implement Bronze-to-Silver normalization transforms.
- [ ] Enforce primary/business key uniqueness and dedup logic.
- [ ] Validate referential integrity across fixture/team/player keys.
- [ ] Add freshness, null-key, and duplicate checks for Silver outputs.
- [ ] Publish initial Silver run summary and sample row counts.
