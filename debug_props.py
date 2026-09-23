import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("PROPLINE_API_KEY")
BASE_URL = "https://api.prop-line.com"
HEADERS = {"X-API-Key": API_KEY}

# 1. Find NFL events and print all teams
events_url = f"{BASE_URL}/v1/sports/americanfootball_nfl/events"
response = requests.get(events_url, headers=HEADERS, timeout=10)
events = response.json()

print(f"Found {len(events)} NFL events. Printing all teams:\n")
for event in events:
    away = event.get('away_team', '?')
    home = event.get('home_team', '?')
    event_id = event.get('id')
    print(f"  ID {event_id}: {away} @ {home}")

# 2. Check if any of these teams match our players
print("\n--- Looking for specific teams ---")
for event in events:
    home = event.get('home_team', '')
    away = event.get('away_team', '')
    for team in ["Vikings", "49ers"]:
        if team.lower() in home.lower() or team.lower() in away.lower():
            print(f"FOUND {team}: {away} @ {home} (ID: {event.get('id')})")
            break