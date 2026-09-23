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
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    print(f"✅ Logged in as {client.user}!")
    print("✅ Slash commands synced to your server!")


@tree.command(name="ping", description="Test if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! The bot is online and working!")

@tree.command(name="roster", description="List all available players and their markets")
async def roster(interaction: discord.Interaction):
    await interaction.response.defer()
    
    # Group players by position based on their markets
    qbs = []
    wrs = []
    rbs = []
    
    for key, info in PLAYERS.items():
        markets = [m["display"] for m in info["markets"]]
        entry = f"`{key}` — {info['name']} ({info['team']})"
        
        # Determine position by checking market types
        market_keys = [m["key"] for m in info["markets"]]
        if "player_pass_yds" in market_keys:
            qbs.append(entry)
        elif "player_rush_yds" in market_keys:
            rbs.append(entry)
        else:
            wrs.append(entry)
    
    embed = discord.Embed(
        title="📋 Available Players",
        description=f"Use `/props player:<name>` to analyze any player.\nTotal roster: **{len(PLAYERS)} players**",
        color=0x3498db
    )
    
    if qbs:
        embed.add_field(
            name=f"🏈 Quarterbacks ({len(qbs)})",
            value="\n".join(qbs) if qbs else "None",
            inline=False
        )
    if wrs:
        embed.add_field(
            name=f"🏃 Wide Receivers ({len(wrs)})",
            value="\n".join(wrs) if wrs else "None",
            inline=False
        )
    if rbs:
        embed.add_field(
            name=f"💨 Running Backs ({len(rbs)})",
            value="\n".join(rbs) if rbs else "None",
            inline=False
        )
    
    embed.set_footer(text="More players coming soon | Data from ESPN & PropLine")
    await interaction.followup.send(embed=embed)

@tree.command(name="props", description="Get NFL player prop analysis")
@app_commands.describe(player="Player name (e.g., jordan_love, justin_jefferson)")
async def props(interaction: discord.Interaction, player: str):
    await interaction.response.defer()
    
    player_key = player.lower()
    if player_key not in PLAYERS:
        await interaction.followup.send(f"❌ Player not found. Try one of these: {', '.join(PLAYERS.keys())}")
        return

    player_info = PLAYERS[player_key]
    player_name = player_info["name"]
    
    # --- 1. Fetch ESPN Stats ---
    espn = ESPNClient()
    data = espn.get_player_gamelog('football', 'nfl', player_info["espn_id"], player_info["espn_stat_map"])
    
    if data is None or data.empty:
        await interaction.followup.send("❌ Could not fetch player data from ESPN.")
        return
    
    # Sample size guard
    if len(data) < 3:
        await interaction.followup.send(
            f"⚠️ {player_name} only has {len(data)} game(s) on record. "
            f"Not enough data for a reliable prediction. Try again after they've played more games."
        )
        return
    
    # --- 2. Build an embed and loop through each market ---
    odds_client = OddsClient()
    
    embed = discord.Embed(
        title=f"{player_name} - NFL Prop Analysis",
        description=f"Team: {player_info['team']} | Based on last 5 games",
        color=0x00ff00
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
            player_name, player_info["team"], market["key"]
        )
        
        if available_lines:
            closest_line = min(available_lines, key=lambda x: abs(x['line'] - avg_stat))
            line_value = closest_line['line']
            odds_display = f"{closest_line['price']}"
            recommendation = "OVER" if avg_stat > line_value else "UNDER"
            edge = abs(avg_stat - line_value)
            
            field_value = (
                f"Avg: **{avg_stat:.1f}** | Line: **{line_value}+** | Odds: **{odds_display}**\n"
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


if __name__ == "__main__":
    client.run(TOKEN)