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

Notes:
- Uses Supabase table: paragon_snapshots (immutable history-by-upsert semantics)
- compute_and_snapshot_paragon() persists snapshot rows
- get_paragon_snapshot() reads latest snapshot for a politician_id
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
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
    Normalizes snapshot row → frontend-ready shape:

    {
      politician_id: int|str,
      overall_score: int,
      calculated_at: str,
      dimensions: [{dimension, score}],
      dimensions_json: [...],
      version: str
    }
    """
    breakdown = row.get("breakdown") or []
    if not isinstance(breakdown, list):
        breakdown = []

    dimensions = [
        {"dimension": d.get("dimension"), "score": int(d.get("score", 0))}
        for d in breakdown
        if isinstance(d, dict)
    ]

    return {
        "politician_id": row.get("politician_id"),
        "overall_score": int(row.get("score", 0)),
        "calculated_at": row.get("computed_at"),
        "dimensions": dimensions,
        "dimensions_json": breakdown,
        "version": row.get("version", "paragon_v1"),
    }


def _fetch_all_snapshots(limit: int = 500) -> List[Dict[str, Any]]:
    """
    Returns newest-first snapshot rows.
    """
    try:
        res = (
            supabase
            .table("paragon_snapshots")
            .select("*")
            .order("computed_at", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception as e:
        print(f"[paragon_api] _fetch_all_snapshots failed: {e}")
        return []


def _compute_deltas(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Computes score deltas per politician from snapshot history.

    Returns:
      {
        politician_id: {
          politician_id, new_score, previous_score, delta
        },
        ...
      }
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for r in rows:
        pid = r.get("politician_id")
        if pid is None:
            continue
        key = str(pid)
        grouped.setdefault(key, []).append(r)

    deltas: Dict[str, Dict[str, Any]] = {}

    for pid, snapshots in grouped.items():
        if len(snapshots) < 2:
            continue

        snapshots_sorted = sorted(
            snapshots,
            key=lambda x: (x.get("computed_at") or ""),
            reverse=True,
        )

        try:
            new_score = int(snapshots_sorted[0].get("score", 0))
            prev_score = int(snapshots_sorted[1].get("score", 0))
        except Exception:
            continue

        deltas[pid] = {
            "politician_id": pid,
            "new_score": new_score,
            "previous_score": prev_score,
            "delta": new_score - prev_score,
        }

    return deltas


def _latest_per_politician(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    From newest-first rows, keep only the first (latest) row per politician.
    """
    latest: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        pid = r.get("politician_id")
        if pid is None:
            continue
        key = str(pid)
        if key not in latest:
            latest[key] = r
    return latest


# ============================================================
# 1. Latest Live Scores
# ============================================================

@router.get("/latest")
def get_latest_scores(limit: int = 500):
    rows = _fetch_all_snapshots(limit=limit)

    latest = _latest_per_politician(rows)

    normalized = [_normalize_snapshot(v) for v in latest.values()]
    normalized.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

    return {"count": len(normalized), "results": normalized}


@router.get("/latest/{politician_id}")
def get_latest_score_for(politician_id: int):
    """
    Returns latest snapshot for one politician.
    """
    snap = get_paragon_snapshot(str(politician_id))
    if not snap:
        raise HTTPException(status_code=404, detail="PARAGON snapshot not found")

    # snap.breakdown is already the dimension list used by frontend
    return {
        "politician_id": snap.politician_id,
        "overall_score": int(snap.score),
        "dimensions": snap.breakdown,
        "dimensions_json": snap.breakdown,
        "version": snap.version,
        "calculated_at": snap.computed_at,
    }


# ============================================================
# 2. Risers / Fallers
# ============================================================

@router.get("/trends/top-risers")
def get_top_risers(limit: int = 10, scan_limit: int = 500):
    rows = _fetch_all_snapshots(limit=scan_limit)
    deltas = _compute_deltas(rows)

    risers = sorted(
        [d for d in deltas.values() if d["delta"] > 0],
        key=lambda x: x["delta"],
        reverse=True,
    )

    return {"count": len(risers), "results": risers[:limit]}


@router.get("/trends/top-fallers")
def get_top_fallers(limit: int = 10, scan_limit: int = 500):
    rows = _fetch_all_snapshots(limit=scan_limit)
    deltas = _compute_deltas(rows)

    fallers = sorted(
        [d for d in deltas.values() if d["delta"] < 0],
        key=lambda x: x["delta"],
    )

    return {"count": len(fallers), "results": fallers[:limit]}


# ============================================================
# 3. Momentum (single politician)
# ============================================================

@router.get("/trends/momentum/{politician_id}")
def get_momentum(politician_id: int):
    """
    Momentum = latest score delta vs previous snapshot.
    """
    try:
        rows = (
            supabase
            .table("paragon_snapshots")
            .select("*")
            .eq("politician_id", str(politician_id))
            .order("computed_at", desc=True)
            .limit(2)
            .execute()
            .data
        ) or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabase read failed: {e}")

    if len(rows) < 2:
        return {"politician_id": str(politician_id), "delta": 0, "message": "Not enough data"}

    new_score = int(rows[0].get("score", 0))
    prev_score = int(rows[1].get("score", 0))

    return {
        "politician_id": str(politician_id),
        "new_score": new_score,
        "previous_score": prev_score,
        "delta": new_score - prev_score,
    }


# ============================================================
# 4. Dashboard Aggregator
# ============================================================

@router.get("/dashboard")
def get_paragon_dashboard(limit: int = 10, scan_limit: int = 500):
    rows = _fetch_all_snapshots(limit=scan_limit)
    latest = _latest_per_politician(rows)

    latest_norm = [_normalize_snapshot(v) for v in latest.values()]
    latest_norm.sort(key=lambda x: x.get("overall_score", 0), reverse=True)

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
def recompute_paragon_live(politician_id: int):
    """
    Recompute + persist snapshot for a single politician.
    """
    try:
        snapshot = compute_and_snapshot_paragon(str(politician_id))
        return {"message": "PARAGON recomputed successfully", "snapshot": snapshot}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PARAGON recomputation failed: {e}")


@router.post("/recompute-all")
def recompute_all():
    """
    Recompute + persist snapshots for all politicians (as defined by loader).
    """
    try:
        updated = recompute_all_paragon()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PARAGON recompute-all failed: {e}")

    return {
        "message": "PARAGON recomputation completed",
        "updated_profiles": updated,
        "timestamp": datetime.utcnow().isoformat(),
    }
