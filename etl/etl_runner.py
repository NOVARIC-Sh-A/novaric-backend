import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from etl.crawlers.media_crawler import MediaCrawler
from etl.transformer import build_signals
from etl.scoring_engine import build_paragon_scores_from_signals
from utils.supabase_client import (
    supabase_upsert,
    supabase_insert,
    fetch_table,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# TREND ENGINE — Writes historical score snapshots
#
# Target schema (as you described):
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

    # 1) Fetch previous scores
    try:
        previous_rows = fetch_table("paragon_scores", select="politician_id, overall_score")
        previous_map: Dict[int, int] = {
            int(row["politician_id"]): int(row["overall_score"])
            for row in (previous_rows or [])
            if row.get("politician_id") is not None and row.get("overall_score") is not None
        }
    except Exception as e:
        print("[Trend] ⚠ Could not fetch previous scores:", e)
        previous_map = {}

    # 2) Build history rows
    history_rows: List[Dict[str, Any]] = []
    now_iso = _utc_now_iso()

    for r in paragon_records:
        pid_raw = r.get("politician_id")
        new_score_raw = r.get("overall_score")

        if pid_raw is None or new_score_raw is None:
            continue

        pid = int(pid_raw)
        new_score = int(new_score_raw)
        previous_score: Optional[int] = previous_map.get(pid)

        delta: Optional[int] = (new_score - previous_score) if previous_score is not None else None

        history_rows.append(
            {
                "politician_id": pid,
                "previous_score": previous_score,
                "new_score": new_score,
                "delta": delta,
                "raw_snapshot": r,         # full JSON snapshot
                "calculated_at": now_iso,  # explicit timestamptz
            }
        )

    if not history_rows:
        print("[Trend] No valid history rows to insert.")
        return

    # 3) Insert trend history
    try:
        supabase_insert("paragon_trends", history_rows)
        print(f"[Trend] Inserted {len(history_rows)} trend rows.")
    except Exception as e:
        print("[Trend] ❌ Trend insert failed:", e)


# ============================================================
# MAIN ETL PIPELINE
# ============================================================
async def run_etl() -> None:
    print("============== NOVARIC® PARAGON ETL ==============")

    # 1) Crawl media
    crawler = MediaCrawler()
    scraped_items: List[Dict[str, Any]] = await crawler.run()
    print(f"[ETL] Scraped {len(scraped_items)} raw items")

    if not scraped_items:
        print("[ETL] No items scraped – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # 2) Build normalized signals
    signals = build_signals(scraped_items)
    print(f"[ETL] Matched signals for {len(signals)} politicians")

    if not signals:
        print("[ETL] No signals matched to any politician.")
        print("============== ETL FINISHED ==============")
        return

    # 3) Scoring engine
    paragon_records = build_paragon_scores_from_signals(signals)

    if not paragon_records:
        print("[ETL] No DB records built – aborting.")
        print("============== ETL FINISHED ==============")
        return

    # 4) Upsert live scores
    print("[ETL] Uploading normalized PARAGON scores to Supabase…")
    try:
        supabase_upsert(
            table="paragon_scores",
            records=paragon_records,
            conflict_col="politician_id",
        )
        print(f"[ETL] ✅ SUCCESS – upserted {len(paragon_records)} live score records.")
    except Exception as e:
        print("[ETL] ❌ FAILED during Supabase upsert:", e)
        print("============== ETL FINISHED ==============")
        return

    # 5) Trend history
    print("[ETL] Writing trend history snapshot…")
    write_trend_history(paragon_records)

    print("============== ETL FINISHED ==============")


if __name__ == "__main__":
    asyncio.run(run_etl())
