# API‑Football v3 Endpoint Reference Guide

This reference guide summarizes the API‑Football v3 REST API. It lists each endpoint grouped by category, describes the request parameters (required vs. optional), provides high‑level response schemas with examples, notes pagination and rate limits, identifies the data covered and suggests common use cases. The guide is based on the API documentation and aims to serve as a quick integration reference.

## Authentication and Rate Limits

All endpoints require an x‑apisports‑key header containing your API key. The API supports only GET requests; additional request headers are not allowed[\[1\]](https://www.api-football.com/documentation-v3#:~:text=REQUESTS%20HEADERS%20%26%20CORS). Responses include headers x‑ratelimit‑requests‑limit and x‑ratelimit‑requests‑remaining (daily quota), plus X‑RateLimit‑Limit and X‑RateLimit‑Remaining (per‑minute quota)[\[2\]](https://www.api-football.com/documentation-v3#:~:text=Headers%20sent%20as%20response). Endpoints list recommended call frequencies; following them avoids being blocked for excessive requests.

## General Response Structure

Every endpoint returns a JSON object with a consistent top‑level schema:

{  
  "get": "endpoint-name",      // the endpoint path (string)  
  "parameters": { … },           // query parameters passed to the request  
  "errors": \[ … \],               // array of error messages (if any)  
  "results": n,                 // number of items returned  
  "paging": {                   // pagination information, if supported  
    "current": 1,  
    "total": 1  
  },  
  "response": \[ … \]             // list of response objects (structure depends on endpoint)  
}

## Endpoint Categories

### Timezone

| Endpoint | Description | Key parameters | Response | Update & use cases |
| :---- | :---- | :---- | :---- | :---- |
| **GET /timezone** | Returns a list of supported time‑zone identifiers. | None. | response is an array of strings (e.g., "Africa/Abidjan")[\[3\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=499). | Updated when time‑zones are added/changed. Use to build timezone pickers or convert dates in API requests. |

### Countries

| Endpoint | Description | Key parameters | Response | Update & use cases |
| :---- | :---- | :---- | :---- | :---- |
| **GET /countries** | Lists countries with football competitions. | Optional: name (string), code (alpha‑2 country code), search (partial name). | Each item includes name, code and flag URL[\[4\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Countries). | Updated when a new league from a new country is added (recommend 1 call/day). Useful for populating country selectors. |

### Leagues

| Endpoint | Description | Parameters (required/optional) | Response | Notes & use cases |
| :---- | :---- | :---- | :---- | :---- |
| **GET /leagues** | Returns leagues/cups with metadata and coverage. | Optional: id, name, country, code, season, team, type (league/cup), current (true/false), search (string), last (last *n* leagues)[\[5\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Update%20Frequency%20%3A%20This%20endpoint,updated%20several%20times%20a%20day). | Each result contains league (id, name, type, logo), country (name, code, flag) and seasons list with year and coverage flags[\[6\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2F%2F%20Allows%20to%20retrieve%20all,sports.io%2Fleagues%3Fid%3D39). | Updated several times a day; recommended 1 call/hour. Use to discover leagues, determine seasons and coverage options. |
| **GET /leagues/seasons** | Returns the list of available seasons across all leagues. | None. | response is an array of years (e.g., 2024). | Updated when a new season starts. Use to generate season dropdowns. |

### Teams

| Endpoint | Description | Parameters | Response highlights | Notes & use cases |
| :---- | :---- | :---- | :---- | :---- |
| **GET /teams** | Retrieves team information and stadium details. | At least one of: id, name, league & season, country, code, venue, search. Only one required when filtering by ID; for league‐based queries, both league and season should be provided[\[7\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=This%20endpoint%20requires%20at%20least,one%20parameter). | Each item has team (id, name, code, country, founded, national flag) and venue (id, name, address, city, country, capacity, surface, image)[\[8\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Updated multiple times per week; recommended 1 call/day. Use to display team rosters and stadium information. |
| **GET /teams/statistics** | Returns aggregated statistics for a team in a league/season. | Required: league, season, team. Optional: date (YYYY‑MM‑DD). | Response includes league and team metadata, form, fixture counts (played, wins, draws, losses), goals by match status and minute intervals, biggest wins/losses, clean\_sheet, failed\_to\_score and streaks[\[9\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Recommended%20Calls%20%3A%201%20call,otherwise%201%20call%20per%20week)[\[10\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Updated when the team plays; call daily or after matches. Use to build team dashboards, compare performance by home/away, etc. |
| **GET /teams/seasons** | Lists seasons available for a team. | Required: team ID. | response is an array of seasons[\[11\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=team). | Useful to determine valid seasons before requesting statistics. |
| **GET /teams/countries** | Lists countries represented in the teams endpoint. | None. | Each entry has name, code and flag[\[12\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Teams%20countries). | Helps build filters for team searches. |

### Venues

| Endpoint | Description | Parameters | Response | Notes |
| :---- | :---- | :---- | :---- | :---- |
| **GET /venues** | Lists stadiums/venues. | Optional: id (venue ID), name, city, country, search[\[13\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Recommended%20Calls%20%3A%201%20call,per%20day). | Each venue includes id, name, address, city, country, capacity, surface, and image[\[14\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Updated weekly; recommended 1 call/day. Use to display stadium info or map events to venues. |

### Standings

| Endpoint | Description | Parameters | Response highlights | Notes |
| :---- | :---- | :---- | :---- | :---- |
| **GET /standings** | Returns league table(s) for a season. | Required: league ID and season. Optional: team ID (to filter by team). | Response contains league metadata and standings – an array of groups where each row includes rank, team details, matches played, wins, draws, losses, goals for/against, goal difference, points, form, and promotion/relegation description[\[15\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=league)[\[16\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2F%2F%20Get%20all%20Standings%20from,sports.io%2Fstandings%3Fleague%3D39%26season%3D2019). | Updated hourly during matches and daily otherwise. Use to display current standings, group tables or team rankings. |

### Fixtures

The **Fixtures** category supplies schedules, match details and live data.

| Endpoint | Description | Key parameters | Response & notes | Suggested use |
| :---- | :---- | :---- | :---- | :---- |
| **GET /fixtures/rounds** | Lists rounds (matchdays) for a league/season. | Required: league ID & season. Optional: current (boolean), dates (string for date range), timezone[\[17\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=league). | Returns an array of round names (e.g., “Regular Season – 1”). | Updated daily; call daily to know current and upcoming rounds. |
| **GET /fixtures** | Retrieves fixtures with options for filtering and live updates. | Many optional parameters: id/ids (single or comma‑separated fixture IDs), live (e.g., all or comma‑separated fixture IDs), date, league, season, team, last, next, from, to, round, status, venue, timezone[\[18\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=id). | Each result contains fixture (id, referee, timezone, date, venue, status), league, teams (home/away), goals, and score (halftime, fulltime, extratime, penalty)[\[19\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2F%2F%20Get%20fixture%20from%20one,sports.io%2Ffixtures%3Fid%3D215662). | Real‑time; update frequency depends on match progress (call every minute during live matches). Use for schedules, live scores, match filtering. |
| **GET /fixtures/headtohead** | Returns fixtures and results between two teams. | Required: h2h (two team IDs separated by a hyphen). Optional: date, league, season, last, next, from, to, status, venue, timezone[\[20\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Head%20To%20Head). | Response structure is identical to /fixtures. | Call as needed to show historical head‑to‑head stats or upcoming meetings. |
| **GET /fixtures/statistics** | Returns match statistics. | Required: fixture. Optional: team (to filter statistics for a team), type (e.g., total, home, away), half (1 or 2\)[\[21\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=,Passes). | Response includes a list of statistics objects: each with team ID and statistics array of name/value pairs (e.g., shots, possession, fouls, etc.)[\[22\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Updated every minute during matches. Use to populate detailed match stats pages. |
| **GET /fixtures/events** | Lists events (goals, cards, substitutions). | Required: fixture. Optional: team, player, type (e.g., Goal, Card)[\[23\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=fixture). | Each event has time (elapsed & extra), team, player, assist, type, detail and comments[\[24\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2A%20). | Use for live event feeds or timeline visualizations. |
| **GET /fixtures/lineups** | Retrieves team lineups and formations. | Required: fixture. Optional: team, player, type (startXI, bench)[\[25\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=fixture). | Response contains each team’s formation, coach, jersey colors and an array of players with position coordinates[\[26\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Use to display starting XIs, bench lists and formations. |
| **GET /fixtures/players** | Returns detailed player statistics for a fixture. | Required: fixture. Optional: team[\[27\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=fixture). | Each team object has players array with rich stats: games (appearances, minutes, position), shots, goals, passes, tackles, duels, dribbles, fouls, cards, penalty[\[28\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2A%20,2284). | Use for player performance analysis and fantasy scoring. |

### Injuries

| Endpoint | Description | Parameters | Response & notes | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /injuries** | Lists players sidelined due to injury or suspension. | One of the following must be supplied: league & season, fixture, team, player, date, or ids. When using league, team or player, the season parameter is required[\[29\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Injuries). | Each entry includes player details, type (reason), team, fixture and league information[\[30\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=get%2Finjuries). | Updated every 4 hours; call daily. Useful for injury reports, fantasy sports and roster management. |

### Predictions

| Endpoint | Description | Parameters | Response highlights | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /predictions** | Provides match outcome predictions. | Required: fixture ID. | Returns predictions object including predicted winner, match winner probabilities, advice (e.g., “Home win or draw”), over/under goals prediction and comparison of team statistics[\[31\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Predictions)[\[32\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Updated hourly during live matches; call hourly when fixtures are in progress, otherwise once per day. Use for betting tips or pre‑match analysis. |

### Coachs (Coaches)

| Endpoint | Description | Parameters | Response | Notes |
| :---- | :---- | :---- | :---- | :---- |
| **GET /coachs** | Retrieves information on coaches and their careers. | Optional: id (coach ID), team (team ID), search (coach name)[\[33\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Get%20all%20the%20information%20about,the%20coachs%20and%20their%20careers). | Each coach object includes id, name, age, nationality, career history with teams and start/end dates[\[34\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Updated daily. Use to display coach bios or track coaching changes. |

### Players

The **Players** category contains numerous endpoints for seasons, profiles, statistics, squads, career history and leaderboards.

#### *Seasons*

| Endpoint | Description | Parameters | Response | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /players/seasons** | Lists seasons available for player statistics. | Optional: player (ID)[\[35\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Get%20all%20available%20seasons%20for,players%20statistics). | response is an array of seasons[\[36\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Use to determine valid seasons before requesting stats. |

#### *Profiles*

| Endpoint | Description | Parameters | Response highlights | Notes |
| :---- | :---- | :---- | :---- | :---- |
| **GET /players/profiles** | Returns player profile data. | Optional: player (ID), search (last name), page (pagination, 250 results/page)[\[37\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=To%20get%20the%20photo%20of,sports.io%2Ffootball%2Fplayers%2F%7Bplayer_id%7D.png). | Each player object includes id, name, first/last name, age, birth info, nationality, height, weight, photo and injury status[\[38\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Updated several times per week; call weekly. Use for roster displays and scouting. |

#### *Statistics*

| Endpoint | Description | Parameters | Response highlights | Notes |
| :---- | :---- | :---- | :---- | :---- |
| **GET /players** | Provides player statistics for a season. | Requires at least one of: id (player ID), team ID or league & season. Optional: search, page (20 results/page)[\[39\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=according%20to%20a%20match%20or,points%20according%20to%20his%20performance). | Returns player profile plus a statistics array with detailed metrics (team, league, games, shots, goals, passes, tackles, duels, dribbles, fouls, cards, penalties)[\[40\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Updated several times per week; call daily. Use for performance dashboards, fantasy scoring and analytics. |

#### *Squads*

| Endpoint | Description | Parameters | Response | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /players/squads** | Returns the squad of a team or the list of teams for a player. | Required: team or player[\[41\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=). | Response contains team details and players array with id, name, age, number, position, photo[\[42\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60). | Use to display team rosters or a player’s current team. |

#### *Teams (Player history)*

| Endpoint | Description | Parameters | Response | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /players/teams** | Lists teams and seasons a player has played for. | Required: player ID[\[43\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=). | Response lists each team with seasons the player was active[\[44\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2A%20%7B%20%2A%20,2932). | Useful for career history, transfers and contract analysis. |

#### *Leaderboards (Top Scorers, Assists, Cards)*

The following endpoints rank players by performance for a league/season. All require league and season parameters.

| Endpoint | Description | Response & notes | Use case |
| :---- | :---- | :---- | :---- |
| **GET /players/topscorers** | Returns the top 20 players by goals. | Response includes each player’s profile and a statistics array with team/league info, games, goals, assists, shots, passes and other metrics[\[45\]](https://www.api-football.com/documentation-v3#:~:text=get%2Fplayers%2Ftopscorers). Update frequency: several times a week; recommended call once per day. | Leaderboards, fantasy rankings, golden boot tracking. |
| **GET /players/topassists** | Returns the top 20 players by assists. | Similar structure to topscorers, with players ordered by assists[\[46\]](https://www.api-football.com/documentation-v3#:~:text=get%2Fplayers%2Ftopassists). Updated several times a week; call daily. | Displays playmaker rankings. |
| **GET /players/topyellowcards** | Returns players with most yellow cards. | Response lists players with their team and detailed statistics, ordered by yellow cards received[\[47\]](https://www.api-football.com/documentation-v3#:~:text=get%2Fplayers%2Ftopyellowcards). | Identify players at disciplinary risk. |
| **GET /players/topredcards** | Returns players with most red cards for a league/season. | The API‑sports documentation shows that this endpoint provides the 20 players with the most red cards. It uses the same query parameters (league, season) and returns similar fields as topyellowcards. Update frequency is several times a week; recommended 1 call/day[\[48\]](https://www.api-football.com/documentation-v3). | Useful to analyze disciplinary records and forecast suspensions. |

### Transfers

| Endpoint | Description | Parameters | Response & notes | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /transfers** | Retrieves transfer records (player moves) for a player or team. | Optional: player (id of the player) or team (id of the team)[\[48\]](https://www.api-football.com/documentation-v3). | Returns each transfer with player details and a transfers array containing date, type (loan/permanent), and teams (in, out, with team id, name and logo). Updated several times a week; recommended call once/day[\[48\]](https://www.api-football.com/documentation-v3). | Track transfers for players or teams, build transfer windows, monitor squad changes. |

### Trophies

| Endpoint | Description | Parameters | Response & notes | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /trophies** | Lists trophies (awards) won by players or coaches. | Accepts player (single ID) or players (string of up to 20 IDs), coach (single ID) or coachs (string of up to 20 IDs)[\[49\]](https://www.api-football.com/documentation-v3). | Response returns objects with league/cup, season, country, place and type of trophy. Updated several times a week; recommended call once/day[\[49\]](https://www.api-football.com/documentation-v3). | Display honours for players/coaches, generate hall‑of‑fame lists. |

### Sidelined

| Endpoint | Description | Parameters | Response & notes | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /sidelined** | Returns a list of players or coaches currently unavailable (injured, suspended, ill, etc.). | Accepts the same parameters as trophies: player, players, coach, coachs[\[50\]](https://api-sports.io/documentation/football/v3%23tag/Trophies/operation/get-trophies). | Each entry includes the person’s profile and an array of sidelined objects with type (e.g., injury), start and end dates. Updated several times a week; recommended call once/day[\[50\]](https://api-sports.io/documentation/football/v3%23tag/Trophies/operation/get-trophies). | Build unavailable lists for squads or track coaching absences. |

### Odds (In‑Play)

| Endpoint | Description | Parameters | Response highlights | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /odds/live** | Returns live betting odds for fixtures in progress. | Optional filters: fixture (id of a fixture), league (id of the league — note: the season parameter is ignored for in‑play odds), bet (id of the bet)[\[51\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29/operation/get-odds-live). | Each item includes fixture, update time and array of bookmakers. For each bookmaker, bets contain id, name and values, each with value, odd, handicap, main (true if main market) and suspended status. The status object indicates if the fixture is stopped, bets blocked or finished. Updated every 5–60 seconds[\[52\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29/operation/get-odds-live). | Provide live betting markets and update odds during matches. |
| **GET /odds/live/bets** | Lists available bet types for in‑play odds. | Optional: id (bet id) or search (bet name, ≥3 characters)[\[53\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29). | Response lists bet objects with id and name. All returned bet IDs can be used in the odds/live endpoint. Updated every 60 seconds[\[53\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29). | Build bet filters or show available betting markets for live odds. |

### Odds (Pre‑Match)

| Endpoint | Description | Parameters | Response highlights | Use case |
| :---- | :---- | :---- | :---- | :---- |
| **GET /odds** | Retrieves pre‑match odds for fixtures, leagues or specific dates. | Optional filters: fixture, league, season, date (YYYY‑MM‑DD), timezone, bookmaker, bet, page (pagination – 10 results/page)[\[54\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29). | Response groups odds by fixture with arrays of bookmakers. Each bookmaker has bets with id, name and values similar to live odds. Provides odds between 1–14 days before kickoff with 7‑day history. Updated every 3 hours[\[54\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29). | Display pre‑match betting markets and compare bookmaker odds. |
| **GET /odds/mapping** | Returns fixtures, leagues and dates available for pre‑match odds. | Parameter: page (default 1, 100 results/page)[\[55\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-odds). | Each mapping contains fixture, league, season and date. Updated daily; recommended call once/day. | Use to know which fixtures/leagues have odds data; prevents unnecessary calls to /odds. |
| **GET /odds/bookmakers** | Lists all available bookmakers. | Optional: id (bookmaker ID), search (≥3 characters)[\[56\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-odds-mapping). | Returns bookmaker objects with id and name. Updated several times a week; call daily. | Use to populate bookmaker selection lists. |
| **GET /odds/bets** | Lists available bet types for pre‑match odds. | Optional: id (bet ID) or search (≥3 characters)[\[57\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-bookmakers). | Response contains bets with id and name. Bet IDs can be used as filters in /odds. Updated several times a week; call daily. | Use to build bet filters for pre‑match markets. |

## Usage Notes & Integration Tips

* **Pagination:** Some endpoints return large datasets and include a paging object. For example, /odds returns 10 results per page, /odds/mapping returns 100, and /players/profiles returns 250 per page. Use the page parameter to iterate through result sets.

* **Filtering:** Combining parameters (e.g., league & season & team in /fixtures) narrows results. Endpoints generally support multiple filters; using them reduces response size and API calls.

* **Timezone handling:** Several endpoints accept a timezone parameter to return date/time values in a specific zone. Use /timezone to list valid values and ensure consistent date handling.

* **Update frequency:** Pay attention to update frequency and recommended calls to avoid unnecessary requests. Live data endpoints (fixtures, events, statistics, odds/live) update every few seconds or minutes, whereas structural endpoints (leagues, teams, venues) update daily or weekly.

* **Data coverage:** Coverage varies by league and season. Use /leagues to check whether a competition provides events, lineups, statistics, predictions or odds, and design your integration accordingly.

## Practical Applications

The API supports numerous football‑related applications:

1. **Live scoreboards and match trackers:** Combining /fixtures, /fixtures/events, /fixtures/statistics and /fixtures/players enables real‑time dashboards with goals, cards, substitutions, player stats and win probabilities.

2. **League tables and team dashboards:** /standings and /teams/statistics provide league tables, form guides and performance metrics. /players extends this to individual player stats.

3. **Fantasy sports & betting:** Use player leaderboards (/players/topscorers, /players/topassists, card endpoints) for fantasy rankings. /odds, /odds/bookmakers and /odds/bets deliver betting markets; /predictions offers algorithmic forecasts.

4. **Historical analysis:** /fixtures/headtohead and player career endpoints (/players/teams) allow analysis of past meetings and career trajectories. /trophies summarises honours.

5. **Roster management:** /transfers, /sidelined and /injuries help track squad changes, suspensions and injuries.

This guide summarises API‑Football v3 as of February 14 2026. Always refer to the official documentation for the most recent changes.

---

[\[1\]](https://www.api-football.com/documentation-v3#:~:text=REQUESTS%20HEADERS%20%26%20CORS) [\[2\]](https://www.api-football.com/documentation-v3#:~:text=Headers%20sent%20as%20response) [\[3\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=499) [\[4\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Countries) [\[5\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Update%20Frequency%20%3A%20This%20endpoint,updated%20several%20times%20a%20day) [\[6\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2F%2F%20Allows%20to%20retrieve%20all,sports.io%2Fleagues%3Fid%3D39) [\[7\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=This%20endpoint%20requires%20at%20least,one%20parameter) [\[8\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[9\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Recommended%20Calls%20%3A%201%20call,otherwise%201%20call%20per%20week) [\[10\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[11\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=team) [\[12\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Teams%20countries) [\[13\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Recommended%20Calls%20%3A%201%20call,per%20day) [\[14\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[15\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=league) [\[16\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2F%2F%20Get%20all%20Standings%20from,sports.io%2Fstandings%3Fleague%3D39%26season%3D2019) [\[17\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=league) [\[18\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=id) [\[19\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2F%2F%20Get%20fixture%20from%20one,sports.io%2Ffixtures%3Fid%3D215662) [\[20\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Head%20To%20Head) [\[21\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=,Passes) [\[22\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[23\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=fixture) [\[24\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2A%20) [\[25\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=fixture) [\[26\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[27\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=fixture) [\[28\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2A%20,2284) [\[29\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Injuries) [\[30\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=get%2Finjuries) [\[31\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Predictions) [\[32\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[33\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Get%20all%20the%20information%20about,the%20coachs%20and%20their%20careers) [\[34\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[35\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=Get%20all%20available%20seasons%20for,players%20statistics) [\[36\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[37\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=To%20get%20the%20photo%20of,sports.io%2Ffootball%2Fplayers%2F%7Bplayer_id%7D.png) [\[38\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[39\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=according%20to%20a%20match%20or,points%20according%20to%20his%20performance) [\[40\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[41\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=) [\[42\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%60) [\[43\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=) [\[44\]](https://www.api-football.com/documentation-v3#tag/Leagues/operation/get-leagues#:~:text=%2A%20%7B%20%2A%20,2932) [\[45\]](https://www.api-football.com/documentation-v3#:~:text=get%2Fplayers%2Ftopscorers) [\[46\]](https://www.api-football.com/documentation-v3#:~:text=get%2Fplayers%2Ftopassists) [\[47\]](https://www.api-football.com/documentation-v3#:~:text=get%2Fplayers%2Ftopyellowcards) [\[48\]](https://www.api-football.com/documentation-v3) [\[49\]](https://www.api-football.com/documentation-v3) API-Football \- Documentation

[https://www.api-football.com/documentation-v3](https://www.api-football.com/documentation-v3)

[\[50\]](https://api-sports.io/documentation/football/v3%23tag/Trophies/operation/get-trophies) API-Sports \- Documentation Football

[https://api-sports.io/documentation/football/v3%23tag/Trophies/operation/get-trophies](https://api-sports.io/documentation/football/v3%23tag/Trophies/operation/get-trophies)

[\[51\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29/operation/get-odds-live) [\[52\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29/operation/get-odds-live) API-Sports \- Documentation Football

[https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29/operation/get-odds-live](https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29/operation/get-odds-live)

[\[53\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29) API-Sports \- Documentation Football

[https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29](https://api-sports.io/documentation/football/v3%23tag/Odds-%28In-Play%29)

[\[54\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29) API-Sports \- Documentation Football

[https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29)

[\[55\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-odds) API-Sports \- Documentation Football

[https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-odds](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-odds)

[\[56\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-odds-mapping) API-Sports \- Documentation Football

[https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-odds-mapping](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-odds-mapping)

[\[57\]](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-bookmakers) API-Sports \- Documentation Football

[https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-bookmakers](https://api-sports.io/documentation/football/v3%23tag/Odds-%28Pre-Match%29/operation/get-bookmakers)