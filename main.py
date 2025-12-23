# main.py

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
from feedgen.feed import FeedGenerator

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
logger.info("Creating FastAPI app")

app = FastAPI(
    title="NOVARIC Backend",
    description="Official NOVARIC® Backend Services • News • PARAGON • Enrichment",
    version="2.2.0",
    docs_url=None,
    redoc_url=None,
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
    allow_origins=["*"],
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
    try:
        title = getattr(parsed_feed.feed, "title", None)
        if title:
            return str(title).strip()
    except Exception:
        pass
    return urlparse(feed_url).netloc.replace("www.", "")


def extract_image(entry: object) -> str:
    for attr in ("media_content", "media_thumbnail"):
        try:
            media = getattr(entry, attr, None)
            if media and media[0].get("url"):
                return media[0]["url"]
        except Exception:
            pass
    return ""


def cache_get(key: str):
    blob = _NEWS_CACHE.get(key)
    if not blob:
        return None
    if time.time() - blob["ts"] > _NEWS_CACHE_TTL_SECONDS:
        return None
    return blob["data"]


def cache_set(key: str, data):
    _NEWS_CACHE[key] = {"ts": time.time(), "data": data}


def _safe_epoch_from_entry(entry: object) -> float:
    try:
        ts = entry.get("published_parsed") or entry.get("updated_parsed")
        if ts:
            return float(time.mktime(ts))
    except Exception:
        pass
    return 0.0


def _normalize_title(title: str) -> str:
    t = (title or "").lower().strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[^\w\sÀ-ž]", "", t)
    return t[:180]


def _dedupe_key(article: NewsArticle) -> str:
    if article.originalArticleUrl:
        return f"url:{article.originalArticleUrl}"
    if article.id:
        return f"id:{article.id}"
    return f"title:{_normalize_title(article.title)}"


def _epoch(ts: str) -> float:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


def _choose_better(a: NewsArticle, b: NewsArticle) -> NewsArticle:
    ar = a.ecosystemRating or -1
    br = b.ecosystemRating or -1
    if br != ar:
        return b if br > ar else a

    ea = _epoch(a.timestamp)
    eb = _epoch(b.timestamp)
    if eb != ea:
        return b if eb > ea else a

    return b if (b.feedUrl, b.id) < (a.feedUrl, a.id) else a


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
        "paragon_router_loaded": bool(paragon_router),
        "enrichment_router_loaded": bool(enrichment_router),
    }


@app.get("/healthz", include_in_schema=False)
def health_probe():
    return {"status": "healthy"}


# ================================================================
# CORE NEWS PIPELINE
# ================================================================
def _parse_feed(url: str):
    try:
        parsed = feedparser.parse(url)
        if getattr(parsed, "bozo", False):
            return None
        return url, parsed
    except Exception:
        return None


async def collect_news_articles(category: str) -> List[NewsArticle]:
    key = (category or "all").strip().lower()
    cached = cache_get(key)
    if cached is not None:
        return cached

    feeds = get_feeds_for_news_category(key) or []
    articles: List[NewsArticle] = []

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(_parse_feed, url) for url in feeds]

        for future in as_completed(futures):
            result = future.result()
            if not result:
                continue

            url, parsed = result
            entries = parsed.entries or []
            if not entries:
                continue

            # Exactly ONE per feed (most recent)
            entry = sorted(entries, key=_safe_epoch_from_entry, reverse=True)[0]

            article_id = str(entry.get("id") or entry.get("link") or "")
            title = (entry.get("title") or "No Title").strip()
            summary = entry.get("summary") or ""
            published_ts = entry.get("published", entry.get("updated", "")) or ""

            source_type = infer_source_type(url)
            source_name = infer_source_name(parsed, url)

            ecosystem_rating = None
            ner_version = None
            ner_breakdown = None

            snapshot = get_snapshot(article_id) if get_snapshot else None

            if snapshot:
                ecosystem_rating = snapshot.ecosystemRating
                ner_version = snapshot.nerVersion
                # snapshot.breakdown can be dataclass-like; preserve safely
                try:
                    ner_breakdown = snapshot.breakdown.__dict__
                except Exception:
                    ner_breakdown = snapshot.breakdown
            elif compute_ner and save_snapshot:
                try:
                    ner = compute_ner(
                        feed_url=url,
                        source_type=source_type,
                        title=title,
                        summary=summary,
                        published_ts=published_ts,
                        peer_titles=[],
                    )
                    ecosystem_rating = ner.ecosystemRating
                    ner_version = ner.nerVersion
                    ner_breakdown = ner.breakdown.__dict__

                    save_snapshot(
                        article_id=article_id,
                        feed_url=url,
                        published_ts=published_ts,
                        ner=ner,
                    )
                except Exception as e:
                    logger.warning(f"NER skipped: {e}")

            articles.append(
                NewsArticle(
                    id=article_id,
                    title=title,
                    content=(summary[:300] + "...") if summary else "",
                    imageUrl=extract_image(entry),
                    timestamp=published_ts,
                    feedUrl=url,
                    sourceName=source_name,
                    sourceType=source_type,
                    category=key,
                    originalArticleUrl=entry.get("link"),
                    ecosystemRating=ecosystem_rating,
                    nerVersion=ner_version,
                    nerBreakdown=ner_breakdown,
                )
            )

    # Cross-feed duplicate suppression
    deduped: Dict[str, NewsArticle] = {}
    for a in articles:
        k = _dedupe_key(a)
        deduped[k] = a if k not in deduped else _choose_better(deduped[k], a)

    final_articles = sorted(
        deduped.values(),
        key=lambda x: (-(x.ecosystemRating or -1), -_epoch(x.timestamp)),
    )

    cache_set(key, final_articles)
    return final_articles


# ================================================================
# NEWS API
# ================================================================
@app.get("/api/v1/news", response_model=List[NewsArticle])
async def get_news(category: str = Query(default="all")):
    return await collect_news_articles(category)


# ================================================================
# RSS FEED
# ================================================================
@app.get("/rss.xml", include_in_schema=False)
async def rss_feed(category: str = Query(default="all")):
    articles = await collect_news_articles(category)

    fg = FeedGenerator()
    fg.id("https://api.media.novaric.al/rss.xml")
    fg.title("NOVARIC® Media")
    fg.link(href="https://media.novaric.al", rel="alternate")
    fg.link(href=f"https://api.media.novaric.al/rss.xml?category={category}", rel="self")
    fg.description("AI-powered media intelligence from NOVARIC®")
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

        if article.ecosystemRating is not None:
            fe.rss_entry()["extension_elements"] = [
                ("novaric:ecosystemRating", str(article.ecosystemRating)),
                ("novaric:nerVersion", str(article.nerVersion or "")),
            ]

        if article.imageUrl:
            fe.enclosure(article.imageUrl, 0, "image/jpeg")

    return Response(
        content=fg.rss_str(pretty=True),
        media_type="application/rss+xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=600"},
    )


# ================================================================
# ROUTERS
# ================================================================
if paragon_router:
    app.include_router(paragon_router)

if enrichment_router:
    app.include_router(enrichment_router)


# ================================================================
# LIFECYCLE
# ================================================================
@app.on_event("startup")
def startup_event():
    logger.info("NOVARIC Backend started.")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("NOVARIC Backend stopped.")
