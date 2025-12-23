# services/paragon_repository.py
from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime, timezone

from utils.supabase_client import supabase

# ==========================================================
# CONSTANTS
# ==========================================================
PARAGON_VERSION = "paragon_v1"


class ParagonSnapshot:
    """
    Immutable snapshot of a PARAGON computation.
    Represents the authoritative score for a politician
    at a given algorithm version.
    """

    def __init__(
        self,
        politician_id: str,
        score: int,
        breakdown: Dict[str, Any],
        version: str,
        computed_at: str,
    ):
        self.politician_id = politician_id
        self.score = int(score)
        self.breakdown = breakdown or {}
        self.version = version
        self.computed_at = computed_at


# ==========================================================
# READ
# ==========================================================
def get_paragon_snapshot(
    politician_id: str,
    *,
    version: str = PARAGON_VERSION,
) -> Optional[ParagonSnapshot]:
    """
    Fetch the latest PARAGON snapshot for a politician
    (version-aware, deterministic).

    Returns None if no snapshot exists.
    """
    res = (
        supabase
        .table("paragon_snapshots")
        .select("*")
        .eq("politician_id", politician_id)
        .eq("version", version)
        .order("computed_at", desc=True)
        .limit(1)
        .execute()
    )

    if not res.data:
        return None

    row = res.data[0]

    return ParagonSnapshot(
        politician_id=row["politician_id"],
        score=row["score"],
        breakdown=row.get("breakdown", {}),
        version=row.get("version", version),
        computed_at=row.get("computed_at"),
    )


# ==========================================================
# WRITE (UPSERT)
# ==========================================================
def save_paragon_snapshot(
    *,
    politician_id: str,
    score: int,
    breakdown: Dict[str, Any],
    version: str = PARAGON_VERSION,
) -> None:
    """
    Persist a PARAGON snapshot.

    Idempotent per (politician_id, version).
    Safe under RLS.
    """
    payload = {
        "politician_id": politician_id,
        "score": int(score),
        "breakdown": breakdown,
        "version": version,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    (
        supabase
        .table("paragon_snapshots")
        .upsert(
            payload,
            on_conflict="politician_id,version",
        )
        .execute()
    )
