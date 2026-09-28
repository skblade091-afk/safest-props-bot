import requests
import pandas as pd
import time
from typing import Optional

# --- Simple in-memory cache ---
_cache = {}
CACHE_TTL = 600  # 10 minutes — gamelogs update at most once per day

def _cache_get(key):
    entry = _cache.get(key)
    if entry and time.time() - entry['time'] < entry['ttl']:
        return entry['data']
    return None

def _cache_set(key, data, ttl):
    _cache[key] = {'data': data, 'time': time.time(), 'ttl': ttl}


class ESPNClient:
    BASE_URL = "https://site.web.api.espn.com/apis/common/v3/sports"

    def get_player_gamelog(self, sport: str, league: str, athlete_id: int, stat_map: dict) -> Optional[pd.DataFrame]:
        """
        Fetches a player's game-by-game log and extracts stats based on the stat_map.
        Caches results for 10 minutes.
        """
        cache_key = f"gamelog:{sport}:{league}:{athlete_id}:{tuple(stat_map.items())}"
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached
        
        url = f"{self.BASE_URL}/{sport}/{league}/athletes/{athlete_id}/gamelog"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            events = data.get('seasonTypes', [{}])[0].get('categories', [{}])[0].get('events', [])
            if not events:
                return None
            
            rows = []
            for event in events:
                stats = event.get('stats', [])
                row = {
                    'game_id': event.get('eventId'),
                    'date': event.get('gameDate'),
                    'opponent': event.get('opponent', {}).get('abbreviation'),
                }
                for stat_name, stat_index in stat_map.items():
                    try:
                        if stat_index < len(stats) and stats[stat_index]:
                            # Handle values like "8-18" (made-attempted) by taking the first number
                            val = stats[stat_index]
                            if isinstance(val, str) and '-' in val:
                                val = val.split('-')[0]
                            row[stat_name] = float(val)
                        else:
                            row[stat_name] = 0
                    except (ValueError, IndexError):
                        row[stat_name] = 0
                rows.append(row)
            
            df = pd.DataFrame(rows)
            _cache_set(cache_key, df, CACHE_TTL)
            return df
        except requests.RequestException as e:
            print(f"Error fetching gamelog for {athlete_id}: {e}")
            return None 