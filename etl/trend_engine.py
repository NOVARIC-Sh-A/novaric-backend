"""
trend_engine.py

Responsible for persisting PARAGON results into Supabase:

- paragon_scores  (latest snapshot per politician)
- paragon_trends  (append-only historical time series)

Now upgraded to store:
    - dimensions_json (JSONB)
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from utils.supabase_client import supabase_upsert, supabase_insert


# =====================================================================
# Helpers
# =====================================================================
def _now_iso() -> str:
    """
    Returns current UTC timestamp in ISO8601 format.
    """
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# 1. Latest score snapshot (paragon_scores)
# =====================================================================
def write_latest_paragon_score(
    politician_id: int,
    overall_score: int,
    dimensions: Any,
    calculated_at: Optional[str] = None,
) -> Any:
    """
    Upserts the latest PARAGON overall score + dimension scores.

    paragon_scores table now stores:
      - politician_id
      - overall_score
      - calculated_at
      - dimensions_json  (JSONB)
    """

    payload = {
        "politician_id": politician_id,
        "overall_score": overall_score,
        "dimensions_json": dimensions,   # <-- NEW FIELD
    }

    # Optional explicit timestamp override
    if calculated_at:
        payload["calculated_at"] = calculated_at

    try:
        print(
            f"[trend_engine] Upserting latest score for {politician_id} → "
            f"{overall_score}, dimensions={len(dimensions)} items"
        )
        return supabase_upsert(
            table="paragon_scores",
            records=[payload],
            conflict_col="politician_id",
        )
    except Exception as e:
        print(f"[trend_engine] Failed to upsert paragon_scores: {e}")
        raise


# =====================================================================
# 2. Historical trend log (paragon_trends)
# =====================================================================
def append_paragon_trend_point(
    politician_id: int,
    overall_score: int,
    dimensions: Any,
    calculated_at: Optional[str] = None,
) -> Any:
    """
    Inserts a new historical data point into paragon_trends.

    New fields stored:
      - politician_id
      - overall_score
      - calculated_at
      - dimensions_json (JSONB)
    """

    payload = {
        "politician_id": politician_id,
        "overall_score": overall_score,
        "dimensions_json": dimensions,  # <-- NEW FIELD
    }

    if calculated_at:
        payload["calculated_at"] = calculated_at

    try:
        print(
            f"[trend_engine] Inserting trend point for {politician_id} → "
            f"{overall_score}, dimensions={len(dimensions)} items"
        )
        return supabase_insert(
            table="paragon_trends",
            records=[payload],
        )
    except Exception as e:
        print(f"[trend_engine] Failed to insert paragon_trends: {e}")
        raise


# =====================================================================
# 3. High-level convenience: record full snapshot
# =====================================================================
def record_paragon_snapshot(
    politician_id: int,
    scoring_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Called by /recompute/{politician_id} in paragon_api.py

    scoring_result contains:
        {
          "overall_score": 73,
          "dimensions": [
             { "dimension": "...", "score": 78 },
             ...
          ]
        }

    This function:
      - upserts current snapshot into paragon_scores
      - appends new row into paragon_trends
      - returns summary dictionary
    """

    overall_score = int(scoring_result.get("overall_score", 0))
    dimensions = scoring_result.get("dimensions", [])
    timestamp = _now_iso()

    # Write latest score
    score_row = write_latest_paragon_score(
        politician_id=politician_id,
        overall_score=overall_score,
        dimensions=dimensions,      # <-- store dimension data
        calculated_at=timestamp,
    )

    # Append trend log
    trend_row = append_paragon_trend_point(
        politician_id=politician_id,
        overall_score=overall_score,
        dimensions=dimensions,      # <-- store dimension data
        calculated_at=timestamp,
    )

    return {
        "politician_id": politician_id,
        "overall_score": overall_score,
        "dimensions": dimensions,
        "calculated_at": timestamp,
        "score_row": score_row,
        "trend_row": trend_row,
    }
