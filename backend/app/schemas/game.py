from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Game(BaseModel):
    id: str
    home_team: str
    away_team: str
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    period: Optional[int] = None
    clock: Optional[str] = None
    start_time: Optional[str] = None

class GameList(BaseModel):
    games: List[Game]

class GameUpdate(BaseModel):
    type: str
    game_id: Optional[str] = None
    clock: Optional[str] = None
    quarter: Optional[int] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    message: Optional[str] = None
    last_play: Optional[dict] = None 