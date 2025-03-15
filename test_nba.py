from backend.app.api.nba.real_client import RealNBAClient
from datetime import datetime
import time

def print_available_games(games):
    """Print available games with their status."""
    print("\nAvailable Games:")
    for i, game in enumerate(games, 1):
        home_team = game.get("home", {}).get("name", "Unknown")
        away_team = game.get("away", {}).get("name", "Unknown")
        status = game.get("status", "unknown").upper()
        scheduled = game.get("scheduled", "Time TBD")
        print(f"{i}. {away_team} @ {home_team}")
        print(f"   Status: {status}")
        print(f"   Scheduled: {scheduled}")
        print()

def watch_specific_game(client, game):
    """Watch a specific game's play-by-play."""
    try:
        home_team = game.get("home", {}).get("name", "Unknown")
        away_team = game.get("away", {}).get("name", "Unknown")
        game_id = game.get("id")
        
        print(f"\nWatching: {away_team} @ {home_team}")
        
        while True:
            # Get play-by-play data
            pbp_data = client.get_play_by_play(game_id)
            
            if pbp_data:
                # Get the most recent play
                plays = pbp_data.get("periods", [])
                if plays:
                    current_period = plays[-1]  # Get the last period
                    events = current_period.get("events", [])
                    if events:
                        latest_play = events[-1]  # Get the last event
                        new_play = client.print_play(latest_play, away_team, home_team)
                        if not new_play:
                            print("\nWaiting for new plays...")
            
            # Wait before checking again
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("\nStopping play-by-play feed...")
    except Exception as e:
        print(f"\nError: {str(e)}")

def main():
    client = RealNBAClient()
    print("Starting NBA play-by-play feed...")
    
    try:
        while True:
            # Get today's date in YYYY-MM-DD format
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Get today's schedule
            data = client.get_games(today)
            games = data.get("games", [])
            
            if not games:
                print(f"\nNo games found for {today}")
                return
            
            # Print available games
            print_available_games(games)
            
            # Let user select a game
            while True:
                try:
                    choice = input("\nEnter game number to stream (or 'q' to quit): ")
                    if choice.lower() == 'q':
                        print("\nExiting...")
                        return
                        
                    choice = int(choice)
                    if 1 <= choice <= len(games):
                        selected_game = games[choice - 1]
                        watch_specific_game(client, selected_game)
                        
                        # After game ends or is interrupted, ask if user wants to choose another game
                        watch_another = input("\nWatch another game? (y/n): ")
                        if watch_another.lower() != 'y':
                            return
                        break
                    else:
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print("Please enter a valid number or 'q' to quit.")
                except Exception as e:
                    print(f"Error: {e}")
                    return
                    
    except KeyboardInterrupt:
        print("\nStopping play-by-play feed...")
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nMake sure your NBA_API_KEY is set in the .env file!")

if __name__ == "__main__":
    main() 