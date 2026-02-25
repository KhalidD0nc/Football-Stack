CREATE TABLE IF NOT EXISTS raw_teams (
    raw VARIANT NOT NULL, league_id INT, season INT, dt DATE, run_id VARCHAR, _file_name VARCHAR, _loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
