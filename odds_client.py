import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("PROPLINE_API_KEY")
BASE_URL = "https://api.prop-line.com"
HEADERS = {"X-API-Key": API_KEY}

class OddsClient:
    def get_player_props(self, player_name: str, team_name: str, market_key: str = "player_pass_yds"):
        """
        Fetches available lines for a specific player and market.
        Returns a list of dicts: [{'line': 250, 'price': -115}, ...]
        Returns an empty list if no data is available.
        """
        sport_key = "americanfootball_nfl"
        all_lines = []
        target_event_id = None

        try:
            # 1. Get all NFL events to find the player's game
            events_url = f"{BASE_URL}/v1/sports/{sport_key}/events"
            events_response = requests.get(events_url, headers=HEADERS, timeout=10)
            events_response.raise_for_status()
            events = events_response.json()

            for event in events:
                home = event.get('home_team', '')
                away = event.get('away_team', '')
                if team_name.lower() in home.lower() or team_name.lower() in away.lower():
                    target_event_id = event.get('id')
                    break

            if not target_event_id:
                return []

            # 2. Get odds for ONLY that specific event
            odds_url = f"{BASE_URL}/v1/sports/{sport_key}/odds"
            odds_params = {"event_id": target_event_id, "markets": market_key}
            odds_response = requests.get(odds_url, headers=HEADERS, params=odds_params, timeout=10)
            odds_response.raise_for_status()
            odds_data = odds_response.json()

            if not odds_data:
                return []

            # 3. Search for the player in the markets
            for bookmaker in odds_data[0].get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    for outcome in market.get('outcomes', []):
                        if player_name.lower() in outcome.get('description', '').lower():
                            match = re.search(r'(\d+)\+', outcome.get('name', ''))
                            if match:
                                line = int(match.group(1))
                                price = outcome.get('price')
                                all_lines.append({'line': line, 'price': price})

            # 4. Remove duplicates and sort
            unique_lines = {item['line']: item for item in all_lines}.values()
            return sorted(unique_lines, key=lambda x: x['line'])

        except requests.RequestException:
            return []