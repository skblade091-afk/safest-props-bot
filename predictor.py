"""
Enhanced prediction logic for player props.
Combines weighted recent form, opponent defense, home/away splits,
rest days, and injury status.
"""

from datetime import datetime
from datetime import datetime, timezone

NFL_PASS_DEFENSE_RANK = {
    "Ravens": 1, "Bills": 2, "Jets": 3, "Browns": 4, "Packers": 5,
    "Chiefs": 6, "49ers": 7, "Cowboys": 8, "Steelers": 9, "Lions": 10,
    "Eagles": 11, "Chargers": 12, "Broncos": 13, "Colts": 14, "Vikings": 15,
    "Texans": 16, "Dolphins": 17, "Bengals": 18, "Falcons": 19, "Seahawks": 20,
    "Saints": 21, "Bears": 22, "Buccaneers": 23, "Raiders": 24, "Titans": 25,
    "Jaguars": 26, "Patriots": 27, "Cardinals": 28, "Giants": 29, "Rams": 30,
    "Panthers": 31, "Commanders": 32,
}

NFL_RUSH_DEFENSE_RANK = {
    "Ravens": 1, "49ers": 2, "Steelers": 3, "Bills": 4, "Lions": 5,
    "Jets": 6, "Browns": 7, "Chiefs": 8, "Eagles": 9, "Texans": 10,
    "Chargers": 11, "Vikings": 12, "Falcons": 13, "Broncos": 14, "Cowboys": 15,
    "Packers": 16, "Saints": 17, "Bears": 18, "Colts": 19, "Bengals": 20,
    "Seahawks": 21, "Rams": 22, "Dolphins": 23, "Raiders": 24,
    "Jaguars": 25, "Titans": 26, "Patriots": 27, "Cardinals": 28, "Giants": 29,
    "Panthers": 30, "Commanders": 31, "Buccaneers": 32,
}

NBA_DEFENSE_RANK = {
    "Celtics": 1, "Thunder": 2, "Timberwolves": 3, "Magic": 4, "Knicks": 5,
    "Nuggets": 6, "Cavaliers": 7, "Heat": 8, "Clippers": 9, "Bucks": 10,
    "Lakers": 11, "Warriors": 12, "Suns": 13, "Mavericks": 14, "76ers": 15,
    "Pacers": 16, "Kings": 17, "Pelicans": 18, "Rockets": 19, "Grizzlies": 20,
    "Bulls": 21, "Hawks": 22, "Raptors": 23, "Nets": 24, "Spurs": 25,
    "Trail Blazers": 26, "Jazz": 27, "Hornets": 28, "Wizards": 29, "Pistons": 30,
}


def _lookup_rank(team_name: str, rank_dict: dict, default: int = 16) -> int:
    """Flexible team lookup — handles 'GB Packers' matching 'Packers'."""
    if not team_name:
        return default
    if team_name in rank_dict:
        return rank_dict[team_name]
    team_lower = team_name.lower()
    for key, rank in rank_dict.items():
        key_lower = key.lower()
        if key_lower in team_lower or team_lower in key_lower:
            return rank
    return default


def _compute_home_away_split(df, stat_key):
    """
    Returns (home_avg, away_avg) from the player's recent games.
    Falls back to None if not enough data.
    """
    if 'home_away' not in df.columns:
        return None, None
    recent = df.tail(10)
    home_games = recent[recent['home_away'] == 'HOME']
    away_games = recent[recent['home_away'] == 'AWAY']
    home_avg = home_games[stat_key].mean() if len(home_games) >= 2 else None
    away_avg = away_games[stat_key].mean() if len(away_games) >= 2 else None
    return home_avg, away_avg


def _compute_rest_days(df):
    """
    Days since the player's most recent game.
    Handles timezone-aware dates by converting to naive UTC.
    """
    if 'date' not in df.columns or df.empty:
        return None
    try:
        dates = []
        for d in df['date'].dropna().tolist():
            try:
                parsed = datetime.fromisoformat(d.replace('Z', ''))
                # Strip timezone to make it naive UTC
                if parsed.tzinfo is not None:
                    parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
                dates.append(parsed)
            except Exception:
                continue
        if not dates:
            return None
        dates.sort()
        most_recent = dates[-1]
        return (datetime.utcnow() - most_recent).days
    except Exception:
        return None


