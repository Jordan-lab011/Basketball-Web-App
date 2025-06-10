from fastapi import FastAPI, HTTPException
from nba_api.stats.static import teams as nba_teams
from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv2, leaguegamelog, playercareerstats
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time

app = FastAPI()

# Build a mapping from team_id → team_abbreviation
_TEAM_MAP = {team["id"]: team["abbreviation"] for team in nba_teams.get_teams()}


@app.get("/player-of-the-day")
def player_of_the_day(days_ago: int = 1):
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
def matches_of_the_day():
    """
    Returns all games scheduled for today (using scoreboardv2).
    For each matched dictionary:
      - 'matchup': e.g. "OKC vs. IND"
      - 'time': if NotStarted: tipoff time (e.g. "7:00 PM ET"); if InProgress: status; if Final: "Final"
      - If status == Final: include
          * 'final_score': "OKC 110–IND 105"
          * 'boxscores': list of player stats (one dict per player)
      - Otherwise: do NOT include 'final_score' or 'boxscores'
    """
    date_str = datetime.now().strftime("%m/%d/%Y")

    try:
        scoreboard = scoreboardv2.ScoreboardV2(game_date=date_str)
        gh = scoreboard.game_header.get_data_frame()
        ls = scoreboard.line_score.get_data_frame()

        if gh.empty:
            return {"message": f"No NBA games scheduled for today ({date_str})."}

        response = []
        for idx, row in gh.iterrows():
            game_id = row["GAME_ID"]
            visitor_id = int(row["VISITOR_TEAM_ID"])
            home_id = int(row["HOME_TEAM_ID"])
            visitor_abbr = _TEAM_MAP.get(visitor_id, "N/A")
            home_abbr = _TEAM_MAP.get(home_id, "N/A")
            status_text = row["GAME_STATUS_TEXT"]  # e.g. "Final", "7:00 PM ET", or "In Progress"
            status_id = int(row["GAME_STATUS_ID"])  # 1=Scheduled, 2=InProgress, 3=Final

            matchup = f"{visitor_abbr} vs. {home_abbr}"
            game_dict = {
                "matchup": matchup,
                "time": status_text
            }

            if status_id == 3:  # Final → include scores & boxscores
                # 1) Final score from line score
                ls_rows = ls[ls["GAME_ID"] == game_id]
                if ls_rows.shape[0] == 2:
                    r1, r2 = ls_rows.iloc[0], ls_rows.iloc[1]
                    tid1, pts1 = int(r1["TEAM_ID"]), int(r1["PTS"])
                    tid2, pts2 = int(r2["TEAM_ID"]), int(r2["PTS"])
                    abbr1 = _TEAM_MAP.get(tid1, "N/A")
                    abbr2 = _TEAM_MAP.get(tid2, "N/A")
                    final_score = f"{abbr1} {pts1}–{abbr2} {pts2}"
                else:
                    final_score = "Unavailable"

                # 2) Boxscore: all player stats
                time.sleep(0.5)
                box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
                player_stats_df = box.player_stats.get_data_frame()
                # Convert to list of dicts
                boxscores = player_stats_df.where(pd.notnull(player_stats_df), None).to_dict(orient="records")

                game_dict["final_score"] = final_score
                game_dict["boxscores"] = boxscores

            # If status_id == 1 or 2, do NOT include final_score or boxscores
            response.append(game_dict)

        return {"date": date_str, "games": response}

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"NBA API error: {str(exc)}")


@app.get("/player-stats/{player_id}")
def player_stats(player_id: int):
    """
    Returns the current season stats for the requested player_id.
    Uses PlayerCareerStats to fetch per‐season splits and filters for the 2024-25 season.
    If no row for 2024-25 is found, returns a 404.
    """
    try:
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = career.get_data_frames()[0]  # DataFrame per season

        # Filter for 2024-25 season
        current_season = "2024-25"
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
