import requests

# Test with Justin Jefferson (WR) and Christian McCaffrey (RB)
for player_id, name in [(4241478, "Justin Jefferson"), (3117251, "Christian McCaffrey")]:
    url = f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{player_id}/gamelog"
    response = requests.get(url)
    data = response.json()
    events = data.get('seasonTypes', [{}])[0].get('categories', [{}])[0].get('events', [])
    if events:
        print(f"\n{name} - Raw stats from last game:")
        print(events[-1].get('stats'))
    else:
        print(f"\n{name} - No events found.")