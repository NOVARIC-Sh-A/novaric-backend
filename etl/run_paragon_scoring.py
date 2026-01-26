# etl/run_paragon_scoring.py
"""
Compute PARAGON scores from paragon_metrics and upsert into paragon_scores.

Design goals:
- Cloud Run safe (no import-time Supabase hard failures beyond utils.supabase_client behavior)
- Defensive against malformed rows
- Uses canonical scoring pipeline:
    paragon_metrics (DB row) -> canonical metrics -> scoring_engine.score_metrics()
- Writes paragon_scores in a schema-aligned way:
    politician_id (int)
    overall_score (int 0..100)
    dimension_scores (jsonb list of {dimension, score})
    dimensions_json (jsonb list mirror; backward compatibility)
    signals_raw (jsonb canonical metrics used)
    calculated_at, last_updated (ISO timestamps)
    leadership, integrity, public_impact (legacy rollups)
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from etl.metrics_contract import db_paragon_metrics_to_canonical
from etl.scoring_engine import score_metrics
from utils.supabase_client import _get, supabase_upsert


# ---------------------------------------------------------------------
# Constants / helpers
# ---------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _clamp_0_100(x: Any) -> int:
    v = _as_int(x, 0)
    return max(0, min(100, v))


def _dims_list_to_map(dimensions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Converts [{"dimension": str, "score": int}, ...] -> {dimension: score}
    Robust to malformed entries.
    """
    out: Dict[str, int] = {}
    for d in dimensions or []:
        if not isinstance(d, dict):
            continue
        name = d.get("dimension")
        if not isinstance(name, str) or not name.strip():
            continue
        out[name] = _clamp_0_100(d.get("score"))
    return out


def _rollups_from_dimensions(dim_map: Dict[str, int]) -> Dict[str, int]:
    """
    Populate legacy numeric fields in paragon_scores (if your table still has them):
      - integrity
      - public_impact
      - leadership

    Mapping strategy (stable and explainable):
      integrity -> Accountability & Transparency
      public_impact -> avg(Governance & Institutional Strength, Representation & Responsiveness)
      leadership -> avg(Assertiveness & Influence, Policy Engagement & Expertise, Narrative & Communication)
    """

    def g(k: str) -> int:
        return _clamp_0_100(dim_map.get(k, 0))

    integrity = g("Accountability & Transparency")

    public_impact = _clamp_0_100(
        (g("Governance & Institutional Strength") + g("Representation & Responsiveness")) / 2
    )

    leadership = _clamp_0_100(
        (g("Assertiveness & Influence") + g("Policy Engagement & Expertise") + g("Narrative & Communication")) / 3
    )

    return {
        "leadership": leadership,
        "integrity": integrity,
        "public_impact": public_impact,
    }


# ---------------------------------------------------------------------
# Supabase fetchers
# ---------------------------------------------------------------------
def _fetch_metrics_page(limit: int, offset: int) -> List[Dict[str, Any]]:
    return _get(
        "paragon_metrics",
        {
            "select": "*",
            "order": "politician_id.asc",
            "limit": str(limit),
            "offset": str(offset),
        },
    )


def _fetch_single_metrics_row(politician_id: int) -> Optional[Dict[str, Any]]:
    rows = _get(
        "paragon_metrics",
        {
            "select": "*",
            "politician_id": f"eq.{int(politician_id)}",
            "limit": "1",
        },
    )
    return rows[0] if rows else None


# ---------------------------------------------------------------------
# Row builder (paragon_scores)
# ---------------------------------------------------------------------
def _build_paragon_scores_row(metrics_row: Dict[str, Any]) -> Dict[str, Any]:
    politician_id = metrics_row.get("politician_id")
    if politician_id is None:
        raise ValueError("paragon_metrics row missing politician_id")

    pid = _as_int(politician_id, default=-1)
    if pid <= 0:
        raise ValueError(f"Invalid politician_id: {politician_id}")

    # 1) Convert DB metrics row -> canonical metrics dict
    canonical_metrics = db_paragon_metrics_to_canonical(metrics_row)

    # 2) Score canonical metrics -> official 7 dimensions + overall
    scored = score_metrics(canonical_metrics)
    overall_score = _clamp_0_100(scored.get("overall_score", 0))
    dimensions = scored.get("dimensions") or []
    if not isinstance(dimensions, list):
        dimensions = []

    # 3) Legacy rollups (optional but keeps backward compatibility)
    dim_map = _dims_list_to_map(dimensions)
    rollups = _rollups_from_dimensions(dim_map)

    # 4) Timestamps
    now_iso = _now_iso()

    # IMPORTANT:
    # - dimension_scores MUST remain a LIST of {dimension, score} to match scoring_engine contract.
    # - dimensions_json is kept as a mirror for older consumers.
    row: Dict[str, Any] = {
        "politician_id": pid,
        "overall_score": overall_score,
        "dimension_scores": dimensions,
        "dimensions_json": dimensions,
        "signals_raw": canonical_metrics,
        "calculated_at": now_iso,
        "last_updated": now_iso,
        **rollups,
    }

    return row


# ---------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------
def run(*, single_id: Optional[int], limit: int, offset: int, batch_size: int) -> None:
    if batch_size <= 0:
        raise ValueError("--batch-size must be > 0")
    if limit <= 0:
        raise ValueError("--limit must be > 0")
    if offset < 0:
        raise ValueError("--offset must be >= 0")

    # Fetch rows
    if single_id is not None:
        row = _fetch_single_metrics_row(int(single_id))
        rows = [row] if row else []
    else:
        rows = _fetch_metrics_page(limit=limit, offset=offset)

    if not rows:
        print("[run_paragon_scoring] No paragon_metrics rows found for the given range.")
        return

    buffer: List[Dict[str, Any]] = []
    processed = 0
    failed = 0

    for metrics_row in rows:
        if not isinstance(metrics_row, dict):
            failed += 1
            print("[run_paragon_scoring] Skipping malformed row (not a dict).")
            continue

        pid = metrics_row.get("politician_id")

        try:
            out_row = _build_paragon_scores_row(metrics_row)
            buffer.append(out_row)
            processed += 1
        except Exception as e:
            failed += 1
            print(f"[run_paragon_scoring] ERROR politician_id={pid}: {e}")
            continue

        # Flush batches
        if len(buffer) >= batch_size:
            supabase_upsert("paragon_scores", buffer, conflict_col="politician_id")
            print(f"[run_paragon_scoring] Upserted batch: {len(buffer)}")
            buffer.clear()

    # Final flush
    if buffer:
        supabase_upsert("paragon_scores", buffer, conflict_col="politician_id")
        print(f"[run_paragon_scoring] Upserted final batch: {len(buffer)}")

    print(f"[run_paragon_scoring] Done. processed={processed}, failed={failed}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Compute paragon_scores from paragon_metrics.")
    p.add_argument("--single-id", type=int, default=None, help="Run scoring for one politician_id only.")
    p.add_argument("--limit", type=int, default=500, help="Pagination limit when scanning metrics.")
    p.add_argument("--offset", type=int, default=0, help="Pagination offset when scanning metrics.")
    p.add_argument("--batch-size", type=int, default=50, help="Upsert batch size.")
    args = p.parse_args()

    run(
        single_id=args.single_id,
        limit=args.limit,
        offset=args.offset,
        batch_size=args.batch_size,
    )
