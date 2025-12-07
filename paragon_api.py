# paragon_api.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from utils.supabase_client import _get

router = APIRouter(
    prefix="/api/paragon",
    tags=["PARAGON Analytics"]
)

# -------------------------------------------------------------------
# Safe Supabase getter
# -------------------------------------------------------------------
def fetch_safe(table: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return _get(table, params)
    except Exception as e:
        print(f"[PARAGON API] Supabase fetch failed for {table}: {e}")
        return []


# -------------------------------------------------------------------
# INTERNAL: compute deltas for momentum
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
# 1) LATEST LIVE SCORES
# -------------------------------------------------------------------
@router.get("/latest")
def get_latest_scores():
    data = fetch_safe(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "order": "overall_score.desc"
        }
    )
    return {"count": len(data), "results": data}


# Single politician latest score
@router.get("/latest/{politician_id}")
def get_latest_score_for(politician_id: int):
    data = fetch_safe(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "politician_id": f"eq.{politician_id}",
            "limit": 1
        }
    )
    if not data:
        raise HTTPException(status_code=404, detail="Politician score not found")
    return data[0]


# -------------------------------------------------------------------
# 2) TREND HISTORY (global)
# -------------------------------------------------------------------
@router.get("/trends/latest")
def get_latest_trends():
    data = fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": 500
        }
    )
    return {"count": len(data), "results": data}


# Trend history for a specific politician
@router.get("/trends/history/{politician_id}")
def get_trend_history(politician_id: int):
    data = fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "politician_id": f"eq.{politician_id}",
            "order": "calculated_at.desc",
            "limit": 50
        }
    )
    return {"count": len(data), "results": data}


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

    risers = [d for d in deltas.values() if d["delta"] > 0]
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

    fallers = [d for d in deltas.values() if d["delta"] < 0]
    sorted_fallers = sorted(fallers, key=lambda x: x["delta"])

    return {"count": len(sorted_fallers), "results": sorted_fallers[:limit]}


# -------------------------------------------------------------------
# 5) MOMENTUM — per politician
# -------------------------------------------------------------------
@router.get("/trends/momentum/{politician_id}")
def get_momentum(politician_id: int):
    history = fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "politician_id": f"eq.{politician_id}",
            "order": "calculated_at.desc",
            "limit": 2
        }
    )

    if len(history) < 2:
        return {"message": "Not enough data", "delta": 0}

    new_score = history[0]["overall_score"]
    prev_score = history[1]["overall_score"]
    delta = new_score - prev_score

    return {
        "politician_id": politician_id,
        "name": history[0].get("politicians", {}).get("name"),
        "new_score": new_score,
        "previous_score": prev_score,
        "delta": delta
    }

# -------------------------------------------------------------------
# 6) DASHBOARD AGGREGATOR (one-call endpoint)
# -------------------------------------------------------------------
@router.get("/dashboard")
def get_paragon_dashboard(limit: int = 10):
    """
    Returns a full PARAGON dashboard dataset in one API call:
      - latestScores: sorted by overall_score
      - topRisers: top Δ positive
      - topFallers: top Δ negative
      - recentTrends: last 500 entries
    """

    # --- Latest Live Scores ---
    latest_scores = fetch_safe(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "order": "overall_score.desc"
        }
    )

    # --- Trend History (global) ---
    trend_history = fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": 500
        }
    )

    # --- Compute Deltas ---
    deltas = compute_deltas(trend_history)

    # Risers = Δ > 0
    top_risers = sorted(
        [d for d in deltas.values() if d["delta"] > 0],
        key=lambda x: x["delta"],
        reverse=True
    )[:limit]

    # Fallers = Δ < 0
    top_fallers = sorted(
        [d for d in deltas.values() if d["delta"] < 0],
        key=lambda x: x["delta"]
    )[:limit]

    return {
        "latestScores": latest_scores,
        "topRisers": top_risers,
        "topFallers": top_fallers,
        "recentTrends": trend_history
    }
