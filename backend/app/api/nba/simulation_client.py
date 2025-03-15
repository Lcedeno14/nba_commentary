"""Simulation NBA client for replaying past games from Sportradar.

Important Notes:
1. Sportradar Simulation API uses different endpoints for different purposes:
   - GraphQL endpoint (/graphql) for session management and recording listings
   - REST endpoints (/replay/...) for one-time data fetching
   - WebSocket endpoints (wss://...subscribe/...) for push updates
   
2. Authentication:
   - Simulations do NOT require an API key
   - Session ID must be included in WebSocket URL and sent as first message
   
3. Common Pitfalls:
   - Don't use HTTP polling for push updates - use WebSockets
   - Don't mix REST and WebSocket URL formats
   - Always handle WebSocket connection closures gracefully
   - WebSocket URLs must use /subscribe/ format
   - Session ID must be in both URL and first message
   - Some WebSocket libraries may handle upgrades differently
   
4. Simulation Flow:
   a. List available recordings via GraphQL
   b. Create a session for a recording via GraphQL mutation
   c. Connect to WebSocket endpoints with proper headers
   d. Send session ID as first message after connecting
   e. Receive real-time updates through WebSocket connections
"""
import requests
from datetime import datetime
import time
import json
import os
from dotenv import load_dotenv
from pathlib import Path
import websockets
import asyncio
import aiohttp
import ssl
import certifi
import uuid
from urllib.parse import urlencode
from base64 import b64encode

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent.parent.parent
load_dotenv(project_root / '.env')

