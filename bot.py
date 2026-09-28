import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
import os
from dotenv import load_dotenv
from espn_client import ESPNClient
from odds_client import OddsClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from tracker import save_prediction
from checker import check_pending_predictions
import asyncio

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

# ============================================================
# NFL PLAYER DATABASE
# ============================================================
PLAYERS = {
    # --- QBs ---
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

    # --- WRs ---
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

    # --- RBs ---
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

# ============================================================
# NBA PLAYER DATABASE (corrected stat indices: reb=7, ast=8, pts=13)
# ============================================================
NBA_PLAYERS = {
    "lebron": {
        "name": "LeBron James", "team": "Lakers", "espn_id": 1966,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
    "curry": {
        "name": "Stephen Curry", "team": "Warriors", "espn_id": 3975,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
    "luka": {
        "name": "Luka Doncic", "team": "Lakers", "espn_id": 3945274,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
    "jokic": {
        "name": "Nikola Jokic", "team": "Nuggets", "espn_id": 3112335,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
    "giannis": {
        "name": "Giannis Antetokounmpo", "team": "Bucks", "espn_id": 3032977,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
    "tatum": {
        "name": "Jayson Tatum", "team": "Celtics", "espn_id": 4065648,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
    "embiid": {
        "name": "Joel Embiid", "team": "76ers", "espn_id": 3059318,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
    "durant": {
        "name": "Kevin Durant", "team": "Suns", "espn_id": 3202,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
    "booker": {
        "name": "Devin Booker", "team": "Suns", "espn_id": 3136195,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
    "anthony_davis": {
        "name": "Anthony Davis", "team": "Lakers", "espn_id": 3059674,
        "markets": [
            {"key": "player_points", "stat": "pts", "display": "Points"},
            {"key": "player_rebounds", "stat": "reb", "display": "Rebounds"},
            {"key": "player_assists", "stat": "ast", "display": "Assists"},
        ],
        "espn_stat_map": {"reb": 7, "ast": 8, "pts": 13}
    },
}

# --- Discord client setup ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


# --- Commands ---
@tree.command(name="ping", description="Test if the bot is online")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! The bot is online and working!")

@tree.command(name="dbcount", description="[Dev] Check how many predictions are in the database")
async def dbcount(interaction: discord.Interaction):
    await interaction.response.defer()
    from tracker import _get_connection
    conn = _get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM predictions").fetchone()["c"]
        pending = conn.execute("SELECT COUNT(*) as c FROM predictions WHERE result = 'PENDING'").fetchone()["c"]
        await interaction.followup.send(f"📊 Total predictions: **{total}** | Pending: **{pending}**")
    finally:
        conn.close()

@tree.command(name="checkresults", description="[Dev] Manually check pending predictions for results")
async def checkresults(interaction: discord.Interaction):
    await interaction.response.defer()
    
    # Use grace_hours=0 for manual test — check immediately
    resolved, pending, errors = check_pending_predictions(PLAYERS, NBA_PLAYERS, grace_hours=0)
    
    await interaction.followup.send(
        f"🔍 **Check complete**\n"
        f"✅ Resolved: **{resolved}**\n"
        f"⏳ Still pending: **{pending}**\n"
        f"❌ Errors: **{errors}**"
    )

@tree.command(name="testresolve", description="[Dev] Force-resolve one pending prediction with a fake value")
async def testresolve(interaction: discord.Interaction):
    await interaction.response.defer()
    from tracker import get_pending_predictions, resolve_prediction
    
    pending = get_pending_predictions()
    # Filter out SKIP predictions
    pending = [p for p in pending if p["recommendation"] != "SKIP"]
    if not pending:
        await interaction.followup.send("No resolvable predictions (SKIPs excluded).")
        return
    
    pred = pending[0]
    # Simulate: actual value = line + 5 (should produce OVER win if recommendation is OVER)
    fake_actual = pred["line"] + 5
    result = resolve_prediction(pred["id"], fake_actual)
    
    await interaction.followup.send(
        f"🧪 **Test Resolve**\n"
        f"Player: {pred['player_name']}\n"
        f"Market: {pred['market_display']}\n"
        f"Line: {pred['line']} | Recommendation: {pred['recommendation']}\n"
        f"Fake actual: {fake_actual}\n"
        f"Result: **{result}**"
    )

@tree.command(name="roster", description="List all available players, optionally filtered by sport")
@app_commands.describe(sport="Optional: filter to just one sport")
@app_commands.choices(sport=[
    app_commands.Choice(name="NFL", value="nfl"),
    app_commands.Choice(name="NBA", value="nba"),
])
async def roster(interaction: discord.Interaction, sport: str = None):
    await interaction.response.defer()
    
    show_nfl = sport in (None, "nfl")
    show_nba = sport in (None, "nba")
    
    embed = discord.Embed(
        title="📋 Available Players",
        description=f"NFL: **{len(PLAYERS)}** | NBA: **{len(NBA_PLAYERS)}**",
        color=0x3498db
    )
    
    if show_nfl:
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
        
        if nfl_qbs:
            embed.add_field(name=f"🏈 NFL QBs ({len(nfl_qbs)})", value="\n".join(nfl_qbs), inline=False)
        if nfl_wrs:
            embed.add_field(name=f"🏈 NFL WRs ({len(nfl_wrs)})", value="\n".join(nfl_wrs), inline=False)
        if nfl_rbs:
            embed.add_field(name=f"🏈 NFL RBs ({len(nfl_rbs)})", value="\n".join(nfl_rbs), inline=False)
    
    if show_nba:
        nba_entries = [f"`{key}` — {info['name']} ({info['team']})" for key, info in NBA_PLAYERS.items()]
        if nba_entries:
            embed.add_field(name=f"🏀 NBA Players ({len(nba_entries)})", value="\n".join(nba_entries), inline=False)
    
    embed.set_footer(text="Use /props sport:<sport> player:<name> to analyze")
    await interaction.followup.send(embed=embed)


@tree.command(name="props", description="Get player prop analysis")
@app_commands.describe(sport="Which sport to analyze", player="Player name (see /roster)")
@app_commands.choices(sport=[
    app_commands.Choice(name="NFL", value="nfl"),
    app_commands.Choice(name="NBA", value="nba"),
])
async def props(interaction: discord.Interaction, sport: str, player: str):
    await interaction.response.defer()
    
    player_key = player.lower()
    
    # Pick the right database based on selected sport
    if sport == "nfl":
        roster = PLAYERS
        sport_key = "americanfootball_nfl"
        espn_sport = "football"
        espn_league = "nfl"
        league_label = "NFL"
        embed_color = 0x00ff00
    else:  # nba
        roster = NBA_PLAYERS
        sport_key = "basketball_nba"
        espn_sport = "basketball"
        espn_league = "nba"
        league_label = "NBA"
        embed_color = 0xff6b00
    
    if player_key not in roster:
        await interaction.followup.send(
            f"❌ Player '{player}' not found in the {league_label} roster. "
            f"Try `/roster sport:{sport}` to see available players."
        )
        return
    
    player_info = roster[player_key]
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
        color=embed_color
    )
    
        # Import the predictor
    from predictor import compute_prediction, get_confidence_label
    
        # Fetch the opponent and determine home/away
    opponent_team = odds_client.get_opponent(player_info["team"], sport_key)
    is_home = odds_client.is_home_game(player_info["team"], sport_key)
    
    # Check injury status from ESPN
    from espn_client import get_injury_status
    injury_status = get_injury_status(espn_sport, espn_league, player_info["espn_id"])
    
    for market in player_info["markets"]:
        stat_key = market["stat"]
        display_name = market["display"]
        
        if stat_key not in data.columns:
            continue
        
        prediction = compute_prediction(
            data, stat_key, sport.lower(),
            opponent_team=opponent_team,
            market_type=market["key"],
            is_home=is_home,
            injury_status=injury_status,
        )
        
        if prediction is None:
            continue
        
        avg_stat = prediction["adjusted_avg"]
        confidence = prediction["confidence"]
        conf_label = get_confidence_label(confidence)
        
        available_lines = odds_client.get_player_props(
            player_name, player_info["team"], market["key"], sport_key
        )
        
        if available_lines:
            closest_line = min(available_lines, key=lambda x: abs(x['line'] - avg_stat))
            line_value = closest_line['line']
            odds_display = f"{closest_line['price']}"
            recommendation = "OVER" if avg_stat > line_value else "UNDER"
            edge = abs(avg_stat - line_value)
            
            # Calculate edge as % of line (better metric than raw edge)
            edge_pct = (edge / line_value * 100) if line_value else 0
            
            reason_line = f"\n_{prediction['adjustment_reason']}_" if prediction['adjustment_reason'] else ""
            
            field_value = (
                f"Projected: **{avg_stat:.1f}** | Line: **{line_value}** | Odds: **{odds_display}**\n"
                f"→ **{recommendation}** (Edge: {edge:+.1f}, {edge_pct:.1f}%){reason_line}\n"
                f"Confidence: {conf_label} ({confidence:.0%})"
            )
        else:
            line_value = round(avg_stat * 2) / 2
            field_value = (
                f"Projected: **{avg_stat:.1f}** | Line: **{line_value}** *(estimated)*\n"
                f"→ No live odds available\n"
                f"Confidence: {conf_label} ({confidence:.0%})"
            )

                # --- Log this prediction ---
        save_prediction(
            sport=sport,
            player_name=player_name,
            team=player_info["team"],
            opponent=opponent_team,
            espn_id=player_info["espn_id"],
            market_key=market["key"],
            market_display=display_name,
            stat_key=stat_key,
            line=line_value,
            line_price=closest_line['price'] if available_lines else None,
            is_estimated=(not available_lines),
            projection=avg_stat,
            confidence=confidence,
            recommendation=recommendation if available_lines else "SKIP",
            edge=(avg_stat - line_value) if available_lines else 0,
        )

        embed.add_field(name=display_name, value=field_value, inline=False)
    
    if len(embed.fields) == 0:
        await interaction.followup.send(f"❌ No market data available for {player_name} yet.")
        return
    
    embed.set_footer(text="Data from ESPN & PropLine | Bet responsibly.")
    await interaction.followup.send(embed=embed)


def _process_player_for_top(player_key, info, espn, odds_client, sport_key, espn_sport, espn_league):
    """Helper that processes one player with smart prediction."""
    from predictor import compute_prediction
    
    try:
        data = espn.get_player_gamelog(espn_sport, espn_league, info["espn_id"], info["espn_stat_map"])
        
        if data is None or data.empty or len(data) < 2:
            return None
        
        primary_market = info["markets"][0]
        stat_key = primary_market["stat"]

        if stat_key not in data.columns:
            return None

        # Find the actual opponent and venue
        opponent_team = odds_client.get_opponent(info["team"], sport_key)
        is_home = odds_client.is_home_game(info["team"], sport_key)

        from espn_client import get_injury_status
        injury_status = get_injury_status(espn_sport, espn_league, info["espn_id"])

        prediction = compute_prediction(
            data, stat_key, espn_league,
            opponent_team=opponent_team,
            market_type=primary_market["key"],
            is_home=is_home,
            injury_status=injury_status,
        )

        if prediction is None:
            return None
        
        avg_stat = prediction["adjusted_avg"]
        confidence = prediction["confidence"]
        
        available_lines = odds_client.get_player_props(
            info["name"], info["team"], primary_market["key"], sport_key
        )
        
        if not available_lines:
            return None
        
        closest_line = min(available_lines, key=lambda x: abs(x['line'] - avg_stat))
        edge = avg_stat - closest_line['line']
        recommendation = "OVER" if edge > 0 else "UNDER"
        
        # --- Log this prediction ---
        from tracker import save_prediction
        save_prediction(
            sport=espn_league,
            player_name=info["name"],
            team=info["team"],
            opponent=opponent_team,
            espn_id=info["espn_id"],
            market_key=primary_market["key"],
            market_display=primary_market["display"],
            stat_key=stat_key,
            line=closest_line['line'],
            line_price=closest_line['price'],
            is_estimated=False,
            projection=avg_stat,
            confidence=confidence,
            recommendation=recommendation,
            edge=edge,
        )
        
        return {
            "player": info["name"],
            "market": primary_market["display"],
            "avg": avg_stat,
            "line": closest_line['line'],
            "price": closest_line['price'],
            "edge": edge,
            "recommendation": recommendation,
            "abs_edge": abs(edge),
            "confidence": confidence,
            "reason": prediction["adjustment_reason"]
        }
    except Exception as e:
        print(f"Error processing {info['name']}: {e}")
        return None


@tree.command(name="top", description="Scan all players and show today's top prop picks")
@app_commands.describe(sport="Which sport to scan")
@app_commands.choices(sport=[
    app_commands.Choice(name="NFL", value="nfl"),
    app_commands.Choice(name="NBA", value="nba"),
])
async def top(interaction: discord.Interaction, sport: str):
    await interaction.response.defer()
    
    if sport == "nfl":
        roster = PLAYERS
        sport_key = "americanfootball_nfl"
        espn_sport = "football"
        espn_league = "nfl"
        league_label = "NFL"
    else:
        roster = NBA_PLAYERS
        sport_key = "basketball_nba"
        espn_sport = "basketball"
        espn_league = "nba"
        league_label = "NBA"
    
    await interaction.followup.send(f"🔍 Scanning {len(roster)} {league_label} players in parallel...")
    
    espn = ESPNClient()
    odds_client = OddsClient()
    results = []
    
    # Run 10 players at a time in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(
                _process_player_for_top,
                k, v, espn, odds_client, sport_key, espn_sport, espn_league
            )
            for k, v in roster.items()
        ]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    
    if not results:
        await interaction.followup.send(
            f"❌ No {league_label} props with live odds available right now. Try again closer to game time."
        )
        return
    
    results.sort(key=lambda x: x["abs_edge"], reverse=True)
    top_picks = results[:5]
    
    embed = discord.Embed(
        title=f"🏆 Today's Top 5 {league_label} Prop Picks",
        description=f"Scanned {len(roster)} players, found {len(results)} with live odds",
        color=0xffd700
    )
    
    from predictor import get_confidence_label
    
    for i, pick in enumerate(top_picks, 1):
        color_emoji = "🟢" if pick["recommendation"] == "OVER" else "🔴"
        field_name = f"{color_emoji} #{i} {pick['player']} — {pick['market']}"
        
        conf_label = get_confidence_label(pick["confidence"])
        reason_line = f"\n_{pick['reason']}_" if pick.get('reason') else ""
        
        field_value = (
            f"Projected: **{pick['avg']:.1f}** vs Line: **{pick['line']}+** | Odds: **{pick['price']}**\n"
            f"→ **{pick['recommendation']}** (Edge: {pick['edge']:+.1f}){reason_line}\n"
            f"Confidence: {conf_label} ({pick['confidence']:.0%})"
        )
        embed.add_field(name=field_name, value=field_value, inline=False)
    
    embed.set_footer(text="Data from ESPN & PropLine | Bet responsibly.")
    await interaction.followup.send(embed=embed)

@tree.command(name="record", description="Show the bot's historical prediction record")
@app_commands.describe(sport="Optional: filter to NFL or NBA only")
@app_commands.choices(sport=[
    app_commands.Choice(name="NFL", value="nfl"),
    app_commands.Choice(name="NBA", value="nba"),
])
async def record(interaction: discord.Interaction, sport: str = None):
    await interaction.response.defer()
    from tracker import get_stats
    
    stats = get_stats(sport=sport)
    overall = stats["overall"]
    
    wins = overall.get("wins") or 0
    losses = overall.get("losses") or 0
    pushes = overall.get("pushes") or 0
    total = wins + losses
    
    if total == 0:
        embed = discord.Embed(
            title="📊 Prediction Record",
            description="No resolved predictions yet. Check back after some games have finished.",
            color=0x808080
        )
        embed.add_field(
            name="Pending",
            value=f"**{stats['pending']}** predictions waiting for results",
            inline=False
        )
        await interaction.followup.send(embed=embed)
        return
    
    win_rate = wins / total * 100
    
    # Color based on performance
    if win_rate >= 55:
        color = 0x00ff00  # green — profitable
    elif win_rate >= 50:
        color = 0xffd700  # gold — break-even
    else:
        color = 0xff0000  # red — losing
    
    # Emoji for win rate
    if win_rate >= 60:
        emoji = "🔥"
    elif win_rate >= 55:
        emoji = "🟢"
    elif win_rate >= 50:
        emoji = "⚪"
    else:
        emoji = "🔴"
    
    sport_label = f" ({sport.upper()})" if sport else ""
    embed = discord.Embed(
        title=f"📊 Prediction Record{sport_label}",
        description=f"**{wins}W - {losses}L** ({win_rate:.1f}%) {emoji}",
        color=color
    )
    
    if pushes > 0:
        embed.add_field(
            name="Pushes",
            value=str(pushes),
            inline=True
        )
    
    embed.add_field(
        name="Pending",
        value=str(stats["pending"]),
        inline=True
    )
    
    embed.add_field(
        name="Total Resolved",
        value=str(total),
        inline=True
    )

@tree.command(name="cleanrecord", description="[Dev] Delete all resolved predictions (fresh start)")
async def cleanrecord(interaction: discord.Interaction):
    await interaction.response.defer()
    from tracker import _get_connection
    conn = _get_connection()
    try:
        count = conn.execute(
            "DELETE FROM predictions WHERE result != 'PENDING'"
        ).rowcount
        conn.commit()
        await interaction.followup.send(f"🗑️ Deleted {count} resolved predictions. Fresh start.")
    finally:
        conn.close()

@tree.command(name="clearcache", description="[Dev] Delete all cached gamelogs")
async def clearcache(interaction: discord.Interaction):
    await interaction.response.defer()
    import os
    from espn_client import DATA_DIR
    count = 0
    if os.path.exists(DATA_DIR):
        for f in os.listdir(DATA_DIR):
            if f.endswith('.json'):
                os.remove(os.path.join(DATA_DIR, f))
                count += 1
    await interaction.followup.send(f"🗑️ Deleted {count} cached files.")

@tree.command(name="rawdump", description="[Dev] Dump raw ESPN JSON structure")
async def rawdump(interaction: discord.Interaction):
    await interaction.response.defer()
    import requests, json
    
    url = "https://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/4036378/gamelog"
    r = requests.get(url, timeout=10)
    data = r.json()
    
    # Top-level keys
    top_keys = list(data.keys())
    
    # First event's keys inside seasonTypes
    first_event_keys = []
    try:
        first_event_keys = list(data['seasonTypes'][0]['categories'][0]['events'][0].keys())
    except Exception as e:
        first_event_keys = [f"error: {e}"]
    
    # Show the first event object (truncated)
    first_event_sample = ""
    try:
        ev = data['seasonTypes'][0]['categories'][0]['events'][0]
        first_event_sample = json.dumps(ev, indent=1)[:800]
    except Exception as e:
        first_event_sample = f"error: {e}"
    
    # Events dict info
    events_dict = data.get('events', {})
    events_info = f"type={type(events_dict).__name__}"
    first_event_meta = ""
    if isinstance(events_dict, dict) and events_dict:
        first_key = list(events_dict.keys())[0]
        events_info += f", len={len(events_dict)}, first key={first_key}"
        first_event_meta = json.dumps(events_dict[first_key], indent=1)[:800]
    elif isinstance(events_dict, list):
        events_info += f", len={len(events_dict)}"
        if events_dict:
            first_event_meta = json.dumps(events_dict[0], indent=1)[:800]
    
    msg = (
        f"**Top-level keys:** `{top_keys}`\n\n"
        f"**First event keys (in seasonTypes):** `{first_event_keys}`\n\n"
        f"**First event (seasonTypes):**\n```json\n{first_event_sample}\n```\n\n"
        f"**Events dict:** {events_info}\n\n"
        f"**First event metadata (events dict):**\n```json\n{first_event_meta}\n```"
    )
    
    # Discord has 2000 char limit per message, so split if needed
    if len(msg) > 1900:
        await interaction.followup.send(msg[:1900])
        if len(msg) > 1900:
            await interaction.followup.send(msg[1900:3800])
    else:
        await interaction.followup.send(msg)

@tree.command(name="gameinfo", description="[Dev] Test game summary lookup")
async def gameinfo(interaction: discord.Interaction, game_id: str):
    await interaction.response.defer()
    import requests
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"
    r = requests.get(url, timeout=10)
    data = r.json()
    await interaction.followup.send(f"Status: {r.status_code}\nTop keys: {list(data.keys())[:10]}")

@tree.command(name="debuglog", description="[Dev] Show raw gamelog for a player")
@app_commands.describe(player="Player key like jordan_love")
async def debuglog(interaction: discord.Interaction, player: str):
    await interaction.response.defer()
    from espn_client import ESPNClient
    
    player_key = player.lower()
    if player_key not in PLAYERS:
        await interaction.followup.send("Not found.")
        return
    
    info = PLAYERS[player_key]
    espn = ESPNClient()
    data = espn.get_player_gamelog('football', 'nfl', info["espn_id"], info["espn_stat_map"])
    
    if data is None or data.empty:
        await interaction.followup.send("No data.")
        return
    
    # Show last 5 rows with the key columns
    msg = "```\n"
    for _, row in data.tail(5).iterrows():
        msg += f"date={str(row.get('date'))[:10]} "
        msg += f"ha={row.get('home_away', '?')} "
        msg += f"opp={row.get('opponent', '?')} "
        msg += f"stat={row.get(info['markets'][0]['stat'], '?')}\n"
    msg += "```"
    
    await interaction.followup.send(msg)
    
    # Confidence breakdown
    conf_lines = []
    for bucket, label in [("high", "🔥 High"), ("medium", "✅ Medium"), ("low", "⚠️ Low")]:
        b = stats["by_confidence"].get(bucket, {})
        b_wins = b.get("wins") or 0
        b_losses = b.get("losses") or 0
        b_total = b_wins + b_losses
        if b_total > 0:
            b_rate = b_wins / b_total * 100
            conf_lines.append(f"{label}: **{b_wins}W - {b_losses}L** ({b_rate:.0f}%)")
    
    if conf_lines:
        embed.add_field(
            name="By Confidence",
            value="\n".join(conf_lines),
            inline=False
        )
    
    # Market breakdown
    market_lines = []
    for market, m in stats["by_market"].items():
        m_wins = m.get("wins") or 0
        m_losses = m.get("losses") or 0
        m_total = m_wins + m_losses
        if m_total > 0:
            m_rate = m_wins / m_total * 100
            market_lines.append(f"**{market}**: {m_wins}W - {m_losses}L ({m_rate:.0f}%)")
    
    if market_lines:
        embed.add_field(
            name="By Market",
            value="\n".join(market_lines[:8]),  # cap at 8 markets
            inline=False
        )
    
    embed.set_footer(text="Data from ESPN & PropLine | Bet responsibly.")
    await interaction.followup.send(embed=embed)

# --- Background refresh task ---
@tasks.loop(hours=6)
async def refresh_player_data():
    """Refresh all player gamelogs from ESPN every 6 hours."""
    print("🔄 Starting background refresh of player gamelogs...")
    espn = ESPNClient()
    nfl_count = espn.refresh_all(PLAYERS, "football", "nfl", force=True)
    nba_count = espn.refresh_all(NBA_PLAYERS, "basketball", "nba", force=True)
    print(f"✅ Refreshed {nfl_count} NFL + {nba_count} NBA players.")


@refresh_player_data.before_loop
async def before_refresh():
    """Wait until the bot is ready before starting the refresh loop."""
    await client.wait_until_ready()


@client.event
async def on_ready():
    """Runs once when the bot logs in."""
    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    print(f"✅ Logged in as {client.user}!")
    print("✅ Slash commands synced to your server!")
    
    if not refresh_player_data.is_running():
        refresh_player_data.start()
        print("🔄 Background refresh task started (runs every 6 hours).")
    
    if not check_results.is_running():
        check_results.start()
        print("🔍 Background result checker started (runs every 1 hour).")

# --- Background result checker task ---
@tasks.loop(hours=1)
async def check_results():
    """Every hour, try to resolve any pending predictions."""
    print("🔍 Checking pending predictions for results...")
    try:
        resolved, pending, errors = check_pending_predictions(PLAYERS, NBA_PLAYERS)
        print(f"✅ Checked: {resolved} resolved, {pending} still pending, {errors} errors")
    except Exception as e:
        print(f"❌ Checker failed: {e}")


@check_results.before_loop
async def before_check():
    """Wait 5 minutes after startup before the first check."""
    await client.wait_until_ready()
    await asyncio.sleep(300)

    
if __name__ == "__main__":
    client.run(TOKEN)