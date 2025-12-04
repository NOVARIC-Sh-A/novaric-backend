# etl/etl_runner.py
import asyncio
from typing import List, Dict, Any

from etl.crawlers.media_crawler import MediaCrawler
from etl.transformer import build_signals
from etl.scoring_engine import build_paragon_scores_from_signals
from utils.supabase_client import supabase_upsert


async def run_etl() -> None:
    print("============== NOVARIC® PARAGON ETL ==============")

    # 1) Crawl live media
    crawler = MediaCrawler()
    scraped_items: List[Dict[str, Any]] = await crawler.run()
    print(f"[ETL] Scraped {len(scraped_items)} raw items")

    if not scraped_items:
        print("[ETL] No items scraped – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # 2) Transform → politician-level signals
    signals = build_signals(scraped_items)
    print(f"[ETL] Matched signals for {len(signals)} politicians")

    if not signals:
        print("[ETL] No signals matched to known profiles.")
        print("============== ETL FINISHED ==============")
        return

    # 3) Convert to PARAGON-style DB records
    db_records = build_paragon_scores_from_signals(signals)

    if not db_records:
        print("[ETL] No DB records built – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # 4) UPSERT → Supabase
    print("[ETL] Uploading scores to Supabase 'paragon_scores'…")

    try:
        response = supabase_upsert(
            table="paragon_scores",
            payload=db_records,
            conflict_col="profile_id"
        )

        # REST client returns dict, Python SDK returns object → handle both
        if isinstance(response, dict) and "error" in response:
            print("❌ Supabase upsert error:", response["error"])
        else:
            print(f"✅ ETL SUCCESS – upserted {len(db_records)} records.")

    except Exception as e:
        print("❌ ETL FAILED during Supabase upsert")
        print(str(e))

    print("============== ETL FINISHED ==============")


if __name__ == "__main__":
    asyncio.run(run_etl())
