from fastapi import (
    FastAPI,
    HTTPException,
    Query,)
from fastapi.middleware.cors import CORSMiddleware
from nba_api.stats.static import teams as nba_teams
from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv2, leaguegamelog, playercareerstats
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
from nba_api.stats.static import players as nba_players_static
from nba_api.stats.endpoints import (
    commonplayerinfo,
    playercareerstats,
    leagueleaders,
)
from fastapi.encoders import jsonable_encoder
import json
from typing import List
from pydantic import BaseModel

app = FastAPI()

# 1. List of allowed origins (your front-end URL)
origins = [
    "http://localhost:3000",   # React/Vue/whatever dev server
    "http://127.0.0.1:3000",   # in case you access by IP
    # add production URLs here once deployed
]

# 2. Add the middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # ← only these OR ["*"] to allow any
    allow_credentials=True,           # if you need cookies/auth headers
    allow_methods=["GET", "POST"],    # or ["*"] to allow all HTTP verbs
    allow_headers=["*"],              # or specify only the headers you need
)

# Build a mapping from team_id → team_abbreviation
_TEAM_MAP = {team["id"]: team["abbreviation"] for team in nba_teams.get_teams()}

#get currrent season fucntion
def get_current_season():
    today = datetime.now()
    if today.month >= 10:  # NBA season starts in October
        start_year = today.year
    else:
        start_year = today.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"



@app.get("/search-player")
def search_player(name: str = Query(..., description="Full or partial player name")):
    """
    Search for players whose names contain the given string (case‐insensitive).
    Returns a list of matching players with:
      - id
      - full_name
      - current_team (abbreviation, or None if unavailable)
    """
    print("Loading...")
    matches = nba_players_static.find_players_by_full_name(name)
    if not matches:
        raise HTTPException(status_code=404, detail="No players found matching that name.")

    result = []
    for p in matches:
        pid = p["id"]
        full_name = p["full_name"]

        # Attempt to get current team via CommonPlayerInfo
        try:
            info = commonplayerinfo.CommonPlayerInfo(player_id=pid).get_data_frames()[0]
            current_team_id = info.loc[0, "TEAM_ID"]
            team_abbr = _TEAM_MAP.get(int(current_team_id), None)
        except Exception:
            team_abbr = None

        result.append({"id": pid, "full_name": full_name, "current_team": team_abbr})

    return result


@app.get("/player-stats/{player_id}")
def player_stats(player_id: int):
    """
    Returns the current season stats for the requested player_id.
    Uses PlayerCareerStats to fetch per‐season splits and filters for the 2024-25 season.
    If no row for 2024-25 is found, returns a 404.
    """
    try:
        print("Loading...")
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = career.get_data_frames()[0]  # DataFrame per season

        # Filter for 2024-25 season
        current_season = get_current_season()
        row = df[df["SEASON_ID"] == current_season]

        if row.empty:
            raise HTTPException(status_code=404, detail=f"No stats found for player {player_id} in season {current_season}.")

        stats = row.iloc[0].to_dict()
        # Convert NaN to None
        stats = {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in stats.items()}

        return {"player_id": player_id, "season": current_season, "stats": stats}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"NBA API error: {str(exc)}")



