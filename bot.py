import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from espn_client import ESPNClient
from odds_client import OddsClient

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# Player database: name, team, ESPN ID, market key, and ESPN stat_map
PLAYERS = {
    # --- QBs: Passing Yards + Passing TDs ---
    "jordan_love": {
        "name": "Jordan Love", "team": "Packers", "espn_id": 4036378,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "patrick_mahomes": {
        "name": "Patrick Mahomes", "team": "Chiefs", "espn_id": 3139477,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "josh_allen": {
        "name": "Josh Allen", "team": "Bills", "espn_id": 3918298,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "lamar_jackson": {
        "name": "Lamar Jackson", "team": "Ravens", "espn_id": 3916387,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "joe_burrow": {
        "name": "Joe Burrow", "team": "Bengals", "espn_id": 3915511,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "justin_herbert": {
        "name": "Justin Herbert", "team": "Chargers", "espn_id": 4241457,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "dak_prescott": {
        "name": "Dak Prescott", "team": "Cowboys", "espn_id": 2577417,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "jalen_hurts": {
        "name": "Jalen Hurts", "team": "Eagles", "espn_id": 4040715,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "brock_purdy": {
        "name": "Brock Purdy", "team": "49ers", "espn_id": 4361741,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "tua_tagovailoa": {
        "name": "Tua Tagovailoa", "team": "Dolphins", "espn_id": 4241470,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "trevor_lawrence": {
        "name": "Trevor Lawrence", "team": "Jaguars", "espn_id": 4360310,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "kyler_murray": {
        "name": "Kyler Murray", "team": "Cardinals", "espn_id": 3917315,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "jared_goff": {
        "name": "Jared Goff", "team": "Lions", "espn_id": 3046779,
        "markets": [
            {"key": "player_pass_yds", "stat": "pass_yds", "display": "Passing Yards"},
            {"key": "player_pass_tds", "stat": "pass_td", "display": "Passing TDs"},
        ],
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },

    # --- WRs: Receiving Yards + Receptions ---
    "justin_jefferson": {
        "name": "Justin Jefferson", "team": "Vikings", "espn_id": 4241478,
        "markets": [
            {"key": "player_reception_yds", "stat": "rec_yds", "display": "Receiving Yards"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "ceedee_lamb": {
        "name": "CeeDee Lamb", "team": "Cowboys", "espn_id": 4241389,
        "markets": [
            {"key": "player_reception_yds", "stat": "rec_yds", "display": "Receiving Yards"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "tyreek_hill": {
        "name": "Tyreek Hill", "team": "Dolphins", "espn_id": 3116406,
        "markets": [
            {"key": "player_reception_yds", "stat": "rec_yds", "display": "Receiving Yards"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "aj_brown": {
        "name": "A.J. Brown", "team": "Eagles", "espn_id": 4047658,
        "markets": [
            {"key": "player_reception_yds", "stat": "rec_yds", "display": "Receiving Yards"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "jamarr_chase": {
        "name": "Ja'Marr Chase", "team": "Bengals", "espn_id": 4362628,
        "markets": [
            {"key": "player_reception_yds", "stat": "rec_yds", "display": "Receiving Yards"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "amonra_stbrown": {
        "name": "Amon-Ra St. Brown", "team": "Lions", "espn_id": 4374302,
        "markets": [
            {"key": "player_reception_yds", "stat": "rec_yds", "display": "Receiving Yards"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "davante_adams": {
        "name": "Davante Adams", "team": "Raiders", "espn_id": 16800,
        "markets": [
            {"key": "player_reception_yds", "stat": "rec_yds", "display": "Receiving Yards"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "cooper_kupp": {
        "name": "Cooper Kupp", "team": "Rams", "espn_id": 3054211,
        "markets": [
            {"key": "player_reception_yds", "stat": "rec_yds", "display": "Receiving Yards"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },

    # --- RBs: Rushing Yards + Rushing TDs + Receptions ---
    "christian_mccaffrey": {
        "name": "Christian McCaffrey", "team": "49ers", "espn_id": 3117251,
        "markets": [
            {"key": "player_rush_yds", "stat": "rush_yds", "display": "Rushing Yards"},
            {"key": "player_rush_tds", "stat": "rush_td", "display": "Rushing TDs"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rush_yds": 1, "rush_td": 3, "receptions": 5}
    },
    "saquon_barkley": {
        "name": "Saquon Barkley", "team": "Eagles", "espn_id": 3929630,
        "markets": [
            {"key": "player_rush_yds", "stat": "rush_yds", "display": "Rushing Yards"},
            {"key": "player_rush_tds", "stat": "rush_td", "display": "Rushing TDs"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rush_yds": 1, "rush_td": 3, "receptions": 5}
    },
    "derrick_henry": {
        "name": "Derrick Henry", "team": "Ravens", "espn_id": 3043078,
        "markets": [
            {"key": "player_rush_yds", "stat": "rush_yds", "display": "Rushing Yards"},
            {"key": "player_rush_tds", "stat": "rush_td", "display": "Rushing TDs"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rush_yds": 1, "rush_td": 3, "receptions": 5}
    },
    "bijan_robinson": {
        "name": "Bijan Robinson", "team": "Falcons", "espn_id": 4430807,
        "markets": [
            {"key": "player_rush_yds", "stat": "rush_yds", "display": "Rushing Yards"},
            {"key": "player_rush_tds", "stat": "rush_td", "display": "Rushing TDs"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rush_yds": 1, "rush_td": 3, "receptions": 5}
    },
    "josh_jacobs": {
        "name": "Josh Jacobs", "team": "Packers", "espn_id": 4047646,
        "markets": [
            {"key": "player_rush_yds", "stat": "rush_yds", "display": "Rushing Yards"},
            {"key": "player_rush_tds", "stat": "rush_td", "display": "Rushing TDs"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rush_yds": 1, "rush_td": 3, "receptions": 5}
    },
    "travis_etienne": {
        "name": "Travis Etienne", "team": "Jaguars", "espn_id": 4241462,
        "markets": [
            {"key": "player_rush_yds", "stat": "rush_yds", "display": "Rushing Yards"},
            {"key": "player_rush_tds", "stat": "rush_td", "display": "Rushing TDs"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rush_yds": 1, "rush_td": 3, "receptions": 5}
    },
    "james_cook": {
        "name": "James Cook", "team": "Bills", "espn_id": 4379394,
        "markets": [
            {"key": "player_rush_yds", "stat": "rush_yds", "display": "Rushing Yards"},
            {"key": "player_rush_tds", "stat": "rush_td", "display": "Rushing TDs"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rush_yds": 1, "rush_td": 3, "receptions": 5}
    },
    "jahmyr_gibbs": {
        "name": "Jahmyr Gibbs", "team": "Lions", "espn_id": 4429795,
        "markets": [
            {"key": "player_rush_yds", "stat": "rush_yds", "display": "Rushing Yards"},
            {"key": "player_rush_tds", "stat": "rush_td", "display": "Rushing TDs"},
            {"key": "player_receptions", "stat": "receptions", "display": "Receptions"},
        ],
        "espn_stat_map": {"rush_yds": 1, "rush_td": 3, "receptions": 5}
    },
}

    # --- NBA Player database ---
NBA_PLAYERS = {
    "lebron": {
        "name": "LeBron James", "team": "Lakers", "espn_id": 1966,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
    "curry": {
        "name": "Stephen Curry", "team": "Warriors", "espn_id": 3975,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
    "luka": {
        "name": "Luka Doncic", "team": "Lakers", "espn_id": 3945274,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
    "jokic": {
        "name": "Nikola Jokic", "team": "Nuggets", "espn_id": 3112335,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
    "giannis": {
        "name": "Giannis Antetokounmpo", "team": "Bucks", "espn_id": 3032977,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
    "tatum": {
        "name": "Jayson Tatum", "team": "Celtics", "espn_id": 4065648,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
    "embiid": {
        "name": "Joel Embiid", "team": "76ers", "espn_id": 3059318,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
    "durant": {
        "name": "Kevin Durant", "team": "Suns", "espn_id": 3202,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
    "booker": {
        "name": "Devin Booker", "team": "Suns", "espn_id": 3136195,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
    "anthony_davis": {
        "name": "Anthony Davis", "team": "Lakers", "espn_id": 3059674,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"min": 0, "reb": 4, "ast": 5, "pts": 10}
    },
}

# --- Discord client setup ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# --- Bot events ---
@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    print(f"✅ Logged in as {client.user}!")
    print("✅ Slash commands synced to your server!")


# --- Commands ---
@tree.command(name="ping", description="Test if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! The bot is online and working!")


@tree.command(name="roster", description="List all available players and their markets")
async def roster(interaction: discord.Interaction):
    await interaction.response.defer()
    
    # NFL players
    nfl_qbs, nfl_wrs, nfl_rbs = [], [], []
    for key, info in PLAYERS.items():
        entry = f"`{key}` — {info['name']} ({info['team']})"
        market_keys = [m["key"] for m in info["markets"]]
        if "player_pass_yds" in market_keys:
            nfl_qbs.append(entry)
        elif "player_rush_yds" in market_keys:
            nfl_rbs.append(entry)
        else:
            nfl_wrs.append(entry)
    
    # NBA players
    nba_entries = [f"`{key}` — {info['name']} ({info['team']})" for key, info in NBA_PLAYERS.items()]
    
    embed = discord.Embed(
        title="📋 Available Players",
        description=f"NFL: **{len(PLAYERS)}** | NBA: **{len(NBA_PLAYERS)}**",
        color=0x3498db
    )
    
    if nfl_qbs:
        embed.add_field(name=f"🏈 NFL QBs ({len(nfl_qbs)})", value="\n".join(nfl_qbs), inline=False)
    if nfl_wrs:
        embed.add_field(name=f"🏈 NFL WRs ({len(nfl_wrs)})", value="\n".join(nfl_wrs), inline=False)
    if nfl_rbs:
        embed.add_field(name=f"🏈 NFL RBs ({len(nfl_rbs)})", value="\n".join(nfl_rbs), inline=False)
    if nba_entries:
        embed.add_field(name=f"🏀 NBA Players ({len(nba_entries)})", value="\n".join(nba_entries), inline=False)
    
    embed.set_footer(text="Use /props player:<name> to analyze | Data from ESPN & PropLine")
    await interaction.followup.send(embed=embed)


@tree.command(name="props", description="Get player prop analysis (NFL or NBA)")
@app_commands.describe(player="Player name (e.g., jordan_love, lebron, curry, luka)")
async def props(interaction: discord.Interaction, player: str):
    await interaction.response.defer()
    
    player_key = player.lower()
    
    # Check both NFL and NBA rosters
    if player_key in PLAYERS:
        player_info = PLAYERS[player_key]
        sport_key = "americanfootball_nfl"
        espn_sport = "football"
        espn_league = "nfl"
        league_label = "NFL"
    elif player_key in NBA_PLAYERS:
        player_info = NBA_PLAYERS[player_key]
        sport_key = "basketball_nba"
        espn_sport = "basketball"
        espn_league = "nba"
        league_label = "NBA"
    else:
        await interaction.followup.send(f"❌ Player not found. Try `/roster` to see all players.")
        return

    player_name = player_info["name"]
    
    espn = ESPNClient()
    data = espn.get_player_gamelog(espn_sport, espn_league, player_info["espn_id"], player_info["espn_stat_map"])
    
    if data is None or data.empty:
        await interaction.followup.send("❌ Could not fetch player data from ESPN.")
        return
    
    if len(data) < 3:
        await interaction.followup.send(
            f"⚠️ {player_name} only has {len(data)} game(s) on record. "
            f"Not enough data for a reliable prediction. Try again after they've played more games."
        )
        return
    
    odds_client = OddsClient()
    
    embed = discord.Embed(
        title=f"{player_name} - {league_label} Prop Analysis",
        description=f"Team: {player_info['team']} | Based on last 5 games",
        color=0x00ff00 if league_label == "NFL" else 0xff6b00
    )
    
    for market in player_info["markets"]:
        stat_key = market["stat"]
        display_name = market["display"]
        
        if stat_key not in data.columns:
            continue
        
        recent_games = data[stat_key].tail(5)
        avg_stat = recent_games.mean()
        
        if len(recent_games) < 3:
            continue
        
        available_lines = odds_client.get_player_props(
            player_name, player_info["team"], market["key"], sport_key
        )
        
        if available_lines:
            closest_line = min(available_lines, key=lambda x: abs(x['line'] - avg_stat))
            line_value = closest_line['line']
            odds_display = f"{closest_line['price']}"
            recommendation = "OVER" if avg_stat > line_value else "UNDER"
            edge = abs(avg_stat - line_value)
            
            field_value = (
                f"Avg: **{avg_stat:.1f}** | Line: **{line_value}** | Odds: **{odds_display}**\n"
                f"→ **{recommendation}** (Edge: {edge:.1f})"
            )
        else:
            line_value = round(avg_stat * 2) / 2
            field_value = (
                f"Avg: **{avg_stat:.1f}** | Line: **{line_value}** *(estimated)*\n"
                f"→ No live odds available"
            )
        
        embed.add_field(name=display_name, value=field_value, inline=False)
    
    if len(embed.fields) == 0:
        await interaction.followup.send(f"❌ No market data available for {player_name} yet.")
        return
    
    embed.set_footer(text="Data from ESPN & PropLine | Bet responsibly.")
    await interaction.followup.send(embed=embed)


@tree.command(name="top", description="Scan all players and show today's top prop picks")
async def top(interaction: discord.Interaction):
    await interaction.response.defer()
    
    await interaction.followup.send("🔍 Scanning all players... This takes about 30 seconds.")
    
    espn = ESPNClient()
    odds_client = OddsClient()
    results = []
    
    for player_key, info in PLAYERS.items():
        player_name = info["name"]
        
        try:
            data = espn.get_player_gamelog('football', 'nfl', info["espn_id"], info["espn_stat_map"])
            
            if data is None or data.empty or len(data) < 2:
                continue
            
            primary_market = info["markets"][0]
            stat_key = primary_market["stat"]
            display_name = primary_market["display"]
            
            if stat_key not in data.columns:
                continue
            
            recent_games = data[stat_key].tail(5)
            avg_stat = recent_games.mean()
            
            available_lines = odds_client.get_player_props(
                player_name, info["team"], primary_market["key"]
            )
            
            if not available_lines:
                continue
            
            closest_line = min(available_lines, key=lambda x: abs(x['line'] - avg_stat))
            line_value = closest_line['line']
            price = closest_line['price']
            
            edge = avg_stat - line_value
            recommendation = "OVER" if edge > 0 else "UNDER"
            
            results.append({
                "player": player_name,
                "market": display_name,
                "avg": avg_stat,
                "line": line_value,
                "price": price,
                "edge": edge,
                "recommendation": recommendation,
                "abs_edge": abs(edge)
            })
        except Exception as e:
            print(f"Error processing {player_name}: {e}")
            continue
    
    if not results:
        await interaction.followup.send("❌ No props with live odds available right now. Try again closer to game time.")
        return
    
    results.sort(key=lambda x: x["abs_edge"], reverse=True)
    top_picks = results[:5]
    
    embed = discord.Embed(
        title="🏆 Today's Top 5 Prop Picks",
        description=f"Scanned {len(PLAYERS)} players, found {len(results)} with live odds",
        color=0xffd700
    )
    
    for i, pick in enumerate(top_picks, 1):
        color_emoji = "🟢" if pick["recommendation"] == "OVER" else "🔴"
        field_name = f"{color_emoji} #{i} {pick['player']} — {pick['market']}"
        field_value = (
            f"Avg: **{pick['avg']:.1f}** vs Line: **{pick['line']}+** | Odds: **{pick['price']}**\n"
            f"→ **{pick['recommendation']}** (Edge: {pick['edge']:+.1f})"
        )
        embed.add_field(name=field_name, value=field_value, inline=False)
    
    embed.set_footer(text="Data from ESPN & PropLine | Bet responsibly.")
    await interaction.followup.send(embed=embed)


if __name__ == "__main__":
    client.run(TOKEN)