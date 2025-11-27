from fastapi import APIRouter
import feedparser

router = APIRouter()

RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml",
    # Add more if needed
]

@router.get("/news")
async def get_news():
    articles = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:  # Limit per source
            articles.append({
                "id": entry.get("id") or entry.get("link"),
                "title": entry.get("title"),
                "content": entry.get("summary", ""),
                "imageUrl": "",
                "category": "International",
                "timestamp": entry.get("published", "Unknown"),
            })

    # Optional: sort by published date if available
    return articles
