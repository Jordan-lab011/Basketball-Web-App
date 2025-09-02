# player_of_the_day.py
import time
import math
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from nba.utils import get_season_string, clean_nans

from nba_api.stats.endpoints import (
    leaguegamelog,
    boxscoretraditionalv2,
    boxscoresummaryv2,
)

# #AVAILABLE FUNCTIONS
# get_player_of_the_day(days_ago: int = 1)

def get_player_of_the_day(days_ago: int = 1): #Main funtion
    """
    Standalone (terminal) function.
    Picks the best player for the day (PTS+REB+AST) across ALL game types.
    Returns a JSON-serializable dict.
    """
    target_dt = (datetime.now() - timedelta(days=days_ago)).date()
    date_str = target_dt.strftime("%m/%d/%Y")
    season = get_season_string(target_dt)

    print(f"Fetching Player of the Day for {date_str} (season {season})...")

    # Gather game IDs using LeagueGameLog for each season type (avoid ScoreboardV2)
    season_types = ["Regular Season", "Playoffs", "Pre Season", "In Season Tournament", "All Star"]
    game_ids = set()

    for stype in season_types:
        try:
            gl = leaguegamelog.LeagueGameLog(
                season=season,
                season_type_all_star=stype,
                date_from_nullable=date_str,
                date_to_nullable=date_str,
                # We *could* pass player/team mode; default works, we'll just dedupe GAME_IDs
            )
            df = gl.get_data_frames()[0]
            if not df.empty:
                # GAME_ID appears per-player when defaulting to player logs; dedupe
                for gid in df["GAME_ID"].unique().tolist():
                    game_ids.add(gid)
        except Exception as e:
            # If a season type isn't valid on that day, just skip it
            # (e.g., no Playoffs that date).
            continue

    if not game_ids:
        return {"message": f"No NBA games were played on {date_str}."}

    best = None  # will hold (score, payload_dict, game_id, team_abbr)
    # We’ll also store team summaries per game to compute final score later
    team_summaries = {}

    for gid in sorted(game_ids):
        # Rate-limit kindness
        time.sleep(0.6)

        try:
            # 1) Player stats (traditional box score)
            box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=gid)
            box_dict = box.get_dict()

            # Extract PlayerStats safely by name
            player_rs = next(
                (rs for rs in box_dict.get("resultSets", []) if rs.get("name") == "PlayerStats"),
                None
            )
            if not player_rs or not player_rs.get("rowSet"):
                continue

            ph = player_rs["headers"]
            idx_PLAYER_NAME = ph.index("PLAYER_NAME")
            idx_TEAM_ABBR   = ph.index("TEAM_ABBREVIATION")
            idx_PTS         = ph.index("PTS")
            idx_REB         = ph.index("REB")
            idx_AST         = ph.index("AST")

            # 2) Team stats for later final-score formatting
            team_rs = next(
                (rs for rs in box_dict.get("resultSets", []) if rs.get("name") == "TeamStats"),
                None
            )
            if team_rs and team_rs.get("rowSet"):
                th = team_rs["headers"]
                idx_TTEAM_ID  = th.index("TEAM_ID")
                idx_TABBR     = th.index("TEAM_ABBREVIATION")
                idx_TPTS      = th.index("PTS")
                team_summaries[gid] = [
                    {
                        "TEAM_ID": row[idx_TTEAM_ID],
                        "ABBR": row[idx_TABBR],
                        "PTS": row[idx_TPTS],
                    }
                    for row in team_rs["rowSet"]
                ]

            # 3) Walk players and compute SCORE = PTS + REB + AST
            for row in player_rs["rowSet"]:
                try:
                    pts = int(row[idx_PTS]) if row[idx_PTS] not in (None, "", "None") else 0
                    reb = int(row[idx_REB]) if row[idx_REB] not in (None, "", "None") else 0
                    ast = int(row[idx_AST]) if row[idx_AST] not in (None, "", "None") else 0
                except Exception:
                    # If any weird types pop up, default to 0
                    pts, reb, ast = 0, 0, 0

                score = pts + reb + ast
                player_name = row[idx_PLAYER_NAME]
                team_abbr = row[idx_TEAM_ABBR]

                payload = {
                    "Player": player_name,
                    "Team": team_abbr,
                    "Points": pts,
                    "Rebounds": reb,
                    "Assists": ast,
                }

                if (best is None) or (score > best[0]):
                    best = (score, payload, gid, team_abbr)

        except Exception as e:
            print(f"  Skipping game {gid} due to error: {e}")
            continue

    if best is None:
        return {"message": f"No player data available for {date_str}."}

    _, best_payload, best_gid, best_team_abbr = best

    # Build final score + opponent using BoxScoreSummaryV2 (no WinProbability here)
    time.sleep(0.6)
    try:
        summ = boxscoresummaryv2.BoxScoreSummaryV2(game_id=best_gid).get_dict()
        # GameSummary has HOME_TEAM_ID / VISITOR_TEAM_ID
        gs = next((rs for rs in summ["resultSets"] if rs.get("name") == "GameSummary"), None)
        ls = next((rs for rs in summ["resultSets"] if rs.get("name") == "LineScore"), None)

        home_abbr = away_abbr = None
        home_pts = away_pts = None

        if gs and gs.get("rowSet"):
            gh = gs["headers"]
            idx_HOME = gh.index("HOME_TEAM_ID")
            idx_AWAY = gh.index("VISITOR_TEAM_ID")
            home_id = gs["rowSet"][0][idx_HOME]
            away_id = gs["rowSet"][0][idx_AWAY]

            # Map team_id -> (abbr, pts) from LineScore
            id_to_abbr_pts = {}
            if ls and ls.get("rowSet"):
                lh = ls["headers"]
                idx_LTEAM = lh.index("TEAM_ID")
                idx_LABBR = lh.index("TEAM_ABBREVIATION")
                idx_LPTS  = lh.index("PTS")
                for row in ls["rowSet"]:
                    id_to_abbr_pts[row[idx_LTEAM]] = (row[idx_LABBR], row[idx_LPTS])

            if home_id in id_to_abbr_pts and away_id in id_to_abbr_pts:
                home_abbr, home_pts = id_to_abbr_pts[home_id]
                away_abbr, away_pts = id_to_abbr_pts[away_id]

        # Fallback: if we didn’t get summary, try from previously captured TeamStats
        if (home_abbr is None or away_abbr is None) and best_gid in team_summaries:
            teams = team_summaries[best_gid]
            if len(teams) == 2:
                # We don’t know home/away, but we can still present "A vs B"
                away_abbr, home_abbr = teams[0]["ABBR"], teams[1]["ABBR"]
                away_pts, home_pts = teams[0]["PTS"], teams[1]["PTS"]

        # Determine opponent based on best player’s team
        if home_abbr and away_abbr:
            if best_team_abbr == home_abbr:
                opponent_abbr = away_abbr
            elif best_team_abbr == away_abbr:
                opponent_abbr = home_abbr
            else:
                opponent_abbr = "N/A"

            if (home_pts is not None) and (away_pts is not None):
                final_score_str = f"{away_abbr}@{home_abbr}: {away_pts}-{home_pts}"
            else:
                final_score_str = "Score unavailable"
        else:
            opponent_abbr = "N/A"
            final_score_str = "Score unavailable"

    except Exception as e:
        opponent_abbr = "N/A"
        final_score_str = "Score unavailable"

    result = {
        "date": date_str,
        "player_of_the_day": {
            **best_payload,
            "Opponent": opponent_abbr,
            "Final_Score": final_score_str,
        },
    }
    return clean_nans(result)

if __name__ == "__main__":#TEST CODE
    # Change days_ago as needed for testing
    out = get_player_of_the_day(days_ago=155)
    print(json.dumps(out, indent=2))
