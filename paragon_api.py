"""
paragon_api.py

PARAGON® Analytics API
────────────────────────────────────────
Uses the existing ETL pipeline + Supabase schema:

Pipelines:
- etl.metric_loader.load_metrics_for
- etl.scoring_engine.score_metrics
- etl.trend_engine.record_paragon_snapshot

Tables:
- paragon_scores   (latest)
- paragon_trends   (history)

Endpoints:
- GET  /api/paragon/latest
- GET  /api/paragon/latest/{politician_id}
- GET  /api/paragon/trends/latest
- GET  /api/paragon/trends/history/{politician_id}
- GET  /api/paragon/trends/top-risers
- GET  /api/paragon/trends/top-fallers
- GET  /api/paragon/trends/momentum/{politician_id}
- GET  /api/paragon/dashboard
- POST /api/paragon/recompute/{politician_id}
- POST /api/paragon/recompute-all
"""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime

from fastapi import APIRouter, HTTPException

from utils.supabase_client import _get
from etl.metric_loader import load_metrics_for
from etl.scoring_engine import score_metrics
from etl.trend_engine import record_paragon_snapshot


router = APIRouter(prefix="/api/paragon", tags=["PARAGON Analytics"])


# =====================================================================
# Safe getter wrapper
# =====================================================================
def _fetch_safe(table: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return _get(table, params) or []
    except Exception as e:
        print(f"[paragon_api] Supabase fetch failed ({table}): {e}")
        return []


# =====================================================================
# Normalize DB row → frontend-ready format
# =====================================================================
def _normalize_paragon_row(row: Dict[str, Any]) -> Dict[str, Any]:
    dims = row.get("dimensions_json") or []
    if not isinstance(dims, list):
        dims = []

    dimensions = [
        {"dimension": d.get("dimension"), "score": int(d.get("score", 0))}
        for d in dims
        if isinstance(d, dict)
    ]

    return {
        **row,
        "overall_score": int(row.get("overall_score", 0) or 0),
        "dimensions": dimensions,
        "dimensions_json": dims,
    }


# =====================================================================
# Compute deltas from paragon_trends
# =====================================================================
def _compute_deltas(history: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    grouped: Dict[int, List[Dict[str, Any]]] = {}

    for row in history:
        pid = row.get("politician_id")
        if pid is None:
            continue
        try:
            pid = int(pid)
        except Exception:
            continue
        grouped.setdefault(pid, []).append(row)

    deltas: Dict[int, Dict[str, Any]] = {}

    for pid, rows in grouped.items():
        if len(rows) < 2:
            continue

        rows_sorted = sorted(
            rows,
            key=lambda r: r.get("calculated_at") or "",
            reverse=True,
        )

        new_score = int(rows_sorted[0].get("overall_score", 0) or 0)
        prev_score = int(rows_sorted[1].get("overall_score", 0) or 0)

        deltas[pid] = {
            "politician_id": pid,
            "name": (rows_sorted[0].get("politicians") or {}).get("name"),
            "new_score": new_score,
            "previous_score": prev_score,
            "delta": new_score - prev_score,
        }

    return deltas


# =====================================================================
# 1. Latest Live Scores
# =====================================================================
@router.get("/latest")
def get_latest_scores(limit: int = 500):
    data = _fetch_safe(
        "paragon_scores",
        {"select": "*,politicians(*)", "order": "overall_score.desc", "limit": limit},
    )
    normalized = [_normalize_paragon_row(x) for x in data]
    return {"count": len(normalized), "results": normalized}


@router.get("/latest/{politician_id}")
def get_latest_score_for(politician_id: int):
    data = _fetch_safe(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "politician_id": f"eq.{politician_id}",
            "limit": 1,
        },
    )
    if not data:
        raise HTTPException(status_code=404, detail="Politician score not found")
    return _normalize_paragon_row(data[0])


# =====================================================================
# 2. Global Trend History
# =====================================================================
@router.get("/trends/latest")
def get_latest_trends(limit: int = 500):
    data = _fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": limit},
    )
    normalized = [_normalize_paragon_row(x) for x in data]
    return {"count": len(normalized), "results": normalized}


@router.get("/trends/history/{politician_id}")
def get_trend_history(politician_id: int, limit: int = 50):
    data = _fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "politician_id": f"eq.{politician_id}",
            "order": "calculated_at.desc",
            "limit": limit,
        },
    )
    normalized = [_normalize_paragon_row(x) for x in data]
    return {"count": len(normalized), "results": normalized}


