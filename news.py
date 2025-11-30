from fastapi import APIRouter
import feedparser

router = APIRouter()

# Top 10 International News Channel RSS Feeds (Focusing on World/Top Stories)
# Note: RSS feeds can sometimes change or require non-commercial use adherence.
RSS_FEEDS = [
    # 1. CNN (Top Stories) - already included
    "https://rss.cnn.com/rss/edition.rss",
    
    # 2. BBC News (World) - already included (using the general news link, which often redirects to world)
    "https://feeds.bbci.co.uk/news/rss.xml", 
    
    # 3. New York Times (World)
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", 
    
    # 4. Al Jazeera (All Content)
    "https://www.aljazeera.com/xml/rss/all.xml",
    
    # 5. Reuters (World News) - Note: Reuters official RSS feeds are often deprecated, this is a common workaround/alternative feed.
    # Official RSS feeds from Reuters are often replaced by paywalled services. This link may vary in performance.
    "http://feeds.reuters.com/reuters/worldNews", 
    
    # 6. The Guardian (World)
    "https://www.theguardian.com/world/rss", 
    
    # 7. France 24 (Top Stories)
    "https://www.france24.com/en/rss",
    
    # 8. The Washington Post (World)
    "http://feeds.washingtonpost.com/rss/world",
    
    # 9. Time Magazine (World)
    "https://time.com/feed/world/",
    
    # 10. Associated Press (AP) (Top Stories)
    "https://apnews.com/feed/rss",
]

@router.get("/news")
async def get_news():
    articles = []

    for url in RSS_FEEDS:
        # Use a timeout to prevent a single slow feed from blocking the service
        feed = feedparser.parse(url, timeout=5) 
        
        # Add a check for parsing errors
        if feed.bozo and feed.status != 200:
            print(f"Error parsing feed from {url}: {feed.bozo_exception}")
            continue

        for entry in feed.entries[:10]:  # Limit per source
            # The 'imageUrl' is often not in a standard 'media' field in all feeds, 
            # so it's common to check for common media namespaces or leave blank.
            # You might need a more complex library for robust image scraping.
            
            # Simple check for a common media namespace (or fallback to an empty string)
            image_url = ''
            if 'media_content' in entry and len(entry.media_content) > 0:
                image_url = entry.media_content[0].get('url', '')
            
            articles.append({
                # Use a combination of GUID or Link for a unique ID
                "id": entry.get("id") or entry.get("link"),
                "title": entry.get("title"),
                # Use 'summary' as the content/snippet. It's often the description.
                "content": entry.get("summary", ""), 
                "imageUrl": image_url,
                "category": "International",
                "timestamp": entry.get("published", "Unknown"),
            })

    # Optional: sort by published date if available.
    # This requires converting the 'timestamp' from a string to a datetime object.
    
    return articles
