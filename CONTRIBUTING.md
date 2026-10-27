# Contributing to Football-Stack

## Contribution scope

Contributions to league/season configuration, dbt models, tests, and documentation are welcome. The existing project policy asks contributors to open an issue before proposing ingestion-layer changes; preserve that discussion step for API fetching and ingestion logic.

## Branch workflow

```text
feature/* → development → staging → main
```

1. Branch from `development` for a focused change and open a pull request back to it.
2. Promote a tested candidate from `development` into `staging` through a pull request.
3. Validate against the intended resources, then promote `staging` into `main`.
4. Synchronize any direct hotfix to `main` back into the other two branches.

Branches organize source changes. Resource isolation, scheduling, branch protection, and approvals are configured separately.

## Local setup and checks

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -q

dbt parse --project-dir leagues_data_dbt --profiles-dir .github/dbt \
  --no-partial-parse --vars '{"enable_gold_layer": true, "enable_platinum_layer": true}'
```

The `.github/dbt` profile uses offline placeholders. For actual dbt execution, copy `leagues_data_dbt/profiles.yml.example` to the ignored `profiles.yml`, configure the intended Snowflake database, and run the modified models and their data tests. See the [dbt guide](leagues_data_dbt/README.md).

## Pull requests

- Explain the change and keep commits focused.
- Cover changed transformation behavior with relevant fixture/schema cases.
- Update setup and operational examples when flags or contracts change.
- State whether verification was offline or used live API/warehouse resources.
- Keep credentials, private keys, local data lakes, and real dbt profiles out of commits.
