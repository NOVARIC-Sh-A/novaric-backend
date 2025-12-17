"""
rss_feeds.py

Central repository for all RSS feed lists used by:
- media_scraper
- social_scraper
- PARAGON (politicians)
- MARAGON (media personalities)
- Judiciary profiles
- Academic profiles
- VIP profiles
- Public News API (/api/v1/news)

Design goals:
- Deterministic feed resolution
- Clear geographic + topical segmentation
- Quality tiering and trust scoring for ranking
- Minimal duplication and easy maintenance
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


# ==============================================================
# 0. FEED METADATA (Weighting, trust scoring, governance hooks)
# ==============================================================

@dataclass(frozen=True)
class FeedMeta:
    """
    Weighting & trust scoring model.

    trust_score: 0..100 (editorial reliability + consistency + low spam)
    weight: 0.0..2.0 (ranking multiplier for selection/ordering in engines)
    tier: 1..3 (1 highest)
    region: "global" | "europe" | "balkan" | "albania" | "asia" | "unknown"
    topics: coarse tags used for routing (politics, judiciary, media, academic, vip, general)
    """
    name: str
    trust_score: int
    weight: float
    tier: int
    region: str
    topics: Tuple[str, ...]


def _meta(name: str, trust: int, weight: float, tier: int, region: str, *topics: str) -> FeedMeta:
    # guardrails (fail fast if someone misconfigures metadata)
    if not (0 <= trust <= 100):
        raise ValueError(f"trust_score must be 0..100 for {name}")
    if not (0.0 <= weight <= 2.0):
        raise ValueError(f"weight must be 0.0..2.0 for {name}")
    if tier not in (1, 2, 3):
        raise ValueError(f"tier must be 1..3 for {name}")
    return FeedMeta(
        name=name,
        trust_score=trust,
        weight=weight,
        tier=tier,
        region=region,
        topics=tuple(dict.fromkeys(topics)),  # de-dup while preserving order
    )


# Canonical metadata registry (single source of truth)
FEED_META: Dict[str, FeedMeta] = {
    # ------------------------------
    # Tier 1 – Global (highest quality)
    # ------------------------------
    "http://feeds.bbci.co.uk/news/rss.xml":
        _meta("BBC News", 95, 1.15, 1, "global", "general", "politics"),
    "http://feeds.bbci.co.uk/news/world/rss.xml":
        _meta("BBC World", 95, 1.15, 1, "global", "general", "politics"),
    "http://feeds.reuters.com/reuters/worldNews":
        _meta("Reuters World", 97, 1.20, 1, "global", "general", "politics", "economy"),
    "https://apnews.com/feed/rss":
        _meta("AP News", 94, 1.10, 1, "global", "general", "politics"),
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml":
        _meta("NYTimes World", 93, 1.05, 1, "global", "general", "politics"),
    "https://www.theguardian.com/world/rss":
        _meta("The Guardian World", 91, 1.00, 1, "global", "general", "politics"),
    "https://rss.dw.com/xml/rss-en-all":
        _meta("Deutsche Welle (EN)", 92, 1.00, 1, "global", "general", "politics"),
    "https://www.france24.com/en/rss":
        _meta("France 24 (EN)", 90, 0.98, 1, "global", "general", "politics"),
    "https://www.aljazeera.com/xml/rss/all.xml":
        _meta("Al Jazeera", 88, 0.95, 1, "global", "general", "politics"),
    "https://rss.cnn.com/rss/edition.rss":
        _meta("CNN International", 87, 0.92, 1, "global", "general", "politics"),
    "http://feeds.washingtonpost.com/rss/world":
        _meta("Washington Post World", 90, 0.98, 1, "global", "general", "politics"),

    # ------------------------------
    # Tier 2 – Europe / Policy / Regional (English-focused)
    # ------------------------------
    "https://www.euronews.com/rss?format=xml":
        _meta("Euronews", 86, 0.90, 2, "europe", "general", "politics"),
    "https://www.politico.eu/feed/":
        _meta("Politico Europe", 88, 0.95, 2, "europe", "politics", "policy"),
    "https://euobserver.com/rss":
        _meta("EUobserver", 85, 0.90, 2, "europe", "politics", "policy"),
    "https://www.spiegel.de/international/index.rss":
        _meta("Der Spiegel International", 87, 0.92, 2, "europe", "general", "politics"),
    "https://www.swissinfo.ch/oai/rss/en":
        _meta("SWI swissinfo.ch (EN)", 84, 0.88, 2, "europe", "general", "politics"),
    "https://www.rte.ie/feeds/rss/?index=/news/":
        _meta("RTÉ News", 83, 0.86, 2, "europe", "general", "politics"),
    "https://www.ekathimerini.com/feed/":
        _meta("Kathimerini", 80, 0.84, 2, "europe", "general", "politics"),
    "https://www.dutchnews.nl/feed/":
        _meta("DutchNews.nl", 78, 0.82, 2, "europe", "general", "politics"),
    "https://www.thelocal.fr/feed":
        _meta("The Local France", 77, 0.80, 2, "europe", "general", "politics"),

    # Sky News moved OUT of Tier 1 by design (UK-centric; Tier 2)
    "https://feeds.skynews.com/feeds/rss/world.xml":
        _meta("Sky News World", 76, 0.78, 2, "europe", "general", "politics"),

    # ------------------------------
    # Tier 2 – Balkans / Southeast Europe
    # ------------------------------
    "https://balkaninsight.com/feed/":
        _meta("Balkan Insight (BIRN)", 85, 0.92, 2, "balkan", "general", "politics", "judiciary"),

    # ------------------------------
    # Tier 2 – Global (specialist / topical / wire-style)
    # ------------------------------
    "https://feeds.npr.org/1004/rss.xml":
        _meta("NPR World", 86, 0.88, 2, "global", "general", "politics"),
    "https://www.cnbc.com/id/100727362/device/rss/rss.html":
        _meta("CNBC International", 75, 0.78, 2, "global", "economy", "general"),
    "https://www.cbsnews.com/latest/rss/world":
        _meta("CBS World", 74, 0.76, 2, "global", "general"),

    # Asia-focused (kept separate from Tier 1 by region semantics)
    "https://www.scmp.com/rss/91/feed":
        _meta("SCMP", 82, 0.86, 2, "asia", "general", "politics"),

    # ------------------------------
    # Albania – primary relevance
    # ------------------------------
    "https://balkanweb.com/feed":
        _meta("BalkanWeb", 70, 0.80, 2, "albania", "general", "politics", "vip"),
    "https://faxweb.al/feed":
        _meta("Faxweb", 68, 0.78, 2, "albania", "general", "politics", "vip"),
    "https://euronews.al/feed":
        _meta("Euronews Albania", 72, 0.82, 2, "albania", "general", "politics", "vip"),
    "https://abcnews.al/feed/":
        _meta("ABC News Albania", 68, 0.78, 2, "albania", "general", "politics", "vip"),
    "https://www.panorama.com.al/feed/":
        _meta("Panorama", 69, 0.79, 2, "albania", "general", "politics", "vip"),
    "https://lapsi.al/feed/":
        _meta("Lapsi.al", 65, 0.74, 2, "albania", "general", "politics", "vip"),
    "https://reporter.al/feed/":
        _meta("Reporter.al (BIRN Albania)", 83, 0.92, 2, "albania", "general", "politics", "judiciary"),

    # ------------------------------
    # Media industry analysis (MARAGON)
    # ------------------------------
    "https://www.theguardian.com/media/rss":
        _meta("The Guardian Media", 88, 0.95, 2, "global", "media"),
    "https://www.niemanlab.org/feed/":
        _meta("Nieman Lab", 86, 0.92, 2, "global", "media"),
    "https://www.poynter.org/feed/":
        _meta("Poynter", 86, 0.92, 2, "global", "media"),

    # ------------------------------
    # Judiciary / rule-of-law (use targeted sources; avoid broad Tier1 injection)
    # ------------------------------
    "https://www.icj.org/feed/":
        _meta("International Commission of Jurists", 90, 1.00, 2, "global", "judiciary", "policy"),
    "https://www.coe.int/en/web/portal/-/news/rss":
        _meta("Council of Europe", 92, 1.05, 2, "europe", "judiciary", "policy"),
    "https://www.echr.coe.int/rss/en":
        _meta("ECHR", 93, 1.08, 2, "europe", "judiciary", "policy"),

    # ------------------------------
    # Academic / science / education
    # ------------------------------
    "https://www.nature.com/nature/articles?type=research&format=rss":
        _meta("Nature Research", 96, 1.20, 1, "global", "academic"),
    "https://www.sciencedaily.com/rss/all.xml":
        _meta("ScienceDaily", 80, 0.85, 2, "global", "academic"),
    "https://www.timeshighereducation.com/rss":
        _meta("Times Higher Education", 85, 0.92, 2, "global", "academic", "policy"),
    "https://universiteti.edu.al/feed":
        _meta("Universiteti.edu.al", 60, 0.70, 3, "albania", "academic"),
    "https://akaps.al/feed/":
        _meta("AKAPS", 70, 0.80, 3, "albania", "academic", "policy"),
}


def get_feed_meta(url: str) -> FeedMeta:
    """
    Returns metadata for a feed URL.
    Unknown feeds are allowed but receive conservative defaults.
    """
    return FEED_META.get(
        url,
        FeedMeta(
            name="Unknown",
            trust_score=50,
            weight=0.60,
            tier=3,
            region="unknown",
            topics=("general",),
        )
    )


# ==============================================================
# 1. CORE INTERNATIONAL NEWS FEEDS (Tier 1)
# ==============================================================

TIER1_GLOBAL_NEWS: List[str] = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "http://feeds.reuters.com/reuters/worldNews",
    "https://apnews.com/feed/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.theguardian.com/world/rss",
    "https://rss.dw.com/xml/rss-en-all",
    "https://www.france24.com/en/rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.cnn.com/rss/edition.rss",
    "http://feeds.washingtonpost.com/rss/world",
]


# ==============================================================
# 2. EUROPEAN (policy + English editions) (Tier 2)
# ==============================================================

EUROPEAN_FEEDS: List[str] = [
    "https://www.euronews.com/rss?format=xml",
    "https://www.politico.eu/feed/",
    "https://euobserver.com/rss",
    "https://www.spiegel.de/international/index.rss",
    "https://www.swissinfo.ch/oai/rss/en",
    "https://www.rte.ie/feeds/rss/?index=/news/",
    "https://www.ekathimerini.com/feed/",
    "https://www.dutchnews.nl/feed/",
    "https://www.thelocal.fr/feed",
    "https://feeds.skynews.com/feeds/rss/world.xml",
]


# ==============================================================
# 3. BALKAN REGIONAL FEEDS (Tier 2)
# ==============================================================

BALKAN_REGIONAL_FEEDS: List[str] = [
    "https://balkaninsight.com/feed/",
]


# ==============================================================
# 4. ALBANIAN NATIONAL MEDIA FEEDS (Primary relevance)
# ==============================================================

ALBANIAN_MEDIA_FEEDS: List[str] = [
    "https://balkanweb.com/feed",
    "https://faxweb.al/feed",
    "https://euronews.al/feed",
    "https://abcnews.al/feed/",
    "https://www.panorama.com.al/feed/",
    "https://lapsi.al/feed/",
    "https://reporter.al/feed/",
]


# ==============================================================
# 5. GLOBAL SECONDARY / SPECIALIST FEEDS (Tier 2)
# ==============================================================

GLOBAL_SECONDARY_FEEDS: List[str] = [
    "https://feeds.npr.org/1004/rss.xml",
    "https://www.cbsnews.com/latest/rss/world",
    "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "https://www.scmp.com/rss/91/feed",
]


# ==============================================================
# 6. POLITICIAN-FOCUSED NEWS SOURCES (PARAGON)
# ==============================================================

POLITICAL_RELEVANCE_FEEDS: List[str] = (
    TIER1_GLOBAL_NEWS
    + EUROPEAN_FEEDS
    + BALKAN_REGIONAL_FEEDS
    + ALBANIAN_MEDIA_FEEDS
    + GLOBAL_SECONDARY_FEEDS
)


# ==============================================================
# 7. MEDIA PROFILE FEEDS (MARAGON Analysis)
# ==============================================================

MEDIA_PROFILE_SCRAPER_FEEDS: List[str] = [
    "https://www.theguardian.com/media/rss",
    "https://www.niemanlab.org/feed/",
    "https://www.poynter.org/feed/",
    *ALBANIAN_MEDIA_FEEDS,
]


# ==============================================================
# 8. JUDICIARY-ORIENTED FEEDS (Targeted; low-noise)
# ==============================================================

JUDICIARY_PROFILE_SCRAPER_FEEDS: List[str] = [
    "https://www.icj.org/feed/",
    "https://www.coe.int/en/web/portal/-/news/rss",
    "https://www.echr.coe.int/rss/en",
    
    # Add rule-of-law adjacent regional sources (higher signal than general news)
    "https://balkaninsight.com/feed/",
    "https://reporter.al/feed/",
    "https://www.politico.eu/feed/",
    "https://euobserver.com/rss",
]


# ==============================================================
# 9. ACADEMIC PROFILE FEEDS
# ==============================================================

ACADEMIC_PROFILE_FEEDS: List[str] = [
    "https://www.nature.com/nature/articles?type=research&format=rss",
    "https://www.sciencedaily.com/rss/all.xml",
    "https://www.timeshighereducation.com/rss",
]


# ==============================================================
# 10. VIP / PUBLIC FIGURES FEEDS
# ==============================================================

VIP_PROFILE_FEEDS: List[str] = [
    *ALBANIAN_MEDIA_FEEDS,
    *TIER1_GLOBAL_NEWS,
    *GLOBAL_SECONDARY_FEEDS,
]


# ==============================================================
# 11. MASTER COMPREHENSIVE FEED SET (fallback)
# ==============================================================

ALL_RSS_FEEDS: List[str] = sorted(
    set(
        POLITICAL_RELEVANCE_FEEDS
        + MEDIA_PROFILE_SCRAPER_FEEDS
        + JUDICIARY_PROFILE_SCRAPER_FEEDS
        + ACADEMIC_PROFILE_FEEDS
        + VIP_PROFILE_FEEDS
    )
)


# ==============================================================
# 12. PROFILE_TYPE → FEED MAP (SCRAPERS / ENRICHMENT)
# ==============================================================

PROFILE_FEED_MAP: Dict[str, List[str]] = {
    "politician": POLITICAL_RELEVANCE_FEEDS,
    "media": MEDIA_PROFILE_SCRAPER_FEEDS,
    "judiciary": JUDICIARY_PROFILE_SCRAPER_FEEDS,
    "academic": ACADEMIC_PROFILE_FEEDS,
    "vip": VIP_PROFILE_FEEDS,
    "unknown": ALL_RSS_FEEDS,
}


def get_feeds_for_profile_type(profile_type: str) -> List[str]:
    """
    Public helper for scrapers and enrichment engines.
    Guarantees a deterministic feed list for any profile class.
    """
    key = (profile_type or "unknown").lower()
    return PROFILE_FEED_MAP.get(key, ALL_RSS_FEEDS)


# ==============================================================
# 13. NEWS API CATEGORY → FEED MAP (PUBLIC API)
# ==============================================================

NEWS_CATEGORY_FEED_MAP: Dict[str, List[str]] = {
    "international": TIER1_GLOBAL_NEWS,
    "global_secondary": GLOBAL_SECONDARY_FEEDS,
    "europe": EUROPEAN_FEEDS,
    "balkan": BALKAN_REGIONAL_FEEDS,
    "albanian": ALBANIAN_MEDIA_FEEDS,
    "politics": POLITICAL_RELEVANCE_FEEDS,
    "media": MEDIA_PROFILE_SCRAPER_FEEDS,
    "judiciary": JUDICIARY_PROFILE_SCRAPER_FEEDS,
    "academic": ACADEMIC_PROFILE_FEEDS,
    "vip": VIP_PROFILE_FEEDS,
    "all": ALL_RSS_FEEDS,
}


def get_feeds_for_news_category(category: str) -> List[str]:
    """
    Public helper for /api/v1/news

    Guarantees:
    - Backward compatibility (defaults to Tier 1 International)
    - Deterministic feed resolution
    - No undefined categories
    """
    key = (category or "international").lower()
    return NEWS_CATEGORY_FEED_MAP.get(key, TIER1_GLOBAL_NEWS)


# ==============================================================
# 14. WEIGHTED FEED SELECTION (ranking and prioritization)
# ==============================================================

def rank_feeds(feeds: Iterable[str]) -> List[str]:
    """
    Returns feeds sorted by:
    1) tier ascending (Tier 1 first)
    2) trust_score descending
    3) weight descending
    4) stable alphabetical by URL
    """
    unique = sorted(set(feeds))
    return sorted(
        unique,
        key=lambda url: (
            get_feed_meta(url).tier,
            -get_feed_meta(url).trust_score,
            -get_feed_meta(url).weight,
            url,
        )
    )


def get_weighted_feeds_for_profile_type(profile_type: str) -> List[str]:
    """
    Convenience: returns profile feeds ranked by quality/trust.
    """
    return rank_feeds(get_feeds_for_profile_type(profile_type))


def get_weighted_feeds_for_news_category(category: str) -> List[str]:
    """
    Convenience: returns category feeds ranked by quality/trust.
    """
    return rank_feeds(get_feeds_for_news_category(category))


def feed_priority_score(url: str) -> float:
    """
    Single numeric score useful for schedulers or sampling.
    Higher means more priority.

    Model:
      base = trust_score * weight
      tier_bonus: Tier1 +20%, Tier2 +0%, Tier3 -15%
      region_bonus: Albania +10% (for local relevance), Balkan +5%
    """
    m = get_feed_meta(url)
    base = float(m.trust_score) * float(m.weight)

    tier_factor = {1: 1.20, 2: 1.00, 3: 0.85}.get(m.tier, 1.00)
    region_factor = {
        "albania": 1.10,
        "balkan": 1.05,
        "europe": 1.00,
        "global": 1.00,
        "asia": 0.98,
        "unknown": 0.90,
    }.get(m.region, 1.00)

    return base * tier_factor * region_factor
