from fastapi import APIRouter
import feedparser
from datetime import datetime
from typing import List, Dict, Any

router = APIRouter(prefix="/api/v1", tags=["News"])

# ============================================================
# TOP GLOBAL RSS FEEDS
# ============================================================
RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "http://feeds.reuters.com/reuters/worldNews",
    "https://www.theguardian.com/world/rss",
    "https://www.france24.com/en/rss",
    "http://feeds.washingtonpost.com/rss/world",
    "https://time.com/feed/world/",
    "https://apnews.com/feed/rss",
]

# Optional logging (Cloud Run uses novaric-backend logger)
try:
    import logging
    logger = logging.getLogger("novaric-backend")
except Exception:
    logger = None


# ============================================================
# IMAGE EXTRACTION — MULTI-STANDARD RSS SUPPORT
# ============================================================
def extract_image(entry: Any) -> str:
    """Extract image URL from various RSS formats."""
    
    # <media:content>
    if hasattr(entry, "media_content") and entry.media_content:
        return entry.media_content[0].get("url", "")

    # <media:thumbnail>
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url", "")

    # <enclosure> (Reuters/AP)
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if "image" in enc.get("type", ""):
                return enc.get("href", "")

    # Guardian-style <link type="image/*">
    if hasattr(entry, "links"):
        for link in entry.links:
            if link.get("type", "").startswith("image"):
                return link.get("href", "")

    return ""


# ============================================================
# TIMESTAMP PARSING → ISO FORMAT
# ============================================================
def parse_timestamp(entry: Any) -> str:
    """Convert RSS timestamp to ISO format."""
    
    published = entry.get("published") or entry.get("updated") or None
    if not published:
        return "Unknown"

    try:
        parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if parsed:
            return datetime(*parsed[:6]).isoformat()
    except Exception:
        pass

    return published


# ============================================================
# MAIN NEWS ENDPOINT
# ============================================================
@router.get("/news")
async def get_news() -> List[Dict[str, Any]]:
    """Unified global news aggregator supporting multi-standard RSS feeds."""
    
    articles = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)

            if feed.bozo and getattr(feed, "status", 200) not in (200, 301):
                if logger:
                    logger.warning(f"Malformed RSS feed: {url}")
                continue

            source_name = feed.feed.get("title", "Unknown")

            for entry in feed.entries[:10]:
                article = {
                    "id": entry.get("id") or entry.get("link") or f"src-{url}",
                    "title": entry.get("title", "Untitled"),
                    "content": entry.get("summary", "")[:300] + "...",
                    "imageUrl": extract_image(entry),
                    "category": "International",
                    "timestamp": parse_timestamp(entry),
                    "source": url,
                    "sourceName": source_name,
                    "sourceType": "international",
                }

                articles.append(article)

        except Exception as e:
            if logger:
                logger.error(f"RSS parsing error for {url}: {e}")
            continue

    # Sort newest → oldest if possible
    def sort_key(a: Dict[str, Any]):
        ts = a.get("timestamp", "")
        try:
            return datetime.fromisoformat(ts)
        except Exception:
            return datetime.min

    articles = sorted(articles, key=sort_key, reverse=True)

    return articles
