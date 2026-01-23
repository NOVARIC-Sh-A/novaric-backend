# services/ner_repository.py

from __future__ import annotations

from typing import Optional

from services.ner_config import NerResult, NerBreakdown
from utils.supabase_client import supabase, is_supabase_configured, supabase_upsert


# ============================================================
# READ: Fetch latest stored NER snapshot for an article
# ============================================================
def get_snapshot(article_id: str) -> Optional[NerResult]:
    """
    Returns the most recent stored NER snapshot for an article,
    or None if not found or Supabase is unavailable.
    """

    if not supabase or not is_supabase_configured():
        # Supabase not configured → skip silently
        return None

    try:
        res = (
            supabase
            .table("ner_snapshots")
            .select("*")
            .eq("article_id", article_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception:
        # Never break caller (news pipeline safety)
        return None

    if not res or not res.data:
        return None

    row = res.data[0]

    try:
        return NerResult(
            ecosystemRating=int(row["ecosystem_rating"]),
            nerVersion=str(row.get("ner_version") or "ner_v1.0"),
            breakdown=NerBreakdown(
                SRS=int(row["srs"]),
                CIS=int(row["cis"]),
                CSC=int(row["csc"]),
                TRF=int(row["trf"]),
                ECM=float(row["ecm"]),
            ),
        )
    except Exception:
        # Malformed row → treat as missing
        return None


# ============================================================
# WRITE: Persist a NER snapshot (idempotent by article_id)
# ============================================================
def save_snapshot(
    article_id: str,
    feed_url: str,
    published_ts: str,
    ner: NerResult,
) -> None:
    """
    Persists a NER snapshot to Supabase.

    Design rules:
    - Best-effort only (no exceptions raised)
    - Uses service-role key when available
    - Never blocks the news ingestion pipeline
    """

    if not supabase or not is_supabase_configured():
        return

    try:
        supabase_upsert(
            table="ner_snapshots",
            records=[
                {
                    "article_id": article_id,
                    "feed_url": feed_url,
                    "published_ts": published_ts,
                    "ecosystem_rating": ner.ecosystemRating,
                    "ner_version": ner.nerVersion,
                    "srs": ner.breakdown.SRS,
                    "cis": ner.breakdown.CIS,
                    "csc": ner.breakdown.CSC,
                    "trf": ner.breakdown.TRF,
                    "ecm": ner.breakdown.ECM,
                }
            ],
            conflict_col="article_id",
        )
    except Exception:
        # Intentionally swallowed: storage must never block NER
        return
