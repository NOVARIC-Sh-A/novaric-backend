"""
populate_paragon_metrics.py

SCHEMA-SAFE batch ETL for paragon_metrics.

Uses ONLY tables confirmed to exist:
- politicians

This guarantees:
- No 404s
- Deterministic output
- PARAGON recomputation works immediately
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

from utils.supabase_client import _get, supabase_upsert


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


# --------------------------------------------------
# Core metric builder (SAFE)
# --------------------------------------------------

def build_metrics_for_politician(pid: int) -> Dict[str, Any]:
    """
    Build baseline metrics using ONLY politicians table.
    """

    rows = _get(
        "politicians",
        {
            "select": "id,party_control_index",
            "id": f"eq.{pid}",
            "limit": 1,
        },
    )

    if not rows:
        raise RuntimeError("politician not found")

    row = rows[0]

    party_control_index = _safe_int(row.get("party_control_index"), 0)

    # Conservative, schema-safe defaults
    return {
        "politician_id": pid,
        "scandals_flagged": 0,
        "wealth_declaration_issues": 0,
        "public_projects_completed": 0,
        "parliamentary_attendance": 0,
        "international_meetings": 0,
        "party_control_index": party_control_index,
        "media_mentions_monthly": 0,
        "legislative_initiatives": 0,
        "independence_index": max(0, 10 - party_control_index),
        "media_positive_events": 0,
        "media_negative_events": 0,
        "updated_at": _now_iso(),
    }


# --------------------------------------------------
# Runner
# --------------------------------------------------

def run(limit: int = 500):
    politicians = _get(
        "politicians",
        {"select": "id", "order": "id.asc", "limit": limit},
    )

    records: List[Dict[str, Any]] = []
    failed = 0

    for row in politicians:
        pid = row.get("id")
        if not pid:
            continue

        try:
            records.append(build_metrics_for_politician(int(pid)))
        except Exception as e:
            failed += 1
            print(f"[ETL] skipped politician {pid}: {e}")

    if not records:
        print("[ETL] No records generated — aborting")
        return

    print(f"[ETL] Upserting {len(records)} paragon_metrics rows ({failed} skipped)")

    supabase_upsert(
        table="paragon_metrics",
        records=records,
        conflict_col="politician_id",
    )

    print("[ETL] paragon_metrics successfully populated")


# --------------------------------------------------
# Entrypoint
# --------------------------------------------------

if __name__ == "__main__":
    run()
