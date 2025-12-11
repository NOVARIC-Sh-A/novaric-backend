import os
import json
from typing import Dict, Any, List, Optional

import feedparser
from dotenv import load_dotenv

from utils.supabase_client import _get
from config.rss_feeds import get_feeds_for_profile_type

# Optional dependencies (SerpAPI, Gemini)
try:
    from serpapi import GoogleSearch  # type: ignore
except Exception:
    GoogleSearch = None  # type: ignore

try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # type: ignore

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


# =====================================================================
# 1. PROFILE CONTEXT DETECTION
# =====================================================================
def _detect_profile_context(entity_id: int) -> Dict[str, Optional[str]]:
    """
    Detects profile type (politician, media, judiciary, academic, vip)
    by checking Supabase tables: politicians → profiles.
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
        print(f"[media_scraper] politician lookup failed: {e}")

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
        print(f"[media_scraper] profiles lookup failed: {e}")

    # --- Fallback ---
    return {
        "profile_type": "unknown",
        "name": None,
        "country": None,
        "party": None,
    }


# =====================================================================
# 2. RSS COLLECTION
# =====================================================================
def _rss_articles_for_name(
    name: str, feeds: List[str], max_per_feed: int = 25
) -> List[Dict[str, Any]]:
    """
    Scan RSS feeds and collect items containing the person's name.
    """
    if not name:
        return []

    results: List[Dict[str, Any]] = []
    needle = name.lower()

    for url in feeds:
        try:
            feed = feedparser.parse(url)
            status = getattr(feed, "status", 200)

            if feed.bozo and status not in (200, 301):
                print(f"[media_scraper] malformed feed: {url}")
                continue

            for entry in feed.entries[:max_per_feed]:
                title = entry.get("title", "") or ""
                summary = entry.get("summary", "") or ""
                text = f"{title} {summary}".lower()

                if needle in text:
                    results.append(
                        {
                            "source": url,
                            "title": title,
                            "summary": summary,
                            "link": entry.get("link", ""),
                        }
                    )

        except Exception as e:
            print(f"[media_scraper] RSS parse failed: {url} → {e}")

    return results


# =====================================================================
# 3. SERPAPI ENRICHMENT (OPTIONAL)
# =====================================================================
def _serpapi_headlines(name: str, country: Optional[str]) -> List[str]:
    """
    Uses SerpAPI (if available) to enrich short headline text.
    """
    if not SERPAPI_KEY or not GoogleSearch:
        return []

    query = " ".join(
        [
            name,
            "profil",
            "biografi",
            "politikan",
            "media",
            "gjyqtar",
            country or "",
        ]
    )

    try:
        search = GoogleSearch(
            {
                "q": query,
                "api_key": SERPAPI_KEY,
                "num": 10,
                "hl": "sq",
            }
        )
        res = search.get_dict()
    except Exception as e:
        print(f"[media_scraper] SerpAPI error: {e}")
        return []

    texts: List[str] = []
    for item in res.get("organic_results", []):
        if item.get("title"):
            texts.append(item["title"])
        if item.get("snippet"):
            texts.append(item["snippet"])

    return texts


# =====================================================================
# 4. GEMINI ANALYSIS
# =====================================================================
def _gemini_media_analysis(
    name: str,
    profile_type: str,
    rss_articles: List[Dict[str, Any]],
    serpapi_texts: List[str],
) -> Dict[str, Any]:

    mentions_estimate = len(rss_articles) + len(serpapi_texts)

    if not genai or not GOOGLE_API_KEY:
        return {
            "sentiment_score": 0.0,
            "scandals_flagged": 0,
            "mentions": mentions_estimate,
            "positive_events": 0,
            "negative_events": 0,
        }

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    rss_text = "\n".join(f"- {a['title']} :: {a['summary']}" for a in rss_articles[:40])
    serp_text = "\n".join(f"- {t}" for t in serpapi_texts[:40])

    prompt = f"""
You are NOVARIC's neutral media analyst.

Subject: "{name}"
Profile type: "{profile_type}"

DATA FROM RSS:
{rss_text}

DATA FROM SERPAPI:
{serp_text}

Return ONLY JSON:
{{
  "sentiment_score": -1 to 1,
  "scandals_flagged": int,
  "mentions": int,
  "positive_events": int,
  "negative_events": int
}}
"""

    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0.25})
        text = response.text.strip()

        # Remove ```json fences
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()

        data = json.loads(text)

        return {
            "sentiment_score": float(data.get("sentiment_score", 0.0)),
            "scandals_flagged": int(data.get("scandals_flagged", 0)),
            "mentions": int(data.get("mentions", mentions_estimate)),
            "positive_events": int(data.get("positive_events", 0)),
            "negative_events": int(data.get("negative_events", 0)),
        }

    except Exception as e:
        print(f"[media_scraper] Gemini failed → {e}")
        return {
            "sentiment_score": 0.0,
            "scandals_flagged": 0,
            "mentions": mentions_estimate,
            "positive_events": 0,
            "negative_events": 0,
        }


# =====================================================================
# 5. PUBLIC ENTRYPOINT
# =====================================================================
def scrape_media_signals(entity_id: int) -> Dict[str, Any]:
    """
    Unified hybrid media analysis engine (RSS → SerpAPI → Gemini → Output).
    """

    ctx = _detect_profile_context(entity_id)
    name = ctx.get("name")
    profile_type = ctx.get("profile_type") or "unknown"
    country = ctx.get("country")

    if not name:
        print(f"[media_scraper] No name for ID {entity_id}")
        return {
            "mentions": 0,
            "scandals_flagged": 0,
            "sentiment_score": 0.0,
            "attendance_signal": 0,
            "positive_events": 0,
            "negative_events": 0,
        }

    print(f"📰 Scraping media for {profile_type} '{name}' (ID {entity_id})...")

    # The new universal selector
    feeds = get_feeds_for_profile_type(profile_type)

    # Hybrid collection pipeline
    rss_articles = _rss_articles_for_name(name, feeds)
    serpapi_texts = _serpapi_headlines(name, country)
    analysis = _gemini_media_analysis(name, profile_type, rss_articles, serpapi_texts)

    attendance_signal = analysis["positive_events"] - analysis["negative_events"]

    return {
        "mentions": analysis["mentions"],
        "scandals_flagged": analysis["scandals_flagged"],
        "sentiment_score": analysis["sentiment_score"],
        "attendance_signal": attendance_signal,
        "positive_events": analysis["positive_events"],
        "negative_events": analysis["negative_events"],
    }
