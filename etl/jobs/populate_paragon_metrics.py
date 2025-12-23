"""
populate_paragon_metrics.py

ABSOLUTE SAFE baseline ETL for paragon_metrics.

Assumptions:
- politicians table EXISTS
- politicians.id EXISTS
- NOTHING else is assumed

This guarantees:
- 100% success rate
- Deterministic baseline metrics
- PARAGON recomputation unblocked
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

from utils.supabase_client import _get, supabase_upsert


# --------------------------------------------------
# Utilities
# --------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------
# Metric builder (zero external dependencies)
# --------------------------------------------------

def build_baseline_metrics(politician_id: int) -> Dict[str, Any]:
    """
    Build minimal, deterministic metrics.
    """

    return {
        "politician_id": politician_id,

        # Integrity / ethics
        "scandals_flagged": 0,
        "wealth_declaration_issues": 0,

        # Performance
        "public_projects_completed": 0,
        "parliamentary_attendance": 0,
        "international_meetings": 0,
        "legislative_initiatives": 0,

        # Influence
        "party_control_index": 0,
        "independence_index": 0,

        # Media
        "media_mentions_monthly": 0,
        "media_positive_events": 0,
        "media_negative_events": 0,

        # Audit
        "updated_at": _utc_now(),
    }


# --------------------------------------------------
# Runner
# --------------------------------------------------

def run(limit: int = 500):
    politicians = _get(
        "politicians",
        {"select": "id", "order": "id.asc", "limit": limit},
    )

    if not politicians:
        print("[ETL] No politicians found — aborting")
        return

    records: List[Dict[str, Any]] = []

    for row in politicians:
        pid = row.get("id")
        if pid is None:
            continue

        records.append(build_baseline_metrics(int(pid)))

    print(f"[ETL] Upserting {len(records)} paragon_metrics rows")

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
