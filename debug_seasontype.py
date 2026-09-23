import requests

# Test with seasontype=2 (regular season)
for player_id, name in [(4241457, "Justin Herbert"), (4241470, "Tua Tagovailoa")]:
    print(f"\n=== {name} ===")
    
    # Try with seasontype=2 explicitly for regular season
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{player_id}/gamelog?seasontype=2"
    response = requests.get(url)
    data = response.json()
    
    # Check what season types are actually available
    print("Season types available:")
    for st in data.get('seasonTypes', []):
        print(f"  - {st.get('displayName')} (id: {st.get('seasonTypeId')})")
    
    # Get the events from the first season type
    events = data.get('seasonTypes', [{}])[0].get('categories', [{}])[0].get('events', [])
    print(f"Number of games: {len(events)}")
    for event in events[-3:]:
        print(f"  Stats: {event.get('stats')}")