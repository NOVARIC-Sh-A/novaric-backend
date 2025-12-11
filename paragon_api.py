"""
paragon_api.py

PARAGON® Analytics API:
- Latest scores
- Trends
- Risers / Fallers
- Momentum
- Dashboard Aggregator
- Real-time recomputation (NEW)
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from utils.supabase_client import _get
from etl.metric_loader import load_metrics_for
from etl.scoring_engine import score_metrics
from etl.trend_engine import record_paragon_snapshot


# Initialize PARAGON Engine early
try:
    print("✔ PARAGON Engine: metric_loader + scoring_engine active")
except Exception as e:
    print(f"✖ PARAGON Engine initialization failed: {e}")


router = APIRouter(
    prefix="/api/paragon",
    tags=["PARAGON Analytics"]
)


# =====================================================================
# Safe getter wrapper
# =====================================================================
def fetch_safe(table: str, params: Dict[str, Any]):
    try:
        return _get(table, params)
    except Exception as e:
        print(f"[paragon_api] Supabase fetch failed ({table}): {e}")
        return []


# =====================================================================
# Helper: Normalize DB row → frontend-ready format
# =====================================================================
def _normalize_paragon_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures all endpoints return consistent shape:

    {
        "politician_id": int,
        "overall_score": int,
        "calculated_at": "...",
        "dimensions": [...],          # always list of {dimension, score}
        "dimensions_json": [...],     # raw from DB for advanced consumers
        "politicians": {...}          # metadata
    }
    """

    # Pull stored JSONB field (may be NULL)
    dims = row.get("dimensions_json") or []

    # Convert into old structure for FE charts
    dimensions = [
        {
            "dimension": d.get("dimension"),
            "score": int(d.get("score", 0)),
        }
        for d in dims
    ]

    return {
        **row,
        "dimensions": dimensions,
        "dimensions_json": dims,
    }


# =====================================================================
# 1. Latest Live Scores
# =====================================================================
@router.get("/latest")
def get_latest_scores():
    data = fetch_safe(
        "paragon_scores",
        {"select": "*,politicians(*)", "order": "overall_score.desc"}
    )

    normalized = [_normalize_paragon_row(x) for x in data]

    return {
        "count": len(normalized),
        "results": normalized
    }


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
        raise HTTPException(404, "Politician score not found")

    return _normalize_paragon_row(data[0])


# =====================================================================
# 2. Global Trend History
# =====================================================================
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

    normalized = [_normalize_paragon_row(x) for x in data]

    return {"count": len(normalized), "results": normalized}


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

    return {
        "count": len(data),
        "results": [_normalize_paragon_row(x) for x in data],
    }


# =====================================================================
# 3. Risers / Fallers (same delta logic)
# =====================================================================
def compute_deltas(history: List[Dict[str, Any]]):
    grouped = {}

    for row in history:
        pid = row.get("politician_id")
        if not pid:
            continue
        grouped.setdefault(pid, []).append(row)

    deltas = {}

    for pid, rows in grouped.items():
        if len(rows) < 2:
            continue

        rows_sorted = sorted(rows, key=lambda r: r["calculated_at"], reverse=True)

        new_score = rows_sorted[0]["overall_score"]
        prev_score = rows_sorted[1]["overall_score"]

        deltas[pid] = {
            "politician_id": pid,
            "name": rows_sorted[0].get("politicians", {}).get("name"),
            "new_score": new_score,
            "previous_score": prev_score,
            "delta": new_score - prev_score,
        }

    return deltas


@router.get("/trends/top-risers")
def get_top_risers(limit: int = 10):
    history = fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": 300}
    )

    deltas = compute_deltas(history)

    risers = sorted(
        [d for d in deltas.values() if d["delta"] > 0],
        key=lambda x: x["delta"],
        reverse=True
    )

    return {"count": len(risers), "results": risers[:limit]}


@router.get("/trends/top-fallers")
def get_top_fallers(limit: int = 10):
    history = fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": 300}
    )

    deltas = compute_deltas(history)

    fallers = sorted(
        [d for d in deltas.values() if d["delta"] < 0],
        key=lambda x: x["delta"]
    )

    return {"count": len(fallers), "results": fallers[:limit]}


# =====================================================================
# 4. Momentum
# =====================================================================
@router.get("/trends/momentum/{politician_id}")
def get_momentum(politician_id: int):
    rows = fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "politician_id": f"eq.{politician_id}",
            "order": "calculated_at.desc",
            "limit": 2,
        }
    )

    if len(rows) < 2:
        return {"message": "Not enough data", "delta": 0}

    new_score = rows[0]["overall_score"]
    prev_score = rows[1]["overall_score"]

    return {
        "politician_id": politician_id,
        "name": rows[0].get("politicians", {}).get("name"),
        "new_score": new_score,
        "previous_score": prev_score,
        "delta": new_score - prev_score,
    }


# =====================================================================
# 5. Dashboard Aggregator
# =====================================================================
@router.get("/dashboard")
def get_paragon_dashboard(limit: int = 10):

    latest_scores = fetch_safe(
        "paragon_scores",
        {"select": "*,politicians(*)", "order": "overall_score.desc"}
    )
    latest_scores = [_normalize_paragon_row(x) for x in latest_scores]

    trend_history = fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": 500}
    )
    trend_history_norm = [_normalize_paragon_row(x) for x in trend_history]

    deltas = compute_deltas(trend_history)

    top_risers = sorted(
        [d for d in deltas.values() if d["delta"] > 0],
        key=lambda x: x["delta"],
        reverse=True
    )[:limit]

    top_fallers = sorted(
        [d for d in deltas.values() if d["delta"] < 0],
        key=lambda x: x["delta"]
    )[:limit]

    return {
        "latestScores": latest_scores,
        "topRisers": top_risers,
        "topFallers": top_fallers,
        "recentTrends": trend_history_norm,
    }


# =====================================================================
# 6. Real-time recomputation
# =====================================================================
@router.post("/recompute/{politician_id}")
def recompute_paragon_score(politician_id: int):

    try:
        metrics = load_metrics_for(politician_id)
        if not metrics:
            raise HTTPException(404, "No metrics found for this politician")

        scoring = score_metrics(metrics)

        snapshot = record_paragon_snapshot(politician_id, scoring)

        return {
            "politician_id": politician_id,
            "metrics": metrics,
            "overall_score": scoring["overall_score"],
            "dimensions": scoring["dimensions"],
            "dimensions_json": scoring["dimensions"],
            "snapshot": snapshot,
            "message": "PARAGON score recomputed successfully",
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"[paragon_api] recompute failed: {e}")
        raise HTTPException(500, "PARAGON recomputation failed")
