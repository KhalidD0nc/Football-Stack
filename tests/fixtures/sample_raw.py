"""Minimal sample raw JSON payloads for each endpoint.

Each fixture matches the structure produced by _upload_payload in fetch.py:
    {"endpoint": ..., "entity_key": ..., "params": ..., "fetched_at": ..., "payload": ...}
"""

TEAMS_RAW = {
    "endpoint": "/teams",
    "entity_key": "league_snapshot",
    "params": {"league": 307, "season": 2024},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "team": {
                    "id": 2932,
                    "name": "Al Hilal",
                    "code": "HIL",
                    "country": "Saudi Arabia",
                    "founded": 1957,
                    "national": False,
                    "logo": "https://media.api-sports.io/football/teams/2932.png",
                },
                "venue": {
                    "id": 4654,
                    "name": "Kingdom Arena",
                    "address": "Riyadh",
                    "city": "Riyadh",
                    "capacity": 67000,
                    "surface": "grass",
                    "image": "https://media.api-sports.io/football/venues/4654.png",
                },
            },
            {
                "team": {
                    "id": 2934,
                    "name": "Al Nassr",
                    "code": "NAS",
                    "country": "Saudi Arabia",
                    "founded": 1955,
                    "national": False,
                    "logo": "https://media.api-sports.io/football/teams/2934.png",
                },
                "venue": {
                    "id": 4656,
                    "name": "Mrsool Park",
                    "address": "Riyadh",
                    "city": "Riyadh",
                    "capacity": 25000,
                    "surface": "grass",
                    "image": "https://media.api-sports.io/football/venues/4656.png",
                },
            },
        ],
    },
}

FIXTURES_RAW = {
    "endpoint": "/fixtures",
    "entity_key": "league_snapshot",
    "params": {"league": 307, "season": 2024},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "fixture": {
                    "id": 1001,
                    "referee": "John Doe",
                    "timezone": "Asia/Riyadh",
                    "date": "2025-01-10T20:00:00+03:00",
                    "timestamp": 1736532000,
                    "periods": {"first": 1736532000, "second": 1736535600},
                    "venue": {"id": 4654, "name": "Kingdom Arena", "city": "Riyadh"},
                    "status": {"long": "Match Finished", "short": "FT", "elapsed": 90},
                },
                "league": {
                    "id": 307,
                    "name": "Saudi Pro League",
                    "country": "Saudi Arabia",
                    "logo": "https://logo.png",
                    "flag": "https://flag.png",
                    "season": 2024,
                    "round": "Regular Season - 15",
                },
                "teams": {
                    "home": {"id": 2932, "name": "Al Hilal", "logo": "https://hilal.png", "winner": True},
                    "away": {"id": 2934, "name": "Al Nassr", "logo": "https://nassr.png", "winner": False},
                },
                "goals": {"home": 2, "away": 1},
                "score": {
                    "halftime": {"home": 1, "away": 0},
                    "fulltime": {"home": 2, "away": 1},
                    "extratime": {"home": None, "away": None},
                    "penalty": {"home": None, "away": None},
                },
            }
        ],
    },
}

ROUNDS_RAW = {
    "endpoint": "/fixtures/rounds",
    "entity_key": "league_snapshot",
    "params": {"league": 307, "season": 2024},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            "Regular Season - 1",
            "Regular Season - 2",
            "Playoffs - Round 1",
        ],
    },
}

MATCH_EVENTS_RAW = {
    "endpoint": "/fixtures/events",
    "entity_key": "fixture=1001",
    "params": {"fixture": 1001},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "time": {"elapsed": 23, "extra": None},
                "team": {"id": 2932, "name": "Al Hilal"},
                "player": {"id": 501, "name": "Player A"},
                "assist": {"id": 502, "name": "Player B"},
                "type": "Goal",
                "detail": "Normal Goal",
                "comments": None,
            },
            {
                "time": {"elapsed": 67, "extra": 2},
                "team": {"id": 2934, "name": "Al Nassr"},
                "player": {"id": 601, "name": "Player C"},
                "assist": {"id": None, "name": None},
                "type": "Card",
                "detail": "Yellow Card",
                "comments": "Foul",
            },
        ],
    },
}

