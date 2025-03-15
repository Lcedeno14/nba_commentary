"""Test script for game streaming functionality."""
import asyncio
import websockets
import json
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def get_available_games():
    """Get list of available NBA games."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/games/")
            response.raise_for_status()
            return response.json()["games"]
        except Exception as e:
            print(f"Error fetching games: {e}")
            return []

async def test_game_stream(game_id: str, home_team: str, away_team: str):
    """Connect to WebSocket and display play-by-play updates."""
    uri = f"{WS_URL}/api/streams/ws/{game_id}"
    
    print(f"\nConnecting to game stream...")
    print(f"{home_team} vs {away_team}\n")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for game updates...\n")
            
            while True:
                try:
                    # Receive game update
                    data = await websocket.recv()
                    game_data = json.loads(data)
                    
                    if game_data.get("type") == "error":
                        print(f"\nError: {game_data.get('message')}")
                        break
                    elif game_data.get("type") == "game_over":
                        print("\nGame Over!")
                        break
                    elif game_data.get("type") == "waiting":
                        print(f"\r{game_data['message']}", end="", flush=True)
                        continue
                    
                    # Clear previous line
                    print("\033[K", end="")
                    
                    # Format and display the update
                    clock = game_data.get("clock", "00:00")
                    quarter = game_data.get("quarter", 1)
                    home_score = game_data.get("home_score", 0)
                    away_score = game_data.get("away_score", 0)
                    
                    # Display score and time
                    print(f"\rQ{quarter} {clock}")
                    print(f"{home_team} {home_score} - {away_score} {away_team}")
                    
                    if "last_play" in game_data:
                        play = game_data["last_play"]
                        print(f"🏀 {play['description']}\n")
                    
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed")
                    break
                except Exception as e:
                    print(f"\nError: {e}")
                    break
                
    except Exception as e:
        print(f"Failed to connect: {e}")

async def main():
    """Run the game streaming test."""
    print("Starting NBA live game stream test...")
    
    print("\nFetching available NBA games...")
    games = await get_available_games()
    
    if not games:
        print("No games available right now.")
        return
    
    print("\nAvailable Games:")
    for i, game in enumerate(games, 1):
        status = game.get("status", "unknown").replace("_", " ").title()
        print(f"{i}. {game['home_team']} vs {game['away_team']} - {status}")
        if "start_time" in game:
            print(f"   Start Time: {game['start_time']}")
    
    # Let user select a game
    while True:
        try:
            choice = int(input("\nEnter game number to stream (or 0 to exit): "))
            if choice == 0:
                return
            if 1 <= choice <= len(games):
                game = games[choice - 1]
                await test_game_stream(
                    game["id"],
                    game["home_team"],
                    game["away_team"]
                )
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    except Exception as e:
        print(f"\nTest failed: {e}") 