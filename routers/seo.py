from __future__ import annotations

from datetime import datetime, timezone
from html import escape as xml_escape
from typing import Optional

from fastapi import APIRouter, Request, Response
from feedgen.feed import FeedGenerator

from utils.supabase_client import supabase, is_supabase_configured

router = APIRouter(tags=["SEO"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(dt_str: Optional[str]) -> str:
    return dt_str or _now_iso()


def _parse_dt(dt_str: Optional[str]) -> datetime:
    """
    Parse ISO timestamps safely; always return a timezone-aware UTC datetime.
    FeedGenerator prefers datetime objects for pubDate.
    """
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        # Handles "Z" suffix
        return datetime.fromisoformat(str(dt_str).replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _base_url(request: Request) -> str:
    """
    Priority:
      1) PUBLIC_BASE_URL env (recommended for production)
      2) derive from Request base_url
    Always returns WITHOUT trailing slash.
    """
    import os

    base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return base

    # Derive from request (works behind most proxies if forwarded headers are configured)
    return str(request.base_url).rstrip("/")


def _supabase_ready() -> bool:
    """
    True only when Supabase is configured and client is initialized.
    """
    return bool(is_supabase_configured() and supabase is not None)


def _empty_sitemap() -> Response:
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        "</urlset>",
    ]
    return Response("\n".join(xml), media_type="application/xml")


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(request: Request):
    """
    Always returns valid XML (never 503).
    If Supabase is not ready or queries fail, returns an empty sitemap rather than an error.
    """
    base = _base_url(request)

    if not _supabase_ready():
        return _empty_sitemap()

    urls: list[dict[str, str]] = []

    try:
        # Case studies
        cs = (
            supabase.table("case_studies")
            .select("id,updated_at,audited_at")
            .eq("is_published", True)
            .order("audited_at", desc=True)
            .limit(5000)
            .execute()
        )
        for row in (cs.data or []):
            if not isinstance(row, dict) or not row.get("id"):
                continue
            loc = f"{base}/fake-news/{row['id']}"
            lastmod = _iso(row.get("updated_at") or row.get("audited_at"))
            urls.append({"loc": loc, "lastmod": lastmod})

        # Verified responses
        vr = (
            supabase.table("verified_responses")
            .select("slug,updated_at,published_at")
            .eq("is_published", True)
            .order("published_at", desc=True)
            .limit(5000)
            .execute()
        )
        for row in (vr.data or []):
            if not isinstance(row, dict) or not row.get("slug"):
                continue
            loc = f"{base}/verified/{row['slug']}"
            lastmod = _iso(row.get("updated_at") or row.get("published_at"))
            urls.append({"loc": loc, "lastmod": lastmod})
    except Exception:
        # Crawler-safe fallback: empty sitemap
        return _empty_sitemap()

    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        xml.append("<url>")
        xml.append(f"<loc>{xml_escape(u['loc'])}</loc>")
        xml.append(f"<lastmod>{xml_escape(u['lastmod'])}</lastmod>")
        xml.append("</url>")
    xml.append("</urlset>")

    return Response("\n".join(xml), media_type="application/xml")


@router.get("/rss.xml", include_in_schema=False)
def rss(request: Request):
    """
    Always returns valid RSS (never 503).
    If Supabase is not ready or queries fail, returns a valid empty feed shell.
    """
    base = _base_url(request)

    fg = FeedGenerator()
    fg.id(f"{base}/rss.xml")
    fg.title("NOVARIC® Verified Updates")
    fg.link(href=f"{base}/", rel="alternate")
    fg.link(href=f"{base}/rss.xml", rel="self")
    fg.description("Verified updates, methodology notes, and audited case studies.")
    fg.language("sq")

    if not _supabase_ready():
        return Response(fg.rss_str(pretty=True), media_type="application/rss+xml")

    try:
        vr = (
            supabase.table("verified_responses")
            .select("title,slug,summary,published_at,updated_at")
            .eq("is_published", True)
            .order("published_at", desc=True)
            .limit(50)
            .execute()
        )

        for row in (vr.data or []):
            if not isinstance(row, dict):
                continue

            slug = (row.get("slug") or "").strip()
            if not slug:
                continue

            title = (row.get("title") or "Verified Update").strip()
            summary = row.get("summary") or ""

            raw_dt = row.get("published_at") or row.get("updated_at")
            dt = _parse_dt(str(raw_dt) if raw_dt else None)

            fe = fg.add_entry()
            fe.id(f"{base}/verified/{slug}")
            fe.title(title)
            fe.link(href=f"{base}/verified/{slug}")
            fe.description(summary)
            fe.pubDate(dt)

    except Exception:
        # Return valid feed shell even if Supabase errors out
        return Response(fg.rss_str(pretty=True), media_type="application/rss+xml")

    return Response(fg.rss_str(pretty=True), media_type="application/rss+xml")
