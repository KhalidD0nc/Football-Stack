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
**Stage 2 - Bronze Expansion for Club + Player Data (Non-Production Complete)**
- Bronze endpoint expansion implemented for league baseline + team deep details
- Non-production run evidence captured in checklist document
- Bronze data collection is sufficient for exploration/design work

## Next Stage
**Stage 3 - Silver Modeling and Normalization**
- Define and implement normalized Silver entities/facts from Bronze payloads
- Add Silver-level data quality checks
- Prepare Silver outputs for first Gold mart design

## Primary Documents
Architecture plan:
- `docs/Data Engineering Architecture and Plan.md`
Implementation checklist (with `Why` and `Goals` per stage):
- `docs/Data Engineering Implementation Checklist.md`
