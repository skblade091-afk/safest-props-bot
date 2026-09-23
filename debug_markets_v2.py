import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("PROPLINE_API_KEY")
BASE_URL = "https://api.prop-line.com"
HEADERS = {"X-API-Key": API_KEY}

# Jordan Love's game (Packers @ Falcons) — we know this has props
event_id = "32648"

# All the market keys we want to test
markets_to_test = [
    "player_pass_yds",       # Passing Yards (confirmed working)
    "player_pass_tds",       # Passing TDs
    "player_pass_td",        # Alternate spelling
    "player_rush_yds",       # Rushing Yards
    "player_rush_tds",       # Rushing TDs
    "player_receptions",     # Receptions
    "player_reception_yds",  # Receiving Yards
    "player_receiving_tds",  # Receiving TDs
    "player_anytime_td",     # Anytime TD Scorer
]

# Test each market key
for market_key in markets_to_test:
    odds_url = f"{BASE_URL}/v1/sports/americanfootball_nfl/odds"
    odds_params = {"event_id": event_id, "markets": market_key}
    try:
        r = requests.get(odds_url, headers=HEADERS, params=odds_params, timeout=10)
        data = r.json()
        
        # Check if we got any real data back
        has_data = False
        player_count = 0
        if data and data[0].get('bookmakers'):
            for bm in data[0]['bookmakers']:
                for m in bm.get('markets', []):
                    if m.get('outcomes'):
                        has_data = True
                        player_count = len(m['outcomes'])
                        break
        
        status = f"✅ {player_count} outcomes" if has_data else "❌ No data"
        print(f"{status}  |  {market_key}")
    except Exception as e:
        print(f"⚠️ Error  |  {market_key}: {e}")