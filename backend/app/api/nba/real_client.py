"""Real NBA client for fetching live game data from Sportradar."""
import requests
from datetime import datetime
import time
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(project_root / '.env')

class RealNBAClient:
    def __init__(self):
        self.api_key = os.getenv('NBA_API_KEY')
        if not self.api_key:
            raise ValueError("NBA_API_KEY not found in environment variables")
            
        self.base_url = "https://api.sportradar.com/nba/trial/v8/en"
        self.headers = {"accept": "application/json"}
        self.timeout = 10
        self.update_interval = 10  # Changed to 10 seconds to match main.py
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum 1 second between requests
        self.last_play_id = None  # Track the last play we've shown

    def _make_request(self, endpoint: str) -> dict:
        """Make a GET request to the Sportradar API with rate limiting."""
        # Implement rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            time.sleep(sleep_time)
        
        url = f"{self.base_url}/{endpoint}?api_key={self.api_key}"
        print(f"Requesting: {url}")
        
        try:
            self.last_request_time = time.time()
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Too Many Requests
                print("Rate limit exceeded. Waiting 60 seconds...")
                time.sleep(60)  # Wait a full minute before retrying
                return self._make_request(endpoint)  # Retry the request
            else:
                print(f"Error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("Request timed out after 10 seconds")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            return None

    def get_games(self, date: str):
        """Get NBA games for a specific date."""
        try:
            # Split the date into components (YYYY-MM-DD format)
            year, month, day = date.split('-')
            data = self._make_request(f"games/{year}/{month}/{day}/schedule.json")
            
            if not data:
                return {"games": []}
            
            # Return the raw response to match main.py behavior
            return data
            
        except Exception as e:
            print(f"Error fetching games: {e}")
            return {"games": []}

    def get_play_by_play(self, game_id: str):
        """Get play-by-play data for a game."""
        try:
            data = self._make_request(f"games/{game_id}/pbp.json")
            if not data:
                return None
            
            return data
            
        except Exception as e:
            print(f"Error fetching play-by-play: {e}")
            return None

    def find_in_progress_game(self, data):
        """Find the first in-progress game from the schedule."""
        if not data or not data.get("games"):
            return None
        
        for game in data.get("games", []):
            if game.get("status") == "inprogress":
                return game
        return None

    def print_play(self, play, away_team, home_team):
        """Print a play in a formatted way."""
        # Get unique identifier for the play
        play_id = play.get("id")
        
        # Skip if we've already shown this play
        if play_id == self.last_play_id:
            return False
            
        description = play.get("description", "No description available")
        clock = play.get("clock", "N/A")
        period = play.get("period", {}).get("number", "N/A")
        away_points = play.get("away_points", 0)
        home_points = play.get("home_points", 0)
        
        print(f"\nQ{period} - {clock}")
        print(f"Score: {away_team} {away_points} - {home_team} {home_points}")
        print(f"Play: {description}")
        print("-" * 80)
        
        # Update the last play ID
        self.last_play_id = play_id
        return True

    def watch_game(self):
        """Watch an in-progress game with continuous updates."""
        try:
            while True:
                # Get today's date in YYYY-MM-DD format
                today = datetime.now().strftime("%Y-%m-%d")
                
                # Get today's schedule
                data = self.get_games(today)
                
                # Find an in-progress game
                game = self.find_in_progress_game(data)
                
                if game:
                    home_team = game.get("home", {}).get("name", "Unknown")
                    away_team = game.get("away", {}).get("name", "Unknown")
                    game_id = game.get("id")
                    
                    # Only print watching message if game ID changed
                    if not hasattr(self, 'current_game_id') or self.current_game_id != game_id:
                        print(f"\nWatching: {away_team} @ {home_team}")
                        self.current_game_id = game_id
                    
                    # Get play-by-play data
                    pbp_data = self.get_play_by_play(game_id)
                    
                    if pbp_data:
                        # Get the most recent play
                        plays = pbp_data.get("periods", [])
                        if plays:
                            current_period = plays[-1]  # Get the last period
                            events = current_period.get("events", [])
                            if events:
                                latest_play = events[-1]  # Get the last event
                                new_play = self.print_play(latest_play, away_team, home_team)
                                if not new_play:
                                    print("\nWaiting for new plays...")
                else:
                    print(f"\nNo in-progress games found at {datetime.now().strftime('%I:%M:%S %p')}")
                
                # Wait before checking again
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\nStopping play-by-play feed...")
        except Exception as e:
            print(f"\nError: {str(e)}")
            print("\nMake sure your NBA_API_KEY is set in the .env file!") 