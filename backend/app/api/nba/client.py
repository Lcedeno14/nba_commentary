import requests
from app.core.config import settings

class NBAClient:
    def __init__(self):
        self.api_key = settings.NBA_API_KEY
        self.base_url = "https://api.sportradar.us/nba/trial/v8/en"

    def _make_request(self, endpoint: str) -> dict:
        """Make a GET request to the NBA API."""
        url = f"{self.base_url}/{endpoint}?api_key={self.api_key}"
        print(f"Requesting: {url}")  # For debugging
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            return None
        return response.json()

    def get_games(self, date: str) -> dict:
        """Get games schedule for a specific date (YYYY/MM/DD format)."""
        endpoint = f"games/{date}/schedule.json"
        return self._make_request(endpoint)

    def get_play_by_play(self, game_id: str) -> dict:
        """Get play-by-play data for a specific game."""
        endpoint = f"games/{game_id}/pbp.json"
        return self._make_request(endpoint)

    def get_last_play(self, pbp_data: dict) -> dict:
        """Extract and format the last play information."""
        if not pbp_data:
            return {"description": "No play-by-play data available."}

        periods = pbp_data.get("periods", [])
        home_team = pbp_data.get("home", {}).get("name")
        away_team = pbp_data.get("away", {}).get("name")

        if not periods:
            return {"description": "No period data available."}

        curr_quarter = max(periods, key=lambda p: p.get("number", 0))
        events = curr_quarter.get("events", [])

        if not events:
            return {"description": "No events found in the current quarter."}

        last_event = events[-1]  # Get the most recent event
        description = last_event.get("description", "No description")
        home_points = last_event.get("home_points", "N/A")
        away_points = last_event.get("away_points", "N/A")

        return {
            "description": description,
            "score": f"{home_team} {home_points} - {away_team} {away_points}",
            "home_team": home_team,
            "away_team": away_team,
            "home_points": home_points,
            "away_points": away_points
        } 