MATCH_TEAM_STATS_RAW = {
    "endpoint": "/fixtures/statistics",
    "entity_key": "fixture=1001",
    "params": {"fixture": 1001},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "team": {"id": 2932, "name": "Al Hilal"},
                "statistics": [
                    {"type": "Ball Possession", "value": "55%"},
                    {"type": "Total Shots", "value": 12},
                    {"type": "Shots on Goal", "value": 5},
                    {"type": "Shots off Goal", "value": 4},
                    {"type": "Blocked Shots", "value": 3},
                    {"type": "Shots insidebox", "value": 8},
                    {"type": "Shots outsidebox", "value": 4},
                    {"type": "Corner Kicks", "value": 6},
                    {"type": "Offsides", "value": 2},
                    {"type": "Fouls", "value": 14},
                    {"type": "Yellow Cards", "value": 3},
                    {"type": "Red Cards", "value": 0},
                    {"type": "Goalkeeper Saves", "value": 4},
                    {"type": "Total passes", "value": 450},
                    {"type": "Passes accurate", "value": 380},
                    {"type": "Passes %", "value": "84%"},
                    {"type": "expected_goals", "value": "1.75"},
                    {"type": "goals_prevented", "value": "0.5"},
                ],
            },
        ],
    },
}

MATCH_PLAYER_STATS_RAW = {
    "endpoint": "/fixtures/players",
    "entity_key": "fixture=1001",
    "params": {"fixture": 1001},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "team": {"id": 2932, "name": "Al Hilal", "logo": "https://hilal.png"},
                "players": [
                    {
                        "player": {"id": 501, "name": "Player A", "photo": "https://photo.png"},
                        "statistics": [
                            {
                                "games": {
                                    "number": 10,
                                    "position": "M",
                                    "rating": "7.8",
                                    "minutes": 90,
                                    "captain": False,
                                    "substitute": False,
                                },
                                "offsides": 1,
                                "shots": {"total": 3, "on": 2},
                                "goals": {"total": 1, "conceded": 0, "assists": 0, "saves": None},
                                "passes": {"total": 45, "key": 2, "accuracy": 38},
                                "tackles": {"total": 3, "blocks": 1, "interceptions": 2},
                                "duels": {"total": 10, "won": 6},
                                "dribbles": {"attempts": 4, "success": 3, "past": None},
                                "fouls": {"drawn": 2, "committed": 1},
                                "cards": {"yellow": 0, "red": 0},
                                "penalty": {
                                    "won": None,
                                    "commited": None,
                                    "scored": 0,
                                    "missed": 0,
                                    "saved": None,
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    },
}

LINEUP_PLAYERS_RAW = {
    "endpoint": "/fixtures/lineups",
    "entity_key": "fixture=1001",
    "params": {"fixture": 1001},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "team": {
                    "id": 2932,
                    "name": "Al Hilal",
                    "colors": {
                        "player": {"primary": "#0000FF", "number": "#FFFFFF", "border": "#0000FF"}
                    },
                },
                "formation": "4-3-3",
                "coach": {"id": 100, "name": "Coach X", "photo": "https://coach.png"},
                "startXI": [
                    {"player": {"id": 501, "name": "Player A", "number": 10, "pos": "M", "grid": "3:2"}},
                ],
                "substitutes": [
                    {"player": {"id": 502, "name": "Player B", "number": 22, "pos": "D", "grid": None}},
                ],
            }
        ],
    },
}

PREDICTIONS_RAW = {
    "endpoint": "/predictions",
    "entity_key": "fixture=1001",
    "params": {"fixture": 1001},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "predictions": {
                    "winner": {"id": 2932, "name": "Al Hilal", "comment": "Win or Draw"},
                    "advice": "Double chance : Al Hilal or draw",
                    "percent": {"home": "55%", "draw": "25%", "away": "20%"},
                },
                "teams": {
                    "home": {"id": 2932, "name": "Al Hilal"},
                    "away": {"id": 2934, "name": "Al Nassr"},
                },
                "comparison": {
                    "form": {"home": "70%", "away": "60%"},
                    "att": {"home": "75%", "away": "65%"},
                    "def": {"home": "80%", "away": "70%"},
                    "poisson_distribution": {"home": "50%", "away": "30%"},
                    "h2h": {"home": "55%", "away": "45%"},
                    "goals": {"home": "60%", "away": "50%"},
                    "total": {"home": "65%", "away": "55%"},
                },
            }
        ],
    },
}

