import requests

# Try fetching Herbert's gamelog with seasontype=2 (regular season)
player_id = 4241457
url = f"https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/{player_id}/gamelog?seasontype=2"
response = requests.get(url)
data = response.json()

# Check what season types are available
print("Season types in response:")
for st in data.get('seasonTypes', []):
    print(f"  - {st.get('displayName', 'unknown')} (id: {st.get('seasonTypeId')})")

# Now get events
events = data.get('seasonTypes', [{}])[0].get('categories', [{}])[0].get('events', [])
print(f"\nJustin Herbert stats with seasontype=2:")
for event in events[-5:]:
    print(f"  {event.get('stats')}")