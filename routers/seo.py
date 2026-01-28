from fastapi import APIRouter, Response
from utils.supabase_client import supabase
from feedgen.feed import FeedGenerator
from datetime import datetime, timezone

router = APIRouter(tags=["SEO"])

def _iso(dt_str: str | None) -> str:
    if not dt_str:
        return datetime.now(timezone.utc).isoformat()
    return dt_str

@router.get("/sitemap.xml")
def sitemap():
    # NOTE: Replace BASE with your real public domain later
    BASE = "https://YOUR_PUBLIC_DOMAIN"

    urls = []

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
        urls.append({
            "loc": f"{BASE}/fake-news/{row['id']}",
            "lastmod": _iso(row.get("updated_at") or row.get("audited_at")),
        })

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
        urls.append({
            "loc": f"{BASE}/verified/{row['slug']}",
            "lastmod": _iso(row.get("updated_at") or row.get("published_at")),
        })

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append("<url>")
        xml.append(f"<loc>{u['loc']}</loc>")
        xml.append(f"<lastmod>{u['lastmod']}</lastmod>")
        xml.append("</url>")
    xml.append("</urlset>")

    return Response("\n".join(xml), media_type="application/xml")


@router.get("/rss.xml")
def rss():
    BASE = "https://YOUR_PUBLIC_DOMAIN"

    fg = FeedGenerator()
    fg.title("NOVARIC® Verified Updates")
    fg.link(href=f"{BASE}/", rel="alternate")
    fg.link(href=f"{BASE}/rss.xml", rel="self")
    fg.description("Verified updates, methodology notes, and audited case studies.")
    fg.language("sq")

    # Pull latest 50 verified responses
    vr = (
        supabase.table("verified_responses")
        .select("title,slug,summary,published_at")
        .eq("is_published", True)
        .order("published_at", desc=True)
        .limit(50)
        .execute()
    )

    for row in (vr.data or []):
        fe = fg.add_entry()
        fe.title(row["title"])
        fe.link(href=f"{BASE}/verified/{row['slug']}")
        fe.description(row.get("summary") or "")
        fe.pubDate(row.get("published_at") or datetime.now(timezone.utc).isoformat())

    rss_str = fg.rss_str(pretty=True)
    return Response(rss_str, media_type="application/rss+xml")
