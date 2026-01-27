# etl/run_paragon_scoring.py

from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from etl.metrics_contract import db_paragon_metrics_to_canonical
from etl.scoring_engine import score_metrics
from utils.supabase_client import _get, supabase_upsert


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat()


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

    Mapping strategy:
      integrity -> Accountability & Transparency
      public_impact -> avg(Governance & Institutional Strength, Representation & Responsiveness)
      leadership -> avg(Assertiveness & Influence, Policy Engagement & Expertise, Narrative & Communication)
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


def _parse_int_list(csv: Optional[str]) -> Optional[List[int]]:
    if not csv:
        return None
    out: List[int] = []
    for part in csv.split(","):
        p = part.strip()
        if not p:
            continue
        try:
            out.append(int(p))
        except Exception:
            continue
    return out or None


# ---------------------------------------------------------------------
# Fetch paragon_metrics rows
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


def _fetch_paragon_metrics_single(politician_id: int) -> List[Dict[str, Any]]:
    return _get(
        "paragon_metrics",
        {"select": "*", "politician_id": f"eq.{int(politician_id)}", "limit": "1"},
    )


def _fetch_paragon_metrics_for_ids(ids: List[int]) -> List[Dict[str, Any]]:
    # PostgREST supports in.(...)
    ids_csv = ",".join(str(int(x)) for x in ids)
    return _get(
        "paragon_metrics",
        {
            "select": "*",
            "politician_id": f"in.({ids_csv})",
            "order": "politician_id.asc",
            "limit": str(max(1000, len(ids))),
        },
    )


def _fetch_paragon_metrics_since_minutes(since_minutes: int, *, limit: int, offset: int) -> List[Dict[str, Any]]:
    since_minutes = max(1, int(since_minutes))
    since_dt = _now_utc() - timedelta(minutes=since_minutes)
    since_iso = since_dt.isoformat()

    return _get(
        "paragon_metrics",
        {
            "select": "*",
            "updated_at": f"gte.{since_iso}",
            "order": "politician_id.asc",
            "limit": str(limit),
            "offset": str(offset),
        },
    )


# ---------------------------------------------------------------------
# Build paragon_scores upsert row (schema-aligned)
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

    # Prepare DB row for paragon_scores
    return {
        "politician_id": int(politician_id),
        "overall_score": max(0, min(100, overall)),
        # Official contract list (jsonb)
        "dimension_scores": dimensions,
        # Legacy/alternate consumer field (keep)
        "dimensions_json": dimensions,
        # Raw canonical input signals used for scoring
        "signals_raw": canonical,
        # timestamps
        "calculated_at": now_iso,
        "last_updated": now_iso,
        # legacy rollups
        **rollups,
    }


# ---------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------
def run(
    *,
    single_id: Optional[int],
    ids: Optional[List[int]],
    since_minutes: Optional[int],
    limit: int,
    offset: int,
    batch_size: int,
) -> None:
    """
    Compute paragon_scores from paragon_metrics.

    Modes (priority order):
      1) --single-id <id>
      2) --ids "1,2,3"
      3) --since-minutes <N>   (incremental scoring based on paragon_metrics.updated_at)
      4) default paging: --limit/--offset (all metrics)
    """
    if single_id is not None:
        rows = _fetch_paragon_metrics_single(int(single_id))
        mode = f"single-id={single_id}"
    elif ids:
        rows = _fetch_paragon_metrics_for_ids(ids)
        mode = f"ids={len(ids)}"
    elif since_minutes is not None:
        rows = _fetch_paragon_metrics_since_minutes(int(since_minutes), limit=limit, offset=offset)
        mode = f"since-minutes={since_minutes}"
    else:
        rows = _fetch_paragon_metrics_rows(limit=limit, offset=offset)
        mode = f"paged limit={limit} offset={offset}"

    if not rows:
        print(f"[run_paragon_scoring] No paragon_metrics rows found ({mode}).")
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
            supabase_upsert("paragon_scores", buffer, conflict_col="politician_id")
            print(f"[run_paragon_scoring] Upserted batch: {len(buffer)} ({mode})")
            buffer.clear()

    if buffer:
        supabase_upsert("paragon_scores", buffer, conflict_col="politician_id")
        print(f"[run_paragon_scoring] Upserted final batch: {len(buffer)} ({mode})")

    print(f"[run_paragon_scoring] Done. processed={processed}, failed={failed} ({mode})")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Compute paragon_scores from paragon_metrics.")
    p.add_argument("--single-id", type=int, default=None, help="Run scoring for one politician_id only.")
    p.add_argument("--ids", type=str, default=None, help='Comma-separated politician_ids, e.g. "1,2,3".')
    p.add_argument("--since-minutes", type=int, default=None, help="Only score metrics updated in the last N minutes.")
    p.add_argument("--limit", type=int, default=500, help="Pagination limit when scanning metrics.")
    p.add_argument("--offset", type=int, default=0, help="Pagination offset when scanning metrics.")
    p.add_argument("--batch-size", type=int, default=50, help="Upsert batch size.")
    args = p.parse_args()

    run(
        single_id=args.single_id,
        ids=_parse_int_list(args.ids),
        since_minutes=args.since_minutes,
        limit=args.limit,
        offset=args.offset,
        batch_size=args.batch_size,
    )
