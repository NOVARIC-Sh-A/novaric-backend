# etl/trend_engine.py

from typing import List, Dict, Any
from utils.supabase_client import fetch_table, supabase_insert


def compute_trends(new_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Compare newly generated PARAGON scores with historical scores.
    Generates trend entries for politicians whose score changed.
    """

    if not new_records:
        return []

    # Fetch last known scores from Supabase
    last_scores = fetch_table("paragon_scores", "politician_id, overall_score")

    # Convert to map for fast lookup
    last_map = {row["politician_id"]: row["overall_score"] for row in last_scores}

    trend_rows = []

    for rec in new_records:
        pid = rec["politician_id"]
        new_score = rec["overall_score"]

        old_score = last_map.get(pid)

        # First-time entry → no trend
        if old_score is None:
            continue

        delta = new_score - old_score

        # Only record meaningful change
        if delta != 0:
            trend_rows.append({
                "politician_id": pid,
                "previous_score": old_score,
                "new_score": new_score,
                "delta": delta,
                "raw_snapshot": rec
            })

    return trend_rows


def store_trends(trend_rows: List[Dict[str, Any]]):
    """
    Insert trend entries into Supabase.
    """
    if not trend_rows:
        return {"status": "no_changes"}

    return supabase_insert("paragon_trends", trend_rows)
