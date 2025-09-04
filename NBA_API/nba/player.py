# player_search.py
from nba_api.stats.static import players as nba_players_static
from nba_api.stats.endpoints import commonplayerinfo, playercareerstats
from nba.utils import (_TEAM_MAP, get_season_string, clean_nans)
import numpy as np

##AVAILABLE FUNCTIONS
# do_player_search(name: str)
# get_player_stats(player_id: int)
# do_players_comparison(player1: int, player2: int)
# do_players_autocomplete(prefix: str, limit: int = 10)

#PLAYER SEARCH FUCTION
#############################################################
def do_player_search(name: str):
    """
    Search for players whose names contain the given string (case-insensitive).
    Returns a list of matching players with:
      - id
      - full_name
      - current_team
    """
    print(f"Retrieving {name}'s details...")
    matches = nba_players_static.find_players_by_full_name(name)

    if not matches:
        print("No players found matching that name.")
        return []

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

        result.append({
            "id": pid,
            "full_name": full_name,
            "current_team": team_abbr
        })

    return result


# if __name__ == "__main__":
#     # Example: Ask user for player name
#     name = input("Enter player name to search: ")
#     results = player_search(name)

#     if results:
#         print("\nMatches found:")
#         for r in results:
#             print(r)


#PLAYER STATS FUCTION
#############################################################


def get_player_stats(player_id: int):
    """
    Returns the current season stats for the requested player_id.
    Uses PlayerCareerStats to fetch per‐season splits and filters for the current season.
    """
    try:
        print(f"Retrieving player {player_id} stats...")
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = career.get_data_frames()[0]  # DataFrame per season

        # Get current season dynamically
        current_season = get_season_string()
        row = df[df["SEASON_ID"] == current_season]

        if row.empty:
            return {"error": f"No stats found for player {player_id} in season {current_season}."}

        stats = row.iloc[0].to_dict()
        # Clean NaNs
        stats = clean_nans(stats)

        return {"player_id": player_id, "season": current_season, "stats": stats}

    except Exception as exc:
        return {"error": f"NBA API error: {str(exc)}"}


# if __name__ == "__main__":
    
#     player_id = input("Player Id: ")
#     result = get_player_stats(player_id)
#     print(result)


#COMPARE PLAYERS FUCTION
#############################################################



def do_players_comparison(player1: int, player2: int):
    season = get_season_string()
    print(f"Comparing players ({player1} vs {player2}) for {season}...")

    p1_data = get_player_stats(player1)
    p2_data = get_player_stats(player2)

    return {"season": season, "player1": p1_data, "player2": p2_data}

# if __name__ == "__main__":
#     # Replace with two valid NBA player IDs
#     player1_id = 2544      # Example: LeBron James
#     player2_id = 201939    # Example: Stephen Curry

#     try:
#         result = do_players_comparison(player1_id, player2_id)
#         print(result)
#     except Exception as e:
#         print(f"Error: {e}")

#NBA PLAYERS NAME AUTOCOMPLETE
##############################################################

def do_players_autocomplete(prefix: str, limit: int = 10):
    """
    Return players whose names contain the given prefix (case-insensitive).
    Prioritize first-name matches before others.
    """
    prefix_lower = prefix.lower()

    # Fetch all players
    all_players = nba_players_static.get_players()

    # Filter matches (substring, not just startswith)
    matches = [
        {"id": p["id"], "full_name": p["full_name"]}
        for p in all_players
        if prefix_lower in p["full_name"].lower()
    ]

    if not matches:
        return []  # No suggestions, just empty list

    def sort_key(player):
        name_parts = player["full_name"].lower().split()
        first_name = name_parts[0]
        # Prioritize first name startswith -> then substring match
        return (
            0 if first_name.startswith(prefix_lower) else 1,
            player["full_name"],
        )

    # Sort with custom key, clamp to limit
    return sorted(matches, key=sort_key)[:limit]



# if __name__ == "__main__":

#     prefix = input("Prefix: ")

#     print(f"Searching for players containing '{prefix}'")
#     results = do_players_autocomplete(prefix=prefix)
#     print(results)
