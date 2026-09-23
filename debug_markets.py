import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("PROPLINE_API_KEY")
BASE_URL = "https://api.prop-line.com"
HEADERS = {"X-API-Key": API_KEY}

# Use the Vikings game (ID 32658) that we found in the last script
event_id = "32648"

# Fetch ALL odds for this game (no market filter)
odds_url = f"{BASE_URL}/v1/sports/americanfootball_nfl/odds"
odds_params = {"event_id": event_id}

response = requests.get(odds_url, headers=HEADERS, params=odds_params, timeout=10)
response.raise_for_status()
data = response.json()

if not data:
    print("No odds returned for this event.")
else:
    print(f"Scanning all market keys for event {event_id}...\n")
    all_market_keys = set()
    player_names = set()
    
    for bookmaker in data[0].get('bookmakers', []):
        for market in bookmaker.get('markets', []):
            key = market.get('key')
            all_market_keys.add(key)
            
            # Also collect any player names we see
            for outcome in market.get('outcomes', []):
                desc = outcome.get('description', '')
                if desc:
                    player_names.add(desc)
    
    print("=== ALL MARKET KEYS AVAILABLE ===")
    for k in sorted(all_market_keys):
        print(f"  {k}")
    
    print(f"\n=== PLAYER NAMES WE SAW ({len(player_names)} unique) ===")
    # Just print the first 20
    for name in sorted(list(player_names))[:20]:
        print(f"  {name}")