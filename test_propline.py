import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()
API_KEY = os.getenv("PROPLINE_API_KEY")
BASE_URL = "https://api.prop-line.com"
headers = {"X-API-Key": API_KEY}

# We'll try the NFL first, then fall back to sports we know are active
SPORT_KEYS_TO_TRY = ["americanfootball_nfl", "baseball_ncaa", "soccer_uefa_nations_league"]

found_sport = False
for sport_key in SPORT_KEYS_TO_TRY:
    print(f"\n--- Trying sport: {sport_key} ---")
    try:
        events_url = f"{BASE_URL}/v1/sports/{sport_key}/events"
        events_response = requests.get(events_url, headers=headers, timeout=10)
        
        if events_response.status_code != 200:
            print(f"Sport {sport_key} not found or no access. Skipping...")
            continue
            
        events = events_response.json()
        if not events:
            print(f"No upcoming events found for {sport_key}. Skipping...")
            continue
            
        print(f"Found {len(events)} events for {sport_key}!")
        first_event_id = events[0]['id']
        print(f"Fetching props for: {events[0].get('away_team')} @ {events[0].get('home_team')}")
        
        # Guess the markets based on the sport
        if "nfl" in sport_key:
            markets = "player_pass_yds,player_rush_yds,player_reception_yds,player_receptions"
        elif "baseball" in sport_key:
            markets = "player_strikeouts,player_hits,player_home_runs,player_rbis"
        else:
            markets = "player_goals,player_shots_on_target,player_assists"

        odds_url = f"{BASE_URL}/v1/sports/{sport_key}/odds"
        odds_params = {
            "event_id": first_event_id,
            "markets": markets
        }
        
        odds_response = requests.get(odds_url, headers=headers, params=odds_params, timeout=10)
        odds_response.raise_for_status()
        odds_data = odds_response.json()
        
        print("\n--- RAW PLAYER PROP DATA ---")
        print(json.dumps(odds_data, indent=2)[:4000])
        print("--- END OF PREVIEW ---")
        found_sport = True
        break # Stop after the first successful sport
        
    except Exception as e:
        print(f"Error with {sport_key}: {e}")

if not found_sport:
    print("\nCould not find any active sports with player props on the free tier.")
    print("You may need to upgrade your PropLine plan or try a different odds provider.")