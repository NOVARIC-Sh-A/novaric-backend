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
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from utils.supabase_client import _get
from utils.paragon_constants import PARAGON_DIMENSIONS
from etl.metric_loader import load_metrics_for
from etl.scoring_engine import score_metrics
from etl.trend_engine import record_paragon_snapshot


# =====================================================================
# ROUTER (Option A — NO /api prefix here)
# Mounted by main.py under /api
# =====================================================================

router = APIRouter(
    prefix="/paragon",
    tags=["PARAGON Analytics"],
)


# =====================================================================
# SUPABASE SAFE FETCH
# =====================================================================

def _fetch_safe(table: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Wrapper around Supabase GET to prevent API crashes.
    """
    try:
        return _get(table, params) or []
    except Exception as e:
        print(f"[paragon_api] Supabase fetch failed ({table}): {e}")
        return []


# =====================================================================
# ROW NORMALIZATION (SCHEMA-RESILIENT)
# =====================================================================

def _extract_score(row: Dict[str, Any]) -> int:
    """
    Extracts score value regardless of historical column naming.
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


def _order_7_dimensions(dims: Any) -> List[Dict[str, Any]]:
    """
    Guarantees the official 7 PARAGON dimensions, ordered exactly as PARAGON_DIMENSIONS.

    Behavior:
    - Accepts any input (list/None/invalid)
    - Deduplicates by dimension name (last one wins)
    - Fills missing official dimensions with neutral score=50
    - Ignores unknown dimensions (e.g. legacy "Momentum & Resilience")
    - Clamps scores to 0..100 for UI stability
    """
    if not isinstance(dims, list):
        dims = []

    by_name: Dict[str, Dict[str, Any]] = {}
    for d in dims:
        if not isinstance(d, dict):
            continue

        name = d.get("dimension")
        if not isinstance(name, str) or not name:
            continue

        # Keep contract stable: only allow official 7 dimensions
        if name not in PARAGON_DIMENSIONS:
            continue

        try:
            score = int(d.get("score", 0) or 0)
        except Exception:
            score = 0

        score = max(0, min(100, score))

        by_name[name] = {
            "dimension": name,
            "score": score,
        }

    ordered: List[Dict[str, Any]] = []
    for name in PARAGON_DIMENSIONS:
        if name in by_name:
            ordered.append(by_name[name])
        else:
            ordered.append({"dimension": name, "score": 50})

    return ordered


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes Supabase row into frontend-safe format.

    Guarantees:
    - overall_score is present (schema-resilient)
    - dimensions/dimensions_json are always 7 official PARAGON dimensions in stable order
    - if overall_score is missing/0 but dimensions exist, it derives a stable overall score
    """
    dims = row.get("dimensions_json") or row.get("dimension_scores") or []
    ordered_dims = _order_7_dimensions(dims)

    overall = _extract_score(row)

    # If score column is missing/legacy, derive from ordered dims (safe for trends rows too)
    if (overall is None) or (overall == 0 and ordered_dims):
        try:
            overall = int(
                sum(int(d.get("score", 0) or 0) for d in ordered_dims) / len(ordered_dims)
            )
        except Exception:
            overall = 0

    return {
        **row,
        "overall_score": int(overall or 0),
        "dimensions": ordered_dims,
        "dimensions_json": ordered_dims,
    }


# =====================================================================
# 1. LATEST SCORES
# =====================================================================

@router.get("/latest")
def get_latest_scores(limit: int = 500):
    rows = _fetch_safe(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "order": "overall_score.desc",
            "limit": limit,
        },
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
# 2. TREND ENDPOINTS
# =====================================================================

@router.get("/trends/latest")
def get_latest_trends(limit: int = 500):
    rows = _fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": limit,
        },
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
# 3. DELTA COMPUTATION
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
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": scan_limit,
        },
    )
    deltas = [d for d in _compute_deltas(history) if d["delta"] > 0]
    deltas.sort(key=lambda x: x["delta"], reverse=True)
    return {"count": len(deltas), "results": deltas[:limit]}


@router.get("/trends/top-fallers")
def get_top_fallers(limit: int = 10, scan_limit: int = 500):
    history = _fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": scan_limit,
        },
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
# 4. DASHBOARD
# =====================================================================

@router.get("/dashboard")
def get_paragon_dashboard(limit: int = 10, scan_limit: int = 500):
    latest = _fetch_safe(
        "paragon_scores",
        {
            "select": "*,politicians(*)",
            "order": "overall_score.desc",
            "limit": 50,
        },
    )
    trends = _fetch_safe(
        "paragon_trends",
        {
            "select": "*,politicians(*)",
            "order": "calculated_at.desc",
            "limit": scan_limit,
        },
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
# 5. RECOMPUTATION (SAFE MODE ONLY)
# =====================================================================

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/recompute/{politician_id}")
def recompute_paragon_score(politician_id: int, request: Request):
    """
    Recomputes the PARAGON score for a single politician.

    Strategy:
    - Preferred: run the metrics+scoring pipeline if available (keeps DB in sync with your new tables).
    - Fallback: legacy metric_loader + trend snapshot (current behavior).
    """
    req_id = request.headers.get("x-request-id") or request.headers.get("x-cloud-trace-context") or ""
    print(f"[paragon_api] recompute start politician_id={politician_id} req={req_id} ts={_utc_now_iso()}")

    try:
        # ------------------------------------------------------------
        # Preferred path: use your working ETL pipeline (if present)
        # ------------------------------------------------------------
        try:
            # Import inside function to avoid import-time failures (Cloud Run safe)
            from etl.run_paragon_pipeline import run_single_politician  # type: ignore

            run_single_politician(int(politician_id))
            # After pipeline run, return freshest score from DB (single source of truth)
            rows = _fetch_safe(
                "paragon_scores",
                {"select": "*", "politician_id": f"eq.{int(politician_id)}", "limit": 1},
            )
            if rows:
                row = _normalize_row(rows[0])
                print(f"[paragon_api] recompute ok (pipeline) politician_id={politician_id} req={req_id}")
                return {
                    "politician_id": politician_id,
                    "overall_score": row.get("overall_score", 0),
                    "dimensions": row.get("dimensions_json") or row.get("dimensions") or [],
                    "calculated_at": row.get("calculated_at") or row.get("last_updated") or _utc_now_iso(),
                    "message": "PARAGON score recomputed successfully",
                }
        except Exception as pipeline_err:
            # Pipeline not installed or failed; continue with legacy safe-mode path
            print(f"[paragon_api] pipeline recompute unavailable/failed politician_id={politician_id}: {pipeline_err}")

        # ------------------------------------------------------------
        # Fallback path (legacy): metric_loader + scoring_engine + trend snapshot
        # ------------------------------------------------------------
        metrics = load_metrics_for(int(politician_id), safe_mode=True)
        scoring = score_metrics(metrics)
        snapshot = record_paragon_snapshot(int(politician_id), scoring)

        print(f"[paragon_api] recompute ok (legacy) politician_id={politician_id} req={req_id}")

        return {
            "politician_id": politician_id,
            "overall_score": snapshot["overall_score"],
            "dimensions": snapshot["dimensions"],
            "calculated_at": snapshot["calculated_at"],
            "message": "PARAGON score recomputed successfully",
        }

    except Exception as e:
        # This is the line you need in Cloud Run to debug real root cause.
        print(f"[paragon_api] recompute failed politician_id={politician_id} req={req_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="PARAGON recomputation failed",
        )


@router.post("/recompute-all")
def recompute_all(scan_limit: int = 500, request: Request | None = None):
    req_id = ""
    if request is not None:
        req_id = request.headers.get("x-request-id") or request.headers.get("x-cloud-trace-context") or ""
    print(f"[paragon_api] recompute-all start scan_limit={scan_limit} req={req_id} ts={_utc_now_iso()}")

    rows = _fetch_safe("politicians", {"select": "id", "limit": scan_limit})

    updated = 0
    failed: List[Dict[str, Any]] = []

    for r in rows:
        try:
            pid = int(r["id"])

            # Preferred pipeline path
            try:
                from etl.run_paragon_pipeline import run_single_politician  # type: ignore
                run_single_politician(pid)
                updated += 1
                continue
            except Exception as pipeline_err:
                print(f"[paragon_api] recompute-all pipeline failed pid={pid}: {pipeline_err}")

            # Fallback legacy path
            metrics = load_metrics_for(pid, safe_mode=True)
            scoring = score_metrics(metrics)
            record_paragon_snapshot(pid, scoring)
            updated += 1

        except Exception as e:
            failed.append(
                {
                    "politician_id": r.get("id"),
                    "error": str(e),
                }
            )

    return {
        "message": "PARAGON recomputation completed",
        "updated_profiles": updated,
        "failed": failed[:25],
        "timestamp": datetime.utcnow().isoformat(),
    }
