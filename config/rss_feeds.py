"""
rss_feeds.py

Central repository for all RSS feed lists used by:
- Public News API (/api/v1/news)
- PARAGON (politicians)
- MARAGON (media personalities)
- Judiciary profiles
- Academic profiles
- VIP profiles
- Background schedulers
- NER trust engines

Design goals:
- Deterministic feed resolution
- Explicit quality tiering
- Trust scoring & governance
- Geographic & topical segmentation
- One-feed-one-article compatibility

Notes (practical reliability):
- Removed Reuters legacy RSS and AP invalid path that commonly return HTML/redirects.
- Prefer HTTPS canonical endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


# ==============================================================
# 0. FEED METADATA
# ==============================================================

@dataclass(frozen=True)
class FeedMeta:
    name: str
    trust_score: int          # 0..100
    weight: float             # 0.0..2.0
    tier: int                 # 1 (highest) .. 3
    region: str               # global | europe | balkan | albania | asia | unknown
    topics: Tuple[str, ...]


def _meta(
    name: str,
    trust: int,
    weight: float,
    tier: int,
    region: str,
    *topics: str,
) -> FeedMeta:
    if not (0 <= trust <= 100):
        raise ValueError(f"Invalid trust_score for {name}")
    if not (0.0 <= weight <= 2.0):
        raise ValueError(f"Invalid weight for {name}")
    if tier not in (1, 2, 3):
        raise ValueError(f"Invalid tier for {name}")

    return FeedMeta(
        name=name,
        trust_score=trust,
        weight=weight,
        tier=tier,
        region=region,
        topics=tuple(dict.fromkeys(topics)),
    )


# ==============================================================
# 1. CANONICAL FEED METADATA REGISTRY
# ==============================================================

FEED_META: Dict[str, FeedMeta] = {

    # ---------------- Tier 1 – Global ----------------
    "https://feeds.bbci.co.uk/news/rss.xml":
        _meta("BBC News", 95, 1.15, 1, "global", "general", "politics"),
    "https://feeds.bbci.co.uk/news/world/rss.xml":
        _meta("BBC World", 95, 1.15, 1, "global", "general", "politics"),

    # Reuters legacy RSS removed (often redirects/blocks or returns non-RSS HTML)
    # "http://feeds.reuters.com/reuters/worldNews": ...

    # AP invalid RSS path removed (typically not RSS XML)
    # "https://apnews.com/feed/rss": ...

    "https://rss.dw.com/xml/rss-en-all":
        _meta("Deutsche Welle", 92, 1.00, 1, "global", "general", "politics"),
    "https://www.france24.com/en/rss":
        _meta("France 24", 90, 0.98, 1, "global", "general", "politics"),
    "https://www.aljazeera.com/xml/rss/all.xml":
        _meta("Al Jazeera", 88, 0.95, 1, "global", "general", "politics"),
    "https://rss.cnn.com/rss/edition.rss":
        _meta("CNN International", 87, 0.92, 1, "global", "general", "politics"),

    # ---------------- Tier 2 – Europe ----------------
    "https://www.euronews.com/rss?format=xml":
        _meta("Euronews", 86, 0.90, 2, "europe", "general", "politics"),
    "https://www.politico.eu/feed/":
        _meta("Politico Europe", 88, 0.95, 2, "europe", "politics"),
    "https://euobserver.com/rss":
        _meta("EUobserver", 85, 0.90, 2, "europe", "politics"),
    "https://feeds.skynews.com/feeds/rss/world.xml":
        _meta("Sky News World", 76, 0.78, 2, "europe", "general", "politics"),

    # ---------------- Tier 2 – Balkans ----------------
    "https://balkaninsight.com/feed/":
        _meta("Balkan Insight (BIRN)", 85, 0.92, 2, "balkan", "general", "politics", "judiciary"),

    # ---------------- Albania ----------------
    "https://balkanweb.com/feed":
        _meta("BalkanWeb", 70, 0.80, 2, "albania", "general", "politics", "vip"),
    "https://euronews.al/feed":
        _meta("Euronews Albania", 72, 0.82, 2, "albania", "general", "politics"),
    "https://reporter.al/feed/":
        _meta("Reporter.al", 83, 0.92, 2, "albania", "general", "politics", "judiciary"),

    # ---------------- Verified Albania expansion (tested & working) ----------------
    "https://www.vizionplus.tv/feed/":
        _meta("Vizion Plus", 68, 0.76, 2, "albania", "general", "politics", "vip"),
    "https://abcnews.al/feed/":
        _meta("ABC News Albania", 68, 0.76, 2, "albania", "general", "politics", "vip"),

    # ---------------- Global secondary (reliable RSS) ----------------
    "https://feeds.npr.org/1004/rss.xml":
        _meta("NPR World", 88, 0.95, 2, "global", "general", "politics"),
    "https://www.cbsnews.com/latest/rss/world":
        _meta("CBS News World", 82, 0.88, 2, "global", "general", "politics"),

    # ---------------- Media analysis ----------------
    "https://www.theguardian.com/media/rss":
        _meta("The Guardian – Media", 88, 0.95, 2, "global", "media"),
    "https://www.niemanlab.org/feed/":
        _meta("Nieman Lab", 86, 0.92, 2, "global", "media"),

    # ---------------- Judiciary ----------------
    "https://www.icj.org/feed/":
        _meta("International Commission of Jurists", 90, 1.00, 2, "global", "judiciary"),
    "https://www.echr.coe.int/rss/en":
        _meta("ECHR", 93, 1.08, 2, "europe", "judiciary"),

    # ---------------- Academic ----------------
    "https://www.nature.com/nature/articles?type=research&format=rss":
        _meta("Nature", 96, 1.20, 1, "global", "academic"),
    "https://www.sciencedaily.com/rss/all.xml":
        _meta("ScienceDaily", 80, 0.85, 2, "global", "academic"),
}


# ==============================================================
# 2. FEED META ACCESSOR
# ==============================================================

def get_feed_meta(url: str) -> FeedMeta:
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
# 3. CORE FEED GROUPS
# ==============================================================

TIER1_GLOBAL_NEWS: List[str] = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.dw.com/xml/rss-en-all",
    "https://www.france24.com/en/rss",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.cnn.com/rss/edition.rss",
]

EUROPEAN_FEEDS: List[str] = [
    "https://www.euronews.com/rss?format=xml",
    "https://www.politico.eu/feed/",
    "https://euobserver.com/rss",
    "https://feeds.skynews.com/feeds/rss/world.xml",
]

BALKAN_REGIONAL_FEEDS: List[str] = [
    "https://balkaninsight.com/feed/",
]

ALBANIAN_MEDIA_FEEDS: List[str] = [
    "https://balkanweb.com/feed",
    "https://euronews.al/feed",
    "https://reporter.al/feed/",
    # Verified Albania expansion (tested & working)
    "https://www.vizionplus.tv/feed/",
    "https://abcnews.al/feed/",
]

GLOBAL_SECONDARY_FEEDS: List[str] = [
    "https://feeds.npr.org/1004/rss.xml",
    "https://www.cbsnews.com/latest/rss/world",
]


# ==============================================================
# 4. PROFILE-SPECIFIC FEEDS
# ==============================================================

POLITICAL_RELEVANCE_FEEDS: List[str] = (
    TIER1_GLOBAL_NEWS
    + EUROPEAN_FEEDS
    + BALKAN_REGIONAL_FEEDS
    + ALBANIAN_MEDIA_FEEDS
    + GLOBAL_SECONDARY_FEEDS
)

MEDIA_PROFILE_SCRAPER_FEEDS: List[str] = [
    "https://www.theguardian.com/media/rss",
    "https://www.niemanlab.org/feed/",
    *ALBANIAN_MEDIA_FEEDS,
]

JUDICIARY_PROFILE_SCRAPER_FEEDS: List[str] = [
    "https://www.icj.org/feed/",
    "https://www.echr.coe.int/rss/en",
    "https://balkaninsight.com/feed/",
    "https://reporter.al/feed/",
]

ACADEMIC_PROFILE_FEEDS: List[str] = [
    "https://www.nature.com/nature/articles?type=research&format=rss",
    "https://www.sciencedaily.com/rss/all.xml",
]

VIP_PROFILE_FEEDS: List[str] = (
    ALBANIAN_MEDIA_FEEDS
    + TIER1_GLOBAL_NEWS
    + GLOBAL_SECONDARY_FEEDS
)


# ==============================================================
# 5. MASTER FEED SET
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
# 6. PROFILE → FEED MAP
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
    return PROFILE_FEED_MAP.get(
        (profile_type or "unknown").lower(),
        ALL_RSS_FEEDS,
    )


# ==============================================================
# 7. NEWS CATEGORY → FEED MAP
# ==============================================================

NEWS_CATEGORY_FEED_MAP: Dict[str, List[str]] = {
    "international": TIER1_GLOBAL_NEWS,
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
    return NEWS_CATEGORY_FEED_MAP.get(
        (category or "international").lower(),
        TIER1_GLOBAL_NEWS,
    )


# ==============================================================
# 8. FEED RANKING & PRIORITY
# ==============================================================

def rank_feeds(feeds: Iterable[str]) -> List[str]:
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


def feed_priority_score(url: str) -> float:
    meta = get_feed_meta(url)
    base = meta.trust_score * meta.weight

    tier_factor = {1: 1.20, 2: 1.00, 3: 0.85}.get(meta.tier, 1.0)
    region_factor = {
        "albania": 1.10,
        "balkan": 1.05,
        "europe": 1.00,
        "global": 1.00,
        "unknown": 0.90,
    }.get(meta.region, 1.00)

    return base * tier_factor * region_factor


# ==============================================================
# 9. OPTIONAL: SANITY CHECK (import-time safe)
# ==============================================================

def validate_feed_registry(strict: bool = False) -> List[str]:
    """
    Returns a list of warnings.

    strict=False:
      - warn if a feed in groups is missing from FEED_META

    strict=True:
      - raise ValueError on missing meta
    """
    warnings: List[str] = []
    all_grouped = set(ALL_RSS_FEEDS)

    missing_meta = sorted([u for u in all_grouped if u not in FEED_META])
    if missing_meta:
        msg = f"Missing FEED_META entries for: {missing_meta}"
        if strict:
            raise ValueError(msg)
        warnings.append(msg)

    return warnings
