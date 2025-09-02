from fastapi import (
    FastAPI,
    HTTPException,
    Query,)
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import time
from fastapi.encoders import jsonable_encoder
import json
from typing import List
from pydantic import BaseModel
from nba.matches import get_game_stats
from nba.leaders import get_league_leaders
from nba.player_of_the_day import get_player_of_the_day
from nba.player import (do_player_search, do_players_comparison, do_players_autocomplete, get_player_stats)

app = FastAPI()

# 1. List of allowed origins (your front-end URL)
origins = [
    "http://localhost:3000",   # React/Vue/whatever dev server
    "http://127.0.0.1:3000",   # in case you access by IP
    # add production URLs here once deployed
    "http://127.0.0.1:51711"
]

# 2. Add the middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # ← only these OR ["*"] to allow any
    allow_credentials=True,           # if you need cookies/auth headers
    allow_methods=["GET", "POST"],    # or ["*"] to allow all HTTP verbs
    allow_headers=["*"],              # or specify only the headers you need
)

@app.get("/search-player")
def search_player(name: str = Query(..., description="Full or partial player name")):
    """
    Search for players whose names contain the given string (case‐insensitive).
    Returns a list of matching players with:
      - id
      - full_name
      - current_team (abbreviation, or None if unavailable)
    """
    try:
        print(f"Retriving {name}'s details...")
        results = do_player_search(name)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Player search failed: {str(exc)}"
        )

@app.get("/player-stats/{player_id}")
def player_stats(player_id: int):
    """
    Returns the current season stats for the requested player_id.
    Uses PlayerCareerStats to fetch per‐season splits and filters for the 2024-25 season.
    If no row for 2024-25 is found, returns a 404.
    """
    try:
        print(f"Retriving {player_id}'s stats...")
        results = get_player_stats(player_id)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve player stats: {str(exc)}"
        )



@app.get("/player-of-the-day")
def player_of_the_day(days_ago: int = 155):#!!CHANGE int= BACK TO 1 AFTER TESTING
    """
    Returns the “best” player of a given day (default = yesterday),
    across Regular Season, Playoffs, and In-Season Tournament games.
    The “best” player is determined by the sum of (PTS + REB + AST).
    Response includes:
      - player’s name, team, points, rebounds, assists
      - opponent team abbreviation
      - final score in the format “TEAM_A @ TEAM_B: A_SCORE–B_SCORE”
    """
    try:
        print(f"Retriving player of the day...")
        results = get_player_of_the_day(days_ago)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve player stats: {str(exc)}"
        )


@app.get("/matches-of-the-day")
def matches_of_the_day(days_ago: int = 155):
    try:
        print(f"Retriving today's matches...")
        results = get_game_stats(days_ago)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve matches today: {str(exc)}"
        )

@app.get("/compare-players")
def compare_players(
    player1: int = Query(..., description="First player’s NBA ID"),
    player2: int = Query(..., description="Second player’s NBA ID"),
):
    """
    Compare two players’ per-game averages for the *current* season.
    Returns PTS, REB, AST, FG_PCT, FG3_PCT, FT_PCT, MIN, along with name and team.
    """
    try:
        print(f"Retriving players' stats...")
        results = do_players_comparison(player1, player2)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve players' stats: {str(exc)}"
        )


@app.get("/leaders")
def league_leaders(
    stat: str = Query(..., description="Stat category (e.g., PTS, REB, AST, BLK, STL, FG3M, etc.)"),
    limit: int = Query(5, description="Number of top players to return"),
):
    """
    Returns the top `limit` players for the current season’s Regular Season, 
    ranked by the given stat category (per game).
    """
    try:
        print(f"Retriving league leaders in {stat}...")
        results = get_league_leaders(stat, limit)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve league leaders in {stat}: {str(exc)}"
        )