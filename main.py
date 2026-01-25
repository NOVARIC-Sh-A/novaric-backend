# main.py

from __future__ import annotations

# ================================================================
# RSS FEED ADAPTER (MUST BE FIRST IMPORT)
# ================================================================
import rss_feeds_adapter  # noqa: F401  # activates weighted feeds globally

import os
import sys
import time
import logging
import re
from typing import List, Dict, Optional, Literal
from urllib.parse import urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import feedparser
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

# ================================================================
# STDOUT/STDERR FLUSH (CLOUD RUN FRIENDLY)
# ================================================================
try:
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

# ================================================================
# LOGGING (BOOT FIRST)
# ================================================================
_root = logging.getLogger()
if not _root.handlers:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
else:
    _root.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

logger = logging.getLogger("novaric-backend")
logger.propagate = True
logger.info("NOVARIC backend boot sequence started")

# ================================================================
# DATA LOADER (LEGACY COMPATIBILITY)
# ================================================================
from utils.data_loader import load_profiles_data  # noqa: E402

# ================================================================
# ROUTERS (GUARDED IMPORTS — DO NOT BLOCK SERVER START)
# ================================================================
paragon_router = None
enrichment_router = None
politicians_router = None

try:
    from paragon_api import router as paragon_router  # type: ignore  # noqa: E402

    logger.info("PARAGON router loaded")
except Exception as e:
    logger.exception("Failed to load PARAGON router (startup continues): %s", e)

try:
    from routers.profile_enrichment import router as enrichment_router  # type: ignore  # noqa: E402

    logger.info("Enrichment router loaded")
except Exception as e:
    logger.exception("Failed to load enrichment router (startup continues): %s", e)

try:
    from routers.politicians import router as politicians_router  # type: ignore  # noqa: E402

    logger.info("Politicians router loaded")
except Exception as e:
    logger.warning("Politicians router not loaded yet: %s", e)

# ================================================================
# FEED REGISTRY
# ================================================================
from config.rss_feeds import (  # noqa: E402
    get_feeds_for_news_category,
    BALKAN_REGIONAL_FEEDS,
    ALBANIAN_MEDIA_FEEDS,
)

# ================================================================
# NER (NOVARIC ECOSYSTEM RATING)
# ================================================================
try:
    from services.ner_engine import compute_ner  # type: ignore  # noqa: E402
    from services.ner_repository import get_snapshot, save_snapshot  # type: ignore  # noqa: E402

    logger.info("NER engine loaded")
except Exception as e:
    compute_ner = None
    get_snapshot = None
    save_snapshot = None
    logger.warning("NER disabled (startup continues): %s", e)

# ================================================================
# SIMPLE IN-MEMORY TTL CACHE
# ================================================================
_NEWS_CACHE: Dict[str, Dict[str, object]] = {}
_NEWS_CACHE_TTL_SECONDS = int(os.getenv("NEWS_CACHE_TTL_SECONDS", "30"))

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
# GLOBAL EXCEPTION LOGGING (DOES NOT CHANGE RESPONSE CONTRACTS)
# ================================================================
@app.middleware("http")
async def _log_unhandled_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.exception("Unhandled exception: %s %s | %s", request.method, request.url.path, e)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


# ================================================================
# ROUTE INTROSPECTION (DEBUG)
# ================================================================
@app.get("/__routes", include_in_schema=False)
def list_routes():
    return sorted(
        [
            {"path": r.path, "methods": list(getattr(r, "methods", [])), "name": r.name}
            for r in app.router.routes
            if hasattr(r, "path")
        ],
        key=lambda x: x["path"],
    )


