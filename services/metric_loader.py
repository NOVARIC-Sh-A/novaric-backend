# services/metric_loader.py

from utils.supabase_client import _get
from etl.media_scraper import scrape_media_signals   # if exists
from etl.social_scraper import scrape_social_signals # if exists

def load_metrics_for(politician_id: int) -> dict:
    """
    Loads all metrics needed for PARAGON scoring.
    Combines:
        - Supabase live metrics (base structured data)
        - Real-time scraper signals (enrichment)
    """

    # -----------------------------------------------------------
    # 1) Load base structured metrics from Supabase
    # -----------------------------------------------------------
    try:
        rows = _get(
            "paragon_metrics",
            {
                "select": "*",
                "politician_id": f"eq.{politician_id}",
                "limit": 1
            }
        )
        base = rows[0] if rows else {}
    except Exception as e:
        print(f"[metric_loader] Error fetching base metrics: {e}")
        base = {}

    # Base metrics should exist, but if they don't, create defaults:
    metrics = {
        "scandals_flagged": base.get("scandals_flagged", 0),
        "wealth_declaration_issues": base.get("wealth_declaration_issues", 0),
        "public_projects_completed": base.get("public_projects_completed", 0),
        "parliamentary_attendance": base.get("parliamentary_attendance", 0),
        "international_meetings": base.get("international_meetings", 0),
        "party_control_index": base.get("party_control_index", 0),
        "media_mentions_monthly": base.get("media_mentions_monthly", 0),
        "legislative_initiatives": base.get("legislative_initiatives", 0),
        "independence_index": base.get("independence_index", 0),
    }

    # -----------------------------------------------------------
    # 2) Enrichment: Media Scraper → sentiment, mentions, stories
    # -----------------------------------------------------------
    try:
        media_data = scrape_media_signals(politician_id)
        metrics["media_mentions_monthly"] += media_data.get("mentions", 0)
        metrics["scandals_flagged"] += media_data.get("scandals_flagged", 0)
        metrics["parliamentary_attendance"] += media_data.get("attendance_signal", 0)
        # Add more as needed
    except Exception as e:
        print(f"[metric_loader] Media scraper failed: {e}")

    # -----------------------------------------------------------
    # 3) Enrichment: Social Signals → virality, influence boost
    # -----------------------------------------------------------
    try:
        social_data = scrape_social_signals(politician_id)
        metrics["party_control_index"] += social_data.get("influence_boost", 0)
    except Exception as e:
        print(f"[metric_loader] Social scraper failed: {e}")

    # -----------------------------------------------------------
    # 4) Clamp values within reasonable boundaries
    # -----------------------------------------------------------
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            metrics[key] = max(0, value)

    return metrics
