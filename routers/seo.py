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

    return str(request.base_url).rstrip("/")


def _supabase_available() -> bool:
    return bool(is_supabase_configured() and supabase is not None)


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(request: Request):
    base = _base_url(request)

    # Always return valid XML (even if Supabase is down)
    urls: list[dict[str, str]] = []

    if _supabase_available():
        # Case studies
        cs = (
            supabase.table("case_studies")
            .select("id,updated_at,audited_at")
            .eq("is_published", True)
            .order("audited_at", desc=True)
            .limit(5000)
            .execute()
        )

        for row in (getattr(cs, "data", None) or []):
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

        for row in (getattr(vr, "data", None) or []):
            loc = f"{base}/verified/{row['slug']}"
            lastmod = _iso(row.get("updated_at") or row.get("published_at"))
            urls.append({"loc": loc, "lastmod": lastmod})

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
    base = _base_url(request)

    fg = FeedGenerator()
    fg.id(f"{base}/rss.xml")
    fg.title("NOVARIC® Verified Updates")
    fg.link(href=f"{base}/", rel="alternate")
    fg.link(href=f"{base}/rss.xml", rel="self")
    fg.description("Verified updates, methodology notes, and audited case studies.")
    fg.language("sq")

    # Always return valid RSS (even if Supabase is down)
    if _supabase_available():
        vr = (
            supabase.table("verified_responses")
            .select("title,slug,summary,published_at,updated_at")
            .eq("is_published", True)
            .order("published_at", desc=True)
            .limit(50)
            .execute()
        )

        for row in (getattr(vr, "data", None) or []):
            slug = row.get("slug") or ""
            title = row.get("title") or "Verified Update"
            summary = row.get("summary") or ""

            raw_dt = row.get("published_at") or row.get("updated_at")
            try:
                dt = datetime.fromisoformat(str(raw_dt).replace("Z", "+00:00")) if raw_dt else datetime.now(timezone.utc)
            except Exception:
                dt = datetime.now(timezone.utc)

            fe = fg.add_entry()
            fe.id(f"{base}/verified/{slug}")
            fe.title(title)
            fe.link(href=f"{base}/verified/{slug}")
            fe.description(summary)
            fe.pubDate(dt)

    return Response(fg.rss_str(pretty=True), media_type="application/rss+xml")
