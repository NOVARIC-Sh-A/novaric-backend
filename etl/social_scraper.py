# etl/social_scraper.py

import os
import json
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from utils.supabase_client import _get
from etl.media_scraper import scrape_media_signals

# Google Gemini (optional)
try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # type: ignore

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# =====================================================================
# 1. PROFILE CONTEXT DETECTION
# =====================================================================
def _detect_profile_context(entity_id: int) -> Dict[str, Optional[str]]:
    """
    Detects profile type automatically (politician, media, judiciary, academic, vip)
    using Supabase live tables: politicians, profiles.
    """

    # --- Politicians table ---
    try:
        rows = _get(
            "politicians",
            {
                "select": "id,name,country,party,role",
                "id": f"eq.{entity_id}",
                "limit": 1,
            },
        )
        if rows:
            row = rows[0]
            return {
                "profile_type": "politician",
                "name": row.get("name"),
                "country": row.get("country"),
                "party": row.get("party"),
            }
    except Exception as e:
        print(f"[social_scraper] politician lookup failed: {e}")

    # --- Generic profiles table ---
    try:
        rows = _get(
            "profiles",
            {
                "select": "id,name,profile_type,category,domain",
                "id": f"eq.{entity_id}",
                "limit": 1,
            },
        )
        if rows:
            row = rows[0]
            raw = (
                row.get("profile_type")
                or row.get("category")
                or row.get("domain")
                or ""
            ).lower()

            if any(k in raw for k in ["media", "journalist", "anchor", "tv"]):
                ptype = "media"
            elif any(k in raw for k in ["judge", "court", "judicial"]):
                ptype = "judiciary"
            elif any(k in raw for k in ["professor", "academic", "scholar"]):
                ptype = "academic"
            elif any(k in raw for k in ["vip", "public", "influencer"]):
                ptype = "vip"
            else:
                ptype = "vip"

            return {
                "profile_type": ptype,
                "name": row.get("name"),
                "country": None,
                "party": None,
            }
    except Exception as e:
        print(f"[social_scraper] profiles lookup failed: {e}")

    # --- Fallback ---
    return {
        "profile_type": "unknown",
        "name": None,
        "country": None,
        "party": None,
    }


# =====================================================================
# 2. GEMINI-BASED SOCIAL INFLUENCE ESTIMATE
# =====================================================================
def _gemini_influence_estimate(
    name: str,
    profile_type: str,
    party: Optional[str],
    media_signals: Dict[str, Any],
) -> float:
    """
    Converts media signals into a 0–10 'influence_boost' using Gemini.

    Inputs from media_signals:
      - mentions
      - sentiment_score
      - scandals_flagged
      - positive_events
      - negative_events
    """

    if not genai or not GOOGLE_API_KEY:
        return 0.0

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    mentions = media_signals.get("mentions", 0)
    sentiment = media_signals.get("sentiment_score", 0.0)
    scandals = media_signals.get("scandals_flagged", 0)
    pos_events = media_signals.get("positive_events", 0)
    neg_events = media_signals.get("negative_events", 0)

    prompt = f"""
You are NOVARIC's social-influence analyst.

Subject: "{name}"
Type: "{profile_type}"
Party/Organisation: "{party or 'Unknown'}"

Signals:
- mentions: {mentions}
- sentiment_score: {sentiment}
- scandals_flagged: {scandals}
- positive_events: {pos_events}
- negative_events: {neg_events}

On a 0–10 scale, rate their current public influence:
- 0 = almost no visible influence
- 5 = typical Albanian public figure
- 10 = highly influential / agenda-setting

Return ONLY valid JSON:
{{ "influence_boost": 6.3 }}
"""

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.25},
        )
        text = response.text.strip()

        # Clean fenced ```json blocks if present
        if text.startswith("```"):
            text = text.strip().strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        data = json.loads(text)
        influence_boost = float(data.get("influence_boost", 0.0))

        # Clamp to 0–10
        return max(0.0, min(10.0, influence_boost))

    except Exception as e:
        print(f"[social_scraper] Gemini influence estimate failed: {e}")
        return 0.0


# =====================================================================
# 3. MAIN ETL FUNCTION
# =====================================================================
def scrape_social_signals(entity_id: int) -> Dict[str, Any]:
    """
    Master ETL for extracting *social influence* signals, built on top of
    the hybrid media pipeline (media_scraper).

    Output:
      {
        "influence_boost": float,   # 0–10
        "media_mentions": int,
        "scandals_flagged": int,
        "sentiment_score": float,
        "positive_events": int,
        "negative_events": int
      }
    """

    ctx = _detect_profile_context(entity_id)
    name = ctx.get("name") or "Unknown"
    profile_type = ctx.get("profile_type") or "unknown"
    party = ctx.get("party")

    print(f"🔎 Scraping social signals for {profile_type} '{name}' (ID: {entity_id})...")

    # 1) Media signals (RSS + SerpAPI + Gemini)
    media_signals = scrape_media_signals(entity_id)

    # 2) Gemini-based influence transform
    influence_boost = _gemini_influence_estimate(
        name=name,
        profile_type=profile_type,
        party=party,
        media_signals=media_signals,
    )

    return {
        "influence_boost": influence_boost,
        "media_mentions": media_signals.get("mentions", 0),
        "scandals_flagged": media_signals.get("scandals_flagged", 0),
        "sentiment_score": media_signals.get("sentiment_score", 0.0),
        "positive_events": media_signals.get("positive_events", 0),
        "negative_events": media_signals.get("negative_events", 0),
    }
