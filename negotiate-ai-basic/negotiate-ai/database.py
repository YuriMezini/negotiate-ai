"""
database.py — MongoDB Integration
Stores negotiation sessions, salary cache, and user history.
"""

import datetime

try:
    from pymongo import MongoClient
    from config import MONGODB_URI, MONGODB_DB_NAME
    if MONGODB_URI and MONGODB_URI != "PASTE_YOUR_MONGODB_CONNECTION_STRING_HERE":
        mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
        # Test connection
        mongo_client.admin.command("ping")
        db = mongo_client[MONGODB_DB_NAME]
        sessions_col = db["sessions"]
        salary_cache_col = db["salary_cache"]
        outcomes_col = db["outcomes"]
        DB_AVAILABLE = True
    else:
        db = None
        sessions_col = None
        salary_cache_col = None
        outcomes_col = None
        DB_AVAILABLE = False
except Exception:
    db = None
    sessions_col = None
    salary_cache_col = None
    outcomes_col = None
    DB_AVAILABLE = False


def save_session(session_data: dict) -> str | None:
    """Save a negotiation session. Returns session_id or None."""
    if not DB_AVAILABLE:
        return None
    try:
        session_data["created_at"] = datetime.datetime.utcnow()
        result = sessions_col.insert_one(session_data)
        return str(result.inserted_id)
    except Exception as e:
        print(f"MongoDB save error: {e}")
        return None


def get_recent_sessions(limit: int = 10) -> list:
    """Get recent negotiation sessions."""
    if not DB_AVAILABLE:
        return []
    try:
        sessions = sessions_col.find().sort("created_at", -1).limit(limit)
        return [
            {**s, "_id": str(s["_id"])} for s in sessions
        ]
    except Exception:
        return []


def save_outcome(outcome_data: dict) -> str | None:
    """Save an anonymized negotiation outcome for the Solana proof system."""
    if not DB_AVAILABLE:
        return None
    try:
        outcome_data["created_at"] = datetime.datetime.utcnow()
        result = outcomes_col.insert_one(outcome_data)
        return str(result.inserted_id)
    except Exception as e:
        print(f"MongoDB outcome save error: {e}")
        return None


def get_aggregate_stats() -> dict:
    """Get aggregate stats across all sessions."""
    if not DB_AVAILABLE:
        return {}
    try:
        pipeline = [
            {"$group": {
                "_id": None,
                "total_sessions": {"$sum": 1},
                "avg_offer": {"$avg": "$profile.offer"},
                "avg_market_median": {"$avg": "$market.median"},
                "avg_gap_pct": {"$avg": "$analysis.gap_pct"},
            }}
        ]
        result = list(sessions_col.aggregate(pipeline))
        return result[0] if result else {}
    except Exception:
        return {}


def is_available() -> bool:
    """Check if database is available."""
    return DB_AVAILABLE
