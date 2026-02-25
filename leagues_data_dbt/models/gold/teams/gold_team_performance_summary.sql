{{ config(materialized='table') }}

WITH team_base AS (
    SELECT
        t.team_id,
        t.team_name,
        r.country,

        -- Standings
        t.standing_rank,
        t.points,
        t.all_played         as matches_played,
        t.all_win            as wins,
        t.all_draw           as draws,
        t.all_lose           as losses,
        t.goals_diff,
        t.last_5_form,
        t.season_form,

        -- Home
        t.home_win,
        t.home_draw,
        t.home_lose,
        t.home_goals_for,
        t.home_goals_against,

        -- Away
        t.away_win,
        t.away_draw,
        t.away_lose,
        t.away_goals_for,
        t.away_goals_against,

        -- Availability
        t.clean_sheets_total,
        t.failed_to_score_total,
        t.league_id,
        t.season

    FROM {{ ref('silver_teams') }} t
    LEFT JOIN {{ source('gold', 'ref_leagues') }} r ON t.league_id = r.league_id
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