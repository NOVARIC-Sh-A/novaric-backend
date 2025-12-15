import os
import logging
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import feedparser

# Data Loader (legacy compatibility)
from utils.data_loader import load_profiles_data

# Routers
from paragon_api import router as paragon_router
from routers.profile_enrichment import router as enrichment_router

# Feed Registry (Category-aware)
from config.rss_feeds import get_feeds_for_news_category


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
    description="NOVARIC® PARAGON Engine • Profile Enrichment • News Aggregation",
    version="2.1.0",
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
# MODELS (Legacy MARAGON)
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

    return {
        "message": "NOVARIC® Engine Online",
        "profiles_loaded": profiles_count,
        "data_mode": (
            "Supabase Live"
            if os.getenv("USE_LIVE_DB") == "True"
            else "Local Mock Data"
        )
    }


@app.get("/healthz")
def health_probe():
    return {"status": "healthy"}


# ================================================================
# PROFILES (Legacy MARAGON)
# ================================================================
@app.get("/api/profiles")
def get_profiles():
    return load_profiles_data()


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    profiles = load_profiles_data()
    found = next((p for p in profiles if str(p["id"]) == profile_id), None)

    if not found:
        raise HTTPException(status_code=404, detail="Profile not found")

    return found


# ================================================================
# ANALYSIS BATCH
# ================================================================
@app.post("/api/profiles/analysis-batch", response_model=AnalysisBatchResponse)
def analyze_profiles(request: AnalysisRequest):
    profiles = load_profiles_data()
    results = []

    for pid in request.ids:
        profile = next((p for p in profiles if str(p["id"]) == pid), None)

        if not profile:
            continue

        analysis = (
            profile.get("maragonAnalysis")
            or profile.get("paragonAnalysis")
            or []
        )

        dims = {
            item["dimension"]: item.get("score", 0)
            for item in analysis
            if item.get("dimension")
        }

        values = list(dims.values())
        overall = int(sum(values) / len(values)) if values else 0

        results.append(
            AnalysisResponseItem(
                id=pid,
                overallScore=overall,
                dimensions=dims
            )
        )

    return AnalysisBatchResponse(analyses=results)


# ================================================================
# NEWS AGGREGATION — CATEGORY-AWARE (BACKWARD SAFE)
# ================================================================
@app.get("/api/v1/news", response_model=List[NewsArticle])
async def get_news(
    category: str = Query(
        default="international",
        description=(
            "News category: international, balkan, albanian, politics, "
            "media, judiciary, academic, vip, all"
        )
    )
):
    articles: List[NewsArticle] = []

    feeds = get_feeds_for_news_category(category)

    for url in feeds:
        try:
            feed = feedparser.parse(url)
            status = getattr(feed, "status", None)

            # Handle malformed RSS or HTTP failures
            if feed.bozo:
                exc = getattr(feed, "bozo_exception", None)
                logger.warning(f"[BOZO] RSS parsing issue for {url}: {exc}")
                if status and status not in (200, 301):
                    continue

            entries = getattr(feed, "entries", [])
            if not entries:
                continue

            for entry in entries[:7]:
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
                        id=str(entry.get("id") or entry.get("link", "unknown")),
                        title=entry.get("title", "No Title"),
                        content=(entry.get("summary", "")[:300] + "..."),
                        imageUrl=image,
                        category=category.capitalize(),
                        timestamp=entry.get(
                            "published",
                            entry.get("updated", "Unknown")
                        ),
                    )
                )

        except Exception as e:
            logger.error(f"[ERROR] Exception while loading {url}: {e}")
            continue

    return articles


# ================================================================
# REGISTER ROUTERS
# ================================================================
app.include_router(paragon_router)
app.include_router(enrichment_router)


# ================================================================
# STARTUP / SHUTDOWN
# ================================================================
@app.on_event("startup")
def startup_event():
    logger.info("NOVARIC Backend started.")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("NOVARIC Backend stopped.")


# ================================================================
# LOCAL DEV ENTRYPOINT
# ================================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=False
    )
