# etl/metric_loader.py

"""
metric_loader.py

Centralized loader for all PARAGON input metrics.

Sources:
- Structured metrics from Supabase (paragon_metrics)
- Optional hybrid media signals
- Optional social influence signals

SAFE MODE (default for API recomputation):
- Uses ONLY structured Supabase metrics
- Disables all external scrapers
"""

from typing import Dict, Any
import os

from utils.supabase_client import _get


# ============================================================
# MODES
# ============================================================

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
SAFE_MODE_ENV = os.getenv("PARAGON_SAFE_MODE", "false").lower() == "true"

if TEST_MODE:
    print("⚠ metric_loader: TEST MODE active — external signals disabled")

if SAFE_MODE_ENV:
    print("🔒 metric_loader: SAFE MODE active — external signals disabled")


# ============================================================
# Lazy imports (Cloud Run safe)
# ============================================================

def _lazy_media_scraper():
    from etl.media_scraper import scrape_media_signals
    return scrape_media_signals


def _lazy_social_scraper():
    from etl.social_scraper import scrape_social_signals
    return scrape_social_signals


# ============================================================
# 1. Base structured metrics
# ============================================================

def _load_base_metrics(politician_id: int) -> Dict[str, Any]:
    """
    Load structured metrics from Supabase table: paragon_metrics.

    Always returns a complete metric dictionary with safe defaults.
    """

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
        "media_positive_events": 0,
        "media_negative_events": 0,
    }

    if TEST_MODE:
        return defaults.copy()

    try:
        rows = _get(
            "paragon_metrics",
            {
                "select": "*",
                "politician_id": f"eq.{politician_id}",
                "limit": 1,
            },
        )
        base = rows[0] if rows else {}
    except Exception as e:
        print(f"[metric_loader] Failed to load base metrics: {e}")
        base = {}

    # Merge DB values over defaults
    return {
        k: base.get(k, v)
        for k, v in defaults.items()
    }


# ============================================================
# 2. Unified loader
# ============================================================

def load_metrics_for(
    politician_id: int,
    *,
    safe_mode: bool = False,
) -> Dict[str, Any]:
    """
    Load all metrics required for PARAGON scoring.

    SAFE MODE:
    - Structured Supabase metrics only
    - sentiment_score = 0.0
    - social_influence = 0.0
    """

    metrics: Dict[str, Any] = _load_base_metrics(politician_id)

    # --------------------------------------------------
    # SAFE / TEST MODE (hard stop)
    # --------------------------------------------------
    if TEST_MODE or safe_mode or SAFE_MODE_ENV:
        metrics["sentiment_score"] = 0.0
        metrics["social_influence"] = 0.0
        return metrics

    # --------------------------------------------------
    # Hybrid media signals
    # --------------------------------------------------
    try:
        scrape_media_signals = _lazy_media_scraper()
        media = scrape_media_signals(politician_id)

        metrics["media_mentions_monthly"] += int(media.get("mentions", 0))
        metrics["scandals_flagged"] += int(media.get("scandals_flagged", 0))
        metrics["parliamentary_attendance"] += int(media.get("attendance_signal", 0))

        metrics["sentiment_score"] = float(media.get("sentiment_score", 0.0))
        metrics["media_positive_events"] += int(media.get("positive_events", 0))
        metrics["media_negative_events"] += int(media.get("negative_events", 0))

    except Exception as e:
        print(f"[metric_loader] media signals skipped: {e}")
        metrics["sentiment_score"] = 0.0

    # --------------------------------------------------
    # Social influence signals
    # --------------------------------------------------
    try:
        scrape_social_signals = _lazy_social_scraper()
        social = scrape_social_signals(politician_id)

        influence = float(social.get("influence_boost", 0.0))
        metrics["social_influence"] = influence
        metrics["party_control_index"] += influence

    except Exception as e:
        print(f"[metric_loader] social signals skipped: {e}")
        metrics["social_influence"] = 0.0

    # --------------------------------------------------
    # Final numeric safety clamp
    # --------------------------------------------------
    for k, v in metrics.items():
        if isinstance(v, (int, float)):
            metrics[k] = max(0, v)

    return metrics
