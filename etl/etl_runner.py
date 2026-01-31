# etl/etl_runner.py
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from etl.crawlers.media_crawler import MediaCrawler
from etl.transformer import build_signals
from etl.scoring_engine import build_paragon_scores_from_signals
from utils.supabase_client import supabase_upsert, supabase_insert, fetch_table


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# TREND ENGINE — Writes historical score snapshots
# Table: paragon_trends
#   id BIGSERIAL PK
#   politician_id INTEGER FK
#   previous_score INTEGER
#   new_score INTEGER
#   delta INTEGER
#   calculated_at timestamptz
#   raw_snapshot jsonb
# ============================================================
def write_trend_history(paragon_records: List[Dict[str, Any]]) -> None:
    if not paragon_records:
        print("[Trend] No records to log.")
        return

    # --------------------------------------------------------
    # 1) Fetch PREVIOUS paragon_scores from Supabase
    # --------------------------------------------------------
    previous_map: Dict[int, int] = {}
    try:
        previous_rows = fetch_table("paragon_scores", select="politician_id, overall_score")
        for row in previous_rows or []:
            try:
                pid = int(row["politician_id"])
                score = int(row["overall_score"])
                previous_map[pid] = score
            except Exception:
                continue
    except Exception as e:
        print(f"[Trend] ⚠ Could not fetch previous scores: {e}")

    # --------------------------------------------------------
    # 2) Build history entries
    # --------------------------------------------------------
    now_iso = _utc_now_iso()
    history_rows: List[Dict[str, Any]] = []

    for r in paragon_records:
        try:
            pid = int(r["politician_id"])
            new_score = int(r["overall_score"])
        except Exception:
            # Skip malformed record
            continue

        previous_score: Optional[int] = previous_map.get(pid)
        delta: Optional[int] = (new_score - previous_score) if previous_score is not None else None

        history_rows.append(
            {
                "politician_id": pid,
                "previous_score": previous_score,
                "new_score": new_score,
                "delta": delta,
                "raw_snapshot": r,          # full JSON snapshot
                "calculated_at": now_iso,   # ✅ DO NOT use "now()"
            }
        )

    if not history_rows:
        print("[Trend] No valid history rows produced.")
        return

    # --------------------------------------------------------
    # 3) INSERT — always add new rows (no upsert)
    # --------------------------------------------------------
    try:
        supabase_insert("paragon_trends", history_rows)
        print(f"[Trend] ✅ Inserted {len(history_rows)} trend rows.")
    except Exception as e:
        print(f"[Trend] ❌ Insert failed: {e}")


# ============================================================
# MAIN ETL PIPELINE
# ============================================================
async def run_etl() -> None:
    print("============== NOVARIC® PARAGON ETL ==============")

    # ----------------------------------------------------
    # 1) CRAWL MEDIA
    # ----------------------------------------------------
    crawler = MediaCrawler()
    scraped_items: List[Dict[str, Any]] = await crawler.run()
    print(f"[ETL] Scraped {len(scraped_items)} raw items")

    if not scraped_items:
        print("[ETL] No items scraped – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 2) BUILD NORMALIZED SIGNALS
    # ----------------------------------------------------
    signals = build_signals(scraped_items)
    print(f"[ETL] Matched signals for {len(signals)} politicians")

    if not signals:
        print("[ETL] No signals matched to any politician.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 3) SCORING ENGINE
    # ----------------------------------------------------
    paragon_records = build_paragon_scores_from_signals(signals)

    if not paragon_records:
        print("[ETL] No DB records built – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 4) UPSERT LIVE SCORES
    # ----------------------------------------------------
    print("[ETL] Uploading normalized PARAGON scores to Supabase…")

    try:
        supabase_upsert(
            table="paragon_scores",
            records=paragon_records,
            conflict_col="politician_id",
        )
        print(f"[ETL] ✅ Upserted {len(paragon_records)} live score records.")
    except Exception as e:
        print(f"[ETL] ❌ Supabase upsert failed: {e}")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 5) TREND ENGINE
    # ----------------------------------------------------
    print("[ETL] Writing trend history snapshot…")
    write_trend_history(paragon_records)

    print("============== ETL FINISHED ==============")


# ------------------------------------------------------------
# CLI entrypoint (optional; safe to keep)
# ------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(run_etl())
