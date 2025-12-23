"""
paragon_api.py

PARAGON® Analytics API
────────────────────────────────────────
ETL pipeline:
- metric_loader.load_metrics_for
- scoring_engine.score_metrics
- trend_engine.record_paragon_snapshot
"""

from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime

from fastapi import APIRouter, HTTPException

from utils.supabase_client import _get
from etl.metric_loader import load_metrics_for
from etl.scoring_engine import score_metrics
from etl.trend_engine import record_paragon_snapshot


# =====================================================================
# Router (Option A: NO /api here)
# =====================================================================

router = APIRouter(prefix="/paragon", tags=["PARAGON Analytics"])


# =====================================================================
# Supabase safe fetch
# =====================================================================

def _fetch_safe(table: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    try:
        return _get(table, params) or []
    except Exception as e:
        print(f"[paragon_api] Supabase fetch failed ({table}): {e}")
        return []


# =====================================================================
# Row normalization (schema-resilient)
# =====================================================================

def _extract_score(row: Dict[str, Any]) -> int:
    """
    Extracts the score regardless of column naming.
    """
    for key in (
        "overall_score",
        "score",
        "paragon_score",
        "paragon",
        "value",
        "overall",
    ):
        if key in row and row[key] is not None:
            try:
                return int(row[key])
            except Exception:
                pass
    return 0


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    dims = row.get("dimensions_json") or []
    if not isinstance(dims, list):
        dims = []

    return {
        **row,
        "overall_score": _extract_score(row),
        "dimensions": dims,
        "dimensions_json": dims,
    }


# =====================================================================
# 1. Latest scores
# =====================================================================

@router.get("/latest")
def get_latest_scores(limit: int = 500):
    rows = _fetch_safe(
        "paragon_scores",
        {"select": "*,politicians(*)", "order": "overall_score.desc", "limit": limit},
    )
    data = [_normalize_row(r) for r in rows]
    return {"count": len(data), "results": data}


@router.get("/latest/{politician_id}")
def get_latest_score_for(politician_id: int):
    rows = _fetch_safe(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "politician_id": f"eq.{politician_id}",
            "limit": 1,
        },
    )

    if not rows:
        raise HTTPException(status_code=404, detail="Politician score not found")

    return _normalize_row(rows[0])


# =====================================================================
# 2. Trend endpoints
# =====================================================================

@router.get("/trends/latest")
def get_latest_trends(limit: int = 500):
    rows = _fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": limit},
    )
    data = [_normalize_row(r) for r in rows]
    return {"count": len(data), "results": data}


@router.get("/trends/history/{politician_id}")
def get_trend_history(politician_id: int, limit: int = 50):
    rows = _fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "politician_id": f"eq.{politician_id}",
            "order": "calculated_at.desc",
            "limit": limit,
        },
    )
    data = [_normalize_row(r) for r in rows]
    return {"count": len(data), "results": data}


# =====================================================================
# 3. Delta computation
# =====================================================================

def _compute_deltas(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[int, List[Dict[str, Any]]] = {}

    for row in history:
        pid = row.get("politician_id")
        if isinstance(pid, int):
            grouped.setdefault(pid, []).append(row)

    deltas: List[Dict[str, Any]] = []

    for pid, rows in grouped.items():
        if len(rows) < 2:
            continue

        rows = sorted(
            rows,
            key=lambda r: r.get("calculated_at") or "",
            reverse=True,
        )

        new_score = _extract_score(rows[0])
        prev_score = _extract_score(rows[1])

        deltas.append(
            {
                "politician_id": pid,
                "name": (rows[0].get("politicians") or {}).get("name"),
                "new_score": new_score,
                "previous_score": prev_score,
                "delta": new_score - prev_score,
            }
        )

    return deltas


@router.get("/trends/top-risers")
def get_top_risers(limit: int = 10, scan_limit: int = 500):
    history = _fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": scan_limit},
    )
    deltas = [d for d in _compute_deltas(history) if d["delta"] > 0]
    deltas.sort(key=lambda x: x["delta"], reverse=True)
    return {"count": len(deltas), "results": deltas[:limit]}


@router.get("/trends/top-fallers")
def get_top_fallers(limit: int = 10, scan_limit: int = 500):
    history = _fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": scan_limit},
    )
    deltas = [d for d in _compute_deltas(history) if d["delta"] < 0]
    deltas.sort(key=lambda x: x["delta"])
    return {"count": len(deltas), "results": deltas[:limit]}


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
        return {"politician_id": politician_id, "delta": 0}

    new_score = _extract_score(rows[0])
    prev_score = _extract_score(rows[1])

    return {
        "politician_id": politician_id,
        "name": (rows[0].get("politicians") or {}).get("name"),
        "new_score": new_score,
        "previous_score": prev_score,
        "delta": new_score - prev_score,
    }


# =====================================================================
# 4. Dashboard
# =====================================================================

@router.get("/dashboard")
def get_paragon_dashboard(limit: int = 10, scan_limit: int = 500):
    latest = _fetch_safe(
        "paragon_scores",
        {"select": "*,politicians(*)", "order": "overall_score.desc", "limit": 50},
    )
    trends = _fetch_safe(
        "paragon_trends",
        {"select": "*,politicians(*)", "order": "calculated_at.desc", "limit": scan_limit},
    )

    latest = [_normalize_row(r) for r in latest]
    trends = [_normalize_row(r) for r in trends]

    deltas = _compute_deltas(trends)

    return {
        "latestScores": latest[:limit],
        "topRisers": sorted(
            [d for d in deltas if d["delta"] > 0],
            key=lambda x: x["delta"],
            reverse=True,
        )[:limit],
        "topFallers": sorted(
            [d for d in deltas if d["delta"] < 0],
            key=lambda x: x["delta"],
        )[:limit],
        "recentTrends": trends[:200],
    }


# =====================================================================
# 5. Recomputation (SAFE MODE only)
# =====================================================================

@router.post("/recompute/{politician_id}")
def recompute_paragon_score(politician_id: int):
    try:
        metrics = load_metrics_for(politician_id, safe_mode=True)
        scoring = score_metrics(metrics)
        snapshot = record_paragon_snapshot(politician_id, scoring)

        return {
            "politician_id": politician_id,
            "overall_score": snapshot["overall_score"],
            "dimensions": snapshot["dimensions"],
            "calculated_at": snapshot["calculated_at"],
            "message": "PARAGON score recomputed successfully",
        }

    except Exception as e:
        print(f"[paragon_api] recompute failed: {e}")
        raise HTTPException(status_code=500, detail="PARAGON recomputation failed")


@router.post("/recompute-all")
def recompute_all(scan_limit: int = 500):
    rows = _fetch_safe("politicians", {"select": "id", "limit": scan_limit})

    updated = 0
    failed: List[Dict[str, Any]] = []

    for r in rows:
        try:
            pid = int(r["id"])
            metrics = load_metrics_for(pid, safe_mode=True)
            scoring = score_metrics(metrics)
            record_paragon_snapshot(pid, scoring)
            updated += 1
        except Exception as e:
            failed.append({"politician_id": r.get("id"), "error": str(e)})

    return {
        "message": "PARAGON recomputation completed",
        "updated_profiles": updated,
        "failed": failed[:25],
        "timestamp": datetime.utcnow().isoformat(),
    }
