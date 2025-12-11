# etl/metric_loader.py

"""
metric_loader.py

Centralized loader for all PARAGON input metrics.

This module merges:
  - Base structured metrics from Supabase (paragon_metrics)
  - Real-time hybrid media signals (RSS + SerpAPI + Gemini)
  - Real-time social influence signals (Gemini-based)

It produces a unified metric dictionary passed to scoring_engine.
"""

from typing import Dict, Any

from utils.supabase_client import _get
from etl.media_scraper import scrape_media_signals
from etl.social_scraper import scrape_social_signals

# ------------------------------------------------------------
# TEST MODE — disables live scraping during pytest
# ------------------------------------------------------------
import os
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

if TEST_MODE:
    print("⚠ metric_loader: TEST MODE active — media & social scrapers disabled.")
    

# =====================================================================
# 1. Base structured metrics from Supabase
# =====================================================================
def _load_base_metrics(politician_id: int) -> Dict[str, Any]:
    """
    Loads structured metrics from table: paragon_metrics

    If no record exists, returns safe defaults.
    """

    if TEST_MODE:
        return {
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
        print(f"[metric_loader] Error fetching base metrics: {e}")
        base = {}

    return {
        "scandals_flagged": base.get("scandals_flagged", 0),
        "wealth_declaration_issues": base.get("wealth_declaration_issues", 0),
        "public_projects_completed": base.get("public_projects_completed", 0),
        "parliamentary_attendance": base.get("parliamentary_attendance", 0),
        "international_meetings": base.get("international_meetings", 0),
        "party_control_index": base.get("party_control_index", 0),
        "media_mentions_monthly": base.get("media_mentions_monthly", 0),
        "legislative_initiatives": base.get("legislative_initiatives", 0),
        "independence_index": base.get("independence_index", 0),
        "media_positive_events": base.get("media_positive_events", 0),
        "media_negative_events": base.get("media_negative_events", 0),
    }


# =====================================================================
# 2. Combine base + media + social signals
# =====================================================================
def load_metrics_for(politician_id: int) -> Dict[str, Any]:
    """
    Loads all metrics needed for PARAGON scoring.

    Expected by scoring_engine.score_metrics():

        {
            scandals_flagged: int,
            wealth_declaration_issues: int,
            public_projects_completed: int,
            parliamentary_attendance: int,
            international_meetings: int,
            party_control_index: float,
            media_mentions_monthly: int,
            legislative_initiatives: int,
            independence_index: int,
            sentiment_score: float,
            social_influence: float,
            media_positive_events: int,
            media_negative_events: int
        }
    """

    # ------------------------------------------------------
    # 1) BASE METRICS from Supabase
    # ------------------------------------------------------
    metrics: Dict[str, Any] = _load_base_metrics(politician_id)

    # Shortcut exit for tests — bypass all scrapers
    if TEST_MODE:
        metrics["sentiment_score"] = 0.0
        metrics["social_influence"] = 0.0
        return metrics

    # ------------------------------------------------------
    # 2) HYBRID MEDIA SIGNALS (RSS + SERPAPI + Gemini)
    # ------------------------------------------------------
    try:
        media = scrape_media_signals(politician_id)

        metrics["media_mentions_monthly"] += media.get("mentions", 0)
        metrics["scandals_flagged"] += media.get("scandals_flagged", 0)

        metrics["parliamentary_attendance"] += media.get("attendance_signal", 0)

        metrics["sentiment_score"] = media.get("sentiment_score", 0.0)

        # raw event counts
        metrics["media_positive_events"] = (
            metrics.get("media_positive_events", 0) + media.get("positive_events", 0)
        )
        metrics["media_negative_events"] = (
            metrics.get("media_negative_events", 0) + media.get("negative_events", 0)
        )

    except Exception as e:
        print(f"[metric_loader] media_scraper failed: {e}")
        metrics["sentiment_score"] = 0.0

    # ------------------------------------------------------
    # 3) SOCIAL SIGNALS (Gemini)
    # ------------------------------------------------------
    try:
        social = scrape_social_signals(politician_id)

        influence_boost = float(social.get("influence_boost", 0.0))

        metrics["social_influence"] = influence_boost
        metrics["party_control_index"] += influence_boost

    except Exception as e:
        print(f"[metric_loader] social_scraper failed: {e}")
        metrics["social_influence"] = 0.0

    # ------------------------------------------------------
    # 4) SAFETY CLAMP — no negative metrics
    # ------------------------------------------------------
    for key, val in list(metrics.items()):
        if isinstance(val, (int, float)):
            metrics[key] = max(0, val)

    return metrics
