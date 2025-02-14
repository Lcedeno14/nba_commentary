import requests
import os
from dotenv import load_dotenv

load_dotenv()
NBA_API_KEY = os.getenv("NBA_API_KEY")
print("API Key:", NBA_API_KEY)
print("hello")

def get_games():
    url = ("https://api.sportradar.us/nba/trial/v8/en/games/2025/02/13/schedule.json"
                   f"?api_key={NBA_API_KEY}"
    )
    print(url)
    response = requests.get(url)
    if response.status_code != 200:
        print("Error fetching schedule:", response.status_code)
        print(response.text)
        return None
    return response.json()

def get_play_by_play(game_id):
    url = (
        f"https://api.sportradar.us/nba/trial/v8/en/games/{game_id}/pbp.json"
        f"?api_key={NBA_API_KEY}"
    )
    print("Fetching play-by-play from", url)
    response = requests.get(url)
    if response.status_code!= 200:
        print("Error fetching play-by-play:", response.status_code)
        print(response.text)
        return None
    
    return response.json()

def print_last_event(pbp_data):
    periods = pbp_data.get("periods", [])
    if not periods:
        print("No period data available.")
    
    curr_quarter = max(periods, key=lambda p: p.get("number", 0))
    
    events = curr_quarter.get("events", [])
    if not events:
        print("No events found in the current quarter.")
        return
    
    for event in events:
        description = event.get("description", "No description")
        home_points = event.get("home_points", "N/A")
        away_points = event.get("away_points", "N/A")
        print(f"Description:", description)
        print("Home Points: ",home_points)
        print("Away Points: ",away_points)
    
def main():
    schedule = get_games()
    if schedule is None:
        print("No scedule data available")
        return
    games = schedule.get("games", [])
    if not games:
        print("No games found in the schedule")
    
    game = games [1]
    game_id =game.get("id")
    print("Selected Game ID:", game_id)
    #ask user to select games
    
    pbp_data = get_play_by_play(game_id)
    if pbp_data:
        print("Play-by-Play Data: Successful")
    else:
        print("No Play-by-Play data available for the selected game")
        
    if pbp_data:
        print_last_event(pbp_data)

if __name__ == "__main__":
    main()


# example code 
# import http.client

# conn = http.client.HTTPSConnection("api.sportradar.com")

# conn.request("GET", "/soccer/trial/v4/en/competitions.json?api_key={your_api_key}")

# res = conn.getresponse()
# data = res.read()

# print(data.decode("utf-8"))