PLAYER_SEASON_STATS_RAW = {
    "endpoint": "/players",
    "entity_key": "page=1",
    "params": {"league": 307, "season": 2024, "page": 1},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "player": {
                    "id": 501,
                    "name": "Player A",
                    "firstname": "First",
                    "lastname": "Last",
                    "age": 28,
                    "birthday": "1996-05-10",
                    "nationality": "Brazilian",
                    "height": "180 cm",
                    "weight": "75 kg",
                    "injured": False,
                    "photo": "https://photo.png",
                },
                "statistics": [
                    {
                        "team": {"id": 2932, "name": "Al Hilal", "logo": "https://hilal.png"},
                        "league": {
                            "id": 307,
                            "name": "Saudi Pro League",
                            "country": "Saudi Arabia",
                            "logo": "https://logo.png",
                            "flag": "https://flag.png",
                            "season": 2024,
                        },
                        "games": {
                            "appearences": 15,
                            "lineups": 14,
                            "minutes": 1200,
                            "number": 10,
                            "position": "Midfielder",
                            "rating": "7.5",
                            "captain": False,
                        },
                        "substitutes": {"in": 1, "out": 3, "bench": 2},
                        "shots": {"total": 25, "on": 12},
                        "goals": {"total": 8, "conceded": 0, "assists": 5, "saves": None},
                        "passes": {"total": 600, "key": 30, "accuracy": 85},
                        "tackles": {"total": 20, "blocks": 5, "interceptions": 15},
                        "duels": {"total": 100, "won": 55},
                        "dribbles": {"attempts": 40, "success": 25, "past": None},
                        "fouls": {"drawn": 20, "committed": 10},
                        "cards": {"yellow": 3, "yellowred": 0, "red": 0},
                        "penalty": {
                            "won": 2,
                            "commited": 0,
                            "scored": 2,
                            "missed": 0,
                            "saved": None,
                        },
                    }
                ],
            }
        ],
    },
}

PLAYER_LEADERBOARDS_RAW_TOPSCORERS = {
    "endpoint": "/players/topscorers",
    "entity_key": "league_snapshot",
    "params": {"league": 307, "season": 2024},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "player": {
                    "id": 501,
                    "name": "Player A",
                    "firstname": "First",
                    "lastname": "Last",
                    "age": 28,
                    "nationality": "Brazilian",
                    "photo": "https://photo.png",
                },
                "statistics": [
                    {
                        "team": {"id": 2932, "name": "Al Hilal"},
                        "league": {"id": 307, "season": 2024},
                        "games": {
                            "appearences": 15,
                            "minutes": 1200,
                            "position": "Midfielder",
                            "rating": "7.5",
                        },
                        "goals": {"total": 12, "assists": 5},
                        "cards": {"yellow": 2, "red": 0},
                    }
                ],
            },
            {
                "player": {
                    "id": 601,
                    "name": "Player C",
                    "firstname": "First2",
                    "lastname": "Last2",
                    "age": 25,
                    "nationality": "Argentine",
                    "photo": "https://photo2.png",
                },
                "statistics": [
                    {
                        "team": {"id": 2934, "name": "Al Nassr"},
                        "league": {"id": 307, "season": 2024},
                        "games": {
                            "appearences": 14,
                            "minutes": 1100,
                            "position": "Forward",
                            "rating": "7.3",
                        },
                        "goals": {"total": 10, "assists": 3},
                        "cards": {"yellow": 4, "red": 1},
                    }
                ],
            },
        ],
    },
}

SQUAD_PLAYERS_RAW = {
    "endpoint": "/players/squads",
    "entity_key": "team=2932",
    "params": {"team": 2932},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "team": {"id": 2932, "name": "Al Hilal", "logo": "https://hilal.png"},
                "players": [
                    {"id": 501, "name": "Player A", "age": 28, "number": 10, "position": "Midfielder", "photo": "https://photo.png"},
                    {"id": 502, "name": "Player B", "age": 24, "number": 22, "position": "Defender", "photo": "https://photo2.png"},
                ],
            }
        ],
    },
}

