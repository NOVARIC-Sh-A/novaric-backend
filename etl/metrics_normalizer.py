from typing import Dict, Any


def normalize_media_metrics(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translates media_scraper output into
    scoring_engine-compatible metrics.
    """

    return {
        # Core media
        "media_mentions_monthly": raw.get("mentions", 0),
        "media_positive_events": raw.get("positive_events", 0),
        "media_negative_events": raw.get("negative_events", 0),
        "sentiment_score": raw.get("sentiment_score", 0.0),
        "scandals_flagged": raw.get("scandals_flagged", 0),

        # Derived governance proxy
        "parliamentary_attendance": max(
            0,
            min(100, 50 + raw.get("attendance_signal", 0) * 5),
        ),
    }
