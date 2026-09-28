"""
Historical tracking for player prop predictions.
Stores every prediction, then matches it against actual game results.
Uses SQLite on the Railway persistent volume.
"""

import sqlite3
import os
from datetime import datetime

# Persistent storage location (Railway volume)
DATA_DIR = "/data"

# Fallback for local testing
if not os.path.exists("/data"):
    DATA_DIR = os.path.join(os.path.dirname(__file__), "data_cache")

os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "predictions.db")


def _get_connection():
    """Get a fresh SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allow dict-style row access
    return conn


def init_db():
    """Create the predictions table if it doesn't exist."""
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                sport TEXT NOT NULL,
                player_name TEXT NOT NULL,
                team TEXT NOT NULL,
                opponent TEXT,
                espn_id INTEGER,
                market_key TEXT NOT NULL,
                market_display TEXT NOT NULL,
                stat_key TEXT NOT NULL,
                line REAL NOT NULL,
                line_price INTEGER,
                is_estimated INTEGER DEFAULT 0,
                projection REAL NOT NULL,
                confidence REAL NOT NULL,
                recommendation TEXT NOT NULL,
                edge REAL NOT NULL,
                game_date TEXT,
                actual_value REAL,
                result TEXT DEFAULT 'PENDING',
                resolved_at TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def save_prediction(
    sport, player_name, team, opponent, espn_id,
    market_key, market_display, stat_key,
    line, line_price, is_estimated,
    projection, confidence, recommendation, edge,
    game_date=None
):
    """
    Save a prediction. Returns the new row id.
    Prevents exact duplicates within the last 2 hours.
    """
    conn = _get_connection()
    try:
        # Dedup check — same player+market+line within 2 hours
        cutoff = datetime.utcnow().isoformat()
        existing = conn.execute("""
            SELECT id FROM predictions
            WHERE player_name = ?
              AND market_key = ?
              AND line = ?
              AND timestamp > datetime(?, '-2 hours')
        """, (player_name, market_key, line, cutoff)).fetchone()
        
        if existing:
            return existing["id"]
        
        cur = conn.execute("""
            INSERT INTO predictions (
                timestamp, sport, player_name, team, opponent, espn_id,
                market_key, market_display, stat_key,
                line, line_price, is_estimated,
                projection, confidence, recommendation, edge, game_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            sport, player_name, team, opponent, espn_id,
            market_key, market_display, stat_key,
            line, line_price, 1 if is_estimated else 0,
            projection, confidence, recommendation, edge, game_date
        ))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_pending_predictions():
    """Get all unresolved predictions (for the result checker)."""
    conn = _get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM predictions
            WHERE result = 'PENDING'
            ORDER BY timestamp ASC
        """).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def resolve_prediction(prediction_id, actual_value):
    """
    Mark a prediction as resolved with its actual value.
    Automatically determines WIN/LOSS/PUSH based on the recommendation and line.
    """
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM predictions WHERE id = ?", (prediction_id,)
        ).fetchone()
        if not row:
            return None
        
        # Skip resolving SKIP predictions — they don't count
        if row["recommendation"] == "SKIP":
            conn.execute("""
                UPDATE predictions
                SET result = 'SKIP', resolved_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), prediction_id))
            conn.commit()
            return "SKIP"

        line = row["line"]
        recommendation = row["recommendation"]

        # Determine result — small tolerance for floating point
        if abs(actual_value - line) < 0.01:
            result = "PUSH"
        elif recommendation == "OVER":
            result = "WIN" if actual_value > line else "LOSS"
        else:  # UNDER
            result = "WIN" if actual_value < line else "LOSS"

        conn.execute("""
            UPDATE predictions
            SET actual_value = ?, result = ?, resolved_at = ?
            WHERE id = ?
        """, (actual_value, result, datetime.utcnow().isoformat(), prediction_id))
        conn.commit()
        return result
    finally:
        conn.close()


def get_stats(sport=None, min_confidence=None, market_key=None):
    """
    Get aggregate win/loss stats. Returns a dict with overall + breakdowns.
    """
    conn = _get_connection()
    try:
        where = ["result IN ('WIN', 'LOSS', 'PUSH')"]
        params = []
        if sport:
            where.append("sport = ?")
            params.append(sport)
        if min_confidence is not None:
            where.append("confidence >= ?")
            params.append(min_confidence)
        if market_key:
            where.append("market_key = ?")
            params.append(market_key)
        
        where_clause = " AND ".join(where)
        
        # Overall
        total = conn.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN result = 'PUSH' THEN 1 ELSE 0 END) as pushes
            FROM predictions
            WHERE {where_clause}
        """, params).fetchone()
        
        # Pending count
        pending_where = where_clause.replace(
            "result IN ('WIN', 'LOSS', 'PUSH')",
            "result = 'PENDING'"
        )
        pending = conn.execute(f"""
            SELECT COUNT(*) as total FROM predictions WHERE {pending_where}
        """, params).fetchone()
        
        # By confidence bucket
        by_confidence = {}
        for bucket_name, min_c, max_c in [
            ("high", 0.75, 1.01),
            ("medium", 0.55, 0.75),
            ("low", 0.0, 0.55),
        ]:
            row = conn.execute(f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses
                FROM predictions
                WHERE {where_clause} AND confidence >= ? AND confidence < ?
            """, params + [min_c, max_c]).fetchone()
            by_confidence[bucket_name] = dict(row) if row else {"total": 0, "wins": 0, "losses": 0}
        
        # By market
        by_market = {}
        market_rows = conn.execute(f"""
            SELECT
                market_display,
                COUNT(*) as total,
                SUM(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN result = 'LOSS' THEN 1 ELSE 0 END) as losses
            FROM predictions
            WHERE {where_clause}
            GROUP BY market_display
        """, params).fetchall()
        for r in market_rows:
            by_market[r["market_display"]] = dict(r)
        
        return {
            "overall": dict(total),
            "pending": pending["total"] if pending else 0,
            "by_confidence": by_confidence,
            "by_market": by_market,
        }
    finally:
        conn.close()


# Initialize the database on import
init_db()