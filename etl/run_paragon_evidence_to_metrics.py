# etl/run_paragon_evidence_to_metrics.py
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List

from utils.supabase_client import _get, supabase_upsert


# =============================================================================
# Configuration (v1 heuristic rules)
# =============================================================================

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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _count_hit(text: str, keywords: Iterable[str]) -> int:
    t = (text or "").lower()
    return 1 if any(k in t for k in keywords) else 0


def _sentiment_unit(text: str) -> int:
    """
    v1 sentiment per evidence item:
      +1 if any positive keywords
      -1 if any negative keywords
       0 otherwise

    NOTE: paragon_metrics.sentiment_score is integer, but scoring_engine expects -1..1 range.
    We'll aggregate and then clamp to -1..1 at the end.
    """
    t = (text or "").lower()
    score = 0
    if any(k in t for k in KW_POSITIVE):
        score += 1
    if any(k in t for k in KW_NEGATIVE):
        score -= 1
    if score > 0:
        return 1
    if score < 0:
        return -1
    return 0


def _text_blob(row: Dict[str, Any]) -> str:
    title = str(row.get("title") or "")
    snippet = str(row.get("snippet") or "")
    raw_text = str(row.get("raw_text") or "")
    return f"{title}\n{snippet}\n{raw_text}".strip()


# =============================================================================
# Evidence fetch
# =============================================================================

def _fetch_evidence_since(days: int) -> List[Dict[str, Any]]:
    since = _utc_now() - timedelta(days=int(max(1, days)))
    since_iso = _iso(since)

    return _get(
        "evidence_items",
        {
            "select": "politician_id,title,snippet,raw_text,source_key,url,fetched_at,published_at",
            "politician_id": "not.is.null",
            "fetched_at": f"gte.{since_iso}",
            "order": "fetched_at.desc",
            "limit": "5000",
        },
    )


# =============================================================================
# Aggregation
# =============================================================================

@dataclass
class Agg:
    politician_id: int
    mentions: int = 0
    pos_events: int = 0
    neg_events: int = 0
    scandals: int = 0
    intl: int = 0
    sent_sum: int = 0


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
        agg.scandals += _count_hit(text, KW_SCANDAL)
        agg.intl += _count_hit(text, KW_INTL)

        s = _sentiment_unit(text)
        agg.sent_sum += s
        if s > 0:
            agg.pos_events += 1
        elif s < 0:
            agg.neg_events += 1

    return out


# =============================================================================
# Scaling into scoring_engine expected ranges
# =============================================================================

def _scale_to_month(value: int, days: int) -> int:
    """
    Convert counts observed in `days` window into a 30-day estimate.
    """
    d = max(1, int(days))
    return int(round((int(value) * 30.0) / d))


def _clamp_int(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, int(value)))


def _sentiment_clamped(sent_sum: int) -> int:
    """
    scoring_engine expects sentiment_score in [-1, 1].
    Convert aggregate sentiment into sign.
    """
    if sent_sum > 0:
        return 1
    if sent_sum < 0:
        return -1
    return 0


def _to_metrics_row(a: Agg, *, days: int) -> Dict[str, Any]:
    now = _iso(_utc_now())

    # Project into the same “units” as scoring_engine ranges
    mentions_monthly = _scale_to_month(a.mentions, days)
    intl_monthly = _scale_to_month(a.intl, days)
    scandals_monthly = _scale_to_month(a.scandals, days)
    pos_monthly = _scale_to_month(a.pos_events, days)
    neg_monthly = _scale_to_month(a.neg_events, days)

    # Conservative caps to match scoring ranges (and keep stable)
    mentions_monthly = _clamp_int(mentions_monthly, 0, 2000)
    intl_monthly = _clamp_int(intl_monthly, 0, 30)
    scandals_monthly = _clamp_int(scandals_monthly, 0, 10)

    return {
        "politician_id": a.politician_id,
        "media_mentions_monthly": mentions_monthly,
        "media_positive_events": pos_monthly,
        "media_negative_events": neg_monthly,
        "scandals_flagged": scandals_monthly,
        "international_meetings": intl_monthly,
        "sentiment_score": _sentiment_clamped(a.sent_sum),
        "updated_at": now,
        # Leave other columns untouched:
        # wealth_declaration_issues, public_projects_completed, parliamentary_attendance,
        # party_control_index, legislative_initiatives, independence_index
    }


# =============================================================================
# Runner
# =============================================================================

def run(*, days: int = 7, batch_size: int = 200) -> None:
    rows = _fetch_evidence_since(days=days)
    if not rows:
        print("[run_paragon_evidence_to_metrics] No evidence rows found in window.")
        return

    grouped = _aggregate(rows)
    if not grouped:
        print("[run_paragon_evidence_to_metrics] No politician-linked evidence in window.")
        return

    metric_rows = [_to_metrics_row(a, days=days) for a in grouped.values()]

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
