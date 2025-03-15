"""NBA Game Commentary System with LLM Integration and Text-to-Speech."""
import asyncio
import json
from datetime import datetime
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import os
import signal
import threading
from pathlib import Path
from dotenv import load_dotenv
from ollama import AsyncClient
from elevenlabs import generate, stream, set_api_key
from elevenlabs.api import Voice
import pygame
from backend.app.api.nba.real_client import RealNBAClient

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Load environment variables
project_root = Path(__file__).parent
load_dotenv(project_root / '.env')

# Set up signal handling
signal.signal(signal.SIGINT, signal.default_int_handler)

# Set up ElevenLabs
ELEVENLABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVEN_LABS_API_KEY not found in environment variables")
set_api_key(ELEVENLABS_API_KEY)

# Data structures for game state management
@dataclass
class GameState:
    game_id: str
    home_team: str
    away_team: str
    status: str
    current_period: int = 1
    home_score: int = 0
    away_score: int = 0
    last_play_id: Optional[str] = None
    conversation_history: List[Dict] = None
    audio_queue: asyncio.Queue = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
            # Updated system prompt for Kanye-style commentary
            self.conversation_history.append({
                "role": "system",
                "content": f"""YO, IT'S KANYE WEST AND I'M THE GREATEST NBA COMMENTATOR OF ALL TIME! 
                I'M HERE TO GIVE YOU THE MOST FIRE COMMENTARY ON THIS GAME BETWEEN {self.away_team} AND {self.home_team}!
                
                RULES FOR MY COMMENTARY:
                1. BE PROVOCATIVE AND CONFIDENT - EVERY PLAY IS THE GREATEST OR WORST OF ALL TIME
                2. USE MY SIGNATURE STYLE - ALL CAPS ENERGY, BOLD STATEMENTS
                3. REFERENCE MY OWN GREATNESS AND COMPARE PLAYERS TO ME
                4. KEEP IT SHORT AND HYPE - ONE OR TWO EXPLOSIVE SENTENCES
                5. BE CONTROVERSIAL BUT KEEP IT BASKETBALL-FOCUSED
                
                REMEMBER: EVERY COMMENT SHOULD FEEL LIKE A KANYE TWEET - BOLD, OUTRAGEOUS, AND UNFORGETTABLE!"""
            })
        if self.audio_queue is None:
            self.audio_queue = asyncio.Queue()