@app.get("/player-of-the-day")
def player_of_the_day(days_ago: int = 2):#!!CHANGE int= BACK TO 1 AFTER TESTING
    """
    Returns the “best” player of a given day (default = yesterday),
    across Regular Season, Playoffs, and In-Season Tournament games.
    The “best” player is determined by the sum of (PTS + REB + AST).
    Response includes:
      - player’s name, team, points, rebounds, assists
      - opponent team abbreviation
      - final score in the format “TEAM_A @ TEAM_B: A_SCORE–B_SCORE”
    """
    # 1) Calculate the target date
    target_dt = (datetime.now() - timedelta(days=days_ago)).date()
    date_str = target_dt.strftime("%m/%d/%Y")

    try:
        print("Loading...")
        # 2) Fetch all games for that day via scoreboardv2
        scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str)
        game_header_df = scoreboard.game_header.get_data_frame()
        line_score_df = scoreboard.line_score.get_data_frame()

        if game_header_df.empty:
            return {"message": f"No NBA games were played on {date_str}."}

        # Collect all player box‐scores across each game_id
        all_player_stats = []
        for game_id in game_header_df["GAME_ID"].tolist():
            time.sleep(0.5)  # avoid rate‐limiting
            box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            players_df = box.player_stats.get_data_frame()
            players_df["GAME_ID"] = game_id
            all_player_stats.append(players_df)

        if not all_player_stats:
            return {"message": f"No player data available for {date_str}."}

        combined_df = pd.concat(all_player_stats, ignore_index=True)

        # 3) Clean and compute “score” = PTS + REB + AST
        combined_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        combined_df.fillna(0, inplace=True)  # ensure no NaN in PTS/REB/AST
        combined_df["SCORE"] = combined_df["PTS"] + combined_df["REB"] + combined_df["AST"]

        # 4) Find the top player by SCORE
        top_row = combined_df.sort_values(by="SCORE", ascending=False).iloc[0].to_dict()

        player_name = top_row["PLAYER_NAME"]
        player_team_id = top_row["TEAM_ID"]
        player_team_abbr = _TEAM_MAP.get(player_team_id, "N/A")
        player_pts = int(top_row["PTS"])
        player_reb = int(top_row["REB"])
        player_ast = int(top_row["AST"])
        game_id = top_row["GAME_ID"]

        # 5) From line_score_df, get final scores for that game
        ls = line_score_df[line_score_df["GAME_ID"] == game_id]
        # ls has two rows: one for each team. Extract points and team IDs
        if ls.shape[0] != 2:
            # Unexpected: if not exactly two rows, fail safely
            final_score_str = "Score unavailable"
            opponent_abbr = "N/A"
        else:
            row1, row2 = ls.iloc[0], ls.iloc[1]
            tid1, pts1 = int(row1["TEAM_ID"]), int(row1["PTS"])
            tid2, pts2 = int(row2["TEAM_ID"]), int(row2["PTS"])
            abbr1 = _TEAM_MAP.get(tid1, "N/A")
            abbr2 = _TEAM_MAP.get(tid2, "N/A")
            # Determine which row is the player’s team
            if tid1 == player_team_id:
                opponent_abbr = abbr2
                player_score = pts1
                opp_score = pts2
                score_line = f"{abbr2}@{abbr1}: {pts2}-{pts1}"
            else:
                opponent_abbr = abbr1
                player_score = pts2
                opp_score = pts1
                score_line = f"{abbr1}@{abbr2}: {pts1}-{pts2}"
            final_score_str = score_line

        return {
            "date": date_str,
            "player_of_the_day": {
                "Player": player_name,
                "Team": player_team_abbr,
                "Points": player_pts,
                "Rebounds": player_reb,
                "Assists": player_ast,
                "Opponent": opponent_abbr,
                "Final_Score": final_score_str
            }
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"NBA API error: {str(exc)}")


