{{ config(materialized='table') }}

WITH discipline_events AS (
    SELECT 
        e.team_id,
        e.team_name,
        e.fixture_id,
        e.event_detail,
        e.league_id,
        e.season,
        CASE 
            WHEN e.event_minute < 1 THEN 'Invalid'
            WHEN e.event_minute <= 30 THEN 'Early'
            WHEN e.event_minute <= 60 THEN 'Mid'
            WHEN e.event_minute <= 90 AND e.event_extra_minute IS NULL THEN 'Late'
            ELSE 'Stoppage'
        END as match_phase
    FROM {{ ref('silver_match_events') }} e
    WHERE e.event_type = 'Card'
        AND e.event_minute >= 1
),

team_info AS (
    SELECT 
        t.team_id,
        t.league_id,
        t.season,
        t.team_name,
        r.country,
        t.all_played as matches_played
    FROM {{ ref('silver_teams') }} t
    LEFT JOIN {{ source('gold', 'ref_leagues') }} r ON t.league_id = r.league_id
)

SELECT
    d.team_id,
    d.team_name,
    t.league_id,
    t.season,
    t.country,
    t.matches_played,

    -- Total cards
    COUNT(*)                                     as total_cards,
    ROUND(COUNT(*) * 1.0 / t.matches_played, 3)  as cards_per_match,

    -- Yellows by phase
    COUNT(CASE WHEN event_detail = 'Yellow Card' AND match_phase = 'Early'    THEN 1 END) as early_yellows,
    COUNT(CASE WHEN event_detail = 'Yellow Card' AND match_phase = 'Mid'      THEN 1 END) as mid_yellows,
    COUNT(CASE WHEN event_detail = 'Yellow Card' AND match_phase = 'Late'     THEN 1 END) as late_yellows,
    COUNT(CASE WHEN event_detail = 'Yellow Card' AND match_phase = 'Stoppage' THEN 1 END) as stoppage_yellows,

    -- Reds by phase
    COUNT(CASE WHEN event_detail = 'Red Card' AND match_phase = 'Early'    THEN 1 END) as early_reds,
    COUNT(CASE WHEN event_detail = 'Red Card' AND match_phase = 'Mid'      THEN 1 END) as mid_reds,
    COUNT(CASE WHEN event_detail = 'Red Card' AND match_phase = 'Late'     THEN 1 END) as late_reds,
    COUNT(CASE WHEN event_detail = 'Red Card' AND match_phase = 'Stoppage' THEN 1 END) as stoppage_reds,

    -- Key rates
    ROUND(COUNT(CASE WHEN event_detail = 'Red Card' AND match_phase = 'Stoppage' THEN 1 END) * 1.0 / t.matches_played, 3) as stoppage_red_rate,
    ROUND(COUNT(CASE WHEN event_detail = 'Red Card'    THEN 1 END) * 1.0 / t.matches_played, 3)                           as red_card_rate,
    ROUND(COUNT(CASE WHEN event_detail = 'Yellow Card' THEN 1 END) * 1.0 / t.matches_played, 3)                           as yellow_card_rate

FROM discipline_events d
JOIN team_info t ON d.team_id = t.team_id AND d.league_id = t.league_id AND d.season = t.season
GROUP BY d.team_id, d.team_name, t.league_id, t.season, t.country, t.matches_played
ORDER BY stoppage_red_rate DESC