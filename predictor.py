"""
Enhanced prediction logic for player props.
Combines weighted recent form, opponent defense, and consistency metrics.
"""

# --- NFL Defense Rankings (1 = best, 32 = worst) ---
# Rough rankings — update these weekly as the season progresses
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
    "Seahawks": 21, "Rams": 22, "Falcons": 23, "Dolphins": 24, "Raiders": 25,
    "Jaguars": 26, "Titans": 27, "Patriots": 28, "Cardinals": 29, "Giants": 30,
    "Panthers": 31, "Commanders": 32,
}

# --- NBA Defense Rankings (1 = best, 30 = worst) ---
NBA_DEFENSE_RANK = {
    "Celtics": 1, "Thunder": 2, "Timberwolves": 3, "Magic": 4, "Knicks": 5,
    "Nuggets": 6, "Cavaliers": 7, "Heat": 8, "Clippers": 9, "Bucks": 10,
    "Lakers": 11, "Warriors": 12, "Suns": 13, "Mavericks": 14, "76ers": 15,
    "Pacers": 16, "Kings": 17, "Pelicans": 18, "Rockets": 19, "Grizzlies": 20,
    "Bulls": 21, "Hawks": 22, "Raptors": 23, "Nets": 24, "Spurs": 25,
    "Trail Blazers": 26, "Jazz": 27, "Hornets": 28, "Wizards": 29, "Pistons": 30,
}


def compute_prediction(df, stat_key, sport, opponent_team, market_type):
    """
    Returns an enhanced prediction dict:
        {
            "raw_avg": simple mean of last 5
            "weighted_avg": recency-weighted mean
            "adjusted_avg": after opponent-defense adjustment
            "confidence": 0.0 - 1.0
            "adjustment_reason": human-readable explanation
        }
    Returns None if there isn't enough data.
    """
    if df is None or df.empty or len(df) < 3:
        return None

    # Use last 5 games
    recent = df.tail(5).copy()
    values = recent[stat_key].dropna().astype(float).values

    if len(values) < 3:
        return None

    # --- 1. Weighted average (recent games matter more) ---
    # Weights: oldest -> newest: 1, 1.5, 2, 2.5, 3
    weights = [1, 1.5, 2, 2.5, 3][-len(values):]
    weighted_avg = sum(v * w for v, w in zip(values, weights)) / sum(weights)
    raw_avg = float(values.mean())

    # --- 2. Consistency (lower std dev = higher confidence) ---
    if weighted_avg > 0:
        cv = values.std() / weighted_avg  # coefficient of variation
    else:
        cv = 1.0
    consistency_score = max(0.0, 1.0 - min(cv, 1.0))

    # --- 3. Sample size ---
    sample_score = min(len(df) / 10.0, 1.0)

    # --- 4. Opponent defense adjustment ---
    adjustment = 0.0
    adjustment_reason = ""

    if sport == "nfl":
        # Determine which defense ranking to use
        if "pass" in market_type:
            rank = NFL_PASS_DEFENSE_RANK.get(opponent_team, 16)  # default to middle
            label = "pass defense"
        elif "rush" in market_type:
            rank = NFL_RUSH_DEFENSE_RANK.get(opponent_team, 16)
            label = "rush defense"
        else:
            rank = 16
            label = "defense"

        # Rank 1 = best defense (reduce avg), Rank 32 = worst (boost avg)
        # Map rank to a multiplier from 0.9 (vs #1) to 1.1 (vs #32)
        rank_pct = (rank - 1) / 31  # 0.0 to 1.0
        multiplier = 0.9 + (rank_pct * 0.2)
        adjustment = weighted_avg * (multiplier - 1.0)

        if rank <= 10:
            adjustment_reason = f"Tough {label} (#{rank})"
        elif rank >= 23:
            adjustment_reason = f"Weak {label} (#{rank})"

    elif sport == "nba":
        rank = NBA_DEFENSE_RANK.get(opponent_team, 15)
        rank_pct = (rank - 1) / 29
        multiplier = 0.92 + (rank_pct * 0.16)
        adjustment = weighted_avg * (multiplier - 1.0)

        if rank <= 10:
            adjustment_reason = f"Tough defense (#{rank})"
        elif rank >= 21:
            adjustment_reason = f"Weak defense (#{rank})"

    adjusted_avg = weighted_avg + adjustment

    # --- 5. Confidence score ---
    # 50% consistency, 30% sample size, 20% edge clarity later
    confidence = 0.5 * consistency_score + 0.3 * sample_score + 0.2 * 0.5

    # Penalize if the opponent defense adjustment is huge (uncertainty)
    if abs(multiplier - 1.0) > 0.08:
        confidence -= 0.05

    confidence = max(0.30, min(confidence, 0.95))  # clamp to 30-95%

    return {
        "raw_avg": raw_avg,
        "weighted_avg": weighted_avg,
        "adjusted_avg": adjusted_avg,
        "confidence": confidence,
        "adjustment_reason": adjustment_reason,
    }


def get_confidence_label(confidence: float) -> str:
    """Turn a confidence number into a visual label."""
    if confidence >= 0.75:
        return "🔥 High"
    elif confidence >= 0.55:
        return "✅ Medium"
    else:
        return "⚠️ Low"