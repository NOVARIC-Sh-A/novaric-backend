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

Feeds are grouped by:
- Domain relevance
- Quality tiers
- Geographic focus

This structure supports scaling, hot-swapping,
and adding new engines (MARAGON, JUDIRANK, ACADEMIRANK).
"""

# ==============================================================
# 1. CORE INTERNATIONAL NEWS FEEDS (Tier 1 – Highest Quality)
# ==============================================================

TIER1_GLOBAL_NEWS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "http://feeds.reuters.com/reuters/worldNews",
    "https://www.theguardian.com/world/rss",
    "https://www.france24.com/en/rss",
    "https://apnews.com/feed/rss",
    "https://rss.cnn.com/rss/edition.rss",
    "http://feeds.washingtonpost.com/rss/world",
]


# ==============================================================
# 2. REGIONAL / BALKAN FEEDS (Tier 2)
# ==============================================================

BALKAN_REGIONAL_FEEDS = [
    "https://balkaninsight.com/feed/",
    "https://www.euronews.com/rss",
]


# ==============================================================
# 3. ALBANIAN NATIONAL MEDIA FEEDS (Primary relevance)
# ==============================================================

ALBANIAN_MEDIA_FEEDS = [
    "https://balkanweb.com/feed",
    "https://faxweb.al/feed",
    "https://euronews.al/feed",
    "https://lapsi.al/feed/",
    "https://abcnews.al/feed/",
]


# ==============================================================
# 4. POLITICIAN-FOCUSED NEWS SOURCES
# ==============================================================

POLITICAL_RELEVANCE_FEEDS = (
    TIER1_GLOBAL_NEWS
    + BALKAN_REGIONAL_FEEDS
    + ALBANIAN_MEDIA_FEEDS
)


# ==============================================================
# 5. MEDIA PROFILE FEEDS (MARAGON Analysis)
# ==============================================================

MEDIA_PROFILE_SCRAPER_FEEDS = [
    # Journalism / Broadcasting hubs
    "https://www.theguardian.com/media/rss",
    "https://www.niemanlab.org/feed/",
    "https://www.poynter.org/feed/",
    # Albanian media ecosystem
    *ALBANIAN_MEDIA_FEEDS,
]


# ==============================================================
# 6. JUDICIARY-ORIENTED FEEDS
# ==============================================================

JUDICIARY_PROFILE_SCRAPER_FEEDS = [
    # Legal + Ethics news
    "https://www.icj.org/feed/",                      # International Commission of Jurists
    "https://www.coe.int/en/web/portal/-/news/rss",   # Council of Europe
    "https://www.echr.coe.int/rss/en",                # European Court of Human Rights
    # Albanian legal media
    "https://plaku.al/feed/",
    "https://liga.al/feed/",
    *TIER1_GLOBAL_NEWS,
]


# ==============================================================
# 7. ACADEMIC PROFILE FEEDS
# ==============================================================

ACADEMIC_PROFILE_FEEDS = [
    "https://www.nature.com/nature/articles?type=research&format=rss",
    "https://www.sciencedaily.com/rss/all.xml",
    "https://www.timeshighereducation.com/rss",
    # Albania & region education / academia
    "https://universiteti.edu.al/feed",
    "https://akaps.al/feed/",
]


# ==============================================================
# 8. VIP / PUBLIC FIGURES FEEDS
# ==============================================================

VIP_PROFILE_FEEDS = [
    *ALBANIAN_MEDIA_FEEDS,
    *TIER1_GLOBAL_NEWS,
]


# ==============================================================
# 9. MASTER COMPREHENSIVE FEED SET (fallback)
# ==============================================================

ALL_RSS_FEEDS = list(
    set(
        POLITICAL_RELEVANCE_FEEDS
        + MEDIA_PROFILE_SCRAPER_FEEDS
        + JUDICIARY_PROFILE_SCRAPER_FEEDS
        + ACADEMIC_PROFILE_FEEDS
        + VIP_PROFILE_FEEDS
    )
)


# ==============================================================
# 10. PROFILE_TYPE → FEED MAP (SCRAPERS / ENRICHMENT)
# ==============================================================

PROFILE_FEED_MAP = {
    "politician": POLITICAL_RELEVANCE_FEEDS,
    "media": MEDIA_PROFILE_SCRAPER_FEEDS,
    "judiciary": JUDICIARY_PROFILE_SCRAPER_FEEDS,
    "academic": ACADEMIC_PROFILE_FEEDS,
    "vip": VIP_PROFILE_FEEDS,
    "unknown": ALL_RSS_FEEDS,
}


def get_feeds_for_profile_type(profile_type: str):
    """
    Public helper for scrapers and enrichment engines.
    Guarantees a deterministic feed list for any profile class.
    """
    key = (profile_type or "unknown").lower()
    return PROFILE_FEED_MAP.get(key, ALL_RSS_FEEDS)


# ==============================================================
# 11. NEWS API CATEGORY → FEED MAP (PUBLIC API)
# ==============================================================

NEWS_CATEGORY_FEED_MAP = {
    "international": TIER1_GLOBAL_NEWS,
    "balkan": BALKAN_REGIONAL_FEEDS,
    "albanian": ALBANIAN_MEDIA_FEEDS,
    "politics": POLITICAL_RELEVANCE_FEEDS,
    "media": MEDIA_PROFILE_SCRAPER_FEEDS,
    "judiciary": JUDICIARY_PROFILE_SCRAPER_FEEDS,
    "academic": ACADEMIC_PROFILE_FEEDS,
    "vip": VIP_PROFILE_FEEDS,
    "all": ALL_RSS_FEEDS,
}


def get_feeds_for_news_category(category: str):
    """
    Public helper for /api/v1/news

    Guarantees:
    - Backward compatibility (defaults to Tier 1 International)
    - Deterministic feed resolution
    - No broken links or undefined categories
    """
    key = (category or "international").lower()
    return NEWS_CATEGORY_FEED_MAP.get(key, TIER1_GLOBAL_NEWS)
