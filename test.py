import requests

url = "https://api.sportradar.com/nba/trial/v8/en/games/2024/01/06/schedule.json?api_key=hGLoBk1PqwMx6UkMSeyOmgu8l31J679lBvndQzY3"

headers = {"accept": "application/json"}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except requests.exceptions.Timeout:
    print("Request timed out after 10 seconds")
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}") 