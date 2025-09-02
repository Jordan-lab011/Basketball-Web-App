# leaders.py
from nba_api.stats.endpoints import leagueleaders
from nba.utils import get_season_string  # assumes you already have this helper

#get_league_leaders(stat: str, limit: int = 5)

def get_league_leaders(stat: str, limit: int = 5):
    """
    Returns the top `limit` players for the current season’s Regular Season,
    ranked by the given stat category (per game).
    """
    season = get_season_string()
    season_type = "Regular Season"

    print(f"Loading Top {limit} players in {stat} for {season} ...")

    ll = leagueleaders.LeagueLeaders(
        season=season,
        season_type_all_star=season_type,
        stat_category_abbreviation=stat,
        per_mode48="PerGame",
        league_id="00",
    )

    df = ll.get_data_frames()[0]
    if df.empty:
        raise Exception(f"No leader data for {stat} in {season}.")

    top_df = df.head(limit)
    result = []
    for _, row in top_df.iterrows():
        result.append({
            "player_id": int(row["PLAYER_ID"]),
            "player_name": row["PLAYER"],
            "team_abbr": row["TEAM"],
            "value": row.get(stat),
        })
    return {"season": season, "stat_category": stat, "leaders": result}


if __name__ == "__main__":
    # Usage:
    #   python leaders.py PTS 5
    #   python leaders.py REB 10

    stat = (input("Stat: "))
    limit = int(input("Limit: "))

    try:
        output = get_league_leaders(stat, limit)
        print(output)
    except Exception as e:
        print(f"Error: {e}")
