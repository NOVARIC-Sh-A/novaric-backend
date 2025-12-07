# paragon_api.py
from fastapi import APIRouter
from typing import List, Dict, Any
from utils.supabase_client import _get

router = APIRouter(
    prefix="/api/paragon",
    tags=["PARAGON Analytics"]
)

# -------------------------------------------------------------------
# Helper: Fetch table with safety wrapper
# -------------------------------------------------------------------
def fetch_safe(table: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return _get(table, params)
    except Exception as e:
        print(f"[PARAGON API] Supabase fetch failed for {table}: {e}")
        return []


# -------------------------------------------------------------------
# 1) LATEST LIVE SCORES (paragon_scores)
# -------------------------------------------------------------------
@router.get("/latest")
def get_latest_scores():
    """
    Returns live PARAGON scores sorted by overall score.
    """
    data = fetch_safe(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "order": "overall_score.desc"
        }
    )
    return {"count": len(data), "results": data}


# -------------------------------------------------------------------
# 2) TREND HISTORY (last 500 entries)
# -------------------------------------------------------------------
@router.get("/trends/latest")
def get_latest_trends():
    """
    Returns a maximum of 500 most recent trend entries.
    """
    data = fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": 500
        }
    )
    return {"count": len(data), "results": data}


# -------------------------------------------------------------------
# Internal function: compute last deltas per politician
# -------------------------------------------------------------------
def compute_deltas(history: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    grouped: Dict[int, List[Dict[str, Any]]] = {}

    # Group by politician_id
    for row in history:
        pid = row.get("politician_id")
        if not pid:
            continue
        grouped.setdefault(pid, []).append(row)

    deltas: Dict[int, Dict[str, Any]] = {}

    for pid, rows in grouped.items():
        if len(rows) < 2:
            continue

        # Ensure sorted by time
        rows_sorted = sorted(rows, key=lambda r: r["calculated_at"], reverse=True)

        new_score = rows_sorted[0]["overall_score"]
        prev_score = rows_sorted[1]["overall_score"]
        delta = new_score - prev_score

        deltas[pid] = {
            "politician_id": pid,
            "name": rows_sorted[0].get("politicians", {}).get("name"),
            "new_score": new_score,
            "previous_score": prev_score,
            "delta": delta,
        }

    return deltas


# -------------------------------------------------------------------
# 3) TOP RISERS
# -------------------------------------------------------------------
@router.get("/trends/top-risers")
def get_top_risers(limit: int = 10):
    history = fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": 200
        }
    )

    deltas = compute_deltas(history)

    risers = [
        entry for entry in deltas.values()
        if entry["delta"] > 0
    ]

    sorted_risers = sorted(risers, key=lambda x: x["delta"], reverse=True)

    return {"count": len(sorted_risers), "results": sorted_risers[:limit]}


# -------------------------------------------------------------------
# 4) TOP FALLERS
# -------------------------------------------------------------------
@router.get("/trends/top-fallers")
def get_top_fallers(limit: int = 10):
    history = fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": 200
        }
    )

    deltas = compute_deltas(history)

    fallers = [
        entry for entry in deltas.values()
        if entry["delta"] < 0
    ]

    sorted_fallers = sorted(fallers, key=lambda x: x["delta"])

    return {"count": len(sorted_fallers), "results": sorted_fallers[:limit]}
