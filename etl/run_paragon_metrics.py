# etl/run_paragon_metrics.py

from __future__ import annotations

import argparse
from typing import Any, Dict, List, Optional

from etl.media_scraper import scrape_media_signals
from etl.metrics_contract import scraper_to_canonical, canonical_to_db_paragon_metrics
from utils.supabase_client import _get, supabase_upsert


# ---------------------------------------------------------------------
# Fetch politician IDs (paged)
# ---------------------------------------------------------------------
def _fetch_politician_ids(limit: int, offset: int) -> List[int]:
    rows = _get(
        "politicians",
        {
            "select": "id",
            "order": "id.asc",
            "limit": str(limit),
            "offset": str(offset),
        },
    )
    ids: List[int] = []
    for r in rows:
        if isinstance(r, dict) and r.get("id") is not None:
            try:
                ids.append(int(r["id"]))
            except Exception:
                continue
    return ids


# ---------------------------------------------------------------------
# Build DB row for paragon_metrics (politician_id + mapped metrics)
# ---------------------------------------------------------------------
def _build_paragon_metrics_row(politician_id: int, scraper_payload: Dict[str, Any]) -> Dict[str, Any]:
    canonical = scraper_to_canonical(scraper_payload)
    db_row = canonical_to_db_paragon_metrics(canonical)

    # Must include PK for upsert
    db_row["politician_id"] = int(politician_id)

    return db_row


# ---------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------
def run(
    *,
    single_id: Optional[int],
    limit: int,
    offset: int,
    batch_size: int,
) -> None:
    if single_id is not None:
        ids = [int(single_id)]
    else:
        ids = _fetch_politician_ids(limit=limit, offset=offset)

    if not ids:
        print("[run_paragon_metrics] No politician IDs found for the given range.")
        return

    buffer: List[Dict[str, Any]] = []
    processed = 0
    failed = 0

    for pid in ids:
        try:
            scraper_payload = scrape_media_signals(pid)
            row = _build_paragon_metrics_row(pid, scraper_payload)
            buffer.append(row)
            processed += 1
        except Exception as e:
            failed += 1
            print(f"[run_paragon_metrics] ERROR politician_id={pid}: {e}")
            continue

        if len(buffer) >= batch_size:
            supabase_upsert("paragon_metrics", buffer, conflict_col="politician_id")
            print(f"[run_paragon_metrics] Upserted batch: {len(buffer)}")
            buffer.clear()

    if buffer:
        supabase_upsert("paragon_metrics", buffer, conflict_col="politician_id")
        print(f"[run_paragon_metrics] Upserted final batch: {len(buffer)}")

    print(f"[run_paragon_metrics] Done. processed={processed}, failed={failed}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Populate paragon_metrics from media scraper signals.")
    p.add_argument("--single-id", type=int, default=None, help="Run for one politician_id only.")
    p.add_argument("--limit", type=int, default=500, help="Pagination limit when scanning all politicians.")
    p.add_argument("--offset", type=int, default=0, help="Pagination offset when scanning all politicians.")
    p.add_argument("--batch-size", type=int, default=50, help="Upsert batch size.")
    args = p.parse_args()

    run(
        single_id=args.single_id,
        limit=args.limit,
        offset=args.offset,
        batch_size=args.batch_size,
    )
