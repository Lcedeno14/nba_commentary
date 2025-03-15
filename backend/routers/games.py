from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/games",
    tags=["games"]
)

class Game(BaseModel):
    id: str
    home_team: str
    away_team: str
    score: dict[str, int]
    status: str
    start_time: str

@router.get("/", response_model=List[Game])
async def list_games():
    """
    Get a list of all available games for today
    """
    # This will be implemented to use your NBA API client
    return []

@router.get("/{game_id}", response_model=Game)
async def get_game(game_id: str):
    """
    Get details for a specific game
    """
    # This will be implemented to use your NBA API client
    raise HTTPException(status_code=501, detail="Not implemented yet") 