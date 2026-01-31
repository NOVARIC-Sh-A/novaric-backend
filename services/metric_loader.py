# services/metric_loader.py

from __future__ import annotations

import os
from typing import Dict, Any

from utils.supabase_client import _get


# -----------------------------------------------------------
# Runtime flags (Cloud Run)
# -----------------------------------------------------------
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
SAFE_MODE_ENV = os.getenv("PARAGON_SAFE_MODE", "false").lower() == "true"
ENABLE_SCRAPERS = os.getenv("ENABLE_SCRAPERS", "false").lower() == "true"


# -----------------------------------------------------------
# Lazy imports (avoid importing scrapers at startup)
# -----------------------------------------------------------
def _lazy_media_scraper():
    from etl.media_scraper import scrape_media_signals
    return scrape_media_signals


def _lazy_social_scraper():
    from etl.social_scraper import scrape_social_signals
    return scrape_social_signals


def load_metrics_for(
    politician_id: int,
    *,
    safe_mode: bool = False,
) -> Dict[str, Any]:
    """
    Loads all metrics needed for PARAGON scoring.

    SAFE MODE:
      - Supabase structured metrics only
      - scrapers disabled
    """

    # -----------------------------------------------------------
    # 1) Load base structured metrics from Supabase
    # -----------------------------------------------------------
    defaults = {
        "scandals_flagged": 0,
        "wealth_declaration_issues": 0,
        "public_projects_completed": 0,
        "parliamentary_attendance": 0,
        "international_meetings": 0,
        "party_control_index": 0,
        "media_mentions_monthly": 0,
        "legislative_initiatives": 0,
        "independence_index": 0,
    }

    if TEST_MODE:
        return defaults.copy()

    try:
        rows = _get(
            "paragon_metrics",
            {"select": "*", "politician_id": f"eq.{politician_id}", "limit": 1},
        )
        base = rows[0] if rows else {}
    except Exception as e:
        print(f"[services.metric_loader] Error fetching base metrics: {e}")
        base = {}

    metrics: Dict[str, Any] = {k: base.get(k, v) for k, v in defaults.items()}

    # -----------------------------------------------------------
    # HARD STOP: never run scrapers unless explicitly enabled
    # -----------------------------------------------------------
    if safe_mode or SAFE_MODE_ENV or (not ENABLE_SCRAPERS):
        # Keep values stable and predictable when scrapers disabled
        return {k: (max(0, v) if isinstance(v, (int, float)) else v) for k, v in metrics.items()}

    # -----------------------------------------------------------
    # 2) Enrichment: Media Scraper
    # -----------------------------------------------------------
    try:
        scrape_media_signals = _lazy_media_scraper()
        media_data = scrape_media_signals(politician_id)

        metrics["media_mentions_monthly"] += int(media_data.get("mentions", 0) or 0)
        metrics["scandals_flagged"] += int(media_data.get("scandals_flagged", 0) or 0)
        metrics["parliamentary_attendance"] += int(media_data.get("attendance_signal", 0) or 0)

    except Exception as e:
        print(f"[services.metric_loader] Media scraper failed: {e}")

    # -----------------------------------------------------------
    # 3) Enrichment: Social Signals
    # -----------------------------------------------------------
    try:
        scrape_social_signals = _lazy_social_scraper()
        social_data = scrape_social_signals(politician_id)

        metrics["party_control_index"] += float(social_data.get("influence_boost", 0) or 0)

    except Exception as e:
        print(f"[services.metric_loader] Social scraper failed: {e}")

    # -----------------------------------------------------------
    # 4) Clamp numeric values
    # -----------------------------------------------------------
    for key, value in list(metrics.items()):
        if isinstance(value, (int, float)):
            metrics[key] = max(0, value)

    return metrics
