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
    "jordan_love": {
        "name": "Jordan Love", "team": "Packers", "espn_id": 4036378,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "patrick_mahomes": {
        "name": "Patrick Mahomes", "team": "Chiefs", "espn_id": 3139477,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "josh_allen": {
        "name": "Josh Allen", "team": "Bills", "espn_id": 3918298,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "lamar_jackson": {
        "name": "Lamar Jackson", "team": "Ravens", "espn_id": 3916387,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "joe_burrow": {
        "name": "Joe Burrow", "team": "Bengals", "espn_id": 3915511,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "justin_jefferson": {
        "name": "Justin Jefferson", "team": "Vikings", "espn_id": 4241478,
        "market": "player_reception_yds",
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "ceedee_lamb": {
        "name": "CeeDee Lamb", "team": "Cowboys", "espn_id": 4241389,
        "market": "player_reception_yds",
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "tyreek_hill": {
        "name": "Tyreek Hill", "team": "Dolphins", "espn_id": 3116406,
        "market": "player_reception_yds",
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "christian_mccaffrey": {
        "name": "Christian McCaffrey", "team": "49ers", "espn_id": 3117251,
        "market": "player_rush_yds",
        "espn_stat_map": {"rush_yds": 1, "rush_att": 0}
    },
    "saquon_barkley": {
        "name": "Saquon Barkley", "team": "Eagles", "espn_id": 3929630,
        "market": "player_rush_yds",
        "espn_stat_map": {"rush_yds": 1, "rush_att": 0}
    },
    "justin_herbert": {
        "name": "Justin Herbert", "team": "Chargers", "espn_id": 4241457,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "dak_prescott": {
        "name": "Dak Prescott", "team": "Cowboys", "espn_id": 2577417,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "jalen_hurts": {
        "name": "Jalen Hurts", "team": "Eagles", "espn_id": 4040715,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "brock_purdy": {
        "name": "Brock Purdy", "team": "49ers", "espn_id": 4361741,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "tua_tagovailoa": {
        "name": "Tua Tagovailoa", "team": "Dolphins", "espn_id": 4241470,
        "market": "player_pass_yds",
        "espn_stat_map": {"pass_yds": 2, "pass_td": 5}
    },
    "aj_brown": {
        "name": "A.J. Brown", "team": "Eagles", "espn_id": 4047658,
        "market": "player_reception_yds",
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "jamarr_chase": {
        "name": "Ja'Marr Chase", "team": "Bengals", "espn_id": 4362628,
        "market": "player_reception_yds",
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "amonra_stbrown": {
        "name": "Amon-Ra St. Brown", "team": "Lions", "espn_id": 4374302,
        "market": "player_reception_yds",
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "davante_adams": {
        "name": "Davante Adams", "team": "Raiders", "espn_id": 16800,
        "market": "player_reception_yds",
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "cooper_kupp": {
        "name": "Cooper Kupp", "team": "Rams", "espn_id": 3054211,
        "market": "player_reception_yds",
        "espn_stat_map": {"rec_yds": 2, "receptions": 0}
    },
    "derrick_henry": {
        "name": "Derrick Henry", "team": "Ravens", "espn_id": 3043078,
        "market": "player_rush_yds",
        "espn_stat_map": {"rush_yds": 1, "rush_att": 0}
    },
    "bijan_robinson": {
        "name": "Bijan Robinson", "team": "Falcons", "espn_id": 4430807,
        "market": "player_rush_yds",
        "espn_stat_map": {"rush_yds": 1, "rush_att": 0}
    },
    "josh_jacobs": {
        "name": "Josh Jacobs", "team": "Packers", "espn_id": 4047646,
        "market": "player_rush_yds",
        "espn_stat_map": {"rush_yds": 1, "rush_att": 0}
    },
    "travis_etienne": {
        "name": "Travis Etienne", "team": "Jaguars", "espn_id": 4241462,
        "market": "player_rush_yds",
        "espn_stat_map": {"rush_yds": 1, "rush_att": 0}
    },
    "james_cook": {
        "name": "James Cook", "team": "Bills", "espn_id": 4379394,
        "market": "player_rush_yds",
        "espn_stat_map": {"rush_yds": 1, "rush_att": 0}
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


@tree.command(name="props", description="Get NFL player prop analysis")
@app_commands.describe(player="Player name (e.g., jordan_love, patrick_mahomes, josh_allen)")
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
    
    stat_key = list(player_info["espn_stat_map"].keys())[0]
    avg_stat = data[stat_key].tail(5).mean()

    # --- 2. Try to fetch real odds from PropLine ---
    odds_client = OddsClient()
    available_lines = odds_client.get_player_props(player_name, player_info["team"], player_info["market"])
    
    # --- 3. Determine the line: real or estimated ---
    if available_lines:
        closest_line = min(available_lines, key=lambda x: abs(x['line'] - avg_stat))
        line_value = closest_line['line']
        odds_display = f"{closest_line['price']}"
        line_label = f"{line_value}+"
        is_estimated = False
    else:
        line_value = round(avg_stat * 2) / 2
        odds_display = "N/A"
        line_label = f"{line_value} (estimated)"
        is_estimated = True
    
    recommendation = "OVER" if avg_stat > line_value else "UNDER"
    edge = abs(avg_stat - line_value)
    
    # --- 4. Create the Embed ---
    stat_display_map = {
        "pass_yds": "Passing Yards",
        "rec_yds": "Receiving Yards",
        "rush_yds": "Rushing Yards",
    }
    stat_display = stat_display_map.get(stat_key, stat_key.replace('_', ' ').title())
    
    if is_estimated:
        embed_color = 0xffa500
    else:
        embed_color = 0x00ff00 if recommendation == "OVER" else 0xff0000
    
    embed = discord.Embed(
        title=f"{player_name} - NFL Prop Analysis",
        description=f"Market: {stat_display}",
        color=embed_color
    )
    embed.add_field(name=f"Recent Avg ({stat_display})", value=f"{avg_stat:.1f}", inline=True)
    embed.add_field(name="Line", value=line_label, inline=True)
    embed.add_field(name="Odds", value=odds_display, inline=True)
    embed.add_field(name="Recommendation", value=f"**{recommendation}** (Edge: {edge:.1f})", inline=True)
    
    if is_estimated:
        embed.set_footer(text="📊 Estimated line — live odds unavailable. Check back closer to game time.")
    else:
        embed.set_footer(text="✅ Live odds from PropLine | Data from ESPN | Bet responsibly.")
    
    await interaction.followup.send(embed=embed)


if __name__ == "__main__":
    client.run(TOKEN)