@app.get("/matches-of-the-day")
def matches_of_the_day(days_ago: int = 4):
    target_dt = (datetime.now() - timedelta(days=days_ago)).date()
    date_str = target_dt.strftime("%m/%d/%Y")
    # Fetch scoreboard for the given date and NBA league
    try:
        print("Loading...")
        scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str, league_id='00')
        data = scoreboard.get_dict()
        
        # Map team ID to abbreviation for team names
        team_list = nba_teams.get_teams()
        team_map = {team['id']: team['abbreviation'] for team in team_list}
        
        games = []
        # Find the GameHeader result set in the scoreboard data
        game_header = None
        for rs in data['resultSets']:
            if rs.get('name') == 'GameHeader':
                game_header = rs
                break
        if not game_header:
            print(json.dumps({"games": []}))
            return json.dumps({"games":[]})

        headers = game_header['headers']
        rows = game_header['rowSet']
        # Column indices for fields
        idx_game_id = headers.index('GAME_ID')
        idx_status_id = headers.index('GAME_STATUS_ID')
        idx_status_text = headers.index('GAME_STATUS_TEXT')
        idx_home_id = headers.index('HOME_TEAM_ID')
        idx_away_id = headers.index('VISITOR_TEAM_ID')
        idx_live_period = headers.index('LIVE_PERIOD')
        idx_live_pct = headers.index('LIVE_PC_TIME')

        for row in rows:
            game_id = row[idx_game_id]
            status_id = int(row[idx_status_id])
            status_text = row[idx_status_text] or ""
            home_id = row[idx_home_id]
            away_id = row[idx_away_id]
            home_abbr = team_map.get(home_id, str(home_id))
            away_abbr = team_map.get(away_id, str(away_id))
            matchup = f"{away_abbr} vs {home_abbr}"
            
            # Determine time text: scheduled (if not started) or live/final status
            if status_id == 1:
                time_text = status_text  # e.g. "7:30 PM ET" or similar
            elif status_id == 3:
                time_text = status_text if status_text else "Final"
            else:
                live_period = row[idx_live_period]
                live_time = row[idx_live_pct]
                # If live period/time available, format as e.g. "Q3 05:32"
                if live_period and live_time:
                    time_text = f"Q{live_period} {live_time}"
                else:
                    time_text = status_text

            game_info = {"matchup": matchup, "time": time_text}
            # If game is in progress or finished, fetch boxscore for player stats
            if status_id != 1:  # started
                box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
                box_data = box.get_dict()
                # Extract the PlayerStats result set
                player_stats = []
                for rs in box_data.get('resultSets', []):
                    if rs.get('name') == 'PlayerStats':
                        headers_ps = rs['headers']
                        idx_player_name = headers_ps.index('PLAYER_NAME')
                        idx_team_abbr = headers_ps.index('TEAM_ABBREVIATION')
                        idx_pts = headers_ps.index('PTS')
                        idx_ast = headers_ps.index('AST')
                        idx_reb = headers_ps.index('REB')
                        idx_stl = headers_ps.index('STL')
                        idx_blk = headers_ps.index('BLK')
                        idx_fg3m = headers_ps.index('FG3M')
                        idx_fg_pct = headers_ps.index('FG_PCT')
                        idx_plus = headers_ps.index('PLUS_MINUS')
                        for prow in rs['rowSet']:
                            player = {}
                            player_name = prow[idx_player_name]
                            if player_name:
                                player['player_name'] = player_name
                            team_abbr = prow[idx_team_abbr]
                            if team_abbr:
                                player['team'] = team_abbr
                            # Add stats if available
                            # Convert numeric strings to int/float
                            def safe_num(val):
                                try:
                                    return int(val) if val != '' else None
                                except:
                                    try:
                                        return float(val) if val != '' else None
                                    except:
                                        return None
                            pts = safe_num(prow[idx_pts])
                            if pts is not None: player['pts'] = pts
                            ast = safe_num(prow[idx_ast])
                            if ast is not None: player['ast'] = ast
                            reb = safe_num(prow[idx_reb])
                            if reb is not None: player['reb'] = reb
                            stl = safe_num(prow[idx_stl])
                            if stl is not None: player['stl'] = stl
                            blk = safe_num(prow[idx_blk])
                            if blk is not None: player['blk'] = blk
                            fg3m = safe_num(prow[idx_fg3m])
                            if fg3m is not None: player['fg3m'] = fg3m
                            fg_pct = prow[idx_fg_pct]
                            if fg_pct not in (None, '', 'None'): 
                                try:
                                    player['fg_pct'] = float(fg_pct)
                                except:
                                    pass
                            plus = safe_num(prow[idx_plus])
                            if plus is not None: player['plus_minus'] = plus
                            # Only include players with a name (skip empty rows)
                            if player:
                                player_stats.append(player)
                        break  # done with PlayerStats

                # Only include player list if non-empty
                if player_stats:
                    game_info['players'] = player_stats

            games.append(game_info)
        print(json.dumps({"games": games}, indent=2))
        return {"games": games}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"NBA API error: {str(exc)}")

