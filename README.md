# Leagues Data Project

## Scope
This repository is for **Data Engineering only**.

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
**Stage 2 - Bronze Expansion for Club + Player Data (Completed)**
- Bronze endpoint expansion implemented for league baseline + team deep details
- Non-production run evidence captured in checklist document
- Bronze data collection is sufficient for exploration/design work

## Next Stage
**Stage 3 - Silver Modeling and Normalization**
- Define and implement normalized Silver entities/facts from Bronze payloads
- Add Silver-level data quality checks
- Prepare Silver outputs for first Gold mart design

## Features
- **Idempotency**: All ingestion steps use S3 marker files to prevent duplicate API calls and ensure safe re-runs.
- **Resilience**: The API client includes exponential backoff retry logic and rate limiting to handle transient failures gracefully.
- **Observability**: Detailed run summary metrics (API calls, failures, writes) are logged at the end of each ingestion run.

## Quick Start
To run the daily ingestion script:

```bash
python -m scripts.run_daily
```

By default, this will run for the current date. You can also specify a date:

```bash
python -m scripts.run_daily
```

## Testing
To run the project's test suite:

```bash
pytest tests/
```

## Transformation Layer
The project includes a dbt project located in `leagues_data` for data transformation and quality testing.

### Features
- **Silver/Gold Modeling**: (Future scope) logic to normalize Bronze data into Silver/Gold layers.
- **Data Quality**: dbt tests ensure data integrity and schema compliance.

### Quick Start
To run the dbt project:

```bash
cd leagues_data
dbt deps
dbt run
```

To run tests:

```bash
cd leagues_data
dbt test
```

## Primary Documents
Architecture plan:
- `docs/Data Engineering Architecture and Plan.md`
Implementation checklist (with `Why` and `Goals` per stage):
- `docs/Data Engineering Implementation Checklist.md`
