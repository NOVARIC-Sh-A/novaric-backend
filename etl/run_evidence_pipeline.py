# etl/run_evidence_pipeline.py
from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from utils.supabase_client import supabase_insert
from etl.evidence.contracts import EvidenceItem
from etl.evidence.politician_matcher import match_politician_id
from etl.evidence.evidence_writer import write_evidence_batch

from config.rss_feeds import get_feeds_for_news_category
import feedparser

def start_run(source_key: str) -> int:
    row = {
        "source_key": source_key,
        "status": "running",
    }
    res = supabase_insert("scrape_runs", [row])
    # Supabase returns inserted row(s)
    return int(res[0]["id"])

def end_run(run_id: int, *, status: str, items_fetched: int, items_extracted: int, error: Optional[str] = None) -> None:
    # Use REST patch via existing helper if you want; simplest is insert-only logs + skip update.
    # If you want update: add a small helper in utils/supabase_client.py to patch by id.
    pass

def rss_pull(category: str, per_feed: int = 5) -> List[Dict[str, Any]]:
    feeds = get_feeds_for_news_category(category)
    out: List[Dict[str, Any]] = []
    for feed_url in feeds:
        parsed = feedparser.parse(feed_url)
        for e in (getattr(parsed, "entries", []) or [])[:per_feed]:
            out.append({
                "url": str(e.get("link") or ""),
                "title": str(e.get("title") or ""),
                "summary": str(e.get("summary") or ""),
                "published": str(e.get("published") or ""),
                "feed_url": feed_url,
            })
    return out

def to_evidence(items: List[Dict[str, Any]], source_key: str) -> List[EvidenceItem]:
    evidence: List[EvidenceItem] = []
    for it in items:
        title = (it.get("title") or "").strip()
        summary = (it.get("summary") or "").strip()
        url = (it.get("url") or "").strip()
        published = (it.get("published") or "").strip() or None

        text_for_match = f"{title}\n{summary}"
        pid = match_politician_id(text_for_match)

        ev = EvidenceItem(
            source_key=source_key,
            url=url,
            title=title,
            published_at=None,          # keep null until you standardize parsing
            content_type="article",
            snippet=summary[:600],
            raw_text=summary[:2000],
            entities={"feed_url": it.get("feed_url")},
            topics=[],
            signals={},
            extraction_confidence=0.6,
            politician_id=pid,
        )
        evidence.append(ev)
    return evidence

def run(category: str, per_feed: int) -> None:
    source_key = "rss_albanian_media"
    run_id = start_run(source_key)

    items = rss_pull(category=category, per_feed=per_feed)
    evidence = to_evidence(items, source_key=source_key)

    inserted = write_evidence_batch(evidence, run_id=run_id, batch_size=200)
    print(f"[run_evidence_pipeline] fetched={len(items)} evidence_written={inserted}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--category", default="all")
    p.add_argument("--per-feed", type=int, default=5)
    args = p.parse_args()
    run(category=args.category, per_feed=args.per_feed)
