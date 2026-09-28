import requests
import pandas as pd
import os
import json
import time
from typing import Optional
from datetime import datetime, timedelta

# Persistent storage location (Railway volume)
DATA_DIR = "/data/gamelogs"

# Fallback to a local folder if not running on Railway (for local testing)
if not os.path.exists("/data"):
    DATA_DIR = os.path.join(os.path.dirname(__file__), "gamelog_cache")

os.makedirs(DATA_DIR, exist_ok=True)

# Refresh gamelogs if older than this (in seconds). 6 hours.
REFRESH_INTERVAL = 6 * 60 * 60


# --- Game info cache: per-game home/away lookup ---
_game_info_cache = {}
GAME_INFO_CACHE_TTL = 24 * 60 * 60  # 24 hours


def _get_game_info(sport: str, league: str, game_id: str) -> dict:
    """
    Fetch ESPN game summary and extract home/away teams.
    Returns {'home': 'team name', 'away': 'team name'} or {}.
    """
    cache_key = f"{sport}:{league}:{game_id}"
    cached = _game_info_cache.get(cache_key)
    if cached and (time.time() - cached['time']) < GAME_INFO_CACHE_TTL:
        return cached['data']

    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/summary?event={game_id}"
    result = {}
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            header = data.get('header', {})
            competitions = header.get('competitions', [])
            if competitions:
                comp = competitions[0]
                home_team = None
                away_team = None
                for competitor in comp.get('competitors', []):
                    team_info = competitor.get('team', {})
                    team_name = team_info.get('displayName') or team_info.get('name', '')
                    location = (competitor.get('homeAway') or '').lower()
                    if location == 'home':
                        home_team = team_name
                    elif location == 'away':
                        away_team = team_name
                if home_team and away_team:
                    result = {'home': home_team, 'away': away_team}
    except requests.RequestException:
        pass

    _game_info_cache[cache_key] = {'data': result, 'time': time.time()}
    return result


# --- Upcoming game lookup ---
_upcoming_cache = {}
UPCOMING_CACHE_TTL = 6 * 60 * 60  # 6 hours


def get_upcoming_game(sport: str, league: str, team_name: str) -> dict:
    """
    Find the upcoming game for a team using ESPN's scoreboard.
    Looks 14 days ahead. Returns {'opponent': str, 'is_home': bool} or {}.
    """
    cache_key = f"{sport}:{league}:{team_name}"
    cached = _upcoming_cache.get(cache_key)
    if cached and (time.time() - cached['time']) < UPCOMING_CACHE_TTL:
        return cached['data']

    today = datetime.utcnow()
    end = today + timedelta(days=14)
    date_range = f"{today.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"

    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={date_range}"
    result = {}

    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            team_lower = team_name.lower()
            for event in data.get('events', []):
                comps = event.get('competitions', [])
                if not comps:
                    continue
                competitors = comps[0].get('competitors', [])
                for c in competitors:
                    team_info = c.get('team', {})
                    name = (team_info.get('name') or '').lower()
                    display = (team_info.get('displayName') or '').lower()
                    if team_lower in name or team_lower in display or (name and name in team_lower):
                        is_home = (c.get('homeAway') or '').lower() == 'home'
                        opponent = None
                        for other in competitors:
                            if other.get('id') != c.get('id'):
                                opp = other.get('team', {})
                                opponent = opp.get('displayName') or opp.get('name', '')
                                break
                        result = {'opponent': opponent or '', 'is_home': is_home}
                        break
                if result:
                    break
    except requests.RequestException:
        pass

    _upcoming_cache[cache_key] = {'data': result, 'time': time.time()}
    return result


# --- Injury status cache ---
_injury_cache = {}
INJURY_CACHE_TTL = 1800  # 30 minutes


def get_injury_status(sport: str, league: str, athlete_id: int) -> Optional[str]:
    """
    Fetches the injury status for a player from ESPN's injury report.
    Returns a string like 'OUT', 'QUESTIONABLE', 'DAY-TO-DAY', or None.
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

    def get_player_gamelog(self, sport: str, league: str, athlete_id: int, stat_map: dict, team_name: str = "") -> Optional[pd.DataFrame]:
        """
        Fetches a player's game-by-game log with persistent file cache.
        team_name: the player's team (e.g., "Packers"). Used to determine home/away.
        """
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
                events_meta = data.get('events', {})

                if not events_list:
                    return None

                # Prefer the passed-in team name; fall back to ESPN's metadata
                player_team = team_name
                if not player_team:
                    try:
                        team_obj = data.get('athlete', {}).get('team', {})
                        player_team = team_obj.get('name') or team_obj.get('displayName') or ""
                    except Exception:
                        pass

                rows = []
                for event in events_list:
                    event_id = str(event.get('eventId', ''))
                    stats = event.get('stats', [])

                    meta = events_meta.get(event_id, {})
                    if not meta:
                        alt = events_meta.get(int(event_id)) if event_id.isdigit() else None
                        if isinstance(alt, dict):
                            meta = alt

                    game_date = meta.get('gameDate') or event.get('gameDate')

                    # Defaults
                    home_away = "HOME"
                    opponent = None

                    # Use the game summary to get home/away + opponent
                    game_info = _get_game_info(sport, league, event_id)
                    if game_info and player_team:
                        p = player_team.lower()
                        h = game_info['home'].lower()
                        a = game_info['away'].lower()
                        if p in h or h in p:
                            home_away = "HOME"
                            opponent = game_info['away']
                        elif p in a or a in p:
                            home_away = "AWAY"
                            opponent = game_info['home']

                    row = {
                        'game_id': event_id,
                        'date': game_date,
                        'opponent': opponent,
                        'home_away': home_away,
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
                    result = self.get_player_gamelog(
                        sport, league, info["espn_id"], info["espn_stat_map"],
                        team_name=info.get("team", "")
                    )
                    if result is not None and not result.empty:
                        success += 1
                    else:
                        failed += 1
                    time.sleep(0.5)
            except Exception as e:
                failed += 1
                print(f"Refresh failed for {info.get('name', player_key)}: {e}")
        return success, failed