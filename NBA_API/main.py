from fastapi import FastAPI
from nba_api.stats.static import players

app = FastAPI()

@app.get("/")
def root():
    return {"message": "NBA Stats API is running."}