# =====================================================================
# 3. Risers / Fallers
# =====================================================================
@router.get("/trends/top-risers")
def get_top_risers(limit: int = 10, scan_limit: int = 500):
    history = _fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": scan_limit},
    )
    deltas = _compute_deltas(history)

    risers = sorted(
        [d for d in deltas.values() if d["delta"] > 0],
        key=lambda x: x["delta"],
        reverse=True,
    )

    return {"count": len(risers), "results": risers[:limit]}


@router.get("/trends/top-fallers")
def get_top_fallers(limit: int = 10, scan_limit: int = 500):
    history = _fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": scan_limit},
    )
    deltas = _compute_deltas(history)

    fallers = sorted(
        [d for d in deltas.values() if d["delta"] < 0],
        key=lambda x: x["delta"],
    )

    return {"count": len(fallers), "results": fallers[:limit]}


# =====================================================================
# 4. Momentum
# =====================================================================
@router.get("/trends/momentum/{politician_id}")
def get_momentum(politician_id: int):
    rows = _fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "politician_id": f"eq.{politician_id}",
            "order": "calculated_at.desc",
            "limit": 2,
        },
    )

    if len(rows) < 2:
        return {"message": "Not enough data", "delta": 0}

    new_score = int(rows[0].get("overall_score", 0) or 0)
    prev_score = int(rows[1].get("overall_score", 0) or 0)

    return {
        "politician_id": politician_id,
        "name": (rows[0].get("politicians") or {}).get("name"),
        "new_score": new_score,
        "previous_score": prev_score,
        "delta": new_score - prev_score,
    }


# =====================================================================
# 5. Dashboard Aggregator
# =====================================================================
@router.get("/dashboard")
def get_paragon_dashboard(limit: int = 10, scan_limit: int = 500):
    latest_scores = _fetch_safe(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "order": "overall_score.desc",
            "limit": max(limit, 50),
        },
    )
    latest_scores = [_normalize_paragon_row(x) for x in latest_scores]

    trend_history = _fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": scan_limit},
    )
    trend_history_norm = [_normalize_paragon_row(x) for x in trend_history]

    deltas = _compute_deltas(trend_history)

    top_risers = sorted(
        [d for d in deltas.values() if d["delta"] > 0],
        key=lambda x: x["delta"],
        reverse=True,
    )[:limit]

    top_fallers = sorted(
        [d for d in deltas.values() if d["delta"] < 0],
        key=lambda x: x["delta"],
    )[:limit]

    return {
        "latestScores": latest_scores[:limit],
        "topRisers": top_risers,
        "topFallers": top_fallers,
        "recentTrends": trend_history_norm[: min(len(trend_history_norm), 200)],
    }


# =====================================================================
# 6. Real-time recomputation (ETL pipeline)
# =====================================================================
@router.post("/recompute/{politician_id}")
def recompute_paragon_score(politician_id: int):
    try:
        metrics = load_metrics_for(politician_id)
        if not metrics:
            raise HTTPException(status_code=404, detail="No metrics found for this politician")

        scoring = score_metrics(metrics)
        snapshot = record_paragon_snapshot(politician_id, scoring)

        return {
            "politician_id": politician_id,
            "overall_score": snapshot["overall_score"],
            "dimensions": snapshot["dimensions"],
            "dimensions_json": snapshot["dimensions"],
            "snapshot": snapshot,
            "message": "PARAGON score recomputed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[paragon_api] recompute failed: {e}")
        raise HTTPException(status_code=500, detail="PARAGON recomputation failed")


@router.post("/recompute-all")
def recompute_all(scan_limit: int = 500):
    rows = _fetch_safe(
        "politicians",
        {"select": "id", "order": "id.asc", "limit": scan_limit},
    )

    ids: List[int] = []
    for r in rows:
        try:
            ids.append(int(r["id"]))
        except Exception:
            continue

    updated = 0
    failed: List[Dict[str, Any]] = []

    for pid in ids:
        try:
            metrics = load_metrics_for(pid)
            if not metrics:
                failed.append({"politician_id": pid, "error": "no metrics"})
                continue

            scoring = score_metrics(metrics)
            record_paragon_snapshot(pid, scoring)
            updated += 1

        except Exception as e:
            failed.append({"politician_id": pid, "error": str(e)})

    return {
        "message": "PARAGON recomputation completed",
        "updated_profiles": updated,
        "failed": failed[:50],
        "timestamp": datetime.utcnow().isoformat(),
    }
