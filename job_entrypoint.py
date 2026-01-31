import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from etl.etl_runner import run_etl


def _setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def _main() -> int:
    """
    Runs ETL once by default.

    Optional behavior:
    - RUN_LOOP=true  -> run forever with sleep between iterations
    - SLEEP_SECONDS=60 -> sleep interval when RUN_LOOP=true
    """
    run_loop = os.getenv("RUN_LOOP", "false").strip().lower() in ("1", "true", "yes")
    sleep_seconds = int(os.getenv("SLEEP_SECONDS", "60"))

    logging.info("etl_start ts=%s run_loop=%s sleep_seconds=%s", _utc_now(), run_loop, sleep_seconds)

    if not run_loop:
        await run_etl()
        logging.info("etl_done ts=%s", _utc_now())
        return 0

    # Loop mode (only enable if you intentionally want a polling runner)
    while True:
        try:
            await run_etl()
            logging.info("etl_iteration_done ts=%s next_in=%ss", _utc_now(), sleep_seconds)
        except Exception:
            logging.exception("etl_iteration_failed ts=%s", _utc_now())
        await asyncio.sleep(sleep_seconds)


def main() -> None:
    _setup_logging()

    try:
        exit_code = asyncio.run(_main())
        raise SystemExit(exit_code)
    except KeyboardInterrupt:
        logging.warning("etl_interrupted ts=%s", _utc_now())
        raise SystemExit(130)
    except Exception:
        logging.exception("etl_fatal ts=%s", _utc_now())
        raise SystemExit(1)


if __name__ == "__main__":
    main()
