# etl/etl_runner.py

import asyncio
from typing import List, Dict, Any

from etl.crawlers.media_crawler import MediaCrawler
from etl.transformer import build_signals
from etl.scoring_engine import build_paragon_scores_from_signals

from utils.supabase_client import (
    supabase_upsert,
    supabase_insert,
    fetch_live_paragon_data
)


async def run_etl() -> None:
    print("============== NOVARIC® PARAGON ETL ==============")

    # ----------------------------------------------------
    # 1) CRAWL LIVE MEDIA
    # ----------------------------------------------------
    crawler = MediaCrawler()
    scraped_items: List[Dict[str, Any]] = await crawler.run()
    print(f"[ETL] Scraped {len(scraped_items)} raw items")

    if not scraped_items:
        print("[ETL] No items scraped – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 2) TRANSFORM → POLITICIAN-LEVEL SIGNALS
    # ----------------------------------------------------
    signals = build_signals(scraped_items)
    print(f"[ETL] Matched signals for {len(signals)} politicians")

    if not signals:
        print("[ETL] No politician signals extracted.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 3) SCORING → PARAGON-FORMAT RECORDS
    # ----------------------------------------------------
    db_records = build_paragon_scores_from_signals(signals)

    if not db_records:
        print("[ETL] No DB records built – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 4) UPSERT CURRENT SNAPSHOT → paragon_scores
    # ----------------------------------------------------
    print("[ETL] Uploading scores to Supabase 'paragon_scores'…")

    try:
        supabase_upsert(
            table="paragon_scores",
            records=db_records,
            conflict_col="politician_id"
        )

        print(f"✅ Live snapshot updated: {len(db_records)} records.")

    except Exception as e:
        print("❌ ETL FAILED during paragon_scores upsert")
        print(str(e))
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 5) FETCH PREVIOUS SNAPSHOT (optional for advanced trend logic)
    # ----------------------------------------------------
    try:
        previous_scores = fetch_live_paragon_data()
    except Exception:
        previous_scores = []

    # ----------------------------------------------------
    # 6) CONVERT NEW RESULTS → TREND ROWS
    # ----------------------------------------------------
    trend_rows = []
    for rec in db_records:
        trend_rows.append({
            "politician_id": rec["profile_id"],
            "overall_score": rec["overall_score"],
            "dimension_scores": rec["dimension_scores"],
            "signals_raw": None,
            "snapshot_at": "now()"   # PostgreSQL handles timestamps
        })

    # ----------------------------------------------------
    # 7) INSERT TREND HISTORY → paragon_trends
    # ----------------------------------------------------
    print("[ETL] Storing historical trend snapshot → 'paragon_trends'…")

    try:
        supabase_insert("paragon_trends", trend_rows)
        print(f"📈 Trend snapshot stored ({len(trend_rows)} rows).")

    except Exception as e:
        print("❌ Failed to store trend snapshot")
        print(str(e))

    print("============== ETL FINISHED ==============")


if __name__ == "__main__":
    asyncio.run(run_etl())
