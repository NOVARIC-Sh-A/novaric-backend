"""
trend_engine.py

Persists PARAGON scoring results into Supabase.

Tables:
- paragon_scores   → latest snapshot (1 row per politician)
- paragon_trends   → historical time series (append-only)

This module is SCHEMA-RESILIENT:
- paragon_scores is assumed to have: politician_id, overall_score, dimensions_json, calculated_at
- paragon_trends score column name is AUTO-DETECTED at runtime (schema cache-safe)

It will:
- Read 1 sample row from paragon_trends to infer the score column
- If table empty or inference fails, it will attempt inserts using common score column candidates
"""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Dict, Any, Optional, List, Tuple

from utils.supabase_client import supabase_upsert, supabase_insert, _get


# =====================================================================
# Utilities
# =====================================================================

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_dimensions(dimensions: Any) -> List[Dict[str, Any]]:
    if not isinstance(dimensions, list):
        return []

    out: List[Dict[str, Any]] = []
    for d in dimensions:
        if isinstance(d, dict):
            out.append(
                {
                    "dimension": d.get("dimension"),
                    "score": int(d.get("score", 0) or 0),
                }
            )
    return out


# =====================================================================
# Schema inference for paragon_trends
# =====================================================================

# Reasonable candidates seen in real-world trend tables
_SCORE_COL_CANDIDATES: Tuple[str, ...] = (
    "overall_score",
    "score",
    "paragon_score",
    "paragon",
    "value",
    "metric_value",
    "overall",
)

# Timestamp candidates (you already use calculated_at elsewhere; keep that default)
_TS_COL_CANDIDATES: Tuple[str, ...] = (
    "calculated_at",
    "created_at",
    "timestamp",
    "ts",
)


@lru_cache(maxsize=1)
def _infer_paragon_trends_columns() -> Tuple[Optional[str], Optional[str]]:
    """
    Attempts to infer:
    - score column name in paragon_trends
    - timestamp column name in paragon_trends

    Returns (score_col, ts_col). Either may be None if undetectable.
    """
    try:
        rows = _get("paragon_trends", {"select": "*", "limit": 1})
        if not rows:
            return (None, None)

        sample = rows[0]
        if not isinstance(sample, dict):
            return (None, None)

        keys = set(sample.keys())

        score_col = next((c for c in _SCORE_COL_CANDIDATES if c in keys), None)
        ts_col = next((c for c in _TS_COL_CANDIDATES if c in keys), None)

        return (score_col, ts_col)

    except Exception:
        # If inference fails (permissions, table empty, etc.), return None and fall back to trial insert.
        return (None, None)


# =====================================================================
# 1) Latest snapshot (UPSERT) → paragon_scores
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
# 2) Historical trend point (INSERT) → paragon_trends
# =====================================================================

def append_paragon_trend_point(
    *,
    politician_id: int,
    overall_score: int,
    dimensions: Any,
    calculated_at: Optional[str] = None,
):
    """
    Appends a new trend record into paragon_trends.

    The score column is auto-detected. If it cannot be detected, we attempt
    a safe multi-try insert across common column candidates until one matches
    the schema cache.
    """

    dims = _safe_dimensions(dimensions)
    ts = calculated_at or _now_iso()

    score_col, ts_col = _infer_paragon_trends_columns()

    # If we inferred column names, use them directly.
    if score_col:
        payload: Dict[str, Any] = {
            "politician_id": int(politician_id),
            score_col: int(overall_score),
            "dimensions_json": dims,
        }
        if ts_col:
            payload[ts_col] = ts
        else:
            # Prefer calculated_at if exists; otherwise omit timestamp field (DB default may exist).
            payload["calculated_at"] = ts

        print(
            f"[trend_engine] INSERT paragon_trends "
            f"(politician_id={politician_id}, {score_col}={overall_score})"
        )
        return supabase_insert(table="paragon_trends", records=[payload])

    # Otherwise, the table is likely empty or schema differs.
    # Fall back to trial inserts using candidate names until one succeeds.
    last_error: Optional[Exception] = None

    for candidate in _SCORE_COL_CANDIDATES:
        payload = {
            "politician_id": int(politician_id),
            candidate: int(overall_score),
            "dimensions_json": dims,
            "calculated_at": ts,
        }

        try:
            print(
                f"[trend_engine] INSERT paragon_trends trial "
                f"(politician_id={politician_id}, {candidate}={overall_score})"
            )
            return supabase_insert(table="paragon_trends", records=[payload])

        except Exception as e:
            # Typical error is PGRST204 "Could not find the '<col>' column..."
            # Continue trying other candidates.
            last_error = e
            continue

    # If we reached here, none of the candidates exist.
    raise RuntimeError(
        "paragon_trends insert failed: could not find a compatible score column. "
        "The table does not expose any of these candidates: "
        f"{', '.join(_SCORE_COL_CANDIDATES)}"
    ) from last_error


# =====================================================================
# 3) Aggregator
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
        overall_score=overall_score,
        dimensions=dimensions,
        calculated_at=ts,
    )

    return {
        "politician_id": int(politician_id),
        "overall_score": overall_score,
        "dimensions": _safe_dimensions(dimensions),
        "calculated_at": ts,
        "latest_row": latest_row,
        "trend_row": trend_row,
    }
