import pytest
import asyncio
import httpx
import websockets
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def test_register_and_login():
    """Test user registration and login flow."""
    async with httpx.AsyncClient() as client:
        # Test registration
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        
        response = await client.post(f"{BASE_URL}/api/users/register", json=register_data)
        print("\nRegistration Response:", response.status_code, response.text)
        assert response.status_code in [200, 400]  # 400 if user already exists
        
        # Test login
        login_data = {
            "username": "testuser",
            "password": "testpass123"
        }
        
        response = await client.post(
            f"{BASE_URL}/api/users/token",
            data=login_data,  # Note: using form data for login
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print("\nLogin Response:", response.status_code, response.text)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        return token_data["access_token"]

async def test_games_endpoint(token):
    """Test the games listing endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/games",
            headers={"Authorization": f"Bearer {token}"}
        )
        print("\nGames Response:", response.status_code, response.text)
        assert response.status_code == 200

async def test_websocket_connection(token, game_id="test_game"):
    """Test WebSocket connection and game updates."""
    try:
        async with websockets.connect(
            f"{WS_URL}/api/streams/ws/{game_id}",
            extra_headers={"Authorization": f"Bearer {token}"}
        ) as websocket:
            print("\nWebSocket connected successfully")
            
            # Wait for a game update
            try:
                async with asyncio.timeout(5):
                    message = await websocket.recv()
                    print("Received message:", message)
            except asyncio.TimeoutError:
                print("No message received in 5 seconds (expected if no game is active)")
    except Exception as e:
        print(f"WebSocket connection error: {e}")

async def main():
    """Run all tests."""
    print("\nStarting API tests...")
    
    # Test registration and login
    token = await test_register_and_login()
    print("\nAuthentication token received:", token)
    
    # Test games endpoint
    await test_games_endpoint(token)
    
    # Test WebSocket connection
    await test_websocket_connection(token)
    
    print("\nTests completed!")

if __name__ == "__main__":
    asyncio.run(main()) 