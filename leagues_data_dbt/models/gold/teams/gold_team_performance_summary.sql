{{ config(materialized='table') }}

WITH finished_team_fixtures AS (
    SELECT
        league_id,
        season,
        fixture_id,
        home_team_id as team_id,
        home_goals as goals_for,
        away_goals as goals_against,
        CASE
            WHEN home_goals > away_goals THEN 'W'
            WHEN home_goals = away_goals THEN 'D'
            ELSE 'L'
        END as match_result,
        'HOME' as venue_bucket
    FROM {{ ref('silver_fixture') }}
    WHERE status_short IN ('FT', 'AET', 'PEN')

    UNION ALL

    SELECT
        league_id,
        season,
        fixture_id,
        away_team_id as team_id,
        away_goals as goals_for,
        home_goals as goals_against,
        CASE
            WHEN away_goals > home_goals THEN 'W'
            WHEN away_goals = home_goals THEN 'D'
            ELSE 'L'
        END as match_result,
        'AWAY' as venue_bucket
    FROM {{ ref('silver_fixture') }}
    WHERE status_short IN ('FT', 'AET', 'PEN')
),

fixture_record AS (
    SELECT
        team_id,
        league_id,
        season,
        COUNT(*) as matches_played,
        SUM(CASE WHEN match_result = 'W' THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN match_result = 'D' THEN 1 ELSE 0 END) as draws,
        SUM(CASE WHEN match_result = 'L' THEN 1 ELSE 0 END) as losses,
        SUM(goals_for) - SUM(goals_against) as goals_diff,
        SUM(CASE WHEN match_result = 'W' THEN 3 WHEN match_result = 'D' THEN 1 ELSE 0 END) as points,
        SUM(CASE WHEN venue_bucket = 'HOME' AND match_result = 'W' THEN 1 ELSE 0 END) as home_win,
        SUM(CASE WHEN venue_bucket = 'HOME' AND match_result = 'D' THEN 1 ELSE 0 END) as home_draw,
        SUM(CASE WHEN venue_bucket = 'HOME' AND match_result = 'L' THEN 1 ELSE 0 END) as home_lose,
        SUM(CASE WHEN venue_bucket = 'HOME' THEN goals_for ELSE 0 END) as home_goals_for,
        SUM(CASE WHEN venue_bucket = 'HOME' THEN goals_against ELSE 0 END) as home_goals_against,
        SUM(CASE WHEN venue_bucket = 'AWAY' AND match_result = 'W' THEN 1 ELSE 0 END) as away_win,
        SUM(CASE WHEN venue_bucket = 'AWAY' AND match_result = 'D' THEN 1 ELSE 0 END) as away_draw,
        SUM(CASE WHEN venue_bucket = 'AWAY' AND match_result = 'L' THEN 1 ELSE 0 END) as away_lose,
        SUM(CASE WHEN venue_bucket = 'AWAY' THEN goals_for ELSE 0 END) as away_goals_for,
        SUM(CASE WHEN venue_bucket = 'AWAY' THEN goals_against ELSE 0 END) as away_goals_against
    FROM finished_team_fixtures
    GROUP BY team_id, league_id, season
),

team_base_pre_rank AS (
    SELECT
        t.team_id,
        t.team_name,
        r.country,
        t.standing_rank as standing_rank_snapshot,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.points
            ELSE t.points
        END as points,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.matches_played
            ELSE t.all_played
        END as matches_played,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.wins
            ELSE t.all_win
        END as wins,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.draws
            ELSE t.all_draw
        END as draws,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.losses
            ELSE t.all_lose
        END as losses,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.goals_diff
            ELSE t.goals_diff
        END as goals_diff,
        t.last_5_form,
        t.season_form,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.home_win
            ELSE t.home_win
        END as home_win,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.home_draw
            ELSE t.home_draw
        END as home_draw,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.home_lose
            ELSE t.home_lose
        END as home_lose,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.home_goals_for
            ELSE t.home_goals_for
        END as home_goals_for,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.home_goals_against
            ELSE t.home_goals_against
        END as home_goals_against,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.away_win
            ELSE t.away_win
        END as away_win,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.away_draw
            ELSE t.away_draw
        END as away_draw,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.away_lose
            ELSE t.away_lose
        END as away_lose,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.away_goals_for
            ELSE t.away_goals_for
        END as away_goals_for,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN fr.away_goals_against
            ELSE t.away_goals_against
        END as away_goals_against,
        t.clean_sheets_total,
        t.failed_to_score_total,
        t.league_id,
        t.season,
        CASE
            WHEN COALESCE(fr.matches_played, 0) > COALESCE(t.all_played, 0) THEN TRUE
            ELSE FALSE
        END as using_fixture_record

    FROM {{ ref('silver_teams') }} t
    LEFT JOIN {{ source('gold', 'ref_leagues') }} r ON t.league_id = r.league_id
    LEFT JOIN fixture_record fr
        ON t.team_id = fr.team_id
       AND t.league_id = fr.league_id
       AND t.season = fr.season
),

