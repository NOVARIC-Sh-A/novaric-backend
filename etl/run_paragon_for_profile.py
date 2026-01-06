from typing import Dict, Any

from etl.media_scraper import scrape_media_signals
from etl.metrics_normalizer import normalize_media_metrics
from etl.scoring_engine import score_metrics
from utils.supabase_client import _patch


def run_paragon(entity_id: int) -> Dict[str, Any]:
    """
    Full PARAGON pipeline for one profile.
    """

    # 1. Collect raw media signals
    media_raw = scrape_media_signals(entity_id)

    # 2. Normalize into scoring-compatible metrics
    metrics = normalize_media_metrics(media_raw)

    # 3. Score
    score = score_metrics(metrics)

    # 4. Persist (NO schema change)
    payload_patch = {
        "metrics": metrics,
        "score": score,
    }

    _patch(
        "profiles",
        payload_patch,
        {"id": f"eq.{entity_id}"},
    )

    return payload_patch
