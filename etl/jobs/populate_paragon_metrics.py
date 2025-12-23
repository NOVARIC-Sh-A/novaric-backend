"""
populate_paragon_metrics.py

Batch ETL job to populate / refresh paragon_metrics.

SAFE:
- No external APIs
- No media scrapers
- Deterministic output

Run:
    python -m etl.jobs.populate_paragon_metrics
"""

from typing import Dict, Any, List
from datetime import datetime, timezone

from utils.supabase_client import (
    _get,
    supabase_upsert,
)


# ============================================================
# Helpers
# ============================================================

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(v) -> int:
    try:
        return int(v or 0)
    except Exception:
        return 0


# ============================================================
# Metric builders (ONE responsibility each)
# ============================================================

def build_metrics_for_politician(pid: int) -> Dict[str, Any]:
    """
    Build structured metrics for one politician.
    """

    # --------------------------------------------------
    # Scandals
    # --------------------------------------------------
    scandals = _get(
        "politician_scandals",
        {"select": "id", "politician_id": f"eq.{pid}"},
    )
    scandals_flagged = len(scandals)

    # --------------------------------------------------
    # Wealth declarations
    # --------------------------------------------------
    wealth = _get(
        "wealth_declarations",
        {
            "select": "issues_count",
            "politician_id": f"eq.{pid}",
            "order": "year.desc",
            "limit": 1,
        },
    )
    wealth_issues = _safe_int(wealth[0].get("issues_count")) if wealth else 0

    # --------------------------------------------------
    # Public projects
    # --------------------------------------------------
    projects = _get(
        "public_projects",
        {"select": "id", "politician_id": f"eq.{pid}", "status": "eq.completed"},
    )
    public_projects_completed = len(projects)

    # --------------------------------------------------
    # Parliamentary attendance
    # --------------------------------------------------
    attendance = _get(
        "parliamentary_attendance",
        {
            "select": "attendance_rate",
            "politician_id": f"eq.{pid}",
            "order": "year.desc",
            "limit": 1,
        },
    )
    parliamentary_attendance = (
        _safe_int(attendance[0].get("attendance_rate")) if attendance else 0
    )

    # --------------------------------------------------
    # International meetings
    # --------------------------------------------------
    intl = _get(
        "international_meetings",
        {"select": "id", "politician_id": f"eq.{pid}"},
    )
    international_meetings = len(intl)

    # --------------------------------------------------
    # Legislative initiatives
    # --------------------------------------------------
    laws = _get(
        "legislative_initiatives",
        {"select": "id", "politician_id": f"eq.{pid}"},
    )
    legislative_initiatives = len(laws)

    # --------------------------------------------------
    # Party control (static, from politicians)
    # --------------------------------------------------
    pol = _get(
        "politicians",
        {"select": "party_control_index", "id": f"eq.{pid}", "limit": 1},
    )
    party_control_index = _safe_int(pol[0].get("party_control_index")) if pol else 0

    # --------------------------------------------------
    # Independence index (derived, conservative)
    # --------------------------------------------------
    independence_index = max(0, 10 - party_control_index)

    return {
        "politician_id": pid,
        "scandals_flagged": scandals_flagged,
        "wealth_declaration_issues": wealth_issues,
        "public_projects_completed": public_projects_completed,
        "parliamentary_attendance": parliamentary_attendance,
        "international_meetings": international_meetings,
        "party_control_index": party_control_index,
        "media_mentions_monthly": 0,          # populated elsewhere if needed
        "legislative_initiatives": legislative_initiatives,
        "independence_index": independence_index,
        "media_positive_events": 0,
        "media_negative_events": 0,
        "updated_at": _now_iso(),
    }


# ============================================================
# Main ETL runner
# ============================================================

def run(limit: int = 1000):
    politicians = _get(
        "politicians",
        {"select": "id", "order": "id.asc", "limit": limit},
    )

    records: List[Dict[str, Any]] = []

    for row in politicians:
        pid = row.get("id")
        if not pid:
            continue

        try:
            metrics = build_metrics_for_politician(int(pid))
            records.append(metrics)
        except Exception as e:
            print(f"[ETL] Failed politician {pid}: {e}")

    if not records:
        print("[ETL] No records generated")
        return

    print(f"[ETL] Upserting {len(records)} paragon_metrics rows")

    supabase_upsert(
        table="paragon_metrics",
        records=records,
        conflict_col="politician_id",
    )

    print("[ETL] paragon_metrics successfully refreshed")


# ============================================================
# Entrypoint
# ============================================================

if __name__ == "__main__":
    run()
