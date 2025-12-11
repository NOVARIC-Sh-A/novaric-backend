# etl/social_scraper.py

import os
import json
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from utils.supabase_client import _get
from etl.media_scraper import scrape_media_signals

# Gemini (optional dependency)
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
    Detect the profile type using Supabase tables:
    - politicians
    - profiles
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
            r = rows[0]
            return {
                "profile_type": "politician",
                "name": r.get("name"),
                "country": r.get("country"),
                "party": r.get("party"),
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
            r = rows[0]

            raw = (
                r.get("profile_type")
                or r.get("category")
                or r.get("domain")
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
                "name": r.get("name"),
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
# 2. GEMINI INFLUENCE TRANSFORM
# =====================================================================
def _gemini_influence_estimate(
    name: str,
    profile_type: str,
    party: Optional[str],
    media_signals: Dict[str, Any],
) -> float:
    """
    Converts raw media signals into a 0–10 social influence index.
    """

    if not genai or not GOOGLE_API_KEY:
        return 0.0

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    mentions = media_signals.get("mentions", 0)
    sentiment = media_signals.get("sentiment_score", 0.0)
    scandals = media_signals.get("scandals_flagged", 0)
    pos = media_signals.get("positive_events", 0)
    neg = media_signals.get("negative_events", 0)

    prompt = f"""
You are NOVARIC's political social-influence analyst.

Subject: "{name}"
Profile type: "{profile_type}"
Party: "{party or 'Unknown'}"

Signals:
- mentions: {mentions}
- sentiment_score: {sentiment}
- scandals_flagged: {scandals}
- positive_events: {pos}
- negative_events: {neg}

Rate influence on a 0–10 scale:
0 = minimal visibility
5 = typical Albanian public figure
10 = major power broker

Return ONLY:
{{ "influence_boost": 7.2 }}
"""

    try:
        response = model.generate_content(
            prompt, 
            generation_config={"temperature": 0.25}
        )
        text = response.text.strip()

        # Remove ```json wrappers if present
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        data = json.loads(text)

        boost = float(data.get("influence_boost", 0.0))

        return max(0.0, min(10.0, boost))

    except Exception as e:
        print(f"[social_scraper] Gemini influence estimate failed: {e}")
        return 0.0


# =====================================================================
# 3. PUBLIC ENTRYPOINT
# =====================================================================
def scrape_social_signals(entity_id: int) -> Dict[str, Any]:
    """
    Master ETL for social influence analysis.
    Builds on top of media_scraper's hybrid pipeline.
    """

    ctx = _detect_profile_context(entity_id)
    name = ctx.get("name") or "Unknown"
    profile_type = ctx.get("profile_type") or "unknown"
    party = ctx.get("party")

    print(f"🔎 Scraping social signals for {profile_type} '{name}' (ID: {entity_id})...")

    # 1) Hybrid media analysis (RSS + SerpAPI + Gemini)
    media = scrape_media_signals(entity_id)

    # 2) Social influence estimation (Gemini)
    influence_boost = _gemini_influence_estimate(
        name=name,
        profile_type=profile_type,
        party=party,
        media_signals=media,
    )

    return {
        "influence_boost": influence_boost,
        "media_mentions": media.get("mentions", 0),
        "scandals_flagged": media.get("scandals_flagged", 0),
        "sentiment_score": media.get("sentiment_score", 0.0),
        "positive_events": media.get("positive_events", 0),
        "negative_events": media.get("negative_events", 0),
    }
