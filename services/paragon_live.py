# services/paragon_live.py

from typing import Dict, List
from datetime import datetime, timezone

from utils.supabase_client import supabase
from utils.paragon_engine import ParagonEngine
from utils.politician_loader import load_politician_metrics

PARAGON_VERSION = "paragon_v1"


def _compute_final_score(dimensions: List[Dict]) -> int:
    """
    Composite PARAGON score = arithmetic mean of all dimension scores.
    """
    if not dimensions:
        return 0
    return int(sum(d["score"] for d in dimensions) / len(dimensions))


def compute_and_snapshot_paragon(politician_id: str) -> Dict:
    """
    Computes PARAGON score for a single politician
    and persists an immutable snapshot.
    """

    metrics = load_politician_metrics(politician_id)
    if not metrics:
        raise ValueError(f"No metrics found for politician_id={politician_id}")

    # 🔑 Correct input shape for ParagonEngine
    raw_data = {
        "metrics": metrics,
        "kapsh_profile": metrics.get("kapsh_profile", "Unknown"),
    }

    engine = ParagonEngine(raw_data)
    breakdown = engine.calculate()
    final_score = _compute_final_score(breakdown)

    snapshot = {
        "politician_id": politician_id,
        "score": final_score,
        "breakdown": breakdown,
        "version": PARAGON_VERSION,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    (
        supabase
        .table("paragon_snapshots")
        .upsert(snapshot)
        .execute()
    )

    return snapshot


def recompute_all_paragon() -> int:
    """
    Recomputes PARAGON for all known politicians.
    Returns number of updated profiles.
    """

    all_metrics = load_politician_metrics()
    count = 0

    for politician_id in all_metrics.keys():
        try:
            compute_and_snapshot_paragon(politician_id)
            count += 1
        except Exception as e:
            print(f"[PARAGON] Skipped {politician_id}: {e}")

    return count
