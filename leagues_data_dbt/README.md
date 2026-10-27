# Football analytics models

This dbt project transforms Football-Stack's warehouse data into team, player, match, availability, transfer, and prediction models. The current SQL targets Snowflake.

| Layer | Role | Default |
| --- | --- | --- |
| Staging | Normalize inputs and select the latest curated source rows | Enabled |
| Silver | Reusable cleaned entities and event tables | Enabled |
| Gold | Team/player/match analytics and summary marts | Disabled |
| Platinum | Match intelligence, player profiles, form, and prediction evaluation | Disabled |

## Configure a profile

From the repository root:

```bash
python -m pip install 'dbt-snowflake>=1.9,<2'
cp leagues_data_dbt/profiles.yml.example leagues_data_dbt/profiles.yml
```

Fill the Snowflake variables in `.env`. dbt does not load that file automatically. Export those values into the shell before calling dbt directly, or invoke dbt through `python -m scripts.run_pipeline`, which loads the pipeline configuration first.

The example uses key-pair authentication. Keep `SNOWFLAKE_PRIVATE_KEY_PATH` outside the repository and use a role with the required database/schema permissions. The `test` target uses `SNOWFLAKE_DATABASE_TEST`.

## Run models

```bash
# From the repository root, with exported Snowflake environment variables
dbt debug --project-dir leagues_data_dbt --profiles-dir leagues_data_dbt

dbt build --project-dir leagues_data_dbt --profiles-dir leagues_data_dbt \
  --select staging silver

dbt build --project-dir leagues_data_dbt --profiles-dir leagues_data_dbt \
  --select gold platinum \
  --vars '{"enable_gold_layer": true, "enable_platinum_layer": true}'
```

The curated source tables must already be present from the Python loader. The default project variable is `use_curated_parquet: true`; the models read these curated warehouse tables, not Parquet files directly.

For generated docs, use `dbt docs generate` and `dbt docs serve` with the same project/profile directory flags.

## Offline parsing

```bash
dbt parse --project-dir leagues_data_dbt --profiles-dir .github/dbt \
  --no-partial-parse --vars '{"enable_gold_layer": true, "enable_platinum_layer": true}'
```

Run this from the repository root. The placeholder CI profile is only for parsing; it is not a working warehouse connection. Parsing does not execute models or data tests.

## Environment isolation

The project's `generate_schema_name` macro preserves explicit model schema names. Separate databases/accounts provide the environment boundary; changing only the target schema does not isolate every layer. See the [architecture guide](../docs/ARCHITECTURE.md).
