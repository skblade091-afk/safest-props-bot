import requests

# Check all the new QBs
qbs = [
    (4241457, "Justin Herbert"),
    (2577417, "Dak Prescott"),
    (4040715, "Jalen Hurts"),
    (4361741, "Brock Purdy"),
    (4241470, "Tua Tagovailoa"),
]

for player_id, name in qbs:
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{player_id}/gamelog"
    response = requests.get(url)
    data = response.json()
    events = data.get('seasonTypes', [{}])[0].get('categories', [{}])[0].get('events', [])
    print(f"\n=== {name} (ID {player_id}) ===")
    if events:
        # Show last 5 games
        for event in events[-5:]:
            stats = event.get('stats', [])
            print(f"  Stats: {stats}")
    else:
        print("  No events found.")
        