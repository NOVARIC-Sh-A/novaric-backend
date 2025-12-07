import os
import logging
from typing import List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import feedparser

# NOVARIC Data Loader (local or Supabase-driven)
from utils.data_loader import load_profiles_data

# PARAGON Router (correct import)
from paragon_api import router as paragon_router


# ================================================================
# LOGGING CONFIGURATION — Cloud Run Compatible
# ================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("novaric-backend")


# ================================================================
# FASTAPI APP INITIALIZATION
# ================================================================
app = FastAPI(
    title="NOVARIC Backend",
    description="Clinical scoring API for NOVARIC® PARAGON System",
    version="1.6.0",
)


# ================================================================
# CORS CONFIGURATION
# ================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with production domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# DATA MODELS
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
# HEALTH CHECKS
# ================================================================
@app.get("/")
def root():
    """Lightweight Cloud Run health + metadata endpoint."""
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
    """Used by Cloud Run to confirm the service is alive."""
    return {"status": "healthy"}


# ================================================================
# PROFILES ENDPOINTS
# ================================================================
@app.get("/api/profiles")
def get_profiles():
    logger.info("Profiles requested")
    return load_profiles_data()


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    logger.info(f"Profile lookup requested for ID={profile_id}")

    profiles = load_profiles_data()
    profile = next((p for p in profiles if str(p["id"]) == profile_id), None)

    if not profile:
        logger.warning(f"Profile not found: {profile_id}")
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


# ================================================================
# PROFILE ANALYSIS ENDPOINT
# ================================================================
@app.post("/api/profiles/analysis-batch", response_model=AnalysisBatchResponse)
def analyze_profiles(request: AnalysisRequest):
    logger.info(f"Batch analysis requested for {len(request.ids)} profiles")

    profiles = load_profiles_data()
    results = []

    for profile_id in request.ids:
        profile = next((p for p in profiles if str(p["id"]) == profile_id), None)
        if not profile:
            logger.warning(f"Profile missing during analysis: {profile_id}")
            continue

        analysis = (
            profile.get("maragonAnalysis")
            or profile.get("paragonAnalysis")
            or []
        )

        dimensions_map = {
            item["dimension"]: item.get("score", 0)
            for item in analysis
            if item.get("dimension")
        }

        values = list(dimensions_map.values())
        overall = int(sum(values) / len(values)) if values else 0

        results.append(
            AnalysisResponseItem(
                id=profile_id,
                overallScore=overall,
                dimensions=dimensions_map
            )
        )

    return AnalysisBatchResponse(analyses=results)


# ================================================================
# NEWS AGGREGATION (RSS)
# ================================================================
RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://news.google.com/rss/search?q=site:reuters.com",
]


@app.get("/api/v1/news", response_model=List[NewsArticle])
async def get_news():
    logger.info("Fetching international news feeds")

    articles = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            if feed.bozo and feed.status not in (200, 301):
                logger.error(f"Bad RSS Feed: {url}")
                continue

            for entry in feed.entries[:5]:
                article_id = entry.get("id") or entry.get("link", "unknown")

                image_url = (
                    entry.media_content[0].get("url", "")
                    if hasattr(entry, "media_content") and entry.media_content
                    else ""
                )

                articles.append(
                    NewsArticle(
                        id=str(article_id),
                        title=entry.get("title", "No Title"),
                        content=(entry.get("summary", "")[:300] + "..."),
                        imageUrl=image_url,
                        category="International",
                        timestamp=entry.get("published", "Unknown"),
                    )
                )

        except Exception as e:
            logger.exception(f"Feed parsing error for {url}: {e}")
            continue

    logger.info(f"News articles delivered: {len(articles)}")
    return articles


# ================================================================
# REGISTER PARAGON ANALYTICS ROUTER
# ================================================================
app.include_router(paragon_router)


# ================================================================
# STARTUP & SHUTDOWN EVENTS
# ================================================================
@app.on_event("startup")
def startup_event():
    logger.info("NOVARIC Backend has started successfully.")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("NOVARIC Backend shutting down gracefully.")


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.environ.get("PORT", 8080))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
