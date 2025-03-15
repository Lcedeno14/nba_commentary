"""Game service for handling NBA game data and streaming."""
import asyncio
from datetime import datetime
from typing import Dict, Set, Optional
from ..api.nba.real_client import RealNBAClient

class GameService:
    def __init__(self):
        self.nba_client = RealNBAClient()
        self.active_streams: Dict[str, dict] = {}

    async def get_todays_games(self):
        """Get list of today's games."""
        schedule = self.nba_client.get_games(
            datetime.now().strftime("%Y/%m/%d")
        )
        return schedule.get("games", [])

    async def start_game_stream(self, game_id: str) -> asyncio.Queue:
        """Start streaming updates for a game."""
        if game_id not in self.active_streams:
            self.active_streams[game_id] = {
                "task": asyncio.create_task(self._stream_game_updates(game_id)),
                "subscribers": set(),
                "queue": asyncio.Queue()
            }
        return self.active_streams[game_id]["queue"]

    def add_subscriber(self, game_id: str, queue: asyncio.Queue):
        """Add a subscriber to a game stream."""
        if game_id in self.active_streams:
            self.active_streams[game_id]["subscribers"].add(queue)

    def remove_subscriber(self, game_id: str, queue: asyncio.Queue):
        """Remove a subscriber from a game stream."""
        if game_id in self.active_streams:
            self.active_streams[game_id]["subscribers"].remove(queue)
            if not self.active_streams[game_id]["subscribers"]:
                self.active_streams[game_id]["task"].cancel()
                del self.active_streams[game_id]

    async def _stream_game_updates(self, game_id: str):
        """Stream game updates to all subscribers."""
        try:
            while True:
                # Get latest play-by-play data
                pbp_data = self.nba_client.get_play_by_play(game_id)
                
                # Check both status and type fields
                status = pbp_data.get("status") or pbp_data.get("type")
                
                if status == "finished" or status == "game_over":
                    # Game is over, notify subscribers and stop streaming
                    for subscriber in self.active_streams[game_id]["subscribers"]:
                        await subscriber.put({
                            "type": "game_over",
                            "message": "Game has ended"
                        })
                    break
                elif status == "error":
                    # Error fetching data, wait longer before retry
                    await asyncio.sleep(10)
                    continue
                elif status == "not_found":
                    # Game not found or not started yet
                    for subscriber in self.active_streams[game_id]["subscribers"]:
                        await subscriber.put({
                            "type": "waiting",
                            "message": "Waiting for game to start..."
                        })
                    await asyncio.sleep(30)  # Check less frequently for game start
                    continue
                elif status == "waiting":
                    # Rate limiting or waiting for next play
                    for subscriber in self.active_streams[game_id]["subscribers"]:
                        await subscriber.put(pbp_data)
                    await asyncio.sleep(1)  # Short wait for waiting messages
                    continue
                
                # Send update to all subscribers
                for subscriber in self.active_streams[game_id]["subscribers"]:
                    await subscriber.put(pbp_data)
                
                # Wait before next update (using the client's rate limiting)
                await asyncio.sleep(3)
        except asyncio.CancelledError:
            # Stream was cancelled, clean up
            pass
        finally:
            if game_id in self.active_streams:
                del self.active_streams[game_id]

# Create a singleton instance
game_service = GameService() 