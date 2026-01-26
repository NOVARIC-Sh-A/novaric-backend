# etl/metrics_from_evidence.py
from __future__ import annotations
from typing import Any, Dict, List
from datetime import datetime, timedelta, timezone

from utils.supabase_client import _get

def compute_media_metrics_from_evidence(politician_id: int, days: int = 30) -> Dict[str, Any]:
    """
    Minimal v1 metrics derived from evidence_items.
    Later you can add sentiment classification and topic tagging.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = _get(
        "evidence_items",
        {
            "select": "id,politician_id,published_at,fetched_at,source_key,content_type",
            "politician_id": f"eq.{politician_id}",
            "content_type": "eq.article",
            "order": "fetched_at.desc",
            "limit": "500",
        },
    )

    media_mentions = len(rows)

    # Placeholder until sentiment pipeline exists
    pos = 0
    neg = 0

    return {
        "media_mentions_monthly": media_mentions,
        "media_positive_events": pos,
        "media_negative_events": neg,
    }
