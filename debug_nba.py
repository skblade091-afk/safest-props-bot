import requests

# LeBron James NBA gamelog
url = "https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/1966/gamelog"
response = requests.get(url)
data = response.json()
events = data.get('seasonTypes', [{}])[0].get('categories', [{}])[0].get('events', [])
if events:
    print("LeBron James last game raw stats:")
    print(events[-1].get('stats'))
else:
    print("No events found.")
    