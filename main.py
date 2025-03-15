from backend.app.api.nba.real_client import RealNBAClient
from backend.app.api.nba.mock_client import MockNBAClient
import time
from datetime import datetime, timedelta
import pytz
import os
from dotenv import load_dotenv
import requests

def get_nba_schedule(date_str):
    """Get NBA schedule for a specific date."""
    load_dotenv()
    api_key = os.getenv('NBA_API_KEY')
    
    if not api_key:
        print("Error: NBA_API_KEY not found in .env file")
        return None
    
    # Split the date into components
    year, month, day = date_str.split('-')
    
    url = f"https://api.sportradar.com/nba/trial/v8/en/games/{year}/{month}/{day}/schedule.json?api_key={api_key}"
    headers = {"accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("Request timed out after 10 seconds")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_play_by_play(game_id):
    """Get play-by-play data for a specific game."""
    load_dotenv()
    api_key = os.getenv('NBA_API_KEY')
    
    if not api_key:
        print("Error: NBA_API_KEY not found in .env file")
        return None
    
    url = f"https://api.sportradar.com/nba/trial/v8/en/games/{game_id}/pbp.json?api_key={api_key}"
    headers = {"accept": "application/json"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("Request timed out after 10 seconds")
        return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def find_in_progress_game(data):
    """Find the first in-progress game from the schedule."""
    if not data or not data.get("games"):
        return None
    
    for game in data.get("games", []):
        if game.get("status") == "inprogress":
            return game
    return None

def print_play(play, away_team, home_team):
    """Print a play in a formatted way."""
    description = play.get("description", "No description available")
    clock = play.get("clock", "N/A")
    period = play.get("period", {}).get("number", "N/A")
    away_points = play.get("away_points", 0)
    home_points = play.get("home_points", 0)
    
    print(f"\nQ{period} - {clock}")
    print(f"Score: {away_team} {away_points} - {home_team} {home_points}")
    print(f"Play: {description}")
    print("-" * 80)

def print_schedule(data, date_str):
    """Print the schedule in a formatted way."""
    if not data or not data.get("games"):
        print(f"\nNo games found for {date_str}")
        return False
    
    print(f"\nGames for {date_str}:")
    for game in data.get("games", []):
        home_team = game.get("home", {}).get("name", "Unknown")
        away_team = game.get("away", {}).get("name", "Unknown")
        status = game.get("status", "Unknown")
        scheduled_time = datetime.strptime(game.get("scheduled", ""), "%Y-%m-%dT%H:%M:%SZ")
        local_time = scheduled_time.strftime("%I:%M %p ET")
        
        print(f"\n{away_team} @ {home_team}")
        print(f"Time: {local_time}")
        print(f"Status: {status}")
        
        if status == "closed":
            home_points = game.get("home_points", "N/A")
            away_points = game.get("away_points", "N/A")
            print(f"Final Score: {away_team} {away_points} - {home_team} {home_points}")
        elif status == "inprogress":
            home_points = game.get("home_points", 0)
            away_points = game.get("away_points", 0)
            print(f"Current Score: {away_team} {away_points} - {home_team} {home_points}")
    
    return True

def main():
    try:
        while True:
            # Get today's date in YYYY-MM-DD format
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Get today's schedule
            data = get_nba_schedule(today)
            
            # Find an in-progress game
            game = find_in_progress_game(data)
            
            if game:
                home_team = game.get("home", {}).get("name", "Unknown")
                away_team = game.get("away", {}).get("name", "Unknown")
                game_id = game.get("id")
                
                print(f"\nWatching: {away_team} @ {home_team}")
                
                # Get play-by-play data
                pbp_data = get_play_by_play(game_id)
                
                if pbp_data:
                    # Get the most recent play
                    plays = pbp_data.get("periods", [])
                    if plays:
                        current_period = plays[-1]  # Get the last period
                        events = current_period.get("events", [])
                        if events:
                            latest_play = events[-1]  # Get the last event
                            print_play(latest_play, away_team, home_team)
            else:
                print(f"\nNo in-progress games found at {datetime.now().strftime('%I:%M:%S %p')}")
            
            # Wait 10 seconds before checking again
            print("\nWaiting 10 seconds before next update...")
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nStopping play-by-play feed...")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nMake sure your NBA_API_KEY is set in the .env file!")

def test_api():
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('NBA_API_KEY')
    
    if not api_key:
        print("Error: NBA_API_KEY not found in .env file")
        return
    
    # Use January 6, 2024 since we know it works
    year = "2024"
    month = "01"
    day = "06"
    
    url = f"https://api.sportradar.com/nba/trial/v8/en/games/{year}/{month}/{day}/schedule.json?api_key={api_key}"
    headers = {"accept": "application/json"}
    
    print(f"\nTesting API connection with daily schedule endpoint...")
    print(f"URL: {url}\n")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nSuccess! Here's the schedule:")
            for game in data.get("games", []):
                home_team = game.get("home", {}).get("name", "Unknown")
                away_team = game.get("away", {}).get("name", "Unknown")
                status = game.get("status", "Unknown")
                home_points = game.get("home_points", "N/A")
                away_points = game.get("away_points", "N/A")
                print(f"\n{away_team} @ {home_team}")
                print(f"Status: {status}")
                if status == "closed":
                    print(f"Final Score: {away_points} - {home_points}")
        else:
            print(f"Error response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("Request timed out after 10 seconds")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

# example code 
# import http.client

# conn = http.client.HTTPSConnection("api.sportradar.com")

# conn.request("GET", "/soccer/trial/v4/en/competitions.json?api_key={your_api_key}")

# res = conn.getresponse()
# data = res.read()

# print(data.decode("utf-8"))