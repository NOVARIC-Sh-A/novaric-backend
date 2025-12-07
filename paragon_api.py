# paragon_api.py
from fastapi import APIRouter
from utils.supabase_client import fetch_table, _get
from typing import List, Dict, Any

router = APIRouter(prefix="/api/paragon", tags=["PARAGON Analytics"])


# ------------------------------------------------------------
# 1) LATEST LIVE SCORES (from paragon_scores)
# ------------------------------------------------------------
@router.get("/latest")
def get_latest_scores():
    """
    Returns live PARAGON scores sorted by overall score DESC.
    """
    data = _get(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "order": "overall_score.desc"
        }
    )
    return {"count": len(data), "results": data}


# ------------------------------------------------------------
# 2) TREND HISTORY (last 30 days)
# ------------------------------------------------------------
@router.get("/trends/latest")
def get_latest_trends():
    """
    Returns the last 30 days of trend history for each politician.
    """
    data = _get(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": 500   # adjust if needed
        }
    )
    return {"count": len(data), "results": data}


# ------------------------------------------------------------
# 3) TOP RISERS (Δ score positive)
# ------------------------------------------------------------
@router.get("/trends/top-risers")
def get_top_risers(limit: int = 10):
    """
    Computes top rising politicians based on Δ between last 2 entries.
    """

    # pull last 2 history rows per politician
    history = _get(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": 200
        }
    )

    # compute last Δ per politician
    deltas: Dict[int, Dict[str, Any]] = {}
    tmp: Dict[int, List[Dict[str, Any]]] = {}

    for row in history:
        pid = row["politician_id"]
        tmp.setdefault(pid, []).append(row)

    for pid, rows in tmp.items():
        if len(rows) < 2:
            continue

        new = rows[0]["overall_score"]
        prev = rows[1]["overall_score"]
        delta = new - prev

        if delta > 0:
            deltas[pid] = {
                "politician_id": pid,
                "name": rows[0].get("politicians", {}).get("name"),
                "new_score": new,
                "previous_score": prev,
                "delta": delta,
            }

    sorted_list = sorted(deltas.values(), key=lambda x: x["delta"], reverse=True)
    return {"results": sorted_list[:limit]}


# ------------------------------------------------------------
# 4) TOP FALLERS (Δ score negative)
# ------------------------------------------------------------
@router.get("/trends/top-fallers")
def get_top_fallers(limit: int = 10):
    """
    Computes steepest falling politicians based on Δ between last 2 entries.
    """

    history = _get(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": 200
        }
    )

    deltas: Dict[int, Dict[str, Any]] = {}
    tmp: Dict[int, List[Dict[str, Any]]] = {}

    for row in history:
        pid = row["politician_id"]
        tmp.setdefault(pid, []).append(row)

    for pid, rows in tmp.items():
        if len(rows) < 2:
            continue

        new = rows[0]["overall_score"]
        prev = rows[1]["overall_score"]
        delta = new - prev

        if delta < 0:
            deltas[pid] = {
                "politician_id": pid,
                "name": rows[0].get("politicians", {}).get("name"),
                "new_score": new,
                "previous_score": prev,
                "delta": delta,
            }

    sorted_list = sorted(deltas.values(), key=lambda x: x["delta"])
    return {"results": sorted_list[:limit]}
