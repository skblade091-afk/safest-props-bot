import requests
import os
import re
import time
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("PROPLINE_API_KEY")
BASE_URL = "https://api.prop-line.com"
HEADERS = {"X-API-Key": API_KEY}

# --- Simple in-memory cache ---
_cache = {}
CACHE_TTL_EVENTS = 300
CACHE_TTL_ODDS = 60

def _cache_get(key):
    entry = _cache.get(key)
    if entry and time.time() - entry['time'] < entry['ttl']:
        return entry['data']
    return None

def _cache_set(key, data, ttl):
    _cache[key] = {'data': data, 'time': time.time(), 'ttl': ttl}


class OddsClient:
    def _get_events(self, sport_key):
        cache_key = f"events:{sport_key}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        events_url = f"{BASE_URL}/v1/sports/{sport_key}/events"
        try:
            r = requests.get(events_url, headers=HEADERS, timeout=10)
            r.raise_for_status()
            events = r.json()
            _cache_set(cache_key, events, CACHE_TTL_EVENTS)
            return events
        except requests.RequestException:
            return []

    def _get_event_odds(self, sport_key, event_id, market_key):
        cache_key = f"odds:{sport_key}:{event_id}:{market_key}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        odds_url = f"{BASE_URL}/v1/sports/{sport_key}/odds"
        params = {"event_id": event_id, "markets": market_key}
        try:
            r = requests.get(odds_url, headers=HEADERS, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            _cache_set(cache_key, data, CACHE_TTL_ODDS)
            return data
        except requests.RequestException:
            return []

    def get_opponent(self, team_name: str, sport_key: str = "americanfootball_nfl") -> str:
        """
        Find the opponent team for a given team. Returns the opponent name,
        or empty string if we can't determine it.
        Example: get_opponent("Packers", "americanfootball_nfl") -> "ATL Falcons"
        """
        events = self._get_events(sport_key)
        team_lower = team_name.lower()
        
        for event in events:
            home = event.get('home_team', '')
            away = event.get('away_team', '')
            if team_lower in home.lower():
                return away
            if team_lower in away.lower():
                return home
        return ""

    def is_home_game(self, team_name: str, sport_key: str = "americanfootball_nfl"):
        """
        Returns True if the given team is the home team in their next game,
        False if away, None if unknown.
        """
        events = self._get_events(sport_key)
        team_lower = team_name.lower()
        
        for event in events:
            home = event.get('home_team', '')
            away = event.get('away_team', '')
            if team_lower in home.lower():
                return True
            if team_lower in away.lower():
                return False
        return None

    def get_player_props(self, player_name: str, team_name: str, market_key: str = "player_pass_yds", sport_key: str = "americanfootball_nfl"):
        """Fetches available lines for a specific player and market (uses cache)."""
        all_lines = []
        
        events = self._get_events(sport_key)
        if not events:
            return []
        
        target_event_id = None
        for event in events:
            home = event.get('home_team', '')
            away = event.get('away_team', '')
            if team_name.lower() in home.lower() or team_name.lower() in away.lower():
                target_event_id = event.get('id')
                break
        
        if not target_event_id:
            return []
        
        odds_data = self._get_event_odds(sport_key, target_event_id, market_key)
        if not odds_data:
            return []
        
        for bookmaker in odds_data[0].get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                for outcome in market.get('outcomes', []):
                    if player_name.lower() in outcome.get('description', '').lower():
                        point_value = outcome.get('point')
                        if point_value is not None:
                            all_lines.append({'line': point_value, 'price': outcome.get('price')})
                        else:
                            match = re.search(r'(\d+)\+', outcome.get('name', ''))
                            if match:
                                all_lines.append({'line': int(match.group(1)), 'price': outcome.get('price')})
        
        unique_lines = {item['line']: item for item in all_lines}.values()
        return sorted(unique_lines, key=lambda x: x['line'])