class SimulationNBAClient:
    def __init__(self):
        self.base_url = "https://playback.sportradar.com"
        self.recording_id = None
        self.session_id = None
        self.http_headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://playback.sportradar.com",
            "Referer": "https://playback.sportradar.com/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
        # Generate a random WebSocket key
        ws_key = b64encode(uuid.uuid4().bytes).decode('utf-8')
        
        self.ws_headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "Upgrade",
            "Host": "playback.sportradar.com",
            "Origin": "https://playback.sportradar.com",
            "Pragma": "no-cache",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "Sec-WebSocket-Key": ws_key,
            "Sec-WebSocket-Version": "13",
            "Upgrade": "websocket",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        self.last_update = {}
        self.update_interval = 3
        self.callbacks = []
        
        # Create SSL context for secure WebSocket connections
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.ssl_context.check_hostname = True
        self.ssl_context.verify_mode = ssl.CERT_REQUIRED

    async def get_available_recordings(self) -> list:
        """Get a list of available NBA game recordings."""
        url = f"{self.base_url}/graphql"
        query = """
        query getRecordings($league: String!) {
            recordings(league: $league) {
                id
                title
                scheduled
                meta
                apis {
                    name
                    apiType
                }
            }
        }
        """
        variables = {
            "league": "nba"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={"query": query, "variables": variables}, headers=self.http_headers) as response:
                if response.status == 200:
                    data = await response.json()
                    recordings = data.get("data", {}).get("recordings", [])
                    
                    # Print available recordings
                    print("\nAvailable NBA Recordings:")
                    for recording in recordings:
                        print(f"\nID: {recording['id']}")
                        print(f"Title: {recording['title']}")
                        print(f"Scheduled: {recording['scheduled']}")
                        if 'apis' in recording:
                            push_apis = [api['name'] for api in recording['apis'] if api.get('apiType') == 'push']
                            rest_apis = [api['name'] for api in recording['apis'] if api.get('apiType') == 'rest']
                            print(f"Push APIs: {push_apis}")
                            print(f"REST APIs: {rest_apis}")
                        if 'meta' in recording:
                            meta = recording['meta']
                            if isinstance(meta, dict):
                                print(f"Teams: {meta.get('awayTeamName', 'Unknown')} @ {meta.get('homeTeamName', 'Unknown')}")
                    
                    return recordings
                else:
                    error_text = await response.text()
                    print(f"Failed to get recordings: {response.status}")
                    print(f"Error: {error_text}")
                    return []

    def _make_request(self, feed: str) -> dict:
        """Make a GET request to the Sportradar Simulation API."""
        if not self.session_id or not self.recording_id:
            raise ValueError("Session not initialized. Call start_session first.")
            
        url = f"{self.base_url}/{self.recording_id}"
        params = {
            'sessionId': self.session_id,
            'contentType': 'json',
            'feed': feed
        }
        
        print(f"Requesting: {url} with params: {params}")  # For debugging
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            return None
        return response.json()

    async def start_session(self, recording_id: str) -> str:
        """Start a simulation session for the given recording ID."""
        self.recording_id = recording_id
        url = "https://playback.sportradar.com/graphql"
        query = """
        mutation CreateSession($input: CreateSessionInput!) {
            createSession(input: $input)
        }
        """
        variables = {"input": {"recordingId": recording_id}}
        data = {"query": query, "variables": variables}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.http_headers, json=data) as response:
                    print(f"Response status code: {response.status}")
                    response_data = await response.json()
                    print(f"Response data: {json.dumps(response_data)}")

                    if response.status == 200 and "data" in response_data:
                        session_id = response_data["data"]["createSession"]
                        self.session_id = session_id
                        return session_id
                    else:
                        print(f"Failed to create session: {response_data}")
                        return None

        except Exception as e:
            print(f"Error creating session: {e}")
            return None

    def get_play_by_play(self) -> dict:
        """Get play-by-play data for the current simulation state."""
        try:
            # Get play-by-play data
            data = self._make_request("pbp")
            if not data:
                return {
                    "type": "error",
                    "message": "Failed to fetch play-by-play data"
                }
            
            return self._format_play_by_play(data)
            
        except Exception as e:
            print(f"Error fetching play-by-play: {e}")
            return {
                "type": "error",
                "message": f"Failed to fetch play-by-play data: {str(e)}"
            }

    def get_statistics(self) -> dict:
        """Get statistics data for the current simulation state."""
        try:
            data = self._make_request("statistics")
            if not data:
                return {
                    "type": "error",
                    "message": "Failed to fetch statistics data"
                }
            return data
        except Exception as e:
            print(f"Error fetching statistics: {e}")
            return {
                "type": "error",
                "message": f"Failed to fetch statistics data: {str(e)}"
            }

    def get_summary(self) -> dict:
        """Get summary data for the current simulation state."""
        try:
            data = self._make_request("summary")
            if not data:
                return {
                    "type": "error",
                    "message": "Failed to fetch summary data"
                }
            return data
        except Exception as e:
            print(f"Error fetching summary: {e}")
            return {
                "type": "error",
                "message": f"Failed to fetch summary data: {str(e)}"
            }

    def _format_play_by_play(self, data):
        """Format raw play-by-play data from Sportradar simulation."""
        print(f"Raw data: {json.dumps(data, indent=2)}")  # Debug print
        
        if not data:
            return {
                "type": "error",
                "message": "No data received from API"
            }
            
        if not data.get('periods'):
            return {
                "type": "waiting",
                "message": "No periods data available"
            }
        
        # Get the current period
        current_period = max(data['periods'], key=lambda p: p.get('number', 0))
        events = current_period.get('events', [])
        
        if not events:
            return {
                "type": "waiting",
                "message": "No events in current period"
            }
        
        latest_event = events[-1]
        
        # Format the play description with more details
        description = latest_event.get('description', "No description available")
        
        # Add shot details if available
        if latest_event.get('event_type') == 'shot':
            shot_type = latest_event.get('shot_type', '')
            shot_distance = latest_event.get('shot_distance', '')
            if shot_type and shot_distance:
                description += f" ({shot_type} from {shot_distance}ft)"
        
        # Add player names if available
        if 'statistics' in latest_event:
            for stat in latest_event['statistics']:
                if 'player' in stat and 'full_name' in stat['player']:
                    description = f"{stat['player']['full_name']}: {description}"
                    break
        
        return {
            "type": "play",
            "game_id": data.get('id', 'unknown'),
            "clock": latest_event.get('clock', "00:00"),
            "quarter": current_period.get('number', 1),
            "home_score": data.get('home', {}).get('points', 0),
            "away_score": data.get('away', {}).get('points', 0),
            "last_play": {
                "description": description,
                "timestamp": latest_event.get('updated', datetime.now().isoformat()),
                "event_type": latest_event.get('event_type', ''),
                "attribution": latest_event.get('attribution', {}).get('name', ''),
                "statistics": latest_event.get('statistics', [])
            }
        }

    async def connect_push_apis(self) -> bool:
        """Test connection to push APIs."""
        if not self.recording_id or not self.session_id:
            print("Recording ID and session ID must be set before connecting to push APIs")
            return False

        # Test events endpoint using WebSocket
        events_url = f"wss://playback.sportradar.com/subscribe/events/{self.recording_id}/{self.session_id}"
        print(f"Testing events endpoint: {events_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    events_url,
                    headers=self.ws_headers,
                    ssl=self.ssl_context,
                    protocols=["sportradar-playback-v1"],
                    heartbeat=20,
                    compress=15,
                    autoclose=True,
                    autoping=True
                ) as ws:
                    print("WebSocket connection established")
                    
                    # First message must be sessionId for authentication
                    auth_message = {"sessionId": self.session_id}
                    print(f"Sending auth message: {auth_message}")
                    await ws.send_json(auth_message)
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(ws.receive_json(), timeout=5)
                        print(f"Events endpoint test response: {response}")
                        return True
                    except asyncio.TimeoutError:
                        print("Timeout waiting for response")
                        return False
                    
        except aiohttp.ClientError as e:
            print(f"WebSocket error testing events endpoint: {e}")
            return False
        except Exception as e:
            print(f"Error testing events endpoint: {e}")
            return False

    async def listen_events(self):
        """Listen for events from the push API using WebSocket."""
        events_url = f"wss://playback.sportradar.com/subscribe/events/{self.recording_id}/{self.session_id}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    events_url,
                    headers=self.ws_headers,
                    ssl=self.ssl_context,
                    protocols=["sportradar-playback-v1"],
                    heartbeat=20,
                    compress=15,
                    autoclose=True,
                    autoping=True
                ) as ws:
                    print("Events WebSocket connection established")
                    
                    # Authentication required as first message
                    auth_message = {"sessionId": self.session_id}
                    print(f"Sending events auth message: {auth_message}")
                    await ws.send_json(auth_message)
                    
                    while True:
                        try:
                            msg = await ws.receive()
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    event_json = json.loads(msg.data)
                                    print("\nEvent received:", json.dumps(event_json, indent=2))
                                    yield event_json
                                except json.JSONDecodeError as e:
                                    print(f"Error decoding event JSON: {e}")
                                    print(f"Raw message data: {msg.data}")
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                print("WebSocket connection closed")
                                break
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                print(f"WebSocket error: {msg.data}")
                                break
                        except Exception as e:
                            print(f"Error receiving event message: {e}")
                            break
        except aiohttp.ClientError as e:
            print(f"Events stream WebSocket error: {e}")
        except Exception as e:
            print(f"Events stream error: {e}")

    async def listen_clock(self):
        """Listen for clock updates from the push API using WebSocket.
        
        Important:
        - Same WebSocket principles as listen_events()
        - Clock updates are separate from game events
        - May receive updates more frequently than events
        - Clock starts automatically after connecting and sending sessionId
        - Using websockets library for WebSocket connections
        """
        clock_url = f"wss://playback.sportradar.com/subscribe/clock?recording_id={self.recording_id}&sessionId={self.session_id}"

        try:
            async with websockets.connect(
                clock_url,
                extra_headers={
                    "Origin": "https://playback.sportradar.com",
                    "User-Agent": "Python/3.11 WebSocket Client",
                    "Accept": "*/*",
                    "Accept-Language": "en-US,en;q=0.9"
                },
                subprotocols=["sportradar-playback-v1"],
                ssl=self.ssl_context
            ) as ws:
                print("Clock WebSocket connection established")
                
                # Authentication required as first message
                auth_message = {"sessionId": self.session_id}
                print(f"Sending clock auth message: {auth_message}")
                await ws.send(json.dumps(auth_message))
                
                while True:
                    try:
                        message = await ws.recv()
                        try:
                            clock_json = json.loads(message)
                            print("\nClock update:", json.dumps(clock_json, indent=2))
                            yield clock_json
                        except json.JSONDecodeError as e:
                            print(f"Error decoding clock JSON: {e}")
                            print(f"Raw message data: {message}")
                        except Exception as e:
                            print(f"Error processing clock data: {e}")
                    except websockets.exceptions.ConnectionClosed:
                        print("Clock WebSocket connection closed")
                        break
                    except Exception as e:
                        print(f"Error receiving clock message: {e}")
                        break
        except websockets.exceptions.WebSocketException as e:
            print(f"Clock stream WebSocket error: {e}")
        except Exception as e:
            print(f"Clock stream error: {e}")

    async def close_push_apis(self):
        """Close the WebSocket connections.
        
        Note: WebSocket connections are automatically closed when exiting 
        their respective context managers (async with blocks).
        No explicit cleanup needed unless implementing manual connection management.
        """
        pass 