def compute_prediction(df, stat_key, sport, opponent_team, market_type,
                       is_home=None, injury_status=None):
    """
    Returns an enhanced prediction dict with adjusted average and confidence.
    New parameters:
      is_home: True if the upcoming game is at home, False if away, None if unknown
      injury_status: 'OUT', 'QUESTIONABLE', 'DAY-TO-DAY', or None
    """
    if df is None or df.empty or len(df) < 3:
        return None

    recent = df.tail(5).copy()
    values = recent[stat_key].dropna().astype(float).values
    if len(values) < 3:
        return None

    # --- Base weighted average ---
    weights = [1, 1.5, 2, 2.5, 3][-len(values):]
    weighted_avg = sum(v * w for v, w in zip(values, weights)) / sum(weights)

    # --- Consistency ---
    if weighted_avg > 0:
        cv = values.std() / weighted_avg
    else:
        cv = 1.0
    consistency_score = max(0.0, 1.0 - min(cv, 1.0))

    # --- Sample size ---
    sample_score = min(len(df) / 10.0, 1.0)

    # --- Home/away adjustment ---
    # Apply the split for whichever venue the upcoming game is at,
    # as long as we have enough games in that specific split.
    home_avg, away_avg = _compute_home_away_split(df, stat_key)
    home_away_adjustment = 0.0
    home_away_reason = ""

    if is_home is True and home_avg is not None and weighted_avg > 0:
        split_bonus = (home_avg - weighted_avg) / weighted_avg
        split_bonus = max(-0.12, min(split_bonus, 0.12))
        home_away_adjustment = weighted_avg * split_bonus
        if abs(split_bonus) > 0.03:
            home_away_reason = f"Home game (avg {home_avg:.1f} at home)"
    elif is_home is False and away_avg is not None and weighted_avg > 0:
        split_bonus = (away_avg - weighted_avg) / weighted_avg
        split_bonus = max(-0.12, min(split_bonus, 0.12))
        home_away_adjustment = weighted_avg * split_bonus
        if abs(split_bonus) > 0.03:
            home_away_reason = f"Away game (avg {away_avg:.1f} away)"

    # --- Rest days adjustment ---
    rest_days = _compute_rest_days(df)
    rest_adjustment = 0.0
    rest_reason = ""
    if rest_days is not None:
        if rest_days <= 4:
            rest_adjustment = -0.03 * weighted_avg
            rest_reason = f"Short rest ({rest_days}d)"
        elif rest_days >= 10:
            rest_adjustment = +0.02 * weighted_avg
            rest_reason = f"Well rested ({rest_days}d)"

    # --- Opponent defense adjustment ---
    defense_adjustment = 0.0
    defense_reason = ""
    multiplier = 1.0

    if sport == "nfl":
        if "pass" in market_type:
            rank = _lookup_rank(opponent_team, NFL_PASS_DEFENSE_RANK, 16)
            label = "pass defense"
        elif "rush" in market_type:
            rank = _lookup_rank(opponent_team, NFL_RUSH_DEFENSE_RANK, 16)
            label = "rush defense"
        else:
            rank = 16
            label = "defense"

        rank_pct = (rank - 1) / 31
        multiplier = 0.9 + (rank_pct * 0.2)
        defense_adjustment = weighted_avg * (multiplier - 1.0)

        if rank <= 10:
            defense_reason = f"Tough {label} (#{rank})"
        elif rank >= 23:
            defense_reason = f"Weak {label} (#{rank})"

    elif sport == "nba":
        rank = _lookup_rank(opponent_team, NBA_DEFENSE_RANK, 15)
        rank_pct = (rank - 1) / 29
        multiplier = 0.92 + (rank_pct * 0.16)
        defense_adjustment = weighted_avg * (multiplier - 1.0)

        if rank <= 10:
            defense_reason = f"Tough defense (#{rank})"
        elif rank >= 21:
            defense_reason = f"Weak defense (#{rank})"

    # --- Injury adjustment ---
    injury_adjustment = 0.0
    injury_reason = ""
    if injury_status:
        status_upper = injury_status.upper()
        if "OUT" in status_upper:
            injury_adjustment = -0.50 * weighted_avg
            injury_reason = "Listed as OUT ⚠️"
        elif "QUESTIONABLE" in status_upper:
            injury_adjustment = -0.15 * weighted_avg
            injury_reason = "Questionable ⚠️"
        elif "DAY-TO-DAY" in status_upper or "DAY TO DAY" in status_upper:
            injury_adjustment = -0.08 * weighted_avg
            injury_reason = "Day-to-day"

    adjusted_avg = weighted_avg + defense_adjustment + home_away_adjustment + rest_adjustment + injury_adjustment

    # --- Combine reasons into one line ---
    reasons = [r for r in [defense_reason, home_away_reason, rest_reason, injury_reason] if r]
    adjustment_reason = " • ".join(reasons)

    # --- Confidence score ---
    confidence = 0.5 * consistency_score + 0.3 * sample_score + 0.2 * 0.5

    # Penalty for large adjustments (more uncertainty)
    total_adj_pct = abs(adjusted_avg - weighted_avg) / weighted_avg if weighted_avg > 0 else 0
    if total_adj_pct > 0.10:
        confidence -= 0.08
    elif total_adj_pct > 0.05:
        confidence -= 0.04

    # Injury heavily penalizes confidence
    if injury_status:
        if "OUT" in injury_status.upper():
            confidence -= 0.30
        elif "QUESTIONABLE" in injury_status.upper():
            confidence -= 0.10

    confidence = max(0.20, min(confidence, 0.95))

    return {
        "raw_avg": weighted_avg,
        "adjusted_avg": adjusted_avg,
        "confidence": confidence,
        "adjustment_reason": adjustment_reason,
        "home_away_adj": home_away_adjustment,
        "rest_adj": rest_adjustment,
        "defense_adj": defense_adjustment,
        "injury_adj": injury_adjustment,
    }


def get_confidence_label(confidence: float) -> str:
    if confidence >= 0.75:
        return "🔥 High"
    elif confidence >= 0.55:
        return "✅ Medium"
    else:
        return "⚠️ Low"