import time

def test_simulation():
    """Test the simulation client with a sample game."""
    client = SimulationNBAClient()
    
    # Get available recordings
    recordings = client.get_available_recordings()
    if not recordings:
        print("No recordings available")
        return
        
    # Use the first available recording
    recording = recordings[0]
    recording_id = recording['id']
    print(f"\nStarting simulation session with recording ID: {recording_id}")
    
    # Start the simulation session
    if not client.start_session(recording_id):
        print("Failed to start simulation session")
        return
        
    print("\nWaiting for simulation to start...")
    time.sleep(5)  # Give time for the simulation to initialize
    
    try:
        while True:
            # Get play-by-play data
            pbp_data = client.get_play_by_play()
            if pbp_data.get('type') == 'error':
                print(f"\nError: {pbp_data.get('message')}")
                break
            elif pbp_data.get('type') == 'waiting':
                print(f"\r{pbp_data.get('message')}", end='', flush=True)
                time.sleep(5)  # Wait longer when in waiting state
                continue
                
            # Clear previous line
            print("\033[K", end='')
            
            # Display game information
            print(f"\nGame: {pbp_data.get('game_id', 'Unknown')}")
            print(f"Clock: {pbp_data.get('clock', '00:00')}")
            print(f"Quarter: {pbp_data.get('quarter', 1)}")
            print(f"Score: {pbp_data.get('home_score', 0)} - {pbp_data.get('away_score', 0)}")
            
            if 'last_play' in pbp_data:
                play = pbp_data['last_play']
                print(f"Last Play: {play.get('description', 'No play available')}")
            
            time.sleep(3)  # Wait before next update
            
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    except Exception as e:
        print(f"\nError during simulation: {e}") 