from fastapi import APIRouter, HTTPException
from typing import List
from app.services.game_service import game_service  # Import the singleton instance
from app.schemas.game import Game, GameList

router = APIRouter()

@router.get("/", response_model=GameList)
async def list_games():
    """
    List all available NBA games for today.
    """
    try:
        games = await game_service.get_todays_games()
        return GameList(games=games)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{game_id}", response_model=Game)
async def get_game(game_id: str):
    """
    Get detailed information about a specific game.
    """
    try:
        game = await game_service.get_game_details(game_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        return game
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{game_id}/stream")
async def start_game_stream(game_id: str):
    """
    Start streaming commentary for a specific game.
    """
    try:
        stream_id = await game_service.start_game_stream(game_id)
        return {"stream_id": stream_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 