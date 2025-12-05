# etl/etl_runner.py

import asyncio
from typing import List, Dict, Any

from etl.crawlers.media_crawler import MediaCrawler
from etl.transformer import build_signals
from etl.scoring_engine import build_paragon_scores_from_signals
from utils.supabase_client import supabase_upsert


# ------------------------------------------------------------
# Trend writing helper (writes history snapshots)
# ------------------------------------------------------------
def write_trend_history(paragon_records: List[Dict[str, Any]]) -> None:
    """
    Saves a historical record of each politician's score.
    Table: paragon_trends
    Columns:
        politician_id
        score
        sentiment
        mentions
        calculated_at (timestamp)
    """

    history_rows = []

    for r in paragon_records:
        history_rows.append(
            {
                "politician_id": r["politician_id"],
                "overall_score": r["overall_score"],
                "sentiment": r["dimension_scores"]["Perceptimi Publik"]["score"],
                "mentions": r["signals_raw"]["mentions"],
                "calculated_at": "now()",
            }
        )

    if not history_rows:
        print("[Trend] No trend rows to write.")
        return

    try:
        supabase_upsert(
            table="paragon_trends",
            records=history_rows,
            conflict_col="id"  # new row each time — no conflict overwrite
        )
        print(f"[Trend] Wrote {len(history_rows)} trend history entries.")
    except Exception as e:
        print("❌ Trend history write failed:", e)


# ------------------------------------------------------------
# MAIN ETL PROCESS
# ------------------------------------------------------------
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
    # 2) BUILD NORMALIZED SIGNALS (names → normalized keys)
    # ----------------------------------------------------
    signals = build_signals(scraped_items)
    print(f"[ETL] Matched signals for {len(signals)} politicians")

    if not signals:
        print("[ETL] No signals matched to any politician.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 3) SCORING ENGINE (PARAGON normalization)
    # ----------------------------------------------------
    db_records = build_paragon_scores_from_signals(signals)

    if not db_records:
        print("[ETL] No DB records built – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 4) UPSERT live scores → Supabase
    # ----------------------------------------------------
    print("[ETL] Uploading normalized PARAGON scores to Supabase…")

    try:
        supabase_upsert(
            table="paragon_scores",
            records=db_records,           # correct param name
            conflict_col="politician_id"  # unique identifier
        )
        print(f"✅ ETL SUCCESS – upserted {len(db_records)} live score records.")
    except Exception as e:
        print("❌ ETL FAILED during Supabase upsert:", str(e))
        print("============== ETL FINISHED ==============")
        return

    # ----------------------------------------------------
    # 5) TREND ENGINE — Append history snapshot
    # ----------------------------------------------------
    print("[ETL] Writing trend history snapshot…")
    write_trend_history(db_records)

    print("============== ETL FINISHED ==============")


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(run_etl())