class NBACommentarySystem:
    def __init__(self):
        self.client = RealNBAClient()
        self.games: Dict[str, GameState] = {}
        self.active_game_id: Optional[str] = None
        self.ollama_client = AsyncClient(host='http://localhost:11434')
        # Simplified voice settings
        self.voice = Voice(
            voice_id="ErXwobaYiN019PkySvjV",  # Josh voice
            settings={
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        )
        
    async def stream_audio(self, text: str, game_state: GameState):
        """Stream audio using ElevenLabs API."""
        try:
            # Generate and stream audio with basic settings
            audio_stream = generate(
                text=text,
                voice=self.voice,
                model="eleven_monolingual_v1",
                stream=True
            )
            
            # Process the audio stream
            audio_data = b""
            for chunk in audio_stream:
                audio_data += chunk
                
            # Add to game's audio queue
            await game_state.audio_queue.put(audio_data)
            
        except Exception as e:
            print(f"Error streaming audio: {e}")
    
    async def play_audio_queue(self, game_state: GameState):
        """Play audio from the game's queue."""
        try:
            while True:
                # Only play audio for active game
                if game_state.game_id == self.active_game_id:
                    # Get audio data from queue
                    audio_data = await game_state.audio_queue.get()
                    
                    # Save to temporary file (pygame needs a file)
                    temp_file = f"temp_{game_state.game_id}.mp3"
                    with open(temp_file, "wb") as f:
                        f.write(audio_data)
                    
                    # Play the audio
                    pygame.mixer.music.load(temp_file)
                    pygame.mixer.music.play()
                    
                    # Wait for audio to finish
                    while pygame.mixer.music.get_busy():
                        await asyncio.sleep(0.1)
                    
                    # Clean up
                    os.remove(temp_file)
                    
                    # Mark task as done
                    game_state.audio_queue.task_done()
                else:
                    # If not active game, just remove from queue
                    _ = await game_state.audio_queue.get()
                    game_state.audio_queue.task_done()
                    
        except asyncio.CancelledError:
            print(f"\nStopping audio for {game_state.away_team} @ {game_state.home_team}")
        except Exception as e:
            print(f"Error playing audio: {e}")
    
    async def process_play(self, game_state: GameState, play: dict) -> None:
        """Process a new play and generate commentary."""
        # Skip if we've already processed this play
        play_id = play.get("id")
        if play_id == game_state.last_play_id:
            return
            
        # Update game state
        game_state.last_play_id = play_id
        game_state.current_period = play.get("period", {}).get("number", game_state.current_period)
        game_state.home_score = play.get("home_points", game_state.home_score)
        game_state.away_score = play.get("away_points", game_state.away_score)
        
        # Format play description
        description = play.get("description", "No description available")
        clock = play.get("clock", "N/A")
        play_text = f"""
Q{game_state.current_period} - {clock}
{game_state.away_team} {game_state.away_score} - {game_state.home_team} {game_state.home_score}
Play: {description}
"""
        
        # Print the play update immediately
        print("\n" + "=" * 80)
        print(f"Game Update: {game_state.away_team} @ {game_state.home_team}")
        print("-" * 80)
        print(play_text.strip())
        
        # Add play to conversation history
        game_state.conversation_history.append({
            "role": "user",
            "content": play_text
        })
        
        # Generate commentary
        try:
            response = await self.ollama_client.chat(
                model='llama2',
                messages=game_state.conversation_history
            )
            commentary = response['message']['content']
            
            # Add commentary to history
            game_state.conversation_history.append({
                "role": "assistant",
                "content": commentary
            })
            
            # Print the commentary
            print("\nKanye's Commentary:")
            print(commentary.strip())
            print("=" * 80 + "\n")
            
            # Generate and stream audio for the commentary
            if game_state.game_id == self.active_game_id:
                await self.stream_audio(commentary, game_state)
            
        except Exception as e:
            print(f"Error generating commentary: {e}")
    
    async def watch_game(self, game_state: GameState) -> None:
        """Watch a specific game and process its plays."""
        try:
            # Start audio player task
            audio_task = asyncio.create_task(self.play_audio_queue(game_state))
            
            while True:
                # Only process if this is the active game
                if game_state.game_id == self.active_game_id:
                    # Get play-by-play data
                    pbp_data = self.client.get_play_by_play(game_state.game_id)
                    
                    if pbp_data:
                        # Get the most recent play
                        plays = pbp_data.get("periods", [])
                        if plays:
                            current_period = plays[-1]
                            events = current_period.get("events", [])
                            if events:
                                latest_play = events[-1]
                                await self.process_play(game_state, latest_play)
                
                # Wait before checking again
                await asyncio.sleep(10)
                
        except asyncio.CancelledError:
            print(f"\nStopping commentary for {game_state.away_team} @ {game_state.home_team}")
            audio_task.cancel()
            await asyncio.gather(audio_task, return_exceptions=True)
        except Exception as e:
            print(f"\nError watching game: {e}")
            
    def print_available_games(self) -> None:
        """Print available games with their status."""
        print("\nAvailable Games:")
        for i, game_state in enumerate(self.games.values(), 1):
            status = "🎙️ " if game_state.game_id == self.active_game_id else "  "
            print(f"{i}. {status}{game_state.away_team} @ {game_state.home_team}")
            print(f"   Status: {game_state.status}")
            print()
    
    async def run(self) -> None:
        """Main loop for the commentary system."""
        print("Starting NBA Commentary System...")
        
        try:
            # Get today's games
            today = datetime.now().strftime("%Y-%m-%d")
            data = self.client.get_games(today)
            games = data.get("games", [])
            
            if not games:
                print(f"\nNo games found for {today}")
                return
            
            # Initialize game states
            for game in games:
                game_id = game.get("id")
                if game_id not in self.games:
                    self.games[game_id] = GameState(
                        game_id=game_id,
                        home_team=game.get("home", {}).get("name", "Unknown"),
                        away_team=game.get("away", {}).get("name", "Unknown"),
                        status=game.get("status", "unknown").upper()
                    )
            
            while True:
                # Print available games
                self.print_available_games()
                
                # Let user select a game
                choice = input("\nEnter game number to watch (or 'q' to quit): ")
                if choice.lower() == 'q':
                    print("\nExiting...")
                    return
                
                try:
                    choice = int(choice)
                    if 1 <= choice <= len(self.games):
                        # Get the selected game
                        selected_game = list(self.games.values())[choice - 1]
                        self.active_game_id = selected_game.game_id
                        
                        print(f"\nWatching: {selected_game.away_team} @ {selected_game.home_team}")
                        print("Press Enter to switch games or 'q' to quit...")
                        
                        # Start watching all games (but only process active one)
                        tasks = []
                        for game_state in self.games.values():
                            tasks.append(asyncio.create_task(self.watch_game(game_state)))
                        
                        # Wait for user input to switch games or quit
                        while True:
                            user_input = await asyncio.get_event_loop().run_in_executor(None, input)
                            if user_input.lower() == 'q':
                                # Cancel all tasks and exit
                                for task in tasks:
                                    task.cancel()
                                await asyncio.gather(*tasks, return_exceptions=True)
                                return
                            # Only show game list if user pressed Enter
                            if user_input == "":
                                break
                        
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number or 'q' to quit.")
                
        except KeyboardInterrupt:
            print("\nGracefully shutting down NBA Commentary System...")
            # Ensure all tasks are cancelled
            for task in asyncio.all_tasks() - {asyncio.current_task()}:
                task.cancel()
            # Wait for tasks to complete cleanup
            await asyncio.gather(*asyncio.all_tasks() - {asyncio.current_task()}, return_exceptions=True)
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("\nMake sure your NBA_API_KEY is set in the .env file!")
        finally:
            # Clean up pygame
            pygame.mixer.quit()
            pygame.quit()

def main():
    """Entry point for the NBA Commentary System."""
    commentary_system = NBACommentarySystem()
    try:
        asyncio.run(commentary_system.run())
    except KeyboardInterrupt:
        print("\nShutdown complete.")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
    finally:
        # Ensure event loop is closed
        try:
            loop = asyncio.get_event_loop()
            loop.stop()
            loop.close()
        except:
            pass
        # Clean up any remaining threads
        for thread in threading.enumerate():
            if thread is not threading.main_thread():
                try:
                    thread.join(timeout=1.0)
                except:
                    pass

if __name__ == "__main__":
    main() 