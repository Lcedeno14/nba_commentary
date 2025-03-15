"""Test script for NBA game simulation using WebSocket connections.

Important Notes:
1. Simulation Flow:
   - First get available recordings
   - Create a session for a specific recording
   - Connect to WebSocket endpoints (this auto-starts the simulation)
   - Listen for updates on both events and clock feeds
   
2. WebSocket Implementation:
   - Must include sessionId in both URL and first message
   - Need to maintain both clock and events connections simultaneously
   - Use asyncio.gather to handle multiple WebSocket connections
"""

import asyncio
import json
from app.api.nba.simulation_client import SimulationNBAClient

async def handle_event(event):
    """Process an event update from the WebSocket feed."""
    print("\nEvent Update:")
    print(json.dumps(event, indent=2))

async def handle_clock(clock):
    """Process a clock update from the WebSocket feed."""
    print("\nClock Update:")
    print(json.dumps(clock, indent=2))

async def test_simulation():
    """Test the simulation client with proper WebSocket handling."""
    client = SimulationNBAClient()
    
    try:
        # Step 1: Get available recordings
        print("Fetching available recordings...")
        recordings = await client.get_available_recordings()
        if not recordings:
            print("No recordings available")
            return

        # Find a recording with both events and clock push APIs
        selected_recording = None
        for recording in recordings:
            push_apis = [api['name'] for api in recording.get('apis', []) 
                        if api.get('apiType') == 'push']
            if 'events' in push_apis and 'clock' in push_apis:
                selected_recording = recording
                break

        if not selected_recording:
            print("No recording found with both events and clock push APIs")
            return

        print(f"\nSelected recording:")
        print(f"ID: {selected_recording['id']}")
        print(f"Title: {selected_recording['title']}")
        print(f"Scheduled: {selected_recording['scheduled']}")

        # Step 2: Create a session
        print("\nCreating session...")
        session_id = await client.start_session(selected_recording['id'])
        if not session_id:
            print("Failed to create session")
            return
        print(f"Session created: {session_id}")

        # Step 3: Connect to push APIs
        print("\nConnecting to push APIs...")
        if not await client.connect_push_apis():
            print("Failed to connect to push APIs")
            return
        print("Successfully connected to push APIs")

        # Step 4: Listen for updates
        print("\nStarting to listen for updates...")
        try:
            # Create tasks for both WebSocket feeds
            events_task = asyncio.create_task(listen_events(client))
            clock_task = asyncio.create_task(listen_clock(client))
            
            # Wait for both tasks to complete or until interrupted
            await asyncio.gather(events_task, clock_task)
            
        except KeyboardInterrupt:
            print("\nReceived interrupt signal, closing connections...")
        except Exception as e:
            print(f"\nError during simulation: {e}")
        finally:
            # Cleanup
            await client.close_push_apis()
            
    except Exception as e:
        print(f"Error in test_simulation: {e}")

async def listen_events(client):
    """Listen to the events WebSocket feed."""
    async for event in client.listen_events():
        await handle_event(event)

async def listen_clock(client):
    """Listen to the clock WebSocket feed."""
    async for clock in client.listen_clock():
        await handle_clock(clock)

if __name__ == "__main__":
    try:
        asyncio.run(test_simulation())
    except KeyboardInterrupt:
        print("\nScript interrupted by user") 