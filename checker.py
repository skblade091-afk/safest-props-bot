"""
Resolves pending predictions by fetching actual results from ESPN.
"""

import requests
from datetime import datetime
from tracker import get_pending_predictions, resolve_prediction

ESPN_BASE = "https://site.web.api.espn.com/apis/common/v3/sports"


def _fetch_raw_gamelog(sport: str, league: str, athlete_id: int):
    """Fetch the raw ESPN gamelog (list of events with raw stats)."""
    url = f"{ESPN_BASE}/{sport}/{league}/athletes/{athlete_id}/gamelog"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get('seasonTypes', [{}])[0].get('categories', [{}])[0].get('events', [])
    except requests.RequestException:
        return []


def _get_stat_index(sport: str, stat_key: str, players_dict: dict, espn_id: int):
    """Look up the ESPN array index for this stat by finding the player in the roster."""
    for info in players_dict.values():
        if info["espn_id"] == espn_id:
            return info["espn_stat_map"].get(stat_key)
    return None


def _parse_timestamp(ts: str):
    """Parse ISO timestamp from DB (UTC)."""
    try:
        # Remove 'Z' suffix if present and parse
        ts = ts.replace("Z", "")
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def check_pending_predictions(players_dict_nfl: dict, players_dict_nba: dict, grace_hours: int = 3):
    """
    Check all pending predictions. Only tries to resolve ones
    made more than `grace_hours` ago (gives the game time to finish).
    Returns (resolved_count, still_pending_count, errors_count).
    """
    pending = get_pending_predictions()
    if not pending:
        return (0, 0, 0)
    
    now = datetime.utcnow()
    resolved = 0
    still_pending = 0
    errors = 0
    
    # Group by player to avoid repeat ESPN calls
    by_player = {}
    for pred in pending:
        # Skip predictions made too recently
        pred_time = _parse_timestamp(pred["timestamp"])
        if pred_time and (now - pred_time).total_seconds() < grace_hours * 3600:
            still_pending += 1
            continue
        
        key = (pred["sport"], pred["espn_id"])
        by_player.setdefault(key, []).append(pred)
    
    # Process each player
    for (sport_league, espn_id), preds in by_player.items():
        # sport_league is "nfl" or "nba" — map to ESPN paths
        if sport_league == "nfl":
            espn_sport, espn_league = "football", "nfl"
            roster = players_dict_nfl
        elif sport_league == "nba":
            espn_sport, espn_league = "basketball", "nba"
            roster = players_dict_nba
        else:
            still_pending += len(preds)
            continue
        
        events = _fetch_raw_gamelog(espn_sport, espn_league, espn_id)
        if not events:
            still_pending += len(preds)
            continue
        
        for pred in preds:
            pred_time = _parse_timestamp(pred["timestamp"])
            if not pred_time:
                still_pending += 1
                continue
            
            stat_index = _get_stat_index(sport_league, pred["stat_key"], roster, espn_id)
            if stat_index is None:
                errors += 1
                continue
            
            # Find the first game after the prediction timestamp
            target_game = None
            for event in events:
                game_date_str = event.get('gameDate', '')
                if not game_date_str:
                    continue
                game_date = _parse_timestamp(game_date_str)
                if game_date and game_date > pred_time:
                    # Keep earliest game after prediction
                    if target_game is None or game_date < _parse_timestamp(target_game.get('gameDate', '')):
                        target_game = event
            
            if not target_game:
                still_pending += 1
                continue
            
            # Extract actual stat value
            stats = target_game.get('stats', [])
            try:
                raw_value = stats[stat_index] if stat_index < len(stats) else None
                if raw_value is None or raw_value == '' or raw_value == '-':
                    # Player didn't play — leave pending
                    still_pending += 1
                    continue
                # Handle "8-18" style values
                if isinstance(raw_value, str) and '-' in raw_value:
                    raw_value = raw_value.split('-')[0]
                actual_value = float(raw_value)
            except (ValueError, IndexError):
                still_pending += 1
                continue
            
            # Resolve!
            try:
                result = resolve_prediction(pred["id"], actual_value)
                if result:
                    resolved += 1
                    print(f"  Resolved: {pred['player_name']} {pred['market_display']} "
                          f"(projected {pred['projection']:.1f}, line {pred['line']}, "
                          f"actual {actual_value:.1f}) → {result}")
                else:
                    errors += 1
            except Exception as e:
                print(f"  Error resolving prediction {pred['id']}: {e}")
                errors += 1
    
    return (resolved, still_pending, errors)