TEAM_STANDINGS_RAW = {
    "endpoint": "/standings",
    "entity_key": "league_snapshot",
    "params": {"league": 307, "season": 2024},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "league": {
                    "id": 307,
                    "standings": [
                        [
                            {
                                "rank": 1,
                                "team": {"id": 2932, "name": "Al Hilal", "logo": "https://hilal.png"},
                                "group": "Group A",
                                "form": "WWWDW",
                                "status": "same",
                                "description": "Champions League",
                                "all": {"played": 15, "win": 12, "draw": 2, "lose": 1, "goals": {"for": 35, "against": 10}},
                                "home": {"played": 8, "win": 7, "draw": 1, "lose": 0, "goals": {"for": 20, "against": 4}},
                                "away": {"played": 7, "win": 5, "draw": 1, "lose": 1, "goals": {"for": 15, "against": 6}},
                                "goalsDiff": 25,
                                "points": 38,
                            }
                        ]
                    ],
                }
            }
        ],
    },
}

TEAM_STATISTICS_RAW = {
    "endpoint": "/teams/statistics",
    "entity_key": "team=2932",
    "params": {"team": 2932, "league": 307, "season": 2024},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": {
            "team": {"id": 2932, "name": "Al Hilal", "logo": "https://hilal.png"},
            "league": {"id": 307, "name": "Saudi Pro League", "season": 2024},
            "form": "WWWDW",
            "fixtures": {
                "played": {"home": 8, "away": 7, "total": 15},
                "wins": {"home": 7, "away": 5, "total": 12},
                "draws": {"home": 1, "away": 1, "total": 2},
                "loses": {"home": 0, "away": 1, "total": 1},
            },
            "goals": {
                "for": {
                    "total": {"home": 20, "away": 15, "total": 35},
                    "average": {"home": "2.5", "away": "2.1", "total": "2.3"},
                },
                "against": {
                    "total": {"home": 4, "away": 6, "total": 10},
                    "average": {"home": "0.5", "away": "0.9", "total": "0.7"},
                },
            },
            "clean_sheet": {"home": 5, "away": 3, "total": 8},
            "failed_to_score": {"home": 0, "away": 1, "total": 1},
            "biggest": {
                "streak": {"wins": 8, "draws": 1, "loses": 1},
                "wins": {"home": "5-0", "away": "0-4"},
                "loses": {"home": None, "away": "2-1"},
                "goals": {"for": {"home": 5, "away": 4}, "against": {"home": 2, "away": 3}},
            },
        },
    },
}

TRANSFERS_RAW = {
    "endpoint": "/transfers",
    "entity_key": "team=2932",
    "params": {"team": 2932},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "player": {"id": 501, "name": "Player A"},
                "transfers": [
                    {
                        "date": "2024-07-01",
                        "type": "Free",
                        "teams": {
                            "in": {"id": 2932, "name": "Al Hilal", "logo": "https://hilal.png"},
                            "out": {"id": 100, "name": "Old Club", "logo": "https://old.png"},
                        },
                    },
                    {
                        "date": "2022-01-15",
                        "type": "Loan",
                        "teams": {
                            "in": {"id": 100, "name": "Old Club", "logo": "https://old.png"},
                            "out": {"id": 200, "name": "Other Club", "logo": "https://other.png"},
                        },
                    },
                ],
            }
        ],
    },
}

INJURIES_RAW = {
    "endpoint": "/injuries",
    "entity_key": "team=2932",
    "params": {"team": 2932, "league": 307, "season": 2024},
    "fetched_at": "2025-01-15T12:00:00Z",
    "payload": {
        "response": [
            {
                "player": {"id": 502, "name": "Player B", "photo": "https://photo2.png"},
                "team": {"id": 2932, "name": "Al Hilal", "logo": "https://hilal.png"},
                "fixture": {
                    "id": 1001,
                    "timezone": "Asia/Riyadh",
                    "date": "2025-01-10T20:00:00+03:00",
                    "timestamp": 1736532000,
                },
                "league": {
                    "id": 307,
                    "name": "Saudi Pro League",
                    "country": "Saudi Arabia",
                    "logo": "https://logo.png",
                    "flag": "https://flag.png",
                    "season": 2024,
                },
                "type": "Muscle Injury",
                "reason": "Hamstring",
            }
        ],
    },
}
