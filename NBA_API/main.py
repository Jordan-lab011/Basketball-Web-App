from fastapi import FastAPI, HTTPException
from nba_api.stats.static import players

app = FastAPI()

@app.get("/")
def root():
    return {"message": "NBA Stats API is running."}

@app.get("/searchPlayer/{name}")
def search_player(name: str):
    matches = players.find_players_by_full_name(name)
    if not matches:
        raise HTTPException(status_code=404, detail="Player not found")
    player = matches[0]
    return {"playerId": player["id"], "fullName": player["full_name"]}