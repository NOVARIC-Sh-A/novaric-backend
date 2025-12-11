"""
trend_engine.py

Persists PARAGON results into Supabase:

- paragon_scores  (latest snapshot)
- paragon_trends  (historical series)

Now supports:
- dimensions_json (JSONB)
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from utils.supabase_client import supabase_upsert, supabase_insert


# -------------------------------------------------------------------
# Util
# -------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# -------------------------------------------------------------------
# 1. Write latest snapshot
# -------------------------------------------------------------------
def write_latest_paragon_score(
    politician_id: int,
    overall_score: int,
    dimensions: Any,
    calculated_at: Optional[str] = None,
):
    payload = {
        "politician_id": politician_id,
        "overall_score": overall_score,
        "dimensions_json": dimensions,
    }

    if calculated_at:
        payload["calculated_at"] = calculated_at

    try:
        print(
            f"[trend_engine] Upserting latest score for {politician_id} "
            f"(overall={overall_score}, dims={len(dimensions)})"
        )
        return supabase_upsert(
            table="paragon_scores",
            records=[payload],
            conflict_col="politician_id",
        )
    except Exception as e:
        print(f"[trend_engine] ERROR: Failed upsert → {e}")
        raise


# -------------------------------------------------------------------
# 2. Append history row
# -------------------------------------------------------------------
def append_paragon_trend_point(
    politician_id: int,
    overall_score: int,
    dimensions: Any,
    calculated_at: Optional[str] = None,
):
    payload = {
        "politician_id": politician_id,
        "overall_score": overall_score,
        "dimensions_json": dimensions,
    }

    if calculated_at:
        payload["calculated_at"] = calculated_at

    try:
        print(
            f"[trend_engine] Insert trend point for {politician_id} "
            f"(overall={overall_score}, dims={len(dimensions)})"
        )
        return supabase_insert(
            table="paragon_trends",
            records=[payload],
        )
    except Exception as e:
        print(f"[trend_engine] ERROR: Failed insert → {e}")
        raise


# -------------------------------------------------------------------
# 3. Top-level aggregator
# -------------------------------------------------------------------
def record_paragon_snapshot(
    politician_id: int,
    scoring_result: Dict[str, Any],
):
    overall_score = int(scoring_result.get("overall_score", 0))
    dimensions = scoring_result.get("dimensions", [])
    ts = _now_iso()

    score_row = write_latest_paragon_score(
        politician_id=politician_id,
        overall_score=overall_score,
        dimensions=dimensions,
        calculated_at=ts,
    )

    trend_row = append_paragon_trend_point(
        politician_id=politician_id,
        overall_score=overall_score,
        dimensions=dimensions,
        calculated_at=ts,
    )

    return {
        "politician_id": politician_id,
        "overall_score": overall_score,
        "dimensions": dimensions,
        "calculated_at": ts,
        "score_row": score_row,
        "trend_row": trend_row,
    }
