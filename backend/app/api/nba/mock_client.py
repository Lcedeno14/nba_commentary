"""Mock NBA client for testing play-by-play streaming."""
import random
from datetime import datetime, timedelta

class MockNBAClient:
    def __init__(self):
        self.game_clock = 720  # 12 minutes in seconds
        self.quarter = 1
        self.home_score = 0
        self.away_score = 0
        self.home_team = "Warriors"
        self.away_team = "Lakers"
        
        # Sample play templates
        self.plays = [
            "{player} drives to the basket... SCORES!",
            "{player} pulls up for three... BANG!",
            "{player} with the mid-range jumper... GOT IT!",
            "{player} with the defensive rebound",
            "{player} finds {player2} for the assist... BUCKET!",
            "{player} steals the ball!",
            "{player} blocks the shot!",
        ]
        
        self.players = {
            "Warriors": ["Curry", "Thompson", "Green", "Wiggins", "Looney"],
            "Lakers": ["James", "Davis", "Russell", "Reaves", "Hachimura"]
        }

    def get_games(self, date: str):
        """Return mock game schedule."""
        return {
            "games": [{
                "id": "mock_game_1",
                "home_team": self.home_team,
                "away_team": self.away_team,
                "status": "in_progress",
                "home_score": self.home_score,
                "away_score": self.away_score
            }]
        }

    def get_play_by_play(self, game_id: str):
        """Generate a random play."""
        # Update game clock
        self.game_clock -= random.randint(10, 30)
        if self.game_clock <= 0:
            self.quarter += 1
            self.game_clock = 720
            if self.quarter > 4:
                return {"status": "finished"}

        # Random scoring
        scoring_play = random.random() < 0.4  # 40% chance of scoring
        if scoring_play:
            points = random.choice([2, 2, 2, 3])
            if random.random() < 0.5:
                self.home_score += points
                team = self.home_team
            else:
                self.away_score += points
                team = self.away_team
        else:
            team = random.choice([self.home_team, self.away_team])

        # Generate play description
        play_template = random.choice(self.plays)
        player = random.choice(self.players[team])
        player2 = random.choice(self.players[team])
        
        play = play_template.format(player=player, player2=player2)
        
        minutes = self.game_clock // 60
        seconds = self.game_clock % 60
        
        return {
            "game": {
                "clock": f"{minutes:02d}:{seconds:02d}",
                "quarter": self.quarter,
                "home_score": self.home_score,
                "away_score": self.away_score,
                "home_team": self.home_team,
                "away_team": self.away_team,
                "last_play": {
                    "description": play,
                    "team": team,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }

    def get_last_play(self, pbp_data: dict):
        """Extract last play from play-by-play data."""
        if not pbp_data or "game" not in pbp_data:
            return None
        return pbp_data["game"]["last_play"] 