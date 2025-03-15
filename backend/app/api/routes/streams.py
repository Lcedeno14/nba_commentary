"""WebSocket routes for game streaming."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...services.game_service import game_service
import asyncio

router = APIRouter()

@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for streaming game updates."""
    await websocket.accept()
    
    # Create queue for this connection
    queue = asyncio.Queue()
    
    try:
        # Add subscriber to game stream
        game_service.add_subscriber(game_id, queue)
        
        # Start game stream if not already started
        await game_service.start_game_stream(game_id)
        
        while True:
            # Wait for updates from game stream
            data = await queue.get()
            await websocket.send_json(data)
            
    except WebSocketDisconnect:
        print(f"Client disconnected from game {game_id}")
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
    finally:
        # Clean up when client disconnects
        game_service.remove_subscriber(game_id, queue) 