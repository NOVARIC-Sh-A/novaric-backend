# etl/etl_runner.py

import asyncio
from typing import List, Dict, Any

from etl.crawlers.media_crawler import MediaCrawler
from etl.transformer import build_signals
from etl.scoring_engine import build_paragon_scores_from_signals
from utils.supabase_client import supabase_upsert


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
    # 2) TRANSFORM → EXTRACT POLITICIAN SIGNALS
    # ----------------------------------------------------
    signals = build_signals(scraped_items)
    print(f"[ETL] Matched signals for {len(signals)} politicians")

    if not signals:
        print("[ETL] No signals matched to known profiles.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 3) SCORING → PARAGON DB RECORDS
    # ----------------------------------------------------
    db_records = build_paragon_scores_from_signals(signals)

    if not db_records:
        print("[ETL] No DB records built – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 4) UPSERT → SUPABASE
    # ----------------------------------------------------
    print("[ETL] Uploading scores to Supabase 'paragon_scores'…")

    try:
        response = supabase_upsert(
            "paragon_scores",     # table name
            db_records,           # list of records
            "profile_id"          # unique conflict column
        )

        print(f"✅ ETL SUCCESS – upserted {len(db_records)} records.")

    except Exception as e:
        print("❌ ETL FAILED during Supabase upsert")
        print(str(e))

    print("============== ETL FINISHED ==============")


if __name__ == "__main__":
    asyncio.run(run_etl())