# ================================================================
# STATIC FILES (SAFE)
# ================================================================
# Avoid startup crash if the static directory is missing in some deployments.
try:
    if os.path.isdir("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
    else:
        logger.warning("Static directory 'static/' not found; /static will not be mounted.")
except Exception as e:
    logger.warning("Static mount failed (startup continues): %s", e)


# ================================================================
# FAVICON (SAFE)
# ================================================================
@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    try:
        path = os.path.join("static", "favicon.ico")
        with open(path, "rb") as f:
            return Response(f.read(), media_type="image/x-icon")
    except Exception:
        return Response(status_code=404)


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
    title = getattr(parsed_feed, "feed", None)
    feed_title = getattr(title, "title", None) if title else None
    return feed_title.strip() if feed_title else urlparse(feed_url).netloc.replace("www.", "")


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
    # ------------------------------------------------------------
    # 0) TTL cache
    # ------------------------------------------------------------
    now = time.time()
    cached = _NEWS_CACHE.get(category)
    if cached:
        cached_at = float(cached.get("ts", 0.0) or 0.0)
        if (now - cached_at) <= _NEWS_CACHE_TTL_SECONDS:
            data = cached.get("data")
            if isinstance(data, list):
                return data

    feeds = get_feeds_for_news_category(category)

    per_feed = int(os.getenv("NEWS_ENTRIES_PER_FEED", "4"))
    per_feed = max(1, min(10, per_feed))

    # ------------------------------------------------------------
    # 1) Parse feeds concurrently
    # ------------------------------------------------------------
    def _fetch_feed(feed_url: str) -> List[dict]:
        try:
            parsed = feedparser.parse(feed_url)
            entries = getattr(parsed, "entries", []) or []
            if not entries:
                return []

            src_name = infer_source_name(parsed, feed_url)
            src_type = infer_source_type(feed_url)

            out: List[dict] = []
            for entry in entries[:per_feed]:
                out.append(
                    {
                        "id": str(entry.get("id") or entry.get("link") or ""),
                        "title": entry.get("title", "") or "",
                        "summary": entry.get("summary", "") or "",
                        "published": entry.get("published", "") or "",
                        "imageUrl": extract_image(entry),
                        "feedUrl": feed_url,
                        "sourceName": src_name,
                        "sourceType": src_type,
                        "originalArticleUrl": entry.get("link"),
                    }
                )
            return out
        except Exception as e:
            logger.warning("Feed parse failed: %s | %s", feed_url, e)
            return []

    raw: List[dict] = []
    max_workers = min(16, max(4, len(feeds) or 4))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [pool.submit(_fetch_feed, url) for url in feeds]
        for f in as_completed(futures):
            raw.extend(f.result() or [])

    if not raw:
        _NEWS_CACHE[category] = {"ts": now, "data": []}
        return []

    # ------------------------------------------------------------
    # 2) Peer titles (fingerprint + Jaccard >= 0.35, cross-source only)
    # ------------------------------------------------------------
    def _fingerprint_title(title: str) -> set[str]:
        t = (title or "").lower()
        tokens = re.findall(r"[a-zA-ZÀ-ž0-9']+", t)
        stop = {
            "the",
            "and",
            "or",
            "of",
            "to",
            "in",
            "a",
            "an",
            "for",
            "on",
            "with",
            "nga",
            "dhe",
            "ose",
            "ne",
            "per",
        }
        core = [x for x in tokens if len(x) >= 4 and x not in stop]
        return set(core[:20])

    def _jacc(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / max(1, len(a | b))

    fps = [_fingerprint_title(it.get("title", "")) for it in raw]

    peer_titles_by_idx: List[List[str]] = [[] for _ in raw]
    for i, it in enumerate(raw):
        fi = fps[i]
        if not fi:
            continue

        peers: List[str] = []
        for j, other in enumerate(raw):
            if i == j:
                continue
            if it.get("sourceName") == other.get("sourceName"):
                continue
            if _jacc(fi, fps[j]) >= 0.35:
                t = (other.get("title") or "").strip()
                if t:
                    peers.append(t)

        seen = set()
        deduped: List[str] = []
        for t in peers:
            k = t.casefold()
            if k not in seen:
                seen.add(k)
                deduped.append(t)
        peer_titles_by_idx[i] = deduped

    # ------------------------------------------------------------
    # 3) Batch-fetch snapshots (optional)
    # ------------------------------------------------------------
    snapshots_by_article_id: Dict[str, dict] = {}

    try:
        from utils.supabase_client import supabase, is_supabase_configured  # type: ignore

        supabase_ok = bool(supabase and is_supabase_configured())
    except Exception:
        supabase_ok = False
        supabase = None  # type: ignore

    if supabase_ok:
        article_ids: List[str] = []
        for it in raw:
            aid = (it.get("id") or it.get("originalArticleUrl") or "").strip()
            if aid:
                article_ids.append(aid)

        article_ids = list(dict.fromkeys(article_ids))

        try:
            if article_ids:
                res = (
                    supabase.table("ner_snapshots")
                    .select("article_id,ecosystem_rating,ner_version,srs,cis,csc,trf,ecm")
                    .in_("article_id", article_ids)
                    .execute()
                )
                rows = getattr(res, "data", None) or []
                for row in rows:
                    aid = str(row.get("article_id") or "")
                    if aid:
                        snapshots_by_article_id[aid] = row
        except Exception as e:
            logger.warning("Batch snapshot fetch failed (fallbacks will apply): %s", e)
            snapshots_by_article_id = {}

    # ------------------------------------------------------------
    # 4) Build response; compute+persist NER only when snapshot missing
    # ------------------------------------------------------------
    ner_enabled = bool(compute_ner and get_snapshot and save_snapshot)
    articles: List[NewsArticle] = []

    for idx, it in enumerate(raw):
        title = it.get("title", "") or ""
        summary = it.get("summary", "") or ""
        published = it.get("published", "") or ""
        feed_url = it.get("feedUrl", "") or ""
        source_type = it.get("sourceType", "international") or "international"
        peers = peer_titles_by_idx[idx]

        article_id = (it.get("id") or it.get("originalArticleUrl") or "").strip()
        if not article_id:
            article_id = f"{feed_url}::{title}".strip()

        a = NewsArticle(
            id=article_id,
            title=title,
            content=(summary[:300] + "...") if summary else "",
            imageUrl=it.get("imageUrl", "") or "",
            timestamp=published,
            feedUrl=feed_url,
            sourceName=it.get("sourceName", "") or "",
            sourceType=source_type,  # type: ignore
            category=category,
            originalArticleUrl=it.get("originalArticleUrl"),
        )

        def _base_breakdown() -> Dict[str, object]:
            return {
                "SRS": 0,
                "CIS": 0,
                "CSC": 0,
                "TRF": 0,
                "ECM": 1.0,
                "peer_titles": peers,
                "corroborators": len(peers),
            }

        if not ner_enabled:
            a.ecosystemRating = None
            a.nerVersion = "ner_disabled"
            a.nerBreakdown = _base_breakdown()
            articles.append(a)
            continue

        try:
            # 1) Prefer batch snapshot
            row = snapshots_by_article_id.get(article_id)
            if isinstance(row, dict):
                a.ecosystemRating = int(row.get("ecosystem_rating") or 0)
                a.nerVersion = str(row.get("ner_version") or "ner_v1.0")
                a.nerBreakdown = {
                    "SRS": int(row.get("srs") or 0),
                    "CIS": int(row.get("cis") or 0),
                    "CSC": int(row.get("csc") or 0),
                    "TRF": int(row.get("trf") or 0),
                    "ECM": float(row.get("ecm") or 1.0),
                    "peer_titles": peers,
                    "corroborators": len(peers),
                }
                articles.append(a)
                continue

            # 2) Repository snapshot
            snap = get_snapshot(article_id)  # type: ignore[misc]
            if snap:
                a.ecosystemRating = int(snap.ecosystemRating)
                a.nerVersion = str(getattr(snap, "nerVersion", None) or "ner_v1.0")
                a.nerBreakdown = {
                    "SRS": int(snap.breakdown.SRS),
                    "CIS": int(snap.breakdown.CIS),
                    "CSC": int(snap.breakdown.CSC),
                    "TRF": int(snap.breakdown.TRF),
                    "ECM": float(snap.breakdown.ECM),
                    "peer_titles": peers,
                    "corroborators": len(peers),
                }
                articles.append(a)
                continue

            # 3) Compute fresh NER
            ner_res = compute_ner(  # type: ignore[misc]
                feed_url=feed_url,
                source_type=source_type,
                title=title,
                summary=summary,
                published_ts=published,
                peer_titles=peers,
            )

            a.ecosystemRating = int(ner_res.ecosystemRating)
            a.nerVersion = str(getattr(ner_res, "nerVersion", None) or "ner_v1.0")
            a.nerBreakdown = {
                "SRS": int(ner_res.breakdown.SRS),
                "CIS": int(ner_res.breakdown.CIS),
                "CSC": int(ner_res.breakdown.CSC),
                "TRF": int(ner_res.breakdown.TRF),
                "ECM": float(ner_res.breakdown.ECM),
                "peer_titles": peers,
                "corroborators": len(peers),
            }

            # Persist snapshot
            save_snapshot(  # type: ignore[misc]
                article_id=article_id,
                feed_url=feed_url,
                published_ts=published,
                ner=ner_res,
            )

        except Exception as e:
            logger.warning("NER compute/persist failed for %s: %s", article_id, e)
            a.ecosystemRating = None
            a.nerVersion = "ner_v1.0"
            a.nerBreakdown = {**_base_breakdown(), "error": True}

        articles.append(a)

    # ------------------------------------------------------------
    # 5) Sort + cache
    # ------------------------------------------------------------
    result = sorted(articles, key=lambda x: -_epoch(x.timestamp))
    _NEWS_CACHE[category] = {"ts": now, "data": result}
    return result


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
    try:
        supabase_url_set = bool(os.getenv("SUPABASE_URL"))
        supabase_service_role_set = bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
        logger.info(
            "ENV: SUPABASE_URL set=%s | SUPABASE_SERVICE_ROLE_KEY set=%s",
            supabase_url_set,
            supabase_service_role_set,
        )
    except Exception:
        pass


@app.on_event("shutdown")
def shutdown_event():
    logger.info("NOVARIC Backend stopped.")


# ================================================================
# ENTRYPOINT (CLOUD RUN COMPATIBLE)
# ================================================================
if __name__ == "__main__":
    try:
        import uvicorn  # type: ignore

        port = int(os.getenv("PORT", "8080"))
        logger.info("Starting uvicorn | host=0.0.0.0 | port=%s", port)

        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
        )
    except Exception as e:
        logger.exception("Failed to start server: %s", e)
        raise
