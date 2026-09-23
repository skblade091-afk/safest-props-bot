import requests
import pandas as pd
from typing import Optional

class ESPNClient:
    BASE_URL = "https://site.web.api.espn.com/apis/common/v3/sports"

    def get_player_gamelog(self, sport: str, league: str, athlete_id: int, stat_map: dict) -> Optional[pd.DataFrame]:
        """
        Fetches a player's game-by-game log and extracts stats based on the stat_map.
        Example: stat_map = {"pass_yds": 2, "pass_td": 5} for NFL QBs
        """
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
                # Loop through the stat_map and safely pull the requested stats
                for stat_name, stat_index in stat_map.items():
                    try:
                        if stat_index < len(stats) and stats[stat_index]:
                            row[stat_name] = float(stats[stat_index])
                        else:
                            row[stat_name] = 0
                    except (ValueError, IndexError):
                        row[stat_name] = 0
                rows.append(row)
            return pd.DataFrame(rows)
        except requests.RequestException as e:
            print(f"Error fetching gamelog for {athlete_id}: {e}")
            return None