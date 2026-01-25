# etl/run_paragon_scoring.py

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from etl.metrics_contract import db_paragon_metrics_to_canonical
from etl.scoring_engine import score_metrics
from utils.supabase_client import _get, supabase_upsert


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dims_list_to_map(dimensions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Converts [{"dimension": str, "score": int}, ...] -> {dimension: score}
    """
    out: Dict[str, int] = {}
    for d in dimensions or []:
        if not isinstance(d, dict):
            continue
        name = d.get("dimension")
        score = d.get("score")
        if isinstance(name, str):
            try:
                out[name] = int(score)
            except Exception:
                out[name] = 0
    return out


def _rollups_from_dimensions(dim_map: Dict[str, int]) -> Dict[str, int]:
    """
    Populate legacy numeric fields in paragon_scores:
      - leadership
      - integrity
      - public_impact

    These are rollups from the official 7 dimensions, so they remain consistent.

    Mapping strategy:
      integrity -> Accountability & Transparency
      public_impact -> average(Governance & Institutional Strength, Representation & Responsiveness)
      leadership -> average(Assertiveness & Influence, Policy Engagement & Expertise, Narrative & Communication)
    """

    def g(k: str) -> int:
        return int(dim_map.get(k, 0) or 0)

    integrity = g("Accountability & Transparency")

    public_impact = int(
        (g("Governance & Institutional Strength") + g("Representation & Responsiveness")) / 2
    )

    leadership = int(
        (g("Assertiveness & Influence") + g("Policy Engagement & Expertise") + g("Narrative & Communication")) / 3
    )

    return {
        "leadership": max(0, min(100, leadership)),
        "integrity": max(0, min(100, integrity)),
        "public_impact": max(0, min(100, public_impact)),
    }


# ---------------------------------------------------------------------
# Fetch paragon_metrics rows (paged)
# ---------------------------------------------------------------------
def _fetch_paragon_metrics_rows(limit: int, offset: int) -> List[Dict[str, Any]]:
    return _get(
        "paragon_metrics",
        {
            "select": "*",
            "order": "politician_id.asc",
            "limit": str(limit),
            "offset": str(offset),
        },
    )


# ---------------------------------------------------------------------
# Build paragon_scores upsert row
# NOTE: Must match actual DB schema (authoritative via information_schema):
#   - dimension_scores (jsonb)
#   - dimensions_json (jsonb)
#   - signals_raw (jsonb)
#   - overall_score (int)
#   - calculated_at (timestamptz)
#   - last_updated (timestamptz)
#   - leadership/integrity/public_impact (int)
# ---------------------------------------------------------------------
def _build_paragon_scores_row(metrics_row: Dict[str, Any]) -> Dict[str, Any]:
    politician_id = metrics_row.get("politician_id")
    if politician_id is None:
        raise ValueError("paragon_metrics row missing politician_id")

    # DB -> canonical
    canonical = db_paragon_metrics_to_canonical(metrics_row)

    # Score
    scored = score_metrics(canonical)
    overall = int(scored.get("overall_score", 0) or 0)
    dimensions = scored.get("dimensions", []) or []
    dim_map = _dims_list_to_map(dimensions)

    # Legacy rollups
    rollups = _rollups_from_dimensions(dim_map)

    now_iso = _now_iso()

    # Prepare DB row for paragon_scores (schema-aligned)
    row: Dict[str, Any] = {
        "politician_id": int(politician_id),
        "overall_score": max(0, min(100, overall)),
        # Store dimensions in both jsonb columns to keep backward compatibility
        "dimension_scores": dimensions,  # jsonb list (authoritative contract)
        "dimensions_json": dimensions,   # jsonb list (legacy/alternate consumer)
        # Raw canonical signals used for scoring
        "signals_raw": canonical,        # jsonb
        # timestamps
        "calculated_at": now_iso,
        "last_updated": now_iso,
        # Keep legacy rollups populated
        **rollups,
    }

    return row


# ---------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------
def run(*, single_id: Optional[int], limit: int, offset: int, batch_size: int) -> None:
    if single_id is not None:
        rows = _get(
            "paragon_metrics",
            {"select": "*", "politician_id": f"eq.{int(single_id)}", "limit": "1"},
        )
    else:
        rows = _fetch_paragon_metrics_rows(limit=limit, offset=offset)

    if not rows:
        print("[run_paragon_scoring] No paragon_metrics rows found for the given range.")
        return

    buffer: List[Dict[str, Any]] = []
    processed = 0
    failed = 0

    for r in rows:
        try:
            out_row = _build_paragon_scores_row(r)
            buffer.append(out_row)
            processed += 1
        except Exception as e:
            failed += 1
            pid = r.get("politician_id")
            print(f"[run_paragon_scoring] ERROR politician_id={pid}: {e}")
            continue

        if len(buffer) >= batch_size:
            # IMPORTANT:
            # paragon_scores PK is id, but we want upsert-by politician_id.
            # For best behavior, enforce UNIQUE(politician_id) in Postgres.
            supabase_upsert("paragon_scores", buffer, conflict_col="politician_id")
            print(f"[run_paragon_scoring] Upserted batch: {len(buffer)}")
            buffer.clear()

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
