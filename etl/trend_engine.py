"""
trend_engine.py

Persists PARAGON scoring results into Supabase.

Tables:
- paragon_scores   → latest snapshot (stores overall_score)
- paragon_trends   → historical series (dimensions only)

IMPORTANT:
- paragon_trends does NOT store a numeric score column
- score is derived from dimensions at read time
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from utils.paragon_constants import PARAGON_DIMENSIONS
from utils.supabase_client import supabase_upsert, supabase_insert


# =====================================================================
# Utilities
# =====================================================================

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dimensions(dimensions: Any) -> List[Dict[str, Any]]:
    """
    Ensures dimensions_json is always:
    - exactly the 7 official PARAGON dimensions
    - ordered exactly as PARAGON_DIMENSIONS
    - clamped score range 0..100
    - missing dimensions filled with neutral score=50
    - unknown/legacy dimensions ignored
    """
    if not isinstance(dimensions, list):
        dimensions = []

    by_name: Dict[str, Dict[str, Any]] = {}

    # Deduplicate (last wins) and keep only official contract dims
    for d in dimensions:
        if not isinstance(d, dict):
            continue

        name = d.get("dimension")
        if not isinstance(name, str) or not name:
            continue

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


# =====================================================================
# 1. Latest snapshot (WITH SCORE)
# =====================================================================

def write_latest_paragon_score(
    *,
    politician_id: int,
    overall_score: int,
    dimensions: Any,
    calculated_at: Optional[str] = None,
):
    payload = {
        "politician_id": int(politician_id),
        "overall_score": int(overall_score),
        "dimensions_json": _safe_dimensions(dimensions),
        "calculated_at": calculated_at or _now_iso(),
    }

    print(
        f"[trend_engine] UPSERT paragon_scores "
        f"(politician_id={politician_id}, overall={overall_score})"
    )

    return supabase_upsert(
        table="paragon_scores",
        records=[payload],
        conflict_col="politician_id",
    )


# =====================================================================
# 2. Historical trend point (NO SCORE COLUMN)
# =====================================================================

def append_paragon_trend_point(
    *,
    politician_id: int,
    dimensions: Any,
    calculated_at: Optional[str] = None,
):
    payload = {
        "politician_id": int(politician_id),
        "dimensions_json": _safe_dimensions(dimensions),
        "calculated_at": calculated_at or _now_iso(),
    }

    print(
        f"[trend_engine] INSERT paragon_trends "
        f"(politician_id={politician_id}, dims={len(payload['dimensions_json'])})"
    )

    return supabase_insert(
        table="paragon_trends",
        records=[payload],
    )


# =====================================================================
# 3. Aggregator
# =====================================================================

def record_paragon_snapshot(
    politician_id: int,
    scoring_result: Dict[str, Any],
) -> Dict[str, Any]:
    if not scoring_result:
        raise ValueError("Empty scoring_result")

    overall_score = int(scoring_result.get("overall_score", 0) or 0)
    dimensions = scoring_result.get("dimensions", [])
    ts = _now_iso()

    latest_row = write_latest_paragon_score(
        politician_id=politician_id,
        overall_score=overall_score,
        dimensions=dimensions,
        calculated_at=ts,
    )

    trend_row = append_paragon_trend_point(
        politician_id=politician_id,
        dimensions=dimensions,
        calculated_at=ts,
    )

    return {
        "politician_id": politician_id,
        "overall_score": overall_score,
        "dimensions": _safe_dimensions(dimensions),
        "calculated_at": ts,
        "latest_row": latest_row,
        "trend_row": trend_row,
    }
