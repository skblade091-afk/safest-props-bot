import requests
import pandas as pd
import os
import json
import time
from typing import Optional

# Persistent storage location (Railway volume)
DATA_DIR = "/data/gamelogs"

# Fallback to a local folder if not running on Railway (for local testing)
if not os.path.exists("/data"):
    DATA_DIR = os.path.join(os.path.dirname(__file__), "gamelog_cache")

os.makedirs(DATA_DIR, exist_ok=True)

# Refresh gamelogs if older than this (in seconds). 6 hours.
REFRESH_INTERVAL = 6 * 60 * 60


class ESPNClient:
    BASE_URL = "https://site.web.api.espn.com/apis/common/v3/sports"

    def _cache_path(self, sport: str, league: str, athlete_id: int) -> str:
        return os.path.join(DATA_DIR, f"{sport}_{league}_{athlete_id}.json")

    def _is_fresh(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        age = time.time() - os.path.getmtime(path)
        return age < REFRESH_INTERVAL

    def _save(self, path: str, df: pd.DataFrame):
        try:
            with open(path, 'w') as f:
                json.dump(df.to_dict(orient='records'), f)
        except Exception as e:
            print(f"Cache save failed for {path}: {e}")

    def _load(self, path: str) -> Optional[pd.DataFrame]:
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r') as f:
                records = json.load(f)
            return pd.DataFrame(records)
        except Exception as e:
            print(f"Cache load failed for {path}: {e}")
            return None

    def get_player_gamelog(self, sport: str, league: str, athlete_id: int, stat_map: dict) -> Optional[pd.DataFrame]:
        """Fetches a player's game-by-game log with persistent file cache."""
        path = self._cache_path(sport, league, athlete_id)
        
        if self._is_fresh(path):
            df = self._load(path)
            if df is not None and not df.empty:
                needed_cols = list(stat_map.keys())
                available = [c for c in needed_cols if c in df.columns]
                if available:
                    return df
        
        url = f"{self.BASE_URL}/{sport}/{league}/athletes/{athlete_id}/gamelog"
        
        # Try up to 2 times with a delay between attempts
        for attempt in range(2):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 404:
                    # Player likely hasn't played — don't retry
                    break
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
                self._save(path, df)
                return df
            except requests.RequestException:
                if attempt == 0:
                    time.sleep(2)  # Wait 2 seconds before retry
                    continue
                else:
                    # Both attempts failed — try stale cache
                    df = self._load(path)
                    return df if df is not None and not df.empty else None
        
        # Hit a 404 — no retry, just return stale cache if any
        df = self._load(path)
        return df if df is not None and not df.empty else None

    def refresh_all(self, players_dict: dict, sport: str, league: str, force: bool = False) -> tuple:
        """
        Refresh all players' gamelogs one at a time with a small delay.
        Returns (success_count, fail_count).
        """
        success = 0
        failed = 0
        for player_key, info in players_dict.items():
            try:
                path = self._cache_path(sport, league, info["espn_id"])
                if force or not self._is_fresh(path):
                    result = self.get_player_gamelog(sport, league, info["espn_id"], info["espn_stat_map"])
                    if result is not None and not result.empty:
                        success += 1
                    else:
                        failed += 1
                    # Be gentle with ESPN — 0.5s between requests
                    time.sleep(0.5)
            except Exception as e:
                failed += 1
                print(f"Refresh failed for {info.get('name', player_key)}: {e}")
        return success, failed