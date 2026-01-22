# ================================================================
# RSS FEED ADAPTER (MUST BE FIRST IMPORT)
# ================================================================
import rss_feeds_adapter  # activates weighted feeds globally

import os
import time
import logging
import re
from typing import List, Dict, Optional, Literal
from urllib.parse import urlparse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import Response
from pydantic import BaseModel

# ================================================================
# LOGGING (BOOT FIRST)
# ================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("novaric-backend")
logger.info("NOVARIC backend boot sequence started")

# ================================================================
# DATA LOADER (LEGACY COMPATIBILITY)
# ================================================================
from utils.data_loader import load_profiles_data

# ================================================================
# ROUTERS (GUARDED IMPORTS — DO NOT BLOCK SERVER START)
# ================================================================
paragon_router = None
enrichment_router = None
politicians_router = None

try:
    from paragon_api import router as paragon_router  # type: ignore
    logger.info("PARAGON router loaded")
except Exception as e:
    logger.error(f"Failed to load PARAGON router (startup continues): {e}")

try:
    from routers.profile_enrichment import router as enrichment_router  # type: ignore
    logger.info("Enrichment router loaded")
except Exception as e:
    logger.error(f"Failed to load enrichment router (startup continues): {e}")

# 🔑 OPTION A: politicians cards API
try:
    from routers.politicians import router as politicians_router  # type: ignore
    logger.info("Politicians router loaded")
except Exception as e:
    logger.warning(f"Politicians router not loaded yet: {e}")

# ================================================================
# FEED REGISTRY
# ================================================================
from config.rss_feeds import (
    get_feeds_for_news_category,
    BALKAN_REGIONAL_FEEDS,
    ALBANIAN_MEDIA_FEEDS,
)

# ================================================================
# NER (NOVARIC ECOSYSTEM RATING)
# ================================================================
try:
    from services.ner_engine import compute_ner  # type: ignore
    from services.ner_repository import get_snapshot, save_snapshot  # type: ignore
    logger.info("NER engine loaded")
except Exception as e:
    compute_ner = None
    get_snapshot = None
    save_snapshot = None
    logger.warning(f"NER disabled (startup continues): {e}")

# ================================================================
# SIMPLE IN-MEMORY TTL CACHE
# ================================================================
_NEWS_CACHE: Dict[str, Dict[str, object]] = {}
_NEWS_CACHE_TTL_SECONDS = int(os.getenv("NEWS_CACHE_TTL_SECONDS", "300"))

# ================================================================
# FASTAPI APP
# ================================================================
app = FastAPI(
    title="NOVARIC Backend",
    description="Official NOVARIC® Backend Services • News • PARAGON",
    version="2.3.0",
    docs_url=None,
    redoc_url=None,
)

# ================================================================
# ROUTE INTROSPECTION (DEBUG)
# ================================================================
@app.get("/__routes", include_in_schema=False)
def list_routes():
    return sorted(
        [
            {
                "path": r.path,
                "methods": list(getattr(r, "methods", [])),
                "name": r.name,
            }
            for r in app.router.routes
            if hasattr(r, "path")
        ],
        key=lambda x: x["path"],
    )

# ================================================================
# STATIC FILES
# ================================================================
app.mount("/static", StaticFiles(directory="static"), name="static")

# ================================================================
# FAVICON
# ================================================================
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    with open("static/favicon.ico", "rb") as f:
        return Response(f.read(), media_type="image/x-icon")

# ================================================================
# CUSTOM SWAGGER
# ================================================================
@app.get("/docs", include_in_schema=False)
def custom_swagger_docs():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="NOVARIC® Backend API",
        swagger_favicon_url="/static/favicon.ico",
    )

# ================================================================
# CORS
# ================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# MODELS
# ================================================================
SourceType = Literal["international", "balkan", "albanian"]


class NewsArticle(BaseModel):
    id: str
    title: str
    content: str
    imageUrl: str = ""
    timestamp: str
    feedUrl: str
    sourceName: str
    sourceType: SourceType
    category: Optional[str] = None
    originalArticleUrl: Optional[str] = None

    ecosystemRating: Optional[int] = None
    nerVersion: Optional[str] = None
    nerBreakdown: Optional[Dict[str, object]] = None


# ================================================================
# HELPERS
# ================================================================
def infer_source_type(feed_url: str) -> SourceType:
    if feed_url in ALBANIAN_MEDIA_FEEDS:
        return "albanian"
    if feed_url in BALKAN_REGIONAL_FEEDS:
        return "balkan"
    return "international"


def infer_source_name(parsed_feed: object, feed_url: str) -> str:
    title = getattr(parsed_feed.feed, "title", None)
    return title.strip() if title else urlparse(feed_url).netloc.replace("www.", "")


def extract_image(entry: object) -> str:
    for attr in ("media_content", "media_thumbnail"):
        media = getattr(entry, attr, None)
        if media and isinstance(media, list) and media[0].get("url"):
            return media[0]["url"]
    return ""


def _epoch(ts: str) -> float:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


# ================================================================
# ROOT / HEALTH
# ================================================================
@app.get("/")
def root():
    try:
        profiles_count = len(load_profiles_data())
    except Exception:
        profiles_count = 0

    return {
        "status": "online",
        "engine": "NOVARIC®",
        "profiles_loaded": profiles_count,
        "paragon": bool(paragon_router),
        "politicians_api": bool(politicians_router),
    }


@app.get("/healthz", include_in_schema=False)
def health_probe():
    return {"status": "healthy"}


# ================================================================
# NEWS API
# ================================================================
@app.get("/api/v1/news", response_model=List[NewsArticle])
async def get_news(category: str = Query(default="all")):
    feeds = get_feeds_for_news_category(category)
    articles: List[NewsArticle] = []

    for url in feeds:
        parsed = feedparser.parse(url)
        for entry in parsed.entries[:1]:
            articles.append(
                NewsArticle(
                    id=str(entry.get("id") or entry.get("link") or ""),
                    title=entry.get("title", ""),
                    content=(entry.get("summary", "")[:300] + "..."),
                    imageUrl=extract_image(entry),
                    timestamp=entry.get("published", ""),
                    feedUrl=url,
                    sourceName=infer_source_name(parsed, url),
                    sourceType=infer_source_type(url),
                    category=category,
                    originalArticleUrl=entry.get("link"),
                )
            )

    return sorted(articles, key=lambda x: -_epoch(x.timestamp))


# ================================================================
# ROUTER MOUNTING (AUTHORITATIVE)
# ================================================================
if paragon_router:
    app.include_router(paragon_router, prefix="/api")

if enrichment_router:
    app.include_router(enrichment_router, prefix="/api")

if politicians_router:
    app.include_router(politicians_router, prefix="/api")

# ================================================================
# LIFECYCLE
# ================================================================
@app.on_event("startup")
def startup_event():
    logger.info("NOVARIC Backend started successfully.")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("NOVARIC Backend stopped.")