@app.get("/compare-players")
def compare_players(
    player1: int = Query(..., description="First player’s NBA ID"),
    player2: int = Query(..., description="Second player’s NBA ID"),
):
    """
    Compare two players’ per-game averages for the *current* season.
    Returns PTS, REB, AST, FG_PCT, FG3_PCT, FT_PCT, MIN, along with name and team.
    """
    season = get_current_season()

    print("Loading...")
    def fetch_season_stats(pid: int, season: str):
        career = playercareerstats.PlayerCareerStats(player_id=pid)
        df = career.get_data_frames()[0]
        row = df[df["SEASON_ID"] == season]
        if row.empty:
            return None
        data = row.iloc[0].to_dict()
        return {
            "player_id": pid,
            "player_name": data["PLAYER_NAME"],
            "team_abbr": _TEAM_MAP.get(int(data["TEAM_ID"]), None),
            "season": season,
            "stats": {
                "PTS": int(data.get("PTS", 0)),
                "REB": int(data.get("REB", 0)),
                "AST": int(data.get("AST", 0)),
                "FG_PCT": None if pd.isna(data.get("FG_PCT")) else float(data.get("FG_PCT")),
                "FG3_PCT": None if pd.isna(data.get("FG3_PCT")) else float(data.get("FG3_PCT")),
                "FT_PCT": None if pd.isna(data.get("FT_PCT")) else float(data.get("FT_PCT")),
                "MIN": data.get("MIN"),
            },
        }

    p1_data = fetch_season_stats(player1, season)
    if p1_data is None:
        raise HTTPException(status_code=404, detail=f"No stats for player {player1} in {season}")
    p2_data = fetch_season_stats(player2, season)
    if p2_data is None:
        raise HTTPException(status_code=404, detail=f"No stats for player {player2} in {season}")

    return {"season": season, "player1": p1_data, "player2": p2_data}


@app.get("/leaders")
def league_leaders(
    stat: str = Query(..., description="Stat category (e.g., PTS, REB, AST, BLK, STL, FG3M, etc.)"),
    limit: int = Query(5, description="Number of top players to return"),
):
    """
    Returns the top `limit` players for the current season’s Regular Season, 
    ranked by the given stat category (per game).
    """
    season = get_current_season()
    season_type = "Regular Season"

    try:
        print("Loading...")
        ll = leagueleaders.LeagueLeaders(
            season=season,
            season_type_all_star=season_type,
            stat_category=stat,
            per_mode_detailed="PerGame",
            league_id="00",
        )
        df = ll.get_data_frames()[0]
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No leader data for {stat} in {season}.")

        top_df = df.head(limit)
        result = []
        for _, row in top_df.iterrows():
            result.append({
                "player_id": int(row["PLAYER_ID"]),
                "player_name": row["PLAYER_NAME"],
                "team_abbr": row["TEAM_ABBREVIATION"],
                "value": row.get(stat),
            })
        return {"season": season, "stat_category": stat, "leaders": result}

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"NBA API error: {str(exc)}")










# Define the shape of each suggestion
class PlayerSuggestion(BaseModel):
    id: int
    full_name: str

@app.get("/autocomplete", response_model=List[PlayerSuggestion])
def autocomplete_players(
    prefix: str = Query(..., min_length=1, description="Name prefix to search"),
    limit: int = Query(10, ge=1, le=50, description="Max number of suggestions")
):
    # Fetch all players once from your static source
    all_players = nba_players_static.find_players_by_full_name("")  # or however you load them
    # Filter for those whose names start with prefix
    matches = [
        {"id": p["id"], "full_name": p["full_name"]}
        for p in all_players
        if p["full_name"].lower().startswith(prefix.lower())
    ]
    if not matches:
        # return empty list instead of 404 so UI can handle “no suggestions”
        return []
    # Sort by name and clamp to limit
    matches_sorted = sorted(matches, key=lambda x: x["full_name"])[:limit]
    return matches_sorted