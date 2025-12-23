"""
paragon_api.py

PARAGON® Analytics API
────────────────────────────────────────
- Latest live scores (from snapshots)
- Single politician score
- Risers / Fallers (derived deltas)
- Momentum
- Dashboard aggregation
- Real-time recomputation (LIVE)
"""

from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException

from utils.supabase_client import supabase
from services.paragon_live import (
    compute_and_snapshot_paragon,
    recompute_all_paragon,
)
from services.paragon_repository import get_paragon_snapshot


router = APIRouter(
    prefix="/api/paragon",
    tags=["PARAGON Analytics"],
)


# ============================================================
# Helpers
# ============================================================

def _normalize_snapshot(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes snapshot row → frontend-ready shape.
    """
    breakdown = row.get("breakdown") or []

    dimensions = [
        {
            "dimension": d.get("dimension"),
            "score": int(d.get("score", 0)),
        }
        for d in breakdown
        if isinstance(d, dict)
    ]

    return {
        "politician_id": row.get("politician_id"),
        "overall_score": int(row.get("score", 0)),
        "calculated_at": row.get("computed_at"),
        "dimensions": dimensions,
        "dimensions_json": breakdown,
        "version": row.get("version"),
    }


def _fetch_all_snapshots(limit: int = 500) -> List[Dict[str, Any]]:
    res = (
        supabase
        .table("paragon_snapshots")
        .select("*")
        .order("computed_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []


def _compute_deltas(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Computes score deltas per politician from snapshots.
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for r in rows:
        pid = r.get("politician_id")
        if not pid:
            continue
        grouped.setdefault(pid, []).append(r)

    deltas: Dict[str, Dict[str, Any]] = {}

    for pid, snapshots in grouped.items():
        if len(snapshots) < 2:
            continue

        snapshots_sorted = sorted(
            snapshots,
            key=lambda x: x.get("computed_at") or "",
            reverse=True,
        )

        new_score = int(snapshots_sorted[0]["score"])
        prev_score = int(snapshots_sorted[1]["score"])

        deltas[pid] = {
            "politician_id": pid,
            "new_score": new_score,
            "previous_score": prev_score,
            "delta": new_score - prev_score,
        }

    return deltas


# ============================================================
# 1. Latest Live Scores
# ============================================================

@router.get("/latest")
def get_latest_scores():
    rows = _fetch_all_snapshots(limit=500)

    # keep only latest snapshot per politician
    latest: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        pid = r["politician_id"]
        if pid not in latest:
            latest[pid] = r

    normalized = [
        _normalize_snapshot(v)
        for v in latest.values()
    ]

    normalized.sort(
        key=lambda x: x["overall_score"],
        reverse=True,
    )

    return {
        "count": len(normalized),
        "results": normalized,
    }


@router.get("/latest/{politician_id}")
def get_latest_score_for(politician_id: str):
    snap = get_paragon_snapshot(politician_id)
    if not snap:
        raise HTTPException(404, "PARAGON snapshot not found")

    return {
        "politician_id": snap.politician_id,
        "overall_score": snap.score,
        "dimensions": snap.breakdown,
        "dimensions_json": snap.breakdown,
        "version": snap.version,
        "calculated_at": snap.computed_at,
    }


# ============================================================
# 2. Risers / Fallers
# ============================================================

@router.get("/trends/top-risers")
def get_top_risers(limit: int = 10):
    rows = _fetch_all_snapshots(limit=500)
    deltas = _compute_deltas(rows)

    risers = sorted(
        [d for d in deltas.values() if d["delta"] > 0],
        key=lambda x: x["delta"],
        reverse=True,
    )

    return {
        "count": len(risers),
        "results": risers[:limit],
    }


@router.get("/trends/top-fallers")
def get_top_fallers(limit: int = 10):
    rows = _fetch_all_snapshots(limit=500)
    deltas = _compute_deltas(rows)

    fallers = sorted(
        [d for d in deltas.values() if d["delta"] < 0],
        key=lambda x: x["delta"],
    )

    return {
        "count": len(fallers),
        "results": fallers[:limit],
    }


# ============================================================
# 3. Momentum (single politician)
# ============================================================

@router.get("/trends/momentum/{politician_id}")
def get_momentum(politician_id: str):
    rows = (
        supabase
        .table("paragon_snapshots")
        .select("*")
        .eq("politician_id", politician_id)
        .order("computed_at", desc=True)
        .limit(2)
        .execute()
        .data
    )

    if not rows or len(rows) < 2:
        return {
            "politician_id": politician_id,
            "delta": 0,
            "message": "Not enough data",
        }

    new_score = int(rows[0]["score"])
    prev_score = int(rows[1]["score"])

    return {
        "politician_id": politician_id,
        "new_score": new_score,
        "previous_score": prev_score,
        "delta": new_score - prev_score,
    }


# ============================================================
# 4. Dashboard Aggregator
# ============================================================

@router.get("/dashboard")
def get_paragon_dashboard(limit: int = 10):
    rows = _fetch_all_snapshots(limit=500)

    latest: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        pid = r["politician_id"]
        if pid not in latest:
            latest[pid] = r

    latest_norm = [
        _normalize_snapshot(v)
        for v in latest.values()
    ]
    latest_norm.sort(
        key=lambda x: x["overall_score"],
        reverse=True,
    )

    deltas = _compute_deltas(rows)

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
        "latestScores": latest_norm[:limit],
        "topRisers": top_risers,
        "topFallers": top_fallers,
    }


# ============================================================
# 5. Real-time recomputation (LIVE)
# ============================================================

@router.post("/recompute/{politician_id}")
def recompute_paragon_live(politician_id: str):
    try:
        snapshot = compute_and_snapshot_paragon(politician_id)
        return {
            "message": "PARAGON recomputed successfully",
            "snapshot": snapshot,
        }
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"PARAGON recomputation failed: {e}")


@router.post("/recompute-all")
def recompute_all():
    updated = recompute_all_paragon()
    return {
        "message": "PARAGON recomputation completed",
        "updated_profiles": updated,
        "timestamp": datetime.utcnow().isoformat(),
    }
