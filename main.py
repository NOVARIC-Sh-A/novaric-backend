import os
import logging
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import feedparser

# NOVARIC Data Loader
from utils.data_loader import load_profiles_data

# PARAGON Router
from paragon_api import router as paragon_router


# ================================================================
# LOGGING
# ================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("novaric-backend")


# ================================================================
# FASTAPI APP
# ================================================================
app = FastAPI(
    title="NOVARIC Backend",
    description="NOVARIC® PARAGON scoring + News Aggregation API",
    version="1.7.0",
)


# ================================================================
# CORS
# ================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# MODELS
# ================================================================
class AnalysisRequest(BaseModel):
    ids: List[str]
    category: str


class AnalysisResponseItem(BaseModel):
    id: str
    overallScore: int
    dimensions: Dict[str, int]


class AnalysisBatchResponse(BaseModel):
    analyses: List[AnalysisResponseItem]


class NewsArticle(BaseModel):
    id: str
    title: str
    content: str
    imageUrl: str = ""
    category: str
    timestamp: str


# ================================================================
# HEALTH CHECK
# ================================================================
@app.get("/")
def root():
    try:
        profiles_count = len(load_profiles_data())
    except Exception:
        profiles_count = 0

    logger.info("Health check executed successfully")

    return {
        "message": "NOVARIC PARAGON Engine is Online",
        "profiles_loaded": profiles_count,
        "data_source": (
            "Supabase (Live)"
            if os.environ.get("USE_LIVE_DB") == "True"
            else "Local Mocks"
        ),
    }


@app.get("/healthz")
def health_probe():
    return {"status": "healthy"}


# ================================================================
# PROFILES
# ================================================================
@app.get("/api/profiles")
def get_profiles():
    logger.info("Profiles requested")
    return load_profiles_data()


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    logger.info(f"Profile lookup requested: {profile_id}")

    profiles = load_profiles_data()
    found = next((p for p in profiles if str(p["id"]) == profile_id), None)

    if not found:
        raise HTTPException(status_code=404, detail="Profile not found")

    return found


# ================================================================
# ANALYSIS ENDPOINT
# ================================================================
@app.post("/api/profiles/analysis-batch", response_model=AnalysisBatchResponse)
def analyze_profiles(request: AnalysisRequest):
    profiles = load_profiles_data()
    results = []

    for pid in request.ids:
        profile = next((p for p in profiles if str(p["id"]) == pid), None)

        if not profile:
            logger.warning(f"Profile missing in batch request: {pid}")
            continue

        analysis = (
            profile.get("maragonAnalysis")
            or profile.get("paragonAnalysis")
            or []
        )

        dims = {
            item["dimension"]: item.get("score", 0)
            for item in analysis if item.get("dimension")
        }

        vals = list(dims.values())
        overall = int(sum(vals) / len(vals)) if vals else 0

        results.append(
            AnalysisResponseItem(
                id=pid,
                overallScore=overall,
                dimensions=dims
            )
        )

    return AnalysisBatchResponse(analyses=results)


# ================================================================
# NEWS AGGREGATION (International + Albanian)
# ================================================================
INTERNATIONAL_FEEDS = [
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

ALBANIAN_FEEDS = [
    "https://top-channel.tv/rss",
    "https://balkanweb.com/feed",
    "https://faxweb.al/feed",
    "https://euronews.al/feed",
]

ALL_FEEDS = (
    [(url, "International") for url in INTERNATIONAL_FEEDS] +
    [(url, "Albanian") for url in ALBANIAN_FEEDS]
)


@app.get("/api/v1/news", response_model=List[NewsArticle])
async def get_news():
    logger.info("Fetching news (International + Albanian)")

    articles = []

    for url, category in ALL_FEEDS:
        try:
            feed = feedparser.parse(url)
            status = getattr(feed, "status", 200)

            if feed.bozo and status not in (200, 301):
                logger.error(f"Malformed feed: {url}")
                continue

            for entry in feed.entries[:7]:
                article_id = entry.get("id") or entry.get("link", "unknown")

                # image extraction fallback
                image = ""
                if hasattr(entry, "media_content") and entry.media_content:
                    image = entry.media_content[0].get("url", "")
                elif hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                    image = entry.media_thumbnail[0].get("url", "")
                elif hasattr(entry, "links"):
                    for link in entry.links:
                        if link.get("type", "").startswith("image"):
                            image = link.get("href", "")
                            break

                articles.append(
                    NewsArticle(
                        id=str(article_id),
                        title=entry.get("title", "No Title"),
                        content=(entry.get("summary", "")[:300] + "..."),
                        imageUrl=image,
                        category=category,
                        timestamp=entry.get(
                            "published",
                            entry.get("updated", "Unknown")
                        ),
                    )
                )

        except Exception as e:
            logger.exception(f"RSS parsing exception: {url} -> {e}")
            continue

    logger.info(f"News delivered: {len(articles)}")
    return articles


# ================================================================
# ROUTERS
# ================================================================
app.include_router(paragon_router)


# ================================================================
# STARTUP / SHUTDOWN
# ================================================================
@app.on_event("startup")
def startup_event():
    logger.info("NOVARIC Backend started successfully.")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("NOVARIC Backend shutting down.")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
