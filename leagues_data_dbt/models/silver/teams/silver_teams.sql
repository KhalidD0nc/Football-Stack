{{config(materialized='table')}}

WITH teams AS (
    SELECT * FROM {{ ref('stg_teams') }}
),
standings AS (
    SELECT * FROM {{ ref('stg_team_standings') }}
),
statistics AS (
    SELECT * FROM {{ ref('stg_team_statistics') }}
)

SELECT
    -- Identity
    t.team_id,
    t.team_name,
    t.team_code,
    t.country,
    t.founded,
    t.is_national_team,
    t.team_logo_url,
    t.league_id,
    t.season,

    -- Venue
    t.venue_id,
    t.venue_name,
    t.venue_address,
    t.venue_city,
    t.venue_capacity,
    t.venue_surface,
    t.venue_image_url,

    -- Standings
    ts.standing_rank,
    ts.standing_group,
    ts.standing_status,
    ts.standing_description,
    ts.points,
    ts.goals_diff,
    ts.recent_form                  AS last_5_form,
    ts.all_played,
    ts.all_win,
    ts.all_draw,
    ts.all_lose,
    ts.all_goals_for,
    ts.all_goals_against,
    ts.home_played,
    ts.home_win,
    ts.home_draw,
    ts.home_lose,
    ts.home_goals_for,
    ts.home_goals_against,
    ts.away_played,
    ts.away_win,
    ts.away_draw,
    ts.away_lose,
    ts.away_goals_for,
    ts.away_goals_against,

    -- Season statistics
    tst.recent_form                 AS season_form,
    tst.clean_sheets_home,
    tst.clean_sheets_away,
    tst.clean_sheets_total,
    tst.failed_to_score_home,
    tst.failed_to_score_away,
    tst.failed_to_score_total,
    tst.biggest_streak_wins,
    tst.biggest_streak_draws,
    tst.biggest_streak_loses,
    tst.biggest_win_home,
    tst.biggest_win_away,
    tst.biggest_loss_home,
    tst.biggest_loss_away,
    tst.biggest_goals_for_home,
    tst.biggest_goals_for_away,
    tst.biggest_goals_against_home,
    tst.biggest_goals_against_away,
    tst.goals_for_avg_home,
    tst.goals_for_avg_away,
    tst.goals_for_avg_total,
    tst.goals_against_avg_home,
    tst.goals_against_avg_away,
    tst.goals_against_avg_total

FROM teams t
LEFT JOIN standings ts
    ON t.team_id = ts.team_id
   AND t.league_id = ts.league_id
   AND t.season = ts.season
LEFT JOIN statistics tst
    ON t.team_id = tst.team_id
   AND t.league_id = tst.league_id
   AND t.season = tst.season
