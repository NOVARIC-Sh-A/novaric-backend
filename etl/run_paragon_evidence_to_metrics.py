# etl/run_paragon_evidence_to_metrics.py
from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from utils.supabase_client import _get, supabase_upsert


# =============================================================================
# Configuration (v1 heuristic rules)
# =============================================================================

# Albanian + English keywords (conservative). You can expand over time.
KW_SCANDAL = (
    "skandal", "skandali", "afera", "korrupsion", "korrupsioni", "abuzim", "shpërdorim",
    "akuz", "akuzë", "akuzat", "nën hetim", "hetim", "prokurori", "spak", "gjykat",
    "arrest", "pranga", "dën", "denim",
    "corruption", "scandal", "investigation", "prosecutor", "trial", "arrest",
)

KW_POSITIVE = (
    "sukses", "arrin", "përfundon", "përfunduar", "investim", "investime", "hap", "inaugur",
    "marrëveshje", "marrveshje", "mbështet", "miraton", "fiton", "rritje", "progres",
    "success", "approved", "agreement", "supports", "growth", "progress",
)

KW_NEGATIVE = (
    "kritik", "kritika", "dështon", "dështim", "protest", "protesta", "tension",
    "dorëheq", "dorëheqje", "akuz", "skandal", "afer",
    "critic", "fails", "failure", "protest", "resign", "resignation", "accus",
)

KW_INTL = (
    "bashkimi europian", "be", "eu", "bruksel", "brussels", "komisioni europian",
    "nato", "okb", "un", "kombet e bashkuara",
    "samiti", "summit", "delegacion", "takim", "meeting", "vizit", "visit",
)

# Very lightweight sentiment: +1 if positive keyword hit, -1 if negative keyword hit.
# We clamp to int range in the end.
def _sentiment_from_text(text: str) -> int:
    t = (text or "").lower()
    score = 0
    if any(k in t for k in KW_POSITIVE):
        score += 1
    if any(k in t for k in KW_NEGATIVE):
        score -= 1
    return score


def _count_hits(text: str, keywords: Iterable[str]) -> int:
    t = (text or "").lower()
    return 1 if any(k in t for k in keywords) else 0


# =============================================================================
# Date parsing (RSS "published_at" might be timestamptz already; we filter by fetched_at)
# =============================================================================

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


# =============================================================================
# Evidence fetch
# =============================================================================

def _fetch_evidence_since(days: int) -> List[Dict[str, Any]]:
    """
    Pull evidence_items in a safe way.
    We filter by fetched_at >= now - days (PostgREST filter).
    Also requires politician_id not null.
    """
    since = _utc_now() - timedelta(days=int(max(1, days)))
    # PostgREST expects timestamps in ISO; using UTC.
    since_iso = _iso(since)

    return _get(
        "evidence_items",
        {
            "select": "politician_id,title,snippet,raw_text,source_key,url,fetched_at,published_at",
            "politician_id": "not.is.null",
            "fetched_at": f"gte.{since_iso}",
            "order": "fetched_at.desc",
            "limit": "5000",  # safety cap; adjust if you ingest more
        },
    )


# =============================================================================
# Metric aggregation
# =============================================================================

@dataclass
class Agg:
    politician_id: int
    mentions: int = 0
    pos_events: int = 0
    neg_events: int = 0
    scandals: int = 0
    intl_meetings: int = 0
    sentiment: int = 0


def _text_blob(row: Dict[str, Any]) -> str:
    title = str(row.get("title") or "")
    snippet = str(row.get("snippet") or "")
    raw_text = str(row.get("raw_text") or "")
    return f"{title}\n{snippet}\n{raw_text}".strip()


def _aggregate(rows: List[Dict[str, Any]]) -> Dict[int, Agg]:
    out: Dict[int, Agg] = {}

    for r in rows:
        pid = r.get("politician_id")
        if pid is None:
            continue
        try:
            pid_i = int(pid)
        except Exception:
            continue

        agg = out.get(pid_i)
        if agg is None:
            agg = Agg(politician_id=pid_i)
            out[pid_i] = agg

        agg.mentions += 1

        text = _text_blob(r)

        agg.scandals += _count_hits(text, KW_SCANDAL)
        agg.intl_meetings += _count_hits(text, KW_INTL)

        s = _sentiment_from_text(text)
        agg.sentiment += int(s)

        if s > 0:
            agg.pos_events += 1
        elif s < 0:
            agg.neg_events += 1

    return out


# =============================================================================
# Build DB rows for paragon_metrics (schema-aligned)
# =============================================================================

def _to_metrics_row(a: Agg) -> Dict[str, Any]:
    """
    IMPORTANT: Column names MUST match Supabase public.paragon_metrics:
      politician_id (PK)
      scandals_flagged
      wealth_declaration_issues
      public_projects_completed
      parliamentary_attendance
      international_meetings
      party_control_index
      media_mentions_monthly
      legislative_initiatives
      independence_index
      media_positive_events
      media_negative_events
      updated_at
      sentiment_score
    """
    now = _iso(_utc_now())

    # v1: We only fill media-driven fields + sentiment + intl/scandals.
    # Leave the rest as-is (DB defaults remain, or prior values remain).
    return {
        "politician_id": a.politician_id,
        "media_mentions_monthly": int(a.mentions),
        "media_positive_events": int(a.pos_events),
        "media_negative_events": int(a.neg_events),
        "scandals_flagged": int(a.scandals),
        "international_meetings": int(a.intl_meetings),
        "sentiment_score": int(a.sentiment),
        "updated_at": now,
        # Leave the following untouched (not included) OR explicitly set if you want:
        # wealth_declaration_issues
        # public_projects_completed
        # parliamentary_attendance
        # party_control_index
        # legislative_initiatives
        # independence_index
    }


def run(*, days: int = 7, batch_size: int = 200) -> None:
    rows = _fetch_evidence_since(days=days)

    if not rows:
        print("[run_paragon_evidence_to_metrics] No evidence rows found in window.")
        return

    grouped = _aggregate(rows)
    if not grouped:
        print("[run_paragon_evidence_to_metrics] No politician-linked evidence in window.")
        return

    metric_rows = [_to_metrics_row(a) for a in grouped.values()]

    total = 0
    for i in range(0, len(metric_rows), batch_size):
        batch = metric_rows[i : i + batch_size]
        supabase_upsert("paragon_metrics", batch, conflict_col="politician_id")
        total += len(batch)

    print(
        "[run_paragon_evidence_to_metrics] "
        f"window_days={days} evidence_rows={len(rows)} politicians_updated={len(metric_rows)} upserted={total}"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Aggregate evidence_items into paragon_metrics.")
    p.add_argument("--days", type=int, default=7, help="Lookback window in days (by fetched_at).")
    p.add_argument("--batch-size", type=int, default=200, help="Upsert batch size.")
    args = p.parse_args()

    run(days=args.days, batch_size=args.batch_size)
