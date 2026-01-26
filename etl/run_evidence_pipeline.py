# etl/run_evidence_pipeline.py
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

import feedparser

from config.rss_feeds import get_feeds_for_news_category
from etl.evidence.contracts import EvidenceItem
from etl.evidence.evidence_writer import write_evidence_batch
from etl.evidence.politician_matcher import match_politician_id
from utils.supabase_client import supabase_insert, supabase_upsert


DEFAULT_SOURCE_KEY = "rss_albanian_media"


# ---------------------------------------------------------------------
# Time parsing helpers
# ---------------------------------------------------------------------
def _to_iso_datetime(value: Optional[str]) -> Optional[str]:
    """
    Best-effort parse RSS published date into ISO8601 (UTC).
    Returns None if parsing fails.
    """
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


# ---------------------------------------------------------------------
# Source registry bootstrap (FK safety)
# ---------------------------------------------------------------------
def ensure_source_registry(source_key: str) -> None:
    """
    Ensures source_registry has a row for source_key.
    Idempotent. Prevents FK failures when inserting scrape_runs.
    """
    row = {
        "key": source_key,
        "name": "Albanian Media RSS (configured)",
        "base_url": "multiple (see backend config/rss_feeds.py)",
        "trust_tier": 2,
        "scrape_method": "rss",
        "enabled": True,
        "refresh_minutes": 60,
        "notes": "Ingests from config/rss_feeds.py via etl/run_evidence_pipeline.py",
    }
    supabase_upsert("source_registry", [row], conflict_col="key")


# ---------------------------------------------------------------------
# scrape_runs lifecycle
# ---------------------------------------------------------------------
def start_run(source_key: str) -> Tuple[int, str, str]:
    """
    Creates a scrape_runs record (status=running) and returns:
      (run_id, source_key, started_at_iso)
    """
    ensure_source_registry(source_key)

    started_at = datetime.now(timezone.utc).isoformat()
    row = {
        "source_key": source_key,
        "status": "running",
        "started_at": started_at,
    }
    res = supabase_insert("scrape_runs", [row])
    run_id = int(res[0]["id"])
    return run_id, source_key, started_at


def end_run(
    run_id: int,
    *,
    source_key: str,
    started_at: str,
    status: str,
    items_fetched: int,
    items_extracted: int,
    error: Optional[str] = None,
) -> None:
    """
    Finalizes scrape_runs.

    IMPORTANT:
    - We use UPSERT on id.
    - Because source_key is NOT NULL, it MUST be included in the payload even during upsert,
      otherwise Postgres can fail BEFORE applying ON CONFLICT.
    """
    row: Dict[str, Any] = {
        "id": int(run_id),
        "source_key": source_key,  # REQUIRED (NOT NULL)
        "started_at": started_at,  # keep stable (optional but consistent)
        "status": status,
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "items_fetched": int(items_fetched),
        "items_extracted": int(items_extracted),
    }
    if error:
        row["error"] = str(error)[:2000]

    supabase_upsert("scrape_runs", [row], conflict_col="id")


# ---------------------------------------------------------------------
# RSS pull
# ---------------------------------------------------------------------
def rss_pull(category: str, per_feed: int = 5) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Pulls up to per_feed entries from each feed for a given category.
    Returns (items, errors).
    """
    feeds = get_feeds_for_news_category(category)
    out: List[Dict[str, Any]] = []
    errors: List[str] = []

    per_feed = max(1, min(10, int(per_feed)))

    for feed_url in feeds:
        try:
            parsed = feedparser.parse(feed_url)
            entries = getattr(parsed, "entries", []) or []
            if not entries:
                continue

            for e in entries[:per_feed]:
                out.append(
                    {
                        "url": str(e.get("link") or ""),
                        "title": str(e.get("title") or ""),
                        "summary": str(e.get("summary") or ""),
                        "published": str(e.get("published") or ""),
                        "feed_url": feed_url,
                    }
                )
        except Exception as ex:
            errors.append(f"{feed_url} :: {ex}")

    return out, errors


# ---------------------------------------------------------------------
# Transform -> EvidenceItem
# ---------------------------------------------------------------------
def to_evidence(items: List[Dict[str, Any]], source_key: str) -> List[EvidenceItem]:
    evidence: List[EvidenceItem] = []

    for it in items:
        url = (it.get("url") or "").strip()
        if not url:
            continue

        title = (it.get("title") or "").strip()
        summary = (it.get("summary") or "").strip()
        published_raw = (it.get("published") or "").strip()
        published_at = _to_iso_datetime(published_raw)

        text_for_match = f"{title}\n{summary}"
        pid = match_politician_id(text_for_match)

        ev = EvidenceItem(
            source_key=source_key,
            url=url,
            title=title,
            published_at=published_at,
            content_type="article",
            language="sq",
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


# ---------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------
def run(*, category: str, per_feed: int, source_key: str = DEFAULT_SOURCE_KEY) -> None:
    run_id, sk, started_at = start_run(source_key)

    fetched = 0
    extracted = 0
    status = "success"
    err_msg: Optional[str] = None

    try:
        items, errors = rss_pull(category=category, per_feed=per_feed)
        fetched = len(items)

        evidence = to_evidence(items, source_key=sk)
        extracted = len(evidence)

        written = write_evidence_batch(evidence, run_id=run_id, batch_size=200)
        matched = sum(1 for ev in evidence if ev.politician_id is not None)

        if errors:
            # Soft-fail: record truncated error context but keep status success
            err_msg = " | ".join(errors[:5])

        print(
            f"[run_evidence_pipeline] run_id={run_id} fetched={fetched} extracted={extracted} "
            f"matched_politicians={matched} evidence_written={written}"
        )

    except Exception as e:
        status = "failed"
        err_msg = str(e)
        print(f"[run_evidence_pipeline] run_id={run_id} FAILED: {e}")
        raise

    finally:
        try:
            end_run(
                run_id,
                source_key=sk,
                started_at=started_at,
                status=status,
                items_fetched=fetched,
                items_extracted=extracted,
                error=err_msg,
            )
        except Exception as e2:
            print(f"[run_evidence_pipeline] run_id={run_id} WARN: failed to finalize scrape_runs: {e2}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run evidence ingestion from RSS feeds into Supabase.")
    p.add_argument("--category", default="all", help="News category (must match config/rss_feeds.py).")
    p.add_argument("--per-feed", type=int, default=5, help="Max entries per feed (1..10).")
    p.add_argument("--source-key", default=DEFAULT_SOURCE_KEY, help="source_registry.key value.")
    args = p.parse_args()

    run(category=args.category, per_feed=args.per_feed, source_key=args.source_key)
