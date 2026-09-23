import requests

# Jordan Love's ESPN ID is 4036378
url = "https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/4036378/gamelog"
response = requests.get(url)
data = response.json()

# Navigate to the events
events = data.get('seasonTypes', [{}])[0].get('categories', [{}])[0].get('events', [])

if events:
    print("RAW STATS ARRAY FOR JORDAN LOVE'S LAST GAME:")
    print(events[-1].get('stats'))
else:
    print("No events found.")