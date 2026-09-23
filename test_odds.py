import requests
import os
from dotenv import load_dotenv
import json
from datetime import date

load_dotenv()
API_KEY = os.getenv("ODDS_API_KEY")

# 1. Use the correct v1 endpoint, not v2
url = "https://api.sportsgameodds.com/v1/events/"

# 2. Get today's date in the format the API needs (YYYY-MM-DD)
today = date.today().isoformat()

# 3. Use the correct parameters: 'league', 'dateFrom', and 'dateTo'
params = {
    "apiKey": API_KEY,
    "league": "NBA",  # Use 'league' instead of 'sport'
    "dateFrom": today,
    "dateTo": today,
    "limit": 10  # Let's limit it to 10 results so it's not a huge file
}

try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()  # This will now catch the error properly
    data = response.json()
    
    # Print the raw JSON so we can see the structure
    print(json.dumps(data, indent=2)[:3000])
    print("\n--- END OF PREVIEW ---")
    
except requests.RequestException as e:
    print(f"Error fetching odds: {e}")