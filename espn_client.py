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

        for attempt in range(2):
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 404:
                    break
                response.raise_for_status()
                data = response.json()

                events_list = data.get('seasonTypes', [{}])[0].get('categories', [{}])[0].get('events', [])
                events_meta = data.get('events', {})  # top-level metadata dict keyed by eventId

                if not events_list:
                    return None

                # Get player's own team id (to determine home/away)
                player_team_id = None
                try:
                    player_team_id = str(data.get('athlete', {}).get('team', {}).get('id', ''))
                except Exception:
                    pass

                rows = []
                for event in events_list:
                    event_id = str(event.get('eventId', ''))
                    stats = event.get('stats', [])

                    # Look up metadata from the top-level events dict
                    meta = events_meta.get(event_id, {})
                    if not meta:
                        # Try string/int variants
                        meta = events_meta.get(int(event_id)) if event_id.isdigit() else {}
                        if isinstance(meta, dict) and 'gameDate' not in meta:
                            meta = {}

                    game_date = meta.get('gameDate') or event.get('gameDate')
                    opponent = None
                    home_away = None

                    # Determine opponent and home/away from meta
                    home_team_id = str(meta.get('homeTeamId', ''))
                    away_team_id = str(meta.get('awayTeamId', ''))

                    if home_team_id and away_team_id and player_team_id:
                        if home_team_id == player_team_id:
                            home_away = "HOME"
                            opponent = meta.get('awayTeamAbbreviation') or away_team_id
                        elif away_team_id == player_team_id:
                            home_away = "AWAY"
                            opponent = meta.get('homeTeamAbbreviation') or home_team_id

                    # Fallback: opponent info stored inside the event (some seasons)
                    if not opponent:
                        opp_obj = event.get('opponent', {})
                        if opp_obj:
                            opponent = opp_obj.get('abbreviation') or opp_obj.get('displayName')

                    row = {
                        'game_id': event_id,
                        'date': game_date,
                        'opponent': opponent,
                        'home_away': home_away if home_away else "HOME",
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
                    time.sleep(2)
                    continue
                else:
                    df = self._load(path)
                    return df if df is not None and not df.empty else None

        df = self._load(path)
        return df if df is not None and not df.empty else None

    def refresh_all(self, players_dict: dict, sport: str, league: str, force: bool = False) -> tuple:
        """Refresh all players' gamelogs one at a time with a small delay."""
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
                    time.sleep(0.5)
            except Exception as e:
                failed += 1
                print(f"Refresh failed for {info.get('name', player_key)}: {e}")
        return success, failed


# --- Injury status lookup ---
_injury_cache = {}
INJURY_CACHE_TTL = 1800  # 30 minutes


def get_injury_status(sport: str, league: str, athlete_id: int):
    """
    Fetches the injury status for a player from ESPN's injury report.
    Returns a string like 'OUT', 'QUESTIONABLE', 'DAY-TO-DAY', or None.
    Caches results for 30 minutes.
    """
    cache_key = f"{sport}:{league}:{athlete_id}"
    cached = _injury_cache.get(cache_key)
    if cached and (time.time() - cached['time']) < INJURY_CACHE_TTL:
        return cached['status']

    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/injuries"
    status = None

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for team_block in data.get('injuries', []):
                for injury in team_block.get('injuries', []):
                    athlete = injury.get('athlete', {})
                    if str(athlete.get('id')) == str(athlete_id):
                        status = injury.get('status', '')
                        break
                if status:
                    break
    except requests.RequestException:
        pass

    _injury_cache[cache_key] = {'status': status, 'time': time.time()}
    return status