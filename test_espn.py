from espn_client import ESPNClient

client = ESPNClient()
data = client.get_player_gamelog('basketball', 'nba', 1966)
print(data.tail())
