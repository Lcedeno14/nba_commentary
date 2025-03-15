from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json

router = APIRouter(
    prefix="/api/streams",
    tags=["streams"]
)

# Store active connections
class ConnectionManager:
    def __init__(self):
        # game_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, game_id: str):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        self.active_connections[game_id].add(websocket)

    def disconnect(self, websocket: WebSocket, game_id: str):
        self.active_connections[game_id].remove(websocket)
        if not self.active_connections[game_id]:
            del self.active_connections[game_id]

    async def broadcast(self, message: str, game_id: str):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/game/{game_id}")
async def game_commentary(websocket: WebSocket, game_id: str):
    """
    WebSocket endpoint for streaming game commentary
    """
    await manager.connect(websocket, game_id)
    try:
        while True:
            # This will be implemented to stream commentary
            data = await websocket.receive_text()
            await manager.broadcast(
                json.dumps({"game_id": game_id, "message": "Commentary coming soon"}),
                game_id
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
        await manager.broadcast(
            json.dumps({"game_id": game_id, "message": "Client disconnected"}),
            game_id
        ) 