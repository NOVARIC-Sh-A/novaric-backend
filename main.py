# main.py

# ================================================================
# RSS FEED ADAPTER (MUST BE FIRST IMPORT)
# ================================================================
import rss_feeds_adapter  # activates weighted feeds globally

import os
import time
import logging
from typing import List, Dict, Optional, Literal
from urllib.parse import urlparse
from datetime import datetime, timezone

import feedparser
from feedgen.feed import FeedGenerator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import Response
from pydantic import BaseModel

# ================================================================
# DATA LOADER (LEGACY COMPATIBILITY)
# ================================================================
from utils.data_loader import load_profiles_data

# ================================================================
# ROUTERS
# ================================================================
from paragon_api import router as paragon_router
from routers.profile_enrichment import router as enrichment_router

# ================================================================
# FEED REGISTRY (CATEGORY-AWARE)
# ================================================================
from config.rss_feeds import (
    get_feeds_for_news_category,
    TIER1_GLOBAL_NEWS,
    BALKAN_REGIONAL_FEEDS,
    ALBANIAN_MEDIA_FEEDS,
)

# ================================================================
# LOGGING
# ================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("novaric-backend")

# ================================================================
# SIMPLE IN-MEMORY TTL CACHE (NEWS ENDPOINT)
# ================================================================
_NEWS_CACHE: Dict[str, Dict[str, object]] = {}
_NEWS_CACHE_TTL_SECONDS = int(os.getenv("NEWS_CACHE_TTL_SECONDS", "60"))

# ================================================================
# FASTAPI APP (SWAGGER DISABLED – CUSTOM DOCS BELOW)
# ================================================================
app = FastAPI(
    title="NOVARIC Backend",
    description="Official NOVARIC® Backend Services • NOVARIC® PARAGON Engine • Profile Enrichment • News Aggregation",
    version="2.2.0",
    docs_url=None,
    redoc_url=None,
)

# ================================================================
# STATIC FILES (FAVICON, ASSETS)
# ================================================================
app.mount("/static", StaticFiles(directory="static"), name="static")

# ================================================================
# FAVICON FALLBACK
# ================================================================
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    with open("static/favicon.ico", "rb") as f:
        return Response(f.read(), media_type="image/x-icon")

# ================================================================
# CUSTOM SWAGGER DOCS (BRANDED)
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
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================================================
# MODELS (LEGACY MARAGON)
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


# ================================================================
# NEWS MODEL (AUTHORITATIVE CONTRACT FOR FRONTEND)
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
    try:
        feed_meta = getattr(parsed_feed, "feed", None)
        title = getattr(feed_meta, "title", None)
        if title:
            return str(title).strip()
    except Exception:
        pass

    try:
        return urlparse(feed_url).netloc.replace("www.", "")
    except Exception:
        return "unknown"


def extract_image(entry: object) -> str:
    try:
        media_content = getattr(entry, "media_content", None)
        if media_content:
            url = media_content[0].get("url")
            if url:
                return str(url)
    except Exception:
        pass

    try:
        media_thumbnail = getattr(entry, "media_thumbnail", None)
        if media_thumbnail:
            url = media_thumbnail[0].get("url")
            if url:
                return str(url)
    except Exception:
        pass

    try:
        links = getattr(entry, "links", None)
        if links:
            for link in links:
                if (link.get("type", "") or "").startswith("image"):
                    href = link.get("href")
                    if href:
                        return str(href)
    except Exception:
        pass

    return ""


def cache_get(key: str) -> Optional[List[NewsArticle]]:
    now = time.time()
    blob = _NEWS_CACHE.get(key)
    if not blob:
        return None
    ts = float(blob.get("ts", 0.0))
    if (now - ts) > _NEWS_CACHE_TTL_SECONDS:
        return None
    return blob.get("data")


def cache_set(key: str, data: List[NewsArticle]) -> None:
    _NEWS_CACHE[key] = {"ts": time.time(), "data": data}


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
        "message": "NOVARIC® Engine Online",
        "profiles_loaded": profiles_count,
        "news_cache_ttl_seconds": _NEWS_CACHE_TTL_SECONDS,
    }


@app.get("/healthz", include_in_schema=False)
def health_probe():
    return {"status": "healthy"}


# ================================================================
# NEWS AGGREGATION (AUTHORITATIVE PIPELINE)
# ================================================================
@app.get("/api/v1/news", response_model=List[NewsArticle])
async def get_news(
    category: str = Query(default="all")
):
    key = (category or "all").strip().lower()

    cached = cache_get(key)
    if cached is not None:
        return cached

    feeds = get_feeds_for_news_category(key)
    articles: List[NewsArticle] = []

    max_entries_per_feed = int(os.getenv("NEWS_MAX_ENTRIES_PER_FEED", "7"))
    max_total_articles = int(os.getenv("NEWS_MAX_TOTAL_ARTICLES", "200"))

    for url in feeds:
        if len(articles) >= max_total_articles:
            break

        try:
            parsed = feedparser.parse(url)
            source_type = infer_source_type(url)
            source_name = infer_source_name(parsed, url)

            entries = getattr(parsed, "entries", []) or []
            for entry in entries[:max_entries_per_feed]:
                if len(articles) >= max_total_articles:
                    break

                title = (entry.get("title") or "No Title").strip()
                summary = entry.get("summary") or entry.get("description") or ""
                link = entry.get("link") or ""
                entry_id = entry.get("id") or link or "unknown"

                articles.append(
                    NewsArticle(
                        id=str(entry_id),
                        title=title,
                        content=(summary[:300] + "...") if summary else "",
                        imageUrl=extract_image(entry),
                        timestamp=entry.get("published", entry.get("updated", "")),
                        feedUrl=url,
                        sourceName=source_name,
                        sourceType=source_type,
                        category=key,
                        originalArticleUrl=str(link) if link else None,
                    )
                )

        except Exception as e:
            logger.error(f"[ERROR] Exception while loading {url}: {e}")
            continue

    cache_set(key, articles)
    return articles


# ================================================================
# RSS FEED (PUBLIC, CANONICAL)
# ================================================================
@app.get("/rss.xml", include_in_schema=False)
async def rss_feed(
    category: str = Query(default="all")
):
    articles = await get_news(category)

    fg = FeedGenerator()
    fg.id("https://media.novaric.al/rss.xml")
    fg.title("NOVARIC® Media")
    fg.link(href="https://media.novaric.al", rel="alternate")
    fg.link(
        href=f"https://media.novaric.al/rss.xml?category={category}",
        rel="self",
    )
    fg.description(
        "Latest AI-powered media intelligence and political news from NOVARIC®."
    )
    fg.language("en")
    fg.updated(datetime.now(timezone.utc))

    for article in articles:
        fe = fg.add_entry()
        fe.id(article.id)
        fe.title(article.title)
        fe.link(href=article.originalArticleUrl or "")
        fe.description(article.content)
        fe.author({"name": article.sourceName})
        fe.category(term=article.sourceType)

        try:
            fe.published(datetime.fromisoformat(article.timestamp))
        except Exception:
            pass

        if article.imageUrl:
            fe.enclosure(article.imageUrl, 0, "image/jpeg")

    return Response(
        content=fg.rss_str(pretty=True),
        media_type="application/rss+xml; charset=utf-8",
        headers={
            "Cache-Control": "public, max-age=600"
        },
    )


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
# LOCAL / CLOUD RUN ENTRYPOINT
# ================================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=False,
    )
