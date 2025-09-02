from nba_api.stats.endpoints import leaguegamelog, boxscoretraditionalv2
from datetime import datetime, timedelta
import pandas as pd
import time
import json
from nba.utils import clean_nans, get_season_string

##AVAILABLE FUNCTIONS
#get_game_stats(days_back: int)

def get_game_stats(days_back: int): #MAIN FUNCTION
    today = datetime.now().date()
    target_date = today - timedelta(days=days_back)
    date_str = target_date.strftime("%m/%d/%Y")
    season_str = get_season_string(target_date)

    games_json = {"games": []}

    try:
        gamelog = leaguegamelog.LeagueGameLog(
            date_from_nullable=date_str,
            date_to_nullable=date_str,
            season=season_str
            # no season_type filter → includes all games (reg season, playoffs, etc.)
        )
        games_df = gamelog.get_data_frames()[0]
        if games_df.empty:
            return clean_nans(games_json)

        for _, game in games_df.iterrows():
            game_id = game["GAME_ID"]
            matchup = game["MATCHUP"]

            try:
                time.sleep(0.6)
                box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)

                # player stats
                players_df = box.get_data_frames()[0]
                stats_df = players_df[[
                    "PLAYER_NAME", "TEAM_ABBREVIATION", "PTS", "REB", "AST",
                    "STL", "BLK", "FG3M", "FG3_PCT", "FGM", "FG_PCT", "PLUS_MINUS"
                ]]
                players = stats_df.to_dict(orient="records")

                # team stats (for final score)
                team_df = box.get_data_frames()[1]
                team_scores = team_df[["TEAM_ABBREVIATION", "PTS"]].to_dict(orient="records")
                final_score = " - ".join(str(team["PTS"]) for team in team_scores)

                # build JSON
                games_json["games"].append({
                    "date": date_str,
                    "matchup": matchup,
                    "final_score": final_score,
                    "players": players
                })

            except Exception as e:
                print(f"   Error fetching box score for game {game_id}: {e}")
                continue

    except Exception as e:
        print(f"Error fetching data for {date_str}: {e}")

    return games_json


# # Example usage
# if __name__ == "__main__":#TEST CODE
#     result = get_game_stats(32)  # Example: 155 days ago
#     print(json.dumps(result, indent=4))