team_base AS (
    SELECT
        p.team_id,
        p.team_name,
        p.country,
        CASE
            WHEN MAX(CASE WHEN p.using_fixture_record THEN 1 ELSE 0 END) OVER (PARTITION BY p.league_id, p.season) = 1 THEN DENSE_RANK() OVER (
                PARTITION BY p.league_id, p.season
                ORDER BY p.points DESC, p.goals_diff DESC, (p.home_goals_for + p.away_goals_for) DESC, p.team_name
            )
            ELSE p.standing_rank_snapshot
        END as standing_rank,
        p.points,
        p.matches_played,
        p.wins,
        p.draws,
        p.losses,
        p.goals_diff,
        p.last_5_form,
        p.season_form,
        p.home_win,
        p.home_draw,
        p.home_lose,
        p.home_goals_for,
        p.home_goals_against,
        p.away_win,
        p.away_draw,
        p.away_lose,
        p.away_goals_for,
        p.away_goals_against,
        p.clean_sheets_total,
        p.failed_to_score_total,
        p.league_id,
        p.season
    FROM team_base_pre_rank p
),

scoring AS (
    SELECT
        team_id,
        league_id,
        season,
        goals_scored,
        open_play_goals,
        penalty_goals,
        penalty_goal_ratio,
        goals_per_match,
        early_goals,
        mid_goals,
        late_goals,
        stoppage_goals
    FROM {{ ref('gold_team_scoring_profile') }}
),

discipline AS (
    SELECT
        team_id,
        league_id,
        season,
        total_cards,
        cards_per_match,
        yellow_card_rate,
        red_card_rate,
        stoppage_red_rate,
        early_reds,
        late_reds,
        stoppage_reds
    FROM {{ ref('gold_team_discipline_profile') }}
)

SELECT
    b.*,
    COALESCE(s.goals_scored, 0)       as goals_scored,
    COALESCE(s.open_play_goals, 0)    as open_play_goals,
    COALESCE(s.penalty_goals, 0)      as penalty_goals,
    COALESCE(s.penalty_goal_ratio, 0) as penalty_goal_ratio,
    COALESCE(s.goals_per_match, 0)    as goals_per_match,
    COALESCE(s.early_goals, 0)        as early_goals,
    COALESCE(s.mid_goals, 0)          as mid_goals,
    COALESCE(s.late_goals, 0)         as late_goals,
    COALESCE(s.stoppage_goals, 0)     as stoppage_goals,
    COALESCE(d.total_cards, 0)        as total_cards,
    COALESCE(d.cards_per_match, 0)    as cards_per_match,
    COALESCE(d.yellow_card_rate, 0)   as yellow_card_rate,
    COALESCE(d.red_card_rate, 0)      as red_card_rate,
    COALESCE(d.stoppage_red_rate, 0)  as stoppage_red_rate,
    COALESCE(d.early_reds, 0)         as early_reds,
    COALESCE(d.late_reds, 0)          as late_reds,
    COALESCE(d.stoppage_reds, 0)      as stoppage_reds

FROM team_base b
LEFT JOIN scoring s    ON b.team_id = s.team_id AND b.league_id = s.league_id AND b.season = s.season
LEFT JOIN discipline d ON b.team_id = d.team_id AND b.league_id = d.league_id AND b.season = d.season
ORDER BY b.standing_rank
