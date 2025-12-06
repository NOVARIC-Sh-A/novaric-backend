# etl/etl_runner.py

import asyncio
from typing import List, Dict, Any

from etl.crawlers.media_crawler import MediaCrawler
from etl.transformer import build_signals
from etl.scoring_engine import build_paragon_scores_from_signals
from utils.supabase_client import (
    supabase_upsert,
    supabase_insert,
    fetch_table
)


# ============================================================
# TREND ENGINE — Writes historical score snapshots
# Matches your real Supabase schema:
#
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
    try:
        previous_rows = fetch_table(
            "paragon_scores",
            select="politician_id, overall_score"
        )
        previous_map = {
            row["politician_id"]: row["overall_score"]
            for row in previous_rows
        }
    except Exception as e:
        print("⚠ Could not fetch previous scores:", e)
        previous_map = {}

    # --------------------------------------------------------
    # 2) Build history entries
    # --------------------------------------------------------
    history_rows = []

    for r in paragon_records:
        pid = r["politician_id"]
        new_score = r["overall_score"]
        previous_score = previous_map.get(pid)

        delta = None
        if previous_score is not None:
            delta = new_score - previous_score

        history_rows.append(
            {
                "politician_id": pid,
                "previous_score": previous_score,
                "new_score": new_score,
                "delta": delta,
                "raw_snapshot": r,     # full JSON snapshot
                "calculated_at": "now()",
            }
        )

    # --------------------------------------------------------
    # 3) INSERT — always add new rows (no upsert)
    # --------------------------------------------------------
    try:
        supabase_insert("paragon_trends", history_rows)
        print(f"[Trend] Inserted {len(history_rows)} trend rows.")
    except Exception as e:
        print("❌ Trend insert failed:", e)


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
            conflict_col="politician_id"
        )
        print(f"✅ ETL SUCCESS – upserted {len(paragon_records)} live score records.")
    except Exception as e:
        print("❌ ETL FAILED during Supabase upsert:", e)
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 5) TREND ENGINE
    # ----------------------------------------------------
    print("[ETL] Writing trend history snapshot…")
    write_trend_history(paragon_records)

    print("============== ETL FINISHED ==============")


# ------------------------------------------------------------
# Entry
# ------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(run_etl())
