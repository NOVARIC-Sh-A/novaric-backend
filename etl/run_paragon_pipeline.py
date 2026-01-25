# etl/run_paragon_pipeline.py

from __future__ import annotations

import argparse
from typing import Optional

from utils.supabase_client import _get

# Import the existing runners (you already have these)
from etl.run_paragon_metrics import run as run_metrics
from etl.run_paragon_scoring import run as run_scoring


def _has_politicians(offset: int) -> bool:
    """
    Determines whether there are politicians remaining for the given offset.
    Uses a lightweight query to prevent running empty pages.
    """
    rows = _get(
        "politicians",
        {
            "select": "id",
            "order": "id.asc",
            "limit": "1",
            "offset": str(offset),
        },
    )
    return bool(rows)


def run_pipeline(
    *,
    single_id: Optional[int],
    limit: int,
    offset: int,
    batch_size: int,
    pages: int,
    skip_metrics: bool,
    skip_scoring: bool,
) -> None:
    """
    Orchestrates the PARAGON pipeline:
      - run_paragon_metrics (writes paragon_metrics)
      - run_paragon_scoring (reads paragon_metrics, writes paragon_scores)

    Paging behavior:
      - If --single-id is provided, runs only that politician.
      - Otherwise, runs in 'pages' chunks: offset, offset+limit, offset+2*limit, ...
      - Stops early if no politicians exist at a given offset.
    """

    if single_id is not None:
        pid = int(single_id)
        print(f"[run_paragon_pipeline] Running SINGLE politician_id={pid}")

        if not skip_metrics:
            run_metrics(single_id=pid, limit=limit, offset=0, batch_size=batch_size)

        if not skip_scoring:
            run_scoring(single_id=pid, limit=limit, offset=0, batch_size=batch_size)

        print("[run_paragon_pipeline] Done (single-id).")
        return

    print(
        "[run_paragon_pipeline] Running paged pipeline "
        f"(limit={limit}, offset={offset}, pages={pages}, batch_size={batch_size}, "
        f"skip_metrics={skip_metrics}, skip_scoring={skip_scoring})"
    )

    processed_pages = 0
    current_offset = int(offset)

    for i in range(int(pages)):
        if not _has_politicians(current_offset):
            print(f"[run_paragon_pipeline] No politicians at offset={current_offset}. Stopping.")
            break

        page_no = i + 1
        print(f"[run_paragon_pipeline] Page {page_no}/{pages} offset={current_offset} limit={limit}")

        if not skip_metrics:
            run_metrics(single_id=None, limit=limit, offset=current_offset, batch_size=batch_size)

        if not skip_scoring:
            run_scoring(single_id=None, limit=limit, offset=current_offset, batch_size=batch_size)

        processed_pages += 1
        current_offset += int(limit)

    print(f"[run_paragon_pipeline] Done. processed_pages={processed_pages}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run PARAGON pipeline (metrics + scoring).")
    p.add_argument("--single-id", type=int, default=None, help="Run pipeline for one politician_id only.")
    p.add_argument("--limit", type=int, default=500, help="Page size for scanning politicians.")
    p.add_argument("--offset", type=int, default=0, help="Starting offset for scanning politicians.")
    p.add_argument("--batch-size", type=int, default=50, help="Upsert batch size inside each stage.")
    p.add_argument("--pages", type=int, default=1, help="How many pages to process (each page is --limit).")
    p.add_argument("--skip-metrics", action="store_true", help="Skip metrics stage (paragon_metrics).")
    p.add_argument("--skip-scoring", action="store_true", help="Skip scoring stage (paragon_scores).")
    args = p.parse_args()

    run_pipeline(
        single_id=args.single_id,
        limit=args.limit,
        offset=args.offset,
        batch_size=args.batch_size,
        pages=args.pages,
        skip_metrics=args.skip_metrics,
        skip_scoring=args.skip_scoring,
    )
